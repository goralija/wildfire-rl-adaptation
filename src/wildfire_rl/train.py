"""Bounded CPU smoke training. This is not the pretrained adaptation experiment."""

import argparse
from dataclasses import asdict
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path

from .evaluation import source_metadata
from .simulator import Scenario


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps', type=int, default=1024)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if not 64 <= args.steps <= 1024 or args.steps % 64:
        parser.error('smoke steps must be a multiple of 64 between 64 and 1024')
    if args.out.exists():
        parser.error('output directory already exists')
    try:
        import torch
        from sb3_contrib import MaskablePPO
        from .gym_env import GridFireEnv
    except ImportError:
        parser.error("install the optional RL extra: pip install -e '.[rl]'")
    torch.set_num_threads(1)
    scenario = Scenario(rows=6, cols=6, ignition=(21,), priority=(4, 5, 10, 11),
                        warmup_steps=3, horizon=24)
    env = GridFireEnv(scenario, budgets=(0, 2, 4), scenario_seeds=tuple(range(32)))
    model = MaskablePPO('MultiInputPolicy', env, n_steps=64, batch_size=64, n_epochs=2,
                        seed=7, device='cpu', verbose=0,
                        policy_kwargs=dict(net_arch=[32, 32]))
    model.learn(args.steps)
    args.out.mkdir(parents=True, exist_ok=False)
    path = args.out / 'synthetic-smoke.zip'
    model.save(path)
    loaded = MaskablePPO.load(path, env=env, device='cpu')
    obs, info = env.reset(seed=200)
    done = False
    while not done:
        action, _ = loaded.predict(obs, action_masks=env.action_masks(), deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
    manifest = dict(label='SYNTHETIC RL SMOKE ONLY; trained from scratch, no adaptation claim',
                    **source_metadata(), scenario=asdict(scenario), training_seed=7,
                    training_scenario_seeds=list(range(32)), training_budgets=[0, 2, 4],
                    reset_seed_for_smoke=200, smoke_rollout=info,
                    smoke_is_held_out=False, requested_steps=args.steps,
                    actual_steps=model.num_timesteps,
                    checkpoint_sha256=sha256(path.read_bytes()).hexdigest(),
                    packages={name: importlib.metadata.version(name) for name in
                              ('torch', 'numpy', 'gymnasium', 'stable-baselines3', 'sb3-contrib')})
    (args.out / 'training_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Saved/reloaded synthetic MaskablePPO after {model.num_timesteps} CPU steps: {path}')


if __name__ == '__main__':
    main()
