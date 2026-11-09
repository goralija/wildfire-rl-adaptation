import unittest

try:
    import numpy  # noqa: F401
except ImportError as exc:
    raise unittest.SkipTest("optional NumPy dependency is not installed: %s" % exc)

from scripts.analyze_budget_adaptation import (
    T975,
    _bootstrap,
    _seed_t_interval,
    _two_level_bootstrap,
    contrasts,
    leave_largest_out,
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


if __name__ == "__main__":
    unittest.main()
