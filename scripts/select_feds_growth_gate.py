#!/usr/bin/env python3
"""Apply the ADR-030 section 3 gate and selection rule to the 17 fixed TRAIN candidates.

Reads the full no-op reports written by ``evaluate_feds_train_noop.py`` (one per
candidate), recomputes the growth gate for each, and writes one summary with the
selected candidate or FAIL. The rule and the candidate list are fixed in ADR-030
and its gate addendum; this script only applies them. A report that is missing,
unfinished, or built from another manifest, weather file or parameter set stops
the selection instead of being skipped.
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
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from evaluate_feds_train_noop import growth_gate, sha256_file

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifests/feds-episode-cohort-v1.json"
WEATHER = ROOT / ".local/gridmet/feds-episode-weather-v1.json"
WEATHER_COVERAGE = ROOT / "reports/real-fire-data/feds-gridmet-weather-coverage-v1.json"
DEFAULT_REPORTS = ROOT / ".local/gate/adr030"
DEFAULT_OUT = ROOT / "reports/real-fire-data/feds-simfire-train-growth-gate-v1.json"

# ADR-030 section 3, "Candidates, fixed now": (wind adjustment factor, ROS multiplier).
CANDIDATES = tuple(
    [(waf, 1.0) for waf in (0.0, 0.0025, 0.01, 0.025, 0.05, 0.10, 0.20, 0.605)]
    + [(waf, ros) for ros in (0.35, 0.5, 0.7) for waf in (0.05, 0.2, 0.4)]
)
ACTIVE_CELL_LIFETIME_MINUTES = 90
INTERNAL_UPDATE_MINUTES = 5
SEED = 0
# The metrics the ADR-030 gate is defined on (feds_spread_metrics.METRICS_VERSION).
METRICS_VERSION = "feds-spread-metrics/3"
SCORED_HOURS = [12, 24, 36, 48]
HECTARES_PER_CELL = 180.0 * 180.0 / 10000.0

PASS_RULE = (
    "ADR-030 section 3: all TRAIN cases complete without errors; zero SimFire map-edge "
    "contacts in any case; on growing cases (observed +48h area >= 1.10 x initial) SimFire "
    "mean case growth IoU (pooled over the four timepoints) is higher than the downwind "
    "ellipse's."
)
SELECTION_RULE = (
    "ADR-030 section 3: among passing candidates, the highest growing-case mean growth IoU; "
    "tie: lower mean absolute area error (all TRAIN case-timepoints). No passing candidate: "
    "FAIL, nothing is frozen."
)


class GateInputError(ValueError):
    """A report cannot be used for the selection; stop instead of skipping it."""


def report_name(wind_adjustment_factor: float, ros_multiplier: float) -> str:
    return "waf-%g-ros-%g.json" % (wind_adjustment_factor, ros_multiplier)


def _simfire_params(wind_adjustment_factor: float, ros_multiplier: float) -> dict:
    return {
        "wind_adjustment_factor": wind_adjustment_factor,
        "internal_update_minutes": INTERNAL_UPDATE_MINUTES,
        "active_cell_lifetime_minutes": ACTIVE_CELL_LIFETIME_MINUTES,
        "ros_multiplier": ros_multiplier,
        "fireline_attenuation": "per_minute",
        "spread_aggregation": "last_write",
    }


def evaluate_candidate(
    payload: dict,
    *,
    wind_adjustment_factor: float,
    ros_multiplier: float,
    expected_scenario_ids,
    manifest_sha256: str,
    weather_sha256: str,
) -> dict:
    """Check one full report against its candidate and return its gate record."""
    label = report_name(wind_adjustment_factor, ros_multiplier)
    if payload.get("status") != "complete":
        raise GateInputError("%s is not complete (status %r); finish it with --resume."
                             % (label, payload.get("status")))
    params = _simfire_params(wind_adjustment_factor, ros_multiplier)
    expected_configuration = {
        "wind_adjustment_factor": wind_adjustment_factor,
        "internal_update_minutes": INTERNAL_UPDATE_MINUTES,
        "active_cell_lifetime_minutes": ACTIVE_CELL_LIFETIME_MINUTES,
        "ros_multiplier": ros_multiplier,
        "seed": SEED,
        "split": "train",
        "manifest_sha256": manifest_sha256,
        "expected_scenarios": len(expected_scenario_ids),
        "frozen_params_sha256": None,
        "metrics_version": METRICS_VERSION,
    }
    configuration = payload.get("configuration", {})
    differing = sorted(key for key, value in expected_configuration.items()
                       if configuration.get(key) != value)
    if differing:
        raise GateInputError("%s configuration differs from the candidate in %s."
                             % (label, differing))
    results, errors = payload["results"], payload["errors"]
    result_ids = [case["scenario_id"] for case in results]
    error_ids = [error["scenario_id"] for error in errors]
    if sorted(result_ids + error_ids) != sorted(expected_scenario_ids):
        raise GateInputError("%s does not cover each manifest TRAIN scenario exactly once." % label)
    for case in results:
        if case.get("split") != "train":
            raise GateInputError("%s holds a non-TRAIN case %s." % (label, case["scenario_id"]))
        if case["weather_source"]["sample_sha256"] != weather_sha256:
            raise GateInputError("%s case %s used another weather file."
                                 % (label, case["scenario_id"]))
        if case["simfire_params"] != params:
            raise GateInputError("%s case %s ran with other simulator parameters."
                                 % (label, case["scenario_id"]))
        if sorted(row["hours_since_start"] for row in case["trajectory"]) != SCORED_HOURS:
            raise GateInputError("%s case %s is not scored at +12/24/36/48h."
                                 % (label, case["scenario_id"]))

    gate = growth_gate(payload)
    stored = payload.get("growth_gate", {})
    if stored.get("pass") is not gate["pass"]:
        raise GateInputError("%s stores growth_gate.pass=%r but its results give %r."
                             % (label, stored.get("pass"), gate["pass"]))

    fail_reasons = []
    if errors:
        fail_reasons.append("case_errors")
    if gate["simfire_edge_contact_cases"]:
        fail_reasons.append("map_edge_contact")
    difference = gate["simfire_minus_ellipse"]
    if difference is None or not difference > 0:
        fail_reasons.append("growth_iou_not_above_ellipse")
    if bool(fail_reasons) is gate["pass"]:
        raise GateInputError("%s: fail reasons %s contradict growth_gate.pass=%r."
                             % (label, fail_reasons, gate["pass"]))

    rows = [row for case in results for row in case["trajectory"]]
    area_errors = [abs(float(row["predicted_area_ha"]) - float(row["observed_area_ha"]))
                   for row in rows]
    cases = gate["cases"]
    growing = cases[:gate["growing_cases"]]
    non_growing = cases[gate["growing_cases"]:]
    overgrowth = [case["simfire_growth_cells_48h"] - case["observed_growth_cells_48h"]
                  for case in non_growing]

    def mean(values):
        return statistics.fmean(values) if values else None

    mean_overgrowth = mean(overgrowth)
    return {
        "wind_adjustment_factor": wind_adjustment_factor,
        "ros_multiplier": ros_multiplier,
        "active_cell_lifetime_minutes": ACTIVE_CELL_LIFETIME_MINUTES,
        "internal_update_minutes": INTERNAL_UPDATE_MINUTES,
        "seed": SEED,
        "metrics_version": METRICS_VERSION,
        "successful_scenarios": len(results),
        "errors": len(errors),
        "simfire_edge_contact_cases": gate["simfire_edge_contact_cases"],
        "simfire_edge_contact_timepoints": sum(bool(row["touches_map_edge"]) for row in rows),
        "growing_cases": gate["growing_cases"],
        "non_growing_cases": gate["non_growing_cases"],
        "growing_scenario_ids": sorted(case["scenario_id"] for case in growing),
        "simfire_mean_case_growth_iou": gate["simfire_mean_case_growth_iou"],
        "ellipse_mean_case_growth_iou": gate["ellipse_mean_case_growth_iou"],
        "simfire_minus_ellipse": difference,
        "growing_cases_without_simfire_growth": sum(
            case["simfire_growth_cells_48h"] == 0 for case in growing),
        "ellipse_cases_without_new_cells": gate["ellipse_cases_without_new_cells"],
        "growth_gate_pass": gate["pass"],
        "fail_reasons": fail_reasons,
        "mean_absolute_area_error_ha": mean(area_errors),
        "non_growing_overgrowth": {
            "description": "SimFire growth beyond observed growth at +48h on non-growing cases; "
                           "reported as a known limitation, not part of the pass rule",
            "cases_with_simfire_growth": sum(
                case["simfire_growth_cells_48h"] > 0 for case in non_growing),
            "mean_simfire_growth_cells_48h": mean(
                [case["simfire_growth_cells_48h"] for case in non_growing]),
            "mean_observed_growth_cells_48h": mean(
                [case["observed_growth_cells_48h"] for case in non_growing]),
            "mean_overgrowth_cells_48h": mean_overgrowth,
            "median_overgrowth_cells_48h": statistics.median(overgrowth) if overgrowth else None,
            "max_overgrowth_cells_48h": max(overgrowth) if overgrowth else None,
            "mean_overgrowth_ha_48h": (mean_overgrowth * HECTARES_PER_CELL
                                       if mean_overgrowth is not None else None),
        },
    }


def select(records: list[dict]) -> dict | None:
    """Return the passing record with the highest growth IoU; tie: lower area error."""
    passing = [record for record in records if record["growth_gate_pass"]]
    if not passing:
        return None
    best_iou = max(record["simfire_mean_case_growth_iou"] for record in passing)
    tied = [record for record in passing if record["simfire_mean_case_growth_iou"] == best_iou]
    lowest_error = min(record["mean_absolute_area_error_ha"] for record in tied)
    tied = [record for record in tied if record["mean_absolute_area_error_ha"] == lowest_error]
    if len(tied) > 1:
        raise GateInputError(
            "Unresolved tie on growth IoU and area error between %s; ADR-030 names no further "
            "rule, so this needs a user decision."
            % [report_name(r["wind_adjustment_factor"], r["ros_multiplier"]) for r in tied])
    return tied[0]


def build_summary(
    reports_dir: Path,
    *,
    expected_scenario_ids,
    manifest_sha256: str,
    weather_sha256: str,
) -> dict:
    """Evaluate all 17 candidate reports and apply the selection rule."""
    records = []
    for waf, ros in CANDIDATES:
        path = Path(reports_dir) / report_name(waf, ros)
        if not path.is_file():
            raise GateInputError("Candidate report is missing: %s" % path)
        record = evaluate_candidate(
            json.loads(path.read_text(encoding="utf-8")),
            wind_adjustment_factor=waf, ros_multiplier=ros,
            expected_scenario_ids=expected_scenario_ids,
            manifest_sha256=manifest_sha256, weather_sha256=weather_sha256)
        try:
            local = str(path.resolve().relative_to(ROOT))
        except ValueError:
            local = str(path)
        record["local_full_report"] = local
        record["local_full_report_sha256"] = sha256_file(path)
        records.append(record)

    # The strata and the ellipse use FEDS and the first-segment wind only, so they cannot
    # differ between candidates that completed every case.
    complete = [record for record in records if not record["errors"]]
    if len({tuple(record["growing_scenario_ids"]) for record in complete}) > 1:
        raise GateInputError("Growing/non-growing strata differ between candidates.")
    if len({record["ellipse_mean_case_growth_iou"] for record in complete}) > 1:
        raise GateInputError("The ellipse reference differs between candidates.")

    chosen = select(records)
    reference = complete[0] if complete else None
    growing_ids = reference["growing_scenario_ids"] if reference else None
    for record in records:
        del record["growing_scenario_ids"]
    return {
        "schema_version": "feds-simfire-train-growth-gate/1.0",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "ADR-030 section 3 and its gate addendum; candidates and rule fixed before any run",
        "split": "train",
        "pass_rule": PASS_RULE,
        "selection_rule": SELECTION_RULE,
        "gate_status": "PASS" if chosen else "FAIL",
        "selected": chosen,
        "passing_candidates": sum(record["growth_gate_pass"] for record in records),
        "expected_scenarios": len(expected_scenario_ids),
        "growing_cases": reference["growing_cases"] if reference else None,
        "non_growing_cases": reference["non_growing_cases"] if reference else None,
        "growing_scenario_ids": growing_ids,
        "ellipse_mean_case_growth_iou": (
            reference["ellipse_mean_case_growth_iou"] if reference else None),
        "manifest_sha256": manifest_sha256,
        "weather_sha256": weather_sha256,
        "candidates": records,
        "test_cases_loaded": False,
        "physical_validation": False,
        "limitations": [
            "A TRAIN screening result. PASS means SimFire places growth better than a fixed "
            "geometric ellipse on growing fires; it is not a physical validation of the simulator.",
            "Non-growing cases are free-burning no-op runs against contained fires; their "
            "overgrowth is reported per candidate and does not decide the gate.",
            "FEDS perimeters are satellite-derived estimates; gridMET wind and fuel moisture are "
            "coarse daily proxies.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("Output exists; the gate summary is written once: %s" % args.out)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("test_cases_loaded") is not False:
        parser.error("Refusing a manifest that includes TEST cases.")
    train_ids = [case["scenario_id"] for case in manifest["cases"] if case.get("split") == "train"]
    manifest_sha256 = sha256_file(MANIFEST)
    weather_sha256 = sha256_file(WEATHER)
    coverage = json.loads(WEATHER_COVERAGE.read_text(encoding="utf-8"))
    if (coverage.get("weather_file_sha256") != weather_sha256
            or coverage.get("episode_manifest_sha256") != manifest_sha256):
        parser.error("The local weather file or manifest does not match the committed "
                     "weather coverage report.")
    try:
        summary = build_summary(
            args.reports_dir, expected_scenario_ids=train_ids,
            manifest_sha256=manifest_sha256, weather_sha256=weather_sha256)
    except GateInputError as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    chosen = summary["selected"]
    print(json.dumps({
        "output": str(args.out),
        "gate_status": summary["gate_status"],
        "passing_candidates": summary["passing_candidates"],
        "growing_cases": summary["growing_cases"],
        "non_growing_cases": summary["non_growing_cases"],
        "ellipse_mean_case_growth_iou": summary["ellipse_mean_case_growth_iou"],
        "selected": None if chosen is None else {
            key: chosen[key] for key in (
                "wind_adjustment_factor", "ros_multiplier", "simfire_mean_case_growth_iou",
                "simfire_minus_ellipse", "mean_absolute_area_error_ha")},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
