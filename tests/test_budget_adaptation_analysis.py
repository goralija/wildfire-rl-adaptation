import unittest

try:
    import numpy  # noqa: F401
except ImportError as exc:
    raise unittest.SkipTest("optional NumPy dependency is not installed: %s" % exc)

from scripts.analyze_budget_adaptation import (
    PRIMARY_FAMILY_SIZE,
    T975,
    _bootstrap,
    _seed_t_interval,
    _two_level_bootstrap,
    contrasts,
    holm_correction,
    leave_largest_out,
    main,
    select_best_train_heuristic,
    sign_flip_test,
)


def _row(policy, budget, scenario, ha):
    return {"policy": policy, "budget": budget, "scenario_id": scenario, "added_burned_ha": ha}


class BudgetAdaptationAnalysisTests(unittest.TestCase):
    def test_contrasts_pair_by_scenario_and_seed(self):
        rows = []
        for scenario, base_damage in (("a", 10.0), ("b", 20.0)):
            for budget in (2, 4):
                rows.append(_row("noop", budget, scenario, base_damage + 5))
                rows.append(_row("base-s1", budget, scenario, base_damage))
                rows.append(_row("ft-b2-s1", budget, scenario, base_damage - 1))
                rows.append(_row("ft-b4-s1", budget, scenario, base_damage - 3))
        result = contrasts({"episodes": rows})
        four = result["by_budget"]["4"]
        self.assertAlmostEqual(four["finetuned_minus_frozen_base"]["seed_averaged_mean_delta_ha"], -3.0)
        self.assertAlmostEqual(four["finetuned_minus_matched_control"]["seed_averaged_mean_delta_ha"], -2.0)
        self.assertAlmostEqual(four["frozen_base_minus_noop"]["seed_averaged_mean_delta_ha"], -5.0)
        self.assertEqual(four["finetuned_minus_frozen_base"]["scenarios_better"], 2)
        self.assertNotIn("finetuned_minus_matched_control", result["by_budget"]["2"])


class IntervalKnownAnswerTests(unittest.TestCase):
    def test_seed_t_interval(self):
        low, high = _seed_t_interval([1.0, 2.0, 3.0])
        half = 4.303 / 3 ** 0.5
        self.assertAlmostEqual(low, 2.0 - half)
        self.assertAlmostEqual(high, 2.0 + half)
        self.assertEqual(_seed_t_interval([0.0, 2.0]), [1.0 - 12.706, 1.0 + 12.706])
        self.assertIsNone(_seed_t_interval([1.0]))
        self.assertIsNotNone(_seed_t_interval(list(range(31))))

    def test_t_table_matches_scipy_when_available(self):
        try:
            from scipy import stats
        except ImportError:
            self.skipTest("SciPy is not installed")
        for df, value in T975.items():
            self.assertAlmostEqual(value, stats.t.ppf(0.975, df), places=3)

    def test_two_level_bootstrap_of_a_constant_is_that_constant(self):
        self.assertEqual(_two_level_bootstrap([[4.0, 4.0, 4.0], [4.0, 4.0, 4.0]]), [4.0, 4.0])

    def test_two_level_bootstrap_spans_every_resample_mean(self):
        # 2 seeds x 2 scenarios: 16 equally likely resamples, each with probability
        # 6.25% > 2.5%, so the percentiles are the smallest and largest resample means.
        self.assertEqual(_two_level_bootstrap([[0.0, 1.0], [2.0, 3.0]]), [0.0, 3.0])

    def test_two_level_bootstrap_carries_seed_variation_that_scenario_bootstrap_hides(self):
        matrix = [[0.0, 0.0, 0.0], [10.0, 10.0, 10.0]]
        self.assertEqual(_two_level_bootstrap(matrix), [0.0, 10.0])
        self.assertEqual(_bootstrap([5.0, 5.0, 5.0]), [5.0, 5.0])


