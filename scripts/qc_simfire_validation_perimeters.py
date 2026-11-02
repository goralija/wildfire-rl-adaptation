#!/usr/bin/env python3
"""Recheck public 2023 VALIDATION perimeter shapes against current SimFire map bounds."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shapely.geometry import MultiPolygon, Polygon, box
from shapely.validation import explain_validity


ROOT = Path(__file__).resolve().parents[1]
ATTRIBUTES = ROOT / "reports/real-fire-data/usfs-nifc-validation-perimeter-screen-20261102.json"
EXTENTS = ROOT / "reports/real-fire-data/simfire-validation-perimeter-extent-screen-20261102.json"
DEFAULT_OUTPUT = ROOT / "reports/real-fire-data/usfs-nifc-validation-perimeter-polygon-qc-20261102.json"
DEFAULT_FIGURE = ROOT / "reports/real-fire-data/validation-perimeter-map-footprints-20261102.png"
M2_PER_ACRE = 4046.8564224

ENDPOINTS = {
    "NIFC": "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters/FeatureServer/0/query",
    "USFS": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceAndPerimeter_01/MapServer/30/query",
}
PRIMARY_SERVICE = {
    "fpa-fod-401316132-hayden": "USFS",
    "fpa-fod-401317993-sourdough": "NIFC",
    "fpa-fod-401321600-river-road-east": "USFS",
    "fpa-fod-401316681-bedrock": "USFS",
    "fpa-fod-401317844-prior": "USFS",
    "fpa-fod-401315421-rabbit": "NIFC",
    "fpa-fod-401308187-pass": "USFS",
    "fpa-fod-401321611-gray": "NIFC",
}
SCENARIO_NAMES = {
    "fpa-fod-401316132-hayden": "Hayden",
    "fpa-fod-401317993-sourdough": "Sourdough",
    "fpa-fod-401321600-river-road-east": "River Road East",
    "fpa-fod-401316681-bedrock": "Bedrock",
    "fpa-fod-401317844-prior": "Prior",
    "fpa-fod-401315421-rabbit": "Rabbit",
    "fpa-fod-401308187-pass": "Pass",
    "fpa-fod-401321611-gray": "Gray",
}
CROSS_SOURCE_PAIRS = (
    "fpa-fod-401316132-hayden",
    "fpa-fod-401321600-river-road-east",
    "fpa-fod-401317844-prior",
    "fpa-fod-401308187-pass",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attributes", type=Path, default=ATTRIBUTES)
    parser.add_argument("--extents", type=Path, default=EXTENTS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def signed_ring_area(ring: list[list[float]]) -> float:
    return sum(
        ring[index][0] * ring[index + 1][1]
        - ring[index + 1][0] * ring[index][1]
        for index in range(len(ring) - 1)
    ) / 2.0


def make_polygon(rings: list[list[list[float]]]) -> tuple[Any, int]:
    """Assemble Esri clockwise shells and counterclockwise holes by full containment."""
    shells: list[tuple[int, list[list[float]], Polygon]] = []
    holes: list[tuple[int, list[list[float]], Polygon]] = []
    for index, ring in enumerate(rings):
        if len(ring) < 4:
            continue
        polygon = Polygon(ring)
        if polygon.is_empty or polygon.area <= 0:
            continue
        item = (index, ring, polygon)
        if signed_ring_area(ring) < 0:
            shells.append(item)
        else:
            holes.append(item)

    assigned_holes: dict[int, list[list[list[float]]]] = {item[0]: [] for item in shells}
    orphan_holes: list[tuple[int, list[list[float]], Polygon]] = []
    for hole in holes:
        point = hole[2].representative_point()
        candidates = [shell for shell in shells if shell[2].contains(point)]
        containing_shells = [shell for shell in candidates if shell[2].covers(hole[2])]
        if not containing_shells:
            containing_shells = [
                shell for shell in shells
                if shell[2].area > hole[2].area and shell[2].covers(hole[2])
            ]
        if containing_shells:
            parent = min(containing_shells, key=lambda shell: shell[2].area)
            assigned_holes[parent[0]].append(hole[1])
        else:
            orphan_holes.append(hole)

    parts = [Polygon(shell[1], assigned_holes[shell[0]]) for shell in shells]
    # Keep unexpected uncontained rings visible in the validity result instead of dropping them.
    parts.extend(Polygon(hole[1]) for hole in orphan_holes)
    geometry = parts[0] if len(parts) == 1 else MultiPolygon(parts)
    return geometry, len(orphan_holes)


def build_requests(attribute_cases: list[dict[str, Any]]) -> list[tuple[str, str, int, str]]:
    by_id = {case["scenario_id"]: case for case in attribute_cases}
    if set(by_id) != set(PRIMARY_SERVICE):
        raise ValueError("attribute receipt must contain exactly the eight matched 2023 VALIDATION cases")

    requests: list[tuple[str, str, int, str]] = []
    for scenario_id, service in PRIMARY_SERVICE.items():
        feature = by_id[scenario_id].get(service.lower(), {})
        object_id = feature.get("objectid")
        if not isinstance(object_id, int):
            raise ValueError("missing exact {} objectid for {}".format(service, scenario_id))
        category = feature.get("feature_category", "unknown")
        requests.append((scenario_id, service, object_id, category))

    for scenario_id in CROSS_SOURCE_PAIRS:
        case = by_id[scenario_id]
        for service in ("USFS", "NIFC"):
            feature = case.get(service.lower(), {})
            object_id = feature.get("objectid")
            if not isinstance(object_id, int):
                raise ValueError("missing alternate-source {} objectid for {}".format(service, scenario_id))
            key = (scenario_id, service, object_id)
            if not any(row[:3] == key for row in requests):
                requests.append((scenario_id, service, object_id, feature.get("feature_category", "unknown")))
    return requests


def fetch_feature(
    request: tuple[str, str, int, str], extent_cases: dict[str, dict[str, Any]]
) -> tuple[tuple[str, str, int, str], bytes, list[list[list[float]]]]:
    scenario_id, service, object_id, _ = request
    output_wkid = extent_cases[scenario_id]["map_crs"].split(":")[-1]
    params = {
        "objectIds": str(object_id),
        "outFields": "OBJECTID",
        "returnGeometry": "true",
        "outSR": output_wkid,
        "f": "json",
    }
    url = ENDPOINTS[service] + "?" + urllib.parse.urlencode(params)
    web_request = urllib.request.Request(
        url, headers={"User-Agent": "wildfire-rl-adaptation validation perimeter QA"}
    )
    with urllib.request.urlopen(web_request, timeout=60) as response:
        raw = response.read()
    payload = json.loads(raw)
    features = payload.get("features", [])
    if "error" in payload or len(features) != 1:
        raise RuntimeError("{} object {} did not return exactly one feature".format(service, object_id))
    rings = features[0].get("geometry", {}).get("rings", [])
    if not rings:
        raise RuntimeError("{} object {} did not return polygon rings".format(service, object_id))
    return request, raw, rings


def calculate_feature(
    request: tuple[str, str, int, str],
    raw: bytes,
    rings: list[list[list[float]]],
    attribute_cases: dict[str, dict[str, Any]],
    extent_cases: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], Any, list[list[list[float]]]]:
    scenario_id, service, object_id, category = request
    source_attributes = attribute_cases[scenario_id][service.lower()]
    extent_case = extent_cases[scenario_id]
    geometry, orphan_count = make_polygon(rings)
    valid = bool(geometry.is_valid) and orphan_count == 0
    crop = box(*extent_case["map_bounds_m"])
    bounds = geometry.bounds
    all_coordinates = [point for ring in rings for point in ring]
    vertex_bounds = [
        min(point[0] for point in all_coordinates),
        min(point[1] for point in all_coordinates),
        max(point[0] for point in all_coordinates),
        max(point[1] for point in all_coordinates),
    ]
    envelope = extent_case["perimeter_extent_m"]
    margins = [
        vertex_bounds[0] - envelope[0],
        vertex_bounds[1] - envelope[1],
        envelope[2] - vertex_bounds[2],
        envelope[3] - vertex_bounds[3],
    ]
    area_acres = geometry.area / M2_PER_ACRE if valid else None
    intersection_area = geometry.intersection(crop).area if valid else None
    columns = math.ceil((vertex_bounds[2] - vertex_bounds[0]) / 30.0)
    rows = math.ceil((vertex_bounds[3] - vertex_bounds[1]) / 30.0)
    fpa_acres = attribute_cases[scenario_id]["fpa_reported_final_area_acres"]
    source_gis_acres = source_attributes.get("gis_acres")
    result = {
        "scenario_id": scenario_id,
        "service": service,
        "objectid": object_id,
        "feature_category": category,
        "requested_output_crs": extent_case["map_crs"],
        "response_bytes": len(raw),
        "ring_count": len(rings),
        "vertex_count": sum(map(len, rings)),
        "orphan_counterclockwise_rings": orphan_count,
        "geometry_valid": valid,
        "geometry_validity_reason": explain_validity(geometry),
        "projected_vertex_bounds_m": [round(float(value), 3) for value in vertex_bounds],
        "extent_only_envelope_margin_m": [round(float(value), 3) for value in margins],
        "extent_only_envelope_contains_vertices_with_0_05m_tolerance": all(
            margin >= -0.05 for margin in margins
        ),
        "projected_polygon_area_acres": round(area_acres, 2) if area_acres is not None else None,
        "source_reported_gis_acres": source_gis_acres,
        "source_reported_incident_size_acres": source_attributes.get(
            "incident_size_acres", source_attributes.get("total_acres")
        ),
        "fpa_reported_final_area_acres": fpa_acres,
        "projected_area_difference_from_fpa_pct": (
            round(100.0 * (area_acres - fpa_acres) / fpa_acres, 3)
            if area_acres is not None and fpa_acres
            else None
        ),
        "projected_area_difference_from_service_gis_acres_pct": (
            round(100.0 * (area_acres - source_gis_acres) / source_gis_acres, 3)
            if area_acres is not None and source_gis_acres
            else None
        ),
        "area_inside_current_map_acres": (
            round(intersection_area / M2_PER_ACRE, 2) if intersection_area is not None else None
        ),
        "percent_polygon_area_inside_current_map": (
            round(100.0 * intersection_area / geometry.area, 3)
            if intersection_area is not None and geometry.area
            else None
        ),
        "percent_current_map_area_inside_polygon": (
            round(100.0 * intersection_area / crop.area, 3)
            if intersection_area is not None
            else None
        ),
        "intersects_current_map": bool(geometry.intersects(crop)) if valid else None,
        "minimum_rectangular_grid_at_30m": {
            "columns": columns,
            "rows": rows,
            "cells": columns * rows,
            "times_current_128x128_cells": round(columns * rows / (128 * 128), 1),
        },
    }
    return result, geometry, rings


def draw_figure(
    figure_path: Path,
    primary_results: list[dict[str, Any]],
    geometries: dict[str, tuple[Any, list[list[list[float]]]]],
    extent_cases: dict[str, dict[str, Any]],
) -> None:
    os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "wildfire-mplconfig"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch, Rectangle

    by_id = {item["scenario_id"]: item for item in primary_results}
    fig, axes = plt.subplots(4, 2, figsize=(14, 19), facecolor="#f6f8fa")
    fig.suptitle(
        "Javni obodi požara naspram trenutne SimFire karte",
        fontsize=20,
        fontweight="bold",
        y=0.99,
        color="#14212b",
    )
    fig.text(
        0.5,
        0.968,
        "2023 VALIDATION • 30 m ćelije • nijedan poligon nije korišten kao ulaz agenta",
        ha="center",
        fontsize=11,
        color="#44515c",
    )
    for axis, scenario_id in zip(axes.flat, PRIMARY_SERVICE):
        record = by_id[scenario_id]
        extent = extent_cases[scenario_id]
        xmin, ymin, xmax, ymax = extent["map_bounds_m"]
        center_x, center_y = (xmin + xmax) / 2.0, (ymin + ymax) / 2.0
        _, rings = geometries[scenario_id]
        for ring in rings:
            axis.plot(
                [point[0] / 1000.0 - center_x / 1000.0 for point in ring],
                [point[1] / 1000.0 - center_y / 1000.0 for point in ring],
                color="#183b56",
                linewidth=0.58,
                alpha=0.82,
                zorder=3,
            )
        axis.add_patch(
            Rectangle(
                (xmin / 1000.0 - center_x / 1000.0, ymin / 1000.0 - center_y / 1000.0),
                (xmax - xmin) / 1000.0,
                (ymax - ymin) / 1000.0,
                facecolor="#f4a261",
                edgecolor="#c44536",
                linewidth=1.5,
                alpha=0.38,
                zorder=2,
            )
        )
        all_x = [point[0] / 1000.0 - center_x / 1000.0 for ring in rings for point in ring]
        all_y = [point[1] / 1000.0 - center_y / 1000.0 for ring in rings for point in ring]
        pad = max(0.45, 0.07 * max(max(all_x) - min(all_x), max(all_y) - min(all_y)))
        axis.set_xlim(min(min(all_x), -1.92) - pad, max(max(all_x), 1.92) + pad)
        axis.set_ylim(min(min(all_y), -1.92) - pad, max(max(all_y), 1.92) + pad)
        axis.set_aspect("equal", adjustable="box")
        axis.grid(color="#89949c", alpha=0.18, linewidth=0.6)
        axis.set_facecolor("#ffffff")
        axis.tick_params(labelsize=8, colors="#57636d")
        source_feature = next(
            feature for feature in primary_results if feature["scenario_id"] == scenario_id
        )
        category = source_feature["feature_category"].lower()
        label = "završni obod" if "final" in category else "dnevni obod (vrijeme nije potvrđeno)"
        axis.set_title(
            "{} · {} {}".format(SCENARIO_NAMES[scenario_id], source_feature["service"], label),
            fontsize=11,
            fontweight="bold",
            loc="left",
            color="#14212b",
            pad=8,
        )
        axis.text(
            0.02,
            0.97,
            "{:.1f}% oboda unutar karte".format(
                source_feature["percent_polygon_area_inside_current_map"]
            ),
            transform=axis.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            fontweight="bold",
            color="#9b3a2d",
            bbox={"boxstyle": "round,pad=.28", "facecolor": "#fff9f4", "edgecolor": "#ecc7b8", "alpha": 0.95},
        )
        axis.set_xlabel("Kilometri od centra karte (istok)", fontsize=8)
        axis.set_ylabel("Kilometri od centra karte (sjever)", fontsize=8)

    fig.legend(
        handles=[
            Line2D([0], [0], color="#183b56", linewidth=1.2, label="Poligon javnog oboda"),
            Patch(
                facecolor="#f4a261",
                edgecolor="#c44536",
                alpha=0.45,
                label="Postojeća 128×128 karta (3.84×3.84 km)",
            ),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.94),
        ncol=2,
        frameon=False,
        fontsize=10,
    )
    fig.text(
        0.5,
        0.014,
        "Preklop mjeri samo dio opaženog obrisa unutar današnje karte. To nije poređenje simulacije sa rastom požara.",
        ha="center",
        fontsize=10,
        color="#44515c",
    )
    fig.subplots_adjust(top=0.865, bottom=0.06, hspace=0.30, wspace=0.20)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    args = parse_args()
    if not args.attributes.is_file() or not args.extents.is_file():
        raise FileNotFoundError("attribute and extent receipts are required")
    if not args.overwrite and (args.out.exists() or args.figure.exists()):
        raise FileExistsError("output exists; pass --overwrite to replace the receipt and figure")

    attribute_receipt = json.loads(args.attributes.read_text(encoding="utf-8"))
    extent_receipt = json.loads(args.extents.read_text(encoding="utf-8"))
    if attribute_receipt.get("scope", {}).get("split", "").upper() != "VALIDATION":
        raise ValueError("input attribute receipt is not restricted to VALIDATION")
    if extent_receipt.get("scope", {}).get("split", "").upper() != "VALIDATION":
        raise ValueError("input extent receipt is not restricted to VALIDATION")
    attribute_cases = {item["scenario_id"]: item for item in attribute_receipt["cases"]}
    extent_cases = {item["scenario_id"]: item for item in extent_receipt["cases"]}
    if set(attribute_cases) != set(PRIMARY_SERVICE) or set(extent_cases) != set(PRIMARY_SERVICE):
        raise ValueError("both input receipts must contain exactly the eight frozen validation matches")

    requests = build_requests(attribute_receipt["cases"])
    fetched: dict[tuple[str, str], tuple[tuple[str, str, int, str], bytes, list[list[list[float]]]]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fetch_feature, item, extent_cases) for item in requests]
        for future in concurrent.futures.as_completed(futures):
            request, raw, rings = future.result()
            fetched[(request[0], request[1])] = (request, raw, rings)

    details: list[dict[str, Any]] = []
    geometries: dict[str, tuple[Any, list[list[list[float]]]]] = {}
    for scenario_id, service in PRIMARY_SERVICE.items():
        request, raw, rings = fetched[(scenario_id, service)]
        detail, geometry, _ = calculate_feature(
            request, raw, rings, attribute_cases, extent_cases
        )
        details.append(detail)
        geometries[scenario_id] = (geometry, rings)

    pairs = []
    for scenario_id in CROSS_SOURCE_PAIRS:
        nifc_geometry = calculate_feature(
            *fetched[(scenario_id, "NIFC")], attribute_cases, extent_cases
        )[1]
        usfs_geometry = calculate_feature(
            *fetched[(scenario_id, "USFS")], attribute_cases, extent_cases
        )[1]
        both_valid = bool(nifc_geometry.is_valid and usfs_geometry.is_valid)
        if both_valid:
            union_area = nifc_geometry.union(usfs_geometry).area
            difference = nifc_geometry.symmetric_difference(usfs_geometry).area
            hausdorff_m = nifc_geometry.hausdorff_distance(usfs_geometry)
            pairs.append({
                "scenario_id": scenario_id,
                "both_valid": True,
                "symmetric_difference_percent_of_union": round(100.0 * difference / union_area, 6),
                "hausdorff_distance_m": round(hausdorff_m, 6),
                "nifc_area_acres": round(nifc_geometry.area / M2_PER_ACRE, 2),
                "usfs_area_acres": round(usfs_geometry.area / M2_PER_ACRE, 2),
                "near_identical_within_1mm": hausdorff_m < 0.001,
                "interpretation": "Cross-publication consistency, not independent survey evidence.",
            })
        else:
            pairs.append({"scenario_id": scenario_id, "both_valid": False})

    valid = [item for item in details if item["geometry_valid"]]
    area_differences = [abs(item["projected_area_difference_from_fpa_pct"]) for item in valid]
    polygon_coverage = [item["percent_polygon_area_inside_current_map"] for item in valid]
    cell_ratios = [item["minimum_rectangular_grid_at_30m"]["times_current_128x128_cells"] for item in details]
    cell_columns = [item["minimum_rectangular_grid_at_30m"]["columns"] for item in details]
    cell_rows = [item["minimum_rectangular_grid_at_30m"]["rows"] for item in details]
    largest = max(details, key=lambda item: item["minimum_rectangular_grid_at_30m"]["cells"])
    summary = {
        "exact_features_queried": len(requests),
        "primary_features_queried": len(details),
        "alternate_cross_source_features_queried": len(requests) - len(details),
        "validation_incidents": len(details),
        "valid_primary_geometries": len(valid),
        "all_geometry_vertices_within_extent_only_bounds_to_0_05m": all(
            item["extent_only_envelope_contains_vertices_with_0_05m_tolerance"] for item in details
        ),
        "primary_shapes_intersecting_current_map": sum(
            item["intersects_current_map"] is True for item in details
        ),
        "fraction_of_polygon_area_inside_current_map_percent_range": [
            min(polygon_coverage), max(polygon_coverage)
        ],
        "maximum_absolute_projected_area_difference_from_fpa_percent": round(max(area_differences), 3),
        "minimum_rectangular_grid_columns_range": [min(cell_columns), max(cell_columns)],
        "minimum_rectangular_grid_rows_range": [min(cell_rows), max(cell_rows)],
        "minimum_rectangular_grid_cell_ratio_range_vs_128x128": [min(cell_ratios), max(cell_ratios)],
        "largest_footprint_case": SCENARIO_NAMES[largest["scenario_id"]],
        "largest_footprint_grid": [
            largest["minimum_rectangular_grid_at_30m"]["columns"],
            largest["minimum_rectangular_grid_at_30m"]["rows"],
        ],
        "four_cross_service_pairs_within_1mm": all(
            pair.get("near_identical_within_1mm", False) for pair in pairs
        ),
    }

    report = {
        "kind": "validation_perimeter_polygon_crop_qc",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": {
            "cohort": extent_receipt["scope"]["cohort"],
            "split": "VALIDATION",
            "incident_year": 2023,
            "validation_incidents": len(details),
            "exact_feature_ids_queried": len(requests),
            "query_breakdown": "8 primary validation polygons plus 4 alternate-source duplicates.",
            "return_geometry": True,
            "geometry_output_crs": "each incident's existing raster CRS",
            "raw_shapes_saved": False,
            "full_geometry_held_in_memory_for_qc_and_plot_only": True,
            "2024_TEST_data_or_geometry_opened": False,
            "simulator_advanced": False,
            "policy_evaluation": False,
            "agent_training": False,
        },
        "sources": extent_receipt["sources"],
        "method": {
            "selected_primary_source_by_scenario": PRIMARY_SERVICE,
            "ring_topology": "Esri clockwise exterior and counterclockwise interior rings; a hole is assigned to the smallest exterior that covers its full ring.",
            "area": "Planar area in each local UTM raster CRS; approximate acreage check, not authoritative geodesic area.",
            "map_overlap": "Exact vector intersection with the existing raster bounding rectangle, measuring map footprint only.",
            "grid_size": "Projected polygon vertex bounds divided by 30 m and rounded up per axis; excludes safety margin and does not estimate runtime or memory.",
            "extent_comparison": "Extent-only envelopes contain projected geometry vertices within a 0.05 m numeric tolerance; these are separate service response products.",
        },
        "summary": summary,
        "primary_case_results": details,
        "cross_service_shape_comparison": pairs,
        "source_attribute_discrepancies": [
            {
                "scenario_id": "fpa-fod-401317844-prior",
                "service": "NIFC",
                "objectid": 21475,
                "published_gis_acres": 0.1,
                "published_incident_size_acres": 12833,
                "projected_polygon_area_acres": next(
                    item["projected_polygon_area_acres"]
                    for item in details
                    if item["scenario_id"] == "fpa-fod-401317844-prior"
                ),
                "interpretation": "NIFC GIS-acre attribute conflicts with both the outline and incident-reported size.",
            },
            {
                "scenario_id": "fpa-fod-401321611-gray",
                "service": "NIFC",
                "objectid": 23496,
                "published_gis_acres": 200,
                "published_incident_size_acres": 10064,
                "projected_polygon_area_acres": next(
                    item["projected_polygon_area_acres"]
                    for item in details
                    if item["scenario_id"] == "fpa-fod-401321611-gray"
                ),
                "interpretation": "NIFC GIS-acre attribute conflicts with both the outline and incident-reported size.",
            },
        ],
        "limitations": [
            "These observed perimeters are mostly final shapes, not a dated sequence of growth; Bedrock and Rabbit daily feature times are unverified.",
            "Final polygons are not starting conditions, agent observations, rewards, or training labels.",
            "Map overlap does not validate spread timing, suppression effects, timestamp alignment, or fuel/weather alignment.",
            "Extent-only envelopes are more conservative than projected polygon vertex bounds; both receipts are retained.",
            "Cross-service shape agreement is publication consistency and may reflect shared geometry, not independent confirmation.",
            "No 2024 TEST data or geometry was queried. No simulation, policy evaluation, or training was run.",
        ],
        "visualization": str(args.figure.relative_to(ROOT)) if args.figure.is_relative_to(ROOT) else str(args.figure),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    draw_figure(args.figure, details, geometries, extent_cases)
    print(
        "validation_cases={} valid_shapes={} map_coverage={:.1f}-{:.1f}% largest_grid={}x{} test_opened=false training=false".format(
            len(details), len(valid), min(polygon_coverage), max(polygon_coverage),
            largest["minimum_rectangular_grid_at_30m"]["columns"],
            largest["minimum_rectangular_grid_at_30m"]["rows"],
        )
    )
    print(args.out)
    print(args.figure)


if __name__ == "__main__":
    main()
