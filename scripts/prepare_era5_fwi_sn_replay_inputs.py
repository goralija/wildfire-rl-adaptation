#!/usr/bin/env python3
"""Create ignored copies of three TRAIN inputs with ERA5-FWI-SN daily codes.

Only the six daily FWI columns are changed. Original case inputs are read-only;
the generated copies and manifests stay under ignored ``runs/``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_RUNS = ROOT.parents[1] / "runs/real-case"
DEFAULT_WEATHER_AUDIT = ROOT / "reports/real-fire-data/era5-fwi-sn-2018-pilot-comparison.json"
DEFAULT_OUTPUT = ROOT / "runs/diagnostics/era5-fwi-sn-2018"
TARGET_DOY = {"2018_1770": 224, "2018_241": 227, "2018_747": 228}
FWI_FIELDS = ("FFMC", "DMC", "DC", "ISI", "BUI", "FWI")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(source_runs: Path, audit_path: Path, output_root: Path) -> dict[str, Any]:
    if output_root.exists():
        raise FileExistsError(f"Refusing to overwrite diagnostic outputs: {output_root}")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    cases_by_id = {item["event_id"]: item for item in audit["cases"]}
    if set(cases_by_id) != set(TARGET_DOY):
        raise ValueError("FWI audit must contain exactly the three specified TRAIN pilots")

    output_root.mkdir(parents=True)
    outputs = []
    for event_id, target_doy in TARGET_DOY.items():
        source_case = source_runs / f"{event_id}-day{target_doy}"
        source_input = source_case / "input"
        source_weather = source_input / "Weather.csv"
        if not source_weather.is_file():
            raise FileNotFoundError(f"Missing existing input Weather.csv: {source_weather}")
        case_manifest = source_case / "case.json"
        if not case_manifest.is_file():
            raise FileNotFoundError(f"Missing existing case manifest: {case_manifest}")

        destination = output_root / event_id
        destination.mkdir()
        destination_input = destination / "input"
        import shutil

        shutil.copytree(source_input, destination_input)
        (destination_input / "Ignitions.csv").write_text("Year,Ncell\n1,372", encoding="utf-8")
        shutil.copy2(case_manifest, destination / "case.json")
        if (source_case / "truth").is_dir():
            shutil.copytree(source_case / "truth", destination / "truth")

        original_rows: list[dict[str, str]]
        with source_weather.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None or not set(FWI_FIELDS).issubset(reader.fieldnames):
                raise ValueError(f"Weather.csv is missing required FWI fields: {source_weather}")
            fieldnames = list(reader.fieldnames)
            original_rows = list(reader)
        if len(original_rows) != 24:
            raise ValueError(f"Expected 24 hourly rows for {event_id}; got {len(original_rows)}")

        values = cases_by_id[event_id]["era5_fwi_sn_daily_values"]
        if set(values) != set(FWI_FIELDS):
            raise ValueError(f"Incomplete six-component FWI values for {event_id}")
        updated_rows = []
        for row in original_rows:
            if not row["datetime"].startswith(cases_by_id[event_id]["target_date_local"]):
                raise ValueError(f"Weather row for {event_id} is outside the target local day")
            updated = dict(row)
            for field in FWI_FIELDS:
                updated[field] = repr(float(values[field]))
            updated_rows.append(updated)
        destination_weather = destination_input / "Weather.csv"
        with destination_weather.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(updated_rows)

        for old, new in zip(original_rows, updated_rows):
            if any(old[key] != new[key] for key in fieldnames if key not in FWI_FIELDS):
                raise AssertionError(f"Non-FWI weather field changed for {event_id}")
            if any(float(new[field]) != float(values[field]) for field in FWI_FIELDS):
                raise AssertionError(f"Daily FWI value was not copied consistently for {event_id}")

        manifest = {
            "schema": "era5-fwi-sn-weather-diagnostic-input/v1",
            "event_id": event_id,
            "target_date_local": cases_by_id[event_id]["target_date_local"],
            "source_case_manifest_sha256": sha256(case_manifest),
            "original_weather_csv_sha256": sha256(source_weather),
            "diagnostic_weather_csv_sha256": sha256(destination_weather),
            "source_comparison_report_sha256": sha256(audit_path),
            "modified_columns": list(FWI_FIELDS),
            "runtime_ignition_input": "same Firehose probe default as the archived replay: year 1, one-based cell 372",
            "hourly_rows": len(updated_rows),
            "daily_values_repeated_unchanged_across_rows": True,
            "other_weather_columns_preserved": True,
            "historical_case_claim": "diagnostic copy only; original case not modified or promoted",
        }
        manifest_path = destination / "input-manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        outputs.append({"event_id": event_id, "directory": str(destination), **manifest})

    return {
        "schema": "era5-fwi-sn-weather-diagnostic-inputs/v1",
        "source_comparison_report_sha256": sha256(audit_path),
        "outputs": outputs,
        "notes": [
            "Only ignored diagnostic copies under runs/ were created.",
            "The six daily FWI indices replaced the old CFSDS event summary codes; all hourly weather columns and simulator inputs were copied unchanged.",
            "This prepares a controlled sensitivity replay, not calibration, physical validation, or a benchmark case.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-runs", type=Path, default=DEFAULT_SOURCE_RUNS)
    parser.add_argument("--weather-audit", type=Path, default=DEFAULT_WEATHER_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = prepare(args.source_runs, args.weather_audit, args.output)
    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "cases": len(result["outputs"]), "manifest": str(manifest_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
