import unittest
from pathlib import Path

import numpy as np

from scripts.analyze_cfsds_replay_timeline import grid_metrics, selected_timeline


class CFSDSReplayTimelineTests(unittest.TestCase):
    def test_grid_metrics_use_fractional_target_area_and_exclude_initial_burn(self):
        initial = np.array([[True, False], [False, False]])
        grid = np.array([[1, 1], [1, 0]])
        target = np.array([[1.0, 0.5], [0.0, 0.0]])
        result = grid_metrics(grid, initial, target, cell_size_m=100)
        self.assertEqual(result["predicted_new_area_ha"], 2.0)
        self.assertEqual(result["target_area_ha"], 1.5)
        self.assertEqual(result["overlap_with_target_ha"], 0.5)
        self.assertEqual(result["precision"], 0.25)
        self.assertEqual(result["recall"], 0.3333)
        self.assertEqual(result["iou"], 0.1667)

    def test_checkpoints_select_latest_saved_snapshot_without_looking_ahead(self):
        grids = {0: Path("grid0.csv"), 11: Path("grid11.csv"), 21: Path("grid21.csv")}
        result = selected_timeline(grids, [20, 0, 15])
        self.assertEqual(
            [(item["requested_elapsed_minutes"], item["grid_index"]) for item in result],
            [(0, 0), (15, 11), (20, 21)],
        )

    def test_invalid_grid_shapes_and_negative_checkpoints_are_rejected(self):
        with self.assertRaises(ValueError):
            grid_metrics(np.zeros((2, 2)), np.zeros((1, 2)), np.zeros((2, 2)), 100)
        with self.assertRaises(ValueError):
            selected_timeline({0: Path("grid0.csv")}, [-1])


if __name__ == "__main__":
    unittest.main()
