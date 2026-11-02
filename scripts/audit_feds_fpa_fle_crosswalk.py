#!/usr/bin/env python3
"""Audit a train/validation FPA-FOD ↔ FEDS-CONUS ↔ FLE incident crosswalk.

FEDS-CONUS annual FlatGeobuf files are read remotely through GDAL byte ranges;
the script does not download the annual archives. Only the train and validation
cases present in the input manifest are inspected. Historical final area and
perimeter are deliberately not used to select a FEDS event.

Optional runtime dependencies are installed with ``pip install -e '.[geo]'``.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ZENODO_RECORD = "https://zenodo.org/api/records/22921773"
ZENODO_LANDING = "https://zenodo.org/records/22921773"
FEDS_FILE_URL = (
    "https://zenodo.org/api/records/22921773/files/"
    "feds_{year}_lf_perimeter.fgb/content"
)
FPA_FOD_SOURCE = "https://www.fs.usda.gov/rds/archive/products/RDS-2013-0009.7"
WFIGS_QUERY = (
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/ArcGIS/rest/services/"
    "WFIGS_Interagency_Perimeters/FeatureServer/0/query"
)
FLE_QUERY = (
    "https://services1.arcgis.com/KNdRU5cN6ENqCTjk/ArcGIS/rest/services/"
    "Fireline_Engagement_Grouped_Line_Polygons/FeatureServer/2/query"
)
FEDS_EPSG_FALLBACK = "EPSG:9311"
FEDS_TIME_STEP = timedelta(hours=12)
FEDS_LOCAL_CACHE = Path(__file__).resolve().parents[1] / ".local/feds-conus"
FEDS_FILE_MD5 = {
    2018: "c205abae4b12544e6cfb2d754a21981c",
    2019: "3b921e9a28d045ffcf3015f893ed5831",
    2023: "ad32170e694e42127f3b865d93e1a81a",
}


def _md5_file(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _feds_file_path(year: int) -> str:
    """Prefer a checksum-verified local archive; otherwise use remote byte ranges."""
    filename = f"feds_{year}_lf_perimeter.fgb"
    local_path = FEDS_LOCAL_CACHE / filename
    if local_path.is_file():
        expected_md5 = FEDS_FILE_MD5.get(year)
        if expected_md5 is None:
            raise ValueError(f"No pinned checksum is recorded for local FEDS year {year}.")
        actual_md5 = _md5_file(local_path)
        if actual_md5 != expected_md5:
            raise ValueError(
                f"Local FEDS archive checksum mismatch for {year}: {local_path} "
                f"({actual_md5} != {expected_md5})."
            )
        return str(local_path)
    return "/vsicurl/" + FEDS_FILE_URL.format(year=year)


def parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    # FEDS `t` values are naive half-day observation timestamps. Keep them naive;
    # no timezone is invented for the FPA-FOD reported calendar date either.
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def parse_discovery_date(value: str) -> date:
    """Read FPA-FOD discovery date, whose reported HHMM may be unavailable."""
    text = str(value).strip()
    date_text = text.split(" ", 1)[0]
    return date.fromisoformat(date_text)


def consecutive_halfday_run(values: Iterable[datetime]) -> int:
    """Return the longest run of unique timestamps exactly 12 hours apart."""
    times = sorted(set(values))
    if not times:
        return 0
    longest = current = 1
    for previous, current_time in zip(times, times[1:]):
        if current_time - previous == FEDS_TIME_STEP:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
    return longest


def filter_report_to_start_window(
    source_report: dict[str, Any],
    *,
    source_path: str | None = None,
    derivation_note: str | None = None,
) -> dict[str, Any]:
    """Apply the strict first-24-hour proximity rule to a saved candidate report.

    Candidate summaries retain the earliest timestamp of any perimeter inside the
    fixed spatial radius. That timestamp is sufficient to decide whether a
    candidate had an in-radius perimeter between ``t_st`` and ``t_st + 24h``.
    This supports reproducible re-filtering when the remote archive is unavailable.
    """
    if source_report.get("schema_version") != "fpa-feds-fle-crosswalk/1.0":
        raise ValueError("Unexpected source report schema.")
    if source_report.get("test_cases_loaded") is not False:
        raise ValueError("Source report must affirm that no test cases were loaded.")
    if source_report.get("crosswalk_derivation"):
        raise ValueError("Refusing to post-filter a report that is already derived.")

    report = deepcopy(source_report)
    for case in report.get("cases", []):
        feds = case.get("feds", {})
        filtered = []
        for candidate in feds.get("candidates", []):
            try:
                start_time = datetime.fromisoformat(candidate["t_start"])
                first_in_radius = datetime.fromisoformat(candidate["first_observed_state"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Candidate in {case.get('scenario_id')} lacks valid earliest timestamps."
                ) from exc
            if start_time <= first_in_radius <= start_time + timedelta(hours=24):
                filtered.append(candidate)

        feds["candidate_rule"] = (
            "FEDS t_st date within -1/+2 days of FPA-FOD discovery date and at least "
            "one perimeter observed during the first 24 hours after t_st within the "
            "fixed search radius of the FPA-FOD reference point; a match is counted "
            "only when unique."
        )
        feds["candidates"] = filtered
        feds["candidate_count"] = len(filtered)
        if len(filtered) == 1:
            feds["selected"] = filtered[0]
            feds["status"] = "unique_spatiotemporal_candidate"
        elif not filtered:
            feds["selected"] = None
            feds["status"] = "no_candidate"
        else:
            feds["selected"] = None
            feds["status"] = "ambiguous_candidates"

    summary = {}
    for split in report.get("audited_splits", []):
        subset = [case for case in report.get("cases", []) if case.get("split") == split]
        summary[split] = {
            "cases": len(subset),
            "unique_feds_matches": sum(
                case["feds"]["status"] == "unique_spatiotemporal_candidate"
                for case in subset
            ),
            "two_consecutive_feds_states": sum(
                bool(case["feds"].get("selected"))
                and case["feds"]["selected"]["two_consecutive_12h_states"]
                for case in subset
            ),
            "full_48h_feds_reference": sum(
                bool(case["feds"].get("selected"))
                and case["feds"]["selected"]["five_states_cover_48h"]
                for case in subset
            ),
            "fle_summary_present": sum(
                bool(case["feds"].get("fle", {}).get("fle_summary_present"))
                for case in subset
            ),
        }
    report["summary"] = summary
    report["created_utc"] = datetime.now(timezone.utc).isoformat()
    report["pre_agent_data_gate"] = {
        "threshold": {
            "train_two_state_minimum": 20,
            "validation_two_state_minimum": 8,
        },
        "pass": None,
        "status": "incomplete",
        "instruction": (
            "A split-only audit is incomplete; combine matching train and validation "
            "reports before evaluating the gate."
        ),
    }
    report["crosswalk_derivation"] = {
        "method": "deterministic_early_window_postfilter",
        "source_report": source_path,
        "source_created_utc": source_report.get("created_utc"),
        "rule": (
            "Keep a candidate only when its earliest recorded in-radius perimeter "
            "timestamp is between t_st and t_st + 24 hours inclusive. The candidate "
            "report records that earliest timestamp and complete temporal run "
            "summaries, so this reproduces the strict time predicate without an "
            "additional archive read."
        ),
        "note": derivation_note,
    }
    return report


def _as_fire_id(value: Any) -> str:
    if isinstance(value, (float, int)) and math.isfinite(float(value)):
        numeric = float(value)
        return str(int(numeric)) if numeric.is_integer() else str(numeric)
    return str(value)


def _sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _fetch_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if params:
        url = f"{url}?{urlencode(params, doseq=True)}"
    request = Request(
        url,
        headers={"User-Agent": "wildfire-rl-adaptation-crosswalk-audit/1.0"},
    )
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def _query_arcgis_all(url: str, where: str, out_fields: str) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    offset = 0
    page_size = 2000
    while True:
        payload = _fetch_json(
            url,
            {
                "f": "json",
                "where": where,
                "outFields": out_fields,
                "returnGeometry": "false",
                "resultOffset": offset,
                "resultRecordCount": page_size,
                "orderByFields": "OBJECTID ASC",
            },
        )
        if payload.get("error"):
            raise RuntimeError(f"ArcGIS query failed: {payload['error']}")
        page = payload.get("features", [])
        features.extend(page)
        if len(page) < page_size:
            break
        offset += len(page)
    return features


def _zenodo_provenance() -> dict[str, Any]:
    record = _fetch_json(ZENODO_RECORD)
    metadata = record.get("metadata", {})
    files_by_name = {item["key"]: item for item in record.get("files", [])}
    return {
        "record_url": ZENODO_LANDING,
        "record_id": str(record.get("id", "22921773")),
        "version": metadata.get("version") or "v1",
        "published": metadata.get("publication_date") or metadata.get("created") or record.get("created"),
        "license": (metadata.get("license") or {}).get("id"),
        "perimeter_files": {
            str(year): {
                "filename": f"feds_{year}_lf_perimeter.fgb",
                "size_bytes": files_by_name[f"feds_{year}_lf_perimeter.fgb"]["size"],
                "checksum": files_by_name[f"feds_{year}_lf_perimeter.fgb"]["checksum"],
                "download_url": files_by_name[f"feds_{year}_lf_perimeter.fgb"]["links"]["self"],
            }
            for year in (2018, 2019, 2023)
            if f"feds_{year}_lf_perimeter.fgb" in files_by_name
        },
    }


def _feds_case_candidates(
    collection: Any,
    transformer: Any,
    case: dict[str, Any],
    radius_m: float,
) -> list[dict[str, Any]]:
    from shapely.geometry import Point, shape

    point_x, point_y = transformer.transform(case["longitude"], case["latitude"])
    point = Point(point_x, point_y)
    bbox = (
        point_x - radius_m,
        point_y - radius_m,
        point_x + radius_m,
        point_y + radius_m,
    )
    discovery = parse_discovery_date(case["discovery_time"])
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    # Use Fiona's collection.filter spatial filter. Passing bbox to open() is an
    # open option and can be ignored, causing a full sequential archive scan.
    for feature in collection.filter(bbox=bbox):
        properties = feature["properties"]
        fire_id = properties.get("fireID")
        start_time = parse_timestamp(properties.get("t_st"))
        observed_time = parse_timestamp(properties.get("t"))
        geometry = feature.get("geometry")
        if fire_id is None or start_time is None or observed_time is None or not geometry:
            continue
        start_offset_days = (start_time.date() - discovery).days
        if not -1 <= start_offset_days <= 2:
            continue
        try:
            distance_m = shape(geometry).distance(point)
        except Exception:
            continue
        if distance_m > radius_m:
            continue
        key = (_as_fire_id(fire_id), start_time.isoformat())
        grouped[key].append(
            {
                "observed_time": observed_time,
                "distance_m": distance_m,
                "area_km2": properties.get("farea"),
                "n_newpixels": properties.get("n_newpixels"),
                "t_ed": properties.get("t_ed"),
            }
        )

    candidates = []
    for (fire_id, start_text), rows in grouped.items():
        start_time = datetime.fromisoformat(start_text)
        start_window_rows = [
            row
            for row in rows
            if start_time <= row["observed_time"] <= start_time + timedelta(hours=24)
        ]
        if not start_window_rows:
            continue
        minimum_start_distance_m = min(row["distance_m"] for row in start_window_rows)
        if minimum_start_distance_m > radius_m:
            continue
        times = sorted({row["observed_time"] for row in rows})
        longest_run = consecutive_halfday_run(times)
        areas = [float(row["area_km2"]) for row in rows if row["area_km2"] is not None]
        candidates.append(
            {
                "fire_id": fire_id,
                "t_start": start_text,
                "discovery_date_offset_days": (start_time.date() - discovery).days,
                "minimum_start_window_distance_m": round(minimum_start_distance_m, 1),
                "observed_states_in_spatial_window": len(times),
                "longest_12h_run": longest_run,
                "two_consecutive_12h_states": longest_run >= 2,
                "five_states_cover_48h": longest_run >= 5,
                "first_observed_state": times[0].isoformat() if times else None,
                "last_observed_state": times[-1].isoformat() if times else None,
                "area_range_km2_in_spatial_window": (
                    [round(min(areas), 3), round(max(areas), 3)] if areas else None
                ),
            }
        )
    return sorted(
        candidates,
        key=lambda item: (
            abs(item["discovery_date_offset_days"]),
            item["minimum_start_window_distance_m"],
            item["fire_id"],
        ),
    )


def _feds_crosswalk(cases: list[dict[str, Any]], radius_m: float) -> list[dict[str, Any]]:
    import fiona
    from pyproj import Transformer

    results: dict[str, dict[str, Any]] = {}
    for year in sorted({int(case["year"]) for case in cases}):
        path = _feds_file_path(year)
        year_cases = [case for case in cases if int(case["year"]) == year]
        with fiona.open(path) as collection:
            target_crs = collection.crs_wkt or collection.crs or FEDS_EPSG_FALLBACK
            transformer = Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)
            for case in year_cases:
                candidates = _feds_case_candidates(collection, transformer, case, radius_m)
                if len(candidates) == 1:
                    selected = candidates[0]
                    status = "unique_spatiotemporal_candidate"
                elif not candidates:
                    selected = None
                    status = "no_candidate"
                else:
                    selected = None
                    status = "ambiguous"
                results[case["scenario_id"]] = {
                    "status": status,
                    "candidate_count": len(candidates),
                    "selected": selected,
                    "candidates": candidates,
                    "selection_used_final_area_or_perimeter": False,
                    "candidate_rule": "FEDS t_st date within -1/+2 days of FPA-FOD discovery date and at least one perimeter observed during the first 24 hours after t_st within the fixed search radius of the FPA-FOD reference point; a match is counted only when unique.",
                }
                print(
                    f"FEDS {case['split']} {case['scenario_id']}: {status} "
                    f"candidates={len(candidates)}",
                    file=sys.stderr,
                    flush=True,
                )
    return [
        {"scenario_id": case["scenario_id"], **results[case["scenario_id"]]}
        for case in cases
    ]


def _fle_crosswalk(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    unique_ids = sorted({case.get("fpa_unique_fire_id") for case in cases if case.get("fpa_unique_fire_id")})
    if not unique_ids:
        return {}
    fpa_clause = ",".join(_sql_quote(value) for value in unique_ids)
    wfigs_features = _query_arcgis_all(
        WFIGS_QUERY,
        f"attr_UniqueFireIdentifier IN ({fpa_clause})",
        "attr_UniqueFireIdentifier,attr_IncidentName,attr_POOState,attr_FinalAcres,"
        "attr_FireDiscoveryDateTime,poly_IRWINID,poly_IncidentName,poly_PolygonDateTime",
    )
    irwin_by_unique: dict[str, set[str]] = defaultdict(set)
    for feature in wfigs_features:
        row = feature.get("attributes", {})
        unique_id = row.get("attr_UniqueFireIdentifier")
        irwin_id = row.get("poly_IRWINID")
        if unique_id and irwin_id:
            irwin_by_unique[str(unique_id)].add(str(irwin_id))

    irwin_ids = sorted({value for values in irwin_by_unique.values() for value in values})
    fle_by_irwin: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if irwin_ids:
        irwin_clause = ",".join(_sql_quote(value) for value in irwin_ids)
        fle_features = _query_arcgis_all(
            FLE_QUERY,
            f"IRWINID IN ({irwin_clause})",
            "IRWINID,FCName,Year,Engagement,TotalLine,HeldLine,BurnedOverLine,"
            "NotEngagedLine,HTr,TR,ER,HER,BTR,NETR",
        )
        for feature in fle_features:
            attributes = feature.get("attributes", {})
            irwin_id = attributes.get("IRWINID")
            if irwin_id:
                fle_by_irwin[str(irwin_id)].append(attributes)

    results: dict[str, dict[str, Any]] = {}
    for case in cases:
        unique_id = case.get("fpa_unique_fire_id")
        irwin_matches = sorted(irwin_by_unique.get(unique_id or "", set()))
        matched_fle = [row for irwin in irwin_matches for row in fle_by_irwin.get(irwin, [])]
        outcomes = sorted(
            {str(row["Engagement"]) for row in matched_fle if row.get("Engagement")}
        )
        metric_rows = [row for row in matched_fle if row.get("TotalLine") is not None]
        results[case["scenario_id"]] = {
            "fpa_unique_fire_id": unique_id,
            "wfigs_irwin_match_count": len(irwin_matches),
            "irwin_ids": irwin_matches,
            "fle_summary_present": bool(matched_fle),
            "fle_rows_returned": len(matched_fle),
            "fle_engagement_categories": outcomes,
            "fle_total_line_meters": metric_rows[0].get("TotalLine") if metric_rows else None,
            "fle_source_is_grouped_summary_not_line_geometry": True,
        }
    return results


def run_audit(
    cohort: dict[str, Any],
    *,
    radius_m: float = 3000.0,
    include_feds_metadata: bool = True,
    splits: set[str] | None = None,
    cohort_manifest: str = "data/manifests/fireline-benchmark-cohort-v1.json",
) -> dict[str, Any]:
    allowed_splits = {"train", "validation"} if splits is None else splits
    if not allowed_splits or not allowed_splits <= {"train", "validation"}:
        raise ValueError("Only non-empty train/validation split selections are allowed.")
    all_cases = [
        case
        for case in cohort.get("cases", [])
        if case.get("split") in {"train", "validation"}
    ]
    if len(all_cases) != int(cohort.get("case_count", len(all_cases))):
        raise ValueError("Input manifest must contain only train/validation cases.")
    if any(case.get("split") == "test" for case in cohort.get("cases", [])):
        raise ValueError("Test cases are locked and must not be read by this audit.")
    cases = [case for case in all_cases if case.get("split") in allowed_splits]
    if not cases:
        raise ValueError("Selected split has no cases in the input manifest.")

    feds_rows = _feds_crosswalk(cases, radius_m)
    fle_rows = _fle_crosswalk(cases)
    feds_by_id = {row["scenario_id"]: row for row in feds_rows}
    for case in cases:
        feds_by_id[case["scenario_id"]]["fle"] = fle_rows.get(case["scenario_id"], {})

    report_cases = [
        {
            "scenario_id": case["scenario_id"],
            "fod_id": case["fod_id"],
            "fpa_unique_fire_id": case.get("fpa_unique_fire_id"),
            "name": case["name"],
            "state": case["state"],
            "year": case["year"],
            "split": case["split"],
            "discovery_date": case["discovery_time"].split(" ", 1)[0],
            "feds": feds_by_id[case["scenario_id"]],
        }
        for case in cases
    ]
    counts = {}
    for split in sorted(allowed_splits):
        subset = [row for row in report_cases if row["split"] == split]
        counts[split] = {
            "cases": len(subset),
            "unique_feds_matches": sum(
                row["feds"]["status"] == "unique_spatiotemporal_candidate" for row in subset
            ),
            "two_consecutive_feds_states": sum(
                bool(row["feds"]["selected"])
                and row["feds"]["selected"]["two_consecutive_12h_states"]
                for row in subset
            ),
            "full_48h_feds_reference": sum(
                bool(row["feds"]["selected"])
                and row["feds"]["selected"]["five_states_cover_48h"]
                for row in subset
            ),
            "fle_summary_present": sum(
                bool(row["feds"]["fle"].get("fle_summary_present")) for row in subset
            ),
        }

    threshold = {"train_two_state_minimum": 20, "validation_two_state_minimum": 8}
    complete_gate_splits = {"train", "validation"} <= allowed_splits
    gate_pass = None
    if complete_gate_splits:
        gate_pass = (
            counts["train"]["two_consecutive_feds_states"] >= threshold["train_two_state_minimum"]
            and counts["validation"]["two_consecutive_feds_states"]
            >= threshold["validation_two_state_minimum"]
        )
    report: dict[str, Any] = {
        "schema_version": "fpa-feds-fle-crosswalk/1.0",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "cohort_manifest": cohort_manifest,
        "cohort_source_commit": cohort.get("source_cohort_commit"),
        "cohort_case_count": len(all_cases),
        "test_cases_loaded": False,
        "audited_splits": sorted(allowed_splits),
        "spatial_search_radius_m": radius_m,
        "feds_start_date_window_days": {"before": 1, "after": 2},
        "summary": counts,
        "pre_agent_data_gate": {
            "threshold": threshold,
            "pass": gate_pass,
            "status": "pass" if gate_pass is True else "fail" if gate_pass is False else "incomplete",
            "instruction": "Stop before agent training if false; a split-only audit is incomplete; do not replace the cohort silently.",
        },
        "sources": {
            "fpa_fod": FPA_FOD_SOURCE,
            "feds_conus": ZENODO_LANDING,
            "wfigs": WFIGS_QUERY.rsplit("/query", 1)[0],
            "fle_grouped_summary": FLE_QUERY.rsplit("/query", 1)[0],
            "fle_rda_record": "https://doi.org/10.2737/RDS-2025-0011",
        },
        "method_limits": [
            "FEDS-CONUS exposes its own fireID, not the FPA-FOD identifier. The event match is provisional and uses only FPA-FOD discovery date, reported point, FEDS t_st, and the fixed spatial tolerance.",
            "The FPA-FOD point has unreported event-specific uncertainty and its date has no timezone in this adapter; the date window is intentionally recorded.",
            "The FLE feature service queried here is an incident-level grouped summary. It is not the line-level GIS used for post-hoc spatial comparisons.",
            "No final area, final perimeter, FLE outcome, or test case is used to choose a FEDS fireID.",
        ],
        "cases": report_cases,
    }
    if include_feds_metadata:
        try:
            report["feds_zenodo_metadata"] = _zenodo_provenance()
        except Exception as exc:  # Preserve the audited case results if metadata API is down.
            report["feds_zenodo_metadata_error"] = f"{type(exc).__name__}: {exc}"
    return report


def combine_split_reports(
    train_report: dict[str, Any],
    validation_report: dict[str, Any],
    *,
    source_paths: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Combine disjoint, same-cohort split audits into the pre-agent gate report."""
    reports = {"train": train_report, "validation": validation_report}
    for split, report in reports.items():
        if report.get("schema_version") != "fpa-feds-fle-crosswalk/1.0":
            raise ValueError(f"Unexpected {split} report schema.")
        if report.get("audited_splits") != [split]:
            raise ValueError(f"Expected a split-only {split} report.")
        if report.get("test_cases_loaded") is not False:
            raise ValueError("Split reports must affirm that no test cases were loaded.")
    invariant_fields = (
        "cohort_manifest",
        "cohort_source_commit",
        "cohort_case_count",
        "spatial_search_radius_m",
        "sources",
    )
    for key in invariant_fields:
        if train_report.get(key) != validation_report.get(key):
            raise ValueError(f"Split reports disagree on {key}.")

    cases_by_id: dict[str, dict[str, Any]] = {}
    for split, report in reports.items():
        if len(report.get("cases", [])) != report.get("summary", {}).get(split, {}).get("cases"):
            raise ValueError(f"The {split} case rows do not match the split summary.")
        for case in report.get("cases", []):
            if case.get("split") != split:
                raise ValueError(f"Found a {case.get('split')} case in the {split} report.")
            scenario_id = case.get("scenario_id")
            if not scenario_id or scenario_id in cases_by_id:
                raise ValueError("Split reports contain a missing or duplicate scenario ID.")
            cases_by_id[scenario_id] = case
    expected_case_count = train_report.get("cohort_case_count")
    if expected_case_count is None:
        expected_case_count = sum(
            report["summary"][split]["cases"] for split, report in reports.items()
        )
    if len(cases_by_id) != expected_case_count:
        raise ValueError("Split reports do not cover every train/validation cohort case.")

    combined = deepcopy(train_report)
    combined["created_utc"] = datetime.now(timezone.utc).isoformat()
    combined["cohort_case_count"] = expected_case_count
    combined["audited_splits"] = ["train", "validation"]
    combined["cases"] = list(train_report["cases"]) + list(validation_report["cases"])
    combined["summary"] = {
        "train": train_report["summary"]["train"],
        "validation": validation_report["summary"]["validation"],
    }
    metadata = combined.get("feds_zenodo_metadata")
    if metadata and not metadata.get("version"):
        metadata["version"] = "v1"
    threshold = combined["pre_agent_data_gate"]["threshold"]
    passed = (
        combined["summary"]["train"]["two_consecutive_feds_states"]
        >= threshold["train_two_state_minimum"]
        and combined["summary"]["validation"]["two_consecutive_feds_states"]
        >= threshold["validation_two_state_minimum"]
    )
    combined["pre_agent_data_gate"].update(
        {"pass": passed, "status": "pass" if passed else "fail"}
    )
    combined["split_report_sources"] = source_paths or {
        "train": "reports/real-fire-data/fpa-feds-fle-crosswalk-train-v1.json",
        "validation": "reports/real-fire-data/fpa-feds-fle-crosswalk-validation-v1.json",
    }
    combined["split_report_provenance"] = {
        split: {
            "report": combined["split_report_sources"].get(split),
            "derivation": report.get("crosswalk_derivation"),
        }
        for split, report in reports.items()
    }
    return combined


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cohort",
        type=Path,
        default=Path("data/manifests/fireline-benchmark-cohort-v1.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("reports/real-fire-data/fpa-feds-fle-crosswalk-v1.json"),
    )
    parser.add_argument("--radius-km", type=float, default=3.0)
    parser.add_argument(
        "--split",
        choices=("train", "validation"),
        action="append",
        dest="splits",
        help="Audit only this split; may be repeated. The full data gate requires both.",
    )
    parser.add_argument(
        "--combine-split-reports",
        nargs=2,
        metavar=("TRAIN_JSON", "VALIDATION_JSON"),
        help="Combine completed split-only reports without making additional network requests.",
    )
    parser.add_argument(
        "--filter-existing-report",
        metavar="CANDIDATE_JSON",
        help="Apply the strict first-24-hour point-proximity predicate to saved candidates offline.",
    )
    parser.add_argument(
        "--derivation-note",
        help="Record why an offline candidate-report filter was used.",
    )
    args = parser.parse_args(argv)
    if args.combine_split_reports and args.filter_existing_report:
        parser.error("choose either --combine-split-reports or --filter-existing-report")
    if args.filter_existing_report:
        source_path = Path(args.filter_existing_report)
        report = filter_report_to_start_window(
            json.loads(source_path.read_text()),
            source_path=str(source_path),
            derivation_note=args.derivation_note,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report["summary"], indent=2, sort_keys=True))
        print(f"STRICT CANDIDATE FILTER: {args.out}")
        return 0
    if args.combine_split_reports:
        train_path, validation_path = map(Path, args.combine_split_reports)
        report = combine_split_reports(
            json.loads(train_path.read_text()),
            json.loads(validation_path.read_text()),
            source_paths={"train": str(train_path), "validation": str(validation_path)},
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report["summary"], indent=2, sort_keys=True))
        print(
            "PRE-AGENT DATA GATE: "
            + ("PASS" if report["pre_agent_data_gate"]["pass"] else "FAIL")
            + f" (details: {args.out})"
        )
        return 0
    cohort = json.loads(args.cohort.read_text())
    splits = set(args.splits or ("train", "validation"))
    report = run_audit(
        cohort,
        radius_m=args.radius_km * 1000.0,
        splits=splits,
        cohort_manifest=str(args.cohort),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print(
        "PRE-AGENT DATA GATE: "
        + ("PASS" if report["pre_agent_data_gate"]["pass"] else "FAIL")
        + f" (details: {args.out})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
