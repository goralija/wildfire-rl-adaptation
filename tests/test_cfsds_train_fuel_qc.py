from __future__ import annotations

import importlib.util
import unittest

_optional = ("numpy", "pandas", "rasterio", "scipy")
_missing = [name for name in _optional if importlib.util.find_spec(name) is None]
if _missing:
    raise unittest.SkipTest(f"optional geo dependencies missing: {', '.join(_missing)}")

import numpy as np

from scripts.audit_cfsds_train_fuel import (
    category_for_fuel,
    derive_day_pair_masks,
    summarize_mask,
)


class CFSDSFuelQCTests(unittest.TestCase):
    def test_day_pair_masks_separate_scar_front_target_and_spots(self) -> None:
        arrival = np.zeros((5, 5), dtype=np.uint32)
        arrival[0, 0] = 1  # earlier scar
        arrival[2, 2] = 6  # day n-1; adjacent front
        arrival[3, 3] = 7  # connected day n target
        arrival[0, 4] = 7  # disconnected day n spot

        masks, counts = derive_day_pair_masks(arrival, 7)

        self.assertTrue(masks["scar"][0, 0])
        self.assertTrue(masks["front"][2, 2])
        self.assertTrue(masks["target"][3, 3])
        self.assertFalse(masks["target"][0, 4])
        self.assertEqual(counts["disconnected_target_pixels"], 1)

    def test_fuel_categories_match_builder_nonfuel_codes(self) -> None:
        mapping = {1: 3, 2: 102, 3: 101, 4: 105}
        labels = {
            "1": {"source_label": "C3"},
            "2": {"source_label": "Water"},
            "3": {"source_label": "Non-fuel"},
            "4": {"source_label": "Veg non-fuel"},
        }

        self.assertEqual(category_for_fuel(1, mapping, labels), "burnable")
        self.assertEqual(category_for_fuel(2, mapping, labels), "water")
        self.assertEqual(category_for_fuel(3, mapping, labels), "nonfuel")
        self.assertEqual(category_for_fuel(4, mapping, labels), "ambiguous")
        self.assertEqual(category_for_fuel(0, mapping, labels), "unmapped")

    def test_reports_native_overlap_and_fractional_model_overlap(self) -> None:
        native_mask = np.array([[True, True], [False, False]])
        native_fuel = np.array([[1, 2], [1, 1]], dtype=np.uint16)
        native_categories = np.array([["burnable", "water"], ["burnable", "burnable"]])
        fraction = np.array([[1.0, 0.2], [0.0, 0.0]], dtype=np.float32)
        model_fuel = np.array([[1, 2], [1, 1]], dtype=np.uint16)
        model_categories = np.array([["burnable", "water"], ["burnable", "burnable"]])

        result = summarize_mask(
            "target", native_mask, native_fuel, native_categories,
            fraction, model_fuel, model_categories,
        )

        self.assertEqual(result["native_90m"]["excluded_or_unmapped_pixels"], 1)
        self.assertEqual(result["model_100m"]["excluded_or_unmapped_majority_cells"], 0)
        self.assertAlmostEqual(
            result["model_100m"]["fractional_area_equivalent_ha_by_fuel_category"]["water"],
            0.2,
        )
        self.assertFalse(result["strict_fuel_compatibility"])


if __name__ == "__main__":
    unittest.main()
