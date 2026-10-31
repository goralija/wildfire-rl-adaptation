#!/usr/bin/env python3
"""Build a verified comparison receipt for paired TRAIN-only weather replays."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
RUN_ROOT = ROOT / "runs/diagnostics/era5-fwi-sn-2018"
AUDIT_PATH = ROOT / "reports/real-fire-data/era5-fwi-sn-2018-pilot-comparison.json"
OUTPUT_PATH = ROOT / "reports/real-fire-data/era5-fwi-sn-2018-weather-replay-comparison.json"
SOURCE_RUNS = REPO_ROOT / "runs/real-case"
TARGET_DOY = {"2018_1770": 224, "2018_241": 227, "2018_747": 228}
FWI_FIELDS = {"FFMC", "DMC", "DC", "ISI", "BUI", "FWI"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        return list(reader.fieldnames), list(reader)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def compare_case(event_id: str, audit_case: dict[str, Any]) -> dict[str, Any]:
    case_root = RUN_ROOT / event_id
    original_case = SOURCE_RUNS / f"{event_id}-day{TARGET_DOY[event_id]}"
    original_input = original_case / "input"
    prepared_input = case_root / "input"
    baseline = load_json(case_root / "baseline-replay/run/result.json")
    updated = load_json(case_root / "era5-fwi-sn-replay/run/result.json")
    baseline_eval = load_json(case_root / "baseline-replay/evaluation.json")
    updated_eval = load_json(case_root / "era5-fwi-sn-replay/evaluation.json")
    input_manifest = load_json(case_root / "input-manifest.json")
    old_report = load_json(
        ROOT / f"reports/real-fire-data/{event_id}-day{TARGET_DOY[event_id]}-replay.json"
    )

    for label, result in (("baseline", baseline), ("ERA5-FWI-SN", updated)):
        require(result.get("success") is True, f"{event_id} {label} replay failed")
        require(result.get("policy") == "none", f"{event_id} {label} was not a no-action run")
        require(result.get("simulator_seed") == 123, f"{event_id} {label} seed changed")
        require(result.get("budget") == 0, f"{event_id} {label} budget changed")
        command = result.get("simulator_command", "")
        before_match = re.search(r"--steps-before\s+(\d+)", command)
        action_match = re.search(r"--steps-action\s+(\d+)", command)
        require(before_match is not None and before_match.group(1) == "0",
                f"{event_id} {label} warmup changed")
        require(action_match is not None and action_match.group(1) == "8",
                f"{event_id} {label} action interval changed")
        require(result.get("firehose_commit") == baseline.get("firehose_commit"), "runtime commit changed")
        require(result.get("script_sha256") == baseline.get("script_sha256"), "probe script changed")
    require(baseline.get("sync_reset") == updated.get("sync_reset"), f"{event_id} reset behavior changed")
    require(baseline.get("initial_state_csv_sha256") == updated.get("initial_state_csv_sha256"),
            f"{event_id} initial state changed")
    require(baseline.get("warmup_affected_cells") == updated.get("warmup_affected_cells"),
            f"{event_id} warmup affected count changed")
    require(baseline.get("warmup_active_cells") == updated.get("warmup_active_cells"),
            f"{event_id} warmup front count changed")
    require(baseline.get("input_sha256") == old_report["run"]["input_sha256"],
            f"{event_id} baseline does not reproduce the archived input tree")

    source_weather = original_input / "Weather.csv"
    updated_weather = prepared_input / "Weather.csv"
    source_fields, source_rows = read_csv(source_weather)
    updated_fields, updated_rows = read_csv(updated_weather)
    require(source_fields == updated_fields, f"{event_id} weather schema changed")
    require(len(source_rows) == len(updated_rows) == 24, f"{event_id} expected 24 weather rows")
    require(FWI_FIELDS.issubset(source_fields), f"{event_id} missing FWI fields")
    expected_values = audit_case["era5_fwi_sn_daily_values"]
    for old_row, new_row in zip(source_rows, updated_rows):
        for field in source_fields:
            if field not in FWI_FIELDS:
                require(old_row[field] == new_row[field],
                        f"{event_id} non-FWI weather field changed: {field}")
            else:
                require(float(new_row[field]) == float(expected_values[field]),
                        f"{event_id} ERA5 daily value mismatch for {field}")

    source_files = {p.relative_to(original_input) for p in original_input.rglob("*") if p.is_file()}
    prepared_files = {p.relative_to(prepared_input) for p in prepared_input.rglob("*") if p.is_file()}
    require(source_files - {Path("Weather.csv")} <= prepared_files,
            f"{event_id} source input file missing from diagnostic copy")
    for relative in source_files - {Path("Weather.csv")}:
        require(sha256(original_input / relative) == sha256(prepared_input / relative),
                f"{event_id} non-weather simulator input changed: {relative}")
    require(input_manifest["original_weather_csv_sha256"] == sha256(source_weather),
            f"{event_id} original weather checksum mismatch")
    require(input_manifest["diagnostic_weather_csv_sha256"] == sha256(updated_weather),
            f"{event_id} updated weather checksum mismatch")

    old_prediction = baseline_eval["simulator_prediction"]
    new_prediction = updated_eval["simulator_prediction"]
    old_metrics = baseline_eval["metrics"]
    new_metrics = updated_eval["metrics"]
    return {
        "event_id": event_id,
        "target_date_local": audit_case["target_date_local"],
        "weather_source_point_wgs84": audit_case["query_point_wgs84"],
        "nearest_era5_fwi_sn_grid_point_wgs84": audit_case["nearest_era5_grid_point_wgs84"],
        "point_to_grid_distance_km": audit_case["point_to_grid_distance_km"],
        "daily_fwi_codes": expected_values,
        "original_cfsds_fire_day_summary_codes": audit_case["cfsds_fire_day_summary_values"],
        "input_control": {
            "baseline_input_tree_sha256": baseline["input_sha256"],
            "updated_input_tree_sha256": updated["input_sha256"],
            "baseline_matches_archived_replay_input": True,
            "initial_state_csv_sha256": updated["initial_state_csv_sha256"],
            "original_weather_csv_sha256": input_manifest["original_weather_csv_sha256"],
            "updated_weather_csv_sha256": input_manifest["diagnostic_weather_csv_sha256"],
            "updated_columns": input_manifest["modified_columns"],
            "hourly_rows": input_manifest["hourly_rows"],
            "daily_fwi_codes_repeated_for_all_24_hour_rows": True,
            "all_other_source_inputs_and_hourly_weather_fields_unchanged": True,
            "same_policy_seed_budget_reset_setting_and_container_probe": True,
        },
        "baseline_result": {
            "decisions": baseline["decisions"],
            "final_grid_index": baseline_eval["run"]["final_grid_index"],
            "new_burned_area_ha": old_prediction["newly_burned_area_ha"],
            "final_total_affected_cells": old_prediction["final_total_affected_cells"],
            "predicted_edge_cells": old_prediction["predicted_edge_cells"],
            "precision": old_metrics["area_weighted_precision"],
            "recall": old_metrics["area_weighted_recall"],
            "iou": old_metrics["area_weighted_iou"],
        },
        "era5_fwi_sn_result": {
            "decisions": updated["decisions"],
            "final_grid_index": updated_eval["run"]["final_grid_index"],
            "new_burned_area_ha": new_prediction["newly_burned_area_ha"],
            "final_total_affected_cells": new_prediction["final_total_affected_cells"],
            "predicted_edge_cells": new_prediction["predicted_edge_cells"],
            "precision": new_metrics["area_weighted_precision"],
            "recall": new_metrics["area_weighted_recall"],
            "iou": new_metrics["area_weighted_iou"],
        },
        "change_era5_fwi_sn_minus_baseline": {
            "new_burned_area_ha": round(
                new_prediction["newly_burned_area_ha"] - old_prediction["newly_burned_area_ha"], 4
            ),
            "final_total_affected_cells": (
                new_prediction["final_total_affected_cells"] - old_prediction["final_total_affected_cells"]
            ),
            "iou": round(new_metrics["area_weighted_iou"] - old_metrics["area_weighted_iou"], 4),
            "edge_cells": new_prediction["predicted_edge_cells"] - old_prediction["predicted_edge_cells"],
        },
        "replay_result_sha256": {
            "baseline": sha256(case_root / "baseline-replay/run/result.json"),
            "era5_fwi_sn": sha256(case_root / "era5-fwi-sn-replay/run/result.json"),
        },
    }


def main() -> int:
    audit = load_json(AUDIT_PATH)
    cases_by_id = {item["event_id"]: item for item in audit["cases"]}
    require(set(cases_by_id) == set(TARGET_DOY), "Expected only the three fixed TRAIN pilot cases")
    cases = [compare_case(event_id, cases_by_id[event_id]) for event_id in TARGET_DOY]
    result = {
        "schema": "era5-fwi-sn-weather-replay-comparison/v1",
        "created_utc_date": "2026-10-31",
        "scope": "Three existing 2018 TRAIN diagnostic cases only; no validation/test targets, calibration, policy test, or training.",
        "question": "Does replacing the old CFSDS fire-day summary codes with nearest-grid daily ERA5-FWI-SN codes resolve the observed no-action mismatch?",
        "runtime": {
            "image": "wildfire-firehose-probe:20261030-real-case",
            "image_id": "sha256:bf250dd34cebdff5f38e17056c73ef2f914055bdde29b0d6fea9afc16cbd10a3",
            "firehose_commit": "e49a52a9a987a1585d25ddca2f711222ca500ffb",
            "container_network": "disabled",
            "training_performed": False,
        },
        "input_preparation_script_sha256": sha256(ROOT / "scripts/prepare_era5_fwi_sn_replay_inputs.py"),
        "comparison_script_sha256": sha256(Path(__file__)),
        "weather_audit_sha256": sha256(AUDIT_PATH),
        "cases": cases,
        "summary": {
            "successful_paired_replays": len(cases),
            "cases_with_changed_final_affected_cell_count": sum(
                item["change_era5_fwi_sn_minus_baseline"]["final_total_affected_cells"] != 0
                for item in cases
            ),
            "cases_with_same_final_affected_cell_count": sum(
                item["change_era5_fwi_sn_minus_baseline"]["final_total_affected_cells"] == 0
                for item in cases
            ),
            "cases_still_touching_crop_edge_after_updated_weather": sum(
                item["era5_fwi_sn_result"]["predicted_edge_cells"] > 0 for item in cases
            ),
            "interpretation": (
                "The updated daily weather source is usable and reproducible, but it does not resolve the large "
                "no-action mismatch in these cases. Two final masks are unchanged; one has three fewer newly "
                "burned cells. All three still touch the crop edge. This is a small deterministic sensitivity "
                "experiment, not physical validation or a model calibration."
            ),
        },
        "limitations": [
            "ERA5-FWI-SN daily codes are held unchanged across 24 hourly simulator weather rows; they are not presented as hourly observations.",
            "The ERA5-FWI-SN grid is approximately 31 km, much coarser than the 2 km Cell2Fire crop and the separate hourly weather point.",
            "CFSDS target masks are satellite-derived daily estimates; exact within-day burn timing is unavailable.",
            "The three pilot incidents have unknown or documented partial suppression evidence, so observed growth is not a clean untreated trajectory.",
            "Only one seed per paired replay was run because this tests input sensitivity, not stochastic policy performance.",
            "Fuel vintage, crop boundary, fuel spread calibration, and suppression evidence remain unresolved.",
        ],
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": str(OUTPUT_PATH), **result["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
