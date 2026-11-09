#!/usr/bin/env python3
"""Calibration gap of the synthetic CA on real FEDS starts (ADR-028 diagnostic).

For each case the synthetic CA runs a no-op (no units) for 48 decisions of 60 min from
the observed FEDS initial state, under the same EpisodeSpec the real-case test uses.
Simulated ever-burned area is compared with the observed FEDS perimeters at 12/24/36/48h
inside the same 128x128 crop. Future FEDS geometry is opened only after the rollout.

This is reported, never used as a gate or for tuning. Run it on all cases only after the
policy is locked (``--all --policy-locked``); otherwise name cases with ``--scenario-id``.
TEST cases are never loaded.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

CHECK_HOURS = (12, 24, 36, 48)


def noop_snapshots(spec, hours=CHECK_HOURS) -> Dict[int, "np.ndarray"]:
    """Ever-burned masks of the env's no-op rollout (same weather, seed and CRN)."""
    from wildfire_rl.synthetic_ca import initial_state_from_masks
    from wildfire_rl.synthetic_env import SUBSTEPS_PER_DECISION

    fire = initial_state_from_masks(spec.landscape, spec.seed, spec.params, spec.scar, spec.front)
    snapshots = {}
    for index in range(max(hours)):
        fire.set_weather(spec.weather.at(index))
        for _ in range(SUBSTEPS_PER_DECISION):
            fire.step_substep()
        if index + 1 in hours:
            snapshots[index + 1] = fire.ever_burned.copy()
    return snapshots


def diagnose_case(inputs: dict, verify_env: bool = False) -> dict:
    import numpy as np

    from run_feds_noop_episode import load_observed_timeline
    from wildfire_rl.feds_spread_metrics import binary_burn_metrics
    from wildfire_rl.synthetic_real_cases import CROP, build_real_episode

    spec, meta = build_real_episode(inputs)
    initial = spec.scar | spec.front
    snapshots = noop_snapshots(spec)
    env_check = None
    if verify_env:
        from wildfire_rl.synthetic_env import TAIL_DECISIONS, SyntheticSuppressionEnv

        env = SyntheticSuppressionEnv(episode_specs=[spec])
        env.reset(options={"episode_spec": spec})
        # The env's no-op runs horizon + tail decisions; this rollout must end identically.
        end = spec.horizon + TAIL_DECISIONS
        check = noop_snapshots(spec, hours=(end,))[end]
        env_check = bool(np.array_equal(check, env.noop_final.ever_burned))

    # Future FEDS perimeters are loaded only now, to score the finished rollout.
    targets = load_observed_timeline(inputs["case"], inputs["receipt"]["grid"])
    r0, c0 = meta["crop_offset_row"], meta["crop_offset_col"]
    window = (slice(r0, r0 + CROP), slice(c0, c0 + CROP))
    observed0 = targets[0]["mask"][window]
    rows = []
    for target in targets[1:]:
        hours = int(target["hours_since_start"])
        full = target["mask"]
        observed = full[window]
        predicted = snapshots[hours] | initial
        row = {"hours_since_start": hours, "timestamp": target["timestamp"],
               "observed_cells_outside_crop": int(full.sum() - observed.sum())}
        if observed.any():
            score = binary_burn_metrics(predicted, observed, initial_burn=initial)
            sim_new = int((predicted & ~initial).sum())
            obs_new = int((observed & ~initial).sum())
            row.update({
                "iou": score["iou"],
                "growth_iou": score["growth_iou"],
                "growth_precision": score["growth_precision"],
                "growth_recall": score["growth_recall"],
                "sim_cells": score["predicted_burned_cells"],
                "obs_cells": score["observed_burned_cells"],
                "area_ratio_sim_over_obs": score["predicted_burned_cells"] / score["observed_burned_cells"],
                "sim_new_cells": sim_new,
                "obs_new_cells": obs_new,
                "growth_vs_observed": ("less" if sim_new < obs_new else
                                       "more" if sim_new > obs_new else "equal"),
                "sim_touches_crop_edge": score["touches_map_edge"],
            })
        rows.append(row)
    return {
        "scenario_id": meta["scenario_id"],
        "split": meta["split"],
        "metadata": meta,
        "observed_initial_cells_in_crop": int(observed0.sum()),
        "env_noop_matches": env_check,
        "trajectory": rows,
    }


