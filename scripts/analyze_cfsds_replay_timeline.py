#!/usr/bin/env python3
"""Summarize a saved no-action CFSDS replay at fixed elapsed-time checkpoints."""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
import re
from pathlib import Path
from typing import Any, Iterable

import numpy as np


def numbered_grids(probe_dir: Path) -> dict[int, Path]:
    grids: dict[int, Path] = {}
    for path in (probe_dir / "simulator").rglob("ForestGrid*.csv"):
        match = re.fullmatch(r"ForestGrid(\d+)\.csv", path.name)
        if match:
            index = int(match.group(1))
            if index in grids:
                raise ValueError(f"Duplicate ForestGrid index {index}")
            grids[index] = path
    if not grids:
        raise FileNotFoundError(f"No numbered ForestGrid CSVs under {probe_dir / 'simulator'}")
    return grids


def command_value(command: str, option: str, default: Any, cast: type) -> Any:
    match = re.search(r"(?:^|\s)" + re.escape(option) + r"\s+([^\s]+)", command)
    return cast(match.group(1)) if match else default


def read_initial_mask(path: Path, shape: tuple[int, int]) -> np.ndarray:
    state = np.zeros(shape, dtype=bool)
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            index = int(row["ncell"]) - 1
            if not 0 <= index < state.size:
                raise ValueError(f"Initial-state cell index {index + 1} is outside {shape}")
            if row["state"] not in ("burnt", "burning"):
                raise ValueError(f"Unknown initial-state value {row['state']!r}")
            state.ravel()[index] = True
    return state


def grid_metrics(
    grid: np.ndarray,
    initial: np.ndarray,
    target_fraction: np.ndarray,
    cell_size_m: float,
) -> dict[str, Any]:
    if grid.shape != initial.shape or grid.shape != target_fraction.shape:
        raise ValueError("Simulator, initial-state and target grids must have identical shapes")
    if cell_size_m <= 0:
        raise ValueError("cell_size_m must be positive")
    predicted = (grid > 0) & ~initial
    cell_area_ha = cell_size_m * cell_size_m / 10_000.0
    target_area = float(target_fraction.sum() * cell_area_ha)
    predicted_area = float(predicted.sum() * cell_area_ha)
    overlap = float(target_fraction[predicted].sum() * cell_area_ha)
    union = predicted_area + target_area - overlap
    return {
        "predicted_new_area_ha": round(predicted_area, 4),
        "target_area_ha": round(target_area, 4),
        "overlap_with_target_ha": round(overlap, 4),
        "precision": round(overlap / predicted_area, 4) if predicted_area else None,
        "recall": round(overlap / target_area, 4) if target_area else None,
        "iou": round(overlap / union, 4) if union else None,
        "predicted_new_cells": int(predicted.sum()),
    }


def selected_timeline(
    grids: dict[int, Path], checkpoints_minutes: Iterable[int]
) -> list[dict[str, Any]]:
    checkpoints = list(checkpoints_minutes)
    if any(type(value) is not int or value < 0 for value in checkpoints):
        raise ValueError("Checkpoints must be nonnegative integer minutes")
    # Grid zero is the imported state. Each following index is one saved
    # simulator fire period; reports define elapsed minutes as index minus one.
    indexed = sorted((max(0, index - 1), index, path) for index, path in grids.items())
    selected = []
    for requested in sorted(set(checkpoints)):
        eligible = [item for item in indexed if item[0] <= requested]
        elapsed, index, _ = eligible[-1] if eligible else indexed[0]
        selected.append({
            "requested_elapsed_minutes": requested,
            "actual_elapsed_minutes": elapsed,
            "grid_index": index,
        })
    return selected


