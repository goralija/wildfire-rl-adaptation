"""Information parity and pilot guards, independent of physical-validity claims."""
import unittest

try:
    import gymnasium  # noqa: F401
    import numpy as np
    import scipy  # noqa: F401
except ImportError as exc:
    raise unittest.SkipTest("optional CA dependencies: %s" % exc)

from wildfire_rl.synthetic_ca import Landscape, SpreadParams, Weather, WeatherSeries
from wildfire_rl.synthetic_env import (
    ACTIONS_PER_UNIT, DOZER, EpisodeSpec, HAND_CREW, MAX_UNITS,
    SyntheticSuppressionEnv,
)
from wildfire_rl.synthetic_heuristics import HEURISTICS
from wildfire_rl.ca_controlled import (
    CAObservationV2, OBSERVATION_VERSION, observed_policy, observation_view,
)


def fixture():
    fuel = np.full((32, 32), 8)
    fuel[2, 2:5] = [13, 98, 91]
    front = np.zeros(fuel.shape, dtype=bool)
    front[16, 16] = True
    return EpisodeSpec(
        landscape=Landscape(fuel, np.zeros(fuel.shape)),
        weather=WeatherSeries([Weather(0.1, 0, 0.1, 10),
                               Weather(4, 180, 0.2, 11),
                               Weather(6, 270, 0.05, 12)]),
        scar=np.zeros_like(front), front=front,
        units=[(DOZER, 0), (HAND_CREW, 60)], horizon=2, seed=901,
        params=SpreadParams(spot_rate=0),
    )


class InformationContractTest(unittest.TestCase):
    def env(self):
        return CAObservationV2(SyntheticSuppressionEnv(map_shape=(32, 32)))

    def test_native_categories_and_version_distinguish_urban_water_and_13(self):
        env = self.env()
        obs, info = env.reset(options={"episode_spec": fixture()})
        self.assertEqual(info["observation_version"], OBSERVATION_VERSION)
        self.assertTrue(env.observation_space.contains(obs))
        self.assertEqual(obs["native"].shape, (21, 32, 32))
        self.assertEqual(obs["native"][17, 2, 2], 1)  # fuel 13
        self.assertEqual(obs["native"][18, 2, 3], 1)  # water is nonburnable
        self.assertEqual(obs["native"][3, 2, 4], 1)   # urban burns in this CA
        self.assertEqual(obs["native"][18, 2, 4], 0)

    def test_current_forcing_is_shared_but_no_future_or_noop_is_available(self):
        env = self.env()
        obs, _ = env.reset(options={"episode_spec": fixture()})
        np.testing.assert_allclose(obs["forcing"], [0.1, 0, 0.1, 10])
        view = observation_view(obs, env.action_masks())
        self.assertAlmostEqual(view.spec_now.weather.at(0).wind_midflame_m_s, 0.1)
        with self.assertRaises(IndexError):
            view.spec_now.weather.at(1)
        self.assertFalse(hasattr(view, "noop_final"))
        self.assertFalse(hasattr(view, "noop_footprint"))
        obs, _, _, _, _ = env.step(np.zeros(MAX_UNITS, dtype=int))
        np.testing.assert_allclose(obs["forcing"], [4, 180, 0.2, 11])

    def test_existing_rules_produce_identical_actions_from_observation_only(self):
        env = self.env()
        obs, _ = env.reset(options={"episode_spec": fixture()})
        for decision in range(2):
            for name, rule in HEURISTICS.items():
                actual = observed_policy(name)(obs, env.action_masks())
                np.testing.assert_array_equal(actual, rule(env.unwrapped))
            obs, _, _, _, _ = env.step(np.zeros(MAX_UNITS, dtype=int))

    def test_loss_exhausts_units_without_ending_fire_or_removing_noop(self):
        env = self.env()
        env.reset(options={"episode_spec": fixture()})
        for unit in env.unwrapped.units:
            unit.active, unit.lost = False, True
        masks = env.action_masks().reshape(MAX_UNITS, ACTIONS_PER_UNIT)
        self.assertTrue(masks[:, 0].all())
        self.assertFalse(masks[:, 1:].any())
        _, _, terminated, truncated, _ = env.step(np.zeros(MAX_UNITS, dtype=int))
        self.assertFalse(terminated or truncated)
        _, _, terminated, _, _ = env.step(np.zeros(MAX_UNITS, dtype=int))
        self.assertTrue(terminated)

    def test_wrapper_leaves_noop_dynamics_and_damage_unchanged(self):
        spec = fixture()
        old = SyntheticSuppressionEnv(map_shape=(32, 32))
        new = self.env()
        old.reset(options={"episode_spec": spec})
        new.reset(options={"episode_spec": spec})
        done = False
        while not done:
            a = old.step(np.zeros(MAX_UNITS, dtype=int))
            b = new.step(np.zeros(MAX_UNITS, dtype=int))
            self.assertEqual(a[1:4], b[1:4])
            np.testing.assert_array_equal(old.fire.ever_burned, new.unwrapped.fire.ever_burned)
            done = b[2]
        self.assertEqual(old.summary(), new.unwrapped.summary())
