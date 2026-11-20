import json
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts import analyze_feds_b1 as analysis
from scripts import enumerate_feds_b1 as enumeration
from wildfire_rl.feds_simfire_setup import sha256_file


class B1ReportGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        plan = analysis.ROOT / "configs/frozen/feds-b1-exploration-v1.json"
        frozen = analysis.ROOT / "configs/frozen/feds-simfire-growth-gate-freeze-v1.json"
        manifest = analysis.ROOT / "data/manifests/feds-episode-cohort-v1.json"
        self.settings = {"plan_sha256": sha256_file(plan),
                         "manifest_sha256": sha256_file(manifest),
                         "params": json.loads(frozen.read_text())["frozen_params"]}
        self.mask = self.root / "train-a.npz"
        self.mask.write_bytes(b"test masks; not loaded or unpickled")
        self.case = {"scenario_id": "train-a", "split": "train", "settings": self.settings,
                     "reference_check": "PASS", "mask_file_sha256": sha256_file(self.mask)}
        self.case_path = self.root / "train-a.json"
        self.table_path = self.root / "table.json"
        self.table = {"split": "train", "validation_used": False, "test_cases_loaded": False,
                      "settings": self.settings, "case_count": 1}
        self.write_case()

    def tearDown(self):
        self.temp.cleanup()

    def write_case(self):
        self.case_path.write_text(json.dumps(self.case))
        self.table["cases"] = [{"scenario_id": "train-a", "file": self.case_path.name,
                                "sha256": sha256_file(self.case_path)}]

    def load(self):
        self.table_path.write_text(json.dumps(self.table))
        with mock.patch.object(analysis, "load_split_cases", return_value={"train-a": {}}):
            return analysis.load_table(self.table_path)

    def test_valid_train_identity_and_artifact_chain_is_accepted(self):
        _, cases = self.load()
        self.assertEqual([case["scenario_id"] for case in cases], ["train-a"])

    def test_holdout_flags_are_refused_before_reading_case_files(self):
        for field, value in (("split", "validation"), ("validation_used", True),
                             ("test_cases_loaded", True)):
            with self.subTest(field=field):
                original = self.table[field]
                self.table[field] = value
                with self.assertRaises(ValueError):
                    self.load()
                self.table[field] = original

    def test_mismatched_case_split_or_reference_is_refused(self):
        for field, value in (("split", "validation"), ("scenario_id", "other"),
                             ("reference_check", "FAIL")):
            with self.subTest(field=field):
                original = self.case[field]
                self.case[field] = value
                self.write_case()
                with self.assertRaises(ValueError):
                    self.load()
                self.case[field] = original

    def test_changed_masks_or_duplicate_fires_are_refused(self):
        self.mask.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.load()
        self.case["mask_file_sha256"] = sha256_file(self.mask)
        self.write_case()
        self.table["cases"] *= 2
        self.table["case_count"] = 2
        with self.assertRaises(ValueError):
            self.load()

    def test_weather_or_simulator_setting_difference_is_refused(self):
        self.case["settings"] = {**self.settings, "weather_sha256": "different"}
        self.write_case()
        with self.assertRaises(ValueError):
            self.load()

    def test_stale_manifest_or_different_frozen_params_are_refused(self):
        self.settings["manifest_sha256"] = "another-manifest"
        self.write_case()
        with self.assertRaises(ValueError):
            self.load()
        manifest = analysis.ROOT / "data/manifests/feds-episode-cohort-v1.json"
        self.settings["manifest_sha256"] = sha256_file(manifest)
        self.settings["params"]["wind_adjustment_factor"] = .605
        self.write_case()
        with self.assertRaises(ValueError):
            self.load()


@unittest.skipUnless(importlib.util.find_spec("gymnasium") and importlib.util.find_spec("numpy"),
                     "resume path requires optional Gymnasium/NumPy")
class B1ResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.settings = {"weather_path": "weather.json", "input_root": "inputs",
                         "weather_sha256": "weather-hash"}
        self.mask = self.root / "train-a.npz"
        self.mask.write_bytes(b"generated binary artifact, never deserialized in this test")
        self.previous = {"settings": self.settings, "mask_file_sha256": sha256_file(self.mask),
                         "input_receipt_sha256": "receipt", "seconds": 1.}
        self.path = self.root / "train-a.json"
        self.path.write_text(json.dumps(self.previous))

    def tearDown(self):
        self.temp.cleanup()

    def test_matching_cache_skips_simulation_after_validating_inputs(self):
        with mock.patch("wildfire_rl.feds_simfire_setup.load_case_inputs",
                        return_value={"receipt_sha256": "receipt"}) as load, \
                mock.patch("wildfire_rl.feds_simfire_env.FedsSimFireEnv") as env:
            result = enumeration.run_case(("train-a", self.settings, str(self.root)))
        self.assertTrue(result["resumed"])
        load.assert_called_once()
        env.assert_not_called()

    def test_changed_weather_identity_is_not_resumed(self):
        changed = {**self.settings, "weather_sha256": "new-weather"}
        with mock.patch("wildfire_rl.feds_simfire_setup.load_case_inputs") as load, \
                self.assertRaises(ValueError):
            enumeration.run_case(("train-a", changed, str(self.root)))
        load.assert_not_called()

    def test_changed_mask_is_not_resumed(self):
        self.mask.write_bytes(b"modified")
        with self.assertRaises(ValueError):
            enumeration.run_case(("train-a", self.settings, str(self.root)))

    def test_changed_verified_input_receipt_is_not_resumed(self):
        with mock.patch("wildfire_rl.feds_simfire_setup.load_case_inputs",
                        return_value={"receipt_sha256": "changed"}), self.assertRaises(ValueError):
            enumeration.run_case(("train-a", self.settings, str(self.root)))
