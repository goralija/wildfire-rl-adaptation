#!/usr/bin/env python3
"""Validate and summarize the compact gridMET weather context for the FPA-FOD cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COHORT_PATH = ROOT / "data/manifests/simfire-fpa-fod-cohort-v2.json"
ACQUISITION_PATH = ROOT / "reports/real-fire-data/simfire-cohort-v2-gridmet-weather.json"
DEFAULT_OUT = ROOT / "reports/real-fire-data"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cohort = json.loads(COHORT_PATH.read_text(encoding="utf-8"))
    acquisition = json.loads(ACQUISITION_PATH.read_text(encoding="utf-8"))
    manifest_cases = {row["scenario_id"]: row for row in cohort["cases"]}
    rows = []
    errors = []
    variables = acquisition["source"]["variables"]
    units_by_variable: dict[str, set[str | None]] = {name: set() for name in variables}

    for receipt in acquisition["cases"]:
        scenario_id = receipt["scenario_id"]
        path = ROOT / receipt["weather_json"]
        raw = path.read_bytes()
        digest = sha256(raw)
        data = json.loads(raw)
        cohort_row = manifest_cases.get(scenario_id)
        if cohort_row is None:
            errors.append("weather case is absent from cohort: " + scenario_id)
            continue
        if digest != receipt["weather_sha256"] or digest != cohort_row.get("weather_sha256"):
            errors.append("weather checksum mismatch: " + scenario_id)
        values = data.get("values", {})
        if data.get("scenario_id") != scenario_id or set(values) != set(variables):
            errors.append("wrong case ID or variable set: " + scenario_id)
            continue
        grid_points = set()
        for variable, item in values.items():
            units_by_variable[variable].add(item.get("unit"))
            if not math.isfinite(float(item["value"])):
                errors.append("non-finite value: {} {}".format(scenario_id, variable))
            grid_points.add((item["sample_grid_latitude"], item["sample_grid_longitude"]))
        if len(grid_points) != 1:
            errors.append("weather variables use different grid cells: " + scenario_id)
        event = json.loads((ROOT / cohort_row["scenario_manifest"]).read_text(encoding="utf-8"))["event"]
        rows.append({
            "scenario_id": scenario_id,
            "split": receipt["split"],
            "date": data["date"],
            "longitude": float(event["location_wgs84"]["longitude"]),
            "latitude": float(event["location_wgs84"]["latitude"]),
            "gridmet_wind_speed_10m_m_s": float(values["wind_speed_10m"]["value"]),
            "gridmet_fm100_model_g_percent": float(values["dead_fuel_moisture_100hr_model_g"]["value"]),
        })

    expected = {row["scenario_id"] for row in cohort["cases"]}
    seen = {row["scenario_id"] for row in rows}
    missing = sorted(expected - seen)
    unexpected = sorted(seen - expected)
    if missing:
        errors.append("weather context is missing {} cohort cases".format(len(missing)))
    if unexpected:
        errors.append("weather context includes {} non-cohort cases".format(len(unexpected)))

    summary = {
        "kind": "simfire_fpa_fod_gridmet_context_summary",
        "scientific_result": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "cohort_id": cohort["cohort_id"],
        "source_receipt": ACQUISITION_PATH.relative_to(ROOT).as_posix(),
        "case_count": len(rows),
        "expected_case_count": len(cohort["cases"]),
        "counts_by_split": {
            split: sum(row["split"] == split for row in rows)
            for split in ("train", "validation", "test")
        },
        "validation": {
            "all_cases_have_all_variables": not missing and not unexpected and not errors,
            "error_count": len(errors),
            "errors": errors,
            "missing_scenario_ids": missing,
            "variable_units": {name: sorted(value for value in units if value is not None)
                               for name, units in units_by_variable.items()},
            "all_weather_json_files_match_manifest_hashes": not any("checksum" in error for error in errors),
            "all_variables_for_each_case_share_one_grid_cell": not any("different grid" in error for error in errors),
        },
        "daily_context_ranges_by_split": {},
        "limitations": [
            "gridMET is daily, approximately 4-km regional gridded context, not hourly weather measured at the ignition point.",
            "FPA-FOD coordinates are incident references; the source does not establish an exact ignition GPS point.",
            "Daily gridMET periods are midnight-to-midnight Mountain Standard Time (UTC-7); FPA-FOD discovery HHMM has no confirmed timezone here.",
            "10-m wind, air humidity and NFDRS model-G 100-hour fuel moisture are not silently equated to SimFire midflame wind or fine-fuel moisture.",
            "This report verifies the downloaded context files; it is not a simulator validation or a trained-agent result.",
        ],
    }

    for split in ("train", "validation", "test"):
        subset = [row for row in rows if row["split"] == split]
        variables_to_summarize = {
            "gridmet_wind_speed_10m_m_s": "m/s",
            "gridmet_fm100_model_g_percent": "%",
        }
        summary["daily_context_ranges_by_split"][split] = {}
        for variable, unit in variables_to_summarize.items():
            values = [row[variable] for row in subset]
            summary["daily_context_ranges_by_split"][split][variable] = {
                "unit": unit,
                "count": len(values),
                "minimum": min(values) if values else None,
                "median": statistics.median(values) if values else None,
                "maximum": max(values) if values else None,
            }

    summary_path = out_dir / "simfire-cohort-v2-gridmet-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if errors:
        print(json.dumps({"summary": str(summary_path), "errors": errors}, indent=2))
        return 1

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"train": "#2b6cb0", "validation": "#dd6b20", "test": "#2f855a"}
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), constrained_layout=True)
    for split in ("train", "validation", "test"):
        subset = [row for row in rows if row["split"] == split]
        axes[0].scatter([row["longitude"] for row in subset], [row["latitude"] for row in subset],
                        s=24, alpha=0.82, color=colors[split], label="{} (n={})".format(split, len(subset)))
    axes[0].set_title("80 USFS incident reference points")
    axes[0].set_xlabel("Longitude")
    axes[0].set_ylabel("Latitude")
    axes[0].grid(alpha=0.2)
    axes[0].legend(frameon=False, fontsize=8)

    for axis, key, title, ylabel in (
        (axes[1], "gridmet_wind_speed_10m_m_s", "Daily gridMET wind", "10 m wind (m/s)"),
        (axes[2], "gridmet_fm100_model_g_percent", "Daily gridMET 100-hour fuel indicator", "NFDRS model-G FM100 (%)"),
    ):
        data = [[row[key] for row in rows if row["split"] == split] for split in ("train", "validation", "test")]
        box = axis.boxplot(data, tick_labels=["Train", "Validation", "Test"], patch_artist=True,
                           showmeans=True, medianprops={"color": "#1a202c", "linewidth": 1.5})
        for patch, split in zip(box["boxes"], ("train", "validation", "test")):
            patch.set_facecolor(colors[split])
            patch.set_alpha(0.55)
        axis.set_title(title)
        axis.set_ylabel(ylabel)
        axis.grid(axis="y", alpha=0.2)

    fig.suptitle("Real daily weather context; SimFire proxy is recorded separately", fontsize=14)
    fig.text(0.5, -0.01,
             "Locations are FPA-FOD incident references, not verified ignition GPS. Weather values are daily ~4-km grid cells.",
             ha="center", fontsize=9)
    visual_path = out_dir / "simfire-cohort-v2-gridmet-overview.png"
    fig.savefig(visual_path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    print(json.dumps({"summary": str(summary_path), "visual": str(visual_path),
                      "case_count": len(rows), "counts_by_split": summary["counts_by_split"],
                      "errors": errors}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
