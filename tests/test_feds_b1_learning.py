import copy
import importlib.util
import unittest

try:
    import numpy as np
except ImportError:
    raise unittest.SkipTest("optional NumPy dependency is not installed")

from wildfire_rl.feds_b1 import action_sequences
from wildfire_rl.feds_b1_learning import (
    METHOD_NAMES, evaluate_fold, observation_features, paired_interval,
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

    def test_paired_interval_is_reproducible_and_keeps_known_shifts(self):
        a = paired_interval([5.] * 8)
        self.assertEqual(a, paired_interval([5.] * 8))
        self.assertEqual(a, [5., 5.])
