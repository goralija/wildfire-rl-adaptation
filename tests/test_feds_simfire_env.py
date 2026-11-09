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
    from wildfire_rl.feds_simfire_setup import (
        WEATHER_OBSERVATIONS,
        SimFireParams,
        observed_weather_records,
    )
    from wildfire_rl.gridmet_weather import FEDS_TIME_REFERENCE, gridmet_proxy_to_simfire
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
            env._set_observed_weather(_weather(SHARED_DAYS))

        env._load_episode = fake_load
        env.weather_observation = "previous"
        env.sim_params = SimFireParams(wind_adjustment_factor=0.5)
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

    def _step_clipped(self, fire_map, sector):
        env = object.__new__(FedsSimFireEnv)
        env.action_space = SimpleNamespace(contains=lambda action: 0 <= action < 9)
        env.scenario_id = "train-fixture"
        env._done = False
        env.remaining_budget = env.initial_budget = 1
        env.max_budget = 4
        env.decision_index = 0
        env.horizon_steps = 4
        env.line_placement = "front_edge"
        env.simulation_active = False
        placed = []
        env.simulation = SimpleNamespace(fire_map=fire_map, update_mitigation=placed.extend)
        env.cumulative_burned = fire_map > 0
        env._observation = lambda: None
        return env.step(sector + 1)[4], placed

    def test_clipped_line_reports_the_length_actually_placed(self):
        nominal_cells = {0: 7, 1: 9}
        # A front cell one row from the top edge: the east line loses its northern
        # cells to the grid edge. One near the right edge: the south-east diagonal
        # loses its north-eastern cells.
        edge = np.zeros((41, 41), dtype=np.uint8)
        edge[1, 20] = 1
        right = np.zeros((41, 41), dtype=np.uint8)
        right[20, 38] = 1
        # A burned strip where the east line would run removes cells from inside.
        burned = np.zeros((41, 41), dtype=np.uint8)
        burned[20, 20] = 1
        burned[17:20, 22] = 2
        for name, fire_map, sector in (("edge-axis", edge, 0), ("edge-diagonal", right, 1),
                                       ("burned-axis", burned, 0)):
            info, placed = self._step_clipped(fire_map, sector)
            with self.subTest(case=name):
                self.assertGreater(len(placed), 0)
                self.assertLess(len(placed), nominal_cells[sector])
                self.assertEqual(info["line_cells_applied"], len(placed))
                self.assertAlmostEqual(
                    info["line_length_m"],
                    line_length_m(sector) * len(placed) / nominal_cells[sector])


def _record(label, value):
    return {"gridmet_daily_label_mst": label, "gridmet_values": {
        "vs": {"value": float(value)}, "th": {"value": 10.0 * value}, "fm100": {"value": float(value)},
    }}


def _weather(labels, pre_start_label="2018-07-22"):
    """Four segments with the given daily labels; values 1..4, pre-start value 9."""
    weather = {"segments": [dict(_record(label, index + 1), segment=str(index))
                            for index, label in enumerate(labels)]}
    if pre_start_label is not None:
        weather["pre_start"] = dict(_record(pre_start_label, 9), segment="pre_start")
    return weather


# Two 12h segments often share one gridMET day (244/396 TRAIN decisions in the
# ADR-029-era file), so "the previous segment" can be the upcoming day's forcing.
SHARED_DAYS = ("2018-07-23", "2018-07-23", "2018-07-24", "2018-07-24")
DISTINCT_DAYS = ("2018-07-23", "2018-07-24", "2018-07-25", "2018-07-26")


def _bare_env(weather_observation="previous", labels=SHARED_DAYS):
    env = object.__new__(FedsSimFireEnv)
    env.weather_observation = weather_observation
    env.sim_params = SimFireParams(wind_adjustment_factor=0.5)
    env.simulation = SimpleNamespace(fire_map=np.zeros((16, 16), dtype=np.uint8))
    env.cumulative_burned = np.zeros((16, 16), dtype=bool)
    env.fuel = np.zeros((16, 16), dtype=np.uint8)
    env.block_count = 16
    env.horizon_steps = 4
    env.initial_budget = env.remaining_budget = 0
    env.max_budget = 4
    env._set_observed_weather(_weather(labels))
    return env


def _expected_weather(record):
    current = gridmet_proxy_to_simfire(
        wind_speed_m_s=record["gridmet_values"]["vs"]["value"],
        wind_from_degrees=record["gridmet_values"]["th"]["value"],
        fm100_percent=record["gridmet_values"]["fm100"]["value"],
        wind_adjustment_factor=0.5,
    )
    direction = np.deg2rad(current["wind_direction_degrees_clockwise_north_to"])
    return np.asarray((min(current["wind_speed_midflame_ft_per_min_proxy"] / 3000.0, 1.0),
                       np.sin(direction), np.cos(direction),
                       min(current["fuel_moisture_fraction_proxy"] / 0.3, 1.0)), dtype=np.float32)


