#!/usr/bin/env python3
"""Compare Canadian daily ERA5-FWI-SN values with three existing TRAIN pilots.

Reads only the three named TRAIN case receipts, the target-blind weather-point
receipt, and operator-downloaded 2018 NetCDF inputs. Does not rebuild cases, alter
Weather.csv, inspect validation/test data, or run Cell2Fire.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/raw/era5-fwi-sn/v2"
DEFAULT_PROVENANCE = ROOT / "reports/real-fire-data/cfsds-train-terrain-weather-provenance.json"
DEFAULT_OUTPUT = ROOT / "reports/real-fire-data/era5-fwi-sn-2018-pilot-comparison.json"
COMPONENTS = ("FFMC", "DMC", "DC", "ISI", "BUI", "FWI")
CASE_REPORTS = {
    "2018_1770": ROOT / "reports/real-fire-data/2018_1770-case.json",
    "2018_241": ROOT / "reports/real-fire-data/2018_241-case.json",
    "2018_747": ROOT / "reports/real-fire-data/2018_747-case.json",
}
# Borealis Dataverse v2 file IDs and MD5 checksums, recorded before download.
FILE_RECORDS = {
    "BUI": (977649, 20_731_112, "9192c88611853090c7ff9fe808b9872a"),
    "DC": (977028, 20_399_821, "bda2a902114d24d6506b3b92de05493b"),
    "DMC": (977355, 20_719_079, "3b7c7d01bbed7b33d165e5fb42e85573"),
    "FFMC": (976865, 19_691_676, "dd71a6c640c3f80eb916cea413a548f8"),
    "FWI": (976732, 21_376_913, "538b91cfeb483425ec0c3c0ef575520c"),
    "ISI": (977599, 21_167_694, "b3a5d85825f479fda5f9bbbcb561ac0b"),
}


def digest(path: Path, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def distance_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    lat1, lat2 = math.radians(lat_a), math.radians(lat_b)
    dlat = lat2 - lat1
    dlon = math.radians(lon_b - lon_a)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(h))


def load_source_files(data_dir: Path) -> tuple[dict[str, Path], list[dict[str, Any]]]:
    paths: dict[str, Path] = {}
    records: list[dict[str, Any]] = []
    for component in COMPONENTS:
        path = data_dir / f"Risque-ESCER_ERA5_{component}_daily_2018_Can_0p25grid.nc"
        if not path.is_file():
            raise FileNotFoundError(f"Missing {component} source file: {path}")
        size = path.stat().st_size
        md5 = digest(path, "md5")
        file_id, expected_size, expected_md5 = FILE_RECORDS[component]
        if size != expected_size or md5 != expected_md5:
            raise ValueError(f"Borealis size/MD5 mismatch for {path.name}")
        paths[component] = path
        records.append({
            "component": component,
            "borealis_file_id": file_id,
            "filename": path.name,
            "bytes": size,
            "md5": md5,
            "sha256": digest(path, "sha256"),
        })
    return paths, records


def load_pilot_points(provenance_path: Path) -> dict[str, dict[str, Any]]:
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    return {
        row["event_id"]: row
        for row in provenance["weather"]["queries"]
        if row["event_id"] in CASE_REPORTS
    }


def extract_component(path: Path, component: str, target_date: str,
                      latitude: float, longitude: float) -> tuple[float, float, float, str]:
    with xr.open_dataset(path) as dataset:
        for coordinate in ("time", "lat", "lon"):
            if coordinate not in dataset.coords:
                raise ValueError(f"{path.name} has no {coordinate!r} coordinate")
        if component not in dataset.data_vars:
            raise ValueError(f"{path.name} has no {component!r} data variable")
        dates = np.asarray(dataset["time"].values).astype("datetime64[D]")
        requested = np.datetime64(target_date, "D")
        matching = np.flatnonzero(dates == requested)
        if len(matching) != 1:
            raise ValueError(f"Expected one {target_date} slice in {path.name}; found {len(matching)}")
        lat = float(dataset["lat"].sel(lat=latitude, method="nearest").item())
        lon = float(dataset["lon"].sel(lon=longitude, method="nearest").item())
        value = float(dataset[component].isel(time=int(matching[0])).sel(
            lat=latitude, lon=longitude, method="nearest"
        ).item())
        if not math.isfinite(value):
            raise ValueError(f"Missing {component} at {target_date}, {lat}, {lon}")
        return value, lat, lon, str(dataset.attrs.get("dataset_version", "unknown"))


def build_report(data_dir: Path, provenance_path: Path) -> dict[str, Any]:
    paths, file_records = load_source_files(data_dir)
    points = load_pilot_points(provenance_path)
    missing_points = sorted(set(CASE_REPORTS) - set(points))
    if missing_points:
        raise ValueError(f"Missing target-blind weather point(s): {missing_points}")

    cases: list[dict[str, Any]] = []
    dataset_versions: set[str] = set()
    for event_id, report_path in CASE_REPORTS.items():
        case = json.loads(report_path.read_text(encoding="utf-8"))
        event = case["event"]
        point = points[event_id]
        latitude, longitude = (float(value) for value in point["request_lat_lon"])
        target_date = event["target_date_local"]
        values: dict[str, float] = {}
        selected_grid: tuple[float, float] | None = None
        for component, path in paths.items():
            value, grid_lat, grid_lon, version = extract_component(
                path, component, target_date, latitude, longitude
            )
            values[component] = value
            dataset_versions.add(version)
            current_grid = (grid_lat, grid_lon)
            if selected_grid is not None and current_grid != selected_grid:
                raise ValueError(f"Component grids differ for {event_id}: {selected_grid} vs {current_grid}")
            selected_grid = current_grid

        assert selected_grid is not None
        grid_lat, grid_lon = selected_grid
        cfsds_summary = {name: float(event["summary_weather"][name.lower()]) for name in COMPONENTS}
        cases.append({
            "event_id": event_id,
            "target_date_local": target_date,
            "query_point_method": "reconstructed target-blind day-n-1 safe-interior-front centroid from the existing provenance receipt",
            "query_point_wgs84": {"lat": latitude, "lon": longitude},
            "nearest_era5_grid_point_wgs84": {"lat": grid_lat, "lon": grid_lon},
            "point_to_grid_distance_km": round(distance_km(latitude, longitude, grid_lat, grid_lon), 3),
            "era5_fwi_sn_daily_values": values,
            "cfsds_fire_day_summary_values": cfsds_summary,
            "era5_fwi_sn_minus_cfsds_summary": {
                name: round(values[name] - cfsds_summary[name], 6) for name in COMPONENTS
            },
            "comparison_note": "Different products and spatial supports: ERA5-FWI-SN is a nearest ~31 km ERA5 grid cell at the reconstructed target-blind point; CFSDS summary values are fire-day summaries. Differences are diagnostic, not error estimates.",
            "case_receipt_sha256": digest(report_path, "sha256"),
        })

    if len(dataset_versions) != 1:
        raise ValueError(f"Expected one product version across files, got {sorted(dataset_versions)}")
    return {
        "schema": "era5-fwi-sn-pilot-comparison/v1",
        "reviewed_on": date.today().isoformat(),
        "purpose": "Read-only comparison of a validated Canadian daily FWI reanalysis against the FWI summary values used in three existing TRAIN pilot cases.",
        "scope": {
            "event_ids": list(CASE_REPORTS),
            "validation_test_data_opened": False,
            "case_manifests_or_weather_csv_modified": False,
            "new_firecase_or_cell2fire_replay_created": False,
            "calibration_or_training_run": False,
        },
        "source": {
            "name": "ERA5-FWI-SN dataset (V1), Borealis release version 2",
            "dataset_doi": "https://doi.org/10.5683/SP3/4B18XZ",
            "paper_doi": "https://doi.org/10.5194/essd-18-5995-2026",
            "dataset_license": "CC BY 4.0",
            "netcdf_product_version": sorted(dataset_versions)[0],
            "spatial_resolution_degrees": 0.25,
            "temporal_resolution": "daily; components calculated using local solar-noon meteorology",
            "source_reanalysis": "ERA5 hourly single-level reanalysis",
            "published_domain_and_years_in_paper": "Canada, 1950–2024; the current Borealis v2 archive also contains selected 2025 products",
            "validation_summary_from_paper": "Against CWFIS station FWI for 2015–2024, median temporal/spatial correlation is 0.81; paper reports modestly high variability and underestimation of some extremes.",
            "selected_files": file_records,
        },
        "cases": cases,
        "interpretation": [
            "This is a Canada-specific, documented alternative for the six daily FWI columns; it is materially better sourced than using CFSDS fire-day means as the simulator weather codes.",
            "Cell2Fire's Weather.csv is hourly, while these six Canadian FWI indices are daily. The compatible first-pass mapping is one dated daily value repeated across that date's hourly rows, explicitly labeled daily; it does not invent an hourly FWI trajectory.",
            "The source is a roughly 31 km grid, not local fire-station truth. It improves provenance and validation, not local spatial precision.",
            "The hourly temperature, humidity, wind and precipitation series remain a separate input source and still need pinned coordinates, versions and matched-time checks before new cases are rebuilt.",
            "These reads do not establish historical suppression, as-of-event fuel maps, no-action physical validity, or an agent's real-world avoided area. No old case is automatically promoted to benchmark status."
        ],
        "source_data_directory": str(data_dir.relative_to(ROOT)),
        "target_blind_point_receipt_sha256": digest(provenance_path, "sha256"),
        "audit_script_sha256": digest(Path(__file__), "sha256"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--provenance", type=Path, default=DEFAULT_PROVENANCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = build_report(args.data_dir, args.provenance)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "cases": len(report["cases"]), "components": len(COMPONENTS), "product_version": report["source"]["netcdf_product_version"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
