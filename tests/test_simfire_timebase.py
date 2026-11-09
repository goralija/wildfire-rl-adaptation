import unittest

from wildfire_rl.simfire_timebase import updates_for_duration


class SimFireTimebaseTests(unittest.TestCase):
    def test_preserves_ninety_minute_active_lifetime_at_coarser_steps(self):
        self.assertEqual(updates_for_duration(90, 1), 90)
        self.assertEqual(updates_for_duration(90, 5), 18)
        self.assertEqual(updates_for_duration(90, 10), 9)
        self.assertGreaterEqual(7 * updates_for_duration(90, 7), 90)

    def test_rejects_nonpositive_or_nonfinite_duration(self):
        for duration, step in ((0, 1), (10, 0), (-1, 1), (1, -1), (float("inf"), 1)):
            with self.subTest(duration=duration, step=step):
                with self.assertRaises(ValueError):
                    updates_for_duration(duration, step)


if __name__ == "__main__":
    unittest.main()
