import unittest

try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest("optional NumPy dependency is not installed: %s" % exc)

try:
    from wildfire_rl.feds_heuristics import (
        advancing_front_policy,
        downwind_policy,
        make_heuristic,
        sector_for_vector,
    )
    from wildfire_rl.feds_simfire_env import FedsSimFireEnv, build_action_mask, front_edge_line_points
except ImportError as exc:
    raise unittest.SkipTest("optional SimFire/Gymnasium dependencies are not installed: %s" % exc)


def _observation(heading_degrees=90.0, grid=None):
    radians = np.deg2rad(heading_degrees)
    return {
        "grid": np.zeros((4, 16, 16), dtype=np.float32) if grid is None else grid,
        "budget": np.asarray((1.0, 1.0), dtype=np.float32),
        "weather": np.asarray((0.1, np.sin(radians), np.cos(radians), 0.2), dtype=np.float32),
        "time": np.asarray((0.0,), dtype=np.float32),
    }


class FedsHeuristicTests(unittest.TestCase):
    def test_sector_mapping_uses_image_rows_for_north_and_south(self):
        self.assertEqual(sector_for_vector(1.0, 0.0), 0)   # east
        self.assertEqual(sector_for_vector(0.0, 1.0), 2)   # south (row grows)
        self.assertEqual(sector_for_vector(0.0, -1.0), 6)  # north

    def test_downwind_policy_follows_the_observed_heading(self):
        mask = np.ones(9, dtype=bool)
        self.assertEqual(downwind_policy(_observation(90.0), mask), 1)   # east -> sector 0
        self.assertEqual(downwind_policy(_observation(0.0), mask), 7)    # north -> sector 6

    def test_heuristics_fall_back_to_noop_when_line_is_illegal(self):
        mask = np.zeros(9, dtype=bool)
        mask[0] = True
        for name in ("downwind", "advancing_front", "random_legal", "noop"):
            self.assertEqual(make_heuristic(name, seed=3)(_observation(), mask), 0)

    def test_advancing_front_points_from_burned_area_to_front(self):
        grid = np.zeros((4, 16, 16), dtype=np.float32)
        grid[0, 8, 4:9] = 1.0
        grid[1, 8, 9] = 1.0
        self.assertEqual(advancing_front_policy(_observation(0.0, grid), np.ones(9, dtype=bool)), 1)

    def test_front_edge_line_sits_beyond_the_leading_front_cell(self):
        fire_map = np.zeros((20, 20), dtype=np.uint8)
        front = np.zeros_like(fire_map, dtype=bool)
        front[10, 5] = front[10, 9] = True
        fire_map[front] = 1
        points = front_edge_line_points(fire_map, front, 0, standoff=2, half_length=3)
        self.assertEqual(points, tuple((11, row) for row in range(7, 14)))

    def test_front_edge_mask_keeps_noop_and_respects_budget(self):
        fire_map = np.zeros((20, 20), dtype=np.uint8)
        fire_map[10, 10] = 1
        front = fire_map == 1
        mask = build_action_mask(fire_map, front, 1, placement="front_edge")
        self.assertTrue(mask.all())
        empty = build_action_mask(fire_map, front, 0, placement="front_edge")
        self.assertEqual(np.flatnonzero(empty).tolist(), [0])

    def test_downwind_uses_the_weather_the_environment_chooses_to_show(self):
        from types import SimpleNamespace

        env = object.__new__(FedsSimFireEnv)
        env.simulation = SimpleNamespace(fire_map=np.zeros((16, 16), dtype=np.uint8))
        env.cumulative_burned = np.zeros((16, 16), dtype=bool)
        env.fuel = np.zeros((16, 16), dtype=np.uint8)
        env.block_count, env.horizon_steps, env.max_budget = 16, 4, 4
        env.initial_budget = env.remaining_budget = 1
        env.decision_index = 1
        env.forcing = [{"wind_speed_midflame_ft_per_min_proxy": 10.0,
                        "wind_direction_degrees_clockwise_north_to": heading,
                        "fuel_moisture_fraction_proxy": 0.05} for heading in (90.0, 0.0, 0.0, 0.0)]
        mask = np.ones(9, dtype=bool)
        self.assertEqual(downwind_policy(env._observation(), mask), 1)   # default, previous: east
        env.weather_observation = "upcoming_perfect_forecast"
        self.assertEqual(downwind_policy(env._observation(), mask), 7)   # ablation, upcoming: north


if __name__ == "__main__":
    unittest.main()
