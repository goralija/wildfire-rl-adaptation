import importlib.util
import unittest
from types import SimpleNamespace
from unittest import mock

if not importlib.util.find_spec('numpy') or not importlib.util.find_spec('gymnasium'):
    raise unittest.SkipTest('optional NumPy/Gymnasium dependencies are not installed')
import numpy as np
import gymnasium as gym
from wildfire_rl.feds_simfire_env import FedsSimFireEnv
from wildfire_rl.feds_observation_v2 import SimFireObservationV2, OBSERVATION_VERSION


def env_at(x=128,y=128,fuel=13):
    env=FedsSimFireEnv.__new__(FedsSimFireEnv)
    state=np.zeros((256,256),dtype=np.int64);state[y,x]=1
    env.simulation=SimpleNamespace(fire_map=state);env.cumulative_burned=state==1
    env.fuel=np.full(state.shape,fuel,dtype=np.int16)
    env.block_count=16;env.line_placement='front_edge';env.scenario_id='fixture'
    env._input_cache={'fixture':{'elevation':np.indices(state.shape)[1].astype(float)*18.}}
    env.initial_budget=env.remaining_budget=1;env.max_budget=4;env.decision_index=0;env.horizon_steps=4
    env.observed_forcing=[{'wind_direction_degrees_clockwise_north_to':90.,
                          'wind_speed_midflame_ft_per_min_proxy':50.,'fuel_moisture_fraction_proxy':.06}]*4
    obs=env._observation();env.action_space=gym.spaces.Discrete(9)
    env.observation_space=gym.spaces.Dict({k:gym.spaces.Box(-1.,1.,shape=v.shape,dtype=np.float32) for k,v in obs.items()})
    return env


class ObservationV2Tests(unittest.TestCase):
    def test_categories_keep_fuel13_separate_from_nonfuel_and_sum_to_one(self):
        a,b=SimFireObservationV2(env_at(fuel=13)),SimFireObservationV2(env_at(fuel=91))
        x,y=a.observation(a.env._observation()),b.observation(b.env._observation())
        np.testing.assert_array_equal(x['grid'],y['grid'])
        self.assertTrue((x['global_grid'][15]==1).all())
        self.assertTrue((x['global_grid'][16]==0).all())
        self.assertTrue((y['global_grid'][15]==0).all())
        self.assertTrue((y['global_grid'][16]==1).all())
        for obs in (x,y):np.testing.assert_allclose(obs['global_grid'][3:17].sum(axis=0),1.)

    def test_native_crop_and_centres_distinguish_old_pooled_position_alias(self):
        a,b=SimFireObservationV2(env_at(113,113)),SimFireObservationV2(env_at(126,126))
        x,y=a.observation(a.env._observation()),b.observation(b.env._observation())
        np.testing.assert_array_equal(x['grid'],y['grid'])
        self.assertFalse(np.array_equal(x['candidate_centres'],y['candidate_centres']))
        self.assertEqual(x['action_patches'].shape,(8,20,17,17))
        self.assertEqual(x['candidate_line_masks'].shape,(8,17,17))
        self.assertEqual(x['global_grid'].shape,(20,64,64))
        self.assertTrue(a.observation_space.contains(x))
        self.assertEqual(a.observation_version,OBSERVATION_VERSION)

    def test_nonfuel_mask_keeps_noop_and_leaves_legacy_environment_unchanged(self):
        base=env_at(fuel=91);wrapped=SimFireObservationV2(base)
        self.assertTrue(base.action_masks().all())
        np.testing.assert_array_equal(wrapped.action_masks(),[True]+[False]*8)
        self.assertTrue(base.action_masks().all())
        base.remaining_budget=0
        np.testing.assert_array_equal(wrapped.action_masks(),[True]+[False]*8)

    def test_partial_burnable_line_stays_legal(self):
        base=env_at(fuel=91);base.fuel[128,130]=1
        wrapped=SimFireObservationV2(base)
        self.assertTrue(wrapped.action_masks()[1])

    def test_invalid_nonfuel_action_does_not_reach_base_or_spend_budget(self):
        base=env_at(fuel=91);obs=base._observation()
        base.step=mock.Mock(return_value=(obs,0.,False,False,{'invalid_action':False}))
        wrapped=SimFireObservationV2(base)
        _,reward,done,_,info=wrapped.step(1)
        base.step.assert_called_once_with(0)
        self.assertEqual(base.remaining_budget,1);self.assertFalse(done)
        self.assertAlmostEqual(reward,-.01);self.assertTrue(info['invalid_action'])
        self.assertTrue(info['v2_blocked_nonfuel'])

    def test_disabling_gate_is_exact_legacy_mask_and_terrain_has_correct_units(self):
        wrapped=SimFireObservationV2(env_at(),mask_nonfuel_lines=False)
        np.testing.assert_array_equal(wrapped.action_masks(),wrapped.env.action_masks())
        obs=wrapped.observation(wrapped.env._observation())
        np.testing.assert_allclose(obs['global_grid'][18],.1,atol=1e-6)
        np.testing.assert_allclose(obs['global_grid'][19],0.,atol=1e-6)
        self.assertNotEqual(wrapped.observation_space,wrapped.env.observation_space)

    def test_outside_map_is_nonfuel_and_observation_stays_in_declared_space(self):
        wrapped=SimFireObservationV2(env_at(0,0))
        obs=wrapped.observation(wrapped.env._observation())
        self.assertTrue(wrapped.observation_space.contains(obs))
        self.assertGreater(float(obs['action_patches'][:,16].sum()),0.)

if __name__=='__main__':unittest.main()
