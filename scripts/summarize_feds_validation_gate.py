#!/usr/bin/env python3
"""Write the committed summary of the single frozen VALIDATION no-op score.

Reads the full report that ``evaluate_feds_train_noop.py --split validation`` wrote
under an allowlisted TRAIN freeze record and summarises it. Nothing is simulated or
scored again here, so rerunning this script is not a second VALIDATION score. The
report must have been run with exactly the freeze record's parameters and inputs.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys

try:
    from scripts.evaluate_feds_train_noop import growth_gate, sha256_file
    from scripts.select_feds_growth_gate import (
        HECTARES_PER_CELL, METRICS_VERSION, SCORED_HOURS, SEED, GateInputError)
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from evaluate_feds_train_noop import growth_gate, sha256_file
    from select_feds_growth_gate import (
        HECTARES_PER_CELL, METRICS_VERSION, SCORED_HOURS, SEED, GateInputError)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / ".local/gate/adr030/validation-frozen.json"
DEFAULT_FREEZE = ROOT / "configs/frozen/feds-simfire-growth-gate-freeze-v1.json"
DEFAULT_OUT = ROOT / "reports/real-fire-data/feds-simfire-validation-growth-gate-v1.json"


def _relative(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def summarize_validation(payload: dict, freeze: dict, *, freeze_sha256: str) -> dict:
    """Check the full VALIDATION report against the freeze record and summarise it."""
    if payload.get("status") != "complete":
        raise GateInputError("The VALIDATION report is not complete (status %r)."
                             % payload.get("status"))
    params = freeze["frozen_params"]
    expected_configuration = {
        "wind_adjustment_factor": params["wind_adjustment_factor"],
        "internal_update_minutes": params["internal_update_minutes"],
        "active_cell_lifetime_minutes": params["active_cell_lifetime_minutes"],
        "ros_multiplier": params["ros_multiplier"],
        "seed": SEED,
        "split": "validation",
        "manifest_sha256": freeze["manifest_sha256"],
        "frozen_params_sha256": freeze_sha256,
        "metrics_version": METRICS_VERSION,
    }
    configuration = payload.get("configuration", {})
    differing = sorted(key for key, value in expected_configuration.items()
                       if configuration.get(key) != value)
    if differing:
        raise GateInputError("The VALIDATION report configuration differs from the freeze "
                             "record in %s." % differing)
    results, errors = payload["results"], payload["errors"]
    if len(results) + len(errors) != configuration.get("expected_scenarios"):
        raise GateInputError("The VALIDATION report does not cover every expected scenario.")
    for case in results:
        if case.get("split") != "validation":
            raise GateInputError("Case %s is not a VALIDATION case." % case["scenario_id"])
        if case["weather_source"]["sample_sha256"] != freeze["weather_sha256"]:
            raise GateInputError("Case %s used another weather file." % case["scenario_id"])
        if case["simfire_params"] != params:
            raise GateInputError("Case %s ran with other simulator parameters."
                                 % case["scenario_id"])
        if sorted(row["hours_since_start"] for row in case["trajectory"]) != SCORED_HOURS:
            raise GateInputError("Case %s is not scored at +12/24/36/48h." % case["scenario_id"])

    gate = growth_gate(payload)
    if payload.get("growth_gate", {}).get("pass") is not gate["pass"]:
        raise GateInputError("The stored growth_gate.pass disagrees with the report's results.")
    cases = gate["cases"]
    growing, non_growing = cases[:gate["growing_cases"]], cases[gate["growing_cases"]:]
    growing_ids = {case["scenario_id"] for case in growing}
    overgrowth = [case["simfire_growth_cells_48h"] - case["observed_growth_cells_48h"]
                  for case in non_growing]
    mean_overgrowth = statistics.fmean(overgrowth) if overgrowth else None
    methods = payload["summary"]["methods"]
    return {
        "schema_version": "feds-simfire-validation-growth-gate/1.1",
        "decision": "ADR-030 section 3: VALIDATION scored once with the TRAIN freeze; never "
                    "used for selection (ADR-031)",
        "split": "validation",
        "scored_once": True,
        "used_for_selection": False,
        "scored_utc": payload.get("finished_utc"),
        "freeze_record_sha256": freeze_sha256,
        "simfire_params": params,
        "seed": SEED,
        "manifest_sha256": freeze["manifest_sha256"],
        "weather_sha256": freeze["weather_sha256"],
        "metrics_version": METRICS_VERSION,
        "successful_scenarios": len(results),
        "errors": len(errors),
        "growth_gate": {
            "rule": gate["rule"],
            "pass": gate["pass"],
            "growing_cases": gate["growing_cases"],
            "non_growing_cases": gate["non_growing_cases"],
            "simfire_mean_case_growth_iou": gate["simfire_mean_case_growth_iou"],
            "ellipse_mean_case_growth_iou": gate["ellipse_mean_case_growth_iou"],
            "simfire_minus_ellipse": gate["simfire_minus_ellipse"],
            "simfire_edge_contact_cases": gate["simfire_edge_contact_cases"],
            "ellipse_cases_without_new_cells": gate["ellipse_cases_without_new_cells"],
            "growing_cases_without_simfire_growth": sum(
                case["simfire_growth_cells_48h"] == 0 for case in growing),
        },
        "non_growing_overgrowth": {
            "description": "SimFire growth beyond observed growth at +48h on non-growing cases; "
                           "known limitation, not part of the rule",
            "cases": [{"scenario_id": case["scenario_id"],
                       "simfire_growth_cells_48h": case["simfire_growth_cells_48h"],
                       "observed_growth_cells_48h": case["observed_growth_cells_48h"]}
                      for case in non_growing],
            "mean_overgrowth_cells_48h": mean_overgrowth,
            "mean_overgrowth_ha_48h": (mean_overgrowth * HECTARES_PER_CELL
                                       if mean_overgrowth is not None else None),
        },
        "full_mask_metrics_for_context": {
            "note": "Full-mask IoU includes the initial burn shared by every method; the "
                    "ADR-022/023 strict screen built on it is superseded by the growth gate.",
            **{name: {"mean_iou": methods[name]["mean_iou"],
                      "mean_absolute_area_error_ha": methods[name]["mean_absolute_area_error_ha"]}
               for name in ("simfire_noop", "persistence", "ellipse_reference")},
            "strict_screen_pass": payload["strict_screen"]["pass"],
        },
        "case_growth_iou": [{"scenario_id": case["scenario_id"],
                             "growing": case["scenario_id"] in growing_ids,
                             "simfire_growth_iou": case["simfire_growth_iou"],
                             "ellipse_growth_iou": case["ellipse_growth_iou"]} for case in cases],
        "test_cases_loaded": False,
        "physical_validation": False,
        "limitations": [
            "%d VALIDATION cases (%d growing); a single no-op run with seed %d. Not a physical "
            "validation of the simulator." % (len(results), gate["growing_cases"], SEED),
            "Stage 2 follows from the TRAIN gate result alone; this score did not decide it.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--freeze-record", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument("--code-commit", required=True,
                        help="repository commit the VALIDATION run was made from")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    payload = json.loads(args.report.read_text(encoding="utf-8"))
    if payload.get("test_cases_loaded") is not False:
        parser.error("Refusing a report that loaded TEST cases.")
    freeze = json.loads(args.freeze_record.read_text(encoding="utf-8"))
    try:
        summary = summarize_validation(payload, freeze,
                                       freeze_sha256=sha256_file(args.freeze_record))
    except GateInputError as exc:
        parser.error(str(exc))
    summary.update({
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "code_commit": args.code_commit,
        "freeze_record": _relative(args.freeze_record),
        "local_full_report": _relative(args.report),
        "local_full_report_sha256": sha256_file(args.report),
    })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.out), "growth_gate": summary["growth_gate"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