class SignFlipTests(unittest.TestCase):
    def test_known_exact_p_values(self):
        self.assertEqual(sign_flip_test([1.0, 1.0, 1.0])["sign_flip_p_two_sided"], 0.25)
        self.assertEqual(sign_flip_test([1.0, -1.0])["sign_flip_p_two_sided"], 1.0)
        self.assertEqual(sign_flip_test([1, 2, 3, 4, 5, 6])["sign_flip_p_two_sided"], 2 / 64)
        # The observed |1 + 2 - 3| = 0 is reached or exceeded by every sign pattern.
        self.assertEqual(sign_flip_test([1.0, 2.0, -3.0])["sign_flip_p_two_sided"], 1.0)
        # [3, 1, 1]: |sum| >= 5 only for (+,+,+) and (-,-,-).
        self.assertEqual(sign_flip_test([3.0, 1.0, 1.0])["sign_flip_p_two_sided"], 0.25)

    def test_unchanged_scenarios_are_counted_and_dropped(self):
        result = sign_flip_test([0.0, 0.0, 2.0])
        self.assertEqual((result["scenarios_changed"], result["sign_flip_p_two_sided"]), (1, 1.0))
        self.assertEqual(sign_flip_test([0.0, 0.0])["scenarios_changed"], 0)

    def test_float_hectare_ties_count_as_ties(self):
        cell_ha = 3.24
        result = sign_flip_test([cell_ha * 3, -cell_ha, -cell_ha * 2])
        self.assertEqual(result["sign_flip_p_two_sided"], 1.0)

    def test_many_scenarios_fall_back_to_seeded_monte_carlo(self):
        result = sign_flip_test([1.0] * 30)
        self.assertEqual(result["sign_flip_method"], "monte_carlo")
        self.assertLess(result["sign_flip_p_two_sided"], 1e-3)
        self.assertEqual(result, sign_flip_test([1.0] * 30))

    def test_leave_largest_out(self):
        self.assertEqual(leave_largest_out([1.0, -10.0, 2.0], ["a", "b", "c"]),
                         {"leave_largest_out_mean_delta_ha": 1.5, "leave_largest_out_scenario": "b"})

    def test_heuristic_contrast_reports_exact_test_and_leave_largest_out(self):
        rows = []
        for scenario, delta in (("a", 0.0), ("b", -1.0), ("c", -2.0), ("d", -30.0)):
            rows.append(_row("noop", 1, scenario, 100.0))
            rows.append(_row("downwind", 1, scenario, 100.0 + delta))
        entry = contrasts({"episodes": rows})["by_budget"]["1"]["heuristics_minus_noop"]["downwind"]
        self.assertEqual(entry["scenarios_changed"], 3)
        self.assertEqual(entry["sign_flip_p_two_sided"], 0.25)
        self.assertEqual(entry["leave_largest_out_scenario"], "d")
        self.assertAlmostEqual(entry["leave_largest_out_mean_delta_ha"], -1.0)


CELL_HA = 3.24


def _report(rows, split="validation"):
    return {"split": split, "test_cases_loaded": False, "episodes": rows,
            "sim_params": {"wind_adjustment_factor": 0.2}, "line_placement": "front_edge",
            "weather_observation": "previous"}


def _train_heuristic_rows():
    """TRAIN: downwind is best at B=2, advancing_front at B=1, random_legal beats both."""
    deltas = {1: {"downwind": -1.0, "advancing_front": -5.0, "random_legal": -9.0},
              2: {"downwind": -4.0, "advancing_front": -2.0, "random_legal": -9.0}}
    rows = []
    for scenario in ("t1", "t2"):
        for budget, by_policy in deltas.items():
            rows.append(_row("noop", budget, scenario, 50.0))
            for policy, delta in by_policy.items():
                rows.append(_row(policy, budget, scenario, 50.0 + delta))
    return rows


SCENARIOS = ("a", "b", "c", "d", "e", "f")


def _validation_rows():
    """Two seeds, six scenarios, B in {1, 2, 4}. Base PPO beats random_legal by 2 ha in
    every scenario (seed 1: 1 ha, seed 2: 3 ha); downwind sits 10 ha above base PPO in
    scenario a only; advancing_front is the best heuristic on VALIDATION, so a selection
    made on this report would differ from the TRAIN one."""
    rows = []
    for budget in (1, 2, 4):
        for scenario in SCENARIOS:
            base = 100.0
            rows.append(_row("noop", budget, scenario, base + 50.0))
            rows.append(_row("base-s1", budget, scenario, base))
            rows.append(_row("base-s2", budget, scenario, base))
            rows.append(_row("random_legal", budget, scenario, base + 2.0))
            rows.append(_row("advancing_front", budget, scenario, base - 20.0))
            rows.append(_row("downwind", budget, scenario, base + (10.0 if scenario == "a" else 0.0)))
    # random_legal is one policy for every PPO seed; the two base seeds differ by 2 ha
    # (seed 1: 101 ha, seed 2: 99 ha) and average to 100 ha.
    for row in rows:
        if row["policy"] == "base-s1":
            row["added_burned_ha"] += 1.0
        elif row["policy"] == "base-s2":
            row["added_burned_ha"] -= 1.0
    return rows


