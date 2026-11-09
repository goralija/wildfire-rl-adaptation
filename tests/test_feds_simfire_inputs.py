"""Regression checks for the fixed-resolution FEDS-to-SimFire input grid."""

from __future__ import annotations

import unittest

from wildfire_rl.feds_simfire_inputs import (
    centered_grid_spec,
    grid_covers_geometry,
    utm_crs_for_lon_lat,
)


class _Bounds:
    def __init__(self, bounds):
        self.bounds = bounds


class FedsSimfireGridTests(unittest.TestCase):
    def test_western_us_coordinate_gets_expected_utm_zone(self):
        self.assertEqual(utm_crs_for_lon_lat(-108.47, 37.65), "EPSG:32612")

    def test_grid_is_256_cells_at_180m_and_centered(self):
        grid = centered_grid_spec(1000.0, -2000.0, crs="EPSG:32612")
        self.assertEqual((grid.rows, grid.columns), (256, 256))
        self.assertEqual(grid.resolution_m, 180.0)
        self.assertEqual(grid.bounds_m, (-22040.0, -25040.0, 24040.0, 21040.0))

    def test_full_initial_geometry_must_fit_without_crop(self):
        grid = centered_grid_spec(0.0, 0.0, crs="EPSG:32612")
        self.assertTrue(grid_covers_geometry(grid, _Bounds((-20000, -20000, 20000, 20000))))
        self.assertFalse(grid_covers_geometry(grid, _Bounds((-24000, -20000, 20000, 20000))))

    def test_perimeter_and_front_rasterize_to_nonempty_same_grid_masks(self):
        try:
            from shapely.geometry import LineString, box
            from wildfire_rl.feds_simfire_inputs import rasterize_observed_masks
        except ImportError as exc:  # pragma: no cover - optional GIS runtime
            self.skipTest(f"optional GIS dependencies unavailable: {exc}")
        grid = centered_grid_spec(0.0, 0.0, crs="EPSG:32612")
        scar, front, transform = rasterize_observed_masks(
            grid,
            box(-900, -900, 900, 900),
            LineString([(-1000, 1000), (1000, -1000)]),
        )
        self.assertEqual(scar.shape, (256, 256))
        self.assertEqual(front.shape, (256, 256))
        self.assertGreater(int(scar.sum()), 0)
        self.assertGreater(int(front.sum()), 0)
        self.assertEqual(tuple(transform)[:6], (180.0, 0.0, -23040.0, 0.0, -180.0, 23040.0))


if __name__ == "__main__":
    unittest.main()
