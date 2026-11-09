from dataclasses import replace as dataclasses_replace
import unittest

try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest("optional NumPy dependency is not installed: %s" % exc)

try:
    import gymnasium  # noqa: F401
    HAS_GYM = True
except ImportError:  # the core suite runs without the training venv
    HAS_GYM = False

from wildfire_rl.synthetic_ca import (
    BURNED,
    BURNING,
    CELL_SIZE_M,
    FireState,
    Landscape,
    REFERENCE_MIDFLAME_WIND_M_S,
    SUBSTEP_MINUTES,
    SpreadParams,
    URBAN,
    WATER,
    Weather,
    hashed_uniform,
    initial_state_from_masks,
    ros_m_per_min,
)


def flat(fuel_code, shape=(64, 64)):
    return Landscape(fuel=np.full(shape, fuel_code), elevation=np.zeros(shape))


def run(fire, weather, minutes):
    fire.set_weather(weather)
    for _ in range(int(minutes / SUBSTEP_MINUTES)):
        fire.step_substep()


NOON_REF = Weather(REFERENCE_MIDFLAME_WIND_M_S, 90.0, 0.08, 13.0)


class SpreadTest(unittest.TestCase):
    def test_head_rate_matches_table_order_of_magnitude(self):
        # Grass (FBFM 1), tabled wind, flat ground: head advance within a factor of two.
        land = flat(1, (16, 200))
        fire = FireState(land, 3, SpreadParams(spot_rate=0.0))
        start = np.zeros(land.shape, dtype=bool)
        start[:, 5] = True
        fire.ignite(start)
        minutes = 60.0
        run(fire, NOON_REF, minutes)
        front = np.mean([np.flatnonzero(row).max() for row in fire.ever_burned])
        advance_m = (front - 5) * CELL_SIZE_M
        expected = ros_m_per_min(1) * minutes
        self.assertGreater(advance_m, 0.75 * expected)
        self.assertLess(advance_m, 1.3 * expected)

    def test_head_faster_than_back(self):
        land = flat(2, (80, 80))
        fire = FireState(land, 5, SpreadParams(spot_rate=0.0))
        start = np.zeros(land.shape, dtype=bool)
        start[40, 40] = True
        fire.ignite(start)
        run(fire, NOON_REF, 120)
        cols = np.flatnonzero(fire.ever_burned.any(axis=0))
        self.assertGreater(cols.max() - 40, 2 * (40 - cols.min()))

    def test_timber_slower_than_grass(self):
        areas = {}
        for code in (1, 8):
            land = flat(code)
            fire = FireState(land, 1, SpreadParams(spot_rate=0.0))
            start = np.zeros(land.shape, dtype=bool)
            start[32, 32] = True
            fire.ignite(start)
            run(fire, NOON_REF, 180)
            areas[code] = fire.ever_burned.sum()
        self.assertGreater(areas[1], 5 * areas[8])

    def test_nonburnable_and_line_stop_contact_spread(self):
        fuel = np.full((20, 40), 1)
        fuel[:, 20] = WATER
        land = Landscape(fuel=fuel, elevation=np.zeros(fuel.shape))
        fire = FireState(land, 2, SpreadParams(spot_rate=0.0))
        fire.line[:, 10] = True
        start = np.zeros(fuel.shape, dtype=bool)
        start[:, 2] = True
        fire.ignite(start)
        run(fire, NOON_REF, 240)
        self.assertFalse(fire.ever_burned[:, 11:].any())
        self.assertFalse(fire.ever_burned[:, 10].any())

    def test_diagonal_line_does_not_leak(self):
        land = flat(3, (30, 30))
        fire = FireState(land, 4, SpreadParams(spot_rate=0.0))
        for i in range(30):
            fire.line[i, 29 - i] = True
            if i:
                fire.line[i, 30 - i] = True  # staircase: orthogonally connected
        start = np.zeros(land.shape, dtype=bool)
        start[0, 0] = True
        fire.ignite(start)
        run(fire, Weather(6.0, 135.0, 0.06, 13.0), 600)
        self.assertTrue(fire.ever_burned[0, 0])
        self.assertFalse(fire.ever_burned[29, 29])

    def test_common_random_numbers_and_prior_damage(self):
        land = flat(2)
        scar = np.zeros(land.shape, dtype=bool)
        front = np.zeros(land.shape, dtype=bool)
        scar[30:34, 28:31] = True
        front[30:34, 31] = True
        a = initial_state_from_masks(land, 9, SpreadParams(), scar, front)
        b = a.copy()
        self.assertTrue((a.state[scar & ~front] == BURNED).all())
        self.assertTrue((a.state[front] == BURNING).all())
        run(a, NOON_REF, 60)
        run(b, NOON_REF, 60)
        np.testing.assert_array_equal(a.ever_burned, b.ever_burned)
        c = initial_state_from_masks(land, 10, SpreadParams(), scar, front)
        run(c, NOON_REF, 60)
        self.assertFalse(np.array_equal(a.ever_burned, c.ever_burned))

    def test_hashed_uniform_is_keyed_per_cell(self):
        cells = np.arange(1000)
        u = hashed_uniform(1, 2, cells, 0)
        self.assertTrue(((u >= 0) & (u < 1)).all())
        self.assertAlmostEqual(float(u.mean()), 0.5, delta=0.05)
        np.testing.assert_array_equal(hashed_uniform(1, 2, cells[500:], 0), u[500:])
        self.assertFalse(np.array_equal(hashed_uniform(1, 3, cells, 0), u))

    def test_urban_cells_can_burn(self):
        fuel = np.full((20, 20), 1)
        fuel[:, 10:] = URBAN
        land = Landscape(fuel=fuel, elevation=np.zeros(fuel.shape))
        fire = FireState(land, 1, SpreadParams(spot_rate=0.0))
        start = np.zeros(fuel.shape, dtype=bool)
        start[:, 0] = True
        fire.ignite(start)
        run(fire, NOON_REF, 600)
        self.assertTrue(fire.ever_burned[:, 10:].any())


