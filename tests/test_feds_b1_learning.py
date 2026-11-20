import copy
import importlib.util
import unittest
from unittest import mock

try:
    import numpy as np
except ImportError:
    raise unittest.SkipTest("optional NumPy dependency is not installed")

from wildfire_rl.feds_b1 import action_sequences
from wildfire_rl.feds_b1_learning import (
    METHOD_NAMES, evaluate_fold, fit_q, observation_features, paired_interval,
)


def fixture(sign, key):
    observations = []
    for k in range(4):
        grid = np.zeros((4, 16, 16))
        grid[0, 8, 8] = 1
        grid[1, 8, 9 if sign > 0 else 7] = 1
        observations.append({"grid": grid.tolist(), "weather": [.1, sign, 0., .2],
                             "budget": [.25, .25], "time": [k / 4]})
    outcomes = []
    for seq in action_sequences():
        gain = 10 if seq[0] == (1 if sign > 0 else 2) else 0
        outcomes.append({"requested_actions": list(seq), "effective_actions": list(seq),
                         "raw_saved_cells": gain, "charged_saved_cells": gain,
                         "raw_damage_cells": 100-gain, "charged_damage_cells": 100-gain})
    return {"scenario_id": key, "observations": observations,
            "action_masks": [[True] * 9 for _ in range(4)], "outcomes": outcomes}


class B1LearningTests(unittest.TestCase):
    def test_feature_extraction_is_current_observation_only(self):
        obs = fixture(1, "a")["observations"][0]
        features = observation_features(obs)
        obs["future_weather"] = [999]
        obs["future_outcome"] = 1e9
        np.testing.assert_array_equal(features, observation_features(obs))
        self.assertTrue(np.isfinite(features).all())

    @unittest.skipUnless(importlib.util.find_spec("gymnasium"), "heuristics require optional Gymnasium")
    def test_heldout_labels_never_change_heldout_actions(self):
        training = [fixture(sign, str(i)) for i, sign in enumerate([1, -1] * 6)]
        held = fixture(1, "held")
        modified = copy.deepcopy(held)
        for row in modified["outcomes"]:
            row["raw_saved_cells"] += 500 if row["requested_actions"][0] == 8 else -500
        for method in METHOD_NAMES:
            with self.subTest(method=method):
                a = evaluate_fold(training, held, "raw", method)
                b = evaluate_fold(training, modified, "raw", method)
                self.assertEqual(a["actions"], b["actions"])

    def test_ridge_and_bc_learn_an_observable_direction_signal(self):
        training = [fixture(sign, str(i)) for i, sign in enumerate([1, -1] * 6)]
        for method in ("ridge_q_alpha_1", "nearest_neighbor_bc_5"):
            for sign, expected in ((1, 1), (-1, 2)):
                with self.subTest(method=method, sign=sign):
                    row = evaluate_fold(training, fixture(sign, "held"), "raw", method)
                    self.assertEqual(row["actions"], [expected, 0, 0, 0])
                    self.assertAlmostEqual(row["saved_ha"], 32.4)

    @unittest.skipUnless(importlib.util.find_spec("gymnasium"), "heuristics require optional Gymnasium")
    def test_no_policy_can_spend_more_than_one_line_or_ignore_the_mask(self):
        training = [fixture(sign, str(i)) for i, sign in enumerate([1, -1] * 4)]
        held = fixture(1, "held")
        held["action_masks"] = [[True] + [False] * 8 for _ in range(4)]
        for method in METHOD_NAMES:
            with self.subTest(method=method):
                self.assertEqual(evaluate_fold(training, held, "charged", method)["actions"],
                                 [0, 0, 0, 0])

    def test_fire_ids_must_be_disjoint(self):
        case = fixture(1, "same")
        with self.assertRaises(ValueError):
            evaluate_fold([case], case, "raw", "fixed_sequence")

    def test_learned_policies_can_wait_and_can_choose_no_intervention(self):
        training = [fixture(1, str(i)) for i in range(8)]
        held = fixture(1, "held")
        for case in training + [held]:
            for row in case["outcomes"]:
                row["raw_saved_cells"] = 20 if row["requested_actions"][2] == 1 else 0
        learned = [method for method in METHOD_NAMES if method not in ("advancing_front", "downwind")]
        for method in learned:
            with self.subTest(method=method, task="wait"):
                self.assertEqual(evaluate_fold(training, held, "raw", method)["actions"],
                                 [0, 0, 1, 0])
        for case in training + [held]:
            for row in case["outcomes"]:
                row["raw_saved_cells"] = -10 if any(row["requested_actions"]) else 0
        for method in learned:
            with self.subTest(method=method, task="no intervention"):
                self.assertEqual(evaluate_fold(training, held, "raw", method)["actions"],
                                 [0, 0, 0, 0])

    def test_paired_interval_is_reproducible_and_keeps_known_shifts(self):
        a = paired_interval([5.] * 8)
        self.assertEqual(a, paired_interval([5.] * 8))
        self.assertEqual(a, [5., 5.])

    def test_percentile_band_has_the_registered_95_percent_level(self):
        # For twenty discrete-uniform observations 0..19, the bootstrap mean has
        # mean 9.5 and SD sqrt(33.25/20) ~= 1.289; its central 95% band is ~[7,12].
        # A 90% or 99% level falls outside these tolerances.
        lower, upper = paired_interval(list(range(20)), samples=100000)
        self.assertAlmostEqual(lower, 7., delta=.15)
        self.assertAlmostEqual(upper, 12., delta=.15)

    def test_pessimistic_q_predictions_keep_the_known_zero_noop_option(self):
        class PessimisticModel:
            def predict(self, x):
                return np.tile([-10.] + [-1.] * 8, (len(np.atleast_2d(x)), 1))

        training = [fixture(1, str(i)) for i in range(8)]
        with mock.patch("wildfire_rl.feds_b1_learning.fit_q",
                        return_value=[PessimisticModel()] * 4):
            result = evaluate_fold(training, fixture(1, "held"), "raw", "ridge_q_alpha_1")
        self.assertEqual(result["actions"], [0, 0, 0, 0])

    def test_bellman_backup_cannot_value_optional_intervention_below_noop(self):
        targets = []

        class PessimisticModel:
            def __init__(self, x, y, alpha):
                targets.append(y[:, 0].copy())

            def predict(self, x):
                return np.tile([-10.] + [-1.] * 8, (len(np.atleast_2d(x)), 1))

        with mock.patch("wildfire_rl.feds_b1_learning.RidgeModel", PessimisticModel):
            fit_q(np.zeros((3, 4, 28)), np.zeros((3, 4, 9)),
                  np.ones((3, 4, 9), dtype=bool), "ridge_q_alpha_1")
        self.assertTrue(all(np.all(value >= 0) for value in targets))
