from __future__ import annotations

import importlib.util
import unittest

if importlib.util.find_spec("numpy") is None:
    raise unittest.SkipTest("numpy is an optional research dependency")

import numpy as np

from scripts.cfsds_fuel_vintage import (
    NODATA_ARRIVAL,
    pre_target_burn_mask,
    select_train_candidate,
)


class CFSDSFuelVintageTests(unittest.TestCase):
    def test_pre_target_mask_includes_day_before_but_excludes_target_and_future(self) -> None:
        arrival = np.array([[0, 225, 226, 227, 228, 229, NODATA_ARRIVAL]], dtype=np.uint32)

        selected = pre_target_burn_mask(arrival, 228)

        np.testing.assert_array_equal(
            selected,
            np.array([[False, True, True, True, False, False, False]]),
        )

    def test_mask_does_not_modify_input_and_is_boolean(self) -> None:
        arrival = np.array([[1, 4_000_000_000]], dtype=np.uint32)
        original = arrival.copy()

        selected = pre_target_burn_mask(arrival, 2)

        self.assertEqual(selected.dtype, np.dtype(bool))
        np.testing.assert_array_equal(arrival, original)

    def test_invalid_raster_or_day_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "two-dimensional"):
            pre_target_burn_mask(np.array([1, 2]), 2)
        with self.assertRaisesRegex(ValueError, "target_doy"):
            pre_target_burn_mask(np.array([[1]]), 0)
        with self.assertRaisesRegex(ValueError, "nodata"):
            pre_target_burn_mask(np.array([[1]]), 2, nodata=2)

    def test_candidate_selector_rejects_non_train_splits(self) -> None:
        candidates = [
            {"event_id": "train-1", "split": "train"},
            {"event_id": "validation-1", "split": "validation"},
            {"event_id": "test-1", "split": "test"},
        ]

        self.assertEqual(select_train_candidate(candidates, "train-1")["split"], "train")
        for event_id in ("validation-1", "test-1"):
            with self.subTest(event_id=event_id), self.assertRaisesRegex(ValueError, "Refusing non-train"):
                select_train_candidate(candidates, event_id)
        with self.assertRaisesRegex(ValueError, "Expected one screen row"):
            select_train_candidate(candidates, "missing")


if __name__ == "__main__":
    unittest.main()
