#!/usr/bin/env python3
"""Run bounded MaskablePPO training on FEDS-derived TRAIN episodes only.

This command proves the local training path. A run is not a calibrated benchmark,
physical validation, or evidence of RL benefit.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


def _parse_budgets(value: str) -> tuple:
    try:
        budgets = tuple(int(item) for item in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("budgets must be comma-separated integers") from exc
    if not budgets or any(item < 0 for item in budgets):
        raise argparse.ArgumentTypeError("budgets must be nonnegative integers")
    return budgets


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, required=True,
                        help="PPO environment decisions; use 64 for the bounded smoke")
    parser.add_argument("--out", type=Path, required=True,
                        help="new, ignored local output directory")
    parser.add_argument("--wind-adjustment-factor", type=float, required=True,
                        help="one provisional factor shared across all TRAIN cases")
    parser.add_argument("--budgets", type=_parse_budgets, default=(0, 2, 4),
                        help="episode budget choices, for example 0,2,4")
    parser.add_argument("--internal-update-minutes", type=int, choices=(1, 3, 5, 10, 15), default=5)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)
    if args.steps < 64 or args.steps % 64:
        parser.error("--steps must be a multiple of 64 and at least 64")
    if not 0.0 <= args.wind_adjustment_factor <= 1.0:
        parser.error("--wind-adjustment-factor must be in [0, 1]")
    if args.out.exists():
        parser.error("output directory already exists; choose a new path")

    try:
        import torch
        from sb3_contrib import MaskablePPO
        from wildfire_rl.feds_simfire_env import FedsSimFireEnv, sha256_file
    except ImportError as exc:
        parser.error("SimFire RL packages are missing from the Python 3.9.25 environment: %s" % exc)

    torch.set_num_threads(1)
    env = FedsSimFireEnv(
        wind_adjustment_factor=args.wind_adjustment_factor,
        budgets=args.budgets,
        internal_update_minutes=args.internal_update_minutes,
    )
    model = MaskablePPO(
        "MultiInputPolicy",
        env,
        n_steps=64,
        batch_size=64,
        n_epochs=2,
        seed=args.seed,
        device="cpu",
        verbose=0,
        policy_kwargs={"net_arch": [64, 64]},
    )
    model.learn(total_timesteps=args.steps)

    args.out.mkdir(parents=True, exist_ok=False)
    checkpoint = args.out / "feds-maskable-ppo.zip"
    model.save(checkpoint)
    loaded = MaskablePPO.load(checkpoint, env=env, device="cpu")
    observation, _reset_info = env.reset(seed=args.seed + 1)
    done = False
    rollout = []
    while not done:
        action, _state = loaded.predict(
            observation,
            action_masks=env.action_masks(),
            deterministic=True,
        )
        observation, reward, terminated, truncated, info = env.step(action)
        rollout.append({"reward": float(reward), **info})
        done = bool(terminated or truncated)

    from wildfire_rl.feds_simfire_env import MANIFEST, WEATHER
    from wildfire_rl.feds_simfire_setup import policy_settings

    receipt = {
        "schema_version": "feds-simfire-ppo-smoke/1.0",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "label": "TRAIN-ONLY TECHNICAL PPO SMOKE; NOT A BENCHMARK OR RESEARCH RESULT",
        "split": "train",
        "train_scenario_count": len(env.scenario_ids),
        "train_scenario_ids": list(env.scenario_ids),
        "validation_or_test_cases_loaded": False,
        "feds_future_perimeters_used_for_observation_or_reward": False,
        "physical_validation": False,
        "rl_benefit_claim": False,
        # Settings the benchmark checks before it loads this checkpoint.
        **policy_settings(env.sim_params, weather_observation=env.weather_observation,
                          line_placement=env.line_placement, observation_max_budget=env.max_budget),
        "wind_adjustment_factor": args.wind_adjustment_factor,
        "wind_adjustment_factor_locked": False,
        "internal_update_minutes": args.internal_update_minutes,
        "decision_hours": 12,
        "episode_horizon_hours": 48,
        "episode_decisions": 4,
        "budgets_sampled": list(args.budgets),
        "actions": "no-op plus eight directional seven-cell fireline segments",
        "reward": "negative incremental cumulative SimFire-burned cells divided by 100",
        "training_seed": args.seed,
        "requested_steps": args.steps,
        "actual_steps": model.num_timesteps,
        "smoke_rollout_seed": args.seed + 1,
        "smoke_rollout": rollout,
        "checkpoint_sha256": sha256_file(checkpoint),
        "source_hashes": {
            "episode_manifest_sha256": sha256_file(MANIFEST),
            "gridmet_train_weather_file_sha256": sha256_file(WEATHER),
        },
        "packages": {
            name: importlib.metadata.version(name)
            for name in ("simfire", "torch", "numpy", "gymnasium", "stable-baselines3", "sb3-contrib")
        },
    }
    (args.out / "training_manifest.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.out),
        "checkpoint": str(checkpoint),
        "actual_steps": model.num_timesteps,
        "train_scenario_count": len(env.scenario_ids),
        "smoke_scenario_id": info["scenario_id"],
        "smoke_budget_left": info["remaining_budget"],
        "label": receipt["label"],
    }, indent=2))
    env.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
