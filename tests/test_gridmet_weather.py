"""Tests for explicit gridMET-to-SimFire units and daily time mapping."""

from __future__ import annotations

import unittest

from wildfire_rl.gridmet_weather import (
    FEDS_TIME_REFERENCE,
    pre_start_weather_day,
    GRIDMET_MST,
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

    def test_feds_label_is_the_viirs_overpass_in_local_solar_time(self):
        # TASK-027 / ADR-030 addendum: FEDS `t` 00:00/12:00 is the AM/PM overpass label
        # (about 01:30/13:30 local solar time), converted to UTC with longitude / 15.
        from datetime import datetime, timezone
        from wildfire_rl.gridmet_weather import feds_overpass_utc

        self.assertEqual(feds_overpass_utc("2018-07-24T00:00:00", -120.0),
                         datetime(2018, 7, 24, 9, 30, tzinfo=timezone.utc))
        self.assertEqual(feds_overpass_utc("2018-07-24T12:00:00", -120.0),
                         datetime(2018, 7, 24, 21, 30, tzinfo=timezone.utc))
        self.assertEqual(feds_overpass_utc("2018-07-24T00:00:00", -105.0),
                         datetime(2018, 7, 24, 8, 30, tzinfo=timezone.utc))

    def test_feds_label_other_than_am_pm_or_with_a_zone_is_refused(self):
        from wildfire_rl.gridmet_weather import feds_overpass_utc

        for value in ("2018-07-24T03:00:00", "2018-07-24T00:30:00",
                      "2018-07-24T00:00:00Z", "2018-07-24T00:00:00+00:00"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                feds_overpass_utc(value, -120.0)
        with self.assertRaises(ValueError):
            feds_overpass_utc("2018-07-24T00:00:00", 200.0)
        # fireatlas v1.4.1 dates `t` by the UTC acquisition date, so an overpass whose
        # UTC date differs from the label's date contradicts the label.
        with self.assertRaises(ValueError):
            feds_overpass_utc("2018-07-24T00:00:00", 120.0)
        with self.assertRaises(ValueError):
            feds_overpass_utc("2018-07-24T12:00:00", -170.0)

    def test_four_12_hour_segments_cover_48_hours(self):
        segments = episode_weather_midpoints("2018-07-24T00:00:00", longitude=-120.0)
        self.assertEqual(len(segments), 4)
        self.assertEqual(segments[0]["start_utc"], "2018-07-24T09:30:00+00:00")
        self.assertEqual(segments[0]["midpoint_utc"], "2018-07-24T15:30:00+00:00")
        self.assertEqual(segments[-1]["end_utc"], "2018-07-26T09:30:00+00:00")
        self.assertEqual([s["gridmet_daily_label_mst"] for s in segments],
                         ["2018-07-24", "2018-07-24", "2018-07-25", "2018-07-25"])
        pm = episode_weather_midpoints("2018-07-24T12:00:00", longitude=-120.0)
        self.assertEqual([s["gridmet_daily_label_mst"] for s in pm],
                         ["2018-07-24", "2018-07-25", "2018-07-25", "2018-07-26"])

    def test_segment_midpoints_stay_far_from_the_mst_day_boundary(self):
        # Over the cohort's longitudes the daily label must not hinge on the Lon/15
        # approximation (equation of time up to ~16 min, swath-edge spread).
        from datetime import datetime

        for longitude in (-125.0, -115.0, -102.0):
            for start in ("2018-07-24T00:00:00", "2018-07-24T12:00:00"):
                for segment in episode_weather_midpoints(start, longitude=longitude):
                    midpoint = datetime.fromisoformat(segment["midpoint_utc"]).astimezone(
                        GRIDMET_MST)
                    hours = midpoint.hour + midpoint.minute / 60
                    with self.subTest(longitude=longitude, start=start, segment=segment["segment"]):
                        self.assertGreaterEqual(min(hours, 24 - hours), 3.0)

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
        # value = 1000 * day index + 10 * row + column + 1, so every cell and day is
        # distinguishable
        cells = np.array([[1, 2], [11, 12]], dtype="f4")
        variable[:] = cells[None, :, :] + 1000.0 * np.arange(365, dtype="f4")[:, None, None]
        dataset.close()

    def test_observed_day_has_ended_before_each_decision(self):
        # ADR-030 observation rule: the record a decision observes is a complete gridMET
        # day before that segment starts, across the cohort's longitudes and both labels.
        from datetime import datetime, timedelta
        from wildfire_rl.feds_simfire_setup import observed_weather_records

        for longitude in (-125.0, -120.0, -110.0, -102.0):
            for start in ("2018-07-24T00:00:00", "2018-07-24T12:00:00"):
                segments = episode_weather_midpoints(start, longitude=longitude)
                weather = {
                    "segments": [{**segment, "gridmet_values": {"th": {}, "vs": {}, "fm100": {}}}
                                 for segment in segments],
                    "pre_start": {**pre_start_weather_day(start, longitude=longitude),
                                  "gridmet_values": {"th": {}, "vs": {}, "fm100": {}}},
                }
                for segment, record in zip(segments, observed_weather_records(weather)):
                    label = datetime.fromisoformat(record["gridmet_daily_label_mst"])
                    day_end = (label + timedelta(days=1)).replace(tzinfo=GRIDMET_MST)
                    with self.subTest(longitude=longitude, start=start, segment=segment["segment"]):
                        self.assertLessEqual(day_end, datetime.fromisoformat(segment["start_utc"]))

    def test_comparison_with_previous_file_counts_cells_and_labels(self):
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
        import sample_gridmet_episode_weather as sampler

        def record(cell, labels, pre_start=True):
            segments = [{"gridmet_daily_label_mst": label,
                         "nearest_gridmet_cell": {"row": cell[0], "column": cell[1]}}
                        for label in labels]
            case = {"segments": segments}
            if pre_start:
                case["pre_start"] = segments[0]
            return case

        new = {"cases": [
            {"scenario_id": "a", **record((1, 1), ["d1", "d1", "d2", "d2"])},
            {"scenario_id": "b", **record((2, 2), ["d1", "d2", "d2", "d3"])},
        ]}
        old = {"schema_version": "1.0", "episode_manifest_sha256": "m", "cases": [
            {"scenario_id": "a", **record((1, 1), ["d0", "d1", "d1", "d2"], pre_start=False)},
            {"scenario_id": "b", **record((1, 1), ["d1", "d2", "d2", "d3"], pre_start=False)},
            {"scenario_id": "dropped", **record((1, 1), ["d0"] * 4, pre_start=False)},
        ]}
        summary = sampler.compare_with_previous(new, old, "h")
        self.assertEqual(summary["cases_compared"], 2)
        self.assertEqual(summary["cases_with_changed_cell"], 1)
        self.assertEqual(summary["segments_with_changed_daily_label"], 2)
        self.assertEqual(summary["previous_distinct_cells"], 1)
        self.assertEqual(summary["previous_cases_with_pre_start"], 0)
        self.assertEqual(summary["cases_only_in_previous"], ["dropped"])

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

        # 2018-07-01 is day index 181 of 2018; the pre-start day 2018-06-30 is 180.
        values = {
            case["scenario_id"]: case["segments"][0]["gridmet_values"]["vs"]["value"]
            for case in weather["cases"]
        }
        self.assertEqual(values, {"first": 181001.0, "second": 181012.0})
        cells = {
            case["scenario_id"]: (case["segments"][0]["nearest_gridmet_cell"]["row"],
                                  case["segments"][0]["nearest_gridmet_cell"]["column"])
            for case in weather["cases"]
        }
        self.assertEqual(cells, {"first": (0, 0), "second": (1, 1)})
        # Segments start at the PM overpass at each case's own centroid longitude
        # (13:30 local solar at -120 is 21:30 UTC; at -119.96 it is 9.6 s earlier).
        self.assertEqual(
            {case["scenario_id"]: case["segments"][0]["start_utc"] for case in weather["cases"]},
            {"first": "2018-07-01T21:30:00+00:00", "second": "2018-07-01T21:29:50.400000+00:00"},
        )

        # ADR-030: one observation-only record for the gridMET day before segment 0,
        # read at the same per-case cell, with the same fields as a segment.
        for case in weather["cases"]:
            pre_start = case["pre_start"]
            with self.subTest(case=case["scenario_id"]):
                self.assertEqual(case["segments"][0]["gridmet_daily_label_mst"], "2018-07-01")
                self.assertEqual(pre_start["gridmet_daily_label_mst"], "2018-06-30")
                self.assertEqual(pre_start["segment"], "pre_start")
                self.assertEqual(set(pre_start), set(case["segments"][0]))
                self.assertEqual(pre_start["nearest_gridmet_cell"],
                                 case["segments"][0]["nearest_gridmet_cell"])
                self.assertEqual(set(pre_start["gridmet_values"]), {"th", "vs", "fm100"})
        self.assertEqual(
            {case["scenario_id"]: case["pre_start"]["gridmet_values"]["vs"]["value"]
             for case in weather["cases"]},
            {"first": 180001.0, "second": 180012.0},
        )
        self.assertIn("pre_start", weather["temporal_mapping"]["agent_visibility"])
        self.assertEqual(weather["temporal_mapping"]["feds_time_reference"],
                         FEDS_TIME_REFERENCE)

    def test_pre_start_record_is_the_gridmet_day_before_segment_zero(self):
        from wildfire_rl.gridmet_weather import pre_start_weather_day

        for start, longitude in (("2018-07-24T00:00:00", -120.0), ("2018-07-24T12:00:00", -120.0),
                                 ("2019-01-02T00:00:00", -102.5)):
            segments = episode_weather_midpoints(start, longitude=longitude)
            record = pre_start_weather_day(start, longitude=longitude)
            with self.subTest(start=start):
                self.assertLess(record["gridmet_daily_label_mst"],
                                segments[0]["gridmet_daily_label_mst"])
                self.assertEqual(set(record), set(segments[0]))
                self.assertEqual(record["segment"], "pre_start")
        # The AM overpass of 2018-07-24 at -120° is 09:30 UTC, still the 24th in MST, so
        # segment 0 is the 24th and the pre-start day is the 23rd.
        self.assertEqual(pre_start_weather_day("2018-07-24T00:00:00", longitude=-120.0)
                         ["gridmet_daily_label_mst"], "2018-07-23")


if __name__ == "__main__":
    unittest.main()
