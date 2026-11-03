#!/usr/bin/env python3
"""Sample checksum-verified daily gridMET records at FEDS start centroids.

This creates four 12-hour environment-forcing records per episode. It retains raw
gridMET values and does not choose a wind-adjustment factor or expose future daily
weather as a policy observation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifests/feds-episode-cohort-v1.json"
PREFLIGHT = ROOT / "reports/real-fire-data/feds-simfire-grid-preflight-v1.json"
DEFAULT_OUTPUT = ROOT / ".local/gridmet/feds-episode-weather-v1.json"
DEFAULT_COVERAGE_REPORT = ROOT / "reports/real-fire-data/feds-gridmet-weather-coverage-v1.json"
GRIDMET_DIR = ROOT / ".local/gridmet"

try:
    from scripts.fetch_gridmet_archives import find_gridmet_variable, validate_gridmet_archive
    from wildfire_rl.gridmet_weather import episode_weather_midpoints, select_gridmet_nearest_cell
except ModuleNotFoundError:
    sys.path.insert(0, str(ROOT / "scripts"))
    from fetch_gridmet_archives import find_gridmet_variable, validate_gridmet_archive
    from wildfire_rl.gridmet_weather import episode_weather_midpoints, select_gridmet_nearest_cell


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verified_hash(path: Path) -> str:
    sidecar = path.with_suffix(path.suffix + ".sha256")
    if not path.is_file() or not sidecar.is_file():
        raise FileNotFoundError(f"Missing gridMET archive or SHA-256 sidecar: {path}")
    expected = sidecar.read_text(encoding="ascii").strip()
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"gridMET SHA-256 mismatch for {path.name}.")
    return actual


def _read_weather(manifest: dict, preflight: dict, gridmet_dir: Path) -> dict:
    import numpy as np
    from netCDF4 import Dataset, num2date

    if manifest.get("test_cases_loaded") is not False or preflight.get("test_cases_loaded") is not False:
        raise ValueError("Refusing to open weather for a manifest/preflight that includes test cases.")
    preflight_cases = {case["scenario_id"]: case for case in preflight["cases"]}
    open_files = {}
    records = []
    try:
        for case in manifest["cases"]:
            year = int(case["event"]["year"])
            preflight_case = preflight_cases.get(case["scenario_id"])
            if preflight_case is None or not preflight_case["fits_grid"]:
                raise ValueError(f"Missing or failed geometry preflight for {case['scenario_id']}.")
            centroid = preflight_case["initial_perimeter_centroid_wgs84"]
            initial_time = case["evaluation_reference"]["initial_state_time"]
            weather_segments = episode_weather_midpoints(initial_time)
            segment_records = []
            for segment in weather_segments:
                date_label = segment["gridmet_daily_label_mst"]
                date_year = int(date_label[:4])
                if date_year not in (2018, 2019, 2023):
                    raise ValueError(
                        f"Episode {case['scenario_id']} needs gridMET year {date_year}, "
                        "which is outside the approved train/validation archive set."
                    )
                data = {}
                for abbreviation in ("th", "vs", "fm100"):
                    cache_key = (date_year, abbreviation)
                    if cache_key not in open_files:
                        path = gridmet_dir / f"{abbreviation}_{date_year}.nc"
                        checksum = verified_hash(path)
                        validate_gridmet_archive(path, date_year, abbreviation)
                        dataset = Dataset(path)
                        native_name, variable = find_gridmet_variable(dataset, abbreviation)
                        day_values = num2date(
                            dataset.variables["day"][:],
                            units=dataset.variables["day"].units,
                            calendar=getattr(dataset.variables["day"], "calendar", "gregorian"),
                            only_use_cftime_datetimes=False,
                        )
                        day_index = {
                            value.strftime("%Y-%m-%d"): index
                            for index, value in enumerate(day_values)
                        }
                        longitudes = dataset.variables["lon"][:]
                        latitudes = dataset.variables["lat"][:]
                        row, column, actual_lon, actual_lat = select_gridmet_nearest_cell(
                            longitudes, latitudes, centroid["longitude"], centroid["latitude"]
                        )
                        units = str(getattr(variable, "units", "unknown"))
                        expected_units = {
                            "th": {"degrees clockwise from north"},
                            "vs": {"m/s"},
                            "fm100": {"%", "percent"},
                        }[abbreviation]
                        if units.lower() not in expected_units:
                            raise ValueError(f"Unexpected gridMET units for {abbreviation}: {units!r}.")
                        open_files[cache_key] = {
                            "dataset": dataset,
                            "variable": variable,
                            "native_name": native_name,
                            "day_index": day_index,
                            "row": row,
                            "column": column,
                            "cell_lon": actual_lon,
                            "cell_lat": actual_lat,
                            "units": units,
                            "sha256": checksum,
                            "path": path.name,
                        }
                    sample = open_files[cache_key]
                    index = sample["day_index"].get(date_label)
                    if index is None:
                        raise ValueError(f"gridMET daily record {date_label} is absent from {sample['path']}.")
                    value = sample["variable"][index, sample["row"], sample["column"]]
                    if np.ma.is_masked(value) or not np.isfinite(float(value)):
                        raise ValueError(f"Missing/non-finite {abbreviation} at {date_label} for {case['scenario_id']}.")
                    data[abbreviation] = {
                        "value": float(value),
                        "units": sample["units"],
                        "native_netcdf_variable": sample["native_name"],
                        "archive": sample["path"],
                        "archive_sha256": sample["sha256"],
                    }
                segment_records.append({
                    **segment,
                    "gridmet_values": data,
                    "nearest_gridmet_cell": {
                        "longitude": open_files[(date_year, "vs")]["cell_lon"],
                        "latitude": open_files[(date_year, "vs")]["cell_lat"],
                        "row": open_files[(date_year, "vs")]["row"],
                        "column": open_files[(date_year, "vs")]["column"],
                    },
                })
            records.append({
                "scenario_id": case["scenario_id"],
                "split": case["split"],
                "event_year": year,
                "source_fire_id": case["evaluation_reference"]["source_fire_id"],
                "initial_state_time": initial_time,
                "weather_sample_location": {
                    "source": "centroid of exact-time initial FEDS perimeter",
                    "longitude": centroid["longitude"],
                    "latitude": centroid["latitude"],
                },
                "segments": segment_records,
            })
    finally:
        for item in open_files.values():
            item["dataset"].close()

    archive_manifest = []
    for year in (2018, 2019, 2023):
        for abbreviation in ("th", "vs", "fm100"):
            path = gridmet_dir / f"{abbreviation}_{year}.nc"
            archive_manifest.append({
                "file": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": verified_hash(path),
                "source_url": f"https://www.northwestknowledge.net/metdata/data/{path.name}",
            })
    return {
        "schema_version": "feds-gridmet-episode-weather/1.0",
        "kind": "retrospective_daily_environment_forcing_not_weather_forecast",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "test_cases_loaded": False,
        "episode_manifest": "data/manifests/feds-episode-cohort-v1.json",
        "episode_manifest_sha256": sha256_file(MANIFEST),
        "source": {
            "dataset": "gridMET daily surface meteorology",
            "access": "official annual NetCDF archives",
            "archives": archive_manifest,
            "variables": {
                "th": "wind-from direction, degrees clockwise from north",
                "vs": "10 m wind speed, m/s",
                "fm100": "100-hour dead fuel moisture, percent",
            },
            "source_note": "gridMET daily labels correspond approximately to MST day boundaries; FEDS naive timestamps are treated as UTC by explicit assumption.",
        },
        "temporal_mapping": {
            "decision_step_hours": 12,
            "horizon_hours": 48,
            "segment_weather_sample": "six-hour midpoint of each 12-hour interval mapped to the fixed MST daily label",
            "agent_visibility": "daily records are simulator forcing only; future segment weather is not included in policy observations",
            "interpretation": "ex-post historical forcing, not a forecast available to crews at decision time",
        },
        "mapping_status": "raw_values_only_no_wind_adjustment_factor_selected",
        "cases": records,
        "limitations": [
            "gridMET is daily and approximately 4 km; each 12-hour interval uses one sampled daily cell.",
            "10 m wind and NFDRS 100-hour fuel moisture are proxies, not measured SimFire midflame wind or FBFM13 fine-fuel moisture.",
            "FEDS timestamps omit timezone metadata in the selected FlatGeobuf fields; UTC interpretation is recorded as an assumption.",
            "Raw weather presence does not validate SimFire spread or any suppression counterfactual.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--preflight", type=Path, default=PREFLIGHT)
    parser.add_argument("--gridmet-dir", type=Path, default=GRIDMET_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--coverage-report", type=Path, default=DEFAULT_COVERAGE_REPORT)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        preflight = json.loads(args.preflight.read_text(encoding="utf-8"))
        result = _read_weather(manifest, preflight, args.gridmet_dir)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        value_ranges = {}
        for abbreviation in ("th", "vs", "fm100"):
            samples = [
                segment["gridmet_values"][abbreviation]["value"]
                for case in result["cases"]
                for segment in case["segments"]
            ]
            value_ranges[abbreviation] = {"minimum": min(samples), "maximum": max(samples)}
        by_split = {
            split: {
                "episode_count": sum(case["split"] == split for case in result["cases"]),
                "sampled_12h_segment_count": sum(
                    len(case["segments"]) for case in result["cases"] if case["split"] == split
                ),
            }
            for split in ("train", "validation")
        }
        coverage = {
            "schema_version": "feds-gridmet-weather-coverage/1.0",
            "kind": "weather_input_coverage_and_provenance_not_simulation_or_physical_validation",
            "created_utc": result["created_utc"],
            "episode_manifest": result["episode_manifest"],
            "episode_manifest_sha256": result["episode_manifest_sha256"],
            "test_cases_loaded": False,
            "source": result["source"],
            "temporal_mapping": result["temporal_mapping"],
            "mapping_status": result["mapping_status"],
            "by_split": by_split,
            "sampled_value_ranges": value_ranges,
            "limitations": result["limitations"],
            "case_level_values": "ignored local cache: .local/gridmet/feds-episode-weather-v1.json",
        }
        args.coverage_report.parent.mkdir(parents=True, exist_ok=True)
        args.coverage_report.write_text(json.dumps(coverage, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "output": str(args.out),
            "coverage_report": str(args.coverage_report),
            "cases": len(result["cases"]),
            "by_split": by_split,
            "segments_per_case": 4,
            "mapping_status": result["mapping_status"],
            "test_cases_loaded": result["test_cases_loaded"],
        }, indent=2))
        return 0
    except Exception as exc:
        print(f"gridMET episode sampling failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
