#!/usr/bin/env python3
"""Run one 48-hour historical-weather SimFire no-op case against FEDS outlines.

Future FEDS perimeters are loaded after the simulator run solely to score it. They
are never passed into SimFire or the policy. The command is an input/model diagnostic,
not physical validation and not a suppression counterfactual.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifests/feds-episode-cohort-v1.json"
PREFLIGHT = ROOT / "reports/real-fire-data/feds-simfire-grid-preflight-v1.json"
WEATHER = ROOT / ".local/gridmet/feds-episode-weather-v1.json"
INPUT_ROOT = ROOT / ".local/feds-simfire-cases"
OUTPUT_ROOT = ROOT / ".local/feds-noop-diagnostics"
CONFIG_TEMPLATE = ROOT / "configs/simfire_feds_base.yml"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_observed_timeline(case: dict, grid: dict) -> list[dict[str, Any]]:
    """Load and rasterize only the five documented comparison timestamps."""
    import fiona
    import numpy as np
    from affine import Affine
    from pyproj import CRS, Transformer
    from rasterio.features import rasterize
    from rasterio.transform import array_bounds
    from rasterio.warp import transform_bounds
    from shapely.geometry import shape
    from shapely.ops import transform as transform_geometry, unary_union

    try:
        from scripts.audit_feds_fpa_fle_crosswalk import _feds_file_path
    except ModuleNotFoundError:
        sys.path.insert(0, str(ROOT / "scripts"))
        from audit_feds_fpa_fle_crosswalk import _feds_file_path

    reference = case["evaluation_reference"]
    year = int(case["event"]["year"])
    fire_id = str(int(reference["source_fire_id"]))
    times = reference["observed_state_times_0_to_48h"]
    if len(times) != 5:
        raise ValueError("Expected five exact FEDS states from start through +48 hours.")
    wanted = {(fire_id, timestamp) for timestamp in times}
    geometries: dict[tuple[str, str], list] = {key: [] for key in wanted}
    path = Path(_feds_file_path(year, "perimeter"))
    transform = Affine(*grid["raster_transform"][:6])
    height, width = (int(value) for value in grid["shape"])
    target_bounds = array_bounds(height, width, transform)
    target_crs = CRS.from_user_input(grid["crs"])
    # FlatGeobuf has a spatial index. Restrict the query to this episode grid;
    # iterating the whole annual CONUS layer made each TRAIN case scan hundreds
    # of megabytes even though only a few local perimeters can be relevant.
    target_masks = []
    with fiona.open(path) as source:
        source_crs = CRS.from_user_input(source.crs_wkt or source.crs or "EPSG:9311")
        source_bounds = transform_bounds(
            target_crs.to_wkt(), source_crs.to_wkt(), *target_bounds, densify_pts=21
        )
        project = Transformer.from_crs(source_crs, target_crs, always_xy=True).transform
        for feature in source.filter(bbox=source_bounds):
            properties = feature["properties"]
            if properties.get("fireID") is None or properties.get("t") is None:
                continue
            key = (str(int(properties["fireID"])), str(properties["t"]))
            if key in wanted and feature.get("geometry"):
                geometries[key].append(
                    transform_geometry(project, shape(feature["geometry"]))
                )

    for index, timestamp in enumerate(times):
        key = (fire_id, timestamp)
        parts = geometries.get(key, [])
        if not parts:
            raise ValueError(f"Missing exact-time comparison perimeter for {case['scenario_id']} at {timestamp}.")
        merged = unary_union(parts)
        mask = rasterize(
            [(merged, 1)],
            out_shape=(height, width),
            transform=transform,
            fill=0,
            all_touched=True,
            dtype="uint8",
        ).astype(bool)
        if not mask.any():
            raise ValueError(f"Observed perimeter rasterized to an empty mask at {timestamp}.")
        target_masks.append({"timestamp": timestamp, "hours_since_start": 12 * index, "mask": mask})
    return target_masks


def run_episode(
    scenario_id: str,
    wind_adjustment_factor: float,
    *,
    seed: int = 0,
    internal_update_minutes: int = 5,
    active_cell_lifetime_minutes: int = 90,
    ros_multiplier: float = 1.0,
    split: str = "train",
) -> dict:
    """Simulate one 48h no-op case; VALIDATION must be requested explicitly."""
    import numpy as np

    from wildfire_rl.feds_simfire_setup import (
        SimFireParams,
        apply_forcing,
        build_simulation,
        load_case_inputs,
    )
    from wildfire_rl.feds_spread_metrics import (
        ELLIPSE_REFERENCE_PROTOCOL,
        METRICS_VERSION,
        binary_burn_metrics,
        ellipse_ignition_point,
        elliptical_growth_reference,
    )
    from wildfire_rl.simfire_initial_state import update_cumulative_burned

    params = SimFireParams(
        wind_adjustment_factor=wind_adjustment_factor,
        internal_update_minutes=internal_update_minutes,
        active_cell_lifetime_minutes=active_cell_lifetime_minutes,
        ros_multiplier=ros_multiplier,
    )
    inputs = load_case_inputs(scenario_id, split=split, manifest_path=MANIFEST,
                              weather_path=WEATHER, input_root=INPUT_ROOT)
    case = inputs["case"]
    receipt = inputs["receipt"]
    scar = inputs["scar"]
    front = inputs["front"]
    expected_time = case["evaluation_reference"]["initial_state_time"]
    front_rows, front_columns = np.where(front)
    simulation, forcing, cumulative = build_simulation(inputs, params, seed=seed)

    rollout_segments = []
    initial_mask = cumulative.copy()
    active = True
    for segment in forcing:
        if not active:
            # Preserve the last state to the fixed 48-hour comparison horizon.
            predicted = cumulative.copy()
        else:
            apply_forcing(simulation, segment)
            final_map, active = simulation.run("12h")
            cumulative = update_cumulative_burned(cumulative, final_map)
            predicted = cumulative
        rollout_segments.append({
            "predicted_mask": predicted.copy(),
            "fire_active_after_segment": bool(active),
            "forcing": {
                "wind_speed_proxy_ft_per_min": segment["wind_speed_midflame_ft_per_min_proxy"],
                "wind_direction_degrees_clockwise_north_to": segment["wind_direction_degrees_clockwise_north_to"],
                "fuel_moisture_fraction_proxy": segment["fuel_moisture_fraction_proxy"],
            },
        })

    # Future FEDS geometry is opened only after all simulator updates are complete.
    targets = load_observed_timeline(case, receipt["grid"])
    if targets[0]["timestamp"] != expected_time:
        raise AssertionError("The first evaluation reference is not the imported initial state.")
    metrics = []
    ellipse_heading = forcing[0]["wind_direction_degrees_clockwise_north_to"]
    ignition_row, ignition_column = ellipse_ignition_point(front, ellipse_heading)
    for rollout, target in zip(rollout_segments, targets[1:]):
        score = binary_burn_metrics(
            rollout["predicted_mask"], target["mask"],
            initial_burn=initial_mask, cell_resolution_m=180.0
        )
        persistence = binary_burn_metrics(
            initial_mask, target["mask"],
            initial_burn=initial_mask, cell_resolution_m=180.0
        )
        ellipse_mask = elliptical_growth_reference(
            initial_mask,
            center_row=ignition_row,
            center_column=ignition_column,
            hours=target["hours_since_start"],
            downwind_degrees=ellipse_heading,
            cell_resolution_m=180.0,
        )
        ellipse = binary_burn_metrics(
            ellipse_mask, target["mask"],
            initial_burn=initial_mask, cell_resolution_m=180.0
        )
        score.update({
            "timestamp": target["timestamp"],
            "hours_since_start": target["hours_since_start"],
            "fire_active_after_segment": rollout["fire_active_after_segment"],
            "forcing": rollout["forcing"],
            "persistence_reference": persistence,
            "ellipse_reference": ellipse,
        })
        metrics.append(score)

    return {
        "schema_version": "feds-simfire-noop-episode/1.1",
        "kind": "historical_weather_noop_model_diagnostic_not_physical_validation",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scenario_id": scenario_id,
        "split": split,
        "test_cases_loaded": False,
        "scientific_result": False,
        "physical_validation": False,
        "suppression_counterfactual": False,
        "policy_input_contains_future_feds": False,
        "simfire_commit": "04905b19fe8c10dc08d64faddd00303e0561bb66",
        "horizon_hours": 48,
        "decision_step_hours": 12,
        "internal_update_minutes": internal_update_minutes,
        "nominal_active_cell_lifetime_minutes": active_cell_lifetime_minutes,
        "active_cell_lifetime_updates": simulation.fire_manager.max_fire_duration,
        "simfire_params": params.as_dict(),
        "wind_adjustment_factor_candidate": wind_adjustment_factor,
        "wind_adjustment_factor_locked": False,
        "baseline_protocol": {
            "persistence": "The initial FEDS burn-scar plus active-front mask is held unchanged through each horizon.",
            "ellipse": ELLIPSE_REFERENCE_PROTOCOL,
            "growth_metrics": "growth_* fields score only cells outside the initial mask; None where the denominator is empty",
        },
        "metrics_version": METRICS_VERSION,
        "initial_feds_state": {
            "time": expected_time,
            "burn_scar_cells": int(scar.sum()),
            "active_front_cells": int(front.sum()),
            "input_receipt_sha256": inputs["receipt_sha256"],
        },
        "weather_source": {
            "dataset": "gridMET daily ex-post forcing",
            "sample_sha256": sha256_file(WEATHER),
            "agent_observation": "future 12-hour forcing is not exposed to a policy",
            "wind_adjustment_factor": "provisional diagnostic value; no train/validation selection has occurred",
        },
        "trajectory": metrics,
        "limitations": [
            "gridMET 10m wind and 100h fuel moisture are coarse proxy inputs, not measurements of SimFire midflame wind or fine-fuel moisture.",
            "FEDS comparison perimeters are satellite-derived estimates, not ground truth.",
            "This single no-op case cannot calibrate shared parameters or establish an agent benchmark.",
            "No line construction or suppression action was simulated.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--wind-adjustment-factor", type=float, required=True)
    parser.add_argument("--internal-update-minutes", type=int, choices=(1, 3, 5, 10, 15), default=5)
    parser.add_argument("--active-cell-lifetime-minutes", type=int, default=90)
    parser.add_argument("--ros-multiplier", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if not 0.0 <= args.wind_adjustment_factor <= 1.0:
        parser.error("wind-adjustment-factor must be in [0,1].")
    try:
        result = run_episode(
            args.scenario_id,
            args.wind_adjustment_factor,
            seed=args.seed,
            internal_update_minutes=args.internal_update_minutes,
            active_cell_lifetime_minutes=args.active_cell_lifetime_minutes,
            ros_multiplier=args.ros_multiplier,
        )
    except Exception as exc:
        print(f"FEDS historical no-op failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    output = args.out or OUTPUT_ROOT / args.scenario_id / (
        f"step-{args.internal_update_minutes}m-waf-{args.wind_adjustment_factor:g}-seed-{args.seed}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "scenario_id": result["scenario_id"],
        "split": result["split"],
        "wind_adjustment_factor_candidate": result["wind_adjustment_factor_candidate"],
        "trajectory": [{
            "hours_since_start": row["hours_since_start"],
            "iou": round(row["iou"], 4),
            "growth_iou": None if row["growth_iou"] is None else round(row["growth_iou"], 4),
            "observed_growth_cells": row["observed_growth_cells"],
            "predicted_growth_cells": row["predicted_growth_cells"],
            "predicted_area_ha": round(row["predicted_area_ha"], 2),
            "observed_area_ha": round(row["observed_area_ha"], 2),
            "touches_map_edge": row["touches_map_edge"],
        } for row in result["trajectory"]],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
