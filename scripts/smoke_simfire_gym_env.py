#!/usr/bin/env python3
"""Run one short, non-training Gymnasium/SimFire smoke in each data split."""

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
from wildfire_rl.simfire_policy import simfire_policy_kwargs


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
    axes[1].set_title("SimFire state after action")
    axes[1].set_xlabel("Grid column (30 m)")
    axes[1].set_ylabel("Grid row")
    fig.colorbar(second, ax=axes[1], shrink=0.8, ticks=range(6), label="0 unburned, 3 fireline")
    fig.suptitle("{} — {}; smoke only".format(
        env._case["manifest"]["scenario_id"], env.weather_mode
    ))
    fig.savefig(path, dpi=140)
    plt.close(fig)


def run_split(
    split: str,
    output: Path,
    weather_mode: str,
    wind_adjustment_factor: float | None,
    decision_minutes: int,
    horizon_decisions: int,
) -> dict:
    env = SimFireCaseEnv(
        split=split,
        fireline_budget=1,
        decision_minutes=decision_minutes,
        horizon_decisions=horizon_decisions,
        weather_mode=weather_mode,
        weather_wind_adjustment_factor=wind_adjustment_factor,
    )
    scenario_id = env.scenario_ids[0]
    observation, reset_info = env.reset(seed=20261101, options={"scenario_id": scenario_id})
    if not env.observation_space.contains(observation):
        raise RuntimeError("Gymnasium observation is outside the declared space")
    masks = env.action_masks()
    if not masks[0] or not masks[1:].any():
        raise RuntimeError("Expected no-op and at least one legal fireline point")
    policy_probe = None
    if split == "train":
        from sb3_contrib import MaskablePPO

        # Instantiate and infer once, but do not call learn() or update any weights.
        model = MaskablePPO(
            "MultiInputPolicy", env, n_steps=64, batch_size=64, n_epochs=1,
            policy_kwargs=simfire_policy_kwargs(), device="cpu", seed=7, verbose=0,
        )
        predicted, _ = model.predict(observation, action_masks=masks, deterministic=True)
        policy_probe = {
            "algorithm": "MaskablePPO",
            "policy": "MultiInputPolicy",
            "learn_called": False,
            "predicted_action": int(predicted),
            "predicted_action_was_legal": bool(masks[int(predicted)]),
        }
        if not masks[int(predicted)]:
            raise RuntimeError("MaskablePPO selected a masked action")
    seed_row, seed_column = [int(value) for value in env._case["manifest"]["fire_behavior"]["seed_cell"]]
    legal_cells = np.argwhere(masks[1:].reshape(env.rows, env.columns))
    distances = np.abs(legal_cells[:, 0] - seed_row) + np.abs(legal_cells[:, 1] - seed_column)
    row, column = [int(value) for value in legal_cells[int(np.argmin(distances))]]
    line_action = 1 + row * env.columns + column
    transitions = []
    terminated = False
    truncated = False
    while not (terminated or truncated):
        if transitions:
            masks_after_budget = env.action_masks()
            if not masks_after_budget[0] or masks_after_budget[1:].any():
                raise RuntimeError("After spending the one-point budget, only no-op should remain")
            action = 0
            action_name = "no_op_after_budget_exhausted"
            action_row = action_column = None
        else:
            action = line_action
            action_name = "place_one_30m_fireline_point"
            action_row, action_column = row, column
        observation, reward, terminated, truncated, step_info = env.step(action)
        transition = {
            "action": action_name,
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
            "info": step_info,
        }
        if action_row is not None:
            transition.update({"row": action_row, "column": action_column})
        transitions.append(transition)
    case_name = scenario_id.replace("/", "-")
    image_path = output / "{}-{}.png".format(split, case_name)
    save_map(env, observation, image_path)
    env.close()
    return {
        "split": split,
        "scenario_id": scenario_id,
        "scenario_manifest": env._case["manifest_path"].relative_to(ROOT).as_posix(),
        "reset_info": reset_info,
        "transitions": transitions,
        "observation_shapes": {key: list(value.shape) for key, value in observation.items()},
        "gym_observation_space_contains_final": env.observation_space.contains(observation),
        "action_count": env.action_space.n,
        "policy_probe": policy_probe,
        "visual": image_path.relative_to(ROOT).as_posix(),
    }


def json_default(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError("Cannot serialize {}".format(type(value).__name__))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "reports/real-fire-data/simfire-cohort-v2-gym-smoke")
    parser.add_argument("--weather-mode", choices=("demonstration_only", "gridmet_daily_proxy"), default="demonstration_only")
    parser.add_argument("--wind-adjustment-factor", type=float, help="override the proxy WAF for sensitivity smoke (0.1–0.5)")
    parser.add_argument("--decision-minutes", type=int, default=10)
    parser.add_argument("--horizon-decisions", type=int, default=2)
    args = parser.parse_args()
    if args.decision_minutes < 1 or args.horizon_decisions < 1:
        parser.error("decision minutes and horizon decisions must be positive")
    output = args.out.expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Output directory is not empty: {}".format(output))
    output.mkdir(parents=True, exist_ok=True)
    splits = [
        run_split(split, output, args.weather_mode, args.wind_adjustment_factor,
                  args.decision_minutes, args.horizon_decisions)
        for split in ("train", "validation", "test")
    ]
    receipt = {
        "kind": "simfire_gymnasium_real_cohort_integration_smoke",
        "scientific_result": False,
        "physical_validation": False,
        "agent_training": False,
        "weather_mode": args.weather_mode,
        "historical_weather_context_used": args.weather_mode == "gridmet_daily_proxy",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "simfire_commit": "04905b19fe8c10dc08d64faddd00303e0561bb66",
        "adapter": "src/wildfire_rl/simfire_gym_env.py",
        "line_budget_per_episode": 1,
        "decision_minutes": args.decision_minutes,
        "horizon_decisions": args.horizon_decisions,
        "maximum_episode_hours": args.decision_minutes * args.horizon_decisions / 60.0,
        "atmosphere": {
            "mode": args.weather_mode,
            "warning": "Daily proxy mode uses explicit assumptions; it is not an hourly event replay or measured midflame weather." if args.weather_mode == "gridmet_daily_proxy" else "These settings are temporary SimFire examples and are not derived from the historical cases.",
            "wind_adjustment_factor_override": args.wind_adjustment_factor,
        },
        "splits": splits,
        "limitations": [
            "This confirms the data-to-SimFire-to-Gymnasium interface only; it is not an RL training run.",
            "Daily gridMET is used only when gridmet_daily_proxy is selected; the default smoke remains demonstration_only.",
            "A fireline action places one 30 m grid point instantly anywhere on the map; crew travel and construction time are omitted.",
            "Reported FPA-FOD incident coordinates are uncertain references, not GPS-confirmed ignition cells.",
        ],
    }
    (output / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True, default=json_default) + "\n", encoding="utf-8"
    )
    print(json.dumps({"output": str(output), "case_count": len(splits), "training": False,
                      "weather_mode": args.weather_mode, "visuals": [row["visual"] for row in splits]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