@unittest.skipUnless(HAS_GYM, "gymnasium is only in the training venv")
class EnvironmentTest(unittest.TestCase):
    def setUp(self):
        from wildfire_rl import synthetic_env as se
        self.se = se

    def _spec(self, units, fuel_code=1, horizon=6, shape=(128, 128)):
        se = self.se
        from wildfire_rl.synthetic_ca import WeatherSeries
        land = Landscape(fuel=np.full(shape, fuel_code), elevation=np.zeros(shape))
        front = np.zeros(shape, dtype=bool)
        front[60:68, 60] = True
        weather = WeatherSeries([Weather(2.0, 90.0, 0.08, 13.0)] * (horizon + se.TAIL_DECISIONS))
        return se.EpisodeSpec(landscape=land, weather=weather, scar=np.zeros(shape, bool),
                              front=front, units=units, horizon=horizon, seed=3,
                              params=SpreadParams(spot_rate=0.0))

    def test_noop_return_is_zero_and_masks_keep_stay(self):
        se = self.se
        env = se.SyntheticSuppressionEnv()
        env.reset(options={"episode_spec": self._spec([(se.HAND_CREW, 0.0)])})
        total, done = 0.0, False
        while not done:
            mask = env.action_masks().reshape(se.MAX_UNITS, se.ACTIONS_PER_UNIT)
            self.assertTrue(mask[:, 0].all())
            self.assertFalse(mask[1:, 1:].any())  # empty slots can only stay
            _, reward, done, _, info = env.step(np.zeros(se.MAX_UNITS, dtype=int))
            total += reward
        self.assertAlmostEqual(total, 0.0, places=9)
        self.assertAlmostEqual(info["episode_summary"]["saved_fraction"], 0.0, places=9)

    def test_unit_speed_is_bounded(self):
        se = self.se
        env = se.SyntheticSuppressionEnv()
        env.reset(options={"episode_spec": self._spec([(se.HAND_CREW, 0.0)], fuel_code=8)})
        env.step(np.zeros(se.MAX_UNITS, dtype=int))
        unit = env.units[0]
        start = (unit.row, unit.col)
        # Move east for one hour.
        action = np.zeros(se.MAX_UNITS, dtype=int)
        action[0] = 1 + 2
        env.step(action)
        moved_m = abs(unit.col - start[1]) * CELL_SIZE_M + abs(unit.row - start[0]) * CELL_SIZE_M
        limit = se.UNIT_TYPES[se.HAND_CREW].travel_m_per_min * se.DECISION_MINUTES
        self.assertLessEqual(moved_m, limit + CELL_SIZE_M)

    def test_line_rate_is_bounded(self):
        se = self.se
        env = se.SyntheticSuppressionEnv(auto_retreat=False)
        env.reset(options={"episode_spec": self._spec([(se.HAND_CREW, 0.0)], fuel_code=8)})
        env.step(np.zeros(se.MAX_UNITS, dtype=int))
        action = np.zeros(se.MAX_UNITS, dtype=int)
        action[0] = 9 + 4  # build line heading south
        before = env.fire.line.sum()
        for _ in range(3):
            env.step(action)
        built_m = (env.fire.line.sum() - before) * CELL_SIZE_M
        rate = se.UNIT_TYPES[se.HAND_CREW].line_m_per_min(8, 0.0)
        self.assertGreater(built_m, 0)
        self.assertLessEqual(built_m, rate * 3 * se.DECISION_MINUTES + CELL_SIZE_M)

    def _cells_built_in_12h(self, headings):
        """Hand crew in FM8 on flat ground, far from the fire, building for 12 decisions."""
        se = self.se
        env = se.SyntheticSuppressionEnv(auto_retreat=False)
        env.reset(options={"episode_spec": self._spec([(se.HAND_CREW, 0.0)], fuel_code=8,
                                                       horizon=14)})
        unit = env.units[0]
        unit.active = True
        unit.row, unit.col = 64, 10
        action = np.zeros(se.MAX_UNITS, dtype=int)
        for hour in range(12):
            action[0] = 9 + headings[hour % len(headings)]
            _, _, done, _, _ = env.step(action)
            self.assertFalse(done)
        return int(env.fire.line.sum())

    def test_changing_heading_keeps_build_progress_in_the_same_cell(self):
        # FM8 hand crew: 5 ch/h = 1.68 m/min, so one 180 m cell takes ~107 min. Alternating
        # two build headings every hour must not reset the cell's progress (ADR-029, item 4).
        holding = self._cells_built_in_12h([2])
        alternating = self._cells_built_in_12h([2, 4])
        self.assertGreaterEqual(holding, 5)
        self.assertEqual(alternating, holding)

    def test_stay_keeps_build_progress(self):
        se = self.se
        env = se.SyntheticSuppressionEnv(auto_retreat=False)
        env.reset(options={"episode_spec": self._spec([(se.HAND_CREW, 0.0)], fuel_code=8,
                                                       horizon=14)})
        unit = env.units[0]
        unit.active = True
        unit.row, unit.col = 64, 10
        build, stay = np.zeros(se.MAX_UNITS, dtype=int), np.zeros(se.MAX_UNITS, dtype=int)
        build[0] = 9 + 2
        env.step(build)  # ~60 of the ~107 minutes the cell needs
        env.step(stay)
        env.step(build)
        self.assertTrue(env.fire.line[64, 10])

    def _corridor_spec(self, horizon=6):
        """One grass row (cols 50-70) in barren ground; the no-op fire burns it end to end."""
        se = self.se
        from wildfire_rl.synthetic_ca import BARREN, WeatherSeries
        shape = (128, 128)
        fuel = np.full(shape, BARREN)
        fuel[64, 50:71] = 1
        land = Landscape(fuel=fuel, elevation=np.zeros(shape))
        front = np.zeros(shape, dtype=bool)
        front[64, 50] = True
        weather = WeatherSeries([Weather(2.0, 90.0, 0.08, 13.0)] * (horizon + se.TAIL_DECISIONS))
        return se.EpisodeSpec(landscape=land, weather=weather, scar=np.zeros(shape, bool),
                              front=front, units=[], horizon=horizon, seed=3,
                              params=SpreadParams(spot_rate=0.0))

    def _run_to_end(self, env):
        se = self.se
        total, done = 0.0, False
        while not done:
            _, reward, done, _, info = env.step(np.zeros(se.MAX_UNITS, dtype=int))
            total += reward
        return total, info["episode_summary"]

    def test_line_on_a_cell_the_noop_burns_is_not_saved(self):
        se = self.se
        env = se.SyntheticSuppressionEnv()
        env.reset(options={"episode_spec": self._corridor_spec()})
        self.assertTrue(env.noop_final.ever_burned[64, 70])
        self.assertEqual(env.noop_total, 20.0)
        env.fire.line[64, 70] = True  # dead end of the corridor: the line protects nothing else
        total, summary = self._run_to_end(env)
        self.assertEqual(summary["saved_fraction"], 0.0)
        self.assertAlmostEqual(total, 0.0, places=9)
        self.assertEqual(summary["line_cells"], 1)
        self.assertEqual(summary["line_cells_in_noop_footprint"], 1)
        self.assertAlmostEqual(summary["line_area_ha"], 3.24)

    def test_line_outside_the_noop_footprint_is_not_charged(self):
        se = self.se
        env = se.SyntheticSuppressionEnv()
        spec = self._corridor_spec()
        spec.landscape.fuel[10, 10] = 1
        spec = dataclasses_replace(spec, landscape=Landscape(fuel=spec.landscape.fuel,
                                                             elevation=spec.landscape.elevation))
        env.reset(options={"episode_spec": spec})
        self.assertFalse(env.noop_final.ever_burned[10, 10])
        env.fire.line[10, 10] = True
        _, summary = self._run_to_end(env)
        self.assertEqual(summary["saved_fraction"], 0.0)
        self.assertEqual(summary["line_cells"], 1)
        self.assertEqual(summary["line_cells_in_noop_footprint"], 0)

    def test_line_that_stops_the_fire_saves_only_the_cells_beyond_it(self):
        se = self.se
        env = se.SyntheticSuppressionEnv()
        env.reset(options={"episode_spec": self._corridor_spec()})
        env.fire.line[64, 60] = True  # cols 61-70 (10 cells) are protected; col 60 is consumed
        _, summary = self._run_to_end(env)
        self.assertAlmostEqual(summary["saved_fraction"], 10 / 20)

    def test_return_equals_saved_minus_safety_penalties(self):
        se = self.se
        from wildfire_rl.synthetic_heuristics import make_random_policy, run_episode
        env = se.SyntheticSuppressionEnv()
        for seed in range(3):
            spec = self._spec([(se.HAND_CREW, 0.0), (se.DOZER, 30.0)], fuel_code=2)
            row = run_episode(env, make_random_policy(seed), {"episode_spec": spec})
            expected = (row["saved_fraction"] - env.unit_loss_penalty * row["units_lost"]
                        - env.close_call_penalty * row["close_calls"])
            self.assertAlmostEqual(row["return"], expected, places=9)

    def test_units_arrive_late_and_away_from_fire(self):
        se = self.se
        env = se.SyntheticSuppressionEnv()
        env.reset(options={"episode_spec": self._spec([(se.DOZER, 150.0)])})
        self.assertFalse(env.units[0].active)
        env.step(np.zeros(se.MAX_UNITS, dtype=int))
        self.assertFalse(env.units[0].active)
        env.step(np.zeros(se.MAX_UNITS, dtype=int))
        env.step(np.zeros(se.MAX_UNITS, dtype=int))
        unit = env.units[0]
        self.assertTrue(unit.active)
        burned = np.argwhere(env.fire.ever_burned)
        nearest = np.abs(burned - (unit.row, unit.col)).max(axis=1).min()
        self.assertGreater(nearest, 3)

    def _unit_at(self, row, col):
        se = self.se
        env = se.SyntheticSuppressionEnv(auto_retreat=False)
        env.reset(options={"episode_spec": self._spec([(se.HAND_CREW, 0.0)])})
        unit = env.units[0]
        unit.active = True
        unit.row, unit.col = row, col
        return env, unit

    def test_surrounded_unit_is_lost_and_penalised(self):
        se = self.se
        env, unit = self._unit_at(30, 30)
        ring = np.zeros(env.land.shape, dtype=bool)
        ring[29:32, 29:32] = True
        env.fire.ignite(ring)
        env._overrun(unit)
        self.assertTrue(unit.lost)
        self.assertFalse(unit.active)

    def test_unit_with_open_neighbour_is_displaced_not_lost(self):
        env, unit = self._unit_at(30, 30)
        cell = np.zeros(env.land.shape, dtype=bool)
        cell[30, 29:31] = True
        env.fire.ignite(cell)
        env._overrun(unit)
        self.assertFalse(unit.lost)
        self.assertEqual(unit.close_calls, 1)
        self.assertNotEqual((unit.row, unit.col), (30, 30))
        self.assertNotEqual(env.fire.state[unit.row, unit.col], 1)

    def test_loss_penalty_reaches_reward(self):
        se = self.se
        env, unit = self._unit_at(30, 30)
        ring = np.zeros(env.land.shape, dtype=bool)
        ring[29:32, 29:32] = True
        ring[30, 30] = False
        env.fire.ignite(ring)
        _, reward, _, _, _ = env.step(np.zeros(se.MAX_UNITS, dtype=int))
        self.assertTrue(unit.lost)
        self.assertLess(reward, -0.5)

    def test_reused_fire_keeps_noop_and_changes_units(self):
        se = self.se
        env = se.SyntheticSuppressionEnv(reuse_fires=3)
        env.reset(seed=1)
        first = (env.spec_now.seed, env.noop_total, env.spec_now.units)
        env.reset()
        second = (env.spec_now.seed, env.noop_total, env.spec_now.units)
        self.assertEqual(first[:2], second[:2])
        self.assertEqual(env.spec_now.variant, 1)
        env.reset()
        env.reset()
        self.assertNotEqual(env.spec_now.seed, first[0])
        # Validation seeds never reuse.
        env.reset(options={"seed": 0})
        a = env.noop_total
        env.reset(options={"seed": 0})
        self.assertEqual(a, env.noop_total)
        self.assertEqual(env.spec_now.variant, 0)

    def test_synthetic_episodes_are_reproducible(self):
        se = self.se
        a = se.sample_synthetic_episode(5, se.Curriculum())
        b = se.sample_synthetic_episode(5, se.Curriculum())
        np.testing.assert_array_equal(a.landscape.fuel, b.landscape.fuel)
        np.testing.assert_array_equal(a.front, b.front)
        self.assertEqual(a.units, b.units)


if __name__ == "__main__":
    unittest.main()