class HolmTests(unittest.TestCase):
    def test_step_down_stops_at_the_first_non_rejection(self):
        result = holm_correction({"x": 0.045, "a": 0.01, "b": 0.04}, alpha=0.05)
        self.assertEqual([result[k]["holm_rank"] for k in ("a", "b", "x")], [1, 2, 3])
        for key, adjusted in (("a", 0.03), ("b", 0.08), ("x", 0.08)):
            self.assertAlmostEqual(result[key]["holm_adjusted_p"], adjusted)
        # 0.045 <= alpha on its own, but Holm stops after 0.04 > 0.05 / 2.
        self.assertEqual({k: v["holm_reject"] for k, v in result.items()},
                         {"a": True, "b": False, "x": False})

    def test_six_test_family_known_answer(self):
        p_values = {"B1_r": 0.004, "B2_r": 0.03, "B4_r": 0.008,
                    "B1_h": 0.5, "B2_h": 0.011, "B4_h": 0.02}
        result = holm_correction(p_values, alpha=0.05)
        expected = {"B1_r": (1, 0.024, True), "B4_r": (2, 0.04, True), "B2_h": (3, 0.044, True),
                    "B4_h": (4, 0.06, False), "B2_r": (5, 0.06, False), "B1_h": (6, 0.5, False)}
        for key, (rank, adjusted, reject) in expected.items():
            with self.subTest(key=key):
                self.assertEqual(result[key]["holm_rank"], rank)
                self.assertAlmostEqual(result[key]["holm_adjusted_p"], adjusted)
                self.assertEqual(result[key]["holm_reject"], reject)

    def test_missing_tests_do_not_shrink_the_family(self):
        result = holm_correction({"a": 0.02}, alpha=0.05, family_size=6)
        self.assertAlmostEqual(result["a"]["holm_adjusted_p"], 0.12)
        self.assertFalse(result["a"]["holm_reject"])


class BestTrainHeuristicTests(unittest.TestCase):
    def test_largest_mean_reduction_at_b2_excluding_noop_and_random(self):
        selection = select_best_train_heuristic(_report(_train_heuristic_rows(), split="train"))
        self.assertEqual(selection["best_heuristic"], "downwind")
        self.assertEqual(selection["candidates_mean_delta_ha_vs_noop"],
                         {"advancing_front": -2.0, "downwind": -4.0})
        self.assertEqual(selection["budget"], 2)

    def test_a_validation_report_is_never_used_for_selection(self):
        for split in ("validation", "test"):
            with self.subTest(split=split), self.assertRaisesRegex(ValueError, "TRAIN"):
                select_best_train_heuristic(_report(_train_heuristic_rows(), split=split))


