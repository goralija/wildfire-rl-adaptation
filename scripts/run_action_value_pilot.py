#!/usr/bin/env python3
"""ADR-059 bounded TRAIN-only collection, one fit, one development evaluation."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import importlib.metadata
import json
import multiprocessing
import os
from pathlib import Path
import platform
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[name] = '1'
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'.local/matplotlib'))
import numpy as np
from wildfire_rl.action_value import (validate_split, action_features, fit_ridge,
                                      select_action, reference_actions, compare)
from wildfire_rl.common_control import CommonControlEnv, encoded_observation
from wildfire_rl.control_factory import native_env
from wildfire_rl.feds_heuristics import advancing_front_policy, downwind_policy
from wildfire_rl.feds_simfire_setup import WEATHER
from wildfire_rl.line_damage import score_line_damage

PLAN = ROOT/'configs/frozen/action-value-pilot-v1.json'
ACTIVE_OUT = None


def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    path = Path(path); tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n'); tmp.replace(path)


def guard():
    sources = sorted((ROOT/'src/wildfire_rl').glob('*.py')) + [Path(__file__), PLAN]
    return dict(source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources},
                runtime=dict(python=platform.python_version(), packages={n: importlib.metadata.version(n)
                             for n in ('numpy', 'gymnasium', 'simfire')}))


def assert_guard(out):
    if read(Path(out)/'guard.json') != guard(): raise ValueError('source/plan/runtime changed')


def setup_worker():
    if os.getpriority(os.PRIO_PROCESS, 0) < 19: raise RuntimeError('nice19 required')


def archive_reference(archive, backend, sid):
    p = archive/'.local/expanded-v1'/backend/(sid+'.npz'); record = read(p.with_suffix('.json'))
    if sha(p) != record['npz_sha256']: raise ValueError('no-op archive hash changed')
    # Check all shared physics sources present in this extraction against the old receipt.
    for name, digest in record['guard']['common']['source_sha256'].items():
        if (ROOT/name).is_file() and sha(ROOT/name) != digest:
            raise ValueError('archived physics differs: '+name)
    with np.load(p, allow_pickle=False) as a:
        return a['initial'].copy(), a['simfire' if backend == 'simfire' else 'ca0'].copy(), sha(p)


def rollout(env, first_action):
    obs, _ = env.reset(); burned = [env.unwrapped.cumulative_burned.copy()]
    for k in range(4):
        action = int(first_action) if k == 0 else 0
        if not env.action_masks()[action]: raise ValueError('illegal proposed action')
        _, _, done, trunc, info = env.step(action)
        if trunc or done != (k == 3) or info['invalid_action']:
            raise ValueError('full four-step legal horizon required')
        burned.append(env.unwrapped.cumulative_burned.copy())
    return dict(env.ledger.score), np.stack(burned), env.ledger.line.copy()


def collect(job):
    out, archive, sid = Path(job[0]), Path(job[1]), job[2]
    assert_guard(out); plan = read(PLAN); started = time.monotonic(); arrays = {}; receipts = {}
    for backend in plan['backends']:
        initial, reference, ref_sha = archive_reference(archive, backend, sid)
        raw, inputs = native_env(backend, sid)
        if inputs['receipt_sha256'] != plan['input_receipt_sha256'][sid]: raise ValueError('input changed')
        if sha(WEATHER) != plan['weather_sha256']: raise ValueError('weather changed')
        obs, _ = raw.reset(); encoded = encoded_observation(obs); mask = raw.action_masks().copy()
        np.testing.assert_array_equal(initial, raw.unwrapped.cumulative_burned)
        refs = reference_actions(encoded, mask)
        if refs['advancing_front64'] != advancing_front_policy({**obs, 'grid': obs['global_grid']}, mask):
            raise ValueError('encoded front reference differs from v2 rule')
        if refs['downwind'] != downwind_policy(obs, mask): raise ValueError('encoded wind reference differs')
        env = CommonControlEnv(raw, reference[-1])
        burns, lines, scores = [], [], []
        if backend == 'ca':
            score, trajectory, line = rollout(env, 0)
            np.testing.assert_array_equal(trajectory, reference)
            for requested in range(9):
                if requested and mask[requested]: score, trajectory, line = rollout(env, requested)
                elif requested:
                    score, trajectory, line = scores[0], reference, lines[0]
                scores.append(dict(score)); burns.append(trajectory[-1].copy()); lines.append(line.copy())
        else:
            folder = archive/'.local/b1-cases'; p = folder/(sid+'.json'); table = read(p)
            if sha(p) != plan['sf_case_json_sha256'][sid] or sha(p.with_suffix('.npz')) != table['mask_file_sha256']:
                raise ValueError('SimFire B1 table changed')
            with np.load(p.with_suffix('.npz'), allow_pickle=False) as old:
                np.testing.assert_array_equal(initial, old['initial'])
                np.testing.assert_array_equal(reference[-1], old['noop'])
                for requested in range(9):
                    sequence = [requested if mask[requested] else 0, 0, 0, 0]
                    index = next(i for i, r in enumerate(table['outcomes']) if r['requested_actions'] == sequence)
                    burned, line = old['agent_burned'][index], old['line_cells'][index]
                    score = score_line_damage(initial, burned, reference[-1], line)
                    if any(score[key] != table['outcomes'][index][key] for key in score):
                        raise ValueError('cached SimFire mask/score differs')
                    scores.append(score); burns.append(burned.copy()); lines.append(line.copy())
        env.close()
        arrays.update({backend+'_obs': encoded, backend+'_mask': mask, backend+'_burned': np.stack(burns),
                       backend+'_line': np.stack(lines), backend+'_reference': reference,
                       backend+'_saved': np.array([r['charged_saved_cells'] for r in scores]),
                       backend+'_noop': np.array(scores[0]['noop_damage_cells'])})
        receipts[backend] = dict(reference_sha256=ref_sha, references=refs)
    np.testing.assert_array_equal(arrays['simfire_obs'], arrays['ca_obs'])
    np.testing.assert_array_equal(arrays['simfire_mask'], arrays['ca_mask'])
    target = out/'cases'/(sid+'.npz'); np.savez_compressed(target, **arrays)
    write(target.with_suffix('.json'), dict(scenario_id=sid, sha256=sha(target), references=receipts,
                                         seconds=time.monotonic()-started, status='PASS'))
    return sid


def load_case(out, sid):
    path = Path(out)/'cases'/(sid+'.npz')
    if sha(path) != read(path.with_suffix('.json'))['sha256']: raise ValueError('collected case changed')
    with np.load(path, allow_pickle=False) as a: return {key: a[key].copy() for key in a.files}


def collect_guarded(job):
    try:
        return collect(job)
    except Exception:
        import traceback
        print('case ERROR', job[2], flush=True)
        traceback.print_exc()
        raise


def fit(out, plan):
    # No development case is opened until both fitted checkpoints have been frozen.
    cases = [load_case(out, sid) for sid in plan['fitting_cases']]
    keep = [i for i, c in enumerate(cases) if c['ca_noop'] > 0 and c['simfire_noop'] > 0]
    models = {}; freeze = dict(guard=read(out/'guard.json'), fitting_ids=[plan['fitting_cases'][i] for i in keep], models={})
    for be in plan['backends']:
        x = np.array([action_features(cases[i][be+'_obs']) for i in keep])
        y = np.array([cases[i][be+'_saved'][1:]/cases[i][be+'_noop'] for i in keep])
        masks = np.array([cases[i][be+'_mask'] for i in keep])
        model = fit_ridge(x, y, masks, alpha=plan['learner']['alpha'])
        path = out/(be+'-model.npz'); np.savez_compressed(path, **model)
        freeze['models'][be] = sha(path); models[be] = model
    write(out/'fit-freeze.json', freeze)
    return models


def evaluate(out, archive, plan, models):
    cases = [load_case(out, sid) for sid in plan['evaluation_cases']]
    joint = np.array([c['ca_noop'] > 0 and c['simfire_noop'] > 0 for c in cases])
    result = dict(scope='Exploratory TRAIN development, not independent/physical validation',
                  guard=read(out/'guard.json'), freeze_sha256=sha(out/'fit-freeze.json'), backends={})
    for be in plan['backends']:
        rows = []; selected = []; references = []
        for sid, c in zip(plan['evaluation_cases'], cases):
            obs, mask, saved = (c[be+'_'+k] for k in ('obs', 'mask', 'saved'))
            action = select_action(models[be], action_features(obs), mask)
            ref_actions = reference_actions(obs, mask)
            ref_values = {name: float(saved[a]) for name, a in ref_actions.items()}
            ref_values['uniform_legal_exact'] = float(saved[1:][mask[1:]].mean()) if mask[1:].any() else 0.
            rows.append(dict(scenario_id=sid, action=action, noop_cells=int(c[be+'_noop']),
                             saved_cells=int(saved[action]), reference_saved_cells=ref_values))
            selected.append(saved[action]); references.append([ref_values[n] for n in plan['references']])
        metrics = compare(np.array(selected), np.array([c[be+'_noop'] for c in cases]), np.array(references).T, joint)
        metrics['reference_names'] = plan['references']; best = plan['references'][int(np.argmax(metrics['reference_means_percent']))]
        # Fresh full-mask replay of each selected SimFire path (CA paths were all freshly collected).
        replay = []
        for sid, c, row in zip(plan['evaluation_cases'], cases, rows):
            a = row['action']
            independent = score_line_damage(c[be+'_reference'][0], c[be+'_burned'][a],
                                           c[be+'_reference'][-1], c[be+'_line'][a])
            if independent['charged_saved_cells'] != row['saved_cells']: raise ValueError('independent score mismatch')
            if be == 'simfire':
                raw, _ = native_env(be, sid); env = CommonControlEnv(raw, c[be+'_reference'][-1])
                score, states, line = rollout(env, a); env.close()
                np.testing.assert_array_equal(states[-1], c[be+'_burned'][a])
                np.testing.assert_array_equal(line, c[be+'_line'][a])
                if score != independent: raise ValueError('fresh native score mismatch')
            replay.append(dict(scenario_id=sid, action=a, status='PASS'))
        result['backends'][be] = dict(metrics=metrics, strongest_reference=best, cases=rows, replay=replay)
    result['joint_positive_ids'] = [sid for sid, keep in zip(plan['evaluation_cases'], joint) if keep]
    result['joint_near'] = all(b['metrics']['near'] for b in result['backends'].values())
    result['joint_better'] = all(b['metrics']['better'] for b in result['backends'].values())
    write(out/'analysis.json', result)


def main():
    global ACTIVE_OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--pilot', action='store_true', help='technical collection of first two fitting fires only')
    args = parser.parse_args(); out = args.out.resolve(); archive = args.archive.resolve()
    setup_worker(); plan = read(PLAN); validate_split(plan['fitting_cases'], plan['evaluation_cases'])
    if not out.exists():
        out.mkdir(parents=True); (out/'cases').mkdir(); write(out/'guard.json', guard())
    assert_guard(out)
    if (out/'analysis.json').exists() or (out/'fit-freeze.json').exists(): raise FileExistsError('fit/evaluation already run')
    import fcntl
    lock = (out/'run.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    ACTIVE_OUT = out
    def deadline(_signal, _frame): raise TimeoutError('30 minute experiment limit')
    signal.signal(signal.SIGALRM, deadline); signal.alarm(1800)
    started = time.monotonic()
    status = dict(pid=os.getpid(), started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), phase='collecting')
    write(out/'status.json', status)
    ids = plan['fitting_cases'][:2] if args.pilot else plan['fitting_cases']+plan['evaluation_cases']
    pending = []
    for sid in ids:
        if (out/'cases'/(sid+'.json')).exists(): load_case(out, sid)
        else: pending.append((str(out), str(archive), sid))
    with ProcessPoolExecutor(3, mp_context=multiprocessing.get_context('spawn'), initializer=setup_worker) as pool:
        jobs = [pool.submit(collect_guarded, job) for job in pending]
        for job in as_completed(jobs):
            sid = job.result(); print('case PASS', sid, flush=True)
            status['completed_cases'] = len(list((out/'cases').glob('*.json'))); write(out/'status.json', status)
    if args.pilot:
        status.update(phase='pilot_complete', seconds=time.monotonic()-started); write(out/'status.json', status); return
    assert_guard(out); status['phase'] = 'fitting'; write(out/'status.json', status)
    models = fit(out, plan); status['phase'] = 'evaluating'; write(out/'status.json', status)
    evaluate(out, archive, plan, models); assert_guard(out)
    status.update(phase='complete', seconds=time.monotonic()-started); write(out/'status.json', status)
    print('COMPLETE', flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as error:
        import traceback
        if ACTIVE_OUT is not None:
            status = read(ACTIVE_OUT/'status.json') if (ACTIVE_OUT/'status.json').exists() else {}
            status.update(phase='failed', error=str(error)); write(ACTIVE_OUT/'status.json', status)
        traceback.print_exc(); sys.exit(1)
