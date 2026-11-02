#!/usr/bin/env python3
"""Screen NIROPS chart filenames against 2023 validation names only.

This is a metadata-only candidate screen. It does not open chart images, fire
perimeter geometries, test cases, or simulator inputs, and it never trains.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COHORT = ROOT / "data/manifests/simfire-fpa-fod-cohort-v2.json"
DEFAULT_ARCHIVE = ROOT / ".local/nirops-progression-v2/Area_Progression_TimeSeries.zip"
DEFAULT_OUTPUT = ROOT / "reports/real-fire-data/nirops-validation-name-screen-20261102.json"
SOURCE_ZIP_BYTES = 78_086_022
SOURCE_ZIP_SHA256 = "dd7eed2587eb15aeccaaa547e47935613b0131a076901384499377639c96be1e"
COHORT_SHA256 = "f6c58b4685dcf24bf17f16c000b5d60d784f6ee49d85b43f750aef20939a4481"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def case_from_chart_path(path: str) -> tuple[str, str] | None:
    """Return state code and incident-label tokens from a regional chart path."""
    parts = PurePosixPath(path).parts
    if len(parts) < 3 or not path.lower().endswith("_progression.png"):
        return None
    stem = PurePosixPath(path).stem[:-len("_progression")]
    if "_" not in stem:
        return None
    incident_code, label = stem.split("_", 1)
    state_code = incident_code[:2].upper()
    if not re.fullmatch(r"[A-Z]{2}", state_code):
        return None
    return state_code, label


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, default=DEFAULT_COHORT)
    parser.add_argument("--timeseries-zip", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.cohort.is_file():
        raise FileNotFoundError("Missing cohort manifest: {}".format(args.cohort))
    if not args.timeseries_zip.is_file():
        raise FileNotFoundError("Missing NIROPS time-series archive: {}".format(args.timeseries_zip))
    cohort_hash = sha256_file(args.cohort)
    source_hash = sha256_file(args.timeseries_zip)
    if cohort_hash != COHORT_SHA256:
        raise ValueError("cohort manifest checksum differs from the frozen source")
    if source_hash != SOURCE_ZIP_SHA256 or args.timeseries_zip.stat().st_size != SOURCE_ZIP_BYTES:
        raise ValueError("local progression archive checksum/size differs from the screened source")

    cohort = json.loads(args.cohort.read_text(encoding="utf-8"))
    cases = [
        row for row in cohort["cases"]
        if row.get("split") == "validation" and row.get("year") == 2023
    ]
    if len(cases) != 20:
        raise ValueError("expected the frozen 20-case validation cohort from 2023")

    with ZipFile(args.timeseries_zip) as archive:
        chart_paths = sorted(
            name for name in archive.namelist()
            if name.lower().endswith("_progression.png")
        )
    candidates = []
    for row in cases:
        target = normalize(row["name"])
        matches = []
        for path in chart_paths:
            parsed = case_from_chart_path(path)
            if parsed is None:
                continue
            state_code, label = parsed
            if state_code != str(row["state"]).upper():
                continue
            label_tokens = [normalize(token) for token in label.split("_")]
            if target == normalize(label) or target in label_tokens:
                matches.append(path)
        candidates.append({
            "scenario_id": row["scenario_id"],
            "state": row["state"],
            "incident_name": row["name"],
            "year": row["year"],
            "candidate_chart_paths": matches,
            "candidate_count": len(matches),
            "incident_crosswalk_verified": False,
            "match_basis": "exact normalized incident-name label/token and two-letter state prefix in chart filename only",
        })

    result = {
        "kind": "nirops_validation_name_screen",
        "source": {
            "dataset": "USFS NIROPS fire-perimeter progression",
            "mendeley_dataset_id": "95rj5d379g",
            "mendeley_version": 2,
            "record_url": "https://data.mendeley.com/datasets/95rj5d379g/2",
            "selected_member": "Area_Progression_TimeSeries.zip",
            "selected_member_bytes": args.timeseries_zip.stat().st_size,
            "selected_member_sha256": source_hash,
            "chart_files_in_member": len(chart_paths),
            "full_v2_outer_archive_bytes": 1_735_431_121,
            "outer_member_extraction": "HTTP byte-range request; no raw perimeter shapefile downloaded",
        },
        "cohort": {
            "manifest": "data/manifests/simfire-fpa-fod-cohort-v2.json",
            "manifest_sha256": cohort_hash,
            "split_screened": "validation",
            "year_screened": 2023,
            "cases_screened": len(cases),
        },
        "screen": {
            "method": "metadata-only filename screen; exact normalized name token plus state prefix",
            "cases_with_name_candidates": sum(row["candidate_count"] > 0 for row in candidates),
            "verified_incident_crosswalks": 0,
            "chart_images_opened": False,
            "perimeter_geometries_opened": False,
            "test_geometries_opened": False,
            "agent_training": False,
            "policy_evaluation": False,
        },
        "candidates": candidates,
        "limitations": [
            "A chart filename is not an official incident-ID match; the year and UTC timestamps were not checked.",
            "No chart pixels, source perimeter geometry, or test incident content were read.",
            "A name/state candidate must be verified against official incident IDs and event dates before use.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        raise FileExistsError("refusing to overwrite existing receipt: {}".format(args.out))
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("cases_screened=20 candidates={} verified=0 test_opened=false".format(
        result["screen"]["cases_with_name_candidates"]
    ))
    print(args.out)


if __name__ == "__main__":
    main()
