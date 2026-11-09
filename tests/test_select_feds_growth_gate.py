"""ADR-030 section 3 selection over the 17 fixed TRAIN gate candidates."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from scripts import evaluate_feds_train_noop as evaluator
from scripts import select_feds_growth_gate as selector

MANIFEST_SHA = "m" * 64
WEATHER_SHA = "w" * 64
HA = selector.HECTARES_PER_CELL


def _row(hours, predicted, observed, hits, *, initial=100, edge=False, ellipse=(1, 0)):
    ellipse_predicted, ellipse_hits = ellipse
    return {
        "hours_since_start": hours,
        "predicted_growth_cells": predicted,
        "observed_growth_cells": observed,
        "growth_intersection_cells": hits,
        "observed_burned_cells": initial + observed,
        "predicted_area_ha": (initial + predicted) * HA,
        "observed_area_ha": (initial + observed) * HA,
        "touches_map_edge": edge,
        "persistence_reference": {"predicted_burned_cells": initial},
        "ellipse_reference": {
            "predicted_growth_cells": ellipse_predicted,
            "observed_growth_cells": observed,
            "growth_intersection_cells": ellipse_hits,
        },
    }


def _case(scenario_id, *, predicted, observed, hits, edge=False, ellipse=(1, 0), waf=0.05, ros=1.0):
    """Four timepoints with the same growth counts; ``observed`` 0 makes it non-growing."""
    return {
        "scenario_id": scenario_id,
        "split": "train",
        "weather_source": {"sample_sha256": WEATHER_SHA},
        "simfire_params": {
            "wind_adjustment_factor": waf,
            "internal_update_minutes": 5,
            "active_cell_lifetime_minutes": 90,
            "ros_multiplier": ros,
            "fireline_attenuation": "per_minute",
            "spread_aggregation": "last_write",
        },
        "trajectory": [
            _row(hours, predicted, observed, hits, edge=edge and hours == 48, ellipse=ellipse)
            for hours in (12, 24, 36, 48)
        ],
    }


CASE_IDS = ("grow-a", "grow-b", "stalled-c")


def _payload(waf=0.05, ros=1.0, *, hits=(30, 30), predicted=(40, 40), stalled_growth=7,
             edge_case=None, status="complete", errors=(), drop=None):
    """Two growing cases (40 observed growth cells, ellipse IoU 10/40) and one stalled case."""
    results = [
        _case("grow-a", predicted=predicted[0], observed=40, hits=hits[0],
              ellipse=(10, 10), edge=edge_case == "grow-a", waf=waf, ros=ros),
        _case("grow-b", predicted=predicted[1], observed=40, hits=hits[1],
              ellipse=(10, 10), edge=edge_case == "grow-b", waf=waf, ros=ros),
        _case("stalled-c", predicted=stalled_growth, observed=0, hits=0,
              ellipse=(3, 0), edge=edge_case == "stalled-c", waf=waf, ros=ros),
    ]
    results = [case for case in results if case["scenario_id"] != drop]
    payload = {
        "status": status,
        "errors": list(errors),
        "results": results,
        "configuration": {
            "wind_adjustment_factor": waf,
            "internal_update_minutes": 5,
            "active_cell_lifetime_minutes": 90,
            "ros_multiplier": ros,
            "seed": 0,
            "manifest_sha256": MANIFEST_SHA,
            "split": "train",
            "expected_scenarios": len(CASE_IDS),
            "frozen_params_sha256": None,
            "metrics_version": "feds-spread-metrics/3",
        },
    }
    if status == "complete":
        payload["growth_gate"] = evaluator.growth_gate(payload)
    return payload


def _evaluate(payload, waf=0.05, ros=1.0):
    return selector.evaluate_candidate(
        payload, wind_adjustment_factor=waf, ros_multiplier=ros,
        expected_scenario_ids=CASE_IDS, manifest_sha256=MANIFEST_SHA, weather_sha256=WEATHER_SHA)


class CandidateListTests(unittest.TestCase):
    def test_candidates_are_the_17_fixed_in_adr030(self):
        expected = {(waf, 1.0) for waf in (0.0, 0.0025, 0.01, 0.025, 0.05, 0.10, 0.20, 0.605)}
        expected |= {(waf, ros) for ros in (0.35, 0.5, 0.7) for waf in (0.05, 0.2, 0.4)}
        self.assertEqual(len(selector.CANDIDATES), 17)
        self.assertEqual(set(selector.CANDIDATES), expected)
        self.assertEqual(len({selector.report_name(*c) for c in selector.CANDIDATES}), 17)


class EvaluateCandidateTests(unittest.TestCase):
    def test_candidate_passes_when_growth_iou_beats_the_ellipse(self):
        record = _evaluate(_payload())
        # SimFire: 30 hits / (40 + 40 - 30) = 0.6 per case; ellipse: 10 / 40 = 0.25.
        self.assertTrue(record["growth_gate_pass"])
        self.assertEqual(record["fail_reasons"], [])
        self.assertAlmostEqual(record["simfire_mean_case_growth_iou"], 0.6)
        self.assertAlmostEqual(record["ellipse_mean_case_growth_iou"], 0.25)
        self.assertEqual((record["growing_cases"], record["non_growing_cases"]), (2, 1))

    def test_candidate_fails_when_growth_iou_is_not_higher_than_the_ellipse(self):
        lower = _evaluate(_payload(hits=(5, 5)))  # 5 / 75 < 0.25
        self.assertFalse(lower["growth_gate_pass"])
        self.assertIn("growth_iou_not_above_ellipse", lower["fail_reasons"])
        equal = _evaluate(_payload(hits=(16, 16)))  # 16 / 64 == 0.25: must be strictly higher
        self.assertAlmostEqual(equal["simfire_minus_ellipse"], 0.0)
        self.assertFalse(equal["growth_gate_pass"])

    def test_edge_contact_in_any_case_fails_even_a_non_growing_one(self):
        for case in ("grow-a", "stalled-c"):
            record = _evaluate(_payload(edge_case=case))
            self.assertFalse(record["growth_gate_pass"])
            self.assertEqual(record["fail_reasons"], ["map_edge_contact"])
            self.assertEqual(record["simfire_edge_contact_cases"], 1)
            self.assertGreater(record["simfire_minus_ellipse"], 0)

    def test_case_errors_fail_the_candidate(self):
        errors = [{"scenario_id": "grow-b", "error_type": "ValueError", "error": "boom"}]
        record = _evaluate(_payload(errors=errors, drop="grow-b"))
        self.assertFalse(record["growth_gate_pass"])
        self.assertIn("case_errors", record["fail_reasons"])
        self.assertEqual((record["successful_scenarios"], record["errors"]), (2, 1))

    def test_unfinished_report_is_refused(self):
        with self.assertRaisesRegex(selector.GateInputError, "not complete"):
            _evaluate(_payload(status="running"))

    def test_report_missing_a_case_is_refused(self):
        with self.assertRaisesRegex(selector.GateInputError, "scenario"):
            _evaluate(_payload(drop="stalled-c"))

    def test_report_of_another_candidate_or_input_is_refused(self):
        with self.assertRaisesRegex(selector.GateInputError, "configuration"):
            _evaluate(_payload(waf=0.2), waf=0.05)
        wrong_manifest = _payload()
        wrong_manifest["configuration"]["manifest_sha256"] = "x" * 64
        with self.assertRaisesRegex(selector.GateInputError, "configuration"):
            _evaluate(wrong_manifest)
        wrong_weather = _payload()
        wrong_weather["results"][0]["weather_source"]["sample_sha256"] = "x" * 64
        with self.assertRaisesRegex(selector.GateInputError, "weather"):
            _evaluate(wrong_weather)
        wrong_params = _payload()
        wrong_params["results"][1]["simfire_params"]["spread_aggregation"] = "max"
        with self.assertRaisesRegex(selector.GateInputError, "simulator parameters"):
            _evaluate(wrong_params)

    def test_stored_gate_that_disagrees_with_the_recomputed_one_is_refused(self):
        payload = _payload()
        payload["growth_gate"]["pass"] = False
        with self.assertRaisesRegex(selector.GateInputError, "growth_gate"):
            _evaluate(payload)

    def test_non_growing_overgrowth_is_reported_in_cells_and_hectares(self):
        record = _evaluate(_payload(stalled_growth=7))
        stalled = record["non_growing_overgrowth"]
        self.assertEqual(stalled["cases_with_simfire_growth"], 1)
        self.assertAlmostEqual(stalled["mean_overgrowth_cells_48h"], 7.0)
        self.assertAlmostEqual(stalled["mean_overgrowth_ha_48h"], 7 * HA)
        # Mean |predicted - observed| over all 12 case-timepoints: (0 + 0 + 7) / 3 cells.
        self.assertAlmostEqual(record["mean_absolute_area_error_ha"], 7 * HA / 3)


class SelectionTests(unittest.TestCase):
    def _record(self, waf, **kwargs):
        return _evaluate(_payload(waf=waf, **kwargs), waf=waf)

    def test_highest_growing_case_growth_iou_among_passing_candidates_wins(self):
        records = [
            self._record(0.01, hits=(20, 20)),                      # passes, IoU 1/3
            self._record(0.05, hits=(30, 30)),                      # passes, IoU 0.6
            self._record(0.2, hits=(38, 38), edge_case="grow-a"),   # best IoU but touches the edge
            self._record(0.4, hits=(5, 5)),                         # below the ellipse
        ]
        chosen = selector.select(records)
        self.assertEqual(chosen["wind_adjustment_factor"], 0.05)

    def test_no_passing_candidate_selects_nothing(self):
        records = [self._record(0.01, hits=(5, 5)), self._record(0.2, edge_case="grow-b")]
        self.assertIsNone(selector.select(records))

    def test_tie_on_growth_iou_goes_to_the_lower_area_error(self):
        records = [
            self._record(0.01, stalled_growth=9),
            self._record(0.05, stalled_growth=2),
            self._record(0.2, stalled_growth=5),
        ]
        self.assertEqual(len({r["simfire_mean_case_growth_iou"] for r in records}), 1)
        self.assertEqual(selector.select(records)["wind_adjustment_factor"], 0.05)

    def test_tie_on_both_criteria_is_refused_not_broken_silently(self):
        records = [self._record(0.01), self._record(0.05)]
        with self.assertRaisesRegex(selector.GateInputError, "tie"):
            selector.select(records)


class SummaryTests(unittest.TestCase):
    def _write_reports(self, directory, *, passing=(0.05, 1.0), skip=None, unfinished=None):
        for waf, ros in selector.CANDIDATES:
            if (waf, ros) == skip:
                continue
            if (waf, ros) == unfinished:
                payload = _payload(waf, ros, status="running")
            elif (waf, ros) == passing:
                payload = _payload(waf, ros, hits=(30, 30))
            else:
                payload = _payload(waf, ros, hits=(5, 5))
            (directory / selector.report_name(waf, ros)).write_text(
                json.dumps(payload), encoding="utf-8")

    def _summary(self, directory):
        return selector.build_summary(
            directory, expected_scenario_ids=CASE_IDS,
            manifest_sha256=MANIFEST_SHA, weather_sha256=WEATHER_SHA)

    def test_summary_lists_all_17_and_the_selected_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            self._write_reports(directory)
            summary = self._summary(directory)
            self.assertEqual(summary["gate_status"], "PASS")
            self.assertEqual(len(summary["candidates"]), 17)
            self.assertEqual(sum(c["growth_gate_pass"] for c in summary["candidates"]), 1)
            self.assertEqual(
                (summary["selected"]["wind_adjustment_factor"], summary["selected"]["ros_multiplier"]),
                (0.05, 1.0))
            self.assertEqual(summary["weather_sha256"], WEATHER_SHA)
            self.assertEqual(summary["manifest_sha256"], MANIFEST_SHA)
            self.assertEqual((summary["growing_cases"], summary["non_growing_cases"]), (2, 1))
            chosen = directory / selector.report_name(0.05, 1.0)
            self.assertEqual(summary["selected"]["local_full_report_sha256"],
                             hashlib.sha256(chosen.read_bytes()).hexdigest())
            self.assertIs(summary["test_cases_loaded"], False)
            self.assertIs(summary["physical_validation"], False)

    def test_summary_records_fail_when_no_candidate_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            self._write_reports(directory, passing=None)
            summary = self._summary(directory)
            self.assertEqual(summary["gate_status"], "FAIL")
            self.assertIsNone(summary["selected"])
            self.assertEqual(len(summary["candidates"]), 17)

    def test_missing_or_unfinished_report_stops_the_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            self._write_reports(directory, skip=(0.4, 0.7))
            with self.assertRaisesRegex(selector.GateInputError, "missing"):
                self._summary(directory)
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            self._write_reports(directory, unfinished=(0.4, 0.7))
            with self.assertRaisesRegex(selector.GateInputError, "not complete"):
                self._summary(directory)

    def test_strata_must_not_depend_on_the_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            self._write_reports(directory)
            path = directory / selector.report_name(0.2, 0.5)
            payload = json.loads(path.read_text(encoding="utf-8"))
            for row in payload["results"][2]["trajectory"]:  # stalled-c now grows in FEDS
                row["observed_burned_cells"] = 150
            payload["growth_gate"] = evaluator.growth_gate(payload)
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(selector.GateInputError, "strata"):
                self._summary(directory)

    def test_main_refuses_to_overwrite_and_reports_the_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "summary.json"
            out.write_text("{}", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                selector.main(["--reports-dir", tmp, "--out", str(out)])
            self.assertIn("exists", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
