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
    with fiona.open(path) as source:
        source_crs = CRS.from_user_input(source.crs_wkt or source.crs or "EPSG:9311")
        target_crs = CRS.from_user_input(grid["crs"])
        project = Transformer.from_crs(source_crs, target_crs, always_xy=True).transform
        for feature in source:
            properties = feature["properties"]
            if properties.get("fireID") is None or properties.get("t") is None:
                continue
            key = (str(int(properties["fireID"])), str(properties["t"]))
            if key in wanted and feature.get("geometry"):
                geometries[key].append(
                    transform_geometry(project, shape(feature["geometry"]))
                )

    transform = Affine(*grid["raster_transform"][:6])
    target_masks = []
    for index, timestamp in enumerate(times):
        key = (fire_id, timestamp)
        parts = geometries.get(key, [])
        if not parts:
            raise ValueError(f"Missing exact-time comparison perimeter for {case['scenario_id']} at {timestamp}.")
        merged = unary_union(parts)
        mask = rasterize(
            [(merged, 1)],
            out_shape=tuple(grid["shape"]),
            transform=transform,
            fill=0,
            all_touched=True,
            dtype="uint8",
        ).astype(bool)
        if not mask.any():
            raise ValueError(f"Observed perimeter rasterized to an empty mask at {timestamp}.")
        target_masks.append({"timestamp": timestamp, "hours_since_start": 12 * index, "mask": mask})
    return target_masks


def _load_weather(case: dict, weather_path: Path) -> dict:
    weather = json.loads(weather_path.read_text(encoding="utf-8"))
    if weather.get("test_cases_loaded") is not False:
        raise ValueError("Refusing a weather file that includes test cases.")
    if weather.get("episode_manifest_sha256") != sha256_file(MANIFEST):
        raise ValueError("gridMET sample was created from a different episode manifest.")
    matches = [item for item in weather["cases"] if item["scenario_id"] == case["scenario_id"]]
    if len(matches) != 1 or matches[0].get("split") != "train":
        raise ValueError("A unique TRAIN gridMET record is required for this diagnostic.")
    if matches[0].get("initial_state_time") != case["evaluation_reference"]["initial_state_time"]:
        raise ValueError("gridMET record does not match the exact manifest start.")
    segments = matches[0]["segments"]
    if len(segments) != 4:
        raise ValueError("Expected four gridMET forcing segments for the 48-hour horizon.")
    return matches[0]


