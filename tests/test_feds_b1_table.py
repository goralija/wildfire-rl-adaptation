import unittest

try:
    import numpy as np
except ImportError:
    raise unittest.SkipTest("optional NumPy dependency is not installed")

from wildfire_rl.feds_b1 import action_sequences, audit_reference, policy_sequence


class B1TableTests(unittest.TestCase):
    def test_exactly_33_sequences_cover_each_time_and_direction_once(self):
        seq = action_sequences()
        self.assertEqual(len(seq), 33)
        self.assertEqual(len(set(seq)), 33)
        self.assertEqual(seq[0], (0, 0, 0, 0))
        self.assertTrue(all(len(s) == 4 and sum(a != 0 for a in s) <= 1 for s in seq))
        self.assertEqual({(i, a) for s in seq for i, a in enumerate(s) if a},
                         {(i, a) for i in range(4) for a in range(1, 9)})

    def test_policy_uses_only_current_observation_and_waits_with_budget(self):
        obs = [{"time": [i / 4]} for i in range(4)]
        masks = [[True] * 9 for _ in range(4)]
        calls = []

        def policy(observation, mask):
            calls.append(observation["time"][0])
            return 3 if observation["time"][0] >= .5 else 0

        self.assertEqual(policy_sequence(policy, obs, masks), (0, 0, 3, 0))
        self.assertEqual(calls, [0, .25, .5])

    def test_masked_choice_becomes_noop_and_does_not_consume_budget(self):
        masks = np.ones((4, 9), dtype=bool)
        masks[0, 3] = False
        self.assertEqual(policy_sequence(lambda o, m: 3, [{}] * 4, masks), (0, 3, 0, 0))

    def test_reference_requires_exact_sequence_and_damage_match(self):
        rows = [{"effective_actions": [0, 2, 0, 0], "raw_damage_cells": 10}]
        self.assertTrue(audit_reference(rows, [0, 2, 0, 0], 10))
        with self.assertRaises(ValueError):
            audit_reference(rows, [0, 2, 0, 0], 11)
        with self.assertRaises(ValueError):
            audit_reference(rows, [2, 0, 0, 0], 10)

    def test_repeated_effective_sequences_must_have_identical_damage(self):
        rows = [{"effective_actions": [0, 0, 0, 0], "raw_damage_cells": n}
                for n in (1, 2)]
        with self.assertRaises(ValueError):
            audit_reference(rows, [0, 0, 0, 0], 1)
