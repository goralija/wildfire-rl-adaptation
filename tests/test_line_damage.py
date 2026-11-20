import unittest

try:
    import numpy as np
except ImportError:
    raise unittest.SkipTest("optional NumPy dependency is not installed")

from wildfire_rl.line_damage import score_line_damage


class LineDamageTests(unittest.TestCase):
    def test_only_new_noop_line_cells_are_charged_without_double_counting(self):
        # Cell 0 was already burned; cell 1 burns with the agent and is also line;
        # cell 2 is prevented from burning by line; cell 3 never burns under no-op.
        result = score_line_damage([[1, 0, 0, 0]], [[1, 1, 0, 0]],
                                   [[1, 1, 1, 0]], [[1, 1, 1, 1]])
        self.assertEqual(result["raw_damage_cells"], 1)
        self.assertEqual(result["line_cells_in_noop_footprint"], 2)
        self.assertEqual(result["extra_line_charge_cells"], 1)
        self.assertEqual(result["charged_damage_cells"], 2)
        self.assertEqual(result["raw_saved_cells"], 1)
        self.assertEqual(result["charged_saved_cells"], 0)

    def test_noop_and_no_line_are_unchanged(self):
        empty = np.zeros((3, 3), dtype=bool)
        burned = empty.copy()
        burned[1, 1] = True
        result = score_line_damage(empty, burned, burned, empty)
        self.assertEqual(result["raw_damage_cells"], 1)
        self.assertEqual(result["charged_damage_cells"], 1)
        self.assertEqual(result["charged_saved_cells"], 0)

    def test_previously_burned_line_does_not_erase_prior_damage(self):
        result = score_line_damage([[1, 0]], [[0, 0]], [[1, 1]], [[1, 0]])
        self.assertEqual(result["extra_line_charge_cells"], 0)
        self.assertEqual(result["charged_saved_cells"], 1)

    def test_line_charge_is_a_union_not_an_additive_area_penalty(self):
        result = score_line_damage([[0, 0]], [[1, 1]], [[1, 0]], [[1, 1]])
        self.assertEqual(result["charged_damage_cells"], 2)
        self.assertEqual(result["charged_saved_cells"], -1)

    def test_masks_must_be_binary_and_have_equal_two_dimensional_shapes(self):
        for bad in ([[2]], [[float("nan")]], [0], [[0, 1]]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                score_line_damage([[0]], bad, [[0]], [[0]])


if __name__ == "__main__":
    unittest.main()
