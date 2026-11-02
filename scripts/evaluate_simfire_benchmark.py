#!/usr/bin/env python3
"""Preflight or evaluate the frozen SimFire benchmark; this script never trains."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".local/cache"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".local/matplotlib"))
sys.path.insert(0, str(ROOT / "src"))

from wildfire_rl.simfire_evaluation import (  # noqa: E402
    DEFAULT_CONFIG,
    choose_front_edge_action,
    sha256_file,
    summarize_paired_episodes,
    select_cohort_cases,
    validate_protocol,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--split", choices=("validation", "test"), default="validation")
    parser.add_argument("--preflight-only", action="store_true",
                        help="load and hash-check one split without advancing a simulation")
    parser.add_argument("--preflight-receipt", type=Path,
                        help="also save the validation preflight receipt to a new JSON file")
    parser.add_argument("--base-checkpoint", type=Path,
                        help="trained generic SimFire PPO checkpoint; inference only")
    parser.add_argument("--fine-tuned-checkpoint", type=Path,
                        help="copy of the base checkpoint fine-tuned on TRAIN; inference only")
    parser.add_argument("--open-test", action="store_true",
                        help="explicitly authorize opening the reserved test inputs")
    parser.add_argument("--final-evaluation", action="store_true",
                        help="declare this run the final paired test evaluation")
    parser.add_argument("--out", type=Path,
                        help="new output directory; defaults under .local/simfire-benchmark-runs")
    args = parser.parse_args()
    if bool(args.base_checkpoint) != bool(args.fine_tuned_checkpoint):
        parser.error("provide both PPO checkpoints or neither")
    if args.split == "test":
        if not (args.open_test and args.final_evaluation):
            parser.error("test inputs require both --open-test and --final-evaluation")
        if args.preflight_only:
            parser.error("do not preflight/open held-out test inputs separately; use the final paired run")
        if not (args.base_checkpoint and args.fine_tuned_checkpoint):
            parser.error("the final test requires both frozen PPO checkpoints")
    elif args.open_test or args.final_evaluation:
        parser.error("--open-test and --final-evaluation are only valid with --split test")
    if args.final_evaluation and args.split != "test":
        parser.error("--final-evaluation requires --split test")
    if args.preflight_only and (args.base_checkpoint or args.fine_tuned_checkpoint):
        parser.error("preflight does not load policy checkpoints")
    if args.preflight_receipt and not args.preflight_only:
        parser.error("--preflight-receipt requires --preflight-only")
    return args


def _make_env(config: dict[str, Any], split: str, scenario_ids: list[str]):
    from wildfire_rl.simfire_gym_env import SimFireCaseEnv

    episode = config["episode"]
    cohort_path = ROOT / config["cohort_manifest"]["path"]
    cohort_manifest = cohort_path
    temporary_directory = None
    cohort = json.loads(cohort_path.read_text(encoding="utf-8"))
    all_split_ids = {
        row["scenario_id"] for row in cohort["cases"] if row["split"] == split
    }
    if set(scenario_ids) != all_split_ids:
        # The test split contains one known smoke-exposed case that must never enter
        # the final cohort. Feed SimFire a temporary metadata manifest with only the
        # frozen membership IDs; raw source manifests remain untouched.
        filtered = select_cohort_cases(cohort, split, scenario_ids)
        local_root = ROOT / ".local"
        local_root.mkdir(parents=True, exist_ok=True)
        temporary_directory = tempfile.TemporaryDirectory(
            prefix="simfire-evaluation-", dir=str(local_root)
        )
        try:
            filtered_path = Path(temporary_directory.name) / "cohort.json"
            filtered_path.write_text(json.dumps(filtered), encoding="utf-8")
            cohort_manifest = filtered_path
        except Exception:
            temporary_directory.cleanup()
            raise
    try:
        env = SimFireCaseEnv(
            split=split,
            cohort_manifest=cohort_manifest,
            weather_mode=episode["weather_mode"],
            weather_wind_adjustment_factor=episode["weather_wind_adjustment_factor"],
            fireline_budget=episode["fireline_budget"],
            decision_minutes=episode["decision_minutes"],
            horizon_decisions=episode["horizon_decisions"],
            max_fire_duration_updates=episode["max_fire_duration_updates"],
        )
    except Exception:
        if temporary_directory is not None:
            temporary_directory.cleanup()
        raise
    return env, temporary_directory


def run_preflight(protocol: dict[str, Any], split: str) -> dict[str, Any]:
    """Hash-check the chosen split and initialize one validation state, without a step."""
    if split != "validation":
        raise ValueError("preflight may inspect validation only; the held-out test stays closed")
    config = protocol["config"]
    expected_ids = protocol["membership"]["splits"][split]
    env, temporary_directory = _make_env(config, split, expected_ids)
    try:
        if set(env.scenario_ids) != set(expected_ids):
            raise ValueError("loaded scenario IDs differ from the frozen validation membership")
        scenario_id = expected_ids[0]
        observation, info = env.reset(
            seed=config["evaluation_seeds"][0], options={"scenario_id": scenario_id}
        )
        if not env.observation_space.contains(observation):
            raise ValueError("initial validation observation is outside the declared Gym space")
        masks = env.action_masks()
        if not masks[0]:
            raise ValueError("no-op is not legal during validation preflight")
        if info.get("scenario_id") != scenario_id:
            raise ValueError("environment initialized the wrong validation scenario")
        return {
            "benchmark_id": config["benchmark_id"],
            "split_checked": split,
            "scenario_count_inputs_verified": len(expected_ids),
            "initialized_scenario_id": scenario_id,
            "observation_shapes": {key: list(value.shape) for key, value in observation.items()},
            "legal_no_op": bool(masks[0]),
            "simulation_steps_advanced": 0,
            "agent_training": False,
            "test_inputs_opened": False,
            "weather_mode": config["episode"]["weather_mode"],
            "fuel_sha256": info.get("fuel_sha256"),
            "terrain_sha256": info.get("terrain_sha256"),
            "weather_mapping_sha256": info.get("weather_mapping_sha256"),
        }
    finally:
        env.close()
        if temporary_directory is not None:
            temporary_directory.cleanup()


def _load_policies(args: argparse.Namespace, env):
    if not args.base_checkpoint:
        return {}, {}
    for path in (args.base_checkpoint, args.fine_tuned_checkpoint):
        if not path.is_file():
            raise FileNotFoundError("PPO checkpoint does not exist: {}".format(path))
    from sb3_contrib import MaskablePPO

    models = {
        "base_ppo": MaskablePPO.load(str(args.base_checkpoint), env=env, device="cpu"),
        "fine_tuned_ppo": MaskablePPO.load(str(args.fine_tuned_checkpoint), env=env, device="cpu"),
    }
    hashes = {
        "base_ppo": sha256_file(args.base_checkpoint),
        "fine_tuned_ppo": sha256_file(args.fine_tuned_checkpoint),
    }
    return models, hashes


def _step_action(policy: str, observation, masks, env, model):
    if policy == "no_op":
        return 0
    if policy == "front_edge_heuristic":
        return choose_front_edge_action(observation, masks, env.rows, env.columns)
    action, _ = model.predict(observation, action_masks=masks, deterministic=True)
    action = int(action)
    if action < 0 or action >= len(masks) or not masks[action]:
        raise RuntimeError("{} selected an illegal action".format(policy))
    return action


def _run_episode(env, scenario_id: str, seed: int, policy: str, model) -> dict[str, Any]:
    observation, _ = env.reset(seed=seed, options={"scenario_id": scenario_id})
    terminated = truncated = False
    while not (terminated or truncated):
        masks = env.action_masks()
        action = _step_action(policy, observation, masks, env, model)
        observation, _, terminated, truncated, info = env.step(action)
    return {
        "scenario_id": scenario_id,
        "split": env.split,
        "seed": seed,
        "policy": policy,
        "cumulative_burned_cells": info["cumulative_burned_cells"],
        "cumulative_burned_area_ha": info["cumulative_burned_area_ha"],
        "burnable_cells": info["burnable_cells"],
        "burnable_area_fraction": (
            info["cumulative_burned_cells"] / max(1, info["burnable_cells"])
        ),
        "fireline_points_used": info["fireline_points_used"],
        "simulated_minutes": info["simulated_minutes"],
        "decision_count": info["decision"],
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "weather_mode": info["weather_mode"],
        "weather_mapping_sha256": info.get("weather_mapping_sha256"),
        "fuel_sha256": info["fuel_sha256"],
        "terrain_sha256": info["terrain_sha256"],
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("cannot write an empty episode table")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _git_metadata() -> dict[str, Any]:
    def git(*args: str):
        try:
            return subprocess.check_output(
                ["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL, text=True
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    return {
        "git_commit": git("rev-parse", "HEAD"),
        "git_dirty": bool(git("status", "--porcelain")),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }


def run_evaluation(args: argparse.Namespace, protocol: dict[str, Any]) -> dict[str, Any]:
    config = protocol["config"]
    split = args.split
    allowed_ids = protocol["membership"]["splits"][split]
    if args.out:
        output = args.out.expanduser().resolve()
    else:
        run_id = "{}-{}".format(
            split, datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        )
        output = ROOT / config["reporting"]["output_root"] / run_id
    if output.exists():
        raise FileExistsError("benchmark output already exists: {}".format(output))
    env, temporary_directory = _make_env(config, split, allowed_ids)
    try:
        if set(env.scenario_ids) != set(allowed_ids):
            raise ValueError("loaded scenario IDs differ from frozen {} membership".format(split))
        models, checkpoint_hashes = _load_policies(args, env)
        policies = ["no_op", "front_edge_heuristic"]
        if models:
            policies.extend(("base_ppo", "fine_tuned_ppo"))
        episodes = []
        for scenario_id in allowed_ids:
            for seed in config["evaluation_seeds"]:
                for policy in policies:
                    episodes.append(_run_episode(env, scenario_id, seed, policy, models.get(policy)))
        statistics = config["metrics"]["confidence_interval"]
        summary = summarize_paired_episodes(
            episodes,
            resamples=statistics["resamples"],
            seed=statistics["seed"],
        )
    finally:
        env.close()
        if temporary_directory is not None:
            temporary_directory.cleanup()

    output.mkdir(parents=True, exist_ok=False)
    _write_csv(output / "episodes.csv", episodes)
    if summary["per_incident_paired_rows"]:
        _write_csv(output / "per_incident_paired.csv", summary["per_incident_paired_rows"])
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    receipt = {
        "kind": "simfire_fpa_fod_policy_evaluation",
        "benchmark_id": config["benchmark_id"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "split": split,
        "scenario_ids": allowed_ids,
        "scenario_count": len(allowed_ids),
        "seeds": config["evaluation_seeds"],
        "policies": policies,
        "episode": config["episode"],
        "config_sha256": sha256_file(args.config),
        "membership_sha256": config["membership"]["sha256"],
        "cohort_manifest_sha256": config["cohort_manifest"]["sha256"],
        "checkpoint_sha256": checkpoint_hashes,
        "source_environment": _git_metadata(),
        "agent_training": False,
        "physical_validation": False,
        "test_inputs_opened": split == "test",
        "final_evaluation": bool(args.final_evaluation),
        "claim_scope": config["reporting"]["scientific_claim_scope"],
        "output": str(output.relative_to(ROOT)) if output.is_relative_to(ROOT) else str(output),
    }
    (output / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {"output": str(output), "episodes": len(episodes), "policies": policies,
            "summary": summary, "agent_training": False, "split": split}


def main() -> int:
    args = parse_args()
    try:
        protocol = validate_protocol(args.config, ROOT)
        if args.preflight_only:
            result = run_preflight(protocol, args.split)
            result.update({
                "kind": "simfire_benchmark_validation_preflight",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "config_sha256": sha256_file(args.config),
                "membership_sha256": protocol["config"]["membership"]["sha256"],
                "source_environment": _git_metadata(),
            })
            if args.preflight_receipt:
                receipt_path = args.preflight_receipt.expanduser().resolve()
                if receipt_path.exists():
                    raise FileExistsError("preflight receipt already exists: {}".format(receipt_path))
                receipt_path.parent.mkdir(parents=True, exist_ok=True)
                receipt_path.write_text(
                    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
                result["receipt_path"] = str(receipt_path.relative_to(ROOT)) if receipt_path.is_relative_to(ROOT) else str(receipt_path)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        print(json.dumps(run_evaluation(args, protocol), indent=2, sort_keys=True))
        return 0
    except (FileNotFoundError, OSError, ValueError, RuntimeError, KeyError) as exc:
        print("benchmark evaluation failed: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
