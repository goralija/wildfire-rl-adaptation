#!/usr/bin/env python3
"""Run a clearly labelled SimFire smoke on a cached real LANDFIRE tile.

This checks raster/cache integration only. The config uses simple demonstration
weather and has no agent, historical fireline replay, training or physical validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIMFIRE_ROOT = ROOT / "external" / "simfire"
CONFIG_PATH = ROOT / "configs" / "simfire_mineral_operational_smoke.yml"
SIMFIRE_COMMIT = "04905b19fe8c10dc08d64faddd00303e0561bb66"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def scenario_case(path: Path, sf_home: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    event = payload.get("event", {})
    location = event.get("location_wgs84", {})
    discovery = event.get("discovery_time", {}).get("value")
    grid = payload.get("grid", {})
    if location.get("latitude") is None or location.get("longitude") is None or not discovery:
        raise ValueError("Scenario needs a reported event location and discovery date.")
    date = datetime.fromisoformat(str(discovery)[:10])
    resolution = grid.get("resolution_m")
    rows = grid.get("rows")
    columns = grid.get("columns")
    seed_cell = payload.get("fire_behavior", {}).get("seed_cell")
    if resolution != 30 or not isinstance(rows, int) or not isinstance(columns, int):
        raise ValueError("Operational smoke currently needs an integer nominal 30 m grid.")
    if (
        not isinstance(seed_cell, list)
        or len(seed_cell) != 2
        or any(not isinstance(value, int) for value in seed_cell)
        or not (0 <= seed_cell[0] < rows and 0 <= seed_cell[1] < columns)
    ):
        raise ValueError("Scenario starting cell must be a valid [row, column] inside its grid.")
    top_left_lat = grid.get("top_left_latitude")
    top_left_lon = grid.get("top_left_longitude")
    if top_left_lat is None or top_left_lon is None:
        raise ValueError("Scenario needs its precomputed top-left grid coordinates.")
    sys.path.insert(0, str(ROOT / "scripts"))
    from prepare_mineral_landfire import cache_directory, simfire_operational_aoi

    expected = simfire_operational_aoi(
        float(location["latitude"]), float(location["longitude"]), rows * resolution, columns * resolution
    )[-1]
    if abs(expected[0] - float(top_left_lat)) > 1e-9 or abs(expected[1] - float(top_left_lon)) > 1e-9:
        raise ValueError("Scenario grid bounds do not match its event location and fixed-size rule.")
    cache = cache_directory(
        sf_home,
        date.year,
        (float(top_left_lat), float(top_left_lon)),
        rows * resolution,
        columns * resolution,
    )
    scenario_id = str(payload.get("scenario_id", "unnamed-scenario"))
    slug = re.sub(r"[^a-z0-9]+", "-", scenario_id.casefold()).strip("-") or "scenario"
    return {
        "payload": payload,
        "event_year": date.year,
        "latitude": float(location["latitude"]),
        "longitude": float(location["longitude"]),
        "height_m": rows * resolution,
        "width_m": columns * resolution,
        "rows": rows,
        "columns": columns,
        "seed_cell": tuple(seed_cell),
        "top_left_latitude": float(top_left_lat),
        "top_left_longitude": float(top_left_lon),
        "scenario_id": scenario_id,
        "output_stem": slug,
        "source_record_id": event.get("source_record_id"),
        "source": event.get("source"),
        "event_location_role": location.get("role", "unknown"),
        "event_location_accuracy_note": location.get("accuracy_note"),
        "manifest_sha256": sha256_file(path),
        "cache": cache,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=30, help="number of simulated minutes")
    parser.add_argument("--sf-home", type=Path, default=ROOT / ".local/simfire-mineral-2020")
    parser.add_argument("--out", type=Path, help="output directory; defaults to a timestamped run folder")
    parser.add_argument(
        "--scenario-manifest",
        type=Path,
        help="run this scenario's fixed grid; otherwise run the default Mineral smoke",
    )
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("--steps must be at least 1")
    if not SIMFIRE_ROOT.is_dir():
        parser.error("Missing external/simfire; see docs/research/SIMFIRE_ENVIRONMENT.md")

    sf_home = args.sf_home.expanduser().resolve()
    # Mirror the cache-key calculation in the LFPS bridge and fail before Config
    # can call SimFire's obsolete network client.
    sys.path.insert(0, str(ROOT / "scripts"))
    from prepare_mineral_landfire import (
        DEFAULT_TILE_HEIGHT_M,
        DEFAULT_TILE_WIDTH_M,
        cache_directory,
        mineral_ignition,
        simfire_operational_aoi,
    )

    if args.scenario_manifest:
        scenario_path = args.scenario_manifest.expanduser().resolve()
        try:
            case = scenario_case(scenario_path, sf_home)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            parser.error(str(exc))
        latitude = case["latitude"]
        longitude = case["longitude"]
        event_year = case["event_year"]
        height_m = case["height_m"]
        width_m = case["width_m"]
        seed_cell = case["seed_cell"]
        top_left = (case["top_left_latitude"], case["top_left_longitude"])
        cache = case["cache"]
        scenario_id = case["scenario_id"]
        output_stem = case["output_stem"]
        source_record_id = case["source_record_id"]
        event_source = case["source"]
        manifest_sha256 = case["manifest_sha256"]
        archive_sha256 = None
    else:
        archive = ROOT / "data/raw/burnmd/BurnMD.zip"
        latitude, longitude, archive_sha256 = mineral_ignition(archive)
        *_, top_left = simfire_operational_aoi(
            latitude, longitude, DEFAULT_TILE_HEIGHT_M, DEFAULT_TILE_WIDTH_M
        )
        height_m = DEFAULT_TILE_HEIGHT_M
        width_m = DEFAULT_TILE_WIDTH_M
        seed_cell = (height_m // 60, width_m // 60)
        event_year = 2020
        cache = cache_directory(sf_home, event_year, top_left, height_m, width_m)
        scenario_id = "mineral-2020-operational-smoke"
        output_stem = "mineral-2020"
        source_record_id = "BurnMD / Mineral_POLYGONS.shp / FireInitPo"
        event_source = "BurnMD"
        manifest_sha256 = None
    tifs = sorted(cache.glob("*.tif")) + sorted(cache.glob("*.tiff"))
    if len(tifs) != 1:
        parser.error(
            f"Expected one verified LANDFIRE GeoTIFF in {cache}; found {len(tifs)}. "
            "Run scripts/prepare_mineral_landfire.py after setting your LANDFIRE_EMAIL."
        )

    output = (
        args.out.expanduser().resolve()
        if args.out
        else ROOT / "runs/simfire-operational-smoke" /
        f"{output_stem}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    if output.exists() and any(output.iterdir()):
        parser.error(f"Output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    local = ROOT / ".local"
    (local / "cache").mkdir(parents=True, exist_ok=True)
    (local / "matplotlib").mkdir(parents=True, exist_ok=True)
    os.environ["SF_HOME"] = str(sf_home)
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("XDG_CACHE_HOME", str(local / "cache"))
    os.environ.setdefault("MPLCONFIGDIR", str(local / "matplotlib"))
    sys.path.insert(0, str(SIMFIRE_ROOT))

    from simfire.enums import BurnStatus
    from simfire.sim.simulation import FireSimulation
    from simfire.utils.config import Config
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import yaml
    from matplotlib.colors import ListedColormap

    config_dict = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    config_dict["area"]["screen_size"] = [height_m // 30, width_m // 30]
    config_dict["operational"].update(
        {
            "latitude": top_left[0],
            "longitude": top_left[1],
            "height": height_m,
            "width": width_m,
            "year": event_year,
        }
    )
    config_dict["historical"].update(
        {
            "fire_init_pos_lat": latitude,
            "fire_init_pos_long": longitude,
            "name": scenario_id,
            "year": str(event_year),
        }
    )
    config_dict["fire"]["fire_initial_position"]["static"]["position"] = seed_cell
    config = Config(config_dict=config_dict)
    config.simulation.headless = False
    config.simulation.save_data = False
    config.simulation.sf_home = str(output)
    simulation = FireSimulation(config)

    try:
        simulation.rendering = True
        fire_map, active = simulation.run(f"{args.steps}m")
        gif_name = f"{output_stem}-operational-fire.gif"
        simulation.save_gif(output / gif_name)
    finally:
        if simulation.rendering:
            simulation.rendering = False

    labels = ["Unburned", "Burning", "Burned", "Fireline", "Scratchline", "Wetline"]
    colors = ["#536b3f", "#e63946", "#8d5524", "#f1faee", "#2a9d8f", "#457b9d"]
    fig, axis = plt.subplots(figsize=(7, 6))
    image = axis.imshow(
        fire_map,
        cmap=ListedColormap(colors),
        vmin=0,
        vmax=len(colors) - 1,
        interpolation="nearest",
    )
    axis.set_title(f"{scenario_id} — SimFire raster smoke, {args.steps} min")
    axis.set_xlabel("Grid column")
    axis.set_ylabel("Grid row")
    colorbar = fig.colorbar(image, ax=axis, ticks=range(len(labels)), shrink=0.8)
    colorbar.ax.set_yticklabels(labels)
    fig.tight_layout()
    fig.savefig(output / "final-state.png", dpi=150)
    plt.close(fig)

    receipt = {
        "kind": "operational_real_fuel_terrain_smoke",
        "scientific_result": False,
        "real_historical_weather": False,
        "human_agent_training": False,
        "historical_action_replay": False,
        "simfire_commit": SIMFIRE_COMMIT,
        "burnmd_archive_sha256": archive_sha256,
        "scenario_id": scenario_id,
        "source_record_id": source_record_id,
        "source": event_source,
        "scenario_manifest_sha256": manifest_sha256,
        "landfire_geotiff_path": str(tifs[0]),
        "landfire_geotiff_sha256": sha256_file(tifs[0]),
        "reported_event_location_wgs84": {
            "latitude": latitude,
            "longitude": longitude,
            "role": case.get("event_location_role", "reported_ignition"),
            "accuracy_note": case.get("event_location_accuracy_note"),
        },
        "grid_shape": list(fire_map.shape),
        "starting_cell_row_column": list(seed_cell),
        "steps_minutes": args.steps,
        "active_after_run": bool(active),
        "burned_cells": int(np.count_nonzero(fire_map == BurnStatus.BURNED)),
        "burning_cells": int(np.count_nonzero(fire_map == BurnStatus.BURNING)),
        "outputs": [gif_name, "final-state.png"],
        "limitations": [
            f"Fuel is LF2016_FBFM13 and is {event_year - 2016} years older than the {event_year} event.",
            "Weather/moisture are simple demonstration settings, not historical observations.",
            "No agent, mitigation action, training or physical validation is included.",
        ],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({**receipt, "output_dir": str(output)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
