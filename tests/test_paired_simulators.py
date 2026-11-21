import unittest
from types import SimpleNamespace
try:
    import gymnasium
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest(str(exc))

from wildfire_rl.paired_simulators import CABridgeEnv, fraction, summarize_pair
from wildfire_rl.feds_observation_v2 import SimFireObservationV2
from wildfire_rl.synthetic_ca import Weather


def fixture():
    fuel=np.full((256,256),8,dtype=np.int16)
    fuel[2,2]=91
    front=np.zeros(fuel.shape,bool);front[128,128]=True
    inputs={'scenario_id':'fixture','split':'train','fuel':fuel,
            'elevation':np.zeros(fuel.shape),'scar':np.zeros(fuel.shape,bool),'front':front}
    observed=[{'wind_direction_degrees_clockwise_north_to':90.,
               'wind_speed_midflame_ft_per_min_proxy':20.,'fuel_moisture_fraction_proxy':.1}]*4
    return inputs,[Weather(.1,90,.1,13)]*48,observed


class BridgeTest(unittest.TestCase):
    def env(self):
        return SimFireObservationV2(CABridgeEnv(*fixture(),seed=17))

    def test_one_line_exhausts_budget_but_keeps_four_decisions_and_noop(self):
        env=self.env();obs,_=env.reset()
        self.assertTrue(env.observation_space.contains(obs))
        _,_,done,_,info=env.step(1)
        self.assertFalse(done);self.assertEqual(env.env.remaining_budget,0)
        self.assertLessEqual(info['line_length_m'],1260.0001)
        self.assertEqual(env.action_masks().tolist(),[True]+[False]*8)
        for k in range(1,4):
            _,_,done,_,_=env.step(0)
            self.assertEqual(done,k==3)

    def test_prior_damage_is_monotone_and_nonfuel_semantics_are_shared(self):
        env=self.env();env.reset();base=env.env
        self.assertFalse(base.land.burnable[2,2])
        self.assertEqual(base.fuel[2,2],91)
        initial=base.cumulative_burned.copy()
        for _ in range(4):
            env.step(0)
            self.assertFalse((initial&~base.cumulative_burned).any())
            initial=base.cumulative_burned.copy()

    def test_unsupported_initial_front_and_nontrain_are_refused(self):
        inputs,w,o=fixture();inputs['split']='validation'
        with self.assertRaises(ValueError):CABridgeEnv(inputs,w,o)
        inputs['split']='train';inputs['front'][2,2]=True
        with self.assertRaises(ValueError):CABridgeEnv(inputs,w,o)

    def test_common_random_noop_replay_is_identical(self):
        a,b=self.env(),self.env();a.reset();b.reset()
        for _ in range(4):a.step(0);b.step(0)
        np.testing.assert_array_equal(a.env.cumulative_burned,b.env.cumulative_burned)

    def test_runner_accepts_the_original_simfire_diagonal_capacity(self):
        import sys
        from pathlib import Path
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
        from run_paired_simulators import rollout
        from wildfire_rl.feds_simfire_env import line_length_m
        result=rollout(self.env(),sequence=[2,0,0,0])
        self.assertAlmostEqual(result['line_length_m'],line_length_m(1))


class PercentageTest(unittest.TestCase):
    def test_zero_denominator_is_undefined_and_negative_savings_survive(self):
        self.assertIsNone(fraction(0,0))
        self.assertEqual(fraction(-10,100),-.1)

    def test_joint_subset_and_pooled_ratio_are_distinct_and_paired(self):
        sf=[{'scenario_id':'a','noop':100,'damage':50},
            {'scenario_id':'b','noop':0,'damage':0},
            {'scenario_id':'c','noop':10,'damage':10}]
        ca=[{'scenario_id':'a','noop':200,'damage':180},
            {'scenario_id':'b','noop':10,'damage':0},
            {'scenario_id':'c','noop':10,'damage':20}]
        x=summarize_pair(sf,ca)
        self.assertEqual(x['joint_positive_cases'],2)
        self.assertAlmostEqual(x['sf_mean_fraction_joint'],.25)
        self.assertAlmostEqual(x['ca_mean_fraction_joint'],-.45)
        self.assertAlmostEqual(x['sf_pooled_fraction_all'],50/110)
        self.assertAlmostEqual(x['ca_pooled_fraction_all'],20/220)
        self.assertEqual(x['sf_zero_noop_cases'],1)
        with self.assertRaises(ValueError):summarize_pair(sf,list(reversed(ca)))
