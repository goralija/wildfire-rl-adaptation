"""Bounded inference-only diagnostic for the isolated legacy Firehose container.

Run this file inside docker/firehose, not in the modern project environment.
The original observation/action architecture and weights are preserved.
"""

import argparse
import csv
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import time
import traceback

CHECKPOINTS = {
    'ppo-fixed': ('20x20-fixed-ppo-maskable.zip',
                  'ec9475239abb141ab627e6e3d07f14e49da2b7a71020699fed55504db0bf9a5c'),
    'ppo-random': ('20x20-random-20m-ppo-maskable.zip',
                   '08cb56f17fdb99f2f17ac542008963324a75a724fe2d5cf032537e7381304dec'),
}
TERMINAL_STATE_PREFIX = 'FIREHOSE_TERMINAL_STATE '
TERMINATION_REASONS = {
    'weather_horizon', 'front_extinguished', 'grid_exhausted', 'no_ignition',
    'upstream_terminal_unclassified',
}


def budget_action(candidate, used, budget):
    return -1 if used >= budget else int(candidate)


def override_seed(command, seed):
    if command.count('--seed 123 ') != 1:
        raise ValueError('expected exactly one upstream --seed 123 argument')
    return command.replace('--seed 123 ', '--seed %d ' % seed)


def history_damage(paths):
    """Read C++ outputGrid codes: 1 burnt, 2 burning, -1 treated, 0 otherwise."""
    affected = set()
    for path in paths:
        with Path(path).open() as file:
            cells = [int(value) for row in csv.reader(file) for value in row]
        affected.update(i for i, value in enumerate(cells) if value > 0)
    return affected


def cells_with_state(grid, states):
    """Return sorted one-based row-major IDs matching one or more grid codes."""
    values = grid.tolist() if hasattr(grid, 'tolist') else grid
    if not values or not values[0]:
        raise ValueError('state grid must be a nonempty rectangle')
    width = len(values[0])
    if any(len(row) != width for row in values):
        raise ValueError('state grid rows must have equal length')
    wanted = set(states)
    return sorted(
        row_index * width + col_index + 1
        for row_index, row in enumerate(values)
        for col_index, value in enumerate(row)
        if int(value) in wanted
    )


def parse_terminal_state(lines):
    """Parse and validate the single structured terminal receipt from C++ stdout."""
    records = [line[len(TERMINAL_STATE_PREFIX):] for line in lines
               if line.startswith(TERMINAL_STATE_PREFIX)]
    if not records:
        return None
    if len(records) != 1:
        raise ValueError('expected at most one Firehose terminal-state record')
    record = json.loads(records[0])
    if record.get('schema') != 'firehose-terminal-state-v1':
        raise ValueError('unsupported Firehose terminal-state schema')
    if record.get('reason') not in TERMINATION_REASONS:
        raise ValueError('unknown Firehose terminal reason')
    if record.get('cell_id_base') != 1:
        raise ValueError('terminal-state cell IDs must be one-based')
    for field in ('active_front_ncells', 'ever_affected_ncells', 'treated_ncells'):
        values = record.get(field)
        if not isinstance(values, list) or any(type(value) is not int or value < 1 for value in values):
            raise ValueError('terminal-state %s must contain positive integer cell IDs' % field)
        if values != sorted(set(values)):
            raise ValueError('terminal-state %s must be sorted and unique' % field)
    if not set(record['active_front_ncells']).issubset(record['ever_affected_ncells']):
        raise ValueError('active-front cells must be included in cumulative affected cells')
    for field in ('available_cell_count', 'total_cell_count', 'fire_period', 'weather_period'):
        if type(record.get(field)) is not int or record[field] < 0:
            raise ValueError('terminal-state %s must be a nonnegative integer' % field)
    if record['available_cell_count'] > record['total_cell_count']:
        raise ValueError('available cell count exceeds total grid size')
    for field in ('active_front_ncells', 'ever_affected_ncells', 'treated_ncells'):
        if any(cell_id > record['total_cell_count'] for cell_id in record[field]):
            raise ValueError('terminal-state %s contains an ID outside the grid' % field)
    return record


