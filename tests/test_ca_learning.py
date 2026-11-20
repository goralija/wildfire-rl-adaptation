import json
from pathlib import Path
import unittest

try:
    import gymnasium
    import numpy as np
    import scipy
except ImportError as exc:
    raise unittest.SkipTest(str(exc))

from wildfire_rl.ca_learning import (
    encode_observation, encoded_space, learning_contrast, discounted_returns,
    validate_learning_plan,
)
from test_ca_controlled import fixture
from wildfire_rl.ca_controlled import CAObservationV2
from wildfire_rl.synthetic_env import SyntheticSuppressionEnv


class EncoderTest(unittest.TestCase):
    def observation(self):
        env = CAObservationV2(SyntheticSuppressionEnv(map_shape=(32, 32)))
        obs, _ = env.reset(options={"episode_spec": fixture()})
        env.step(np.zeros(4, int))
        return env, env._wrap(env.env._observation())

    def test_encoding_is_finite_versioned_and_uses_only_observation(self):
        env, obs = self.observation()
        a = encode_observation(obs)
        self.assertTrue(encoded_space().contains(a))
        before = {k: v.copy() for k, v in a.items()}
        env.env.noop_footprint[:] = ~env.env.noop_footprint
        env.env.spec_now.weather.steps[-1].wind_to_deg = 123
        b = encode_observation(obs)
        for key in before:
            np.testing.assert_array_equal(before[key], b[key])

    def test_native_local_fuel_categories_remain_distinct(self):
        _, obs = self.observation()
        obs["unit_state"][0, 1] = 1
        obs["unit_state"][0, 5:7] = [2, 2]
        a = encode_observation(obs)["tokens"]
        obs["native"][17, 2, 2] = 0
        obs["native"][18, 2, 2] = 1
        b = encode_observation(obs)["tokens"]
        self.assertFalse(np.array_equal(a, b))

    def test_discounted_return_stops_at_episode_boundary(self):
        np.testing.assert_allclose(discounted_returns([1, 2, 4], .5), [3, 4, 4])


class LearningStatisticsTest(unittest.TestCase):
    def test_training_seeds_are_averaged_before_case_cluster_bootstrap(self):
        # Shape: model seed x case x roster. Duplicating model seeds cannot inflate n.
        a = np.array([[[.2, .4], [.1, .3]], [[.4, .6], [.3, .5]]])
        b = np.zeros((2, 2))
        x = learning_contrast(a, b)
        y = learning_contrast(np.repeat(a, 3, axis=0), b)
        self.assertEqual(x["n_cases"], y["n_cases"])
        np.testing.assert_allclose([x["mean"]] + x["ci95"], [y["mean"]] + y["ci95"])
        self.assertEqual(x["n_cases"], 2)
        self.assertAlmostEqual(x["mean"], .35)

    def test_mismatched_case_roster_layout_is_rejected(self):
        with self.assertRaises(ValueError):
            learning_contrast(np.zeros((3, 16, 3)), np.zeros((48, 1)))

    def test_protocol_is_bounded_and_scenario_plan_hash_is_checked(self):
        root = Path(__file__).resolve().parents[1]
        p = json.loads((root / "configs/frozen/ca-learning-pilot-v1.json").read_text())
        validate_learning_plan(p, root)
        p["scenario_plan_sha256"] = "wrong"
        with self.assertRaises(ValueError):
            validate_learning_plan(p, root)

    def test_cached_training_reset_matches_fresh_v2_noop(self):
        from wildfire_rl.ca_learning import CATrainingEnv
        root = Path(__file__).resolve().parents[1]
        plan = json.loads((root / "configs/frozen/ca-controlled-pilot-v2.json").read_text())
        train = CATrainingEnv(plan)
        train.reset()
        spec = train.raw.env.spec_now
        fresh = CAObservationV2(SyntheticSuppressionEnv())
        fresh.reset(options={"episode_spec": spec})
        for _ in range(12):
            a = train.step(np.zeros(4, int))
            b = fresh.step(np.zeros(4, int))
            self.assertAlmostEqual(a[1], b[1])
            np.testing.assert_array_equal(train.raw.env.fire.ever_burned,
                                          fresh.env.fire.ever_burned)
            if a[2]:
                self.assertTrue(b[2])
                break
        self.assertEqual(train.training_manifest(), [(plan['case_seeds']['train'][0], 'B2')])
