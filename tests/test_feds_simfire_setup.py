import json
import tempfile
import unittest
from pathlib import Path

try:
    from wildfire_rl.feds_simfire_setup import (
        SimFireParams,
        check_split_access,
        load_split_cases,
        require_validation_freeze,
        sha256_file,
    )
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
            dict(wind_adjustment_factor=0.1, fireline_attenuation="per_hour"),
            dict(wind_adjustment_factor=0.1, spread_aggregation="sum"),
        ):
            with self.assertRaises(ValueError):
                SimFireParams(**bad)


class ValidationFreezeGuardTests(unittest.TestCase):
    LEGACY = {"wind_adjustment_factor": 0.01, "internal_update_minutes": 5,
              "active_cell_lifetime_minutes": 90, "ros_multiplier": 1.0,
              "fireline_attenuation": "per_minute", "spread_aggregation": "last_write"}

    def _files(self, directory, *, record=None, allowlisted=True):
        directory = Path(directory)
        weather = directory / "weather.json"
        weather.write_text('{"cases": []}', encoding="utf-8")
        freeze = directory / "freeze.json"
        content = {"selected_on_split": "train", "frozen_params": self.LEGACY,
                   "weather_sha256": sha256_file(weather)}
        content.update(record or {})
        freeze.write_text(json.dumps(content), encoding="utf-8")
        allowlist = directory / "allowlist.json"
        hashes = [{"file": "freeze.json", "sha256": sha256_file(freeze)}] if allowlisted else []
        allowlist.write_text(json.dumps({"records": hashes}), encoding="utf-8")
        return freeze, weather, allowlist

    def test_allowlisted_matching_record_is_accepted_and_hashed(self):
        with tempfile.TemporaryDirectory() as directory:
            freeze, weather, allowlist = self._files(directory)
            digest = require_validation_freeze(SimFireParams(**self.LEGACY), freeze,
                                               weather_path=weather, allowlist_path=allowlist)
            self.assertEqual(digest, sha256_file(freeze))

    def test_mismatches_are_refused(self):
        legacy = SimFireParams(**self.LEGACY)
        cases = (
            ("allowlist", dict(allowlisted=False), legacy),
            ("TRAIN", dict(record={"selected_on_split": "validation"}), legacy),
            ("gridMET", dict(record={"weather_sha256": "0" * 64}), legacy),
            ("parameters", {}, SimFireParams(**dict(self.LEGACY, spread_aggregation="max"))),
            ("parameters", {}, SimFireParams(**dict(self.LEGACY, wind_adjustment_factor=0.05))),
            # A record that predates a field may not inherit today's default for it.
            ("every simulator field",
             dict(record={"frozen_params": {key: value for key, value in self.LEGACY.items()
                                            if key != "fireline_attenuation"}}), legacy),
        )
        for message, options, params in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                freeze, weather, allowlist = self._files(directory, **options)
                with self.assertRaisesRegex(ValueError, message):
                    require_validation_freeze(params, freeze, weather_path=weather,
                                              allowlist_path=allowlist)

    def test_edited_record_loses_its_allowlisted_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            freeze, weather, allowlist = self._files(directory)
            freeze.write_text(freeze.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "allowlist"):
                require_validation_freeze(SimFireParams(**self.LEGACY), freeze,
                                          weather_path=weather, allowlist_path=allowlist)

    def test_test_is_refused_even_with_a_valid_record(self):
        with tempfile.TemporaryDirectory() as directory:
            freeze, weather, allowlist = self._files(directory)
            with self.assertRaisesRegex(ValueError, "TEST"):
                check_split_access("test", SimFireParams(**self.LEGACY), freeze,
                                   weather_path=weather, allowlist_path=allowlist)
            self.assertIsNone(check_split_access("train", SimFireParams(**self.LEGACY)))

    def test_committed_allowlist_is_well_formed(self):
        from wildfire_rl.feds_simfire_setup import FREEZE_ALLOWLIST, ROOT

        allowlist = json.loads(FREEZE_ALLOWLIST.read_text(encoding="utf-8"))
        for item in allowlist["records"]:
            self.assertEqual(sha256_file(ROOT / item["file"]), item["sha256"])


if __name__ == "__main__":
    unittest.main()
