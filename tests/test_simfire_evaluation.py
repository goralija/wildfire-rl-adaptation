"""Pure protocol and metric tests for the non-training SimFire evaluator."""

from __future__ import annotations

import unittest

import numpy as np

from wildfire_rl.simfire_evaluation import (
    choose_front_edge_action,
    select_cohort_cases,
    summarize_paired_episodes,
    validate_protocol,
)


class SimFireEvaluationTests(unittest.TestCase):
    def test_frozen_contract_hashes_and_membership_validate(self):
        protocol = validate_protocol()
        self.assertEqual(len(protocol["membership"]["splits"]["train"]), 40)
        self.assertEqual(len(protocol["membership"]["splits"]["validation"]), 20)
        self.assertEqual(len(protocol["membership"]["splits"]["test"]), 19)
        self.assertNotIn(
            "fpa-fod-401411292-larch-creek",
            protocol["membership"]["splits"]["test"],
        )

    def test_front_edge_rule_uses_mask_and_stable_tie_break(self):
        observation = {"map": np.zeros((1, 4, 4), dtype=np.float32)}
        observation["map"][-1, 1, 1] = 1 / 5  # currently burning
        mask = np.zeros(17, dtype=bool)
        mask[0] = True
        mask[1 + 1 * 4 + 2] = True  # (1, 2)
        mask[1 + 2 * 4 + 1] = True  # (2, 1), same distance
        action = choose_front_edge_action(observation, mask, rows=4, columns=4)
        self.assertEqual(action, 1 + 1 * 4 + 2)

    def test_front_edge_rule_falls_back_to_noop_without_front_or_candidates(self):
        observation = {"map": np.zeros((1, 2, 2), dtype=np.float32)}
        mask = np.asarray([True, True, False, False, False], dtype=bool)
        self.assertEqual(choose_front_edge_action(observation, mask, rows=2, columns=2), 0)
        observation["map"][-1, 0, 0] = 2 / 5
        no_candidates = np.asarray([True, False, False, False, False], dtype=bool)
        self.assertEqual(choose_front_edge_action(observation, no_candidates, rows=2, columns=2), 0)

    def test_paired_result_averages_seeds_inside_incident(self):
        rows = []
        values = {
            "a": {"base_ppo": [10.0, 14.0], "fine_tuned_ppo": [8.0, 10.0], "no_op": [12.0, 16.0]},
            "b": {"base_ppo": [20.0, 24.0], "fine_tuned_ppo": [18.0, 20.0], "no_op": [22.0, 26.0]},
        }
        for scenario_id, policies in values.items():
            for policy, areas in policies.items():
                for seed, area in zip((1, 2), areas):
                    rows.append({
                        "scenario_id": scenario_id,
                        "seed": seed,
                        "policy": policy,
                        "cumulative_burned_area_ha": area,
                    })
        summary = summarize_paired_episodes(rows, resamples=200, seed=9)
        base_comparison = next(
            row for row in summary["paired_comparisons"] if row["comparator"] == "base_ppo"
        )
        self.assertEqual(base_comparison["incident_count"], 2)
        self.assertEqual(base_comparison["paired_mean_area_difference_ha"], 3.0)
        self.assertTrue(base_comparison["positive_means_fine_tuned_had_less_simulated_burned_area"])

    def test_explicit_test_membership_filters_the_opened_case_list(self):
        cohort = {"cases": [
            {"scenario_id": "kept", "split": "test"},
            {"scenario_id": "smoke-exposed", "split": "test"},
            {"scenario_id": "validation", "split": "validation"},
        ]}
        selected = select_cohort_cases(cohort, "test", ["kept"])
        self.assertEqual([row["scenario_id"] for row in selected["cases"]], ["kept"])
        self.assertEqual(len(cohort["cases"]), 3)
        with self.assertRaisesRegex(ValueError, "not an incident"):
            select_cohort_cases(cohort, "test", ["validation"])

    def test_paired_summary_rejects_missing_matched_episode(self):
        rows = [
            {"scenario_id": "a", "seed": 1, "policy": "base_ppo", "cumulative_burned_area_ha": 10.0},
            {"scenario_id": "a", "seed": 1, "policy": "fine_tuned_ppo", "cumulative_burned_area_ha": 8.0},
            {"scenario_id": "b", "seed": 1, "policy": "base_ppo", "cumulative_burned_area_ha": 10.0},
            {"scenario_id": "b", "seed": 1, "policy": "fine_tuned_ppo", "cumulative_burned_area_ha": 8.0},
            {"scenario_id": "b", "seed": 2, "policy": "base_ppo", "cumulative_burned_area_ha": 9.0},
        ]
        with self.assertRaisesRegex(ValueError, "matched episode"):
            summarize_paired_episodes(rows, resamples=100, seed=9)


if __name__ == "__main__":
    unittest.main()
