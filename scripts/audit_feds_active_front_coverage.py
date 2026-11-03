#!/usr/bin/env python3
"""Check exact-time FEDS active-front coverage for the approved episode manifest.

The active line is a satellite-derived FEDS front, not a crew-built suppression line.
This audit only reads the episode's initial FEDS timestamp and its matching perimeter.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # Import works as a module and when called as ``python scripts/...py``.
    from scripts.audit_feds_fpa_fle_crosswalk import FEDS_FILE_MD5, _feds_file_path
except ModuleNotFoundError:
    from audit_feds_fpa_fle_crosswalk import FEDS_FILE_MD5, _feds_file_path


ROOT = Path(__file__).resolve().parents[1]
EPISODE_MANIFEST = ROOT / "data/manifests/feds-episode-cohort-v1.json"
DEFAULT_OUTPUT = ROOT / "reports/real-fire-data/feds-active-front-coverage-v1.json"


def _key(fire_id: Any, timestamp: Any) -> tuple[str, str]:
    """Normalize FlatGeobuf's numeric fireID and ISO timestamp fields."""
    return str(int(fire_id)), str(timestamp)


def audit_front_coverage(manifest_path: Path = EPISODE_MANIFEST) -> dict[str, Any]:
    try:
        import fiona
        from shapely.geometry import shape
        from shapely.ops import unary_union
    except ImportError as exc:  # pragma: no cover - optional GIS environment
        raise RuntimeError("Install the optional GIS dependencies to audit FEDS geometry.") from exc

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("test_cases_loaded") is not False:
        raise ValueError("The episode manifest must explicitly state that test cases are not loaded.")
    cases = manifest.get("cases", [])
    if not cases or any(case.get("split") not in {"train", "validation"} for case in cases):
        raise ValueError("Expected a non-empty train/validation-only episode manifest.")

    cases_by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)
    references: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        year = int(case["event"]["year"])
        ref = case["evaluation_reference"]
        key = _key(ref["source_fire_id"], ref["initial_state_time"])
        references[key].append(case)
        cases_by_year[year].append(case)

    by_case: dict[str, dict[str, Any]] = {}
    source_checksums: dict[str, dict[str, str]] = {}
    for year, year_cases in sorted(cases_by_year.items()):
        line_path = Path(_feds_file_path(year, "fireline"))
        perimeter_path = Path(_feds_file_path(year, "perimeter"))
        source_checksums[str(year)] = {
            "fireline_md5": FEDS_FILE_MD5["fireline"][year],
            "perimeter_md5": FEDS_FILE_MD5["perimeter"][year],
        }
        selected_keys = {
            _key(
                case["evaluation_reference"]["source_fire_id"],
                case["evaluation_reference"]["initial_state_time"],
            )
            for case in year_cases
        }
        lines: dict[tuple[str, str], list[Any]] = defaultdict(list)
        perimeters: dict[tuple[str, str], list[Any]] = defaultdict(list)

        for path, sink in ((line_path, lines), (perimeter_path, perimeters)):
            with fiona.open(path) as source:
                for feature in source:
                    props = feature["properties"]
                    if props.get("fireID") is None or props.get("t") is None:
                        continue
                    key = _key(props.get("fireID"), props.get("t"))
                    if key in selected_keys and feature.get("geometry"):
                        sink[key].append(shape(feature["geometry"]))

        for key in selected_keys:
            line_parts = lines.get(key, [])
            perimeter_parts = perimeters.get(key, [])
            if not line_parts or not perimeter_parts:
                status = "missing_exact_timestamp_geometry"
                line_length_m = None
                overlap_fraction = None
                boundary_distance_m = None
                line_geometry_types: list[str] = []
            else:
                line = unary_union(line_parts)
                perimeter = unary_union(perimeter_parts)
                boundary = perimeter.boundary
                line_length_m = float(line.length)
                overlap_length_m = float(line.intersection(boundary).length)
                overlap_fraction = overlap_length_m / line_length_m if line_length_m else 0.0
                boundary_distance_m = float(line.distance(boundary))
                within_source_pixel_length_m = float(line.intersection(boundary.buffer(375.0)).length)
                within_source_pixel_fraction = (
                    within_source_pixel_length_m / line_length_m if line_length_m else 0.0
                )
                status = "exact_timestamp_front_and_perimeter_available"
                line_geometry_types = sorted({part.geom_type for part in line_parts})
            for case in references[key]:
                by_case[case["scenario_id"]] = {
                    "scenario_id": case["scenario_id"],
                    "split": case["split"],
                    "year": year,
                    "feds_fire_id": key[0],
                    "initial_state_time": key[1],
                    "status": status,
                    "active_front_feature_count": len(line_parts),
                    "perimeter_feature_count": len(perimeter_parts),
                    "active_front_geometry_types": line_geometry_types,
                    "active_front_length_m": line_length_m,
                    "fraction_of_front_overlapping_perimeter_boundary": overlap_fraction,
                    "fraction_of_front_within_375m_of_perimeter_boundary": within_source_pixel_fraction,
                    "distance_to_perimeter_boundary_m": boundary_distance_m,
                }

    case_rows = [by_case[case["scenario_id"]] for case in cases]
    available = [row for row in case_rows if row["status"] == "exact_timestamp_front_and_perimeter_available"]
    overlap_values = [row["fraction_of_front_overlapping_perimeter_boundary"] for row in available]
    distances = [row["distance_to_perimeter_boundary_m"] for row in available]
    lengths = [row["active_front_length_m"] for row in available]

    split_summary: dict[str, Any] = {}
    for split in ("train", "validation"):
        rows = [row for row in case_rows if row["split"] == split]
        split_summary[split] = {
            "episode_count": len(rows),
            "exact_front_count": sum(row["status"] == "exact_timestamp_front_and_perimeter_available" for row in rows),
            "missing_front_count": sum(row["status"] != "exact_timestamp_front_and_perimeter_available" for row in rows),
        }

    return {
        "schema_version": "feds-active-front-coverage/1.0",
        "kind": "data_coverage_audit_not_simulation_or_physical_validation",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "episode_manifest": manifest_path.relative_to(ROOT).as_posix(),
        "episode_manifest_sha256": _sha256_file(manifest_path),
        "test_cases_loaded": False,
        "source": {
            "dataset": "FEDS-CONUS v1 lf_fireline and lf_perimeter",
            "record": "https://zenodo.org/records/22921773",
            "spatial_temporal_resolution_note": "FEDS active fronts/perimeters are 12-hourly products derived from VIIRS detections with 375 m nominal pixel resolution.",
            "meaning": "satellite-estimated active front; not a constructed suppression line",
            "checksums_md5": source_checksums,
        },
        "matching_rule": "Exact episode source_fire_id plus exact initial_state_time; no future timestamp used to create the initial front.",
        "coverage": {
            "episode_count": len(case_rows),
            "exact_active_front_count": len(available),
            "missing_active_front_count": len(case_rows) - len(available),
            "fraction": len(available) / len(case_rows),
            "all_fronts_intersect_matching_perimeter": bool(available)
            and all(value == 0.0 for value in distances),
            "median_front_length_m": statistics.median(lengths) if lengths else None,
            "median_boundary_overlap_fraction": statistics.median(overlap_values) if overlap_values else None,
            "minimum_boundary_overlap_fraction": min(overlap_values) if overlap_values else None,
            "minimum_front_fraction_within_375m_of_perimeter_boundary": min(
                row["fraction_of_front_within_375m_of_perimeter_boundary"] for row in available
            ) if available else None,
            "max_distance_to_perimeter_boundary_m": max(distances) if distances else None,
        },
        "by_split": split_summary,
        "feature_geometry_types": dict(Counter(
            geometry_type
            for row in available
            for geometry_type in row["active_front_geometry_types"]
        )),
        "cases": case_rows,
        "limitations": [
            "FEDS is a satellite-derived estimate, not a ground-truth fire edge.",
            "This verifies exact-time vector availability and geometric alignment only; it does not assess SimFire spread or suppression effects.",
            "Source event identity still depends on the documented provisional FPA-FOD to FEDS crosswalk.",
        ],
    }


def _sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=EPISODE_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    report = audit_front_coverage(args.manifest)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    coverage = report["coverage"]
    print(
        "exact initial FEDS active fronts: {}/{}; train {}/{}; validation {}/{}".format(
            coverage["exact_active_front_count"], coverage["episode_count"],
            report["by_split"]["train"]["exact_front_count"], report["by_split"]["train"]["episode_count"],
            report["by_split"]["validation"]["exact_front_count"], report["by_split"]["validation"]["episode_count"],
        )
    )
    print(f"wrote {args.out}")
    return 0 if coverage["missing_active_front_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