class WeatherObservationTests(unittest.TestCase):
    """ADR-030: the observed daily record is always strictly earlier than the upcoming
    segment's record; decision 0 observes the pre-start day."""

    def test_observed_record_is_strictly_earlier_than_the_upcoming_segment(self):
        expected = {SHARED_DAYS: ("2018-07-22", "2018-07-22", "2018-07-23", "2018-07-23"),
                    DISTINCT_DAYS: ("2018-07-22", "2018-07-23", "2018-07-24", "2018-07-25")}
        for labels, observed_labels in expected.items():
            weather = _weather(labels)
            observed = observed_weather_records(weather)
            with self.subTest(labels=labels):
                self.assertEqual(tuple(r["gridmet_daily_label_mst"] for r in observed), observed_labels)
                for decision, record in enumerate(observed):
                    self.assertLess(record["gridmet_daily_label_mst"],
                                    weather["segments"][decision]["gridmet_daily_label_mst"])
                    self.assertIsNot(record, weather["segments"][decision])

    def test_environment_observation_shows_the_strictly_earlier_record(self):
        for labels in (SHARED_DAYS, DISTINCT_DAYS):
            env = _bare_env(labels=labels)
            weather = _weather(labels)
            records = [weather["pre_start"], *weather["segments"]]
            by_label = {}
            for record in records:
                by_label.setdefault(record["gridmet_daily_label_mst"], []).append(record)
            for decision in range(4):
                env.decision_index = decision
                label = env.observed_weather_labels[decision]
                upcoming = weather["segments"][decision]
                with self.subTest(labels=labels, decision=decision):
                    self.assertLess(label, upcoming["gridmet_daily_label_mst"])
                    np.testing.assert_allclose(env._observation()["weather"],
                                               _expected_weather(by_label[label][-1]), rtol=1e-6)
                    self.assertFalse(np.allclose(env._observation()["weather"],
                                                 _expected_weather(upcoming)))
            # The terminal observation after the last step must not index past the horizon.
            env.decision_index = 4
            env._observation()

    def test_perfect_forecast_ablation_shows_the_upcoming_segment(self):
        env = _bare_env("upcoming_perfect_forecast")
        weather = _weather(SHARED_DAYS)
        for decision in range(4):
            env.decision_index = decision
            np.testing.assert_allclose(env._observation()["weather"],
                                       _expected_weather(weather["segments"][decision]), rtol=1e-6)

    def test_old_upcoming_label_is_not_accepted(self):
        with self.assertRaisesRegex(ValueError, "weather observation"):
            FedsSimFireEnv(sim_params=SimFireParams(wind_adjustment_factor=0.01),
                           weather_observation="upcoming")

    def test_weather_file_with_another_feds_time_reading_is_refused(self):
        # TASK-027: a file sampled under the old "FEDS t is UTC" reading (no stated
        # reference) must not load, even with a matching manifest hash.
        import hashlib
        import json

        for reference in (None, "naive_feds_t_as_utc"):
            with self.subTest(reference=reference), tempfile.TemporaryDirectory() as directory:
                manifest = Path(directory) / "manifest.json"
                manifest.write_text(json.dumps({"test_cases_loaded": False, "cases": [
                    {"scenario_id": "a", "split": "train"}]}), encoding="utf-8")
                record = dict(_weather(SHARED_DAYS), scenario_id="a", split="train")
                payload = {
                    "test_cases_loaded": False,
                    "episode_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
                    "cases": [record],
                }
                if reference is not None:
                    payload["temporal_mapping"] = {"feds_time_reference": reference}
                weather = Path(directory) / "weather.json"
                weather.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "FEDS time reference"):
                    FedsSimFireEnv(sim_params=SimFireParams(wind_adjustment_factor=0.01),
                                   manifest_path=manifest, weather_path=weather)

    def test_weather_file_without_pre_start_record_is_refused(self):
        import hashlib
        import json

        for mode in WEATHER_OBSERVATIONS:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                manifest = Path(directory) / "manifest.json"
                manifest.write_text(json.dumps({"test_cases_loaded": False, "cases": [
                    {"scenario_id": "a", "split": "train"}]}), encoding="utf-8")
                old = dict(_weather(SHARED_DAYS, pre_start_label=None), scenario_id="a", split="train")
                weather = Path(directory) / "weather.json"
                weather.write_text(json.dumps({
                    "test_cases_loaded": False,
                    "episode_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
                    "temporal_mapping": {"feds_time_reference": FEDS_TIME_REFERENCE},
                    "cases": [old],
                }), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "pre_start.*stage 1"):
                    FedsSimFireEnv(sim_params=SimFireParams(wind_adjustment_factor=0.01),
                                   weather_observation=mode, manifest_path=manifest,
                                   weather_path=weather)


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
