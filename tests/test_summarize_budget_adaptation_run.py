"""Run record of the ADR-030 section 4 budget benchmark (stage 2 of TASK-026)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts import summarize_budget_adaptation_run as record

FREEZE_SHA = "f" * 64
SCENARIOS = ("fire-a", "fire-b")
BUDGETS = (0, 2)
# added burned ha at budget 2 per scenario; every policy equals no-op at budget 0
ADDED = {"noop": (100.0, 40.0), "random_legal": (90.0, 40.0), "downwind": (70.0, 30.0),
         "base-s11": (80.0, 40.0), "base-s12": (80.0, 40.0), "ft-b1-s11": (60.0, 20.0)}
ACTIONS = {"noop": (0, 0), "random_legal": (6, 5), "downwind": (1, 1),
           "base-s11": (7, 7), "base-s12": (7, 7), "ft-b1-s11": (3, 0)}
CHECKPOINTS = {name: "%064d" % index for index, name in enumerate(sorted(ADDED))
               if record.PPO_NAME.fullmatch(name)}


def _report(split, created="2026-11-10T12:00:00+00:00"):
    episodes = [
        {"policy": policy, "budget": budget, "scenario_id": scenario,
         "added_burned_ha": ADDED[policy][index] if budget else ADDED["noop"][index],
         "actions": list(ACTIONS[policy]) if budget else [0, 0],
         "lines_applied": sum(action > 0 for action in ACTIONS[policy]) if budget else 0}
        for policy in ADDED for budget in BUDGETS for index, scenario in enumerate(SCENARIOS)]
    return {
        "split": split, "test_cases_loaded": False, "params_file_sha256": FREEZE_SHA,
        "errors": [], "legacy_checkpoints": [], "created_utc": created, "runtime_minutes": 1.5,
        "sim_params": {"wind_adjustment_factor": 0.1}, "policy_settings": {"line_placement": "front_edge"},
        "checkpoint_receipts": {name: {"checkpoint_sha256": digest}
                                for name, digest in CHECKPOINTS.items()},
        "episodes": episodes,
    }


class BenchmarkBlockTests(unittest.TestCase):
    def _block(self, report, split="validation"):
        return record.benchmark_block(report, split=split, freeze_sha256=FREEZE_SHA,
                                      checkpoints=CHECKPOINTS)

    def test_family_means_average_over_seeds_and_scenarios(self):
        block = self._block(_report("validation"))
        self.assertEqual((block["scenario_count"], block["policies"], block["episodes"]), (2, 6, 24))
        self.assertTrue(block["budget0_all_policies_equal_noop"])
        self.assertAlmostEqual(block["noop_mean_added_ha"], 70.0)
        means = block["family_mean_delta_ha_vs_noop"]
        self.assertNotIn("noop", means)
        self.assertAlmostEqual(means["base"]["2"], -10.0)  # two seeds, each (-20, 0)
        self.assertAlmostEqual(means["ft-b1"]["2"], -30.0)
        self.assertAlmostEqual(means["downwind"]["2"], -20.0)
        self.assertAlmostEqual(means["base"]["0"], 0.0)

    def test_budget_zero_difference_is_reported(self):
        report = _report("validation")
        next(row for row in report["episodes"]
             if row["policy"] == "base-s11" and row["budget"] == 0)["added_burned_ha"] += 1.0
        self.assertFalse(self._block(report)["budget0_all_policies_equal_noop"])

    def test_refuses_reports_that_do_not_match_the_lock(self):
        cases = {
            "split": lambda r: r.update(split="train"),
            "test": lambda r: r.update(test_cases_loaded=True),
            "freeze": lambda r: r.update(params_file_sha256="0" * 64),
            "errors": lambda r: r.update(errors=[{"scenario_id": "fire-a"}]),
            "legacy": lambda r: r.update(legacy_checkpoints=["base-s11"]),
            "checkpoint": lambda r: r["checkpoint_receipts"]["base-s11"].update(checkpoint_sha256="x"),
            "grid": lambda r: r["episodes"].pop(),
        }
        for name, change in cases.items():
            report = _report("validation")
            change(report)
            with self.subTest(name), self.assertRaises(record.RunRecordError):
                self._block(report)


class BehaviourBlockTests(unittest.TestCase):
    def test_groups_policies_with_identical_actions(self):
        block = record.behaviour_block(_report("validation"))
        self.assertEqual(block["ppo_policies"], 3)
        self.assertEqual(block["distinct_ppo_behaviours"], 2)
        self.assertEqual(block["identical_behaviour_groups"], [["base-s11", "base-s12"]])
        self.assertEqual(block["distinct_base_behaviours"], 1)
        self.assertEqual(block["policies_that_never_place_a_line"], [])
        self.assertEqual(block["base_policies"]["base-s11"], {
            "distinct_action_sequences": 1, "most_common_first_action": 7,
            "share_of_episodes_with_that_first_action": 1.0})

    def test_lists_policies_that_never_place_a_line(self):
        report = _report("validation")
        for row in report["episodes"]:
            if row["policy"] == "ft-b1-s11":
                row["lines_applied"] = 0
        self.assertEqual(record.behaviour_block(report)["policies_that_never_place_a_line"],
                         ["ft-b1-s11"])

    def test_budget_zero_episodes_are_ignored(self):
        report = _report("validation")
        for row in report["episodes"]:
            if row["budget"] == 0:
                row["actions"] = [8, 8]
        self.assertEqual(record.behaviour_block(report)["distinct_ppo_behaviours"], 2)


class BuildRecordTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.train = self._write("train.json", _report("train", "2026-11-10T10:00:00+00:00"))
        self.validation = self._write("validation.json", _report("validation"))
        for name, digest in CHECKPOINTS.items():
            self._write("runs/%s/training_manifest.json" % name, {
                "phase": "base", "budgets": [2], "seed": 11, "requested_steps": 64,
                "actual_steps": 64, "wall_clock_minutes": 2.0, "checkpoint_sha256": digest,
                "init_checkpoint_sha256": None, "params_file_sha256": FREEZE_SHA,
                "split": "train", "validation_or_test_cases_loaded": False})
        self.lock = {"created_utc": "2026-11-10T11:00:00+00:00", "freeze_record_sha256": FREEZE_SHA,
                     "checkpoint_sha256": CHECKPOINTS,
                     "train_benchmark": {"sha256": record.sha256_file(self.train)},
                     "best_heuristic_selection": {"best_heuristic": "downwind"}}
        self.analysis = {
            "source_split": "validation",
            "best_heuristic_selection": {"best_heuristic": "downwind",
                                         "source_report_sha256": record.sha256_file(self.train)},
            "contrasts": {"by_budget": {
                "0": {"frozen_base_minus_noop": {"seed_averaged_mean_delta_ha": 0.0}},
                "2": {"frozen_base_minus_noop": {"seed_averaged_mean_delta_ha": -10.0}}}}}

    def _write(self, name, payload):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _build(self, lock=None, analysis=None):
        return record.build_record(
            runs_dir=self.root / "runs", train_path=self.train, validation_path=self.validation,
            lock_path=self._write("lock.json", lock or self.lock),
            analysis_path=self._write("analysis.json", analysis or self.analysis),
            code_commits={"validation_benchmark": "abc1234"})

    def test_record_collates_training_and_both_benchmarks(self):
        built = self._build()
        self.assertEqual(built["training"]["models"], 3)
        self.assertEqual(built["training"]["total_decisions"], 192)
        self.assertAlmostEqual(built["training"]["total_wall_clock_minutes"], 6.0)
        self.assertEqual(built["lock"]["best_heuristic"], "downwind")
        self.assertEqual(built["code_commits"], {"validation_benchmark": "abc1234"})
        self.assertIs(built["test_cases_loaded"], False)
        for split, path in (("train", self.train), ("validation", self.validation)):
            self.assertEqual(built["benchmarks"][split]["local_full_report_sha256"],
                             record.sha256_file(path))

    def test_refuses_inputs_that_disagree(self):
        def changed(source, **updates):
            item = copy.deepcopy(source)
            item.update(updates)
            return item

        cases = {
            "train hash in lock": {"lock": changed(self.lock, train_benchmark={"sha256": "0" * 64})},
            "train hash in analysis": {"analysis": changed(self.analysis, best_heuristic_selection={
                "best_heuristic": "downwind", "source_report_sha256": "0" * 64})},
            "best heuristic": {"lock": changed(self.lock, best_heuristic_selection={
                "best_heuristic": "advancing_front"})},
            "lock after validation": {"lock": changed(self.lock, created_utc="2026-11-10T13:00:00+00:00")},
            # the report was written at 12:00 after a 1.5-minute run
            "lock during validation": {"lock": changed(self.lock, created_utc="2026-11-10T11:59:00+00:00")},
            "analysis of another report": {"analysis": changed(self.analysis, contrasts={"by_budget": {
                "2": {"frozen_base_minus_noop": {"seed_averaged_mean_delta_ha": -11.0}}}})},
            "analysis of train": {"analysis": changed(self.analysis, source_split="train")},
        }
        for name, arguments in cases.items():
            with self.subTest(name), self.assertRaises(record.RunRecordError):
                self._build(**arguments)

    def test_refuses_a_receipt_for_another_checkpoint_or_split(self):
        path = self.root / "runs/base-s11/training_manifest.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        for updates in ({"checkpoint_sha256": "9" * 64}, {"split": "validation"},
                        {"params_file_sha256": "9" * 64},
                        {"validation_or_test_cases_loaded": True}):
            self._write("runs/base-s11/training_manifest.json", {**receipt, **updates})
            with self.subTest(updates=updates), self.assertRaises(record.RunRecordError):
                self._build()


class CommittedStageTwoRecordTests(unittest.TestCase):
    """The committed lock, analysis report and run record must agree with each other."""

    def setUp(self):
        self.freeze_path = record.ROOT / "configs/frozen/feds-simfire-growth-gate-freeze-v1.json"
        self.lock = json.loads(record.DEFAULT_LOCK.read_text(encoding="utf-8"))
        self.analysis = json.loads(record.DEFAULT_ANALYSIS.read_text(encoding="utf-8"))
        self.record = json.loads(record.DEFAULT_OUT.read_text(encoding="utf-8"))

    def test_everything_ran_under_the_committed_freeze_record(self):
        digest = record.sha256_file(self.freeze_path)
        freeze = json.loads(self.freeze_path.read_text(encoding="utf-8"))
        self.assertEqual(self.lock["freeze_record_sha256"], digest)
        self.assertEqual(self.record["freeze_record_sha256"], digest)
        for item in (self.lock, self.analysis, self.record):
            self.assertEqual(item["sim_params"], freeze["frozen_params"])
        self.assertEqual({run["params_file_sha256"] for run in self.record["training"]["runs"]},
                         {digest})

    def test_lock_predates_validation_and_fixes_the_analysed_heuristic(self):
        selection = self.analysis["best_heuristic_selection"]
        self.assertIs(self.lock["validation_benchmark_run"], False)
        self.assertLess(self.lock["created_utc"],
                        self.record["benchmarks"]["validation"]["created_utc"])
        self.assertEqual(self.record["code_commits"]["validation_benchmark"],
                         self.record["code_commits"]["validation_lock"])
        self.assertEqual(self.lock["best_heuristic_selection"]["best_heuristic"],
                         selection["best_heuristic"])
        self.assertEqual(selection["source_split"], "train")
        self.assertEqual(self.lock["train_benchmark"]["sha256"], selection["source_report_sha256"])
        self.assertEqual(self.record["benchmarks"]["train"]["local_full_report_sha256"],
                         selection["source_report_sha256"])
        self.assertEqual(self.record["lock"]["sha256"], record.sha256_file(record.DEFAULT_LOCK))
        self.assertEqual(self.record["analysis"]["sha256"], record.sha256_file(record.DEFAULT_ANALYSIS))

    def test_ten_seeds_and_the_six_primary_tests_are_complete(self):
        runs = self.record["training"]["runs"]
        self.assertEqual({run["run"]: run["checkpoint_sha256"] for run in runs},
                         self.lock["checkpoint_sha256"])
        self.assertEqual(sorted(run["seed"] for run in runs if run["phase"] == "base"),
                         list(range(11, 21)))
        self.assertEqual({(run["phase"], run["actual_steps"]) for run in runs},
                         {("base", 8064), ("finetune", 3024)})
        primary = self.analysis["contrasts"]["primary"]
        self.assertEqual(self.analysis["source_split"], "validation")
        self.assertEqual(self.analysis["contrasts"]["seeds"], list(range(11, 21)))
        self.assertTrue(primary["complete"])
        self.assertEqual(primary["family_size"], 6)
        self.assertEqual(sorted(primary["tests"]), sorted(
            "B%d_base_minus_%s" % (budget, name)
            for budget in (1, 2, 4) for name in ("random_legal", "best_heuristic")))

    def test_benchmarks_are_complete_and_open_no_test_case(self):
        for split, scenarios in (("train", 98), ("validation", 20)):
            block = self.record["benchmarks"][split]
            self.assertEqual((block["scenario_count"], block["policies"], block["errors"]),
                             (scenarios, 44, 0))
            self.assertEqual(block["episodes"], scenarios * 44 * 4)
            self.assertTrue(block["budget0_all_policies_equal_noop"])
        self.assertIs(self.record["test_cases_loaded"], False)
        self.assertEqual(self.analysis["line_burns_more_than_noop"]["no_line_episodes_differing_from_noop"], 0)


if __name__ == "__main__":
    unittest.main()
