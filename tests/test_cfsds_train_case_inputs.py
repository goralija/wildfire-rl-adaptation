from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from scripts.audit_cfsds_train_case_inputs import (
    build_report,
    haversine_km,
    parse_weather,
    read_ascii_grid,
)


class CFSDSCaseInputQCTests(unittest.TestCase):
    def test_report_only_materializes_cases_listed_in_train_split(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cohort = root / "cohort.json"
            fuel_qc = root / "fuel-qc.json"
            runs = root / "runs"
            cohort.write_text(
                json.dumps({
                    "selection": {
                        "candidate_day_pairs_by_split": {
                            "train": [{"event_id": "event_train", "year": 2018, "target_doy": 10}],
                            "validation": [{"event_id": "event_validation", "year": 2018, "target_doy": 11}],
                            "test": [{"event_id": "event_test", "year": 2018, "target_doy": 12}],
                        }
                    }
                }),
                encoding="utf-8",
            )
            fuel_qc.write_text(json.dumps({"cases": [], "input_provenance": {}}), encoding="utf-8")

            train_case = runs / "event_train-day10"
            train_case.mkdir(parents=True)
            (train_case / "case.json").write_text(
                json.dumps({
                    "split": "train",
                    "event": {
                        "event_id": "event_train",
                        "target_doy": 10,
                        "target_date_local": "2018-01-10",
                    },
                    "sources": {},
                }),
                encoding="utf-8",
            )
            validation_case = runs / "event_validation-day11"
            validation_case.mkdir(parents=True)
            (validation_case / "case.json").write_text(
                "This non-JSON validation file must never be opened.",
                encoding="utf-8",
            )

            report = build_report(cohort, fuel_qc, runs)

        self.assertEqual(report["scope"]["train_candidate_count"], 1)
        self.assertEqual(report["scope"]["materialized_train_event_ids"], ["event_train"])
        self.assertEqual(report["scope"]["validation_or_test_case_files_opened"], 0)

    def test_haversine_measures_expected_distance(self) -> None:
        # Approximate distance between two points about 5.2 km apart in British Columbia.
        distance = haversine_km(49.8422232, -115.9310211, 49.800003, -115.9)
        self.assertAlmostEqual(distance, 5.195, places=2)

    def test_ascii_grid_reports_geometry_and_nodata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "elevation.asc"
            path.write_text(
                "ncols 2\nnrows 2\nxllcorner 10\nyllcorner 20\n"
                "cellsize 100\nNODATA_value -9999\n1 2\n-9999 4\n",
                encoding="utf-8",
            )
            result = read_ascii_grid(path)

        self.assertEqual(result["valid_cells"], 3)
        self.assertEqual(result["nodata_cells"], 1)
        self.assertEqual(result["minimum"], 1)
        self.assertEqual(result["maximum"], 4)
        self.assertEqual(result["header"]["cellsize"], 100)

    def test_weather_requires_target_local_day_and_complete_hourly_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "Weather.csv"
            start = datetime(2018, 8, 16)
            rows = [
                f"case,{(start + timedelta(hours=i)):%Y-%m-%d %H:%M},0,20,40,5,180,90,30,200,8,50,20"
                for i in range(24)
            ]
            path.write_text(
                "Scenario,datetime,APCP,TMP,RH,WS,WD,FFMC,DMC,DC,ISI,BUI,FWI\n"
                + "\n".join(rows) + "\n",
                encoding="utf-8",
            )
            result = parse_weather(path, "2018-08-16")

        self.assertEqual(result["row_count"], 24)
        self.assertTrue(result["ordered_hourly_24_rows"])
        self.assertTrue(result["all_rows_on_target_local_day"])
        self.assertTrue(all(result["fwi_fields_constant_across_hourly_rows"].values()))


if __name__ == "__main__":
    unittest.main()
