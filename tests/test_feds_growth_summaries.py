"""Growth-only metric reporting in the FEDS no-op gate and calibration-gap scripts."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest("optional NumPy dependency is not installed: %s" % exc)

from scripts import diagnose_feds_noop_gate as gate_diagnosis
from scripts import diagnose_synthetic_calibration_gap as calibration_gap
from scripts import evaluate_feds_train_noop as evaluator
from wildfire_rl.feds_spread_metrics import binary_burn_metrics


def _masks():
    initial = np.zeros((6, 6), dtype=bool)
    initial[1:4, 1:4] = True
    grown = initial.copy()
    grown[1:4, 4] = True
    false_growth = initial.copy()
    false_growth[4, 1] = True
    return initial, grown, false_growth


def _trajectory_row(predicted, observed, initial, hours):
    row = binary_burn_metrics(predicted, observed, initial_burn=initial)
    row.update({
        "hours_since_start": hours,
        "fire_active_after_segment": True,
        "forcing": {"wind_speed_proxy_ft_per_min": 100.0, "fuel_moisture_fraction_proxy": 0.1},
        "persistence_reference": binary_burn_metrics(initial, observed, initial_burn=initial),
        "ellipse_reference": binary_burn_metrics(initial, observed, initial_burn=initial),
    })
    return row


def _case():
    """One growing timepoint scored perfectly and one stalled timepoint with false growth."""
    initial, grown, false_growth = _masks()
    return {
        "scenario_id": "train-fake",
        "initial_feds_state": {"burn_scar_cells": int(initial.sum())},
        "trajectory": [
            _trajectory_row(grown, grown, initial, 12),
            _trajectory_row(false_growth, initial, initial, 24),
        ],
    }


class EvaluatorGrowthSummaryTests(unittest.TestCase):
    def test_growth_summary_is_stratified_on_observed_growth(self):
        summary = evaluator.summarize([_case()])

        noop = summary["methods"]["simfire_noop"]
        persistence = summary["methods"]["persistence"]
        self.assertIn("mean_iou", noop)
        self.assertEqual(noop["growth"]["growing_timepoints"], 1)
        self.assertEqual(noop["growth"]["mean_growth_iou"], 1.0)
        self.assertEqual(noop["growth"]["median_growth_iou"], 1.0)
        self.assertEqual(noop["growth"]["mean_growth_recall"], 1.0)
        # Pooled over all timepoints, so false growth on the stalled one counts.
        self.assertAlmostEqual(noop["growth"]["pooled_growth_precision"], 3 / 4)
        self.assertEqual(noop["growth"]["pooled_growth_recall"], 1.0)
        self.assertEqual(noop["growth"]["stalled_timepoints"], 1)
        self.assertEqual(noop["growth"]["stalled_timepoints_with_predicted_growth"], 1)
        self.assertEqual(noop["growth"]["mean_false_growth_cells_when_stalled"], 1.0)

        self.assertEqual(persistence["growth"]["mean_growth_iou"], 0.0)
        self.assertIsNone(persistence["growth"]["pooled_growth_precision"])
        self.assertEqual(persistence["growth"]["growing_timepoints_without_predicted_growth"], 1)
        self.assertEqual(persistence["growth"]["stalled_timepoints_with_predicted_growth"], 0)

        paired = summary["paired_comparisons"]["persistence"]
        self.assertEqual(paired["mean_growth_iou_delta_noop_minus_reference"], 1.0)
        self.assertIn("mean_iou_delta_noop_minus_reference", paired)

    def test_growth_summary_handles_no_growing_timepoints(self):
        case = _case()
        case["trajectory"] = case["trajectory"][1:]

        summary = evaluator.summarize([case])

        growth = summary["methods"]["simfire_noop"]["growth"]
        self.assertEqual(growth["growing_timepoints"], 0)
        self.assertIsNone(growth["mean_growth_iou"])
        self.assertIsNone(
            summary["paired_comparisons"]["persistence"]["mean_growth_iou_delta_noop_minus_reference"]
        )

    def test_resume_refuses_report_scored_with_previous_metrics(self):
        manifest = json.loads(evaluator.MANIFEST.read_text(encoding="utf-8"))
        old_configuration = {
            "wind_adjustment_factor": 0.5,
            "internal_update_minutes": 5,
            "active_cell_lifetime_minutes": 90,
            "ros_multiplier": 1.0,
            "seed": 0,
            "manifest_sha256": evaluator.sha256_file(evaluator.MANIFEST),
            "split": "train",
            "expected_scenarios": manifest["case_counts_by_split"]["train"],
            "frozen_params_sha256": None,
        }
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "old.json"
            out.write_text(json.dumps({"configuration": old_configuration, "status": "complete"}))
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                evaluator.main(["--wind-adjustment-factor", "0.5", "--out", str(out), "--resume"])
        self.assertIn("does not match this configuration", stderr.getvalue())


class GateDiagnosisGrowthTests(unittest.TestCase):
    def test_rows_derive_growth_iou_from_counts(self):
        case = _case()
        rows = gate_diagnosis.case_rows({"results": [case]})

        for row, scored in zip(rows, case["trajectory"]):
            self.assertEqual(row["growth_iou"], scored["growth_iou"])
            self.assertEqual(row["persistence_growth_iou"],
                             scored["persistence_reference"]["growth_iou"])
        self.assertEqual(rows[0]["growth_iou"], 1.0)
        self.assertEqual(rows[1]["growth_iou"], 0.0)  # false growth while FEDS stalled
        self.assertIsNone(rows[1]["persistence_growth_iou"])

    def test_summary_reports_growth_iou_only_where_feds_grows(self):
        summary = gate_diagnosis.summarize(gate_diagnosis.case_rows({"results": [_case()]}))

        block = summary["all"]
        self.assertEqual(block["growing_timepoints"], 1)
        self.assertEqual(block["mean_growth_iou_when_observed_grows"], 1.0)
        self.assertEqual(block["mean_persistence_growth_iou_when_observed_grows"], 0.0)
        self.assertAlmostEqual(block["pooled_growth_iou"], 3 / 4)
        self.assertIn("growth_iou", summary["worst_timepoints"][0])


class CalibrationGapGrowthTests(unittest.TestCase):
    def test_aggregate_reports_growth_iou_on_growing_cases(self):
        def row(growth_iou, obs_new, sim_new):
            return {
                "hours_since_start": 12, "observed_cells_outside_crop": 0,
                "iou": 0.8, "area_ratio_sim_over_obs": 1.0,
                "growth_vs_observed": "equal", "sim_new_cells": sim_new,
                "obs_new_cells": obs_new, "growth_iou": growth_iou,
                "growth_precision": None, "growth_recall": None,
            }

        results = [
            {"split": "train", "trajectory": [row(0.2, 4, 3)]},
            {"split": "train", "trajectory": [row(0.6, 2, 2)]},
            {"split": "train", "trajectory": [row(None, 0, 1)]},
        ]

        by_hour = calibration_gap.aggregate(results)["ex_train"]["by_hour"]

        self.assertEqual(by_hour["12"]["growing_cases"], 2)
        self.assertAlmostEqual(by_hour["12"]["median_growth_iou"], 0.4)
        self.assertEqual(by_hour["12"]["stalled_cases_sim_grows"], 1)
        self.assertEqual(by_hour["12"]["median_iou"], 0.8)
        self.assertIsNone(by_hour["24"]["median_growth_iou"])


if __name__ == "__main__":
    unittest.main()


def _gate_case(scenario_id, sim, ellipse, observed, initial, edge_hour=None):
    """Four-timepoint case with SimFire, ellipse and FEDS masks given per horizon."""
    rows = []
    for hours in (12, 24, 36, 48):
        row = binary_burn_metrics(sim[hours], observed[hours], initial_burn=initial)
        row.update({
            "hours_since_start": hours,
            "persistence_reference": binary_burn_metrics(initial, observed[hours], initial_burn=initial),
            "ellipse_reference": binary_burn_metrics(ellipse[hours], observed[hours], initial_burn=initial),
        })
        if edge_hour == hours:
            row["touches_map_edge"] = True
        rows.append(row)
    return {"scenario_id": scenario_id, "trajectory": rows}


def _late_growing_case(scenario_id="late", edge_hour=None):
    """Growing under ADR-030 (48h area 2.5x) but flat at 12h and 24h, as in the review repro."""
    initial = np.zeros((40, 40), dtype=bool)
    initial[18:22, 18:22] = True
    observed = {hours: initial.copy() for hours in (12, 24, 36, 48)}
    observed[36][14:18, 18:22] = True
    observed[48][12:18, 18:22] = True
    sim = {hours: initial.copy() for hours in observed}
    sim[36][16:18, 18:22] = True
    sim[48][14:18, 18:22] = True
    ellipse = {hours: initial.copy() for hours in observed}
    ellipse[24][17, 18:22] = True
    ellipse[36][16:18, 18:22] = True
    ellipse[48][15:18, 18:22] = True
    return _gate_case(scenario_id, sim, ellipse, observed, initial, edge_hour)


def _stalled_case(scenario_id="stalled"):
    initial = np.zeros((40, 40), dtype=bool)
    initial[18:22, 18:22] = True
    observed = {hours: initial.copy() for hours in (12, 24, 36, 48)}
    sim = {hours: initial.copy() for hours in observed}
    sim[48][22:26, 18:22] = True
    return _gate_case(scenario_id, sim, dict(observed), observed, initial)


class GrowthGateTests(unittest.TestCase):
    def payload(self, cases, status="complete", errors=()):
        return {"status": status, "errors": list(errors), "results": cases}

    def test_case_level_strata_and_pooled_iou_are_defined_for_late_growth(self):
        gate = evaluator.growth_gate(self.payload([_late_growing_case(), _stalled_case()]))
        self.assertEqual((gate["growing_cases"], gate["non_growing_cases"]), (1, 1))
        # SimFire hits 8 of a 16-cell union at 36h and 16 of 24 at 48h; pooled 24/40.
        self.assertAlmostEqual(gate["simfire_mean_case_growth_iou"], (8 + 16) / (16 + 24))
        # Ellipse grows early (24h) while FEDS has not: that false growth is part of its union.
        self.assertAlmostEqual(gate["ellipse_mean_case_growth_iou"], (8 + 12) / (4 + 16 + 24))
        self.assertTrue(gate["pass"])
        self.assertEqual(gate["non_growing_overgrowth"]["mean_simfire_growth_cells_48h"], 16)

    def test_gate_fails_on_any_edge_contact_or_incomplete_cohort(self):
        self.assertFalse(evaluator.growth_gate(
            self.payload([_late_growing_case(edge_hour=24)]))["pass"])
        self.assertFalse(evaluator.growth_gate(
            self.payload([_late_growing_case()], status="incomplete"))["pass"])
        self.assertFalse(evaluator.growth_gate(
            self.payload([_late_growing_case()], errors=[{"scenario_id": "x"}]))["pass"])

    def test_gate_without_growing_cases_cannot_pass(self):
        gate = evaluator.growth_gate(self.payload([_stalled_case()]))
        self.assertEqual(gate["growing_cases"], 0)
        self.assertFalse(gate["pass"])
