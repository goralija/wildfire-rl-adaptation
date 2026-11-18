import unittest
from pathlib import Path
from unittest import mock

try:
    import numpy as np
except ImportError:
    raise unittest.SkipTest("optional NumPy dependency is not installed")

from scripts import sample_gridmet_episode_weather as sampler


class TrainOnlyWeatherTests(unittest.TestCase):
    def test_train_only_never_opens_validation_archives_or_geometry(self):
        manifest = {"test_cases_loaded": False, "cases": [
            {"scenario_id": "train", "split": "train", "event": {"year": 2018},
             "evaluation_reference": {"initial_state_time": "2018-07-01T12:00:00",
                                      "source_fire_id": 1}},
            {"scenario_id": "validation", "split": "validation", "event": {"year": 2023}},
        ]}
        preflight = {"test_cases_loaded": False, "cases": [
            {"scenario_id": "train", "fits_grid": True,
             "initial_perimeter_centroid_wgs84": {"longitude": -120., "latitude": 45.}},
        ]}
        dataset = mock.Mock()
        sample = {"dataset": dataset, "variable": np.ones((2, 1, 1)),
                  "day_index": {"2018-07-01": 0, "2018-07-02": 1, "2018-06-30": 0,
                                "2018-07-03": 1},
                  "longitudes": np.array([-120.]), "latitudes": np.array([45.]),
                  "units": "test", "native_name": "test", "sha256": "hash", "path": "test",
                  "size_bytes": 1}
        with mock.patch.object(sampler, "_open_archive", return_value=sample) as opened, \
                mock.patch.object(sampler, "sha256_file", return_value="manifest"):
            result = sampler._read_weather(manifest, preflight, Path("unused"), split="train")
        self.assertEqual([case["scenario_id"] for case in result["cases"]], ["train"])
        self.assertEqual({call.args[1] for call in opened.call_args_list}, {2018})
        self.assertEqual({item["file"] for item in result["source"]["archives"]},
                         {"th_2018.nc", "vs_2018.nc", "fm100_2018.nc"})

    def test_test_split_is_refused_before_any_archive_is_opened(self):
        with mock.patch.object(sampler, "_open_archive") as opened, self.assertRaises(ValueError):
            sampler._read_weather({"test_cases_loaded": False, "cases": []},
                                  {"test_cases_loaded": False, "cases": []}, Path("unused"),
                                  split="test")
        opened.assert_not_called()
