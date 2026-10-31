from __future__ import annotations

import importlib.util
import unittest

OPTIONAL_RESEARCH_PACKAGES = ("numpy", "pandas", "pyproj", "rasterio", "scipy")
MISSING_RESEARCH_PACKAGES = [
    package for package in OPTIONAL_RESEARCH_PACKAGES
    if importlib.util.find_spec(package) is None
]
if MISSING_RESEARCH_PACKAGES:
    raise unittest.SkipTest(
        f"optional research dependencies are unavailable: {MISSING_RESEARCH_PACKAGES}"
    )

import numpy as np

from scripts.cfsds_initial_state import (
    NODATA_ARRIVAL,
    derive_pre_target_state_masks,
    initial_state_cells,
    select_target_blind_window,
)
from scripts.profile_cfsds_cohort import find_window


class CFSDSInitialStateTests(unittest.TestCase):
    def test_initial_input_is_invariant_to_target_mask_changes(self) -> None:
        arrival_a = np.full((40, 40), NODATA_ARRIVAL, dtype=np.uint32)
        arrival_a[5:26, 5:26] = 210
        arrival_a[10:20, 10:20] = 227
        arrival_a[26:29, 22:25] = 228

        arrival_b = arrival_a.copy()
        arrival_b[arrival_b == 228] = NODATA_ARRIVAL
        arrival_b[1:4, 1:4] = 228

        window_a = select_target_blind_window(arrival_a, 228)
        window_b = select_target_blind_window(arrival_b, 228)
        screened_a = find_window(arrival_a, 228, 23)
        screened_b = find_window(arrival_b, 228, 23)

        self.assertIsNotNone(window_a)
        self.assertIsNotNone(window_b)
        self.assertIsNotNone(screened_a)
        self.assertIsNotNone(screened_b)
        self.assertEqual(window_a, window_b)
        assert screened_a is not None and screened_b is not None
        self.assertEqual((screened_a["row_off"], screened_a["col_off"]), (screened_b["row_off"], screened_b["col_off"]))
        self.assertFalse(screened_a["target_geometry_used_for_window_selection"])
        self.assertFalse(screened_a["target_geometry_used_for_candidate_ranking"])
        assert window_a is not None and window_b is not None
        row, col = window_a["row_off"], window_a["col_off"]
        crop_a = arrival_a[row:row + 23, col:col + 23]
        crop_b = arrival_b[row:row + 23, col:col + 23]
        masks_a = derive_pre_target_state_masks(crop_a, 228)
        masks_b = derive_pre_target_state_masks(crop_b, 228)
        np.testing.assert_array_equal(masks_a["scar"], masks_b["scar"])
        np.testing.assert_array_equal(masks_a["front"], masks_b["front"])

        self.assertEqual(
            initial_state_cells(masks_a["scar"], masks_a["front"]),
            initial_state_cells(masks_b["scar"], masks_b["front"]),
        )
        self.assertFalse(np.array_equal(arrival_a == 228, arrival_b == 228))

    def test_safe_interior_day_n_minus_one_is_front_and_crop_edge_is_scar(self) -> None:
        arrival = np.zeros((7, 7), dtype=np.uint32)
        arrival[2, 2] = 226
        arrival[3, 3] = 227
        arrival[0, 4] = 227
        arrival[4, 4] = 228

        masks = derive_pre_target_state_masks(arrival, 228)

        self.assertTrue(masks["scar"][2, 2])
        self.assertTrue(masks["front"][3, 3])
        self.assertTrue(masks["scar"][0, 4])
        self.assertFalse(masks["front"][0, 4])
        self.assertFalse(masks["scar"][4, 4])
        self.assertFalse(masks["front"][4, 4])

    def test_target_blind_window_centers_on_day_n_minus_one_centroid(self) -> None:
        arrival = np.full((32, 32), NODATA_ARRIVAL, dtype=np.uint32)
        arrival[4:27, 4:27] = 220
        arrival[8:22, 8:22] = 227
        arrival[25:28, 25:28] = 228

        selected = select_target_blind_window(arrival, 228, tile_size=23)

        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertGreaterEqual(selected["day_n_minus_1_front_pixels_in_window"], 3)
        self.assertEqual(selected["day_n_minus_1_centroid_to_window_center_px"], 0.707107)
        self.assertEqual(
            selected["day_n_minus_1_pixels_in_window"],
            selected["day_n_minus_1_front_pixels_in_window"]
            + selected["day_n_minus_1_border_pixels_as_burnt_scar"],
        )

    def test_initial_state_serialization_is_row_major_and_disjoint(self) -> None:
        scar = np.array([[True, False], [False, False]])
        front = np.array([[False, True], [False, True]])

        self.assertEqual(
            initial_state_cells(scar, front),
            [("burnt", 1), ("burning", 2), ("burning", 4)],
        )
        with self.assertRaisesRegex(ValueError, "must not overlap"):
            initial_state_cells(np.array([[True]]), np.array([[True]]))

    def test_explicit_nonfuel_scar_serializes_separately_from_active_front(self) -> None:
        scar = np.array([[True, True], [False, False]])
        front = np.array([[False, False], [False, True]])
        nonfuel_scar = np.array([[True, False], [False, False]])

        self.assertEqual(
            initial_state_cells(scar, front, nonfuel_scar=nonfuel_scar),
            [("scar_nf", 1), ("burnt", 2), ("burning", 4)],
        )

    def test_nonfuel_scar_serialization_requires_explicit_prior_burnt_cell(self) -> None:
        with self.assertRaisesRegex(ValueError, "subset of burnt"):
            initial_state_cells(
                np.array([[False, False]]),
                np.array([[False, False]]),
                nonfuel_scar=np.array([[True, False]]),
            )

    def test_invalid_rasters_and_days_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "two-dimensional"):
            select_target_blind_window(np.array([1, 2]), 2)
        with self.assertRaisesRegex(ValueError, "target_doy"):
            select_target_blind_window(np.zeros((23, 23)), 1)
        with self.assertRaisesRegex(ValueError, "edge_margin_cells"):
            derive_pre_target_state_masks(np.zeros((2, 2)), 2)


if __name__ == "__main__":
    unittest.main()
