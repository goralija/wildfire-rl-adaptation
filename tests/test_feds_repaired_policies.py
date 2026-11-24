import importlib.util
import unittest
if not importlib.util.find_spec('numpy') or not importlib.util.find_spec('gymnasium'):
    raise unittest.SkipTest('optional NumPy/Gymnasium dependencies are not installed')
import numpy as np
from wildfire_rl.feds_repaired_policies import make_repaired_heuristic

class RepairedPolicyTests(unittest.TestCase):
    def test_fine_front_policy_uses_current_fine_geometry_and_respects_mask(self):
        grid=np.zeros((4,16,16));grid[0,8,8]=grid[1,8,8]=1
        fine=np.zeros((20,64,64));fine[0,32,32]=1;fine[1,28,32]=1
        obs={'grid':grid,'global_grid':fine,'weather':[.1,1.,0.,.2]}
        mask=np.ones(9,dtype=bool)
        self.assertEqual(make_repaired_heuristic('advancing_front')(obs,mask),1)
        self.assertEqual(make_repaired_heuristic('advancing_front64')(obs,mask),7)
        mask[7]=False
        self.assertEqual(make_repaired_heuristic('advancing_front64')(obs,mask),0)
        obs['future_weather']=[999]
        self.assertEqual(make_repaired_heuristic('advancing_front64')(obs,mask),0)

if __name__=='__main__':unittest.main()
