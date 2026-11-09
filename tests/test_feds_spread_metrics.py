import unittest

try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest("optional NumPy dependency is not installed: %s" % exc)

from wildfire_rl.feds_spread_metrics import (
    binary_burn_metrics,
    elliptical_growth_reference,
    growth_overlap_metrics,
)


class FedsSpreadMetricTests(unittest.TestCase):
    def test_overlap_area_cumulative_damage_and_edge_counts(self):
        predicted = np.zeros((4, 4), dtype=bool)
        observed = np.zeros((4, 4), dtype=bool)
        initial = np.zeros((4, 4), dtype=bool)
        predicted[1, 1] = True
        predicted[0, 1] = True
        observed[1, 1] = True
        observed[1, 2] = True
        initial[1, 1] = True

        metrics = binary_burn_metrics(predicted, observed, initial_burn=initial)

        self.assertEqual(metrics["intersection_cells"], 1)
        self.assertEqual(metrics["union_cells"], 3)
        self.assertAlmostEqual(metrics["iou"], 1 / 3)
        self.assertEqual(metrics["new_burned_cells_since_initial"], 1)
        self.assertAlmostEqual(metrics["new_burned_area_ha"], 3.24)
        self.assertEqual(metrics["edge_cells"], 1)
        self.assertTrue(metrics["touches_map_edge"])

    def _growth_case(self):
        initial = np.zeros((6, 6), dtype=bool)
        initial[1:4, 1:4] = True
        observed = initial.copy()
        observed[1:4, 4] = True
        return initial, observed

    def test_prediction_equal_to_initial_has_zero_growth_iou(self):
        initial, observed = self._growth_case()

        metrics = binary_burn_metrics(initial, observed, initial_burn=initial)

        self.assertAlmostEqual(metrics["iou"], 9 / 12)
        self.assertEqual(metrics["predicted_growth_cells"], 0)
        self.assertEqual(metrics["observed_growth_cells"], 3)
        self.assertEqual(metrics["growth_intersection_cells"], 0)
        self.assertEqual(metrics["growth_iou"], 0.0)
        self.assertEqual(metrics["growth_recall"], 0.0)
        self.assertIsNone(metrics["growth_precision"])

    def test_perfect_growth_has_unit_growth_metrics(self):
        initial, observed = self._growth_case()

        metrics = binary_burn_metrics(observed.copy(), observed, initial_burn=initial)

        self.assertEqual(metrics["growth_iou"], 1.0)
        self.assertEqual(metrics["growth_precision"], 1.0)
        self.assertEqual(metrics["growth_recall"], 1.0)

    def test_shared_initial_burn_does_not_inflate_growth_iou(self):
        initial, observed = self._growth_case()
        predicted = initial.copy()
        predicted[4, 1:4] = True  # grows south while FEDS grows east

        metrics = binary_burn_metrics(predicted, observed, initial_burn=initial)

        self.assertAlmostEqual(metrics["iou"], 9 / 15)
        self.assertEqual(metrics["growth_iou"], 0.0)
        self.assertEqual(metrics["growth_precision"], 0.0)
        self.assertEqual(metrics["growth_recall"], 0.0)

    def test_growth_metrics_are_undefined_when_neither_mask_grows(self):
        initial, _ = self._growth_case()

        metrics = binary_burn_metrics(initial, initial, initial_burn=initial)

        self.assertEqual(metrics["iou"], 1.0)
        self.assertEqual(metrics["observed_growth_cells"], 0)
        self.assertIsNone(metrics["growth_iou"])
        self.assertIsNone(metrics["growth_precision"])
        self.assertIsNone(metrics["growth_recall"])

    def test_growth_excludes_initial_cells_missing_from_the_observation(self):
        initial, observed = self._growth_case()
        observed[1, 1] = False  # FEDS outline leaves out one initial cell
        predicted = initial.copy()
        predicted[2, 4] = True

        metrics = binary_burn_metrics(predicted, observed, initial_burn=initial)

        self.assertEqual(metrics["observed_growth_cells"], 3)
        self.assertEqual(metrics["growth_intersection_cells"], 1)
        self.assertAlmostEqual(metrics["growth_iou"], 1 / 3)
        self.assertEqual(metrics["growth_precision"], 1.0)
        self.assertAlmostEqual(metrics["growth_recall"], 1 / 3)

    def test_growth_overlap_from_counts_matches_masks_and_rejects_bad_counts(self):
        self.assertEqual(
            growth_overlap_metrics(1, 1, 3),
            {"growth_iou": 1 / 3, "growth_precision": 1.0, "growth_recall": 1 / 3},
        )
        self.assertEqual(
            growth_overlap_metrics(0, 0, 0),
            {"growth_iou": None, "growth_precision": None, "growth_recall": None},
        )
        with self.assertRaises(ValueError):
            growth_overlap_metrics(2, 1, 3)
        with self.assertRaises(ValueError):
            growth_overlap_metrics(-1, 1, 3)

    def test_mask_shapes_and_empty_truth_are_rejected(self):
        with self.assertRaises(ValueError):
            binary_burn_metrics(np.zeros((2, 2)), np.zeros((3, 3)))
        with self.assertRaises(ValueError):
            binary_burn_metrics(np.zeros((2, 2)), np.zeros((2, 2)))

    def test_predeclared_ellipse_expands_downwind_and_preserves_initial_burn(self):
        initial = np.zeros((9, 9), dtype=bool)
        initial[4, 4] = True

        at_12h = elliptical_growth_reference(
            initial, center_row=4, center_column=4, hours=12, downwind_degrees=0
        )
        at_24h = elliptical_growth_reference(
            initial, center_row=4, center_column=4, hours=24, downwind_degrees=0
        )

        self.assertTrue(at_12h[4, 4])
        self.assertTrue(at_12h[3, 4])
        self.assertFalse(at_12h[4, 5])
        self.assertFalse(at_12h[5, 4])
        # The head of a rear-focus ellipse reaches (1 + sqrt(3)/2) * 360 m = 672 m at 24h.
        self.assertTrue(at_24h[1, 4])
        self.assertFalse(at_24h[5, 4])
        self.assertGreater(int(at_24h.sum()), int(at_12h.sum()))

    def _single_cell_ellipse(self, heading, hours=48):
        initial = np.zeros((41, 41), dtype=bool)
        initial[20, 20] = True
        return elliptical_growth_reference(
            initial, center_row=20, center_column=20, hours=hours, downwind_degrees=heading
        )

    def test_ellipse_heading_and_its_reverse_give_different_masks(self):
        for heading in (0.0, 90.0, 137.0, 250.0):
            with self.subTest(heading=heading):
                forward = self._single_cell_ellipse(heading)
                reverse = self._single_cell_ellipse(heading + 180.0)
                self.assertFalse(np.array_equal(forward, reverse))

    def test_ellipse_head_extends_further_downwind_than_upwind(self):
        north = self._single_cell_ellipse(0.0)
        rows = np.where(north.any(axis=1))[0]
        downwind_cells = 20 - int(rows.min())
        upwind_cells = int(rows.max()) - 20
        # 48h: semi-major 720 m, head 1343 m (7 cells), back 96 m (under one cell).
        self.assertEqual(downwind_cells, 7)
        self.assertEqual(upwind_cells, 0)
        self.assertTrue(np.array_equal(self._single_cell_ellipse(180.0), np.flipud(north)))

        east = self._single_cell_ellipse(90.0)
        self.assertTrue(east[20, 27])
        self.assertFalse(east[20, 13])

        northeast = self._single_cell_ellipse(45.0)
        rows, columns = np.where(northeast)
        upper_right = int(np.count_nonzero((rows < 20) & (columns > 20)))
        lower_left = int(np.count_nonzero((rows > 20) & (columns < 20)))
        self.assertGreater(upper_right, 0)
        self.assertEqual(lower_left, 0)

    def test_ignition_point_is_the_leading_edge_of_a_ring_front(self):
        from wildfire_rl.feds_spread_metrics import ellipse_ignition_point

        rows, columns = np.indices((41, 41))
        distance = np.hypot(rows - 20, columns - 20)
        scar = distance <= 15
        front = (distance <= 15) & (distance > 14)
        # Heading east (90 degrees): the leading edge is the eastern rim, not the centre.
        row, column = ellipse_ignition_point(front, 90.0)
        self.assertAlmostEqual(row, 20.0, places=6)
        self.assertGreaterEqual(column, 34.5)
        # From the centroid the 12h ellipse adds nothing; from the leading edge it grows.
        centred = elliptical_growth_reference(scar, center_row=20.0, center_column=20.0,
                                              hours=12, downwind_degrees=90.0)
        leading = elliptical_growth_reference(scar, center_row=row, center_column=column,
                                              hours=12, downwind_degrees=90.0)
        self.assertEqual(int((centred & ~scar).sum()), 0)
        self.assertGreater(int((leading & ~scar).sum()), 0)
        # North heading picks the northern rim (row 0 is north).
        north_row, _ = ellipse_ignition_point(front, 0.0)
        self.assertLessEqual(north_row, 5.5)
        with self.assertRaises(ValueError):
            ellipse_ignition_point(np.zeros((3, 3), dtype=bool), 0.0)

    def test_ellipse_rejects_invalid_grid_and_time_parameters(self):
        initial = np.zeros((3, 3), dtype=bool)
        with self.assertRaises(ValueError):
            elliptical_growth_reference(
                initial, center_row=1, center_column=1, hours=-1, downwind_degrees=0
            )
        with self.assertRaises(ValueError):
            elliptical_growth_reference(
                initial, center_row=1, center_column=1, hours=12,
                downwind_degrees=0, semi_major_growth_m_per_12h=0
            )


if __name__ == "__main__":
    unittest.main()
