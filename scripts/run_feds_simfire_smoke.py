#!/usr/bin/env python3
"""Run a short no-action SimFire integration smoke from one verified FEDS start.

This checks the installed simulator against real 180 m LANDFIRE fuel/terrain and
the same-time multi-cell FEDS scar/front. The default wind/moisture are explicitly
demonstration values; this is not the gridMET no-op gate or physical validation.
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
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SIMFIRE_COMMIT = "04905b19fe8c10dc08d64faddd00303e0561bb66"
MANIFEST = ROOT / "data/manifests/feds-episode-cohort-v1.json"
INPUT_ROOT = ROOT / ".local/feds-simfire-cases"
OUTPUT_ROOT = ROOT / ".local/simfire-noop-smoke"
CONFIG_TEMPLATE = ROOT / "configs/simfire_feds_base.yml"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_smoke(scenario_id: str, minutes: int, seed: int, output_root: Path) -> dict:
    import numpy as np
    import rasterio
    import yaml

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("test_cases_loaded") is not False:
        raise ValueError("Refusing a manifest that has loaded TEST cases.")
    cases = {case["scenario_id"]: case for case in manifest["cases"]}
    if scenario_id not in cases:
        raise ValueError(f"Unknown train/validation scenario_id: {scenario_id}")
    case = cases[scenario_id]
    if case["split"] != "train":
        raise ValueError("The one-case smoke is restricted to TRAIN scenarios.")

    case_dir = INPUT_ROOT / scenario_id
    receipt_path = case_dir / "input-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("scenario_id") != scenario_id or receipt.get("test_cases_loaded") is not False:
        raise ValueError("Input receipt does not match the requested train scenario.")
    expected_time = case["evaluation_reference"]["initial_state_time"]
    if receipt.get("initial_state_time") != expected_time:
        raise ValueError("Input receipt does not use the exact manifest initial-state timestamp.")

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

    with rasterio.open(fuel_path) as src:
        fuel = src.read(1)
    with rasterio.open(terrain_path) as src:
        elevation_m = src.read(1)
    with np.load(masks_path) as masks:
        scar = masks["burn_scar"].astype(bool)
        front = masks["active_front"].astype(bool)
    if fuel.shape != (256, 256) or elevation_m.shape != fuel.shape:
        raise ValueError("Input rasters do not match the 256x256 study grid.")
    if scar.shape != fuel.shape or front.shape != fuel.shape or not front.any():
        raise ValueError("FEDS mask dimensions/front are invalid.")

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
    from wildfire_rl.simfire_initial_state import compose_initial_fire_map, update_cumulative_burned

    unmapped = sorted(set(int(value) for value in np.unique(fuel)) - set(FuelModelToFuel))
    unmapped_rgb = sorted(set(int(value) for value in np.unique(fuel)) - set(FuelModelRGB13))
    if unmapped or unmapped_rgb:
        raise ValueError(f"Pinned SimFire cannot map these LANDFIRE fuel codes: {unmapped or unmapped_rgb}.")

    base_config = yaml.safe_load(CONFIG_TEMPLATE.read_text(encoding="utf-8"))
    rows, columns = fuel.shape
    active_rows, active_columns = np.where(front)
    seed_row, seed_column = int(active_rows[0]), int(active_columns[0])
    base_config["fire"]["fire_initial_position"]["static"]["position"] = [seed_column, seed_row]
    config = Config(config_dict=base_config)
    # SimFire 2.0.1 compares ndarray shapes (tuples) directly with screen_size;
    # keep this tuple-shaped to avoid its list/tuple equality mismatch.
    config.area.screen_size = (rows, columns)
    config.area.pixel_scale = 180.0 * 3.280839895
    source_layers = SimpleNamespace(layers=["fuel"], fuel=fuel, topography=elevation_m)
    config.terrain.fuel_layer = OperationalFuelLayer(source_layers)
    config.terrain.topography_layer = OperationalTopographyLayer(source_layers)
    config.wind.speed = np.full((rows, columns), 7.0 * 88.0, dtype=np.float64)
    config.wind.direction = np.full((rows, columns), 90.0, dtype=np.float64)
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    simulation = FireSimulation(config)
    initial_map = compose_initial_fire_map(scar, front)
    simulation.fire_map = initial_map.astype(np.int64)
    simulation.fire_manager.sprites = [
        Fire((int(column), int(row)), config.display.fire_size, headless=True)
        for row, column in zip(active_rows, active_columns)
    ]
    simulation.fire_manager.durations = [0] * len(simulation.fire_manager.sprites)
    simulation.fire_sprites = simulation.fire_manager.sprites
    initial_cumulative = update_cumulative_burned(scar, simulation.fire_map)
    if not np.array_equal(initial_cumulative, scar | front):
        raise AssertionError("The cumulative initial scar/front masks are not preserved.")

    final_map, active = simulation.run(f"{minutes}m")
    cumulative = update_cumulative_burned(initial_cumulative, final_map)
    output_dir = output_root / scenario_id
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "schema_version": "feds-simfire-noop-smoke/1.0",
        "kind": "integration_smoke_not_noop_gate_or_physical_validation",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_result": False,
        "physical_validation": False,
        "historical_noop_gate": False,
        "agent_training": False,
        "scenario_id": scenario_id,
        "split": case["split"],
        "initial_state_time": expected_time,
        "simfire_commit": SIMFIRE_COMMIT,
        "grid": receipt["grid"],
        "inputs": {
            "receipt_sha256": sha256_file(receipt_path),
            "fuel_sha256": sha256_file(fuel_path),
            "terrain_sha256": sha256_file(terrain_path),
            "masks_sha256": sha256_file(masks_path),
        },
        "initial_cells": {
            "scar": int(scar.sum()),
            "front": int(front.sum()),
            "front_fuel_codes": sorted(int(value) for value in np.unique(fuel[front])),
            "front_cells_burnable_by_simfire": int(sum(FuelModelToFuel[int(value)].w_0 > 0 for value in fuel[front])),
        },
        "run": {
            "action": "no-op",
            "minutes": minutes,
            "random_seed": seed,
            "initial_front_cells": int(front.sum()),
            "fire_active_after_run": bool(active),
            "final_burning_cells": int(np.count_nonzero(final_map == BurnStatus.BURNING)),
            "final_burned_cells": int(np.count_nonzero(final_map == BurnStatus.BURNED)),
            "cumulative_burned_cells": int(cumulative.sum()),
            "cumulative_burned_area_ha": float(cumulative.sum() * 180.0 * 180.0 / 10000.0),
            "max_fire_duration_updates": int(config.fire.max_fire_duration),
        },
        "forcing": {
            "wind_speed_mph": 7.0,
            "wind_direction_simfire_degrees_clockwise_from_north": 90.0,
            "fuel_moisture_fraction": 0.03,
            "status": "demonstration_values_only_not_historical_gridMET",
        },
        "limitations": [
            "A successful runtime/input smoke does not prove physical spread accuracy.",
            "The constant wind and moisture are demonstration placeholders, not observed weather.",
            "FEDS supplies a satellite-estimated burn scar and active front, not ground truth or a constructed suppression line.",
            "This is one training case over a short interval, not the planned train/validation no-op gate.",
        ],
    }
    out_path = output_dir / "smoke-result.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out_path), "run": result["run"], "initial_cells": result["initial_cells"], "forcing": result["forcing"]}, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--minutes", type=int, default=60)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out-dir", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    if not 1 <= args.minutes <= 60:
        parser.error("Smoke duration must be between 1 and 60 minutes.")
    try:
        run_smoke(args.scenario_id, args.minutes, args.seed, args.out_dir)
    except Exception as exc:
        print(f"SimFire smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
