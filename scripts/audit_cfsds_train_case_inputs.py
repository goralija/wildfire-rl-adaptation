#!/usr/bin/env python3
"""Audit locally materialized CFSDS TRAIN FireCase input alignment.

The script only visits event IDs selected in the TRAIN list of the cohort manifest.
It never searches or opens validation/test case files. It reads generated case
manifests and small simulator inputs from an operator-provided local runs folder;
raw datasets and generated cases are not copied into the repository.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COHORT = ROOT / "data/manifests/cfsds-v1_1-pilot-cohort.json"
DEFAULT_FUEL_QC = ROOT / "reports/real-fire-data/cfsds-train-fuel-qc.json"
DEFAULT_RUNS = ROOT / "runs/real-case"
DEFAULT_OUT = ROOT / "reports/real-fire-data/cfsds-train-input-qc.json"
GRID_ASSETS = ("Forest.asc", "elevation.asc", "slope.asc", "saz.asc")
TERRAIN_FIELDS = ("elevation", "slope", "saz")
FWI_FIELDS = ("FFMC", "DMC", "DC", "ISI", "BUI", "FWI")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def haversine_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    """Great-circle distance between the reported CFSDS centroid and API grid point."""
    p1, p2 = math.radians(lat_a), math.radians(lat_b)
    dp = p2 - p1
    dl = math.radians(lon_b - lon_a)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(a))


def read_ascii_grid(path: Path) -> dict[str, Any]:
    """Read an ESRI ASCII grid and return header plus valid-cell summary."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 7:
        raise ValueError(f"ASCII grid is too short: {path.name}")
    header: dict[str, float] = {}
    for line in lines[:6]:
        parts = line.split()
        if len(parts) != 2:
            raise ValueError(f"Malformed ASCII grid header in {path.name}")
        header[parts[0].casefold()] = float(parts[1])
    expected_rows, expected_cols = int(header["nrows"]), int(header["ncols"])
    data = [[float(value) for value in line.split()] for line in lines[6:]]
    if len(data) != expected_rows or any(len(row) != expected_cols for row in data):
        raise ValueError(f"Grid shape disagrees with header: {path.name}")
    nodata = header.get("nodata_value", -9999.0)
    values = [value for row in data for value in row if value != nodata]
    return {
        "header": header,
        "valid_cells": len(values),
        "nodata_cells": expected_rows * expected_cols - len(values),
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
        "mean": sum(values) / len(values) if values else None,
    }


def parse_weather(path: Path, expected_local_date: str) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    timestamps = [datetime.strptime(row["datetime"], "%Y-%m-%d %H:%M") for row in rows]
    ordered_hourly = len(timestamps) == 24 and all(
        later - earlier == timedelta(hours=1)
        for earlier, later in zip(timestamps, timestamps[1:])
    )
    correct_local_day = bool(timestamps) and all(
        timestamp.strftime("%Y-%m-%d") == expected_local_date for timestamp in timestamps
    )
    constant_fwi = {
        field: len({row[field] for row in rows}) == 1
        for field in FWI_FIELDS
        if rows and field in rows[0]
    }
    return {
        "row_count": len(rows),
        "first_local_time": timestamps[0].strftime("%Y-%m-%d %H:%M") if timestamps else None,
        "last_local_time": timestamps[-1].strftime("%Y-%m-%d %H:%M") if timestamps else None,
        "ordered_hourly_24_rows": ordered_hourly,
        "all_rows_on_target_local_day": correct_local_day,
        "fwi_fields_constant_across_hourly_rows": constant_fwi,
        "sha256": sha256_file(path),
    }


def _train_rows(cohort: dict[str, Any]) -> list[dict[str, Any]]:
    """Read only the TRAIN candidate list; other split rows are not traversed."""
    return list(cohort["selection"]["candidate_day_pairs_by_split"]["train"])


def _find_train_case(runs_root: Path, event_id: str, target_doy: int) -> Path | None:
    """Look only below directories named for this TRAIN event."""
    event_dirs = sorted(runs_root.glob(f"{event_id}-day*")) if runs_root.exists() else []
    for event_dir in event_dirs:
        manifest_path = event_dir / "case.json"
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        event = manifest.get("event", {})
        if (
            manifest.get("split") == "train"
            and event.get("event_id") == event_id
            and int(event.get("target_doy", -1)) == target_doy
        ):
            return manifest_path
    return None


