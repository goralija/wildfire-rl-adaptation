import copy
import unittest

try:
    import numpy as np
    import gymnasium
except ImportError as exc:
    raise unittest.SkipTest(str(exc))

from wildfire_rl.paired_ppo_learning import (validate_design,case_schedule,LazyTrainingCases,
    summarize_learning,completed_job)
from test_common_control import environment


class LearningContractTests(unittest.TestCase):
    def test_disjoint_design_and_same_seed_schedule(self):
        plan=dict(fitting_cases=['a','b','c'],evaluation_cases=['d'],model_seeds=[17,29,43],
                  checkpoints=[0,512,2048],training_steps=2048)
        validate_design(plan)
        self.assertEqual(case_schedule(plan['fitting_cases'],17),case_schedule(plan['fitting_cases'],17))
        self.assertEqual(set(case_schedule(plan['fitting_cases'],17)),set(plan['fitting_cases']))
        for changed in [dict(evaluation_cases=['a']),dict(fitting_cases=['a','a']),
                        dict(model_seeds=[17,17]),dict(checkpoints=[0,512,1024])]:
            with self.assertRaises(ValueError):validate_design(dict(plan,**changed))

    def test_lazy_environment_closes_old_case_and_preserves_four_decisions(self):
        built=[]
        def factory(sid):
            env=environment();env.unwrapped.scenario_id=sid
            built.append(env);return env
        env=LazyTrainingCases(['a','b'],factory)
        for sid in ['a','b','a']:
            _,info=env.reset();self.assertEqual(info['scenario_id'],sid)
            for k,action in enumerate([1,0,0,0]):
                _,_,done,_,info=env.step(action)
                self.assertEqual(done,k==3);self.assertTrue(env.action_masks()[0])
                self.assertEqual(info['remaining_budget'],0)
        self.assertEqual(env.episode_schedule,['a','b','a'])
        self.assertEqual(len(built),3)
        with self.assertRaises(ValueError):env.reset(options={'scenario_id':'eval'})


def rows_fixture():
    policies=[];baseline=[]
    for backend in ['simfire','ca']:
        for sid,noop in [('a',100),('b',0),('c',200)]:
            for method,saved in [('noop',0),('advancing_front64',.1)]:
                baseline.append(dict(backend=backend,scenario_id=sid,method=method,
                    noop_damage_cells=noop,charged_damage_cells=noop*(1-saved)))
            for seed in [17,29,43]:
                for stage,saved in [(0,0.),(512,.1),(2048,.2 if backend=='simfire' else .25)]:
                    policies.append(dict(backend=backend,scenario_id=sid,seed=seed,checkpoint=stage,
                        noop_damage_cells=noop,charged_damage_cells=noop*(1-saved),
                        raw_damage_cells=noop*(1-saved)))
    return policies,baseline


class LearningStatisticsTests(unittest.TestCase):
    def test_seeds_are_averaged_inside_fire_and_zero_denominator_excluded(self):
        p,b=rows_fixture();r=summarize_learning(p,b,['a','b','c'],[17,29,43])
        self.assertEqual(r['joint_positive_ids'],['a','c'])
        self.assertEqual(r['backends']['ca']['final_minus_front_pp']['n'],2)
        self.assertAlmostEqual(r['backends']['simfire']['final_minus_front_pp']['mean'],10.)
        self.assertAlmostEqual(r['ca_minus_sf_relative_gap_pp']['mean'],5.)
        self.assertEqual(r['backends']['ca']['zero_noop_ids'],['b'])
        self.assertTrue(r['backends']['ca']['descriptive_positive_signal'])

    def test_case_mean_and_pooled_percent_are_both_kept(self):
        p,b=rows_fixture()
        for row in p:
            if row['checkpoint']==2048 and row['scenario_id']=='a':row['charged_damage_cells']=100
        r=summarize_learning(p,b,['a','b','c'],[17,29,43])
        metric=r['backends']['simfire']['checkpoints']['2048']
        self.assertAlmostEqual(metric['mean_saved_percent_joint'],10.)
        self.assertAlmostEqual(metric['pooled_saved_percent_all'],100*40/300)

    def test_missing_duplicate_nonfinite_or_inconsistent_baseline_rejected(self):
        p,b=rows_fixture()
        with self.assertRaises(ValueError):summarize_learning(p[:-1],b,['a','b','c'],[17,29,43])
        with self.assertRaises(ValueError):summarize_learning(p+[p[0]],b,['a','b','c'],[17,29,43])
        bad=copy.deepcopy(p);bad[0]['charged_damage_cells']=float('nan')
        with self.assertRaises(ValueError):summarize_learning(bad,b,['a','b','c'],[17,29,43])
        bad=copy.deepcopy(p);bad[0]['noop_damage_cells']=999
        with self.assertRaises(ValueError):summarize_learning(bad,b,['a','b','c'],[17,29,43])

    def test_worse_than_noop_keeps_negative_savings(self):
        p,b=rows_fixture()
        for row in p:
            if row['checkpoint']==2048:row['charged_damage_cells']=2*row['noop_damage_cells']
        r=summarize_learning(p,b,['a','b','c'],[17,29,43])
        self.assertEqual(r['backends']['ca']['checkpoints']['2048']['mean_saved_percent_joint'],-100.)
        self.assertFalse(r['backends']['ca']['descriptive_positive_signal'])

    def test_higher_ca_agent_percent_can_still_have_worse_relative_heuristic_gap(self):
        p,b=rows_fixture()
        for row in b:
            if row['backend']=='ca' and row['method']=='advancing_front64':
                row['charged_damage_cells']=.6*row['noop_damage_cells']
        r=summarize_learning(p,b,['a','b','c'],[17,29,43])
        self.assertGreater(r['backends']['ca']['checkpoints']['2048']['mean_saved_percent_joint'],
                           r['backends']['simfire']['checkpoints']['2048']['mean_saved_percent_joint'])
        self.assertAlmostEqual(r['ca_minus_sf_relative_gap_pp']['mean'],-25.)
        self.assertFalse(r['backends']['ca']['descriptive_positive_signal'])

    def test_all_zero_noop_remains_undefined(self):
        p,b=rows_fixture()
        for row in p+b:row['noop_damage_cells']=row['charged_damage_cells']=0
        r=summarize_learning(p,b,['a','b','c'],[17,29,43])
        self.assertIsNone(r['ca_minus_sf_relative_gap_pp']['mean'])
        self.assertIsNone(r['backends']['ca']['checkpoints']['2048']['mean_saved_percent_joint'])

    def test_completion_receipt_needs_matching_guard_and_all_files(self):
        import json,tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.assertFalse(completed_job(root,{'a':1}))
            (root/'done.json').write_text(json.dumps({'guard':{'a':2},'files':{}}))
            with self.assertRaises(ValueError):completed_job(root,{'a':1})
            (root/'done.json').write_text(json.dumps({'guard':{'a':1},'files':{'missing':'abc'}}))
            with self.assertRaises(ValueError):completed_job(root,{'a':1})
            import hashlib
            artifact=root/'result.json';artifact.write_text('{}')
            (root/'done.json').write_text(json.dumps({'guard':{'a':1},'files':{
                'result.json':hashlib.sha256(artifact.read_bytes()).hexdigest()}}))
            self.assertTrue(completed_job(root,{'a':1}))
            artifact.write_text('{"changed":true}')
            with self.assertRaises(ValueError):completed_job(root,{'a':1})
