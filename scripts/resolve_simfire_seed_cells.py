#!/usr/bin/env python3
"""Resolve FPA-FOD reference points to valid SimFire starting cells using only fuel input."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
COHORT = ROOT / "data/manifests/simfire-fpa-fod-cohort-v2.json"
SEARCH_RADIUS_M = 804.672
# SimFire's pinned FuelModelToFuel mapping marks the Anderson FBFM13 codes 1-13
# burnable; urban, snow/ice, agriculture, water, barren and nodata codes are not.
SIMFIRE_BURNABLE_FBFM13 = set(range(1, 14))


def _resolve(scenario: dict) -> dict:
    grid = scenario["grid"]
    crs = grid["crs"]
    xmin, ymin, xmax, ymax = [float(value) for value in grid["projected_bounds_m"]]
    resolution = float(grid["resolution_m"])
    rows, columns = int(grid["rows"]), int(grid["columns"])
    location = scenario["event"]["location_wgs84"]
    transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    x, y = transformer.transform(float(location["longitude"]), float(location["latitude"]))
    reported_column = min(columns - 1, max(0, int((x - xmin) // resolution)))
    reported_row = min(rows - 1, max(0, int((ymax - y) // resolution)))
    fuel_path = ROOT / scenario["inputs"]["fuel"]["path"]
    with rasterio.open(fuel_path) as dataset:
        if dataset.crs is None or dataset.crs.to_string() != crs:
            raise ValueError("Fuel raster CRS does not match scenario {}.".format(scenario["scenario_id"]))
        fuel = dataset.read(1)
    if fuel.shape != (rows, columns):
        raise ValueError("Fuel raster shape does not match scenario {}.".format(scenario["scenario_id"]))
    if int(fuel[reported_row, reported_column]) in SIMFIRE_BURNABLE_FBFM13:
        selected_row, selected_column = reported_row, reported_column
        distance_m = math.hypot(
            xmin + (selected_column + 0.5) * resolution - x,
            ymax - (selected_row + 0.5) * resolution - y,
        )
        method = "reported_point_cell_is_burnable"
    else:
        fuel_rows, fuel_columns = np.where(np.isin(fuel, sorted(SIMFIRE_BURNABLE_FBFM13)))
        center_x = xmin + (fuel_columns.astype(float) + 0.5) * resolution
        center_y = ymax - (fuel_rows.astype(float) + 0.5) * resolution
        distances = np.hypot(center_x - x, center_y - y)
        eligible = np.where(distances <= SEARCH_RADIUS_M)[0]
        if eligible.size == 0:
            raise ValueError(
                "No burnable cell within {:.1f}m of the reported point for {}.".format(
                    SEARCH_RADIUS_M, scenario["scenario_id"]
                )
            )
        # Deterministic nearest cell; ties break by row then column. No observed perimeter
        # or final area is loaded by this script.
        order = sorted(
            eligible.tolist(),
            key=lambda index: (float(distances[index]), int(fuel_rows[index]), int(fuel_columns[index])),
        )
        index = order[0]
        selected_row = int(fuel_rows[index])
        selected_column = int(fuel_columns[index])
        distance_m = float(distances[index])
        method = "nearest_burnable_cell_within_half_section"
    fuel_code = int(fuel[selected_row, selected_column])
    scenario["fire_behavior"]["seed_cell"] = [int(selected_row), int(selected_column)]
    scenario["fire_behavior"]["seed_cell_selection"] = {
        "method": method,
        "reported_point_cell": [int(reported_row), int(reported_column)],
        "selected_fuel_code": fuel_code,
        "distance_from_reported_point_m": float(distance_m),
        "search_radius_m": SEARCH_RADIUS_M,
        "uses_observed_perimeter": False,
        "note": (
            "Starting cell is selected from the pre-event FBFM13 map only. If the reported "
            "cell is non-burnable, the closest burnable cell within half a PLSS section is "
            "used as an uncertain proxy; this does not claim a verified ignition location."
        ),
    }
    return scenario["fire_behavior"]["seed_cell_selection"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, default=COHORT)
    args = parser.parse_args()
    cohort_path = args.cohort.expanduser().resolve()
    cohort = json.loads(cohort_path.read_text(encoding="utf-8"))
    rows = []
    for case in cohort["cases"]:
        manifest_path = ROOT / case["scenario_manifest"]
        scenario = json.loads(manifest_path.read_text(encoding="utf-8"))
        selection = _resolve(scenario)
        scenario["references"]["notes"] += (
            " Simulation start is selected by the pre-event fuel-only rule recorded in "
            "fire_behavior.seed_cell_selection; it does not use observed burn perimeters."
        )
        if selection["method"] != "reported_point_cell_is_burnable":
            scenario["limitations"].append(
                "Reported point landed on a non-burnable class; simulation starts at the nearest burnable fuel cell within 804.672 m, an uncertain proxy rather than a verified ignition."
            )
        manifest_path.write_text(json.dumps(scenario, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        case["seed_cell"] = scenario["fire_behavior"]["seed_cell"]
        case["seed_selection"] = selection
        rows.append({
            "scenario_id": case["scenario_id"],
            "source_record_id": case["source_record_id"],
            "split": case["split"],
            "scenario_manifest": case["scenario_manifest"],
            "seed_cell": scenario["fire_behavior"]["seed_cell"],
            **selection,
        })
    report = {
        "kind": "simfire_cohort_seed_cell_resolution",
        "scientific_result": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "Map the incident-reference point into the projected grid. If its FBFM13 cell is non-burnable in SimFire, pick the nearest burnable cell within the 804.672m half-width of a one-mile PLSS section, with deterministic row/column tie-breaks.",
        "burnable_fbfm13_codes": sorted(SIMFIRE_BURNABLE_FBFM13),
        "search_radius_m": SEARCH_RADIUS_M,
        "case_count": len(rows),
        "reported_cell_already_burnable": sum(row["method"] == "reported_point_cell_is_burnable" for row in rows),
        "used_nearest_burnable_proxy": sum(row["method"] != "reported_point_cell_is_burnable" for row in rows),
        "cases": rows,
        "limitations": [
            "FPA-FOD gives an incident-reference coordinate with unknown event-specific accuracy, not GPS-confirmed ignition.",
            "Fuel-only seed adjustment does not reconstruct the historical ignition or fire perimeter.",
            "All policies must use the same selected cell and fixed selection rule.",
        ],
    }
    report_path = ROOT / "reports/real-fire-data/simfire-cohort-v2-seed-selection.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    cohort["seed_selection_report"] = report_path.relative_to(ROOT).as_posix()
    cohort["seed_selection_summary"] = {
        "cases": len(rows),
        "reported_point_cell_burnable": report["reported_cell_already_burnable"],
        "nearest_burnable_proxy": report["used_nearest_burnable_proxy"],
        "uses_observed_perimeter": False,
    }
    cohort_path.write_text(json.dumps(cohort, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(cohort["seed_selection_summary"], indent=2))
    for row in rows:
        if row["method"] != "reported_point_cell_is_burnable":
            print("{}: moved {:.1f}m, fuel code {}".format(row["scenario_id"], row["distance_from_reported_point_m"], row["selected_fuel_code"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
