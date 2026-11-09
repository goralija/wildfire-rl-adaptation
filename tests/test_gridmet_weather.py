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
        try:
            import numpy as np
        except ImportError as exc:
            self.skipTest("optional NumPy dependency is not installed: %s" % exc)

        row, column, longitude, latitude = select_gridmet_nearest_cell(
            np.array([-110.0, -109.95]),
            np.array([37.7, 37.65]),
            longitude=-109.96,
            latitude=37.66,
        )
        self.assertEqual((row, column), (1, 1))
        self.assertEqual((longitude, latitude), (-109.95, 37.65))

    def test_case_cell_is_chosen_per_location_and_far_cells_are_refused(self):
        try:
            import numpy as np
        except ImportError as exc:
            self.skipTest("optional NumPy dependency is not installed: %s" % exc)

        from wildfire_rl.gridmet_weather import select_case_gridmet_cell

        longitudes = np.array([-120.0, -119.96])
        latitudes = np.array([45.0, 44.96])
        first = select_case_gridmet_cell(longitudes, latitudes, -120.0, 45.0)
        second = select_case_gridmet_cell(longitudes, latitudes, -119.96, 44.96)
        self.assertEqual((first["row"], first["column"]), (0, 0))
        self.assertEqual((second["row"], second["column"]), (1, 1))
        self.assertLess(second["distance_km"], 0.01)
        with self.assertRaises(ValueError):
            select_case_gridmet_cell(longitudes, latitudes, -110.0, 35.0)

    @staticmethod
    def _write_gridmet_archive(path, year, name, units, longitudes, latitudes):
        import numpy as np
        from netCDF4 import Dataset

        dataset = Dataset(path, "w")
        dataset.createDimension("day", 365)
        dataset.createDimension("lat", len(latitudes))
        dataset.createDimension("lon", len(longitudes))
        day = dataset.createVariable("day", "f8", ("day",))
        day.units = "days since %d-01-01" % year
        day[:] = np.arange(365)
        dataset.createVariable("lon", "f8", ("lon",))[:] = longitudes
        dataset.createVariable("lat", "f8", ("lat",))[:] = latitudes
        variable = dataset.createVariable(name, "f4", ("day", "lat", "lon"))
        variable.units = units
        # value = 10 * row + column + 1, so every cell is distinguishable
        variable[:] = np.broadcast_to(np.array([[1, 2], [11, 12]], dtype="f4"), (365, 2, 2))
        dataset.close()

    def test_sampler_reads_each_case_at_its_own_cell(self):
        try:
            import numpy as np
            from netCDF4 import Dataset
        except ImportError as exc:
            self.skipTest("optional NetCDF dependencies are not installed: %s" % exc)
        import sys
        import tempfile
        from pathlib import Path
        from unittest import mock

        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root / "scripts"))
        import sample_gridmet_episode_weather as sampler

        names = {
            "th": ("wind_from_direction", "degrees clockwise from north"),
            "vs": ("wind_speed", "m/s"),
            "fm100": ("dead_fuel_moisture_100hr", "%"),
        }
        longitudes = np.array([-120.0, -119.96])
        latitudes = np.array([45.0, 44.96])
        with tempfile.TemporaryDirectory() as directory:
            # The sampler records an archive manifest for every approved year.
            for year in (2018, 2019, 2023):
                for abbreviation, (name, units) in names.items():
                    self._write_gridmet_archive(
                        Path(directory) / f"{abbreviation}_{year}.nc", year, name, units,
                        longitudes, latitudes,
                    )

            def case(scenario_id):
                return {
                    "scenario_id": scenario_id,
                    "split": "train",
                    "event": {"year": 2018},
                    "evaluation_reference": {
                        "initial_state_time": "2018-07-01T12:00:00",
                        "source_fire_id": 1,
                    },
                }

            manifest = {"test_cases_loaded": False, "cases": [case("first"), case("second")]}
            preflight = {"test_cases_loaded": False, "cases": [
                {"scenario_id": "first", "fits_grid": True,
                 "initial_perimeter_centroid_wgs84": {"longitude": -120.0, "latitude": 45.0}},
                {"scenario_id": "second", "fits_grid": True,
                 "initial_perimeter_centroid_wgs84": {"longitude": -119.96, "latitude": 44.96}},
            ]}
            with mock.patch.object(sampler, "verified_hash", return_value="test"), \
                    mock.patch.object(sampler, "validate_gridmet_archive"), \
                    mock.patch.object(sampler, "find_gridmet_variable",
                                      side_effect=lambda ds, ab: (names[ab][0], ds.variables[names[ab][0]])), \
                    mock.patch.object(sampler, "sha256_file", return_value="test"):
                weather = sampler._read_weather(manifest, preflight, Path(directory))

        values = {
            case["scenario_id"]: case["segments"][0]["gridmet_values"]["vs"]["value"]
            for case in weather["cases"]
        }
        self.assertEqual(values, {"first": 1.0, "second": 12.0})
        cells = {
            case["scenario_id"]: (case["segments"][0]["nearest_gridmet_cell"]["row"],
                                  case["segments"][0]["nearest_gridmet_cell"]["column"])
            for case in weather["cases"]
        }
        self.assertEqual(cells, {"first": (0, 0), "second": (1, 1)})


if __name__ == "__main__":
    unittest.main()
