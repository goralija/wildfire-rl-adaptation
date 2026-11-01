#!/usr/bin/env python3
"""Fetch compact daily gridMET point context for the v2 FPA-FOD cohort."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import io
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COHORT = ROOT / "data/manifests/simfire-fpa-fod-cohort-v2.json"
DEFAULT_OUT = ROOT / "data/processed/simfire-cohort-v2-gridmet-weather"
BASE_URL = "https://tds.gdex.ucar.edu/thredds/ncss/grid/files/d761426"
DATASET_ID = "d761426"
DATASET_DOI = "10.5065/FDBC-FV90"

# GDEX NCSS file names and the actual variable names inside the annual NetCDF files.
VARIABLES = {
    "wind_speed_10m": ("vs", "wind_speed"),
    "wind_from_direction_10m": ("th", "wind_from_direction"),
    "daily_max_air_temperature": ("tmmx", "air_temperature"),
    "daily_min_relative_humidity": ("rmin", "relative_humidity"),
    "daily_max_relative_humidity": ("rmax", "relative_humidity"),
    "daily_precipitation": ("pr", "precipitation_amount"),
    "dead_fuel_moisture_100hr_model_g": ("fm100", "dead_fuel_moisture_100hr"),
    "energy_release_component_model_g": ("erc", "energy_release_component-g"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _parse_number(text: str) -> float:
    value = float(text)
    if not (value == value and abs(value) != float("inf")):
        raise ValueError("weather response contains a non-finite value")
    return value


def _fetch_one(
    variable_id: str,
    dataset_name: str,
    latitude: float,
    longitude: float,
    day: str,
) -> dict:
    year = day[:4]
    params = urlencode({
        "var": dataset_name,
        "latitude": "{:.8f}".format(latitude),
        "longitude": "{:.8f}".format(longitude),
        "time_start": day + "T00:00:00Z",
        "time_end": day + "T00:00:00Z",
        "accept": "csv",
    })
    url = "{}/{}_{}.nc?{}".format(BASE_URL, variable_id, year, params)
    request = Request(url, headers={"User-Agent": "wildfire-rl-adaptation/1.0"})
    last_error = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=45) as response:
                payload = response.read().decode("utf-8")
            break
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt == 2:
                raise RuntimeError("gridMET query failed for {} on {}: {}".format(
                    variable_id, day, exc
                )) from exc
            time.sleep(1.0 + attempt * 2.0)
    else:
        raise RuntimeError("gridMET query failed: {}".format(last_error))

    rows = list(csv.DictReader(io.StringIO(payload)))
    if len(rows) != 1:
        raise ValueError("expected one gridMET point/day row, got {}: {}".format(len(rows), url))
    row = rows[0]
    value_column = next((name for name in row if name.startswith(dataset_name + "[")), None)
    if value_column is None:
        value_column = next((name for name in row if name == dataset_name), None)
    if value_column is None:
        raise ValueError("{} column missing from gridMET CSV: {}".format(dataset_name, payload[:500]))
    unit_match = re.search(r'\[unit="([^"]+)"\]', value_column)
    sample_lat = next((float(value) for key, value in row.items() if key.startswith("latitude")), None)
    sample_lon = next((float(value) for key, value in row.items() if key.startswith("longitude")), None)
    if sample_lat is None or sample_lon is None:
        raise ValueError("gridMET response omitted sampled coordinates")
    response_time = row.get("time")
    if response_time != day + "T00:00:00Z":
        raise ValueError("gridMET returned unexpected day label {!r} for {}".format(response_time, day))
    return {
        "value": _parse_number(row[value_column]),
        "unit": unit_match.group(1) if unit_match else None,
        "provider_variable": dataset_name,
        "sample_grid_latitude": sample_lat,
        "sample_grid_longitude": sample_lon,
        "query_url": url,
    }


def _fetch_case(case: dict) -> dict:
    scenario_path = ROOT / case["scenario_manifest"]
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    point = scenario["event"]["location_wgs84"]
    latitude = float(point["latitude"])
    longitude = float(point["longitude"])
    date_value = scenario["event"]["discovery_time"]["value"]
    day = str(date_value)[:10]
    try:
        datetime.strptime(day, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("case {} has no valid discovery date".format(case["scenario_id"])) from exc

    values = {}
    for semantic_name, (variable_id, dataset_name) in VARIABLES.items():
        values[semantic_name] = _fetch_one(
            variable_id, dataset_name, latitude, longitude, day
        )

    sample_points = {
        (round(row["sample_grid_latitude"], 6), round(row["sample_grid_longitude"], 6))
        for row in values.values()
    }
    if len(sample_points) != 1:
        raise ValueError("gridMET variables sampled inconsistent grid cells: {}".format(sample_points))
    sample_lat, sample_lon = next(iter(sample_points))

    return {
        "scenario_id": case["scenario_id"],
        "scenario_path": scenario_path,
        "day": day,
        "reported_point": {"latitude": latitude, "longitude": longitude},
        "gridmet_point": {"latitude": sample_lat, "longitude": sample_lon},
        "values": values,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort-manifest", type=Path, default=DEFAULT_COHORT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit", type=int, help="fetch only the first N cases (for a source smoke)")
    parser.add_argument("--scenario-id", help="fetch or retry only this scenario ID")
    args = parser.parse_args()
    if not 1 <= args.workers <= 6:
        parser.error("--workers must be between 1 and 6 to limit load on the public data service")

    cohort_path = args.cohort_manifest.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()
    cohort = json.loads(cohort_path.read_text(encoding="utf-8"))
    all_cases = list(cohort["cases"])
    cases = list(all_cases)
    if args.scenario_id:
        cases = [row for row in cases if row["scenario_id"] == args.scenario_id]
        if not cases:
            parser.error("scenario ID is not in the cohort: {}".format(args.scenario_id))
    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be positive")
        cases = cases[: args.limit]
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(_fetch_case, case): case for case in cases}
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            case = futures[future]
            try:
                result = future.result()
                result["cohort_case"] = case
                results.append(result)
                print("[{}/{}] OK {}".format(index, len(cases), case["scenario_id"]), flush=True)
            except Exception as exc:
                failures.append({"scenario_id": case["scenario_id"], "error": str(exc)})
                print("[{}/{}] FAILED {}: {}".format(
                    index, len(cases), case["scenario_id"], exc
                ), file=sys.stderr, flush=True)

    case_receipts_by_id = {}
    failure_by_id = {}
    report_path = ROOT / "reports/real-fire-data/simfire-cohort-v2-gridmet-weather.json"
    if report_path.is_file():
        previous_report = json.loads(report_path.read_text(encoding="utf-8"))
        case_receipts_by_id = {
            row["scenario_id"]: row for row in previous_report.get("cases", [])
            if row["scenario_id"] not in {case["scenario_id"] for case in cases}
        }
        failure_by_id = {
            row["scenario_id"]: row for row in previous_report.get("failures", [])
            if row["scenario_id"] not in {case["scenario_id"] for case in cases}
        }
    cohort_case_by_id = {row["scenario_id"]: row for row in all_cases}
    for result in results:
        case = result.pop("cohort_case")
        case_json = {
            "kind": "gridmet_daily_point_weather",
            "schema_version": "gridmet-point/1.0",
            "scenario_id": case["scenario_id"],
            "date": result["day"],
            "source": {
                "name": "gridMET Daily Surface Data",
                "provider": "NCAR GDEX, UCAR",
                "dataset_id": DATASET_ID,
                "doi": DATASET_DOI,
                "access": "GDEX NetCDF Subset Service (NCSS), nearest 4-km grid cell",
                "nominal_resolution": "approximately 4 km; daily",
                "daily_period_note": "Climatology Lab labels gridMET days midnight-to-midnight Mountain Standard Time (UTC-7); not aligned to the FPA-FOD HHMM field.",
                "sample_query_utc": datetime.now(timezone.utc).isoformat(),
                "reported_point": result["reported_point"],
                "sampled_grid_point": result["gridmet_point"],
            },
            "values": result["values"],
            "limitations": [
                "Daily environmental context is not an hourly event replay; FPA-FOD discovery HHMM timezone is not used.",
                "Wind is a gridMET daily 10-m product, not SimFire midflame wind; an explicit height/shelter conversion is still required.",
                "100-hour fuel moisture and ERC are NFDRS model-G context, not direct FBFM13 fine-fuel moisture.",
                "Daily max temperature/minimum relative humidity are separate daily extrema and are not asserted to co-occur at the fire start.",
            ],
        }
        output_path = out_dir / (case["scenario_id"] + ".json")
        output_path.write_text(json.dumps(case_json, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        digest = sha256_file(output_path)
        scenario = json.loads(result["scenario_path"].read_text(encoding="utf-8"))
        relative_output = output_path.relative_to(ROOT).as_posix()
        scenario["inputs"]["weather"] = {
            "status": "candidate",
            "source": "gridMET daily point values via NCAR GDEX",
            "source_release": "gridMET Daily Surface Data; GDEX dataset d761426",
            "path": relative_output,
            "sha256": digest,
            "units_and_mapping": "Daily point context; preserve per-variable units in the linked JSON. Wind height, daily time convention and fuel-moisture mapping to SimFire remain unresolved.",
        }
        scenario["fire_behavior"]["weather_mapping_note"] = (
            "GDEX gridMET daily point values are saved in the linked weather JSON. "
            "They are real historical daily context, not a direct SimFire mapping: "
            "10 m wind is not midflame wind; 100-hour model-G moisture is not FBFM13 "
            "fine-fuel moisture; event HHMM is not aligned to gridMET's daily period."
        )
        result["scenario_path"].write_text(
            json.dumps(scenario, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        cohort_row = cohort_case_by_id[case["scenario_id"]]
        cohort_row["input_status"]["weather"] = "downloaded_unmapped"
        cohort_row["weather_json"] = relative_output
        cohort_row["weather_sha256"] = digest
        case_receipts_by_id[case["scenario_id"]] = {
            "scenario_id": case["scenario_id"],
            "split": cohort_row["split"],
            "weather_json": relative_output,
            "weather_sha256": digest,
            "sampled_grid_point": case_json["source"]["sampled_grid_point"],
        }
    for failure in failures:
        failure_by_id[failure["scenario_id"]] = failure
    cohort_order = {row["scenario_id"]: index for index, row in enumerate(all_cases)}
    case_receipts = sorted(case_receipts_by_id.values(), key=lambda row: cohort_order[row["scenario_id"]])
    merged_failures = sorted(failure_by_id.values(), key=lambda row: cohort_order[row["scenario_id"]])

    report = {
        "kind": "simfire_fpa_fod_gridmet_weather_acquisition",
        "scientific_result": False,
        "cohort_id": cohort.get("cohort_id"),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "name": "gridMET Daily Surface Data",
            "provider": "NCAR GDEX / UCAR",
            "dataset_id": DATASET_ID,
            "doi": DATASET_DOI,
            "service": BASE_URL,
            "nominal_resolution": "approximately 4 km, daily",
            "variables": list(VARIABLES),
        },
        "requested_case_count": len(all_cases),
        "attempted_this_run_case_count": len(cases),
        "downloaded_case_count": len(case_receipts),
        "failed_case_count": len(merged_failures),
        "historical_weather_mapped_case_count": 0,
        "cases_ready_for_historical_weather_training": 0,
        "downloaded_unmapped_weather_count_by_split": {
            split: sum(row["split"] == split for row in case_receipts)
            for split in ("train", "validation", "test")
        },
        "weather_json_directory": out_dir.relative_to(ROOT).as_posix(),
        "cases": case_receipts,
        "failures": merged_failures,
        "limitations": [
            "gridMET is daily at approximately 4-km resolution; it does not provide the hourly weather sequence required to replay a 12-hour episode.",
            "The daily series is not aligned to the discovery HHMM; the data provider defines days midnight-to-midnight MST.",
            "10-m daily wind must be converted to SimFire midflame wind; terrain/canopy sheltering is not resolved by this extraction.",
            "100-hour fuel moisture and ERC use NFDRS model-G context and must not be treated as exact FBFM13 fine-fuel moisture.",
            "Downloaded daily observations are stored as historical context only; no simulator weather mapping is applied here.",
        ],
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    cohort["weather_acquisition_report"] = report_path.relative_to(ROOT).as_posix()
    cohort["weather_acquisition_summary"] = {
        "requested": report["requested_case_count"],
        "downloaded": report["downloaded_case_count"],
        "failed": report["failed_case_count"],
        "mapped_to_simfire": 0,
        "ready_for_historical_weather_training": 0,
    }
    cohort_path.write_text(json.dumps(cohort, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(report_path),
        "requested": report["requested_case_count"],
        "downloaded": report["downloaded_case_count"],
        "failed": report["failed_case_count"],
        "mapped": 0,
    }, indent=2))
    return 1 if merged_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
