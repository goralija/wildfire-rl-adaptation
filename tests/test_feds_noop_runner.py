"""Tests for TRAIN-only post-hoc perimeter loading in the FEDS no-op runner."""

from __future__ import annotations

import unittest
from unittest.mock import patch

try:
    import fiona  # noqa: F401
    import rasterio  # noqa: F401
    import shapely  # noqa: F401
except ImportError:
    HAS_GEOSPATIAL = False
else:
    HAS_GEOSPATIAL = True


@unittest.skipUnless(HAS_GEOSPATIAL, "SimFire geospatial dependencies are optional")
class FedsNoopRunnerTests(unittest.TestCase):
    def test_observed_timeline_uses_flatgeobuf_spatial_filter(self):
        from scripts import audit_feds_fpa_fle_crosswalk as audit
        from scripts.run_feds_noop_episode import load_observed_timeline

        times = [
            "2018-01-01T00:00:00",
            "2018-01-01T12:00:00",
            "2018-01-02T00:00:00",
            "2018-01-02T12:00:00",
            "2018-01-03T00:00:00",
        ]
        polygon = {
            "type": "Polygon",
            "coordinates": [[
                [0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]
            ]],
        }
        features = [
            {"properties": {"fireID": 1, "t": timestamp}, "geometry": polygon}
            for timestamp in times
        ]

        class FakeSource:
            crs_wkt = "EPSG:4326"
            crs = None

            def __init__(self):
                self.query_bbox = None

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def filter(self, *, bbox):
                self.query_bbox = bbox
                return iter(features)

            def __iter__(self):
                raise AssertionError("the full annual FEDS layer must not be scanned")

        source = FakeSource()
        case = {
            "scenario_id": "train-test",
            "event": {"year": 2018},
            "evaluation_reference": {
                "source_fire_id": "1",
                "observed_state_times_0_to_48h": times,
            },
        }
        grid = {
            "crs": "EPSG:4326",
            "shape": [4, 4],
            "raster_transform": [1, 0, 0, 0, -1, 4],
        }
        with patch.object(audit, "_feds_file_path", return_value="unused.fgb"):
            with patch("fiona.open", return_value=source):
                timeline = load_observed_timeline(case, grid)

        self.assertEqual(len(timeline), 5)
        self.assertEqual(source.query_bbox, (0.0, 0.0, 4.0, 4.0))
        self.assertTrue(all(item["mask"].shape == (4, 4) for item in timeline))
        self.assertTrue(all(item["mask"].any() for item in timeline))


if __name__ == "__main__":
    unittest.main()