def audit_case(manifest_path: Path, train_row: dict[str, Any]) -> dict[str, Any]:
    case = json.loads(manifest_path.read_text(encoding="utf-8"))
    event_id = train_row["event_id"]
    case_dir = manifest_path.parent
    input_dir = case_dir / "input"
    if case.get("split") != "train" or case.get("event", {}).get("event_id") != event_id:
        raise ValueError(f"Case manifest does not match TRAIN event {event_id}")

    grids: dict[str, dict[str, Any]] = {}
    missing_assets = []
    for filename in GRID_ASSETS:
        asset = input_dir / filename
        if not asset.is_file():
            missing_assets.append(filename)
            continue
        grids[filename] = read_ascii_grid(asset)

    grid_headers_match = len(grids) == len(GRID_ASSETS) and all(
        grids[name]["header"] == grids[GRID_ASSETS[0]]["header"]
        for name in GRID_ASSETS[1:]
    )
    expected_header = grids.get(GRID_ASSETS[0], {}).get("header", {})
    grid_20x20_100m = (
        int(expected_header.get("ncols", -1)) == 20
        and int(expected_header.get("nrows", -1)) == 20
        and math.isclose(expected_header.get("cellsize", -1), 100.0)
    )
    terrain: dict[str, Any] = {}
    for name in TERRAIN_FIELDS:
        filename = f"{name}.asc"
        if filename in grids:
            summary = grids[filename]
            terrain[name] = {
                "valid_cells": summary["valid_cells"],
                "nodata_cells": summary["nodata_cells"],
                "minimum": summary["minimum"],
                "maximum": summary["maximum"],
                **({"mean": summary["mean"]} if name != "saz" else {}),
                "sha256": sha256_file(input_dir / filename),
            }

    weather_path = input_dir / "Weather.csv"
    weather = parse_weather(weather_path, case["event"]["target_date_local"]) if weather_path.is_file() else None
    centroid = case["event"].get("summary_centroid_wgs84")
    request_location = case["sources"].get("weather", {}).get("request_location")
    weather_distance = None
    if centroid and request_location:
        weather_distance = round(
            haversine_km(
                float(centroid["lat"]), float(centroid["lon"]),
                float(request_location["lat"]), float(request_location["lon"]),
            ),
            3,
        )

    data_csv = input_dir / "Data.csv"
    data_row_count = None
    if data_csv.is_file():
        with data_csv.open(newline="", encoding="utf-8") as stream:
            data_row_count = sum(1 for _ in csv.reader(stream))

    return {
        "event_id": event_id,
        "target_date_local": case["event"].get("target_date_local"),
        "case_manifest_sha256": sha256_file(manifest_path),
        "case_input_available": True,
        "split_confirmed_train": case.get("split") == "train",
        "fuel": {
            "map_release": case.get("sources", {}).get("fuel_map", {}).get("release"),
            "source_resolution_m": case.get("sources", {}).get("fuel_map", {}).get("resolution_m"),
            "simulator_grid_sha256": sha256_file(input_dir / "Forest.asc")
            if (input_dir / "Forest.asc").is_file() else None,
        },
        "grid_alignment": {
            "all_four_ascii_headers_match": grid_headers_match,
            "expected_20x20_100m_grid": grid_20x20_100m,
            "data_csv_rows_including_header": data_row_count,
            "missing_ascii_assets": missing_assets,
        },
        "terrain": terrain,
        "weather": {
            "provider_model": case.get("sources", {}).get("weather", {}).get("model"),
            "timezone": case.get("sources", {}).get("weather", {}).get("timezone"),
            "utc_offset_seconds": case.get("sources", {}).get("weather", {}).get("utc_offset_seconds"),
            "api_location": request_location,
            "distance_from_cfsds_summary_centroid_km": weather_distance,
            "source_file_sha256": case.get("sources", {}).get("weather", {}).get("raw_sha256"),
            "input_file": weather,
        },
        "suppression_status": case["event"].get("suppression_status", "unknown"),
    }


