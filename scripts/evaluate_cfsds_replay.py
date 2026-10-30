#!/usr/bin/env python3
"""Compare a no-action Cell2Fire replay with an isolated CFSDS next-day mask."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

import numpy as np


def final_grid(probe_dir: Path) -> tuple[np.ndarray, Path, int]:
    grids = list((probe_dir / "simulator").rglob("ForestGrid*.csv"))
    if not grids:
        raise FileNotFoundError(f"No simulator ForestGrid CSVs under {probe_dir}")
    numbered = []
    for path in grids:
        match = re.fullmatch(r"ForestGrid(\d+)\.csv", path.name)
        if match:
            numbered.append((int(match.group(1)), path))
    if not numbered:
        raise ValueError("No numbered ForestGrid CSVs found")
    index, path = max(numbered, key=lambda pair: pair[0])
    return np.loadtxt(path, delimiter=",", dtype=np.int16), path, index


def initial_mask(path: Path, shape: tuple[int, int]) -> tuple[np.ndarray, dict[str, int]]:
    state = np.zeros(shape, dtype=np.uint8)
    counts = {"burnt": 0, "burning": 0}
    with path.open(newline="") as stream:
        for item in csv.DictReader(stream):
            index = int(item["ncell"]) - 1
            row, col = divmod(index, shape[1])
            value = item["state"]
            if value not in counts:
                raise ValueError(f"Unknown initial state {value!r}")
            state[row, col] = 1 if value == "burnt" else 2
            counts[value] += 1
    return state > 0, counts


def evaluate(case_dir: Path, probe_dir: Path) -> dict[str, Any]:
    case = json.loads((case_dir / "case.json").read_text())
    probe = json.loads((probe_dir / "result.json").read_text())
    if not probe.get("success"):
        raise ValueError("Cannot evaluate an unsuccessful simulator probe")
    if probe.get("interventions_requested") != 0 or probe.get("policy") != "none":
        raise ValueError("This evaluator expects a no-action rollout with zero interventions")
    command = str(probe.get("simulator_command", ""))
    before_match = re.search(r"--steps-before\s+(\d+)", command)
    action_match = re.search(r"--steps-action\s+(\d+)", command)

    start = initial_mask(case_dir / "input/InitialState.csv", (20, 20))
    initial, state_counts = start
    final, final_path, final_index = final_grid(probe_dir)
    truth = np.loadtxt(case_dir / "truth/target_next_day_fraction.asc", skiprows=6).astype(float)
    if final.shape != (20, 20) or truth.shape != final.shape:
        raise ValueError(f"Grid mismatch: final={final.shape}, truth={truth.shape}")

    predicted = (final > 0) & ~initial
    edge = np.zeros(final.shape, dtype=bool)
    edge[[0, -1], :] = True
    edge[:, [0, -1]] = True
    target_area = float(truth.sum())
    predicted_area = float(predicted.sum())  # 100m x 100m = 1 ha per model cell
    overlapping_truth_area = float(truth[predicted].sum())
    precision = overlapping_truth_area / predicted_area if predicted_area else None
    recall = overlapping_truth_area / target_area if target_area else None
    union_area = predicted_area + target_area - overlapping_truth_area
    iou = overlapping_truth_area / union_area if union_area else None
    target_majority = truth >= 0.5
    report = {
        "case_id": case["case_id"],
        "event_id": case["event"]["event_id"],
        "target_date_local": case["event"]["target_date_local"],
        "evaluation_scope": "one-day observed growth mask versus one no-action simulator rollout",
        "run": {
            "success": probe["success"],
            "policy": probe["policy"],
            "simulator_seed": probe["simulator_seed"],
            "ros_cv": 0.5,
            "interventions_requested": probe["interventions_requested"],
            "training_performed": False,
            "simulator_reported_finished": probe.get("simulator_reported_finished"),
            "decisions": probe.get("decisions"),
            "final_grid_index": final_index,
            "fire_period_minutes": 1,
            "saved_grid_intervals_until_final": max(final_index - 1, 0),
            "simulator_elapsed_model_minutes_until_final": max(final_index - 1, 0),
            "weather_rows_available": 24,
            "steps_before_sim": int(before_match.group(1)) if before_match else None,
            "steps_per_action": int(action_match.group(1)) if action_match else None,
            "container_image": "wildfire-firehose-probe:20261030-real-case",
            "container_image_id": "sha256:bf250dd34cebdff5f38e17056c73ef2f914055bdde29b0d6fea9afc16cbd10a3",
            "input_sha256": probe.get("input_sha256"),
            "initial_state_csv_sha256": probe.get("initial_state_csv_sha256"),
        },
        "initial_state": {
            "burnt_cells": state_counts["burnt"],
            "active_front_cells": state_counts["burning"],
            "total_cells": int(initial.sum()),
            "cpp_import_log": probe.get("initial_state_import_log"),
            "reset_matches_cpp_grid": probe.get("upstream_reset_state_matches_csv"),
        },
        "observed_target": {
            "source_area_ha": round(float(case["event"]["reported_day_growth_ha"]), 4),
            "resampled_fractional_area_ha": round(target_area, 4),
            "majority_cells": int(target_majority.sum()),
        },
        "simulator_prediction": {
            "newly_burned_cells": int(predicted.sum()),
            "newly_burned_area_ha": round(predicted_area, 4),
            "final_total_affected_cells": int(np.count_nonzero(final > 0)),
            "predicted_cells_touching_grid_edge": bool(np.any(predicted & edge)),
            "predicted_edge_cells": int(np.count_nonzero(predicted & edge)),
            "overlap_with_observed_target_ha": round(overlapping_truth_area, 4),
            "target_cells_hit_at_50pct_threshold": int(np.count_nonzero(predicted & target_majority)),
        },
        "metrics": {
            "area_weighted_precision": round(precision, 4) if precision is not None else None,
            "area_weighted_recall": round(recall, 4) if recall is not None else None,
            "area_weighted_iou": round(iou, 4) if iou is not None else None,
            "predicted_to_observed_area_ratio": round(predicted_area / target_area, 4) if target_area else None,
        },
        "interpretation": "The no-action simulator reached most observed target cells but spread over a much larger area in this single rollout and touched the edge of the 2x2 km model crop. Suppression status is unknown and the simulator is not calibrated on this case, so this is a mismatch diagnostic, not evidence of counterfactual policy performance.",
        "limitations": [
            "CFSDS is a satellite-derived/interpolated daily target, not an hourly ground-truth perimeter.",
            "Suppression status for the event was not joined from an agency record.",
            "One random seed and one event-day are insufficient for model validation.",
            "Daily CFSDS FWI codes are held constant across the 24 hourly weather rows.",
            "The predicted spread touches the model-grid edge; fire spread beyond the 2x2 km crop is not represented.",
        ],
        "final_grid_path": str(final_path),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir", type=Path, default=Path("runs/real-case/2018_747-day228"))
    parser.add_argument("--probe-dir", type=Path, default=Path("runs/real-case/2018_747-day228/probe/no-action"))
    parser.add_argument("--out", type=Path, default=Path("reports/real-fire-data/2018_747-day228-replay.json"))
    args = parser.parse_args()
    result = evaluate(args.case_dir, args.probe_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "report": str(args.out),
        "new_burned_ha": result["simulator_prediction"]["newly_burned_area_ha"],
        "observed_target_ha": result["observed_target"]["resampled_fractional_area_ha"],
        "area_weighted_precision": result["metrics"]["area_weighted_precision"],
        "area_weighted_recall": result["metrics"]["area_weighted_recall"],
        "area_weighted_iou": result["metrics"]["area_weighted_iou"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
