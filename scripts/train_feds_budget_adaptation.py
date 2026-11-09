#!/usr/bin/env python3
"""Train a base MaskablePPO policy or fine-tune it to one budget, TRAIN cases only.

``--phase base`` trains from scratch on the reference budget set. ``--phase
finetune`` loads a base checkpoint and continues training on a target budget set
with the same simulator parameters, observations and action space. Fine-tuning at
the base budget is the matched "more training" control. Outputs stay in ignored
local directories; receipts state that this is a simulator experiment only.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


def _parse_budgets(value: str) -> tuple:
    budgets = tuple(int(item) for item in value.split(","))
    if not budgets or any(item < 0 or item > 4 for item in budgets):
        raise argparse.ArgumentTypeError("budgets must be integers in [0, 4]")
    return budgets


def _make_env_factory(params: dict, budgets: tuple, placement: str, rank: int,
                      weather_observation: str = "previous"):
    def factory():
        import os

        os.environ.setdefault("OMP_NUM_THREADS", "1")
        from wildfire_rl.feds_simfire_env import FedsSimFireEnv
        from wildfire_rl.feds_simfire_setup import SimFireParams

        return FedsSimFireEnv(
            sim_params=SimFireParams(**params),
            budgets=budgets,
            split="train",
            line_placement=placement,
            max_budget=4,
            weather_observation=weather_observation,
        )

    return factory


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("base", "finetune"), required=True)
    parser.add_argument("--params", type=Path, required=True, help="JSON with frozen_params")
    parser.add_argument("--budgets", type=_parse_budgets, required=True)
    parser.add_argument("--steps", type=int, required=True, help="total environment decisions")
    parser.add_argument("--init", type=Path, help="base checkpoint for --phase finetune")
    parser.add_argument("--n-envs", type=int, default=7)
    parser.add_argument("--n-steps", type=int, default=16, help="rollout length per env")
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--line-placement", choices=("centroid", "front_edge"), default="front_edge")
    parser.add_argument("--perfect-forecast-ablation", action="store_true",
                        help="ABLATION ONLY (ADR-030): observe the upcoming 12h forcing instead of the previous one")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("output directory exists; choose a new path")
    if (args.phase == "finetune") != (args.init is not None):
        parser.error("--init is required for, and only for, --phase finetune")

    import torch
    from sb3_contrib import MaskablePPO
    from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor

    from wildfire_rl.feds_simfire_setup import MANIFEST, WEATHER, SimFireParams, policy_settings, sha256_file

    torch.set_num_threads(1)
    freeze = json.loads(args.params.read_text(encoding="utf-8"))
    params = freeze["frozen_params"]
    sim_params = SimFireParams(**params)
    if sim_params.internal_update_minutes != 5:
        parser.error("ADR-030 fixes the SimFire internal step at 5 minutes.")
    weather_observation = "upcoming_perfect_forecast" if args.perfect_forecast_ablation else "previous"
    expected_settings = policy_settings(sim_params, weather_observation=weather_observation,
                                        line_placement=args.line_placement,
                                        observation_max_budget=4)
    env = VecMonitor(SubprocVecEnv([
        _make_env_factory(params, args.budgets, args.line_placement, rank, weather_observation)
        for rank in range(args.n_envs)
    ], start_method="spawn"))
    env.seed(args.seed)
    started = time.monotonic()
    if args.phase == "base":
        model = MaskablePPO(
            "MultiInputPolicy",
            env,
            n_steps=args.n_steps,
            batch_size=(args.n_steps * args.n_envs) // 2,
            n_epochs=4,
            gamma=1.0,
            learning_rate=args.learning_rate,
            ent_coef=0.01,
            seed=args.seed,
            device="cpu",
            verbose=0,
            policy_kwargs={"net_arch": [64, 64]},
        )
    else:
        # The base checkpoint must have been trained under the same settings (receipt check
        # before unpickling, as in the benchmark); legacy checkpoints are not fine-tuned.
        sys.path.insert(0, str(ROOT / "scripts"))
        from benchmark_feds_policies import CheckpointReceiptError, check_checkpoint_receipt

        try:
            check_checkpoint_receipt(args.init, expected_settings, allow_legacy=False)
        except CheckpointReceiptError as exc:
            parser.error(str(exc))
        # The restored learning-rate schedule is kept; fine-tuning uses the base rate.
        model = MaskablePPO.load(args.init, env=env, device="cpu")
        model.set_random_seed(args.seed)
    model.learn(total_timesteps=args.steps, reset_num_timesteps=True)
    elapsed = time.monotonic() - started

    args.out.mkdir(parents=True)
    checkpoint = args.out / "policy.zip"
    model.save(checkpoint)
    episode_returns = [float(item["r"]) for item in getattr(model, "ep_info_buffer", [])]
    receipt = {
        "schema_version": "feds-simfire-budget-adaptation-train/1.0",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "label": "TRAIN-ONLY SIMULATOR POLICY TRAINING; NOT PHYSICAL VALIDATION",
        "phase": args.phase,
        "init_checkpoint": str(args.init) if args.init else None,
        "init_checkpoint_sha256": sha256_file(args.init) if args.init else None,
        "budgets": list(args.budgets),
        # Settings the benchmark checks before it loads this checkpoint.
        **policy_settings(sim_params, weather_observation=weather_observation,
                          line_placement=args.line_placement, observation_max_budget=4),
        "params_file_sha256": sha256_file(args.params),
        "params_gate_status": freeze.get("gate_status"),
        "split": "train",
        "validation_or_test_cases_loaded": False,
        "seed": args.seed,
        "requested_steps": args.steps,
        "actual_steps": int(model.num_timesteps),
        "n_envs": args.n_envs,
        "n_steps": args.n_steps,
        "learning_rate": args.learning_rate,
        "gamma": 1.0,
        "wall_clock_minutes": elapsed / 60.0,
        "recent_episode_returns": episode_returns,
        "checkpoint_sha256": sha256_file(checkpoint),
        "source_hashes": {
            "episode_manifest_sha256": sha256_file(MANIFEST),
            "gridmet_weather_file_sha256": sha256_file(WEATHER),
        },
        "packages": {
            name: importlib.metadata.version(name)
            for name in ("simfire", "torch", "numpy", "gymnasium", "stable-baselines3", "sb3-contrib")
        },
    }
    (args.out / "training_manifest.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("phase", "budgets", "seed", "actual_steps",
                                                     "wall_clock_minutes")}, indent=2))
    env.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
