"""Synthetic SimFire runs for line geometry, line strength and spread-order options.

These build a small flat, uniform-fuel grid through the production ``build_simulation``
path. They exercise simulator mechanics only; no FEDS, LANDFIRE or gridMET data.
"""

import unittest

try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest("optional NumPy dependency is not installed: %s" % exc)

try:
    import simfire  # noqa: F401
    from wildfire_rl.feds_simfire_env import SIMFIRE_FIRELINE, sector_line_cells
    from wildfire_rl.feds_simfire_setup import (
        SimFireParams,
        apply_forcing,
        build_simulation,
        forcing_segments,
    )
except ImportError as exc:
    raise unittest.SkipTest("optional SimFire/Gymnasium dependencies are not installed: %s" % exc)


SIZE = 40


def _inputs(front_cells, *, wind_m_s, wind_from=270.0, fuel_code=1):
    segment = {"gridmet_values": {
        "vs": {"value": wind_m_s}, "th": {"value": wind_from}, "fm100": {"value": 5.0},
    }}
    front = np.zeros((SIZE, SIZE), dtype=bool)
    for x, y in front_cells:
        front[y, x] = True
    return {
        "fuel": np.full((SIZE, SIZE), fuel_code, dtype=np.int16),
        "elevation": np.zeros((SIZE, SIZE)),
        "scar": np.zeros((SIZE, SIZE), dtype=bool),
        "front": front,
        "weather": {"segments": [segment] * 4},
    }


def _burn(inputs, line_cells, params, *, duration="48h", reverse_sprites=False):
    simulation, forcing, _cumulative = build_simulation(inputs, params, seed=0)
    if reverse_sprites:
        simulation.fire_manager.sprites = simulation.fire_manager.sprites[::-1]
        simulation.fire_sprites = simulation.fire_manager.sprites
    inside = [(x, y) for x, y in line_cells if 0 <= x < SIZE and 0 <= y < SIZE]
    if inside:
        simulation.update_mitigation([(x, y, SIMFIRE_FIRELINE) for x, y in inside])
    apply_forcing(simulation, forcing[0])
    simulation.run(duration)
    return np.isin(simulation.fire_map, (1, 2))


class DiagonalBarrierTests(unittest.TestCase):
    """A 4-connected diagonal line must stop 8-connected SimFire spread."""

    def setUp(self):
        # Wind from the north-west pushes the fire south-east, straight at the line.
        self.inputs = _inputs([(x, y) for x in range(6, 10) for y in range(6, 10)],
                              wind_m_s=2.0, wind_from=315.0)
        self.params = SimFireParams(wind_adjustment_factor=1.0, internal_update_minutes=5,
                                    active_cell_lifetime_minutes=720)
        # Sector 1 points south-east; its line runs south-west to north-east through
        # the grid centre, with main cells on x + y = 40 and corner cells on x + y = 41.
        self.barrier = sector_line_cells(20, 20, 1, half_steps=SIZE)
        rows, columns = np.indices((SIZE, SIZE))
        self.beyond = columns + rows > 41

    def test_corner_only_diagonal_leaks(self):
        corners_only = [(x, y) for x, y in self.barrier if x + y == 40]
        burned = _burn(self.inputs, corners_only, self.params)
        self.assertGreater(int((burned & self.beyond).sum()), 50)

    def test_four_connected_diagonal_stops_the_fire(self):
        no_line = _burn(self.inputs, (), self.params)
        burned = _burn(self.inputs, self.barrier, self.params)
        self.assertGreater(int((no_line & self.beyond).sum()), 50)
        self.assertEqual(int((burned & self.beyond).sum()), 0)


