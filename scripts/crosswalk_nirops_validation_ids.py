#!/usr/bin/env python3
"""Crosswalk the frozen 2023 validation cases to NIROPS chart incident codes.

Uses only the local FPA-FOD cohort screen and the small NIROPS progression-chart
archive. It does not open perimeter geometries, 2024 test records, or simulator
inputs, and it never trains or evaluates a policy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COHORT = ROOT / "data/manifests/simfire-fpa-fod-cohort-v2.json"
DEFAULT_FPA_GEOJSON = ROOT / "reports/real-fire-data/fpa-fod-simfire-cohort-v2/2023-screen.geojson"
DEFAULT_CHART_ZIP = ROOT / ".local/nirops-progression-v2/Area_Progression_TimeSeries.zip"
DEFAULT_OUTPUT = ROOT / "reports/real-fire-data/nirops-validation-id-crosswalk-20261102.json"
COHORT_SHA256 = "f6c58b4685dcf24bf17f16c000b5d60d784f6ee49d85b43f750aef20939a4481"
CHART_ZIP_BYTES = 78_086_022
CHART_ZIP_SHA256 = "dd7eed2587eb15aeccaaa547e47935613b0131a076901384499377639c96be1e"
FPA_GEOJSON_SHA256 = "f14cd70374ce808f889d0c05959387b899e4b4e5d2a8b9acaee7b78c6e016c3a"
REVIEWED_CHART_COPY = ROOT / "reports/real-fire-data/nirops-validation-charts/hayden-area-progression.png"
REVIEWED_CHART_SHA256 = "28a669a8be127e77321e4e44944f6cfe6d8041e7a9a8ee38980d9f064bcc4ce9"
VISUALLY_REVIEWED_CHARTS = {
    "fpa-fod-401316132-hayden": {
        "path": "Area_Progression_TimeSeries/Great_Basin/ID-SCF-023084_Hayden_progression.png",
        "repository_copy": "reports/real-fire-data/nirops-validation-charts/hayden-area-progression.png",
        "observations": {
            "chart_axis": "UTC Date and Time; Area (acres)",
            "first_plotted_observation_approx": "2023-07-21",
            "last_plotted_observation_approx": "2023-08-31",
            "final_plotted_area_acres_approx": 24800,
            "fpa_reported_final_area_acres": 24706,
            "fpa_discovery_date_utc": "2023-07-19",
            "interpretation": "The chart begins about two days after FPA-FOD discovery and its final plotted area is close to FPA-FOD reported final size. Visual axis estimates only; not a polygon comparison or proof of complete containment timing.",
        },
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def chart_identity(path: str) -> dict[str, str] | None:
    stem = PurePosixPath(path).stem
    suffix = "_progression"
    if not stem.lower().endswith(suffix):
        return None
    stem = stem[:-len(suffix)]
    if "_" not in stem:
        return None
    event_code, label = stem.split("_", 1)
    match = re.fullmatch(r"([A-Z]{2})-([A-Z0-9]+)-([A-Z0-9]+)", event_code.upper())
    if match is None:
        return None
    return {
        "state": match.group(1),
        "event_code": event_code,
        "normalized_event_code": normalize(event_code),
        "label": label,
    }


def fod_id_from_row(row: dict) -> int:
    match = re.fullmatch(r"FOD_ID:(\d+)", str(row.get("source_record_id", "")))
    if match is None:
        raise ValueError("unexpected FPA-FOD source_record_id for {}".format(row.get("scenario_id")))
    return int(match.group(1))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, default=DEFAULT_COHORT)
    parser.add_argument("--fpa-geojson", type=Path, default=DEFAULT_FPA_GEOJSON)
    parser.add_argument("--chart-zip", type=Path, default=DEFAULT_CHART_ZIP)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for path, label in (
        (args.cohort, "cohort manifest"),
        (args.fpa_geojson, "FPA-FOD validation screen"),
        (args.chart_zip, "NIROPS chart archive"),
    ):
        if not path.is_file():
            raise FileNotFoundError("missing {}: {}".format(label, path))

    cohort_hash = sha256_file(args.cohort)
    if cohort_hash != COHORT_SHA256:
        raise ValueError("cohort manifest checksum differs from the frozen source")
    chart_hash = sha256_file(args.chart_zip)
    if chart_hash != CHART_ZIP_SHA256 or args.chart_zip.stat().st_size != CHART_ZIP_BYTES:
        raise ValueError("NIROPS chart archive checksum/size differs from the screened source")
    fpa_hash = sha256_file(args.fpa_geojson)
    if FPA_GEOJSON_SHA256 and fpa_hash != FPA_GEOJSON_SHA256:
        raise ValueError("FPA-FOD screen checksum differs from the screened source")
    if not REVIEWED_CHART_COPY.is_file() or sha256_file(REVIEWED_CHART_COPY) != REVIEWED_CHART_SHA256:
        raise ValueError("the attributed Hayden chart copy is missing or changed")

    cohort = json.loads(args.cohort.read_text(encoding="utf-8"))
    cases = [
        row for row in cohort["cases"]
        if row.get("split") == "validation" and row.get("year") == 2023
    ]
    if len(cases) != 20:
        raise ValueError("expected the frozen 20-case VALIDATION cohort from 2023")

    fpa_payload = json.loads(args.fpa_geojson.read_text(encoding="utf-8"))
    fpa_rows = {}
    for feature in fpa_payload.get("features", []):
        props = feature.get("properties", {})
        if "fod_id" in props:
            fod_id = int(props["fod_id"])
            if fod_id in fpa_rows:
                raise ValueError("duplicate FOD_ID in FPA-FOD screen: {}".format(fod_id))
            fpa_rows[fod_id] = props

    with ZipFile(args.chart_zip) as archive:
        chart_paths = sorted(
            path for path in archive.namelist()
            if path.lower().endswith("_progression.png")
        )
    chart_rows = []
    for path in chart_paths:
        identity = chart_identity(path)
        if identity is not None:
            chart_rows.append({**identity, "path": path})

    results = []
    for row in cases:
        fod_id = fod_id_from_row(row)
        source = fpa_rows.get(fod_id)
        if source is None:
            raise ValueError("FOD_ID {} missing from FPA-FOD screen".format(fod_id))
        fpa_id = str(source.get("fpa_id", ""))
        match = re.fullmatch(r"INF-(\d{4})-(.+)", fpa_id.upper())
        if match is None:
            raise ValueError("unexpected FPA_ID format for {}: {}".format(row["scenario_id"], fpa_id))
        event_year, fpa_event_code = match.groups()
        expected_code = normalize(fpa_event_code)
        state = str(row["state"]).upper()
        incident_name = str(row["name"])

        exact_id = [chart for chart in chart_rows if chart["normalized_event_code"] == expected_code]
        name_state = [
            chart for chart in chart_rows
            if chart["state"] == state
            and normalize(incident_name) in [normalize(part) for part in chart["label"].split("_")]
        ]
        corroborated = [
            chart for chart in exact_id
            if chart["state"] == state
            and normalize(incident_name) in [normalize(part) for part in chart["label"].split("_")]
            and event_year == str(row["year"])
        ]
        if len(exact_id) > 1:
            outcome = "ambiguous_duplicate_event_code"
        elif len(corroborated) == 1:
            outcome = "exact_incident_code_state_name_match"
        elif exact_id:
            outcome = "exact_code_needs_manual_review"
        else:
            outcome = "no_exact_event_code_match"

        record = {
            "scenario_id": row["scenario_id"],
            "fpa_fod_id": fod_id,
            "fpa_id": fpa_id,
            "fpa_event_code_normalized": expected_code,
            "incident_name": incident_name,
            "state": state,
            "year": row["year"],
            "fpa_discovery_date_utc": datetime.fromtimestamp(
                int(source["discovery_date"]) / 1000, tz=timezone.utc
            ).date().isoformat() if source.get("discovery_date") is not None else None,
            "fpa_reported_final_area_acres": source.get("fire_size"),
            "exact_event_code_chart_matches": exact_id,
            "same_state_name_chart_candidates": name_state,
            "crosswalk_outcome": outcome,
            "date_alignment_checked": False,
            "perimeter_geometry_obtained": False,
        }
        visual = VISUALLY_REVIEWED_CHARTS.get(row["scenario_id"])
        if visual:
            if len(exact_id) != 1 or exact_id[0]["path"] != visual["path"]:
                raise ValueError("visual note path no longer matches exact incident-code crosswalk")
            record["chart_visual_review"] = visual["observations"]
        results.append(record)

    verified = [row for row in results if row["crosswalk_outcome"] == "exact_incident_code_state_name_match"]
    name_mismatches = [
        row for row in results
        if row["same_state_name_chart_candidates"] and not row["exact_event_code_chart_matches"]
    ]
    manually_reviewed = [
        {"scenario_id": row["scenario_id"], "path": VISUALLY_REVIEWED_CHARTS[row["scenario_id"]]["path"]}
        for row in results if row["scenario_id"] in VISUALLY_REVIEWED_CHARTS
    ]

    result = {
        "kind": "nirops_validation_id_crosswalk",
        "created_utc": "2026-11-02",
        "sources": {
            "dataset": "USFS NIROPS fire-perimeter progression, Mendeley v2",
            "record_url": "https://data.mendeley.com/datasets/95rj5d379g/2",
            "chart_archive_member": "Area_Progression_TimeSeries.zip",
            "chart_archive_bytes": args.chart_zip.stat().st_size,
            "chart_archive_sha256": chart_hash,
            "chart_count": len(chart_paths),
            "fpa_screen": "reports/real-fire-data/fpa-fod-simfire-cohort-v2/2023-screen.geojson",
            "fpa_screen_sha256": fpa_hash,
            "cohort_manifest": "data/manifests/simfire-fpa-fod-cohort-v2.json",
            "cohort_manifest_sha256": cohort_hash,
        },
        "method": {
            "primary_key": "FPA-FOD FPA_ID event identifier after INF-YYYY- equals NIROPS chart event code after punctuation normalization",
            "corroborating_fields": ["state", "incident name in chart label"],
            "scope": "only frozen 2023 VALIDATION cases; chart filenames and a single validation chart visual review",
            "interpretation": "Exact code, year, state, and name matches establish an incident crosswalk candidate for acquiring source polygons; they do not validate simulated spread.",
        },
        "screen": {
            "cases_screened": len(cases),
            "exact_incident_code_state_name_matches": len(verified),
            "same_state_name_candidates_without_exact_incident_code": len(name_mismatches),
            "charts_visually_reviewed": len(manually_reviewed),
            "perimeter_geometries_opened": False,
            "test_geometries_opened": False,
            "simulator_advanced": False,
            "agent_training": False,
            "policy_evaluation": False,
        },
        "visually_reviewed_charts": manually_reviewed,
        "visual_chart_copy": {
            "path": "reports/real-fire-data/nirops-validation-charts/hayden-area-progression.png",
            "sha256": REVIEWED_CHART_SHA256,
            "source_attribution": "Magstadt et al. (2026), NIROPS fire-perimeter progression dataset, Mendeley Data v2, DOI 10.17632/95rj5d379g.2, CC BY 4.0; original chart copied unchanged.",
        },
        "cases": results,
        "limitations": [
            "NIROPS chart PNGs summarize area over time; they are not the underlying perimeter polygons.",
            "The Hayden chart was visually reviewed; its first/last dates and final acreage are approximate axis readings.",
            "No actual NIROPS shapefile geometry, suppression log, weather replay, or spatial overlap metric was inspected.",
            "Eight code matches nominate 2023 validation cases for polygon acquisition; they are not physical validation results.",
            "The 2024 held-out test cohort was not read or opened.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        raise FileExistsError("refusing to overwrite existing receipt: {}".format(args.out))
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("cases={} exact_id_matches={} name_only_mismatches={} chart_images_reviewed={} test_opened=false training=false".format(
        len(cases), len(verified), len(name_mismatches), len(manually_reviewed)
    ))
    print(args.out)


if __name__ == "__main__":
    main()