def run_episode(
    scenario_id: str,
    wind_adjustment_factor: float,
    *,
    seed: int = 0,
    internal_update_minutes: int = 5,
) -> dict:
    import numpy as np
    import rasterio
    import yaml

    from wildfire_rl.feds_spread_metrics import binary_burn_metrics
    from wildfire_rl.gridmet_weather import gridmet_proxy_to_simfire
    from wildfire_rl.simfire_initial_state import compose_initial_fire_map, update_cumulative_burned
    from wildfire_rl.simfire_timebase import updates_for_duration

    if internal_update_minutes not in {1, 3, 5, 10, 15}:
        raise ValueError("Internal SimFire update interval must be one of 1, 3, 5, 10, or 15 minutes.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("test_cases_loaded") is not False:
        raise ValueError("Refusing a manifest that includes TEST cases.")
    cases = {case["scenario_id"]: case for case in manifest["cases"]}
    if scenario_id not in cases or cases[scenario_id].get("split") != "train":
        raise ValueError("Only manifest TRAIN cases may be run for parameter calibration.")
    case = cases[scenario_id]
    weather = _load_weather(case, WEATHER)

    case_dir = INPUT_ROOT / scenario_id
    receipt_path = case_dir / "input-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("scenario_id") != scenario_id or receipt.get("split") != "train":
        raise ValueError("LANDFIRE input receipt does not match the requested TRAIN case.")
    if receipt.get("test_cases_loaded") is not False:
        raise ValueError("Input receipt must explicitly exclude TEST cases.")
    expected_time = case["evaluation_reference"]["initial_state_time"]
    if receipt.get("initial_state_time") != expected_time:
        raise ValueError("LANDFIRE/FEDS input receipt does not use the manifest start time.")

    fuel_path = case_dir / receipt["fuel"]["file"]
    terrain_path = case_dir / receipt["terrain"]["file"]
    masks_path = case_dir / receipt["initial_feds_state"]["mask_file"]
    for path, expected in (
        (fuel_path, receipt["fuel"]["sha256"]),
        (terrain_path, receipt["terrain"]["sha256"]),
        (masks_path, receipt["initial_feds_state"]["mask_sha256"]),
    ):
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"Missing or changed verified simulator input: {path}")

    with rasterio.open(fuel_path) as source:
        fuel = source.read(1)
    with rasterio.open(terrain_path) as source:
        elevation_m = source.read(1)
    with np.load(masks_path) as masks:
        scar = masks["burn_scar"].astype(bool)
        front = masks["active_front"].astype(bool)
    if fuel.shape != (256, 256) or elevation_m.shape != fuel.shape:
        raise ValueError("LANDFIRE rasters do not match the 256x256 study grid.")
    if scar.shape != fuel.shape or front.shape != fuel.shape or not front.any():
        raise ValueError("FEDS start masks are invalid.")

    forcing = []
    for segment in weather["segments"]:
        values = segment["gridmet_values"]
        forcing.append(gridmet_proxy_to_simfire(
            wind_speed_m_s=values["vs"]["value"],
            wind_from_degrees=values["th"]["value"],
            fm100_percent=values["fm100"]["value"],
            wind_adjustment_factor=wind_adjustment_factor,
        ))

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".local/mpl-cache"))
    os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".local/cache"))
    (ROOT / ".local/mpl-cache").mkdir(parents=True, exist_ok=True)
    (ROOT / ".local/cache").mkdir(parents=True, exist_ok=True)

    from simfire.enums import BurnStatus, FuelModelRGB13, FuelModelToFuel
    from simfire.game.sprites import Fire
    from simfire.sim.simulation import FireSimulation
    from simfire.utils.config import Config
    from simfire.utils.layers import OperationalFuelLayer, OperationalTopographyLayer

    unsupported = sorted(set(int(value) for value in np.unique(fuel)) - set(FuelModelToFuel))
    unsupported_rgb = sorted(set(int(value) for value in np.unique(fuel)) - set(FuelModelRGB13))
    if unsupported or unsupported_rgb:
        raise ValueError(f"Pinned SimFire cannot map LANDFIRE fuel codes: {unsupported or unsupported_rgb}.")

    base_config = yaml.safe_load(CONFIG_TEMPLATE.read_text(encoding="utf-8"))
    nominal_fire_lifetime_minutes = 90
    base_config["simulation"]["update_rate"] = internal_update_minutes
    base_config["fire"]["max_fire_duration"] = updates_for_duration(
        nominal_fire_lifetime_minutes, internal_update_minutes
    )
    rows, columns = fuel.shape
    front_rows, front_columns = np.where(front)
    base_config["fire"]["fire_initial_position"]["static"]["position"] = [
        int(front_columns[0]), int(front_rows[0])
    ]
    config = Config(config_dict=base_config)
    config.area.screen_size = (rows, columns)
    config.area.pixel_scale = 180.0 * 3.280839895
    source_layers = SimpleNamespace(layers=["fuel"], fuel=fuel, topography=elevation_m)
    config.terrain.fuel_layer = OperationalFuelLayer(source_layers)
    config.terrain.topography_layer = OperationalTopographyLayer(source_layers)
    config.wind.speed = np.full(
        (rows, columns), forcing[0]["wind_speed_midflame_ft_per_min_proxy"], dtype=np.float64
    )
    config.wind.direction = np.full(
        (rows, columns), forcing[0]["wind_direction_degrees_clockwise_north_to"], dtype=np.float64
    )
    config.environment.moisture = forcing[0]["fuel_moisture_fraction_proxy"]
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    simulation = FireSimulation(config)
    initial_map = compose_initial_fire_map(scar, front)
    simulation.fire_map = initial_map.astype(np.int64)
    simulation.fire_manager.sprites = [
        Fire((int(column), int(row)), config.display.fire_size, headless=True)
        for row, column in zip(front_rows, front_columns)
    ]
    simulation.fire_manager.durations = [0] * len(simulation.fire_manager.sprites)
    simulation.fire_sprites = simulation.fire_manager.sprites
    cumulative = update_cumulative_burned(scar, simulation.fire_map)
    if not np.array_equal(cumulative, scar | front):
        raise AssertionError("The cumulative initial scar/front masks were not preserved.")

    rollout_segments = []
    initial_mask = cumulative.copy()
    final_map = simulation.fire_map
    active = True
    for index, segment in enumerate(forcing):
        if not active:
            # Preserve the last state to the fixed 48-hour comparison horizon.
            predicted = cumulative.copy()
        else:
            simulation.fire_manager.U[:] = segment["wind_speed_midflame_ft_per_min_proxy"]
            simulation.fire_manager.U_dir[:] = segment["wind_direction_degrees_clockwise_north_to"]
            simulation.fire_manager.environment.M_f = segment["fuel_moisture_fraction_proxy"]
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
    for rollout, target in zip(rollout_segments, targets[1:]):
        score = binary_burn_metrics(
            rollout["predicted_mask"], target["mask"],
            initial_burn=initial_mask, cell_resolution_m=180.0
        )
        score.update({
            "timestamp": target["timestamp"],
            "hours_since_start": target["hours_since_start"],
            "fire_active_after_segment": rollout["fire_active_after_segment"],
            "forcing": rollout["forcing"],
        })
        metrics.append(score)

    return {
        "schema_version": "feds-simfire-noop-episode/1.0",
        "kind": "historical_weather_noop_model_diagnostic_not_physical_validation",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scenario_id": scenario_id,
        "split": "train",
        "test_cases_loaded": False,
        "scientific_result": False,
        "physical_validation": False,
        "suppression_counterfactual": False,
        "policy_input_contains_future_feds": False,
        "simfire_commit": "04905b19fe8c10dc08d64faddd00303e0561bb66",
        "horizon_hours": 48,
        "decision_step_hours": 12,
        "internal_update_minutes": internal_update_minutes,
        "nominal_active_cell_lifetime_minutes": nominal_fire_lifetime_minutes,
        "active_cell_lifetime_updates": base_config["fire"]["max_fire_duration"],
        "wind_adjustment_factor_candidate": wind_adjustment_factor,
        "wind_adjustment_factor_locked": False,
        "initial_feds_state": {
            "time": expected_time,
            "burn_scar_cells": int(scar.sum()),
            "active_front_cells": int(front.sum()),
            "input_receipt_sha256": sha256_file(receipt_path),
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
            "predicted_area_ha": round(row["predicted_area_ha"], 2),
            "observed_area_ha": round(row["observed_area_ha"], 2),
            "touches_map_edge": row["touches_map_edge"],
        } for row in result["trajectory"]],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
