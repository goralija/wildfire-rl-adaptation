#!/usr/bin/env python3
"""Check that WAF sensitivity smoke runs use the same real cases and inputs."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
RUNS = {
    0.1: ROOT / "reports/real-fire-data/simfire-cohort-v2-gridmet-weather-smoke-waf-01/receipt.json",
    0.3: ROOT / "reports/real-fire-data/simfire-cohort-v2-gridmet-weather-smoke-waf-03/receipt.json",
    0.5: ROOT / "reports/real-fire-data/simfire-cohort-v2-gridmet-weather-smoke-waf-05/receipt.json",
}


def main() -> int:
    errors: list[str] = []
    receipts = {}
    for factor, path in RUNS.items():
        if not path.is_file():
            errors.append("missing smoke receipt: " + str(path))
            continue
        receipts[factor] = json.loads(path.read_text(encoding="utf-8"))

    expected_splits = ("train", "validation", "test")
    cases_by_factor: dict[float, dict[str, dict]] = {}
    for factor, receipt in receipts.items():
        if receipt.get("agent_training") is not False:
            errors.append("a sensitivity smoke unexpectedly trained a policy")
        if receipt.get("weather_mode") != "gridmet_daily_proxy":
            errors.append("wrong weather mode for WAF {}".format(factor))
        if receipt.get("atmosphere", {}).get("wind_adjustment_factor_override") != factor:
            errors.append("wrong WAF override in receipt for {}".format(factor))
        rows = {row["split"]: row for row in receipt.get("splits", [])}
        if set(rows) != set(expected_splits):
            errors.append("WAF {} does not include exactly all three splits".format(factor))
        cases_by_factor[factor] = rows

    baseline_factor = 0.3
    baseline = cases_by_factor.get(baseline_factor, {})
    details = []
    for factor, rows in cases_by_factor.items():
        for split in expected_splits:
            row = rows.get(split)
            base_row = baseline.get(split)
            if row is None or base_row is None:
                continue
            info = row["reset_info"]
            base_info = base_row["reset_info"]
            params = info.get("weather_proxy_parameters") or {}
            base_params = base_info.get("weather_proxy_parameters") or {}
            for key in ("scenario_id", "fuel_sha256", "terrain_sha256", "weather_source_sha256", "weather_mapping_sha256"):
                if info.get(key) != base_info.get(key):
                    errors.append("{} changed between WAF {} and 0.3 in {}".format(key, factor, split))
            if params.get("wind_adjustment_factor") != factor:
                errors.append("WAF was not applied in {} split at factor {}".format(split, factor))
            if params.get("wind_direction_degrees_clockwise_north_to") != base_params.get("wind_direction_degrees_clockwise_north_to"):
                errors.append("wind direction changed during WAF sensitivity")
            if params.get("fuel_moisture_fraction_proxy") != base_params.get("fuel_moisture_fraction_proxy"):
                errors.append("fuel-moisture proxy changed during WAF sensitivity")
            actual_speed = float(params["wind_speed_midflame_mph_proxy"])
            reference_speed = actual_speed / factor
            if abs(reference_speed - float(base_params["wind_speed_midflame_mph_proxy"]) / baseline_factor) > 1e-9:
                errors.append("WAF does not scale wind linearly for {}".format(split))
            details.append({
                "factor": factor,
                "split": split,
                "scenario_id": info.get("scenario_id"),
                "wind_speed_midflame_mph_proxy": actual_speed,
                "wind_direction_degrees_clockwise_north_to": params.get("wind_direction_degrees_clockwise_north_to"),
                "fuel_moisture_fraction_proxy": params.get("fuel_moisture_fraction_proxy"),
                "weather_mapping_sha256": info.get("weather_mapping_sha256"),
            })

    split_samples = []
    for split in expected_splits:
        values = [row["wind_speed_midflame_mph_proxy"] for row in details if row["split"] == split]
        split_samples.append({
            "split": split,
            "case_count": 1 if split in baseline else 0,
            "wind_speed_mean_by_factor_mph": {
                str(factor): mean([row["wind_speed_midflame_mph_proxy"] for row in details
                                  if row["split"] == split and row["factor"] == factor])
                for factor in RUNS if any(row["split"] == split and row["factor"] == factor for row in details)
            },
            "scenario_id": baseline.get(split, {}).get("scenario_id"),
        })

    report = {
        "kind": "simfire_gridmet_weather_waf_sensitivity_smoke",
        "scientific_result": False,
        "physical_validation": False,
        "agent_training": False,
        "waf_factors": list(RUNS),
        "same_case_and_input_hashes_across_factors": not errors,
        "same_weather_direction_and_moisture_across_factors": not errors,
        "wind_speed_scales_with_waf": not errors,
        "episode_scope": "One short integration smoke case per split and WAF; this is a software/data-flow check, not a policy evaluation.",
        "errors": errors,
        "cases_by_split": split_samples,
        "smoke_rows": details,
        "receipt_paths": {str(factor): path.relative_to(ROOT).as_posix() for factor, path in RUNS.items()},
    }
    out = ROOT / "reports/real-fire-data/simfire-cohort-v2-gridmet-waf-sensitivity.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(out), "errors": errors, "rows": len(details)}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