class PrimaryFamilyTests(unittest.TestCase):
    def setUp(self):
        self.selection = select_best_train_heuristic(_report(_train_heuristic_rows(), split="train"))
        self.result = contrasts(_report(_validation_rows()), best_heuristic=self.selection)

    def test_six_primary_tests_with_the_train_selected_heuristic(self):
        primary = self.result["primary"]
        self.assertEqual(PRIMARY_FAMILY_SIZE, 6)
        self.assertEqual(primary["best_heuristic"], "downwind")  # not advancing_front
        self.assertTrue(primary["complete"])
        self.assertEqual(sorted(primary["tests"]), sorted(
            "B%d_base_minus_%s" % (budget, name) for budget in (1, 2, 4)
            for name in ("random_legal", "best_heuristic")))

    def test_known_answers_on_seed_averaged_scenario_deltas(self):
        tests = self.result["primary"]["tests"]
        random = tests["B2_base_minus_random_legal"]
        # Seed-averaged base is exactly 100 ha, random_legal 102 ha: -2 in all six.
        self.assertAlmostEqual(random["seed_averaged_mean_delta_ha"], -2.0)
        self.assertEqual(random["scenarios_changed"], 6)
        self.assertEqual(random["sign_flip_method"], "exact")
        self.assertAlmostEqual(random["sign_flip_p_two_sided"], 2 / 64)
        self.assertAlmostEqual(random["leave_largest_out_mean_delta_ha"], -2.0)
        self.assertEqual(random["per_seed_mean_delta_ha"], {"1": -1.0, "2": -3.0})
        low, high = random["two_level_bootstrap_95ci_ha"]
        self.assertLessEqual(low, -2.0)
        self.assertGreaterEqual(high, -2.0)
        heuristic = tests["B2_base_minus_best_heuristic"]
        # Base minus downwind is -10 in scenario a and 0 elsewhere.
        self.assertEqual(heuristic["scenarios_changed"], 1)
        self.assertAlmostEqual(heuristic["sign_flip_p_two_sided"], 1.0)
        self.assertEqual(heuristic["leave_largest_out_scenario"], "a")
        self.assertAlmostEqual(heuristic["leave_largest_out_mean_delta_ha"], 0.0)
        # Holm over six: three p = 1/32 (adjusted 6/32 > .05) and three p = 1.
        for key, entry in tests.items():
            with self.subTest(key=key):
                self.assertFalse(entry["holm_reject"])
        self.assertAlmostEqual(random["holm_adjusted_p"], 6 / 32)

    def test_noop_contrasts_are_labelled_sanity_checks(self):
        two = self.result["by_budget"]["2"]
        self.assertEqual(two["frozen_base_minus_noop"]["role"], "sanity_check")
        for name, entry in two["heuristics_minus_noop"].items():
            with self.subTest(name=name):
                self.assertEqual(entry["role"], "sanity_check")

    def test_without_a_selection_the_primary_family_is_not_reported(self):
        self.assertNotIn("primary", contrasts(_report(_validation_rows())))

    def test_cli_requires_a_train_report_and_refuses_a_validation_one(self):
        import contextlib
        import io
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "validation.json"
            report.write_text(json.dumps(_report(_validation_rows())), encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                main([str(report)])
            for split in ("validation",):
                wrong = Path(directory) / "wrong.json"
                wrong.write_text(json.dumps(_report(_train_heuristic_rows(), split=split)),
                                 encoding="utf-8")
                with contextlib.redirect_stderr(io.StringIO()) as err, \
                        self.assertRaises(SystemExit):
                    main([str(report), "--train-report", str(wrong)])
                self.assertIn("TRAIN", err.getvalue())
            train = Path(directory) / "train.json"
            train.write_text(json.dumps(_report(_train_heuristic_rows(), split="train")),
                             encoding="utf-8")
            out = Path(directory) / "out.json"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(report), "--train-report", str(train),
                                       "--out", str(out)]), 0)
            result = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(result["contrasts"]["primary"]["best_heuristic"], "downwind")
            self.assertEqual(result["best_heuristic_selection"]["source_split"], "train")
            self.assertEqual(len(result["best_heuristic_selection"]["source_report_sha256"]), 64)


class FineTuneInferenceTests(unittest.TestCase):
    def test_finetune_contrasts_carry_sign_flip_changed_count_and_leave_largest_out(self):
        rows = []
        for scenario, gain in zip(SCENARIOS, (1.0, 2.0, 3.0, 4.0, 5.0, 30.0)):
            for budget in (2, 4):
                rows.append(_row("noop", budget, scenario, 200.0))
                rows.append(_row("base-s1", budget, scenario, 100.0))
                rows.append(_row("ft-b2-s1", budget, scenario, 100.0))
                rows.append(_row("ft-b4-s1", budget, scenario, 100.0 - gain))
        four = contrasts(_report(rows))["by_budget"]["4"]
        for name in ("finetuned_minus_frozen_base", "finetuned_minus_matched_control"):
            entry = four[name]
            with self.subTest(name=name):
                self.assertEqual(entry["role"], "secondary")
                self.assertEqual(entry["scenarios_changed"], 6)
                self.assertAlmostEqual(entry["sign_flip_p_two_sided"], 2 / 64)
                self.assertEqual(entry["leave_largest_out_scenario"], "f")
                self.assertAlmostEqual(entry["leave_largest_out_mean_delta_ha"], -3.0)

    def test_seed_averaged_float_cancellation_counts_as_unchanged(self):
        # Three seeds whose cell deltas (+7, -2, -5) cancel; in hectares the mean is
        # about -1e-15, which must not count as a changed scenario.
        values = [CELL_HA * 7, -CELL_HA * 2, -CELL_HA * 5]
        mean = sum(values) / 3
        self.assertNotEqual(mean, 0.0)
        result = sign_flip_test([mean, -CELL_HA, -2 * CELL_HA])
        self.assertEqual(result["scenarios_changed"], 2)


if __name__ == "__main__":
    unittest.main()
