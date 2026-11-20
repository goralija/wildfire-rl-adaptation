import unittest
try:
    import numpy as np
except ImportError:
    raise unittest.SkipTest('optional NumPy dependency is not installed')
from wildfire_rl.feds_repaired_learning import select_reference

class RepairedReferenceTests(unittest.TestCase):
    def test_reference_selection_cannot_see_outer_heldout_rewards(self):
        values=np.tile([10.,5.,0.],(10,1));self.assertEqual(select_reference(values,9),0)
        values[9]=[-1e9,1e9,5e8]
        self.assertEqual(select_reference(values,9),0)

    def test_reference_ties_follow_declared_order_and_invalid_index_is_rejected(self):
        self.assertEqual(select_reference(np.ones((10,3)),0),0)
        with self.assertRaises(ValueError):select_reference(np.ones((10,3)),10)

if __name__=='__main__':unittest.main()
