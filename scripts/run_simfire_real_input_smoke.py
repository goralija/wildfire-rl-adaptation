#!/usr/bin/env python3
"""Run a short SimFire integration smoke using fetched real LANDFIRE layers.

This validates that real FBFM13 and elevation arrays enter the pinned simulator.
The run uses clearly labelled demonstration wind and fuel moisture: the fetched ERA5
series is preserved as event context but is not mapped into SimFire yet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import rasterio


ROOT = Path(__file__).resolve().parents[1]
SIMFIRE_ROOT = ROOT / "external/simfire"
CONFIG_PATH = SIMFIRE_ROOT / "configs/functional_config.yml"
SIMFIRE_COMMIT = "04905b19fe8c10dc08d64faddd00303e0561bb66"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_inputs(manifest: dict, input_dir: Path | None = None) -> tuple[np.ndarray, np.ndarray, dict[str, Path]]:
    grid = manifest["grid"]
    bounds = [float(value) for value in grid["projected_bounds_m"]]
    shape = (int(grid["rows"]), int(grid["columns"]))
    fuel_release = str(manifest["inputs"]["fuel"].get("source_release") or "LF2016").split()[0]
    paths = {}
    for key, path_key, fallback_name in (
        ("fuel", "fuel", "fuel-{}-fbfm13.tif".format(fuel_release.lower())),
        ("elevation", "terrain", "elevation-lf2020-m.tif"),
    ):
        reference = manifest["inputs"][path_key].get("path")
        path = ROOT / reference if reference and not Path(reference).is_absolute() else Path(reference or "")
        if not path.is_file() and input_dir:
            path = input_dir / fallback_name
        if not path.is_file():
            raise FileNotFoundError("Missing {} raster: {}".format(path_key, path))
        paths[key] = path
    arrays: dict[str, np.ndarray] = {}
    for key, path in paths.items():
        with rasterio.open(path) as dataset:
            if dataset.crs is None or dataset.crs.to_string() != grid["crs"]:
                raise ValueError(f"{path} has CRS {dataset.crs}; expected {grid['crs']}.")
            if (dataset.height, dataset.width) != shape or dataset.count != 1:
                raise ValueError(f"{path} must have one {shape[0]}x{shape[1]} band.")
            actual = [dataset.bounds.left, dataset.bounds.bottom, dataset.bounds.right, dataset.bounds.top]
            if not np.allclose(actual, bounds, atol=0.01):
                raise ValueError(f"{path} bounds do not match the scenario manifest.")
            array = dataset.read(1)
            if dataset.nodata is not None and np.any(array == dataset.nodata):
                raise ValueError(f"NoData values in {path} need an explicit policy first.")
            if not np.isfinite(array).all():
                raise ValueError(f"Non-finite values in {path}.")
            arrays[key] = array
    return arrays["fuel"], arrays["elevation"], paths


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def render_inputs(
    fuel: np.ndarray,
    elevation: np.ndarray,
    bounds: list[float],
    point_cell: list[int],
    destination: Path,
    scenario_id: str,
    fuel_release: str,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap

    sys.path.insert(0, str(SIMFIRE_ROOT))
    from simfire.enums import FuelModelRGB13

    codes = sorted(int(value) for value in np.unique(fuel))
    colors = [FuelModelRGB13[code] for code in codes]
    midpoint_edges = np.arange(len(codes) + 1) - 0.5
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(midpoint_edges, len(codes))
    xmin, ymin, xmax, ymax = bounds
    extent = [xmin / 1000, xmax / 1000, ymin / 1000, ymax / 1000]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), constrained_layout=True)
    image = axes[0].imshow(fuel, origin="upper", extent=extent, cmap=cmap, norm=norm, interpolation="nearest")
    axes[0].scatter(
        [xmin / 1000 + (point_cell[1] + 0.5) * 0.03],
        [ymax / 1000 - (point_cell[0] + 0.5) * 0.03],
        marker="+", s=120, linewidths=2, color="black", label="reported point cell (uncertain)",
    )
    axes[0].set_title("LANDFIRE FBFM13 — {}".format(fuel_release))
    axes[0].set_xlabel("UTM easting (km)")
    axes[0].set_ylabel("UTM northing (km)")
    axes[0].legend(loc="upper right", fontsize=8)
    bar = fig.colorbar(image, ax=axes[0], ticks=np.arange(len(codes)))
    bar.ax.set_yticklabels([str(code) for code in codes])
    bar.set_label("Source fuel model code")
    elevation_image = axes[1].imshow(elevation, origin="upper", extent=extent, cmap="terrain", interpolation="nearest")
    axes[1].set_title("LANDFIRE elevation — 2020")
    axes[1].set_xlabel("UTM easting (km)")
    axes[1].set_ylabel("UTM northing (km)")
    fig.colorbar(elevation_image, ax=axes[1], label="Elevation (m)")
    fig.suptitle("{} — exact 30 m UTM grid; point accuracy unknown".format(scenario_id))
    fig.savefig(destination, dpi=160)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario-manifest",
        type=Path,
        default=ROOT / "data/manifests/simfire-fpa-fod-401019270-dixie-candidate.json",
    )
    parser.add_argument("--inputs", type=Path, help="optional override directory for raster files")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "reports/real-fire-data/simfire-dixie-real-input-smoke",
    )
    parser.add_argument("--steps", type=int, default=30)
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("--steps must be at least 1")
    manifest_path = args.scenario_manifest.expanduser().resolve()
    input_dir = args.inputs.expanduser().resolve() if args.inputs else None
    output = args.out.expanduser().resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        fuel_codes, elevation_m, input_paths = read_inputs(manifest, input_dir)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    if not SIMFIRE_ROOT.is_dir():
        parser.error("Missing external/simfire; see docs/research/SIMFIRE_ENVIRONMENT.md")
    if output.exists() and any(output.iterdir()):
        parser.error(f"Output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    cache = ROOT / ".local/cache"
    matplotlib_dir = ROOT / ".local/matplotlib"
    fontconfig_dir = ROOT / ".local/fontconfig"
    for directory in (cache, matplotlib_dir, fontconfig_dir):
        directory.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("XDG_CACHE_HOME", str(cache))
    os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_dir))
    os.environ.setdefault("FONTCONFIG_PATH", str(fontconfig_dir))
    sys.path.insert(0, str(SIMFIRE_ROOT))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import yaml
    from matplotlib.colors import ListedColormap
    from simfire.enums import FuelModelRGB13
    from simfire.sim.simulation import FireSimulation
    from simfire.utils.config import Config
    from simfire.utils.layers import OperationalFuelLayer, OperationalTopographyLayer

    unmapped = sorted(set(int(code) for code in np.unique(fuel_codes)) - set(FuelModelRGB13))
    if unmapped:
        parser.error(f"FBFM13 codes are not mapped by pinned SimFire: {unmapped}")
    config_dict = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    config_dict["area"]["screen_size"] = list(fuel_codes.shape)
    # The manifest's 30 m projected pixels must match SimFire's feet-per-pixel scale.
    config_dict["area"]["pixel_scale"] = float(manifest["grid"]["resolution_m"]) * 3.280839895
    config_dict["terrain"]["fuel"]["type"] = "functional"
    config_dict["terrain"]["topography"]["type"] = "functional"
    config_dict["simulation"]["headless"] = False
    config_dict["simulation"]["record"] = True
    config_dict["simulation"]["save_data"] = False
    config_dict["simulation"]["sf_home"] = str(output)
    config_dict["wind"]["function"] = "simple"
    config_dict["wind"]["simple"]["speed"] = 7
    config_dict["wind"]["simple"]["direction"] = 90.0
    config_dict["environment"]["moisture"] = 0.03
    seed_cell = [int(value) for value in manifest["fire_behavior"]["seed_cell"]]
    # The shared manifest stores [row, column]; SimFire's static position is (x, y).
    config_dict["fire"]["fire_initial_position"]["static"]["position"] = [seed_cell[1], seed_cell[0]]
    config = Config(config_dict=config_dict)

    # Reuse SimFire's official FBFM13 code mapping and its documented meters-to-feet
    # elevation conversion without triggering its obsolete LANDFIRE network client.
    source_layers = SimpleNamespace(layers=["fuel"], fuel=fuel_codes, topography=elevation_m)
    config.terrain.fuel_layer = OperationalFuelLayer(source_layers)
    config.terrain.topography_layer = OperationalTopographyLayer(source_layers)
    simulation = FireSimulation(config)
    try:
        simulation.rendering = True
        fire_map, active = simulation.run(f"{args.steps}m")
        gif_path = output / "{}-demo-weather.gif".format(manifest["scenario_id"])
        simulation.save_gif(gif_path)
    finally:
        if simulation.rendering:
            simulation.rendering = False

    xmin, ymin, xmax, ymax = [float(value) for value in manifest["grid"]["projected_bounds_m"]]
    fuel_release = str(manifest["inputs"]["fuel"].get("source_release") or "LF2016").split()[0]
    render_inputs(
        fuel_codes,
        elevation_m,
        [xmin, ymin, xmax, ymax],
        seed_cell,
        output / "input-layers.png",
        manifest["scenario_id"],
        fuel_release,
    )
    fig, axis = plt.subplots(figsize=(7, 6))
    image = axis.imshow(fire_map, cmap=ListedColormap(["#536b3f", "#e63946", "#8d5524", "#f1faee", "#2a9d8f", "#457b9d"]), vmin=0, vmax=5, interpolation="nearest")
    colorbar = fig.colorbar(image, ax=axis, ticks=range(6), shrink=0.8)
    colorbar.ax.set_yticklabels(["Unburned", "Burning", "Burned", "Fireline", "Scratchline", "Wetline"])
    axis.set_title(f"{manifest['scenario_id']} — {args.steps} min\nReal LANDFIRE layers; demonstration wind/moisture")
    axis.set_xlabel("Grid column")
    axis.set_ylabel("Grid row")
    fig.tight_layout()
    fig.savefig(output / "final-state.png", dpi=160)
    plt.close(fig)

    receipt = {
        "kind": "simfire_real_fuel_terrain_integration_smoke",
        "scientific_result": False,
        "physical_validation": False,
        "historical_action_replay": False,
        "agent_training": False,
        "historical_weather_used_in_simulation": False,
        "scenario_id": manifest["scenario_id"],
        "scenario_manifest": str(manifest_path.relative_to(ROOT)),
        "scenario_manifest_sha256": sha256_file(manifest_path),
        "simfire_commit": SIMFIRE_COMMIT,
        "grid_resolution_m": manifest["grid"]["resolution_m"],
        "simfire_pixel_scale_ft": config_dict["area"]["pixel_scale"],
        "steps": args.steps,
        "fire_active_after_horizon": bool(active),
        "inputs": {
            "fuel": {"path": display_path(input_paths["fuel"]), "sha256": sha256_file(input_paths["fuel"]), "codes": sorted(int(value) for value in np.unique(fuel_codes))},
            "terrain": {"path": display_path(input_paths["elevation"]), "sha256": sha256_file(input_paths["elevation"]), "source_units": "meters", "SimFire_units": "feet"},
            "weather": (
                "Historical ERA5 record is stored but not used because ERA5 wind is at 10 m and SimFire expects midflame wind, while RH is not fuel moisture."
                if manifest["inputs"]["weather"].get("sha256")
                else "Historical weather was not downloaded; explicit demonstration wind/moisture are used."
            ),
        },
        "fire_initial_position": {"cell_row_column": seed_cell, "simfire_xy_column_row": [seed_cell[1], seed_cell[0]], "source_role": manifest["event"]["location_wgs84"]["role"], "accuracy_note": manifest["event"]["location_wgs84"].get("accuracy_note")},
        "environment_used": {"wind": "configuration demo value", "fuel_moisture": "configuration demo value; not inferred from ERA5 RH"},
        "outputs": ["input-layers.png", "final-state.png", gif_path.name],
        "limitations": [
            "The FPA-FOD point is an incident reference with unknown event-specific precision, not GPS-confirmed ignition.",
            "LANDFIRE {} FBFM13 is a pre-event candidate, not a field-verified event-year vegetation survey.".format(fuel_release),
            "The run demonstrates real fuel/terrain array integration only; its demo atmosphere is not historical weather.",
            "The event discovery HHMM timezone is unresolved, and 10 m wind/RH are not yet mapped to SimFire's midflame wind/fuel moisture.",
            "The output is not a counterfactual reconstruction or a claim about real-world area saved.",
        ],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "fire_active": bool(active), "inputs": receipt["inputs"], "visuals": receipt["outputs"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
