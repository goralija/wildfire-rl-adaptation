import unittest
try:
    import numpy as np
except ImportError:
    raise unittest.SkipTest('optional NumPy dependency is not installed')
from wildfire_rl.feds_repaired_learning import repaired_features, legal_oracle
from wildfire_rl.feds_b1_learning import observation_features


def obs():
    grid=np.zeros((4,16,16));grid[0,8,8]=1;grid[1,8,9]=1
    g=np.zeros((20,64,64));g[15]=1;g[0,32,32]=1;g[1,32,36]=1
    patch=np.zeros((8,20,17,17));patch[:,15]=1;patch[:,1,8,6]=1
    lines=np.zeros((8,17,17));lines[:,5:12,8]=1
    return {'grid':grid,'weather':np.array([.1,1.,0.,.2]),'time':np.array([0.]),'budget':np.array([.25,.25]),
            'global_grid':g,'action_patches':patch,'candidate_line_masks':lines,'candidate_centres':np.full((8,2),.5)}


class RepairedFeaturesTests(unittest.TestCase):
    def test_fixed_dimensions_and_legacy_identity(self):
        o=obs()
        for name,size in [('legacy28',28),('categorical154',154),('local458',458),('terrain536',536)]:
            values=repaired_features(o,name);self.assertEqual(values.shape,(size,));self.assertTrue(np.isfinite(values).all())
        np.testing.assert_array_equal(repaired_features(o,'legacy28'),observation_features(o))
        with self.assertRaises(ValueError):repaired_features(o,'future')

    def test_new_features_use_no_extra_metadata_or_future_outcome(self):
        o=obs();before=repaired_features(o,'terrain536')
        o['future_weather']=1e9;o['outcome']=1e9;o['scenario_id']='secret'
        np.testing.assert_array_equal(before,repaired_features(o,'terrain536'))

    def test_categories_and_native_geometry_change_their_targeted_features(self):
        a,b=obs(),obs();b['global_grid'][15]=0;b['global_grid'][16]=1
        self.assertFalse(np.array_equal(repaired_features(a,'categorical154'),repaired_features(b,'categorical154')))
        b=obs();b['candidate_centres'][0,0]=.7
        np.testing.assert_array_equal(repaired_features(a,'categorical154'),repaired_features(b,'categorical154'))
        self.assertFalse(np.array_equal(repaired_features(a,'local458'),repaired_features(b,'local458')))
        b=obs();b['global_grid'][17]=.5
        np.testing.assert_array_equal(repaired_features(a,'local458'),repaired_features(b,'local458'))
        self.assertFalse(np.array_equal(repaired_features(a,'terrain536'),repaired_features(b,'terrain536')))

    def test_masked_oracle_includes_noop_and_cannot_take_a_blocked_line(self):
        gains=np.zeros((4,9));gains[0,1]=100;gains[2,2]=20
        mask=np.ones((4,9),dtype=bool);mask[0,1]=False
        self.assertEqual(legal_oracle(gains,mask),20.)
        gains[:]=-10;gains[:,0]=0
        self.assertEqual(legal_oracle(gains,mask),0.)

if __name__=='__main__':unittest.main()