def analyze(case_dir: Path, probe_dir: Path, checkpoints_minutes: list[int]) -> dict[str, Any]:
    case = json.loads((case_dir / "case.json").read_text())
    replay = json.loads((probe_dir / "result.json").read_text())
    if replay.get("policy") != "none" or replay.get("interventions_requested") != 0:
        raise ValueError("Timeline analysis requires a no-action replay with zero interventions")
    if not replay.get("success"):
        raise ValueError("Cannot analyze an unsuccessful simulator replay")
    shape = (int(case["grid"]["rows"]), int(case["grid"]["cols"]))
    initial = read_initial_mask(case_dir / "input/InitialState.csv", shape)
    target = np.loadtxt(case_dir / "truth/target_next_day_fraction.asc", skiprows=6).astype(float)
    if target.shape != shape:
        raise ValueError(f"Target grid has shape {target.shape}, expected {shape}")
    cell_size_m = float(case["grid"]["cell_size_m"])
    paths = numbered_grids(probe_dir)
    timeline = selected_timeline(paths, checkpoints_minutes)
    for item in timeline:
        grid = np.loadtxt(paths[item["grid_index"]], delimiter=",", dtype=np.int16)
        item.update(grid_metrics(grid, initial, target, cell_size_m))
    final_index = max(paths)
    final_grid = np.loadtxt(paths[final_index], delimiter=",", dtype=np.int16)
    edge_mask = np.zeros(shape, dtype=bool)
    edge_mask[[0, -1], :] = True
    edge_mask[:, [0, -1]] = True
    new_cells = (final_grid > 0) & ~initial
    first_edge_index = None
    first_full_grid_index = None
    for index, path in sorted(paths.items()):
        snapshot = np.loadtxt(path, delimiter=",", dtype=np.int16)
        snapshot_new = (snapshot > 0) & ~initial
        if first_edge_index is None and np.any(snapshot_new & edge_mask):
            first_edge_index = index
        if first_full_grid_index is None and np.count_nonzero(snapshot > 0) == initial.size:
            first_full_grid_index = index
        if first_edge_index is not None and first_full_grid_index is not None:
            break
    command = str(replay.get("simulator_command", ""))
    fire_period_minutes = command_value(command, "--Fire-Period-Length", 1.0, float)
    weather_period_minutes = command_value(command, "--Weather-Period-Length", 60, int)
    steps_per_action = command_value(command, "--steps-action", None, int)
    ros_cv = command_value(command, "--ROS-CV", None, float)
    weather_rows = int(case["sources"]["weather"]["rows_for_target_day"])
    return {
        "schema_version": "cfsds-no-action-timeline-1.0",
        "analysis_scope": "train-only diagnostic of saved no-action snapshots; not calibration or policy evaluation",
        "event_id": case["event"]["event_id"],
        "case_id": case["case_id"],
        "target_date_local": case["event"]["target_date_local"],
        "input_provenance": {
            "case_manifest_sha256": sha256((case_dir / "case.json").read_bytes()).hexdigest(),
            "cfsds_arrival_archive_sha256": case["sources"]["cfsds_arrival_raster"]["sha256"],
            "cfsds_daily_summary_archive_sha256": case["sources"]["cfsds_daily_summary"]["sha256"],
            "fuel_map_sha256": case["sources"]["fuel_map"]["sha256"],
            "simulator_lookup_sha256": case["sources"]["simulator_lookup"]["sha256"],
            "weather_sha256": case["sources"]["weather"]["raw_sha256"],
            "simulator_input_sha256": replay.get("input_sha256"),
            "initial_state_csv_sha256": replay.get("initial_state_csv_sha256"),
            "container_image_id": replay.get("container_image_id"),
        },
        "replay": {
            "policy": replay["policy"],
            "simulator_seed": replay.get("simulator_seed"),
            "ros_cv": ros_cv,
            "fire_period_minutes": fire_period_minutes,
            "steps_per_action": steps_per_action,
            "weather_rows": weather_rows,
            "weather_period_minutes": weather_period_minutes,
            "weather_horizon_minutes": weather_period_minutes * weather_rows,
            "final_grid_index": final_index,
            "final_elapsed_minutes": max(0, final_index - 1),
            "first_predicted_grid_edge_index": first_edge_index,
            "first_predicted_grid_edge_elapsed_minutes": (
                max(0, first_edge_index - 1) if first_edge_index is not None else None
            ),
            "first_fully_affected_grid_index": first_full_grid_index,
            "first_fully_affected_grid_elapsed_minutes": (
                max(0, first_full_grid_index - 1) if first_full_grid_index is not None else None
            ),
            "predicted_edge_cells": int(np.count_nonzero(new_cells & edge_mask)),
            "predicted_new_edge_touched": bool(np.any(new_cells & edge_mask)),
            "final_total_affected_cells": int(np.count_nonzero(final_grid > 0)),
            "final_active_cells": int(np.count_nonzero(final_grid == 2)),
            "final_unburned_cells": int(np.count_nonzero(final_grid == 0)),
        },
        "fixed_checkpoints": timeline,
        "interpretation": (
            "Saved checkpoints show timing sensitivity: area and precision change as the model advances. "
            "The CFSDS target is a daily satellite-interpolated mask without an observed within-day fire time, "
            "so these checkpoints diagnose mismatch and do not identify a correct stopping time."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--probe-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--checkpoints-minutes", default="30,60,120,240,480,720,1440",
        help="comma-separated elapsed-minute checkpoints (default: %(default)s)",
    )
    args = parser.parse_args()
    try:
        checkpoints = [int(value) for value in args.checkpoints_minutes.split(",")]
    except ValueError:
        parser.error("--checkpoints-minutes must be comma-separated integers")
    result = analyze(args.case_dir, args.probe_dir, checkpoints)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "event_id": result["event_id"],
        "final_elapsed_minutes": result["replay"]["final_elapsed_minutes"],
        "checkpoints": [
            {k: item[k] for k in (
                "requested_elapsed_minutes", "actual_elapsed_minutes", "predicted_new_area_ha", "iou"
            )}
            for item in result["fixed_checkpoints"]
        ],
        "out": str(args.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
