"""Tests for the real-FEDS-case adapter of the synthetic CA (ADR-028)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np

from wildfire_rl.feds_simfire_setup import INPUT_ROOT, MANIFEST, WEATHER
from wildfire_rl.synthetic_env import TAIL_DECISIONS
from wildfire_rl.synthetic_real_cases import (
    CROP,
    DEFAULT_UNITS,
    HORIZON,
    REAL_WIND_ADJUSTMENT,
    VALID_FUEL_CODES,
    crop_window,
    fill_elevation_nodata,
    load_real_episode_specs,
    local_solar_hour,
    map_fuel_codes,
    stable_case_seed,
    weather_from_segments,
)


def _segment(start: str, end: str, vs: float, th: float, fm100: float) -> dict:
    return {"start_utc": start, "end_utc": end,
            "gridmet_values": {"vs": {"value": vs}, "th": {"value": th},
                               "fm100": {"value": fm100}}}


SEGMENTS = [
    _segment("2018-07-24T00:00:00+00:00", "2018-07-24T12:00:00+00:00", 2.0, 183.0, 7.4),
    _segment("2018-07-24T12:00:00+00:00", "2018-07-25T00:00:00+00:00", 4.0, 10.0, 8.0),
    _segment("2018-07-25T00:00:00+00:00", "2018-07-25T12:00:00+00:00", 6.0, 270.0, 9.0),
    _segment("2018-07-25T12:00:00+00:00", "2018-07-26T00:00:00+00:00", 8.0, 90.0, 10.0),
]
START = datetime(2018, 7, 24, tzinfo=timezone.utc)
LOCAL_DATA = MANIFEST.is_file() and WEATHER.is_file() and INPUT_ROOT.is_dir()


class WeatherConversionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.series = weather_from_segments(SEGMENTS, START, longitude=-120.0)

    def test_length_covers_horizon_and_tail(self) -> None:
        self.assertEqual(len(self.series.steps), HORIZON + TAIL_DECISIONS)

    def test_direction_flip_from_wind_from_to_wind_to(self) -> None:
        self.assertAlmostEqual(self.series.steps[0].wind_to_deg, 3.0)
        self.assertAlmostEqual(self.series.steps[12].wind_to_deg, 190.0)
        self.assertAlmostEqual(self.series.steps[24].wind_to_deg, 90.0)
        self.assertAlmostEqual(self.series.steps[36].wind_to_deg, 270.0)

    def test_wind_adjustment_and_moisture(self) -> None:
        self.assertEqual(REAL_WIND_ADJUSTMENT, 0.3)
        self.assertAlmostEqual(self.series.steps[0].wind_midflame_m_s, 0.6)
        self.assertAlmostEqual(self.series.steps[0].moisture, 0.074)
        custom = weather_from_segments(SEGMENTS, START, -120.0, wind_adjustment=0.5)
        self.assertAlmostEqual(custom.steps[12].wind_midflame_m_s, 2.0)

    def test_local_solar_hour_from_utc_and_longitude(self) -> None:
        # 00 UTC at 120 W is 16:00 local solar time, then one hour per decision.
        self.assertAlmostEqual(self.series.steps[0].local_hour, 16.0)
        self.assertAlmostEqual(self.series.steps[1].local_hour, 17.0)
        self.assertAlmostEqual(self.series.steps[8].local_hour, 0.0)
        moment = datetime(2020, 1, 1, 18, 30, tzinfo=timezone.utc)
        self.assertAlmostEqual(local_solar_hour(moment, 15.0), 19.5)
        self.assertAlmostEqual(local_solar_hour(moment, -108.0), (18.5 - 7.2) % 24)

    def test_segments_held_constant_and_last_held_beyond(self) -> None:
        steps = self.series.steps
        for block in range(4):
            values = {(s.wind_midflame_m_s, s.wind_to_deg, s.moisture)
                      for s in steps[12 * block:12 * block + 12]}
            self.assertEqual(len(values), 1)
        tail = {(s.wind_midflame_m_s, s.wind_to_deg, s.moisture) for s in steps[36:]}
        self.assertEqual(tail, {(0.3 * 8.0, 270.0, 0.10)})
        hours = [s.local_hour for s in steps[36:]]
        self.assertEqual(len(set(np.round(hours, 6))), 24)

    def test_naive_start_time_is_utc_and_unordered_segments_are_sorted(self) -> None:
        from wildfire_rl.synthetic_real_cases import parse_utc

        start = parse_utc("2018-07-24T00:00:00")
        series = weather_from_segments(list(reversed(SEGMENTS)), start, -120.0)
        self.assertAlmostEqual(series.steps[0].wind_to_deg, 3.0)
        with self.assertRaises(ValueError):
            weather_from_segments(SEGMENTS, parse_utc("2018-07-23T00:00:00"), -120.0)


class CropTest(unittest.TestCase):
    def test_centred_on_centroid(self) -> None:
        mask = np.zeros((256, 256), dtype=bool)
        mask[100:110, 140:150] = True  # centroid (104.5, 144.5)
        r0, c0 = crop_window(mask)
        self.assertEqual((r0 + (CROP - 1) / 2, c0 + (CROP - 1) / 2), (104.5, 144.5))

    def test_clipped_inside_tile(self) -> None:
        mask = np.zeros((256, 256), dtype=bool)
        mask[2, 250] = True
        self.assertEqual(crop_window(mask), (0, 256 - CROP))
        mask[:] = False
        mask[255, 0] = True
        self.assertEqual(crop_window(mask), (256 - CROP, 0))

    def test_crop_larger_than_tile_rejected(self) -> None:
        with self.assertRaises(ValueError):
            crop_window(np.ones((64, 64), dtype=bool))


class FuelAndElevationTest(unittest.TestCase):
    def test_valid_codes_kept_unknown_mapped_to_barren(self) -> None:
        fuel = np.array([[1, 13, 91, 92], [93, 98, 99, -9999], [0, 14, 5, -9999]])
        mapped, unknown = map_fuel_codes(fuel)
        self.assertEqual(mapped.tolist(), [[1, 13, 91, 92], [93, 98, 99, 99], [99, 99, 5, 99]])
        self.assertEqual(unknown, {-9999: 2, 0: 1, 14: 1})
        self.assertTrue(set(np.unique(mapped).tolist()) <= VALID_FUEL_CODES)

    def test_elevation_nodata_filled_from_nearest_valid(self) -> None:
        elevation = np.array([[np.nan, 100.0, -9999.0, -9999.0, 400.0]])
        filled, bad = fill_elevation_nodata(elevation)
        self.assertEqual(bad.tolist(), [[True, False, True, True, False]])
        self.assertEqual(filled.tolist(), [[100.0, 100.0, 100.0, 400.0, 400.0]])
        self.assertEqual(filled.dtype, np.float64)
        clean = np.array([[1.0, 2.0]])
        self.assertFalse(fill_elevation_nodata(clean)[1].any())


class SplitAndSeedTest(unittest.TestCase):
    def test_test_split_refused_before_any_file_is_opened(self) -> None:
        missing = Path("/nonexistent/manifest.json")
        for splits in (("test",), ("train", "test"), ("TRAIN",), ()):
            with self.assertRaises(ValueError):
                load_real_episode_specs(splits, manifest_path=missing, weather_path=missing,
                                        input_root=missing)

    def test_stable_seed_is_deterministic_across_processes(self) -> None:
        seed = stable_case_seed("fpa-fod-400300427-plateau")
        self.assertEqual(seed, stable_case_seed("fpa-fod-400300427-plateau"))
        self.assertTrue(0 <= seed < 2 ** 31)
        self.assertNotEqual(seed, stable_case_seed("fpa-fod-400300631-ranch"))
        code = ("from wildfire_rl.synthetic_real_cases import stable_case_seed;"
                "print(stable_case_seed('fpa-fod-400300427-plateau'))")
        env = {"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
               "PYTHONHASHSEED": "random"}
        output = subprocess.run([sys.executable, "-c", code], env=env, check=True,
                                capture_output=True, text=True).stdout.strip()
        self.assertEqual(int(output), seed)


@unittest.skipUnless(LOCAL_DATA, "local FEDS/gridMET inputs are not available")
class LocalCaseTest(unittest.TestCase):
    def test_one_train_case_builds_a_valid_spec(self) -> None:
        [(spec, meta)] = load_real_episode_specs(
            ("train",), scenario_ids=["fpa-fod-400300427-plateau"])
        self.assertEqual(spec.landscape.shape, (CROP, CROP))
        self.assertEqual(spec.scar.shape, (CROP, CROP))
        self.assertEqual(spec.front.dtype, bool)
        self.assertTrue(spec.front.any())
        self.assertEqual(spec.horizon, HORIZON)
        self.assertEqual(len(spec.weather.steps), HORIZON + TAIL_DECISIONS)
        self.assertEqual(spec.units, DEFAULT_UNITS)
        self.assertEqual(spec.params.spread_scale, 1.0)
        self.assertEqual(spec.seed, stable_case_seed(spec.name))
        self.assertEqual(meta["split"], "train")
        self.assertEqual(meta["initial_cells_outside_crop"], 0)
        self.assertEqual(sum(meta["fuel_code_histogram"].values()), CROP * CROP)
        self.assertEqual(meta["start_time_utc"], "2018-07-24T00:00:00+00:00")

    def test_case_from_the_other_split_is_not_found(self) -> None:
        with self.assertRaises(ValueError):
            load_real_episode_specs(("validation",), scenario_ids=["fpa-fod-400300427-plateau"])


if __name__ == "__main__":
    unittest.main()
