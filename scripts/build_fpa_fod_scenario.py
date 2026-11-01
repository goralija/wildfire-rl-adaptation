#!/usr/bin/env python3
"""Turn one official FPA-FOD GeoJSON record into a SimFire scenario candidate.

This creates a provenance-rich *candidate card*, not a runnable scientific case. Fuel,
terrain and weather remain marked missing until their files have been fetched and checked.
By default the script requests one record by FOD_ID from the current USFS map service and
keeps the response under ignored data/raw/. Use --input-geojson to rebuild offline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from pyproj import Transformer


ROOT = Path(__file__).resolve().parents[1]
SERVICE_LAYER = (
    "https://apps.fs.usda.gov/arcx/rest/services/EDW/"
    "EDW_FireOccurrenceCurrentEdition_01/MapServer/0"
)
QUERY_URL = f"{SERVICE_LAYER}/query"
SOURCE_RELEASE = "FPA_FOD_20260615 (7th edition, 6th update)"
SIMFIRE_COMMIT = "04905b19fe8c10dc08d64faddd00303e0561bb66"
ACRES_TO_HECTARES = 0.40468564224
OUT_FIELDS = (
    "fod_id,fpa_id,fire_name,fire_year,discovery_date,discovery_time,fire_size,"
    "latitude,longitude,state,mtbs_id,mtbs_fire_name"
)


def _fetch_record(fod_id: int, destination: Path) -> dict:
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - platform setup message
        raise RuntimeError("Install requests in the selected project environment.") from exc

    metadata_response = requests.get(SERVICE_LAYER, params={"f": "json"}, timeout=60)
    metadata_response.raise_for_status()
    metadata = metadata_response.json()
    release_text = json.dumps(metadata, sort_keys=True)
    release_code = SOURCE_RELEASE.split()[0]
    if release_code not in release_text:
        raise RuntimeError(
            f"The live USFS service no longer advertises pinned release {release_code}; "
            "review the new edition before using it."
        )

    params = {
        "where": f"fod_id = {fod_id}",
        "outFields": OUT_FIELDS,
        "outSR": "4326",
        "returnGeometry": "true",
        "f": "geojson",
    }
    response = requests.get(QUERY_URL, params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _read_geojson(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection":
        raise ValueError("Input must be a GeoJSON FeatureCollection from the USFS query.")
    features = payload.get("features")
    if not isinstance(features, list) or len(features) != 1:
        raise ValueError(f"Expected exactly one FPA-FOD record; got {len(features or [])}.")
    feature = features[0]
    properties = feature.get("properties") or {}
    geometry = feature.get("geometry") or {}
    if geometry.get("type") != "Point":
        raise ValueError(f"Expected point geometry; got {geometry.get('type')!r}.")
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        raise ValueError("Record has no valid point coordinates.")
    longitude, latitude = map(float, coordinates[:2])
    if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
        raise ValueError("Point geometry is outside EPSG:4326 bounds.")
    required = ("fod_id", "fire_year", "discovery_date", "fire_size")
    missing = [field for field in required if properties.get(field) is None]
    if missing:
        raise ValueError(f"FPA-FOD record lacks required fields: {', '.join(missing)}")
    return {"properties": properties, "longitude": longitude, "latitude": latitude}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _fixed_grid(latitude: float, longitude: float, height_m: int, width_m: int) -> dict:
    if height_m <= 0 or width_m <= 0 or height_m % 30 or width_m % 30:
        raise ValueError("Grid height and width must be positive multiples of 30 m.")
    zone = min(60, max(1, int(math.floor((longitude + 180) / 6)) + 1))
    epsg = (32600 if latitude >= 0 else 32700) + zone
    crs = f"EPSG:{epsg}"
    to_projected = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    x, y = to_projected.transform(longitude, latitude)
    xmin = math.floor((x - width_m / 2) / 30) * 30
    ymax = math.ceil((y + height_m / 2) / 30) * 30
    xmax = xmin + width_m
    ymin = ymax - height_m
    columns = width_m // 30
    rows = height_m // 30
    seed_column = min(columns - 1, max(0, int((x - xmin) // 30)))
    seed_row = min(rows - 1, max(0, int((ymax - y) // 30)))
    return {
        "crs": crs,
        "resolution_m": 30,
        "resolution_note": (
            "Exact 30 m projected cells in the event's UTM zone; the reported point is "
            "assigned to its containing cell and remains spatially uncertain."
        ),
        "rows": rows,
        "columns": columns,
        "projected_bounds_m": [xmin, ymin, xmax, ymax],
        "extent_selection": "fixed_around_event_location",
        "top_left_latitude": None,
        "top_left_longitude": None,
        "seed_cell": [seed_row, seed_column],
    }


def _scenario(record: dict, height_m: int, width_m: int, snapshot_path: Path) -> dict:
    props = record["properties"]
    fod_id = int(props["fod_id"])
    year = int(props["fire_year"])
    name = str(props.get("fire_name") or f"fire-{fod_id}").strip()
    slug = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-") or f"fire-{fod_id}"
    date = datetime.fromtimestamp(float(props["discovery_date"]) / 1000, tz=timezone.utc).date()
    raw_time = str(props.get("discovery_time") or "").strip()
    if raw_time and (not raw_time.isdigit() or len(raw_time) not in (3, 4)):
        raise ValueError(f"Unexpected discovery_time value: {raw_time!r}")
    reported_time = raw_time.zfill(4)
    reported_datetime = f"{date.isoformat()} {reported_time}" if reported_time else date.isoformat()
    time_precision = (
        "reported calendar date and HHMM; source timezone is not assigned by this adapter"
        if reported_time
        else "reported calendar date only"
    )
    area_ha = float(props["fire_size"]) * ACRES_TO_HECTARES
    try:
        relative_snapshot_path = snapshot_path.relative_to(ROOT).as_posix()
    except ValueError:
        relative_snapshot_path = str(snapshot_path)
    query_url = f"{QUERY_URL}?{urlencode({'where': f'fod_id = {fod_id}', 'outFields': OUT_FIELDS, 'outSR': '4326', 'returnGeometry': 'true', 'f': 'geojson'})}"
    latitude = record["latitude"]
    longitude = record["longitude"]
    grid = _fixed_grid(latitude, longitude, height_m, width_m)
    return {
        "schema_version": "simfire-scenario/1.0",
        "scenario_id": f"fpa-fod-{fod_id}-{slug}",
        "readiness": "candidate",
        "event": {
            "source": "USFS FPA-FOD current edition",
            "source_release": SOURCE_RELEASE,
            "source_record_id": f"FOD_ID:{fod_id}; FPA_ID:{props.get('fpa_id') or 'unavailable'}",
            "source_url": query_url,
            "source_record_snapshot": {
                "path": relative_snapshot_path,
                "sha256": _sha256(snapshot_path),
                "source_url": query_url,
            },
            "data_license_status": (
                "USFS Research Data Archive says the data may be used without additional "
                "permissions or fees; cite Short (2026), DOI 10.2737/RDS-2013-0009.7. "
                "Check licenses separately for any joined raster or perimeter products."
            ),
            "discovery_time": {
                "value": reported_datetime,
                "timezone": None,
                "precision": time_precision,
            },
            "location_wgs84": {
                "latitude": latitude,
                "longitude": longitude,
                "role": "incident_reference_point",
                "accuracy_m": None,
                "accuracy_note": (
                    "Point geometry requested from the current USFS service in EPSG:4326. "
                    "The publication's stated minimum location precision is a PLSS section "
                    "(one-square-mile grid); event-specific accuracy is not provided here."
                ),
            },
            "final_area_ha_reference_only": area_ha,
            "final_perimeter_reference": None,
        },
        "grid": {key: value for key, value in grid.items() if key != "seed_cell"},
        "inputs": {
            "fuel": {
                "status": "missing",
                "source": None,
                "source_release": None,
                "path": None,
                "sha256": None,
                "units_and_mapping": "Need a pre-event fuel layer; document native classes, vintage and SimFire conversion.",
            },
            "terrain": {
                "status": "missing",
                "source": None,
                "source_release": None,
                "path": None,
                "sha256": None,
                "units_and_mapping": "Need an elevation raster aligned to the fixed grid; document units, resampling and NoData handling.",
            },
            "weather": {
                "status": "missing",
                "source": None,
                "source_release": None,
                "path": None,
                "sha256": None,
                "units_and_mapping": "Need event-date weather and explicit timezone/unit conversion into SimFire wind and moisture.",
            },
        },
        "fire_behavior": {
            "simulator": "SimFire",
            "simulator_commit": SIMFIRE_COMMIT,
            "seed_cell": grid["seed_cell"],
            "horizon_minutes": None,
            "seed": None,
            "weather_mapping_note": (
                "Candidate only; FPA-FOD point is an incident reference point, not a "
                "verified ignition; it is used as a provisional seed location. Weather is missing."
            ),
        },
        "split": "unassigned",
        "references": {
            "perimeters_and_actions_are_agent_inputs": False,
            "perimeters_and_actions_are_reward_inputs": False,
            "notes": (
                f"FPA-FOD MTBS_ID={props.get('mtbs_id') or 'missing'} is a perimeter-join "
                "hint only; the perimeter has not been retrieved. FPA final size is not an "
                "untreated-fire target or agent reward."
            ),
        },
        "limitations": [
            "Candidate record only: fuel, terrain and historical weather files have not been obtained or validated.",
            "The source coordinate's event-specific accuracy is unknown; do not treat it as a 30-m GPS ignition.",
            "The reported final fire size reflects actual response and reporting; it is context only, not a no-action target.",
            "Discovery HHMM is kept without an assumed timezone until the source field definition is checked.",
            f"Final area was converted from {float(props['fire_size']):g} acres using 1 acre = {ACRES_TO_HECTARES} hectares.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fod-id", type=int, default=401019270, help="USFS FOD_ID; default is the Dixie Fire record")
    parser.add_argument("--input-geojson", type=Path, help="use a saved one-record GeoJSON instead of calling USFS")
    parser.add_argument(
        "--source-record-out",
        type=Path,
        default=ROOT / "data/raw/fpa-fod/fod-401019270.geojson",
        help="ignored raw-data path where the one-record service response is saved",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/manifests/simfire-fpa-fod-401019270-dixie-candidate.json",
    )
    parser.add_argument("--height-m", type=int, default=3840)
    parser.add_argument("--width-m", type=int, default=3840)
    parser.add_argument(
        "--snapshot-out",
        type=Path,
        help="tracked small source-record snapshot; defaults to reports/real-fire-data/fpa-fod-{FOD_ID}-source.geojson",
    )
    args = parser.parse_args()

    if args.input_geojson:
        source_path = args.input_geojson.expanduser().resolve()
    else:
        source_path = args.source_record_out.expanduser().resolve()
        payload = _fetch_record(args.fod_id, source_path)
        if len(payload.get("features", [])) != 1:
            parser.error(f"FOD_ID {args.fod_id} did not return exactly one record.")
    try:
        record = _read_geojson(source_path)
        actual_id = int(record["properties"]["fod_id"])
        if actual_id != args.fod_id:
            raise ValueError(f"Input FOD_ID {actual_id} does not match requested {args.fod_id}.")
        if args.snapshot_out:
            snapshot_path = args.snapshot_out.expanduser().resolve()
        elif args.input_geojson:
            try:
                source_path.relative_to(ROOT / "reports/real-fire-data")
                snapshot_path = source_path
            except ValueError:
                snapshot_path = ROOT / "reports/real-fire-data" / f"fpa-fod-{actual_id}-source.geojson"
        else:
            snapshot_path = ROOT / "reports/real-fire-data" / f"fpa-fod-{actual_id}-source.geojson"
        if snapshot_path != source_path:
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            if snapshot_path.exists():
                if _sha256(snapshot_path) != _sha256(source_path):
                    raise ValueError(f"Refusing to replace a different source snapshot: {snapshot_path}")
            else:
                shutil.copyfile(source_path, snapshot_path)
        scenario = _scenario(record, args.height_m, args.width_m, snapshot_path)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        parser.error(str(exc))

    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(scenario, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "scenario_id": scenario["scenario_id"],
        "readiness": scenario["readiness"],
        "event": scenario["event"]["source_record_id"],
        "output": str(output_path),
        "grid": f"{scenario['grid']['rows']}x{scenario['grid']['columns']} at 30m",
        "missing_inputs": [name for name, item in scenario["inputs"].items() if item["status"] != "verified"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