class FirelineAttenuationStepTests(unittest.TestCase):
    """Pinned SimFire subtracts a fixed 980 ft per update from R * update_rate; ADR-030
    makes the per-minute scaling the default so line strength does not depend on the step."""

    def setUp(self):
        # Fuel 1 with a 5 m/s west wind gives about 558 ft/min eastward: below 980
        # (holds at 1 min) but above 980 / 5 = 196 (breached at 5 min).
        self.inputs = _inputs([(5, y) for y in range(14, 26)], wind_m_s=5.0)
        self.line = sector_line_cells(10, 20, 0, half_steps=SIZE)
        rows, columns = np.indices((SIZE, SIZE))
        self.beyond = columns > 10

    def _beyond(self, minutes, attenuation=None):
        options = {} if attenuation is None else {"fireline_attenuation": attenuation}
        params = SimFireParams(wind_adjustment_factor=1.0, internal_update_minutes=minutes,
                               active_cell_lifetime_minutes=90, **options)
        return int((_burn(self.inputs, self.line, params, duration="2h") & self.beyond).sum())

    def test_pinned_simfire_line_strength_depends_on_the_internal_step(self):
        self.assertEqual(self._beyond(1, "per_update"), 0)
        self.assertGreater(self._beyond(5, "per_update"), 0)

    def test_default_attenuation_gives_the_same_outcome_at_one_and_five_minutes(self):
        self.assertEqual(SimFireParams(wind_adjustment_factor=0.0).fireline_attenuation, "per_minute")
        self.assertEqual(self._beyond(1), 0)
        self.assertEqual(self._beyond(5), 0)

    def test_per_minute_attenuation_matches_default_at_one_minute(self):
        params = [SimFireParams(wind_adjustment_factor=1.0, internal_update_minutes=1,
                                active_cell_lifetime_minutes=90, fireline_attenuation=mode)
                  for mode in ("per_update", "per_minute")]
        maps = [_burn(self.inputs, self.line, item, duration="2h") for item in params]
        np.testing.assert_array_equal(maps[0], maps[1])


class FirelineBankingTests(unittest.TestCase):
    """Pinned SimFire subtracts the line attenuation from every line cell on every update,
    fire or no fire, so an idle line banks a large negative burn amount and becomes a
    near-absolute barrier. The ADR-030 wrapper floors line burn amounts at zero, so a
    line holds iff the rate of spread reaching it stays below 980 ft/min."""

    LINE_X = 37

    def _line(self):
        return [(x, y) for x, y in sector_line_cells(self.LINE_X, 20, 0, half_steps=SIZE)
                if 0 <= y < SIZE]

    def _approach_then_push(self, minutes, wind_m_s):
        """A slow 3 m/s approach for 3h (the line waits), then 3h of a strong west wind."""
        inputs = _inputs([(1, y) for y in range(14, 26)], wind_m_s=3.0)
        params = SimFireParams(wind_adjustment_factor=1.0, internal_update_minutes=minutes)
        simulation, forcing, _cumulative = build_simulation(inputs, params, seed=0)
        line = self._line()
        simulation.update_mitigation([(x, y, SIMFIRE_FIRELINE) for x, y in line])
        apply_forcing(simulation, forcing[0])
        lowest = []
        for _hour in range(3):
            simulation.run("1h")
            lowest.append(min(float(simulation.fire_manager.burn_amounts[y, x]) for x, y in line))
        burned = np.isin(simulation.fire_map, (1, 2))
        self.assertFalse(burned[:, self.LINE_X:].any())
        self.assertTrue(burned[:, self.LINE_X - 6:self.LINE_X].any(), "the fire must be near the line")
        push = forcing_segments(_inputs([(0, 0)], wind_m_s=wind_m_s)["weather"], params)[0]
        apply_forcing(simulation, push)
        simulation.run("3h")
        beyond = int(np.isin(simulation.fire_map, (1, 2))[:, self.LINE_X + 1:].sum())
        return lowest, beyond

    @staticmethod
    def _rates_ft_per_min(wind_m_s):
        """Eastward rates of spread from a north-south front: (diagonal, straight)."""
        inputs = _inputs([(20, y) for y in range(14, 26)], wind_m_s=wind_m_s)
        params = SimFireParams(wind_adjustment_factor=1.0, internal_update_minutes=1)
        simulation, forcing, _cumulative = build_simulation(inputs, params, seed=0)
        apply_forcing(simulation, forcing[0])
        simulation.fire_manager.update(simulation.fire_map)
        rate = simulation.fire_manager.rate_of_spread
        # Interior targets are last written by a diagonal neighbour; the end target by
        # its straight neighbour.
        return float(rate[20, 21]), float(rate[25, 21])

    def test_premise_rates_straddle_the_fireline_attenuation(self):
        diagonal, straight = self._rates_ft_per_min(10.0)
        self.assertGreater(min(diagonal, straight), 980.0 * 1.1)
        diagonal, straight = self._rates_ft_per_min(6.0)
        self.assertLess(max(diagonal, straight), 980.0 * 0.9)

    def test_idle_line_does_not_bank_negative_burn(self):
        for minutes in (1, 5):
            lowest, _beyond = self._approach_then_push(minutes, 6.0)
            with self.subTest(minutes=minutes):
                self.assertEqual(min(lowest), 0.0)

    def test_fire_above_the_attenuation_crosses_a_waiting_line_at_one_and_five_minutes(self):
        for minutes in (1, 5):
            with self.subTest(minutes=minutes):
                self.assertGreater(self._approach_then_push(minutes, 10.0)[1], 0)

    def test_fire_below_the_attenuation_is_held_at_one_and_five_minutes(self):
        for minutes in (1, 5):
            with self.subTest(minutes=minutes):
                self.assertEqual(self._approach_then_push(minutes, 6.0)[1], 0)


