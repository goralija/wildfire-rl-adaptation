from __future__ import annotations

import unittest

try:
    import numpy as np
except ImportError as exc:  # pragma: no cover - optional research dependency
    raise unittest.SkipTest("numpy is required for CFSDS spatial-feasibility tests") from exc

from scripts.cfsds_initial_state import NODATA_ARRIVAL
from scripts.cfsds_spatial_feasibility import (
    evaluate_target_blind_window,
    native_window_shape,
)


class CFSDSSpatialFeasibilityTests(unittest.TestCase):
    def test_native_window_covers_requested_ground_extent(self) -> None:
        self.assertEqual(native_window_shape(20, 20, 100), (23, 23))
        self.assertEqual(native_window_shape(20, 20, 200), (45, 45))
        self.assertEqual(native_window_shape(40, 40, 100), (45, 45))

    def test_window_and_pre_target_metrics_do_not_depend_on_target_mask(self) -> None:
        arrival_a = np.full((80, 80), NODATA_ARRIVAL, dtype=np.uint32)
        arrival_a[10:61, 10:61] = 98
        arrival_a[35:46, 35:46] = 99
        arrival_a[43:52, 39:49] = 100

        arrival_b = arrival_a.copy()
        arrival_b[arrival_b == 100] = NODATA_ARRIVAL
        arrival_b[66:72, 66:72] = 100

        result_a = evaluate_target_blind_window(
            arrival_a,
            100,
            grid_rows=20,
            grid_cols=20,
            cell_size_m=100,
        )
        result_b = evaluate_target_blind_window(
            arrival_b,
            100,
            grid_rows=20,
            grid_cols=20,
            cell_size_m=100,
        )

        invariant_keys = (
            "window_found",
            "row_off",
            "col_off",
            "pre_target_pixels_in_window",
            "day_n_minus_1_front_pixels_total",
            "day_n_minus_1_front_pixels_in_window",
            "day_n_minus_1_front_pixels_in_safe_interior",
        )
        for key in invariant_keys:
            self.assertEqual(result_a[key], result_b[key], key)
        self.assertNotEqual(result_a["target_pixels_total"], result_b["target_pixels_total"])
        self.assertNotEqual(result_a["target_pixels_in_window"], result_b["target_pixels_in_window"])
        self.assertFalse(result_a["target_geometry_used_for_window_selection"])

    def test_window_that_cannot_fit_is_reported_without_target_scoring(self) -> None:
        arrival = np.full((30, 30), NODATA_ARRIVAL, dtype=np.uint32)
        arrival[10:20, 10:20] = 99
        arrival[18:23, 18:23] = 100
        result = evaluate_target_blind_window(
            arrival,
            100,
            grid_rows=40,
            grid_cols=40,
            cell_size_m=100,
        )
        self.assertFalse(result["window_found"])
        self.assertFalse(result["target_geometry_used_for_window_selection"])
        self.assertNotIn("target_capture_ratio", result)


if __name__ == "__main__":
    unittest.main()
