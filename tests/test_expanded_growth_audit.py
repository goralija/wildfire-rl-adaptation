import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest(str(exc))

from wildfire_rl.expanded_growth_audit import (
    select_eligible_cases, growth_group, reuse_prediction, trace_noop, subgroup_summaries,
)
from wildfire_rl.observed_growth_audit import growth_metrics, METHODS


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ExpandedGrowthTest(unittest.TestCase):
    def cohort(self):
        cases = [{'scenario_id':'case%02d'%k,'split':'train','event':{'year':2018}} for k in range(61)]
        qc = [{'scenario_id':c['scenario_id'],'eligible':True,
               'front_unsupported_common_vegetation':0,'unknown_fuel_count':0,
               'elevation_filled_cells':0} for c in cases]
        return {'input_qc':{'cases':qc}}, {'cases':cases}

    def test_selection_includes_every_eligible_case_and_never_uses_outcomes(self):
        p,m = self.cohort();p['input_qc']['cases'].reverse()
        p['input_qc']['cases'].append({'scenario_id':'excluded','eligible':False})
        result = select_eligible_cases(p,m)
        self.assertEqual(len(result),61)
        self.assertEqual([c['scenario_id'] for c in result],sorted(c['scenario_id'] for c in m['cases']))

    def test_selection_refuses_duplicate_nontrain_or_changed_qc(self):
        p,m = self.cohort();p['input_qc']['cases'].append(p['input_qc']['cases'][0])
        with self.assertRaises(ValueError): select_eligible_cases(p,m)
        p,m = self.cohort();m['cases'][0]['split']='validation'
        with self.assertRaises(ValueError): select_eligible_cases(p,m)
        p,m = self.cohort();p['input_qc']['cases'][0]['unknown_fuel_count']=1
        with self.assertRaises(ValueError): select_eligible_cases(p,m)

    def test_growth_groups_have_exact_exclusive_zero_and_ten_percent_boundaries(self):
        self.assertEqual(growth_group(100,0),'zero_growth')
        self.assertEqual(growth_group(100,1),'near_stalled')
        self.assertEqual(growth_group(100,9),'near_stalled')
        self.assertEqual(growth_group(100,10),'growing')
        self.assertEqual(growth_group(3,1),'growing')
        for initial,observed in [(0,1),(2,-1),(100,.5),(100,np.nan)]:
            with self.assertRaises(ValueError): growth_group(initial,observed)

    def previous(self,folder):
        p=folder/'original'/'a.json';p.parent.mkdir()
        np.savez_compressed(p.with_suffix('.npz'),initial=np.eye(3,dtype=bool),simfire=np.ones((5,3,3),bool))
        oldguard={'backend':'simfire','runtime':{'python':'fixture'},'common':{
            'source_sha256':{'physics.py':'same'},'weather_sha256':'weather','manifest_sha256':'manifest'}}
        record={'scenario_id':'a','guard':oldguard,'input_receipt_sha256':'receipt',
                'npz_sha256':digest(p.with_suffix('.npz')),'seconds':15.,'backend':'simfire'}
        p.write_text(json.dumps(record))
        expected={'record_sha256':digest(p),'npz_sha256':record['npz_sha256'],
                  'runtime':oldguard['runtime'],'input_receipt_sha256':'receipt'}
        newguard={**oldguard,'common':{**oldguard['common'],'plan_sha256':'new',
                  'source_sha256':{'physics.py':'same','new_driver.py':'added'}}}
        return p,expected,newguard

    def test_reuse_retains_original_provenance_and_exact_arrays(self):
        with tempfile.TemporaryDirectory() as f:
            folder=Path(f);p,e,g=self.previous(folder);target=folder/'new'/'a.json'
            r=reuse_prediction(p,target,e,g)
            self.assertEqual(r['reused_from']['record_sha256'],e['record_sha256'])
            self.assertEqual(r['reused_from']['original_guard']['common']['source_sha256'],{'physics.py':'same'})
            self.assertEqual(r['guard'],g);self.assertTrue(r['compute_reused'])
            self.assertEqual(digest(target.with_suffix('.npz')),e['npz_sha256'])

    def test_reuse_refuses_changed_source_runtime_or_corrupted_arrays_before_copy(self):
        for failure in ('source','runtime','arrays'):
            with tempfile.TemporaryDirectory() as f:
                folder=Path(f);p,e,g=self.previous(folder);target=folder/'new'/'a.json'
                if failure=='source':g['common']['source_sha256']['physics.py']='changed'
                if failure=='runtime':g['runtime']={'python':'other'}
                if failure=='arrays':p.with_suffix('.npz').write_bytes(b'corrupt')
                with self.assertRaises(ValueError):reuse_prediction(p,target,e,g)
                self.assertFalse(target.exists());self.assertFalse(target.with_suffix('.npz').exists())

    def test_trace_preserves_all_four_decisions_after_extinction_and_prior_damage(self):
        initial=np.eye(3,dtype=bool)
        class Env:
            def reset(self):
                self.cumulative_burned=initial.copy();self.remaining_budget=1;self.k=0
                return {},{}
            def action_masks(self):return np.array([True]+[False]*8)
            def step(self,action):
                self.k+=1;return {},0.,self.k==4,False,{}
        env=Env();result=trace_noop(env,initial)
        self.assertEqual(env.k,4);self.assertEqual(result.shape,(5,3,3))
        np.testing.assert_array_equal(result[-1],initial)
        class BadEnv(Env):
            def step(self,action):
                result=super().step(action);self.cumulative_burned[:]=False;return result
        with self.assertRaises(ValueError):trace_noop(BadEnv(),initial)

    def test_zero_group_keeps_undefined_iou_and_missing_stays_unclassified(self):
        initial=np.ones((10,10),bool);initial[-1]=False
        rows=[]
        for sid,n in [('zero',0),('near',1),('large',10)]:
            target=initial.copy();target[-1,:n]=True
            pred=initial.copy();pred[-1,:3]=True
            metrics={m:growth_metrics(initial,pred,target) for m in METHODS if m!='ca_mean3'}
            rows.append({'scenario_id':sid,'complete':True,'fully_covered':sid!='large',
                         'metrics':{'raw':{'48':metrics}}})
        rows.append({'scenario_id':'missing','complete':False})
        result=subgroup_summaries(rows,['zero'])
        self.assertEqual(result['unclassified_missing_ids'],['missing'])
        self.assertEqual(result['growth_groups']['zero_growth']['complete_ids'],['zero'])
        self.assertIsNone(result['growth_groups']['zero_growth']['methods']['simfire']['mean_growth_iou'])
        self.assertEqual(result['growth_groups']['near_stalled']['complete_ids'],['near'])
        self.assertEqual(result['growth_groups_fully_covered']['growing']['complete_ids'],[])
        self.assertEqual(result['new_cases']['missing_ids'],['missing'])


if __name__=='__main__':unittest.main()
