import hashlib
import unittest
try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest(str(exc))
from wildfire_rl.control_features import terrain_features


def observation():
    obs=dict(grid=np.zeros((4,16,16),np.float32),weather=np.zeros(4,np.float32),
        time=np.zeros(1,np.float32),budget=np.array([.25,.25],np.float32),
        global_grid=np.zeros((20,64,64),np.float32),action_patches=np.zeros((8,20,17,17),np.float32),
        candidate_line_masks=np.zeros((8,17,17),np.float32),candidate_centres=np.zeros((8,2),np.float32))
    obs['global_grid'][15]=1;obs['action_patches'][:,15]=1
    return obs


class ControlFeaturesTests(unittest.TestCase):
    def test_encoder_matches_pre_extraction_golden_vector(self):
        values=np.asarray(terrain_features(observation()),np.float32)
        self.assertEqual(values.shape,(536,));self.assertTrue(np.isfinite(values).all())
        self.assertEqual(hashlib.sha256(values.tobytes()).hexdigest(),
                         '5f93ef7cb9a79ecce20df933b8e75a5b3aaf80a3d772829a0717c3e7505119b9')

    def test_grid_contract_and_nonfinite_global_input_rejected(self):
        obs=observation();obs['grid']=np.zeros((4,8,8))
        with self.assertRaises(ValueError):terrain_features(obs)
        obs=observation();obs['global_grid'][0,0,0]=np.nan
        with self.assertRaises(ValueError):terrain_features(obs)