def terminal_damage_matches_grid_history(terminal_state, grid_damage):
    """Check grid coverage and explain treated cells hidden by the final grid code.

    Cell2Fire gives treatment precedence in its categorical grid output. A cell
    that was affected and later treated therefore appears as ``-1`` in every
    saved grid after treatment, even though the terminal C++ cumulative set
    correctly retains it.
    """
    if terminal_state is None:
        return False
    terminal_damage = set(terminal_state['ever_affected_ncells'])
    visible_damage = set(grid_damage)
    treated = set(terminal_state['treated_ncells'])
    hidden_by_treatment = terminal_damage - visible_damage
    return visible_damage.issubset(terminal_damage) and hidden_by_treatment.issubset(treated)


def input_tree_hash(root):
    root = Path(root)
    h = sha256()
    for path in sorted(p for p in root.rglob('*') if p.is_file()):
        h.update(str(path.relative_to(root)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def weather_horizon(path, minutes_per_weather_row=60):
    """Return the number of weather rows and their modeled time coverage."""
    if type(minutes_per_weather_row) is not int or minutes_per_weather_row < 1:
        raise ValueError('minutes_per_weather_row must be a positive integer')
    with Path(path).open(newline='') as stream:
        rows = list(csv.reader(stream))
    if not rows:
        raise ValueError('Weather.csv is empty')
    data_rows = [row for row in rows[1:] if any(value.strip() for value in row)]
    return len(data_rows), len(data_rows) * minutes_per_weather_row


def weight_hash(model):
    h = sha256()
    for name, value in sorted(model.policy.state_dict().items()):
        h.update(name.encode())
        h.update(value.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', choices=('none', 'min_l2', 'max_l2', *CHECKPOINTS), required=True)
    parser.add_argument('--seed', type=int, default=123)
    parser.add_argument('--budget', type=int, default=8)
    parser.add_argument('--sync-reset', action='store_true', help='load actual warmup CSV before first action')
    parser.add_argument('--steps-before-sim', type=int, default=20)
    parser.add_argument('--steps-per-action', type=int, default=8)
    parser.add_argument('--max-steps', type=int, default=200)
    parser.add_argument('--fire-map', default='Sub20x20',
                        help='map directory under cell2fire/data; use a mounted real-case input map when needed')
    parser.add_argument('--initial-state-csv', type=Path,
                        help='optional historical state,ncell CSV copied into the scenario input')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.seed < 0 or args.budget < 0:
        parser.error('seed and budget must be nonnegative')
    if args.steps_before_sim < 0 or args.steps_per_action < 1 or args.max_steps < 1:
        parser.error('steps-before must be nonnegative; steps-per-action and max-steps must be positive')
    args.out.mkdir(parents=True, exist_ok=False)

    def timeout_handler(*_):
        raise TimeoutError('90-second probe deadline')

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(90)
    env = None
    model = None
    result = dict(policy=args.policy, simulator_seed=args.seed, budget=args.budget,
                  sync_reset=args.sync_reset, fire_map=args.fire_map, no_training=True, success=False,
                  termination_reason=None,
                  firehose_commit='e49a52a9a987a1585d25ddca2f711222ca500ffb',
                  contrib_commit='43b7fe6fcdda71c2c10de7af0d20f39e48ae5df3',
                  script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                  python=platform.python_version(), platform=platform.platform())
    start = time.perf_counter()
    try:
        import numpy as np
        import pandas as pd
        import torch
        from sb3_contrib import MaskablePPO
        from cell2fire.gym_env import FireEnv
        from firehose.helpers import IgnitionPoint, IgnitionPoints
        from firehose.baselines import NaiveAlgorithm, HumanExpertAlgorithm

        torch.set_num_threads(1)
        result['packages'] = {name: importlib.metadata.version(name) for name in
                              ('numpy', 'torch', 'gym', 'stable-baselines3', 'sb3-contrib', 'cloudpickle')}
        if args.policy in CHECKPOINTS:
            filename, expected = CHECKPOINTS[args.policy]
            path = Path('/opt/firehose/pretrained_models') / filename
            actual = sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError('checkpoint checksum mismatch')
            model = MaskablePPO.load(str(path), device='cpu')
            result['checkpoint_sha256'] = actual
            result['weights_before'] = weight_hash(model)
            result['pretrained_timesteps'] = model.num_timesteps
            result['model_observation_shape'] = list(model.observation_space.shape)
            result['model_actions'] = int(model.action_space.n)

        env = FireEnv(fire_map=args.fire_map, action_type='flat', observation_type='forest_rgb',
                      ignition_points=IgnitionPoints([IgnitionPoint(372, 1, x=11, y=18)]),
                      steps_before_sim=args.steps_before_sim,
                      steps_per_action=args.steps_per_action, max_steps=args.max_steps,
                      output_dir=str(args.out / 'simulator'), verbose=False)
        if args.initial_state_csv:
            shutil.copyfile(args.initial_state_csv,
                            Path(env.helper.tmp_input_folder) / 'InitialState.csv')
            env.has_initial_state = True
        original = env.fire_process.get_command_str
        env.fire_process.get_command_str = lambda: override_seed(original(), args.seed)
        result['simulator_command'] = env.fire_process.get_command_str()
        result['input_sha256'] = input_tree_hash(env.helper.tmp_input_folder)
        result['initial_state_csv_sha256'] = (
            sha256(args.initial_state_csv.read_bytes()).hexdigest()
            if args.initial_state_csv else None
        )
        result['ignition_cell_one_based'] = 372
        result['weather_file'] = 'Weather.csv (rows mode)'
        result['weather_rows_available'], result['weather_horizon_minutes'] = weather_horizon(
            Path(env.helper.tmp_input_folder) / 'Weather.csv'
        )
        observation = env.reset()
        initial_paths = [line for line in env.fire_process.lines if 'ForestGrid' in line and '.csv' in line]
        initial_state = pd.read_csv(initial_paths[-1], header=None).values
        active_state_code = 2 if env.has_initial_state else 1
        result['upstream_nonfuel_mask_cells'] = int(np.sum(env.helper.forest_non_fuel))
        result['warmup_affected_cells'] = int(np.sum(initial_state > 0))
        result['warmup_active_cells'] = (
            int(np.sum(initial_state == active_state_code)) if env.has_initial_state else None
        )
        result['warmup_ever_affected_cell_ids_one_based'] = cells_with_state(initial_state, {1, 2})
        result['warmup_active_front_cell_ids_one_based'] = (
            cells_with_state(initial_state, {active_state_code}) if env.has_initial_state else None
        )
        result['warmup_historical_scar_cell_ids_one_based'] = (
            cells_with_state(initial_state, {1}) if env.has_initial_state else []
        )
        result['initial_state_import_log'] = next(
            (line for line in env.fire_process.lines if line.startswith('Imported historical state:')),
            None,
        )
        result['upstream_reset_state_matches_csv'] = bool(np.array_equal(env.state, initial_state))
        if args.sync_reset:
            env.state = initial_state
            env._update_counters()
            observation = env.get_observation()
        heuristic = {'min_l2': NaiveAlgorithm, 'max_l2': HumanExpertAlgorithm}.get(args.policy)
        heuristic = heuristic(env) if heuristic else None
        used = 0
        nonfuel_requests = 0
        transitions = []
        done = False
        last_info = {}
        for decision in range(args.max_steps):
            candidate = -1
            if used < args.budget:
                if model is not None:
                    mask = np.asarray(env.action_masks(), dtype=bool)
                    candidate, _ = model.predict(observation, action_masks=mask, deterministic=True)
                    if not mask[int(candidate)]:
                        raise RuntimeError('model selected masked action')
                elif heuristic is not None:
                    candidate, _ = heuristic.predict(observation)
            action = budget_action(candidate, used, args.budget)
            if action >= 0:
                used += 1
                nonfuel_requests += int(env.helper.forest_non_fuel.ravel()[action] != 0)
            observation, reward, done, info = env.step(action)
            last_info = info
            transition = dict(
                decision=decision,
                action=action,
                used=used,
                affected_snapshot=int(np.sum(env.state > 0)),
                active_snapshot=(
                    int(np.sum(env.state == 2)) if env.has_initial_state else None
                ),
                ever_affected_cell_ids_one_based=info.get(
                    'ever_affected_cell_ids_one_based',
                    sorted(int(row * env.width + col + 1) for row, col in env.cells_burned),
                ),
                active_front_cell_ids_one_based=info.get(
                    'active_front_cell_ids_one_based',
                    cells_with_state(env.state, {2}) if env.has_initial_state else None,
                ),
                state_sha256=sha256(env.state.tobytes()).hexdigest(),
            )
            transitions.append(transition)
            if done:
                break
        grids = list(Path(env.helper.output_folder).rglob('ForestGrid*.csv'))
        exported_damage = sorted(index + 1 for index in history_damage(grids))
        terminal_state = parse_terminal_state(env.fire_process.lines)
        if terminal_state is not None:
            terminal_damage = terminal_state['ever_affected_ncells']
            state_export_matches_grids = terminal_damage_matches_grid_history(
                terminal_state, exported_damage
            )
            termination_reason = terminal_state['reason']
            active_front = terminal_state['active_front_ncells']
        else:
            terminal_damage = exported_damage
            state_export_matches_grids = None
            active_front = cells_with_state(env.state, {2}) if env.has_initial_state else None
            if last_info.get('termination_reason'):
                termination_reason = last_info['termination_reason']
            elif done and not env.fire_process.finished:
                termination_reason = 'probe_step_limit'
            elif env.fire_process.finished:
                termination_reason = 'upstream_terminal_unclassified'
        if not done and termination_reason is None:
            termination_reason = 'probe_step_limit'
        python_damage = sorted(
            int(row * env.width + col + 1) for row, col in env.cells_burned
        )
        python_damage_matches_simulator = (
            terminal_state is not None and python_damage == terminal_damage
        )
        result.update(decisions=len(transitions), actions=[r['action'] for r in transitions],
                      interventions_requested=used, transitions=transitions,
                      nonfuel_requests=nonfuel_requests,
                      observed_ever_affected_cells=len(terminal_damage),
                      ever_affected_cell_ids_one_based=terminal_damage,
                      active_front_cell_ids_one_based=active_front,
                      terminal_state=terminal_state,
                      terminal_state_matches_grid_history=state_export_matches_grids,
                      simulator_cumulative_affected_cells=len(terminal_damage),
                      python_cumulative_affected_cells=len(python_damage),
                      python_cumulative_matches_simulator=python_damage_matches_simulator,
                      upstream_cumulative_cells=len(env.cells_burned),
                      simulator_reported_finished=env.fire_process.finished,
                      termination_reason=termination_reason,
                      budget_exhausted_followed_by_noops=any(
                          r['action'] == -1 and r['used'] == args.budget for r in transitions))
        if model is not None:
            result['weights_after'] = weight_hash(model)
            result['weights_unchanged'] = result['weights_before'] == result['weights_after']
            if not result['weights_unchanged']:
                raise RuntimeError('inference changed policy tensors')
        result['success'] = bool(
            done and env.fire_process.finished and terminal_state is not None
            and terminal_state['reason'] != 'upstream_terminal_unclassified'
            and state_export_matches_grids and python_damage_matches_simulator
        )
    except Exception as exc:
        result['error'] = type(exc).__name__ + ': ' + str(exc)
        result['termination_reason'] = 'probe_timeout' if isinstance(exc, TimeoutError) else 'adapter_error'
        (args.out / 'error.txt').write_text(traceback.format_exc())
    finally:
        signal.alarm(0)
        if env is not None:
            process = env.fire_process.process
            if process is not None:
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    result['cleanup_killed_process'] = True
                result['subprocess_returncode'] = process.returncode
                (args.out / 'simulator-stderr.txt').write_bytes(process.stderr.read())
                (args.out / 'simulator-stdout.txt').write_text('\n'.join(env.fire_process.lines))
                for stream in (process.stdin, process.stdout, process.stderr):
                    stream.close()
                if process.returncode != 0:
                    result['success'] = False
                    result['termination_reason'] = 'subprocess_error'
            env.close()
        result['runtime_seconds'] = time.perf_counter() - start
        (args.out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('transitions', 'actions')}, indent=2))
    return 0 if result['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
