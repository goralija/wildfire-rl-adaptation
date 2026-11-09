import importlib.util
import unittest

from wildfire_rl.simfire_initial_state import compose_initial_fire_map, update_cumulative_burned


@unittest.skipUnless(importlib.util.find_spec("numpy"), "NumPy is an optional simulator dependency")
class SimFireInitialStateTests(unittest.TestCase):
    def test_initial_state_imports_burned_interior_and_multiple_active_front_cells(self):
        import numpy as np

        scar = np.zeros((5, 6), dtype=bool)
        scar[1:4, 1:5] = True
        front = np.zeros_like(scar)
        front[1, 2:5] = True
        front[2, 1] = True

        fire_map = compose_initial_fire_map(scar, front)

        self.assertEqual(np.count_nonzero(fire_map == 2), np.count_nonzero(scar & ~front))
        self.assertEqual(np.count_nonzero(fire_map == 1), 4)
        self.assertEqual(fire_map[3, 4], 2)
        self.assertEqual(fire_map[1, 2], 1)

    def test_burned_cells_remain_cumulative_after_fire_manager_state_changes(self):
        import numpy as np

        original_scar = np.zeros((4, 4), dtype=bool)
        original_scar[1, 1] = True
        current_map = np.zeros((4, 4), dtype=np.uint8)
        current_map[2, 2] = 1

        cumulative = update_cumulative_burned(original_scar, current_map)

        self.assertTrue(cumulative[1, 1])
        self.assertTrue(cumulative[2, 2])
        self.assertEqual(np.count_nonzero(cumulative), 2)

    def test_initial_state_rejects_shape_mismatch_or_empty_front(self):
        import numpy as np

        scar = np.zeros((3, 3), dtype=bool)
        with self.assertRaisesRegex(ValueError, "same two-dimensional shape"):
            compose_initial_fire_map(scar, np.zeros((2, 3), dtype=bool))
        with self.assertRaisesRegex(ValueError, "at least one active-front cell"):
            compose_initial_fire_map(scar, np.zeros_like(scar))


if __name__ == "__main__":
    unittest.main()
