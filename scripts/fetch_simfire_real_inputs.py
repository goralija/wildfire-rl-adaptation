#!/usr/bin/env python3
"""Fetch and validate small, real environmental inputs for a SimFire scenario.

Raw source data is written under ignored ``.local/``. The runner stores only a
provenance receipt in ``reports/``; it does not publish or claim a fire replay.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import numpy as np
import rasterio
import requests


ROOT = Path(__file__).resolve().parents[1]
FUEL_SERVICES = {
    "LF2016": (
        "https://lfps.usgs.gov/arcgis/rest/services/Landfire_LF2016/"
        "LF2016_FBFM13_CONUS/ImageServer/exportImage"
    ),
    "LF2022": (
        "https://lfps.usgs.gov/arcgis/rest/services/Landfire_LF2022/"
        "LF2022_FBFM13_CONUS/ImageServer/exportImage"
    ),
}
ELEVATION_SERVICE = (
    "https://lfps.usgs.gov/arcgis/rest/services/Landfire_Topo/"
    "LF2020_Elev_CONUS/ImageServer/exportImage"
)
WEATHER_SERVICE = "https://archive-api.open-meteo.com/v1/archive"
SIMFIRE_COMMIT = "04905b19fe8c10dc08d64faddd00303e0561bb66"
ALLOWED_FUEL_CODES = {
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
    91, 92, 93, 98, 99, -32768, -9999, 32767,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def load_scenario(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    location = payload["event"]["location_wgs84"]
    grid = payload["grid"]
    required = (location.get("latitude"), location.get("longitude"), grid.get("projected_bounds_m"))
    if any(value is None for value in required):
        raise ValueError("Scenario needs a location and exact projected_bounds_m.")
    crs = str(grid.get("crs", ""))
    if not (crs.startswith("EPSG:326") or crs.startswith("EPSG:327")):
        raise ValueError("Scenario grid must use a UTM north or south CRS (EPSG:326xx/327xx).")
    if grid.get("resolution_m") != 30:
        raise ValueError("LANDFIRE FBFM13 input currently requires 30 m cells.")
    return payload


def image_params(bounds: list[float], rows: int, columns: int, crs: str) -> dict[str, str]:
    xmin, ymin, xmax, ymax = bounds
    wkid = crs.removeprefix("EPSG:")
    return {
        "bbox": f"{xmin},{ymin},{xmax},{ymax}",
        "bboxSR": wkid,
        "imageSR": wkid,
        "size": f"{columns},{rows}",
        "adjustAspectRatio": "false",
        "format": "tiff",
        "pixelType": "S16",
        "interpolation": "RSP_NearestNeighbor",
        "f": "image",
    }


def fetch_image(url: str, params: dict[str, str], path: Path, force: bool) -> str:
    if path.exists() and not force:
        return sha256_file(path)
    response = requests.get(url, params=params, timeout=180)
    response.raise_for_status()
    if "image/tiff" not in response.headers.get("content-type", "").lower():
        raise RuntimeError(f"Expected a TIFF from LANDFIRE; got {response.headers.get('content-type')}")
    if len(response.content) < 1024:
        raise RuntimeError(f"LANDFIRE returned an unexpectedly small file for {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    return hashlib.sha256(response.content).hexdigest()


def validate_raster(path: Path, crs: str, rows: int, columns: int, bounds: list[float]) -> dict:
    with rasterio.open(path) as dataset:
        array = dataset.read(1)
        if dataset.count != 1 or dataset.width != columns or dataset.height != rows:
            raise ValueError(f"Unexpected raster shape/band count in {path}")
        if dataset.crs is None or dataset.crs.to_string() != crs:
            raise ValueError(f"Expected {crs}, received {dataset.crs} in {path}")
        actual = [dataset.bounds.left, dataset.bounds.bottom, dataset.bounds.right, dataset.bounds.top]
        if not np.allclose(actual, bounds, atol=0.01):
            raise ValueError(f"Raster bounds {actual} do not match scenario bounds {bounds}")
        if dataset.nodata is not None and np.any(array == dataset.nodata):
            raise ValueError(f"Raster contains NoData cells; define a documented policy before use: {path}")
        if not np.isfinite(array).all():
            raise ValueError(f"Raster contains non-finite values: {path}")
        return {
            "shape": [rows, columns],
            "crs": crs,
            "bounds_m": actual,
            "dtype": array.dtype.name,
            "minimum": float(array.min()),
            "maximum": float(array.max()),
            "mean": float(array.mean()),
            "unique_values": sorted(int(value) for value in np.unique(array)),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario-manifest",
        type=Path,
        default=ROOT / "data/manifests/simfire-fpa-fod-401019270-dixie-candidate.json",
    )
    parser.add_argument("--out", type=Path, default=ROOT / ".local/real-input-dixie")
    parser.add_argument("--force", action="store_true", help="replace existing downloaded inputs")
    parser.add_argument(
        "--skip-weather",
        action="store_true",
        help="fetch and validate fuel/terrain even when the historical-weather API is unavailable",
    )
    args = parser.parse_args()
    manifest_path = args.scenario_manifest.expanduser().resolve()
    output = args.out.expanduser().resolve()
    try:
        scenario = load_scenario(manifest_path)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        parser.error(str(exc))

    grid = scenario["grid"]
    rows, columns = grid["rows"], grid["columns"]
    bounds = [float(value) for value in grid["projected_bounds_m"]]
    params = image_params(bounds, rows, columns, grid["crs"])
    fuel_input = scenario["inputs"]["fuel"]
    fuel_release = str(fuel_input.get("source_release") or "LF2016").split()[0]
    if fuel_release not in FUEL_SERVICES:
        parser.error(
            "Unsupported fuel vintage {!r}; available: {}".format(
                fuel_release, ", ".join(FUEL_SERVICES)
            )
        )
    fuel_service = FUEL_SERVICES[fuel_release]
    output.mkdir(parents=True, exist_ok=True)
    fuel_path = output / "fuel-{}-fbfm13.tif".format(fuel_release.lower())
    elevation_path = output / "elevation-lf2020-m.tif"
    weather_path = output / "weather-era5-discovery-date-utc.json"

    fuel_hash = fetch_image(fuel_service, params, fuel_path, args.force)
    elevation_hash = fetch_image(ELEVATION_SERVICE, params, elevation_path, args.force)
    fuel_info = validate_raster(fuel_path, grid["crs"], rows, columns, bounds)
    elevation_info = validate_raster(elevation_path, grid["crs"], rows, columns, bounds)
    unexpected = sorted(set(fuel_info["unique_values"]) - ALLOWED_FUEL_CODES)
    if unexpected:
        raise ValueError(f"Unmapped FBFM13 codes found: {unexpected}")

    event = scenario["event"]
    discovery = str(event["discovery_time"]["value"])[:10]
    location = event["location_wgs84"]
    weather_params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "start_date": discovery,
        "end_date": discovery,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation",
        "timezone": "GMT",
        "wind_speed_unit": "ms",
        "models": "era5",
    }
    if args.skip_weather:
        weather = {"hourly": {"time": []}, "hourly_units": None}
        weather_url = None
        weather_hash = None
    elif not weather_path.exists() or args.force:
        response = requests.get(WEATHER_SERVICE, params=weather_params, timeout=180)
        response.raise_for_status()
        weather = response.json()
        if "hourly" not in weather or len(weather["hourly"].get("time", [])) != 24:
            raise ValueError("ERA5 response did not contain 24 hourly values for the discovery date.")
        weather_path.write_text(json.dumps(weather, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        weather_url = response.url
        weather_hash = sha256_file(weather_path)
    else:
        weather = json.loads(weather_path.read_text(encoding="utf-8"))
        weather_url = "{}?{}".format(WEATHER_SERVICE, urlencode(weather_params))
        weather_hash = sha256_file(weather_path)

    receipt = {
        "kind": "real_environmental_input_acquisition",
        "scientific_result": False,
        "scenario_id": scenario["scenario_id"],
        "event_year": str(scenario["event"]["discovery_time"]["value"])[:4],
        "split": scenario.get("split"),
        "scenario_manifest_sha256": sha256_file(manifest_path),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "simfire_commit": SIMFIRE_COMMIT,
        "grid": {
            "crs": grid["crs"],
            "resolution_m": grid["resolution_m"],
            "rows": rows,
            "columns": columns,
            "bounds_m": bounds,
            "cell_alignment": "30 m UTM grid, nearest-neighbor export from native LANDFIRE service",
        },
        "fuel": {
            "source": fuel_service.removesuffix("/exportImage"),
            "source_release": "{} FBFM13 CONUS".format(fuel_release),
            "file": fuel_path.name,
            "sha256": fuel_hash,
            "validation": fuel_info,
            "use_limit": fuel_input.get(
                "units_and_mapping",
                "Pre-event candidate fuel map; not a field-verified event-year vegetation survey.",
            ),
        },
        "terrain": {
            "source": ELEVATION_SERVICE.removesuffix("/exportImage"),
            "source_release": "LF2020 Elevation CONUS",
            "file": elevation_path.name,
            "sha256": elevation_hash,
            "units": "meters in source; convert to feet for pinned SimFire",
            "validation": elevation_info,
        },
        "weather": {
            "source": WEATHER_SERVICE,
            "source_release": "ERA5 historical reanalysis via Open-Meteo",
            "query_url": weather_url,
            "file": weather_path.name if weather_hash else None,
            "sha256": weather_hash,
            "time_zone": "UTC requested for unambiguous storage; source discovery HHMM timezone is unresolved",
            "spatial_resolution_note": "ERA5 is approximately 25 km, much coarser than the 30 m simulator grid.",
            "simulator_use": "stored as historical context only; not fed into SimFire until wind-height and fuel-moisture semantics are mapped" if weather_hash else "not acquired in this run; the archive API host was not reachable from this runtime",
            "hour_count": len(weather.get("hourly", {}).get("time", [])) if weather_hash else None,
            "hourly_units": weather.get("hourly_units"),
        },
        "limitations": [
            "FPA-FOD location is an incident reference point with unknown event-specific precision, not verified GPS ignition.",
            "FPA-FOD discovery time is retained without a time zone; the weather date is not aligned to the reported HHMM.",
            "The selected fuel layer is pre-event and source-compatible, but is not a field-verified event-year vegetation survey.",
            "This receipt proves source retrieval and spatial raster alignment, not model accuracy or physical fire replay.",
        ],
    }
    receipt_path = output / "input-receipt.json"
    scenario["inputs"]["fuel"].update(
        {"status": "verified", "path": display_path(fuel_path), "sha256": fuel_hash}
    )
    scenario["inputs"]["terrain"].update(
        {"status": "verified", "path": display_path(elevation_path), "sha256": elevation_hash}
    )
    scenario["inputs"]["weather"].update(
        {
            "status": "candidate",
            "path": display_path(weather_path) if weather_hash else scenario["inputs"]["weather"].get("path"),
            "sha256": weather_hash,
        }
    )
    scenario["readiness"] = "candidate"
    manifest_path.write_text(json.dumps(scenario, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["scenario_manifest_sha256"] = sha256_file(manifest_path)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "receipt": str(receipt_path), "grid": receipt["grid"], "fuel_codes": fuel_info["unique_values"], "terrain_m": [elevation_info["minimum"], elevation_info["maximum"]], "weather_hours": receipt["weather"]["hour_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