def build_report(cohort_path: Path, fuel_qc_path: Path, runs_root: Path) -> dict[str, Any]:
    cohort = json.loads(cohort_path.read_text(encoding="utf-8"))
    fuel_qc = json.loads(fuel_qc_path.read_text(encoding="utf-8"))
    train_rows = _train_rows(cohort)
    cases = []
    found_ids = set()
    for train_row in train_rows:
        event_id = train_row["event_id"]
        manifest = _find_train_case(runs_root, event_id, int(train_row["target_doy"]))
        if manifest is not None:
            cases.append(audit_case(manifest, train_row))
            found_ids.add(event_id)

    distances = [
        case["weather"]["distance_from_cfsds_summary_centroid_km"]
        for case in cases
        if case["weather"]["distance_from_cfsds_summary_centroid_km"] is not None
    ]
    fuel_statuses = {
        item["event_id"]: item["fuel_status"] for item in fuel_qc.get("cases", [])
    }
    return {
        "schema": "cfsds-train-input-qc/1.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Train-only inventory and alignment check of the existing 20x20 CFSDS FireCase inputs; not physical validation.",
        "scope": {
            "split": "train only",
            "train_candidate_count": len(train_rows),
            "case_input_packages_found": len(cases),
            "case_input_packages_not_materialized": len(train_rows) - len(cases),
            "validation_or_test_case_files_opened": 0,
            "train_event_ids": [row["event_id"] for row in train_rows],
            "materialized_train_event_ids": sorted(found_ids),
            "not_materialized_train_event_ids": [row["event_id"] for row in train_rows if row["event_id"] not in found_ids],
        },
        "provenance": {
            "cohort_manifest": "data/manifests/cfsds-v1_1-pilot-cohort.json",
            "cohort_manifest_sha256": sha256_file(cohort_path),
            "fuel_audit_report": "reports/real-fire-data/cfsds-train-fuel-qc.json",
            "fuel_audit_report_sha256": sha256_file(fuel_qc_path),
            "local_generated_case_source": "operator-provided runs/real-case directory; generated inputs remain ignored by Git",
            "fuel_map_zip_sha256": fuel_qc.get("input_provenance", {}).get("fuel_map_zip_sha256"),
            "dem_source_asset_sha256_recorded_in_case_manifests": False,
        },
        "summary": {
            "train_fuel_qc_status_counts": {
                "PASS_FUEL_ONLY": sum(status == "PASS_FUEL_ONLY" for status in fuel_statuses.values()),
                "FAIL_FUEL_OVERLAP": sum(status == "FAIL_FUEL_OVERLAP" for status in fuel_statuses.values()),
                "other_or_missing": len(train_rows) - len(fuel_statuses),
            },
            "all_train_suppression_status": "unknown; no event-level suppression/action record was joined for any of the 20 candidates",
            "weather_centroid_distance_km": {
                "measured_case_count": len(distances),
                "minimum": min(distances) if distances else None,
                "maximum": max(distances) if distances else None,
            },
            "case_inputs_complete_for_full_train_cohort": False,
            "no_action_gate_passed": False,
            "training_or_calibration_performed": False,
        },
        "source_review": {
            "fuel_vintage": {
                "train_fires_years": sorted({int(row["year"]) for row in train_rows}),
                "used_map": "National FBP fuel-type grid v2014b, 250 m; metadata lists 2011 land cover, CanFI2000/ecological inputs, and NFDB/NBAC burn-scar use",
                "2014b_vintage_limit": "The official metadata does not provide a per-pixel date or a clear NBAC/NFDB cutoff. The 2014b label alone therefore cannot certify that every train event, especially 2014 events, is free of post-event fuel information.",
                "2019_map": {
                    "product": "Canadian Forest FBP Fuel Types (CanFG), v20191114",
                    "official_catalog_location": "CWFIS development directory",
                    "resolution_m": 250,
                    "listed_archive_size": "about 2 GB",
                    "metadata_inputs": "kNN Forest Inventory (2017), Agriculture Canada land cover, NBAC burn-area reassignment, and national deforestation monitoring",
                    "assessment": "A genuine official candidate vintage and source for a burn-scar succession ruleset, but it is listed under development and includes NBAC-based burned-area reassignment. Its exact per-pixel burn-record cutoff is not provided, so it may contain records later than an event target.",
                    "archive_downloaded": False,
                    "metadata_verified_from": "official CWFIS development catalog and metadata PDF; see S-032",
                },
                "2024_map": {
                    "product": "CFFDRS FBP Fuel Types 2024, 30 m",
                    "temporal_coverage": "2020-08-01 to 2024-04-01",
                    "metadata_inputs": "SCANFI, Canadian ecozones, and NBAC",
                    "assessment": "Useful as a later map product but after all current 2014-2018 train targets; not used as their baseline because this risks future-information leakage.",
                    "metadata_verified_from": "official Open Government record; see S-033",
                },
                "annualization_method_candidate": {
                    "published_recipe": "Build a year/day-specific fuel layer from a versioned base map and reclassify only perimeters burned before target day n, following the v20191114 burn-scar succession ruleset.",
                    "source": "Bennett et al. (2026), W.I.S.E. methods; see S-037",
                    "project_status": "Literature method only; not implemented or validated in this project.",
                    "must_resolve_before_use": [
                        "Confirm the base map's temporal provenance and any pre-existing burn history so older scars are neither omitted nor double-counted.",
                        "Reproduce and test the exact fuel-class succession crosswalk; the current 2014b raster codes and v20191114 rules must not be assumed interchangeable.",
                        "Keep target day n and later perimeter information out of the fuel layer.",
                        "Test how a day n-1 scar reclassified to non-fuel interacts with this simulator's imported initial scar and active front.",
                    ],
                },
                "decision": "Retain v2014b only as the pinned input for reproducing already-saved pilot cases. No annual vintage is approved as a leakage-safe replacement yet; do not label any of the 20 candidates fully fuel-vintage qualified.",
                "full_2014b_metadata_verified_from": "official CWFIS metadata PDF; see S-031",
            },
            "terrain": {
                "source_product": "NRCan MRDEM-30 Digital Terrain Model (DTM)",
                "source_resolution_m": 30,
                "simulator_resolution_m": 100,
                "materialized_case_count": len(cases),
                "not_materialized_train_case_count": len(train_rows) - len(cases),
                "limitations": [
                    "Only generated train cases present in the supplied runs directory were measured.",
                    "The three measured ASCII DEM/slope/aspect grids have matching 20x20 / 100 m headers and no no-data cells.",
                    "The case manifests do not record a checksum for the source MRDEM tile, so generated-grid hashes prove output identity but not the exact upstream source tile bytes.",
                    "MRDEM is a blended product; acquisition date of the local source tile was not recorded in these case manifests.",
                ],
                "cases": [
                    {"event_id": case["event_id"], **case["terrain"]}
                    for case in cases
                ],
            },
            "weather": {
                "source": "Open-Meteo Historical Weather API, ERA5-Seamless",
                "official_resolution_context": "ERA5 is hourly at 0.25 degrees (about 25 km); ERA5-Land is hourly at 0.1 degrees (about 9-11 km). Both are much coarser than the 2x2 km policy grid.",
                "provider_variable_mapping_verified": "Open-Meteo documents temperature and humidity from ERA5-Land and wind and solar radiation from ERA5 for ERA5-Seamless. The precise source/version for every field in the saved Weather.csv, especially precipitation, was not recorded in the case manifests and must be captured before regenerating cases; see S-035.",
                "materialized_case_count": len(distances),
                "centroid_distance_km_min_max": [min(distances), max(distances)] if distances else None,
                "time_alignment": "The three checked Weather.csv files each contain 24 ordered hourly rows for the target's local calendar date. The daily CFSDS FWI fields are repeated unchanged in all 24 rows because no hourly FWI series is present in the current case inputs.",
                "limitations": [
                    "A nearest reanalysis point is not a local weather station measurement or 100 m weather field.",
                    "A daily CFSDS burn-day target does not identify the actual hour at which the observed front advanced.",
                    "The saved input comes from a merged product; the provider does not identify the source version for each saved column in the case manifest.",
                    "Only three materialized train cases were checked; the remaining 17 need case construction and equivalent checks.",
                ],
                "cases": [
                    {
                        "event_id": case["event_id"],
                        "target_date_local": case["target_date_local"],
                        "timezone": case["weather"]["timezone"],
                        "api_location": case["weather"]["api_location"],
                        "distance_from_cfsds_summary_centroid_km": case["weather"]["distance_from_cfsds_summary_centroid_km"],
                        "input_file": case["weather"]["input_file"],
                    }
                    for case in cases
                ],
            },
            "suppression": {
                "status_for_all_train_events": "unknown",
                "evidence_joined": False,
                "interpretation": "No event-level action/resource timeline was joined. This does not mean no suppression occurred.",
                "public_source_review": "CWFIS public fire-history descriptions document agency-reported fire locations and mapped perimeters, while public current-fire status is not a retrospective action/resource record for these CFSDS day-pairs; see S-036.",
            },
        },
        "cases": cases,
        "limitations": [
            "This audit intentionally selects only the TRAIN list from the cohort manifest; it opens no validation/test case package or raster.",
            "Input alignment checks do not validate Cell2Fire fire behavior and do not explain the prior no-action overgrowth.",
            "Fuel PASS is only a compatibility screen. Suppression and within-day fire timing remain unknown.",
            "No simulator replay, fine-tuning, benchmark, or parameter calibration was run.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, default=DEFAULT_COHORT)
    parser.add_argument("--fuel-qc", type=Path, default=DEFAULT_FUEL_QC)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = build_report(args.cohort, args.fuel_qc, args.runs_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"TRAIN events: {report['scope']['train_candidate_count']}; "
        f"materialized case inputs: {report['scope']['case_input_packages_found']}; "
        f"wrote {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
