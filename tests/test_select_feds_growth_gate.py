"""ADR-030 section 3 selection over the 17 fixed TRAIN gate candidates."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock

from scripts import evaluate_feds_train_noop as evaluator
from scripts import select_feds_growth_gate as selector
from scripts import summarize_feds_validation_gate as validation_summary

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


def _case(scenario_id, *, predicted, observed, hits, edge=False, ellipse=(1, 0), waf=0.05, ros=1.0,
          split="train", weather_sha=WEATHER_SHA):
    """Four timepoints with the same growth counts; ``observed`` 0 makes it non-growing."""
    return {
        "scenario_id": scenario_id,
        "split": split,
        "weather_source": {"sample_sha256": weather_sha},
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
             edge_case=None, status="complete", errors=(), drop=None, split="train",
             manifest_sha=MANIFEST_SHA, weather_sha=WEATHER_SHA, frozen_sha=None):
    """Two growing cases (40 observed growth cells, ellipse IoU 10/40) and one stalled case."""
    shared = dict(waf=waf, ros=ros, split=split, weather_sha=weather_sha)
    results = [
        _case("grow-a", predicted=predicted[0], observed=40, hits=hits[0],
              ellipse=(10, 10), edge=edge_case == "grow-a", **shared),
        _case("grow-b", predicted=predicted[1], observed=40, hits=hits[1],
              ellipse=(10, 10), edge=edge_case == "grow-b", **shared),
        _case("stalled-c", predicted=stalled_growth, observed=0, hits=0,
              ellipse=(3, 0), edge=edge_case == "stalled-c", **shared),
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
            "manifest_sha256": manifest_sha,
            "split": split,
            "expected_scenarios": len(CASE_IDS),
            "frozen_params_sha256": frozen_sha,
            "metrics_version": "feds-spread-metrics/3",
        },
    }
    if status == "complete":
        payload["growth_gate"] = evaluator.growth_gate(payload)
    return payload


def _set_stalled_growth(payload, cells_by_timepoint):
    """Give the stalled case different SimFire growth at each of its four timepoints."""
    for row, cells in zip(payload["results"][2]["trajectory"], cells_by_timepoint):
        row["predicted_growth_cells"] = cells
        row["predicted_area_ha"] = (100 + cells) * HA
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

    def test_pinned_metrics_version_is_the_one_the_metrics_module_states(self):
        source = (selector.ROOT / "src/wildfire_rl/feds_spread_metrics.py").read_text(encoding="utf-8")
        stated = re.search(r'^METRICS_VERSION = "([^"]+)"', source, re.MULTILINE).group(1)
        self.assertEqual(selector.METRICS_VERSION, stated)


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

    def test_every_configuration_field_of_the_candidate_is_checked(self):
        wrong = {"seed": 1, "split": "validation", "frozen_params_sha256": "f" * 64,
                 "expected_scenarios": 2, "active_cell_lifetime_minutes": 60,
                 "internal_update_minutes": 1, "ros_multiplier": 0.5,
                 "metrics_version": "feds-spread-metrics/2"}
        for key, value in wrong.items():
            payload = _payload()
            payload["configuration"][key] = value
            with self.subTest(field=key), self.assertRaisesRegex(selector.GateInputError, key):
                _evaluate(payload)

    def test_non_train_case_or_missing_timepoint_is_refused(self):
        foreign = _payload()
        foreign["results"][0]["split"] = "validation"
        with self.assertRaisesRegex(selector.GateInputError, "non-TRAIN"):
            _evaluate(foreign)
        short = _payload()
        del short["results"][2]["trajectory"][3]  # the stalled case loses its +48h row
        short["growth_gate"] = evaluator.growth_gate(short)
        with self.assertRaisesRegex(selector.GateInputError, "12/24/36/48h"):
            _evaluate(short)

    def test_fail_reasons_that_contradict_the_gate_are_refused(self):
        payload = _payload(edge_case="grow-a")
        claimed = dict(payload["growth_gate"], **{"pass": True})
        payload["growth_gate"]["pass"] = True
        with mock.patch.object(selector, "growth_gate", return_value=claimed), \
                self.assertRaisesRegex(selector.GateInputError, "contradict"):
            _evaluate(payload)

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

    def test_tie_break_area_error_covers_all_four_timepoints(self):
        # Late growth: 8 cells at +48h only (mean 2 over its timepoints). Steady growth: 5
        # cells at every timepoint. A +48h-only error would prefer the steady candidate.
        late = _evaluate(_set_stalled_growth(_payload(waf=0.01), (0, 0, 0, 8)), waf=0.01)
        steady = _evaluate(_set_stalled_growth(_payload(waf=0.05), (5, 5, 5, 5)), waf=0.05)
        self.assertEqual(late["simfire_mean_case_growth_iou"], steady["simfire_mean_case_growth_iou"])
        self.assertAlmostEqual(late["mean_absolute_area_error_ha"], 8 * HA / 12)
        self.assertEqual(selector.select([steady, late])["wind_adjustment_factor"], 0.01)

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

    def test_ellipse_reference_must_not_depend_on_the_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            self._write_reports(directory)
            path = directory / selector.report_name(0.2, 0.5)
            payload = json.loads(path.read_text(encoding="utf-8"))
            for row in payload["results"][0]["trajectory"]:
                row["ellipse_reference"]["growth_intersection_cells"] = 9
            payload["growth_gate"] = evaluator.growth_gate(payload)
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(selector.GateInputError, "ellipse"):
                self._summary(directory)

    def _main_inputs(self, directory, *, test_cases_loaded=False, coverage_weather=None):
        """A manifest (TRAIN cases plus one VALIDATION case), weather file, coverage report
        and 17 reports that name their hashes."""
        manifest = directory / "manifest.json"
        cases = [{"scenario_id": name, "split": "train"} for name in CASE_IDS]
        cases.append({"scenario_id": "held-out", "split": "validation"})
        manifest.write_text(json.dumps({"test_cases_loaded": test_cases_loaded, "cases": cases}),
                            encoding="utf-8")
        weather = directory / "weather.json"
        weather.write_text("{}", encoding="utf-8")
        manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
        weather_sha = hashlib.sha256(weather.read_bytes()).hexdigest()
        coverage = directory / "coverage.json"
        coverage.write_text(json.dumps({"weather_file_sha256": coverage_weather or weather_sha,
                                        "episode_manifest_sha256": manifest_sha}), encoding="utf-8")
        reports = directory / "reports"
        reports.mkdir()
        for waf, ros in selector.CANDIDATES:
            payload = _payload(waf, ros, hits=(30, 30) if (waf, ros) == (0.05, 1.0) else (5, 5),
                               manifest_sha=manifest_sha, weather_sha=weather_sha)
            (reports / selector.report_name(waf, ros)).write_text(json.dumps(payload), encoding="utf-8")
        return mock.patch.multiple(selector, MANIFEST=manifest, WEATHER=weather,
                                   WEATHER_COVERAGE=coverage), reports

    def test_main_selects_from_the_manifest_train_cases_and_writes_the_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            patched, reports = self._main_inputs(directory)
            out = directory / "summary.json"
            with patched, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(selector.main(["--reports-dir", str(reports), "--out", str(out)]), 0)
            summary = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(summary["gate_status"], "PASS")
            self.assertEqual(summary["expected_scenarios"], len(CASE_IDS))
            self.assertEqual(summary["selected"]["wind_adjustment_factor"], 0.05)

    def test_main_refuses_a_test_manifest_and_inputs_unlike_the_coverage_report(self):
        for options, message in ((dict(test_cases_loaded=True), "TEST"),
                                 (dict(coverage_weather="0" * 64), "coverage")):
            with self.subTest(**options), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                patched, reports = self._main_inputs(directory, **options)
                stderr = io.StringIO()
                with patched, contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                    selector.main(["--reports-dir", str(reports),
                                   "--out", str(directory / "summary.json")])
                self.assertIn(message, stderr.getvalue())

    def test_main_refuses_to_overwrite_and_reports_the_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "summary.json"
            out.write_text("{}", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                selector.main(["--reports-dir", tmp, "--out", str(out)])
            self.assertIn("exists", stderr.getvalue())


FREEZE_SHA = "f" * 64
FREEZE = {
    "frozen_params": {
        "wind_adjustment_factor": 0.05,
        "internal_update_minutes": 5,
        "active_cell_lifetime_minutes": 90,
        "ros_multiplier": 1.0,
        "fireline_attenuation": "per_minute",
        "spread_aggregation": "last_write",
    },
    "weather_sha256": WEATHER_SHA,
    "manifest_sha256": MANIFEST_SHA,
}


def _validation_payload(**kwargs):
    payload = _payload(split="validation", frozen_sha=FREEZE_SHA, **kwargs)
    payload["finished_utc"] = "2026-11-09T20:14:32+00:00"
    methods = {name: {"mean_iou": 0.5, "mean_absolute_area_error_ha": 10.0}
               for name in ("simfire_noop", "persistence", "ellipse_reference")}
    payload["summary"] = {"methods": methods}
    payload["strict_screen"] = {"pass": False}
    return payload


class ValidationSummaryTests(unittest.TestCase):
    def _summarize(self, payload, freeze=FREEZE):
        return validation_summary.summarize_validation(payload, freeze, freeze_sha256=FREEZE_SHA)

    def test_summary_restates_the_report_without_rescoring(self):
        summary = self._summarize(_validation_payload())
        gate = summary["growth_gate"]
        self.assertTrue(gate["pass"])
        self.assertAlmostEqual(gate["simfire_mean_case_growth_iou"], 0.6)
        self.assertAlmostEqual(gate["ellipse_mean_case_growth_iou"], 0.25)
        self.assertEqual((gate["growing_cases"], gate["non_growing_cases"]), (2, 1))
        self.assertEqual(summary["non_growing_overgrowth"]["cases"], [
            {"scenario_id": "stalled-c", "simfire_growth_cells_48h": 7, "observed_growth_cells_48h": 0}])
        self.assertAlmostEqual(summary["non_growing_overgrowth"]["mean_overgrowth_ha_48h"], 7 * HA)
        self.assertEqual([case["growing"] for case in summary["case_growth_iou"]], [True, True, False])
        self.assertEqual(summary["scored_utc"], "2026-11-09T20:14:32+00:00")
        self.assertIs(summary["used_for_selection"], False)
        self.assertEqual(summary["freeze_record_sha256"], FREEZE_SHA)

    def test_report_that_does_not_match_the_freeze_record_is_refused(self):
        cases = {
            "frozen_params_sha256": _validation_payload(),
            "split": _payload(frozen_sha=FREEZE_SHA),
            "wind_adjustment_factor": _validation_payload(waf=0.2),
            "manifest_sha256": _validation_payload(manifest_sha="x" * 64),
        }
        cases["frozen_params_sha256"]["configuration"]["frozen_params_sha256"] = "0" * 64
        for field, payload in cases.items():
            with self.subTest(field=field), self.assertRaisesRegex(selector.GateInputError, field):
                self._summarize(payload)
        with self.assertRaisesRegex(selector.GateInputError, "weather"):
            self._summarize(_validation_payload(weather_sha="x" * 64))
        with self.assertRaisesRegex(selector.GateInputError, "not complete"):
            self._summarize(_validation_payload(status="running"))
        other_params = dict(FREEZE, frozen_params=dict(FREEZE["frozen_params"], spread_aggregation="max"))
        with self.assertRaisesRegex(selector.GateInputError, "simulator parameters"):
            self._summarize(_validation_payload(), other_params)


class CommittedStageOneRecordTests(unittest.TestCase):
    """The committed freeze record, allowlist and summaries must agree with each other."""

    def setUp(self):
        root = selector.ROOT
        self.freeze_path = root / "configs/frozen/feds-simfire-growth-gate-freeze-v1.json"
        self.gate_path = root / "reports/real-fire-data/feds-simfire-train-growth-gate-v1.json"
        self.validation_path = root / "reports/real-fire-data/feds-simfire-validation-growth-gate-v1.json"
        self.freeze = json.loads(self.freeze_path.read_text(encoding="utf-8"))
        self.gate = json.loads(self.gate_path.read_text(encoding="utf-8"))
        self.validation = json.loads(self.validation_path.read_text(encoding="utf-8"))

    def test_freeze_record_states_the_candidate_the_gate_summary_selected(self):
        chosen = self.gate["selected"]
        self.assertEqual(self.gate["gate_status"], "PASS")
        self.assertEqual(self.freeze["gate_status"], "PASS")
        self.assertEqual(self.freeze["selected_on_split"], "train")
        self.assertEqual(self.freeze["frozen_params"], selector._simfire_params(
            chosen["wind_adjustment_factor"], chosen["ros_multiplier"]))
        self.assertEqual(self.freeze["gate_report_sha256"], evaluator.sha256_file(self.gate_path))
        for key in ("weather_sha256", "manifest_sha256"):
            self.assertEqual(self.freeze[key], self.gate[key])
        stated = self.freeze["selected_candidate"]
        for key in ("simfire_mean_case_growth_iou", "ellipse_mean_case_growth_iou"):
            self.assertAlmostEqual(stated[key], chosen[key], places=4)
        self.assertEqual(stated["local_full_report_sha256"], chosen["local_full_report_sha256"])
        self.assertEqual(
            [(item["wind_adjustment_factor"], item["ros_multiplier"], item["growth_gate_pass"])
             for item in self.freeze["candidates"]],
            [(item["wind_adjustment_factor"], item["ros_multiplier"], item["growth_gate_pass"])
             for item in self.gate["candidates"]])

    def test_gate_summary_selection_follows_from_its_own_candidates(self):
        chosen = selector.select(self.gate["candidates"])
        self.assertEqual(chosen, self.gate["selected"])
        self.assertEqual([(c["wind_adjustment_factor"], c["ros_multiplier"])
                          for c in self.gate["candidates"]], list(selector.CANDIDATES))

    def test_validation_summary_was_scored_under_the_committed_freeze_record(self):
        digest = evaluator.sha256_file(self.freeze_path)
        self.assertEqual(self.validation["freeze_record_sha256"], digest)
        self.assertEqual(self.validation["simfire_params"], self.freeze["frozen_params"])
        for key in ("weather_sha256", "manifest_sha256"):
            self.assertEqual(self.validation[key], self.freeze[key])
        self.assertIs(self.validation["used_for_selection"], False)


if __name__ == "__main__":
    unittest.main()
