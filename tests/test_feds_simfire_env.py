import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest("optional NumPy dependency is not installed: %s" % exc)

try:
    from wildfire_rl.feds_simfire_env import (
        LINE_LENGTH_M,
        SECTOR_DIRECTIONS,
        FedsSimFireEnv,
        build_action_mask,
        cumulative_burn_mask,
        fireline_points,
        front_edge_line_points,
        line_length_m,
        sector_line_cells,
    )
    from wildfire_rl.feds_simfire_setup import SimFireParams
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

    def test_reset_options_pin_scenario_and_budget_for_paired_evaluation(self):
        env = object.__new__(FedsSimFireEnv)
        env.cases = {"a": {}, "b": {}}
        env.scenario_ids = ("a", "b")
        env.budgets = (2,)
        env.max_budget = 4
        env.split = "validation"
        env.horizon_steps = 4
        loaded = []

        def fake_load(scenario_id):
            loaded.append(scenario_id)
            env.simulation = SimpleNamespace(fire_map=np.zeros((16, 16), dtype=np.uint8))
            env.cumulative_burned = np.zeros((16, 16), dtype=bool)
            env.fuel = np.zeros((16, 16), dtype=np.uint8)
            env.forcing = [{"wind_speed_midflame_ft_per_min_proxy": 0.0,
                            "wind_direction_degrees_clockwise_north_to": 0.0,
                            "fuel_moisture_fraction_proxy": 0.1}] * 4

        env._load_episode = fake_load
        env.block_count = 16
        observation, info = env.reset(seed=1, options={"scenario_id": "b", "budget": 4})

        self.assertEqual(loaded, ["b"])
        self.assertEqual((info["scenario_id"], info["budget"], info["split"]), ("b", 4, "validation"))
        self.assertEqual(env.remaining_budget, 4)
        self.assertAlmostEqual(float(observation["budget"][0]), 1.0)
        with self.assertRaises(ValueError):
            env.reset(options={"budget": 5})
        with self.assertRaises(ValueError):
            env.reset(options={"scenario_id": "test-case"})