class SpreadAggregationTests(unittest.TestCase):
    """SimFire's last-write ROS assignment depends on sprite order; max does not."""

    def setUp(self):
        # An irregular multi-cell front under a diagonal wind, so many target cells are
        # reached from several burning neighbours with different rates of spread.
        cells = [(12, 12), (13, 12), (12, 13), (14, 14), (13, 15), (16, 13), (15, 16)]
        self.inputs = _inputs(cells, wind_m_s=3.0, wind_from=300.0)

    def _maps(self, aggregation):
        params = SimFireParams(wind_adjustment_factor=1.0, internal_update_minutes=5,
                               active_cell_lifetime_minutes=90, spread_aggregation=aggregation)
        return [_burn(self.inputs, (), params, duration="6h", reverse_sprites=flag)
                for flag in (False, True)]

    def test_last_write_depends_on_sprite_order(self):
        forward, reverse = self._maps("last_write")
        self.assertFalse(np.array_equal(forward, reverse))

    def test_max_aggregation_is_order_invariant(self):
        forward, reverse = self._maps("max")
        np.testing.assert_array_equal(forward, reverse)


class GlobalRandomStateTests(unittest.TestCase):
    """Building an episode must not reseed the process-wide RNGs that SB3 uses."""

    def test_build_simulation_leaves_global_random_streams_untouched(self):
        import random

        inputs = _inputs([(5, 5)], wind_m_s=1.0)
        params = SimFireParams(wind_adjustment_factor=1.0)
        random.seed(123)
        np.random.seed(123)
        expected = (random.random(), float(np.random.rand()))
        random.seed(123)
        np.random.seed(123)
        build_simulation(inputs, params, seed=0)
        self.assertEqual((random.random(), float(np.random.rand())), expected)

    def test_build_simulation_is_still_deterministic(self):
        inputs = _inputs([(5, y) for y in range(10, 20)], wind_m_s=3.0)
        params = SimFireParams(wind_adjustment_factor=1.0)
        np.random.seed(1)
        first = _burn(inputs, (), params, duration="2h")
        np.random.seed(2)
        second = _burn(inputs, (), params, duration="2h")
        np.testing.assert_array_equal(first, second)


if __name__ == "__main__":
    unittest.main()
