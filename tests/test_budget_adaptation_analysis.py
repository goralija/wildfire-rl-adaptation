import unittest

try:
    import numpy  # noqa: F401
except ImportError as exc:
    raise unittest.SkipTest("optional NumPy dependency is not installed: %s" % exc)

from scripts.analyze_budget_adaptation import contrasts


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


if __name__ == "__main__":
    unittest.main()
