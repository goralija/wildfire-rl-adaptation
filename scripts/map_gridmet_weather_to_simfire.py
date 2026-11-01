#!/usr/bin/env python3
"""Write an explicit daily-weather proxy mapping for every cohort case."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from statistics import median
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wildfire_rl.gridmet_simfire_weather import (  # noqa: E402
    DEFAULT_WIND_ADJUSTMENT_FACTOR,
    MAPPING_VERSION,
    map_gridmet_daily_weather,
)


COHORT_PATH = ROOT / "data/manifests/simfire-fpa-fod-cohort-v2.json"
DEFAULT_OUT = ROOT / "data/processed/simfire-cohort-v2-gridmet-mappings"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort-manifest", type=Path, default=COHORT_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--wind-adjustment-factor", type=float, default=DEFAULT_WIND_ADJUSTMENT_FACTOR)
    args = parser.parse_args()
    cohort_path = args.cohort_manifest.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()
    cohort = json.loads(cohort_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    errors = []
    mapped_rows = []

    for cohort_row in cohort["cases"]:
        scenario_path = ROOT / cohort_row["scenario_manifest"]
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
        weather_path = ROOT / scenario["inputs"]["weather"]["path"]
        raw = weather_path.read_bytes()
        source_hash = digest(raw)
        expected_hash = scenario["inputs"]["weather"].get("sha256")
        if source_hash != expected_hash or source_hash != cohort_row.get("weather_sha256"):
            errors.append({"scenario_id": cohort_row["scenario_id"], "error": "weather source checksum mismatch"})
            continue
        weather = json.loads(raw)
        try:
            mapped = map_gridmet_daily_weather(
                weather, wind_adjustment_factor=args.wind_adjustment_factor
            )
        except (KeyError, ValueError, TypeError) as exc:
            errors.append({"scenario_id": cohort_row["scenario_id"], "error": str(exc)})
            continue
        mapped["weather_source_sha256"] = source_hash
        mapped["source_file"] = scenario["inputs"]["weather"]["path"]
        output_path = out_dir / (cohort_row["scenario_id"] + ".json")
        encoded = (json.dumps(mapped, indent=2, sort_keys=True) + "\n").encode("utf-8")
        output_path.write_bytes(encoded)
        mapping_hash = digest(encoded)
        relative_path = output_path.relative_to(ROOT).as_posix()

        scenario["fire_behavior"]["weather_mapping_note"] = (
            "Mapped from per-case gridMET daily context using the explicit v1 proxy in "
            "weather_mapping. It is a stationary representative-day assumption, not an "
            "hourly event replay or measured midflame weather."
        )
        scenario["fire_behavior"]["weather_mapping"] = {
            "status": "approximate_proxy",
            "version": MAPPING_VERSION,
            "path": relative_path,
            "sha256": mapping_hash,
            "wind_adjustment_factor": args.wind_adjustment_factor,
        }
        scenario["inputs"]["weather"]["units_and_mapping"] = (
            "Original daily gridMET context; see fire_behavior.weather_mapping for the "
            "separate approximate SimFire proxy and its assumptions."
        )
        scenario["readiness"] = "inputs_ready"
        scenario_path.write_text(json.dumps(scenario, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        cohort_row["input_status"]["weather"] = "mapped_proxy"
        cohort_row["weather_mapping_path"] = relative_path
        cohort_row["weather_mapping_sha256"] = mapping_hash
        mapped_rows.append({
            "scenario_id": cohort_row["scenario_id"],
            "split": cohort_row["split"],
            "weather_json": scenario["inputs"]["weather"]["path"],
            "weather_sha256": source_hash,
            "mapping_json": relative_path,
            "mapping_sha256": mapping_hash,
            "wind_adjustment_factor": args.wind_adjustment_factor,
            "wind_speed_midflame_mph_proxy": mapped["simfire_parameters"]["wind_speed_midflame_mph_proxy"],
            "wind_direction_degrees_clockwise_north_to": mapped["simfire_parameters"]["wind_direction_degrees_clockwise_north_to"],
            "fuel_moisture_percent_proxy": mapped["simfire_parameters"]["fuel_moisture_fraction_proxy"] * 100.0,
        })

    report = {
        "kind": "simfire_fpa_fod_gridmet_daily_mapping",
        "mapping_version": MAPPING_VERSION,
        "scientific_result": False,
        "physical_validation": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "cohort_id": cohort.get("cohort_id"),
        "requested_case_count": len(cohort["cases"]),
        "mapped_proxy_case_count": len(mapped_rows),
        "failed_case_count": len(errors),
        "mapped_proxy_count_by_split": {
            split: sum(row["split"] == split for row in mapped_rows)
            for split in ("train", "validation", "test")
        },
        "wind_adjustment_factor": args.wind_adjustment_factor,
        "wind_factor_sensitivity": [0.1, 0.3, 0.5],
        "mapped_parameter_ranges_by_split": {},
        "exact_historical_weather_mapping_count": 0,
        "cases_with_proxy_inputs_ready_for_environment": len(mapped_rows) if not errors else 0,
        "agent_training_started": False,
        "cases": mapped_rows,
        "errors": errors,
        "limitations": [
            "A daily approximately 4-km grid value is treated as a constant representative condition over the episode; it is not hourly ignition-time weather.",
            "gridMET 10-m wind is assumed to approximate a 20-ft reference wind before applying the selected wind-adjustment factor; there is no site-specific profile/canopy conversion.",
            "The nominal 0.3 factor represents a partially sheltered scenario, but sheltering was not measured. Factors 0.1 and 0.5 are sensitivity cases, not verified local bounds.",
            "Meteorological wind-from direction is reversed to the direction toward which SimFire spread responds.",
            "A Simard equilibrium-moisture estimate based on daily maximum temperature and minimum RH is used as a dry-side fine-fuel proxy; these extrema may not be simultaneous and EMC is not measured fuel moisture.",
            "The gridMET model-G 100-hour moisture and ERC remain source context and are not substituted for SimFire fine-fuel moisture.",
            "This profile is a reproducible first training assumption, not a validated historical replay or proof of real-world fire reduction.",
        ],
    }
    for split in ("train", "validation", "test"):
        selected = [row for row in mapped_rows if row["split"] == split]
        report["mapped_parameter_ranges_by_split"][split] = {}
        for key, unit in (
            ("wind_speed_midflame_mph_proxy", "mph"),
            ("fuel_moisture_percent_proxy", "%"),
        ):
            values = sorted(float(row[key]) for row in selected)
            report["mapped_parameter_ranges_by_split"][split][key] = {
                "unit": unit,
                "count": len(values),
                "minimum": values[0] if values else None,
                "median": median(values) if values else None,
                "maximum": values[-1] if values else None,
            }
    report_path = ROOT / "reports/real-fire-data/simfire-cohort-v2-gridmet-simfire-mapping.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    cohort["weather_mapping_report"] = report_path.relative_to(ROOT).as_posix()
    cohort["weather_mapping_summary"] = {
        "mapping_version": MAPPING_VERSION,
        "requested": report["requested_case_count"],
        "mapped_proxy": report["mapped_proxy_case_count"],
        "failed": report["failed_case_count"],
        "exact_historical_mapping": 0,
        "proxy_environment_inputs_ready": report["cases_with_proxy_inputs_ready_for_environment"],
        "agent_training_started": False,
    }
    cohort_path.write_text(json.dumps(cohort, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(report_path),
        "requested": report["requested_case_count"],
        "mapped_proxy": report["mapped_proxy_case_count"],
        "failed": report["failed_case_count"],
        "exact_mapping": 0,
        "training_started": False,
    }, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
