"""Tests for explicit gridMET-to-SimFire units and daily time mapping."""

from __future__ import annotations

import unittest

from wildfire_rl.gridmet_weather import (
    direction_from_to_simfire_direction,
    episode_weather_midpoints,
    gridmet_day_for_utc,
    gridmet_proxy_to_simfire,
    select_gridmet_nearest_cell,
)


class GridmetWeatherTests(unittest.TestCase):
    def test_mst_daily_label_boundary(self):
        from datetime import datetime, timezone

        self.assertEqual(
            gridmet_day_for_utc(datetime(2018, 7, 24, 0, tzinfo=timezone.utc)),
            "2018-07-23",
        )
        self.assertEqual(
            gridmet_day_for_utc(datetime(2018, 7, 24, 12, tzinfo=timezone.utc)),
            "2018-07-24",
        )

    def test_four_12_hour_segments_cover_48_hours(self):
        segments = episode_weather_midpoints("2018-07-24T00:00:00")
        self.assertEqual(len(segments), 4)
        self.assertEqual(segments[0]["midpoint_utc"], "2018-07-24T06:00:00+00:00")
        self.assertEqual(segments[-1]["end_utc"], "2018-07-26T00:00:00+00:00")

    def test_from_direction_is_rotated_to_simfire_downwind_direction(self):
        self.assertEqual(direction_from_to_simfire_direction(0), 180)
        self.assertEqual(direction_from_to_simfire_direction(270), 90)

    def test_speed_moisture_and_adjustment_mapping_are_explicit(self):
        mapped = gridmet_proxy_to_simfire(
            wind_speed_m_s=1.0,
            wind_from_degrees=0.0,
            fm100_percent=10.0,
            wind_adjustment_factor=0.5,
        )
        self.assertAlmostEqual(mapped["wind_speed_midflame_ft_per_min_proxy"], 98.4251968504)
        self.assertEqual(mapped["wind_direction_degrees_clockwise_north_to"], 180.0)
        self.assertEqual(mapped["fuel_moisture_fraction_proxy"], 0.1)

    def test_nearest_rectilinear_gridmet_cell(self):
        import numpy as np

        row, column, longitude, latitude = select_gridmet_nearest_cell(
            np.array([-110.0, -109.95]),
            np.array([37.7, 37.65]),
            longitude=-109.96,
            latitude=37.66,
        )
        self.assertEqual((row, column), (1, 1))
        self.assertEqual((longitude, latitude), (-109.95, 37.65))


if __name__ == "__main__":
    unittest.main()
