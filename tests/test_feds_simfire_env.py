import unittest
from types import SimpleNamespace

import numpy as np

try:
    from wildfire_rl.feds_simfire_env import (
        FedsSimFireEnv,
        build_action_mask,
        cumulative_burn_mask,
        fireline_points,
    )
except ImportError as exc:
    raise unittest.SkipTest("optional SimFire/Gymnasium dependencies are not installed: %s" % exc)


class FedsSimFireEnvironmentTests(unittest.TestCase):
    def test_sector_line_is_fixed_length_and_avoids_nonfuel_states(self):
        fire_map = np.zeros((15, 15), dtype=np.uint8)
        front = np.zeros_like(fire_map, dtype=bool)
        front[7, 7] = True
        fire_map[7, 7] = 1
        fire_map[7, 13] = 2

        points = fireline_points(fire_map, front, sector=0, radius=6, half_length=3)

        self.assertEqual(points, ((13, 4), (13, 5), (13, 6), (13, 8), (13, 9), (13, 10)))
        self.assertNotIn((13, 7), points)

    def test_noop_remains_the_only_legal_action_when_budget_is_empty(self):
        fire_map = np.zeros((15, 15), dtype=np.uint8)
        fire_map[7, 7] = 1
        front = fire_map == 1

        mask = build_action_mask(fire_map, front, remaining_budget=0)

        self.assertTrue(mask[0])
        self.assertEqual(np.flatnonzero(mask).tolist(), [0])

    def test_cumulative_damage_survives_fireline_overwrite(self):
        previous = np.zeros((3, 3), dtype=bool)
        previous[1, 1] = True
        fire_map = np.zeros((3, 3), dtype=np.uint8)
        fire_map[1, 1] = 3
        fire_map[1, 2] = 1

        cumulative = cumulative_burn_mask(previous, fire_map)

        self.assertTrue(cumulative[1, 1])
        self.assertTrue(cumulative[1, 2])
        self.assertEqual(int(cumulative.sum()), 2)

    def test_budget_exhaustion_and_fire_extinction_do_not_shorten_horizon(self):
        class FakeSimulation:
            def __init__(self):
                self.fire_map = np.zeros((15, 15), dtype=np.uint8)
                self.fire_map[7, 7] = 1
                self.fire_manager = SimpleNamespace(
                    U=np.zeros((1, 1)), U_dir=np.zeros((1, 1)), sprites=[object()],
                    environment=SimpleNamespace(M_f=None)
                )
                self.run_calls = 0

            def run(self, _duration):
                self.run_calls += 1
                self.fire_map[7, 7] = 2
                return self.fire_map, False

            def update_mitigation(self, _points):
                raise AssertionError("No-op must not place a control line")

        env = object.__new__(FedsSimFireEnv)
        env.action_space = SimpleNamespace(contains=lambda action: action == 0)
        env.scenario_id = "train-fixture"
        env._done = False
        env.remaining_budget = 0
        env.initial_budget = 0
        env.max_budget = 4
        env.decision_index = 0
        env.horizon_steps = 4
        env.simulation_active = True
        env.simulation = FakeSimulation()
        env.cumulative_burned = np.zeros((15, 15), dtype=bool)
        env.forcing = [
            {"wind_speed_midflame_ft_per_min_proxy": 1.0,
             "wind_direction_degrees_clockwise_north_to": 90.0,
             "fuel_moisture_fraction_proxy": 0.05}
        ] * 4
        env._observation = lambda: np.asarray([env.decision_index], dtype=np.float32)

        done_flags = []
        for _ in range(4):
            _observation, _reward, terminated, truncated, _info = env.step(0)
            done_flags.append(terminated or truncated)

        self.assertEqual(done_flags, [False, False, False, True])
        self.assertEqual(env.simulation.run_calls, 1)
        self.assertTrue(env.cumulative_burned[7, 7])


if __name__ == "__main__":
    unittest.main()
