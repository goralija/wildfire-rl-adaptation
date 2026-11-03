import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/build_feds_simfire_inputs.py"
SPEC = importlib.util.spec_from_file_location("build_feds_simfire_inputs", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BulkFedsInputTests(unittest.TestCase):
    def _item(self, scenario_id, split):
        return {"case": {"scenario_id": scenario_id, "split": split}}

    def _receipt(self, item, _output_root):
        scenario_id = item["case"]["scenario_id"]
        if scenario_id == "bad":
            raise RuntimeError("fixture failure")
        return {
            "fuel": {"sha256": "fuel-hash"},
            "terrain": {"sha256": "terrain-hash"},
            "initial_feds_state": {"mask_sha256": "mask-hash"},
        }

    def test_split_fetch_filters_cases_and_keeps_processing_after_a_failure(self):
        geometries = {
            "train-good": self._item("train-good", "train"),
            "train-bad": self._item("bad", "train"),
            "validation": self._item("validation", "validation"),
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            report = MODULE.fetch_split_cases(
                geometries, "train", Path(temp_dir), fetcher=self._receipt
            )

        self.assertEqual(report["selected_case_count"], 2)
        self.assertEqual(report["verified_case_count"], 1)
        self.assertEqual(report["failed_case_count"], 1)
        self.assertFalse(report["all_cases_verified"])
        self.assertFalse(report["test_cases_loaded"])
        self.assertEqual([row["status"] for row in report["cases"]], ["failed", "verified"])

    def test_bulk_fetch_rejects_test_split_or_empty_selection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                MODULE.fetch_split_cases({}, "test", Path(temp_dir), fetcher=self._receipt)
            with self.assertRaises(ValueError):
                MODULE.fetch_split_cases({}, "train", Path(temp_dir), fetcher=self._receipt)


if __name__ == "__main__":
    unittest.main()
