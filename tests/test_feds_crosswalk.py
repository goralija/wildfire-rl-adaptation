import unittest
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

from scripts.audit_feds_fpa_fle_crosswalk import (
    combine_split_reports,
    consecutive_halfday_run,
    filter_report_to_start_window,
    _feds_case_candidates,
    _feds_crosswalk,
    _feds_file_path,
    _discovery_time_text,
    parse_discovery_date,
    parse_timestamp,
    run_audit,
)
from scripts.fetch_feds_archive import fetch_archive
from scripts.build_feds_episode_manifest import build_episode_manifest


def _case(number, split):
    return {
        "scenario_id": f"case-{number}",
        "fod_id": number,
        "fpa_unique_fire_id": f"fpa-{number}",
        "name": f"Fire {number}",
        "state": "CA",
        "year": 2023 if split == "validation" else 2018,
        "split": split,
        "discovery_time": "2023-07-01 1200" if split == "validation" else "2018-07-01 1200",
        "longitude": -120.0,
        "latitude": 38.0,
    }


class FedsCrosswalkTests(unittest.TestCase):
    def test_episode_manifest_separates_future_reference_from_policy_inputs(self):
        frame_case = {
            "scenario_id": "case-1",
            "split": "train",
            "fod_id": 1,
            "fpa_unique_fire_id": "fpa-1",
            "name": "Fire",
            "state": "CA",
            "year": 2018,
            "discovery_date": "2018-07-01",
            "longitude": -120.0,
            "latitude": 38.0,
            "reported_final_area_acres_reference_only": 9000,
            "mtbs_id_reference_only": "secret-target-id",
        }
        candidate = {
            "fire_id": "123",
            "t_start": "2018-07-01T00:00:00",
            "episode_start_state": "2018-07-01T12:00:00",
            "episode_48h_state_timestamps": [
                f"2018-07-{day:02}T{hour:02}:00:00"
                for day, hour in [(1, 12), (2, 0), (2, 12), (3, 0), (3, 12)]
            ],
            "minimum_start_window_distance_m": 1200,
            "two_consecutive_12h_states": True,
            "five_states_cover_48h": True,
        }
        crosswalk_case = {
            "scenario_id": "case-1",
            "split": "train",
            "feds": {
                "status": "unique_spatiotemporal_candidate",
                "selected": candidate,
            },
        }
        frame = {
            "schema_version": "fpa-feds-candidate-frame/1.0",
            "cohort_id": "test-frame",
            "case_count": 1,
            "cases": [frame_case],
            "candidate_frame": {
                "test_year_not_loaded": True,
                "filter": {"minimum_reported_fire_size_acres": 5000},
            },
        }
        crosswalk = {
            "schema_version": "fpa-feds-fle-crosswalk/1.0",
            "test_cases_loaded": False,
            "audited_splits": ["train", "validation"],
            "spatial_search_radius_m": 3000,
            "feds_start_date_window_days": {"before": 1, "after": 2},
            "pre_agent_data_gate": {
                "pass": True,
                "threshold": {
                    "train_two_state_minimum": 1,
                    "validation_two_state_minimum": 0,
                },
            },
            "cases": [crosswalk_case],
        }
        result = build_episode_manifest(
            frame, crosswalk, frame_sha256="a" * 64, crosswalk_sha256="b" * 64
        )
        case = result["cases"][0]
        self.assertNotIn("reported_final_area_acres_reference_only", case["event"])
        self.assertNotIn("mtbs_id_reference_only", case["event"])
        self.assertEqual(len(case["evaluation_reference"]["observed_state_times_0_to_48h"]), 5)
        self.assertIn("future FEDS state timestamps and geometries", result["information_boundary"]["evaluation_only"])

    def test_feds_fetcher_pins_integrity_and_rejects_test_year(self):
        from hashlib import md5
        from tempfile import TemporaryDirectory

        payload = b"small synthetic flatgeobuf fixture"
        checksum = md5(payload).hexdigest()

        class FakeResponse:
            headers = {"Content-Length": str(len(payload))}

            def __enter__(self):
                self.offset = 0
                return self

            def __exit__(self, *_args):
                return False

            def read(self, size):
                block = payload[self.offset : self.offset + size]
                self.offset += len(block)
                return block

        with TemporaryDirectory() as directory, patch(
            "scripts.fetch_feds_archive.FEDS_FILE_MD5",
            {"perimeter": {2018: checksum}, "fireline": {2018: checksum}},
        ), patch("scripts.fetch_feds_archive.urlopen", return_value=FakeResponse()):
            destination = fetch_archive(2018, "perimeter", Path(directory))
            self.assertEqual(destination.read_bytes(), payload)
            with self.assertRaisesRegex(ValueError, "test-year data are not fetched"):
                fetch_archive(2024, "perimeter", Path(directory))

    def test_feds_path_prefers_local_archive_and_falls_back_to_remote_ranges(self):
        with patch("scripts.audit_feds_fpa_fle_crosswalk.FEDS_LOCAL_CACHE", Path("/missing/feds-cache")):
            self.assertEqual(
                _feds_file_path(2018),
                "/vsicurl/https://zenodo.org/api/records/22921773/files/feds_2018_lf_perimeter.fgb/content",
            )
        with patch("scripts.audit_feds_fpa_fle_crosswalk.FEDS_LOCAL_CACHE", Path("/feds-cache")), patch(
            "scripts.audit_feds_fpa_fle_crosswalk.Path.is_file", return_value=True
        ), patch(
            "scripts.audit_feds_fpa_fle_crosswalk._md5_file", return_value="ad32170e694e42127f3b865d93e1a81a"
        ):
            self.assertEqual(_feds_file_path(2023), "/feds-cache/feds_2023_lf_perimeter.fgb")
        with patch("scripts.audit_feds_fpa_fle_crosswalk.FEDS_LOCAL_CACHE", Path("/feds-cache")), patch(
            "scripts.audit_feds_fpa_fle_crosswalk.Path.is_file", return_value=True
        ), patch(
            "scripts.audit_feds_fpa_fle_crosswalk._md5_file", return_value="51207e8d755e66adcc21030b645e9a0a"
        ):
            self.assertEqual(_feds_file_path(2018, "fireline"), "/feds-cache/feds_2018_lf_fireline.fgb")
        with patch("scripts.audit_feds_fpa_fle_crosswalk.FEDS_LOCAL_CACHE", Path("/feds-cache")), patch(
            "scripts.audit_feds_fpa_fle_crosswalk.Path.is_file", return_value=True
        ), patch("scripts.audit_feds_fpa_fle_crosswalk._md5_file", return_value="bad"):
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                _feds_file_path(2023)

    def test_portable_cohort_manifest_excludes_test_and_keeps_incidents_whole(self):
        path = Path(__file__).resolve().parents[1] / "data/manifests/fireline-benchmark-cohort-v1.json"
        cohort = json.loads(path.read_text())
        self.assertEqual(cohort["case_count"], 60)
        self.assertEqual(cohort["case_counts_by_split"], {"train": 40, "validation": 20})
        self.assertEqual({case["split"] for case in cohort["cases"]}, {"train", "validation"})
        self.assertTrue(all(case["reported_final_area_ha_reference_only"] > 0 for case in cohort["cases"]))
        self.assertTrue(all(case["mtbs_id_reference_only"] for case in cohort["cases"]))

    def test_broad_candidate_frame_is_train_validation_only_and_discovery_time_normalizes(self):
        path = Path(__file__).resolve().parents[1] / "data/manifests/fpa-feds-candidate-frame-v1.json"
        frame = json.loads(path.read_text())
        self.assertEqual(frame["case_count"], 264)
        self.assertEqual(frame["case_counts_by_split"], {"train": 208, "validation": 56})
        self.assertEqual({case["split"] for case in frame["cases"]}, {"train", "validation"})
        self.assertTrue(frame["candidate_frame"]["test_year_not_loaded"])
        case = next(case for case in frame["cases"] if case["discovery_time_hhmm"])
        self.assertEqual(
            _discovery_time_text(case),
            f"{case['discovery_date']} {case['discovery_time_hhmm']}",
        )
        date_only = dict(case, discovery_time_hhmm="")
        self.assertEqual(_discovery_time_text(date_only), case["discovery_date"])

    def test_timestamps_normalize_timezone_and_halfday_runs(self):
        first = parse_timestamp("2023-07-01T00:00:00Z")
        second = parse_timestamp("2023-07-01T12:00:00")
        third = parse_timestamp("2023-07-02T00:00:00")
        gap = parse_timestamp("2023-07-03T00:00:00")
        self.assertEqual(first, parse_timestamp("2023-07-01T02:00:00+02:00"))
        self.assertEqual(consecutive_halfday_run([first, second, third, gap]), 3)
        self.assertEqual(parse_discovery_date("2023-07-01 1200").isoformat(), "2023-07-01")
        self.assertEqual(parse_discovery_date("2023-07-01").isoformat(), "2023-07-01")

    @unittest.skipUnless(importlib.util.find_spec("shapely"), "optional geo extra is not installed")
    def test_feds_candidate_uses_start_date_and_point_not_reported_final_area(self):
        from shapely.geometry import box, mapping, shape

        class FakeCollection:
            def __init__(self, features):
                self.features = features

            def filter(self, bbox):
                query = box(*bbox)
                return [
                    feature
                    for feature in self.features
                    if shape(feature["geometry"]).intersects(query)
                ]

        class IdentityTransformer:
            @staticmethod
            def transform(longitude, latitude):
                return longitude, latitude

        features = []
        for offset, hour in enumerate((0, 12, 24, 36, 48)):
            from datetime import datetime, timedelta

            observed = datetime(2023, 7, 1) + timedelta(hours=hour)
            features.append(
                {
                    "geometry": mapping(box(-100, -100, 100, 100)),
                    "properties": {
                        "fireID": 123,
                        "t_st": "2023-07-01T00:00:00",
                        "t": observed.isoformat(),
                        "farea": 999999 if offset == 4 else offset + 1,
                        "n_newpixels": 2,
                        "t_ed": observed.isoformat(),
                    },
                }
            )
        features.append(
            {
                "geometry": mapping(box(0, 0, 100, 100)),
                "properties": {
                    "fireID": 456,
                    "t_st": "2023-07-01T00:00:00",
                    "t": "2023-07-20T00:00:00",
                    "farea": 3,
                },
            }
        )
        case = {
            "discovery_time": "2023-07-01 1200",
            "longitude": 0,
            "latitude": 0,
        }
        candidates = _feds_case_candidates(FakeCollection(features), IdentityTransformer(), case, 3000)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["fire_id"], "123")
        self.assertEqual(candidates[0]["longest_12h_run"], 5)
        self.assertTrue(candidates[0]["five_states_cover_48h"])

    @unittest.skipUnless(
        importlib.util.find_spec("fiona")
        and importlib.util.find_spec("pyproj")
        and importlib.util.find_spec("shapely"),
        "optional geo extra is not installed",
    )
    def test_feds_crosswalk_counts_event_states_after_fire_leaves_start_search_area(self):
        import fiona
        import pyproj
        from datetime import datetime, timedelta
        from shapely.geometry import box, mapping

        class FakeCollection:
            crs_wkt = "EPSG:9311"
            crs = None

            def __init__(self, features):
                self.features = features

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def filter(self, bbox):
                query = box(*bbox)
                return [
                    feature
                    for feature in self.features
                    if shape(feature["geometry"]).intersects(query)
                ]

            def __iter__(self):
                return iter(self.features)

        from shapely.geometry import shape

        features = []
        start = datetime(2023, 7, 1)
        for step in range(5):
            observed = start + timedelta(hours=12 * step)
            x = 0 if step == 0 else 5000 + step * 100
            features.append(
                {
                    "geometry": mapping(box(x, 0, x + 10, 10)),
                    "properties": {
                        "fireID": 123,
                        "t_st": start.isoformat(),
                        "t": observed.isoformat(),
                        "farea": step + 1,
                    },
                }
            )
        collection = FakeCollection(features)
        case = {
            "scenario_id": "fire-moving-away",
            "split": "train",
            "year": 2023,
            "discovery_date": "2023-07-01",
            "discovery_time_hhmm": "0000",
            "longitude": 0,
            "latitude": 0,
        }
        with patch("scripts.audit_feds_fpa_fle_crosswalk._feds_file_path", return_value="fake.fgb"), patch(
            "fiona.open", return_value=collection
        ), patch.object(pyproj.Transformer, "from_crs", return_value=type("T", (), {"transform": staticmethod(lambda x, y: (x, y))})()):
            result = _feds_crosswalk([case], 3000)[0]

        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["selected"]["observed_states_in_spatial_window"], 1)
        self.assertEqual(result["selected"]["event_observed_states"], 5)
        self.assertTrue(result["selected"]["two_consecutive_12h_states"])
        self.assertEqual(result["selected"]["episode_48h_state_count"], 5)
        self.assertTrue(result["selected"]["five_states_cover_48h"])

    def test_full_gate_passes_only_at_both_predeclared_thresholds(self):
        cases = [_case(index, "train") for index in range(20)]
        cases += [_case(index + 100, "validation") for index in range(8)]
        cohort = {"case_count": len(cases), "cases": cases, "source_cohort_commit": "abc"}

        def fake_feds(rows, _radius_m):
            return [
                {
                    "scenario_id": case["scenario_id"],
                    "status": "unique_spatiotemporal_candidate",
                    "candidate_count": 1,
                    "selected": {
                        "two_consecutive_12h_states": True,
                        "five_states_cover_48h": False,
                    },
                    "candidates": [],
                }
                for case in rows
            ]

        with patch("scripts.audit_feds_fpa_fle_crosswalk._feds_crosswalk", fake_feds), patch(
            "scripts.audit_feds_fpa_fle_crosswalk._fle_crosswalk", return_value={}
        ):
            report = run_audit(cohort, include_feds_metadata=False)
        self.assertIs(report["pre_agent_data_gate"]["pass"], True)
        self.assertEqual(report["pre_agent_data_gate"]["status"], "pass")
        self.assertFalse(report["test_cases_loaded"])

    def test_split_only_audit_is_incomplete_not_a_pass_or_full_failure(self):
        cases = [_case(index + 100, "validation") for index in range(8)]
        cohort = {"case_count": len(cases), "cases": cases}

        def fake_feds(rows, _radius_m):
            return [
                {
                    "scenario_id": case["scenario_id"],
                    "status": "unique_spatiotemporal_candidate",
                    "candidate_count": 1,
                    "selected": {
                        "two_consecutive_12h_states": True,
                        "five_states_cover_48h": False,
                    },
                    "candidates": [],
                }
                for case in rows
            ]

        with patch("scripts.audit_feds_fpa_fle_crosswalk._feds_crosswalk", fake_feds), patch(
            "scripts.audit_feds_fpa_fle_crosswalk._fle_crosswalk", return_value={}
        ):
            report = run_audit(
                cohort,
                include_feds_metadata=False,
                splits={"validation"},
                cohort_manifest="validation-only-manifest.json",
            )
        gate = report["pre_agent_data_gate"]
        self.assertIsNone(gate["pass"])
        self.assertEqual(gate["status"], "incomplete")
        self.assertEqual(report["audited_splits"], ["validation"])
        self.assertEqual(report["cohort_manifest"], "validation-only-manifest.json")

    def test_optional_fle_join_can_be_skipped_for_candidate_frame_audit(self):
        cases = [_case(index, "train") for index in range(1)]
        cohort = {"case_count": 1, "cases": cases}
        with patch(
            "scripts.audit_feds_fpa_fle_crosswalk._feds_crosswalk",
            return_value=[
                {
                    "scenario_id": cases[0]["scenario_id"],
                    "status": "no_candidate",
                    "candidate_count": 0,
                    "selected": None,
                    "candidates": [],
                }
            ],
        ), patch("scripts.audit_feds_fpa_fle_crosswalk._fle_crosswalk") as fle:
            report = run_audit(cohort, include_feds_metadata=False, include_fle=False)
        fle.assert_not_called()
        self.assertFalse(report["fle_crosswalk_included"])
        self.assertEqual(report["cases"][0]["feds"]["fle"], {})

    def test_test_cases_are_rejected_before_any_network_access(self):
        cohort = {"case_count": 1, "cases": [_case(1, "train"), _case(999, "test")]}
        with self.assertRaisesRegex(ValueError, "Test cases are locked"):
            run_audit(cohort, include_feds_metadata=False)

    def test_split_reports_combine_only_for_the_same_complete_cohort(self):
        train_case = _case(1, "train")
        validation_case = _case(101, "validation")

        def split_report(split, case, two_state_count):
            return {
                "schema_version": "fpa-feds-fle-crosswalk/1.0",
                "audited_splits": [split],
                "test_cases_loaded": False,
                "cohort_manifest": "cohort.json",
                "cohort_source_commit": "abc",
                "cohort_case_count": 2,
                "spatial_search_radius_m": 3000,
                "sources": {"feds": "zenodo"},
                "cases": [{"scenario_id": case["scenario_id"], "split": split}],
                "summary": {
                    split: {
                        "cases": 1,
                        "unique_feds_matches": two_state_count,
                        "two_consecutive_feds_states": two_state_count,
                        "full_48h_feds_reference": two_state_count,
                        "fle_summary_present": 0,
                    }
                },
                "pre_agent_data_gate": {
                    "threshold": {
                        "train_two_state_minimum": 1,
                        "validation_two_state_minimum": 1,
                    },
                    "pass": None,
                    "status": "incomplete",
                },
            }

        train_report = split_report("train", train_case, 1)
        validation_report = split_report("validation", validation_case, 1)
        validation_report["crosswalk_derivation"] = {"method": "offline_filter"}
        combined = combine_split_reports(train_report, validation_report)
        self.assertTrue(combined["pre_agent_data_gate"]["pass"])
        self.assertEqual(len(combined["cases"]), 2)
        self.assertEqual(combined["audited_splits"], ["train", "validation"])
        self.assertEqual(
            combined["split_report_provenance"]["validation"]["derivation"]["method"],
            "offline_filter",
        )

        other_cohort = split_report("validation", validation_case, 1)
        other_cohort["cohort_source_commit"] = "different"
        with self.assertRaisesRegex(ValueError, "disagree on cohort_source_commit"):
            combine_split_reports(split_report("train", train_case, 1), other_cohort)

    def test_saved_candidates_are_filtered_by_inclusive_first_24_hours(self):
        case = _case(101, "validation")

        def candidate(first, five_states):
            return {
                "fire_id": str(first),
                "t_start": "2023-07-01T00:00:00",
                "first_observed_state": first,
                "two_consecutive_12h_states": True,
                "five_states_cover_48h": five_states,
            }

        early = candidate("2023-07-02T00:00:00", True)
        late = candidate("2023-07-02T12:00:00", True)
        case["feds"] = {
            "status": "ambiguous_candidates",
            "candidate_count": 2,
            "candidates": [early, late],
            "selected": None,
            "fle": {"fle_summary_present": True},
        }
        report = {
            "schema_version": "fpa-feds-fle-crosswalk/1.0",
            "created_utc": "2026-11-02T00:00:00+00:00",
            "audited_splits": ["validation"],
            "test_cases_loaded": False,
            "cohort_case_count": 1,
            "summary": {"validation": {"cases": 1}},
            "cases": [case],
        }

        strict = filter_report_to_start_window(report, source_path="candidate.json")

        self.assertEqual(strict["cases"][0]["feds"]["candidates"], [early])
        self.assertEqual(strict["cases"][0]["feds"]["status"], "unique_spatiotemporal_candidate")
        self.assertEqual(strict["summary"]["validation"]["two_consecutive_feds_states"], 1)
        self.assertIsNone(strict["pre_agent_data_gate"]["pass"])
        self.assertEqual(strict["crosswalk_derivation"]["source_report"], "candidate.json")
        self.assertEqual(len(report["cases"][0]["feds"]["candidates"]), 2)


if __name__ == "__main__":
    unittest.main()
