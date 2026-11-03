import json
import tempfile
import unittest
from pathlib import Path

try:
    from wildfire_rl.feds_simfire_setup import SimFireParams, load_split_cases
except ImportError as exc:
    raise unittest.SkipTest("optional SimFire setup dependencies are not installed: %s" % exc)


def _manifest(directory, *, test_loaded=False):
    path = Path(directory) / "manifest.json"
    path.write_text(json.dumps({
        "test_cases_loaded": test_loaded,
        "cases": [
            {"scenario_id": "a", "split": "train"},
            {"scenario_id": "b", "split": "validation"},
        ],
    }), encoding="utf-8")
    return path


class FedsSimFireSetupTests(unittest.TestCase):
    def test_test_split_is_never_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = _manifest(directory)
            with self.assertRaises(ValueError):
                load_split_cases("test", path)

    def test_validation_is_returned_only_when_requested(self):
        with tempfile.TemporaryDirectory() as directory:
            path = _manifest(directory)
            self.assertEqual(sorted(load_split_cases("train", path)), ["a"])
            self.assertEqual(sorted(load_split_cases("validation", path)), ["b"])

    def test_manifest_with_test_cases_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = _manifest(directory, test_loaded=True)
            with self.assertRaises(ValueError):
                load_split_cases("train", path)

    def test_params_reject_out_of_range_values(self):
        SimFireParams(wind_adjustment_factor=0.1, active_cell_lifetime_minutes=720, ros_multiplier=0.5)
        for bad in (
            dict(wind_adjustment_factor=1.5),
            dict(wind_adjustment_factor=0.1, internal_update_minutes=7),
            dict(wind_adjustment_factor=0.1, active_cell_lifetime_minutes=0),
            dict(wind_adjustment_factor=0.1, ros_multiplier=0.0),
        ):
            with self.assertRaises(ValueError):
                SimFireParams(**bad)


if __name__ == "__main__":
    unittest.main()