def _single_front(size=41):
    fire_map = np.zeros((size, size), dtype=np.uint8)
    fire_map[size // 2, size // 2] = 1
    return fire_map, fire_map == 1


class LineGeometryTests(unittest.TestCase):
    def test_every_sector_line_is_four_connected(self):
        fire_map, front = _single_front()
        for sector in range(8):
            for points in (sector_line_cells(20, 20, sector),
                           front_edge_line_points(fire_map, front, sector),
                           fireline_points(fire_map, front, sector)):
                with self.subTest(sector=sector, points=points):
                    self.assertGreaterEqual(len(points), 7)
                    for (x0, y0), (x1, y1) in zip(points, points[1:]):
                        self.assertEqual(abs(x1 - x0) + abs(y1 - y0), 1)

    def test_every_sector_line_is_one_crew_shift_long(self):
        for sector in range(8):
            with self.subTest(sector=sector):
                self.assertAlmostEqual(line_length_m(sector), LINE_LENGTH_M, delta=0.02 * LINE_LENGTH_M)
        self.assertEqual(len(sector_line_cells(0, 0, 0)), 7)
        self.assertEqual(len(sector_line_cells(0, 0, 1)), 9)

    def test_diagonal_corner_cells_sit_on_the_side_away_from_the_fire(self):
        fire_map, front = _single_front()
        for sector in (1, 3, 5, 7):
            dx, dy = (int(value) for value in SECTOR_DIRECTIONS[sector])
            projections = {(x - 20) * dx + (y - 20) * dy
                           for x, y in front_edge_line_points(fire_map, front, sector)}
            with self.subTest(sector=sector):
                self.assertEqual(projections, {4, 5})

    def test_step_reports_one_unit_and_the_line_length(self):
        env = object.__new__(FedsSimFireEnv)
        env.action_space = SimpleNamespace(contains=lambda action: 0 <= action < 9)
        env.scenario_id = "train-fixture"
        env._done = False
        env.remaining_budget = env.initial_budget = 2
        env.max_budget = 4
        env.decision_index = 0
        env.horizon_steps = 4
        env.line_placement = "front_edge"
        env.simulation_active = False
        fire_map, _front = _single_front()
        placed = []
        env.simulation = SimpleNamespace(fire_map=fire_map, update_mitigation=placed.extend)
        env.cumulative_burned = fire_map > 0
        env._observation = lambda: None
        _obs, _reward, _terminated, _truncated, info = env.step(2)
        self.assertEqual((env.remaining_budget, info["line_cells_applied"], len(placed)), (1, 9, 9))
        self.assertAlmostEqual(info["line_length_m"], line_length_m(1))


def _forcing(values):
    return [{"wind_speed_midflame_ft_per_min_proxy": 100.0 * value,
             "wind_direction_degrees_clockwise_north_to": 10.0 * value,
             "fuel_moisture_fraction_proxy": 0.01 * value} for value in values]


def _bare_env(weather_observation=None):
    env = object.__new__(FedsSimFireEnv)
    if weather_observation is not None:
        env.weather_observation = weather_observation
    env.simulation = SimpleNamespace(fire_map=np.zeros((16, 16), dtype=np.uint8))
    env.cumulative_burned = np.zeros((16, 16), dtype=bool)
    env.fuel = np.zeros((16, 16), dtype=np.uint8)
    env.block_count = 16
    env.horizon_steps = 4
    env.initial_budget = env.remaining_budget = 0
    env.max_budget = 4
    env.forcing = _forcing((1, 2, 3, 4))
    return env


def _expected_weather(segment):
    current = _forcing((1, 2, 3, 4))[segment]
    direction = np.deg2rad(current["wind_direction_degrees_clockwise_north_to"])
    return np.asarray((current["wind_speed_midflame_ft_per_min_proxy"] / 3000.0, np.sin(direction),
                       np.cos(direction), current["fuel_moisture_fraction_proxy"] / 0.3), dtype=np.float32)


class WeatherObservationTests(unittest.TestCase):
    def test_default_observes_the_upcoming_segment(self):
        env = _bare_env()
        for decision in range(4):
            env.decision_index = decision
            np.testing.assert_allclose(env._observation()["weather"], _expected_weather(decision))

    def test_previous_option_never_shows_the_segment_about_to_run(self):
        env = _bare_env("previous")
        env.decision_index = 0
        # Decision 0 sees the initial condition the simulation was built with.
        np.testing.assert_allclose(env._observation()["weather"], _expected_weather(0))
        for decision in (1, 2, 3):
            env.decision_index = decision
            observed = env._observation()["weather"]
            with self.subTest(decision=decision):
                np.testing.assert_allclose(observed, _expected_weather(decision - 1))
                self.assertFalse(np.allclose(observed, _expected_weather(decision)))


class SplitGuardTests(unittest.TestCase):
    PARAMS = SimFireParams(wind_adjustment_factor=0.01)

    def test_test_split_is_refused(self):
        with self.assertRaisesRegex(ValueError, "TEST"):
            FedsSimFireEnv(sim_params=self.PARAMS, split="test")

    def test_validation_without_an_allowlisted_freeze_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "freeze.json"
            record.write_text('{"selected_on_split": "train"}', encoding="utf-8")
            allowlist = Path(directory) / "allowlist.json"
            allowlist.write_text('{"records": []}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "freeze record"):
                FedsSimFireEnv(sim_params=self.PARAMS, split="validation")
            with self.assertRaisesRegex(ValueError, "allowlist"):
                FedsSimFireEnv(sim_params=self.PARAMS, split="validation",
                               freeze_record=record, freeze_allowlist=allowlist)


if __name__ == "__main__":
    unittest.main()