def aggregate(results: List[dict]) -> dict:
    summary = {}
    for split in ("train", "validation"):
        cases = [case for case in results if case["split"] == split]
        per_hour = {}
        for hours in CHECK_HOURS:
            rows = [row for case in cases for row in case["trajectory"]
                    if row["hours_since_start"] == hours and "iou" in row]
            ratios = [row["area_ratio_sim_over_obs"] for row in rows]
            ious = [row["iou"] for row in rows]
            # Growth IoU is defined on every case where FEDS grew; stalled cases are counted.
            growth_ious = [row["growth_iou"] for row in rows if row["obs_new_cells"] > 0]
            per_hour[str(hours)] = {
                "scored_cases": len(rows),
                "median_area_ratio_sim_over_obs": statistics.median(ratios) if ratios else None,
                "median_iou": statistics.median(ious) if ious else None,
                "growing_cases": len(growth_ious),
                "median_growth_iou": statistics.median(growth_ious) if growth_ious else None,
                "stalled_cases_sim_grows": sum(
                    row["obs_new_cells"] == 0 and row["sim_new_cells"] > 0 for row in rows),
                "share_sim_grows_less": (sum(r["growth_vs_observed"] == "less" for r in rows)
                                         / len(rows)) if rows else None,
                "share_sim_grows_more": (sum(r["growth_vs_observed"] == "more" for r in rows)
                                         / len(rows)) if rows else None,
                "share_equal_growth": (sum(r["growth_vs_observed"] == "equal" for r in rows)
                                       / len(rows)) if rows else None,
                "cases_with_observed_outside_crop": sum(
                    row["observed_cells_outside_crop"] > 0 for row in rows),
            }
        summary["ex_" + split] = {"cases": len(cases), "by_hour": per_hour}
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario-id", action="append", default=[],
                        help="TRAIN/VALIDATION scenario to diagnose (repeatable)")
    parser.add_argument("--all", action="store_true", help="diagnose all 119 cases")
    parser.add_argument("--policy-locked", action="store_true",
                        help="required with --all: confirms the policy is already locked")
    parser.add_argument("--verify-env", action="store_true",
                        help="also check the rollout against SyntheticSuppressionEnv's no-op")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.all == bool(args.scenario_id):
        parser.error("give either --scenario-id ... or --all")
    if args.all and not args.policy_locked:
        parser.error("--all needs --policy-locked; the full gap is run once, after locking")

    from wildfire_rl.feds_simfire_setup import (load_case_inputs, load_split_cases,
                                                load_weather_records)

    wanted = set(args.scenario_id)
    results = []
    for split in ("train", "validation"):
        cases = load_split_cases(split)
        records = load_weather_records(split)
        for scenario_id in cases:
            if not args.all and scenario_id not in wanted:
                continue
            inputs = load_case_inputs(scenario_id, split=split, cases=cases,
                                      weather_records=records)
            results.append(diagnose_case(inputs, verify_env=args.verify_env))
            wanted.discard(scenario_id)
    if wanted:
        parser.error("not TRAIN/VALIDATION manifest cases: %s" % sorted(wanted))

    report = {
        "schema_version": "synthetic-ca-calibration-gap/1.0",
        "kind": "synthetic_ca_noop_vs_feds_growth_diagnostic_not_a_gate",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "test_cases_loaded": False,
        "full_cohort": bool(args.all),
        "physical_validation": False,
        "used_for_tuning": False,
        "protocol": {
            "simulator": "wildfire_rl.synthetic_ca, SpreadParams() defaults, no units",
            "decision_minutes": 60, "check_hours": list(CHECK_HOURS),
            "crop": "128x128 centred on the initial burn_scar|active_front centroid",
            "predicted_mask": "simulated ever-burned | initial scar/front, inside the crop",
            "observed_mask": "FEDS lf_perimeter rasterized all_touched on the 180 m grid, cropped",
            "growth_vs_observed": "new cells beyond the initial mask, sim vs observed",
            "growth_iou": "IoU/precision/recall on cells outside the initial mask; None where "
                          "the denominator is empty; medians only over cases where FEDS grew",
        },
        "summary": aggregate(results),
        "cases": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.out), "cases": [
        {"scenario_id": case["scenario_id"], "split": case["split"],
         "env_noop_matches": case["env_noop_matches"],
         "observed_initial_cells_in_crop": case["observed_initial_cells_in_crop"],
         "initial_burned_cells": case["metadata"]["initial_burned_cells"],
         "trajectory": [{key: (round(value, 3) if isinstance(value, float) else value)
                         for key, value in row.items() if key != "timestamp"}
                        for row in case["trajectory"]]}
        for case in results]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
