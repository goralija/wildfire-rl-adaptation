import unittest

try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest("optional NumPy dependency is not installed: %s" % exc)

from wildfire_rl.feds_spread_metrics import binary_burn_metrics


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

    def test_mask_shapes_and_empty_truth_are_rejected(self):
        with self.assertRaises(ValueError):
            binary_burn_metrics(np.zeros((2, 2)), np.zeros((3, 3)))
        with self.assertRaises(ValueError):
            binary_burn_metrics(np.zeros((2, 2)), np.zeros((2, 2)))


if __name__ == "__main__":
    unittest.main()
