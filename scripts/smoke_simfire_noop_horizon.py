#!/usr/bin/env python3
"""Record no-intervention SimFire horizon probes without starting an agent."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".local/cache"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".local/matplotlib"))
sys.path.insert(0, str(ROOT / "src"))

from wildfire_rl.simfire_gym_env import SimFireCaseEnv


SAMPLE_IDS = {
    "train": "fpa-fod-400310930-owyhee",
    "validation": "fpa-fod-401316132-hayden",
    "test": "fpa-fod-401411292-larch-creek",
}


def save_map(env: SimFireCaseEnv, observation: dict, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fuel = env._case["fuel"]
    fire = np.rint(observation["map"][-1] * 5).astype(np.int8)
    fig, axes = plt.subplots(1, 2, figsize=(10, 5), constrained_layout=True)
    first = axes[0].imshow(fuel, cmap="terrain", interpolation="nearest")
    axes[0].set_title("Real LANDFIRE FBFM13")
    axes[0].set_xlabel("Grid column (30 m)")
    axes[0].set_ylabel("Grid row")
    fig.colorbar(first, ax=axes[0], shrink=0.8, label="Source fuel code")
    second = axes[1].imshow(fire, cmap="viridis", vmin=0, vmax=5, interpolation="nearest")
    axes[1].set_title("SimFire after no intervention")
    axes[1].set_xlabel("Grid column (30 m)")
    axes[1].set_ylabel("Grid row")
    fig.colorbar(second, ax=axes[1], shrink=0.8, ticks=range(6), label="Fire state")
    fig.suptitle("{} — no-op horizon probe".format(env._case["manifest"]["scenario_id"]))
    fig.savefig(path, dpi=140)
    plt.close(fig)


def run_case(split: str, output: Path, weather_wind_adjustment_factor: float) -> dict:
    env = SimFireCaseEnv(
        split=split,
        fireline_budget=32,
        decision_minutes=30,
        horizon_decisions=24,
        max_fire_duration_updates=15,
        weather_mode="gridmet_daily_proxy",
        weather_wind_adjustment_factor=weather_wind_adjustment_factor,
    )
    scenario_id = SAMPLE_IDS[split]
    observation, reset_info = env.reset(seed=20261101, options={"scenario_id": scenario_id})
    if not env.observation_space.contains(observation):
        raise RuntimeError("Initial observation is outside the declared Gymnasium space")
    transitions = []
    terminated = truncated = False
    while not (terminated or truncated):
        if not env.action_masks()[0]:
            raise RuntimeError("No-op action must remain legal throughout the episode")
        observation, reward, terminated, truncated, info = env.step(0)
        transitions.append({
            "action": "no_op",
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
            "info": info,
        })
    image_path = output / "{}-{}.png".format(split, scenario_id)
    save_map(env, observation, image_path)
    case = {
        "split": split,
        "scenario_id": scenario_id,
        "scenario_manifest": env._case["manifest_path"].relative_to(ROOT).as_posix(),
        "reset_info": reset_info,
        "transitions": transitions,
        "final_observation_shapes": {key: list(value.shape) for key, value in observation.items()},
        "final_observation_in_space": env.observation_space.contains(observation),
        "visual": image_path.relative_to(ROOT).as_posix(),
    }
    env.close()
    return case


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "reports/real-fire-data/simfire-cohort-v2-gridmet-noop-horizon")
    parser.add_argument("--splits", nargs="+", choices=tuple(SAMPLE_IDS), default=("train", "validation"))
    parser.add_argument("--wind-adjustment-factor", type=float, default=0.3)
    args = parser.parse_args()
    if not 0.1 <= args.wind_adjustment_factor <= 0.5:
        parser.error("wind adjustment factor must be between 0.1 and 0.5")
    output = args.out.expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Output directory is not empty: {}".format(output))
    output.mkdir(parents=True, exist_ok=True)
    cases = [run_case(split, output, args.wind_adjustment_factor) for split in args.splits]
    receipt = {
        "kind": "simfire_real_cohort_noop_horizon_probe",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "simfire_commit": "04905b19fe8c10dc08d64faddd00303e0561bb66",
        "weather_mode": "gridmet_daily_proxy",
        "wind_adjustment_factor": args.wind_adjustment_factor,
        "max_fire_duration_updates": 15,
        "decision_minutes": 30,
        "horizon_decisions": 24,
        "maximum_simulated_hours": 12,
        "actions": "no-op only; no fireline is placed",
        "agent_training": False,
        "physical_validation": False,
        "cases": cases,
        "interpretation": "Engineering smoke only. Episode duration and simulated burned cells are outputs of this SimFire configuration, not validated predictions of the historical fires.",
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "training": False,
        "cases": [{
            "split": row["split"],
            "scenario_id": row["scenario_id"],
            "steps": len(row["transitions"]),
            "simulated_minutes": row["transitions"][-1]["info"]["simulated_minutes"],
            "burned_cells": row["transitions"][-1]["info"]["cumulative_burned_cells"],
            "terminated": row["transitions"][-1]["terminated"],
            "truncated": row["transitions"][-1]["truncated"],
        } for row in cases],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
