import hashlib
import json
from pathlib import Path
import tempfile
import unittest
try:
    import numpy as np
except ImportError:
    raise unittest.SkipTest('optional NumPy dependency is not installed')
from wildfire_rl.feds_observation_dataset import load_observation_case

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def fixture(root):
    arrays={'grid':np.zeros((4,4,16,16)),'weather':np.zeros((4,4)),'time':np.arange(4)[:,None]/4,
      'budget':np.full((4,2),.25),'global_grid':np.zeros((4,20,64,64)),
      'action_patches':np.zeros((4,8,20,17,17)),'candidate_line_masks':np.zeros((4,8,17,17)),
      'candidate_centres':np.full((4,8,2),.5),'mask_legacy':np.ones((4,9),dtype=bool),
      'mask_burnable_lines':np.ones((4,9),dtype=bool)}
    npz=root/'a.npz';np.savez_compressed(npz,**arrays)
    record={'scenario_id':'a','split':'train','settings':{'plan_sha256':'registered'},
      'legacy_and_candidate_and_whole_mask_check':'PASS','npz_sha256':sha(npz)}
    p=root/'a.json';p.write_text(json.dumps(record));item={'scenario_id':'a','file':'a.json','sha256':sha(p)}
    return arrays,record,item


class ObservationDatasetTests(unittest.TestCase):
    def test_valid_case_and_changed_npz_are_distinguished(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);arrays,r,item=fixture(root)
            _,obs,masks=load_observation_case(root,item,r['settings'])
            self.assertEqual(len(obs),4);self.assertTrue(masks['legacy'][:,0].all())
            (root/'a.npz').write_bytes(b'changed')
            with self.assertRaises(ValueError):load_observation_case(root,item,r['settings'])

    def test_case_identity_split_settings_and_reference_are_guarded(self):
        for key,value in [('scenario_id','other'),('split','validation'),('settings',{}),('legacy_and_candidate_and_whole_mask_check','FAIL')]:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as d:
                root=Path(d);_,r,item=fixture(root);expected=r['settings'];r[key]=value
                p=root/'a.json';p.write_text(json.dumps(r));item['sha256']=sha(p)
                with self.assertRaises(ValueError):load_observation_case(root,item,expected)

    def test_new_mask_cannot_enable_an_old_illegal_action_or_remove_noop(self):
        for kind in ('superset','noop'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as d:
                root=Path(d);arrays,r,item=fixture(root)
                if kind=='superset':arrays['mask_legacy'][0,1]=False
                else:arrays['mask_burnable_lines'][0,0]=False
                np.savez_compressed(root/'a.npz',**arrays);r['npz_sha256']=sha(root/'a.npz')
                p=root/'a.json';p.write_text(json.dumps(r));item['sha256']=sha(p)
                with self.assertRaises(ValueError):load_observation_case(root,item,r['settings'])

if __name__=='__main__':unittest.main()
