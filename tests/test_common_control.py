"""Contract tests precede the opt-in common charged-reward adapter (ADR-049)."""
import unittest

try:
    import gymnasium as gym
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest('optional Gym/NumPy required: %s' % exc)

from wildfire_rl.common_control import ChargedLedger, CommonControlEnv, CyclingCases


def observation(budget=1, step=0):
    return dict(grid=np.zeros((4,16,16),np.float32),
                budget=np.array([.25,budget/4.],np.float32),
                weather=np.zeros(4,np.float32),time=np.array([step/4.],np.float32),
                global_grid=np.zeros((20,64,64),np.float32),
                action_patches=np.zeros((8,20,17,17),np.float32),
                candidate_line_masks=np.zeros((8,17,17),np.float32),
                candidate_centres=np.zeros((8,2),np.float32))


class FakeV2(gym.Env):
    action_space=gym.spaces.Discrete(9)
    observation_space=gym.spaces.Dict({k:gym.spaces.Box(-1,1,v.shape,dtype=np.float32)
                                       for k,v in observation().items()})
    scenario_id='fake'

    def reset(self,*,seed=None,options=None):
        super().reset(seed=seed)
        self.initial_budget=self.remaining_budget=1
        self.decision_index=0
        self.cumulative_burned=np.zeros((4,4),bool)
        self.cumulative_burned[0,0]=True
        return observation(), {'scenario_id':self.scenario_id}

    def candidate_points(self):
        return [[(0,0),(1,1),(2,1)]]+[[] for _ in range(7)]

    def action_masks(self):
        return np.array([True,self.remaining_budget>0]+[False]*7)

    def step(self,action):
        if self.decision_index==4:raise RuntimeError('done')
        if action:self.remaining_budget-=1
        # The second new burn is already charged through the line footprint.
        y,x=[(2,2),(1,2),(3,1),(3,2)][self.decision_index]
        self.cumulative_burned[y,x]=True
        self.decision_index+=1
        return observation(self.remaining_budget,self.decision_index),999.,self.decision_index==4,False,dict(
            line_cells_applied=3 if action else 0,invalid_action=False,
            remaining_budget=self.remaining_budget,line_length_m=360. if action else 0.)


def environment(reference=None):
    reference=np.ones((4,4),bool) if reference is None else reference
    return CommonControlEnv(FakeV2(),reference)


class CommonControlTests(unittest.TestCase):
    def test_union_prior_and_incremental_return(self):
        initial=np.zeros((3,3),bool);initial[0,0]=1
        noop=initial.copy();noop[1,:]=1
        ledger=ChargedLedger(initial,noop)
        burned=initial.copy();burned[2,2]=1
        line=initial.copy();line[1,0:2]=1
        self.assertEqual(ledger.update(burned,line),3)
        burned[1,0]=1
        self.assertEqual(ledger.update(burned,line),0)
        self.assertEqual(ledger.score['charged_damage_cells'],3)
        self.assertEqual(ledger.score['raw_damage_cells'],2)
        self.assertEqual(ledger.score['extra_line_charge_cells'],1)

    def test_damage_cannot_disappear_and_masks_are_binary(self):
        initial=np.eye(3,dtype=bool)
        with self.assertRaises(ValueError):ChargedLedger(initial,np.zeros((2,2)))
        with self.assertRaises(ValueError):ChargedLedger(initial,np.full((3,3),.5))
        ledger=ChargedLedger(initial,np.ones((3,3),bool))
        with self.assertRaises(ValueError):ledger.update(np.zeros((3,3),bool),initial)
        ledger.update(initial,np.ones((3,3),bool))
        with self.assertRaises(ValueError):ledger.update(initial,initial)

    def test_invalid_after_budget_is_noop_and_full_horizon_remains(self):
        env=environment();obs,_=env.reset()
        self.assertEqual(obs.shape,(536,));self.assertEqual(obs.dtype,np.float32)
        rewards=[]
        for k,action in enumerate([1,1,0,0]):
            obs,reward,done,trunc,info=env.step(action);rewards.append(reward)
            self.assertEqual(done,k==3);self.assertFalse(trunc)
            self.assertTrue(env.action_masks()[0])
            self.assertFalse(env.action_masks()[1:].any())
            self.assertEqual(info['remaining_budget'],0)
            self.assertEqual(info['effective_action'],1 if k==0 else 0)
            self.assertEqual(info['invalid_action'],k==1)
        self.assertAlmostEqual(sum(rewards),-info['charged_damage_cells']/100.-.01)
        with self.assertRaises(RuntimeError):env.step(0)

    def test_private_reference_changes_reward_never_features_or_masks(self):
        a=environment();b=environment(np.eye(4,dtype=bool))
        oa,_=a.reset();ob,_=b.reset();np.testing.assert_array_equal(oa,ob)
        oa,ra,_,_,_=a.step(1);ob,rb,_,_,_=b.step(1)
        np.testing.assert_array_equal(oa,ob)
        np.testing.assert_array_equal(a.action_masks(),b.action_masks())
        self.assertNotEqual(ra,rb)

    def test_out_of_space_rejected_before_state_change(self):
        env=environment();env.reset()
        with self.assertRaises(ValueError):env.step(9)
        self.assertEqual(env.unwrapped.decision_index,0)

    def test_common_metadata_does_not_depend_on_backend_info(self):
        env=environment();env.reset()
        _,_,_,_,info=env.step(0)
        self.assertEqual(info['scenario_id'],'fake')
        self.assertEqual(info['split'],'train')

    def test_cyclic_schedule_and_explicit_reset(self):
        a,b,c=environment(),environment(),environment()
        env=CyclingCases({'a':a,'b':b,'c':c})
        for key in ['a','b','c','a']:
            _,info=env.reset();self.assertEqual(info['common_case_id'],key)
        _,info=env.reset(options={'scenario_id':'c'})
        self.assertEqual(info['common_case_id'],'c')
        with self.assertRaises(ValueError):env.reset(options={'scenario_id':'unknown'})
        self.assertEqual(env.episode_schedule,['a','b','c','a','c'])

