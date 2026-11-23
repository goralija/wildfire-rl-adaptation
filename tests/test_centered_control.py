import unittest
try:
    import numpy as np
    import gymnasium
except ImportError as exc:
    raise unittest.SkipTest(str(exc))
from test_common_control import environment
from wildfire_rl.centered_control import CenteredControlEnv,REWARD_VERSION,compare_costs,method_metrics


def trajectory():
    initial=np.zeros((4,4),bool);initial[0,0]=1
    result=[initial.copy()]
    cells=[(y,x) for y in range(4) for x in range(4) if (y,x)!=(0,0)]
    for count in [4,8,12,15]:
        a=initial.copy()
        for y,x in cells[:count]:a[y,x]=1
        result.append(a)
    return np.stack(result)


class CenteredRewardTests(unittest.TestCase):
    def test_same_physics_features_masks_full_horizon_and_exact_saved_return(self):
        ref=trajectory();raw=environment(ref[-1]);centered=CenteredControlEnv(environment(ref[-1]),ref)
        a,_=raw.reset();b,info=centered.reset();np.testing.assert_array_equal(a,b)
        self.assertEqual(info['common_contract'],REWARD_VERSION)
        r0=r1=0.
        for k,action in enumerate([1,1,0,0]):
            np.testing.assert_array_equal(raw.action_masks(),centered.action_masks())
            a,x,d0,t0,i0=raw.step(action);b,y,d1,t1,i1=centered.step(action)
            np.testing.assert_array_equal(a,b)
            np.testing.assert_array_equal(raw.unwrapped.cumulative_burned,centered.unwrapped.cumulative_burned)
            self.assertEqual(d0,d1);self.assertEqual(d1,k==3);self.assertFalse(t0 or t1)
            self.assertEqual(i0['remaining_budget'],i1['remaining_budget'])
            self.assertEqual(i0['invalid_action'],i1['invalid_action'])
            self.assertAlmostEqual(y-x,i1['noop_increment_cells']/100.)
            r0+=x;r1+=y
        self.assertAlmostEqual(r1-r0,15/100.)
        self.assertAlmostEqual(r1,(15-i1['charged_damage_cells'])/100.-.01)
        with self.assertRaises(RuntimeError):centered.step(0)

    def test_reference_shape_binary_monotonic_and_case_binding(self):
        ref=trajectory()
        for bad in [ref[:4],ref.astype(float)*.5]:
            with self.assertRaises(ValueError):CenteredControlEnv(environment(ref[-1]),bad)
        bad=ref.copy();bad[2,0,1]=False
        with self.assertRaises(ValueError):CenteredControlEnv(environment(ref[-1]),bad)
        bad=ref.copy();bad[0,0,1]=True
        env=CenteredControlEnv(environment(ref[-1]),bad)
        with self.assertRaises(ValueError):env.reset()
        env=CenteredControlEnv(environment(np.eye(4,dtype=bool)),ref)
        with self.assertRaises(ValueError):env.reset()

    def test_reference_timing_is_private_and_episode_offset_is_constant(self):
        a=trajectory();b=np.stack([a[0],a[-1],a[-1],a[-1],a[-1]])
        x=CenteredControlEnv(environment(a[-1]),a);y=CenteredControlEnv(environment(b[-1]),b)
        ox,_=x.reset();oy,_=y.reset();np.testing.assert_array_equal(ox,oy)
        sums=[0.,0.]
        for action in [1,0,0,0]:
            ox,rx,_,_,_=x.step(action);oy,ry,_,_,_=y.step(action)
            np.testing.assert_array_equal(ox,oy);np.testing.assert_array_equal(x.action_masks(),y.action_masks())
            sums[0]+=rx;sums[1]+=ry
        self.assertAlmostEqual(*sums)

    def test_out_of_space_does_not_advance_reward_reference(self):
        env=CenteredControlEnv(environment(),trajectory());env.reset()
        with self.assertRaises(ValueError):env.step(9)
        self.assertEqual(env.decision,0)


class CenteredComparisonTests(unittest.TestCase):
    def test_seed_pairs_are_inside_fire_and_zero_noop_is_undefined(self):
        centered=np.array([[80,9,180],[90,8,170],[70,7,190]])
        raw=np.array([[90,0,190],[100,0,180],[80,0,200]])
        d=compare_costs(centered,raw,[100,0,200],[True,False,True])
        self.assertEqual(d['n'],2);self.assertAlmostEqual(d['mean'],7.5)
        m=method_metrics(centered,[100,0,200],[True,False,True])
        self.assertAlmostEqual(m['mean_saved_percent_joint'],15.)
        self.assertEqual(m['undefined_case_indices'],[1])

    def test_negative_differences_and_all_zero_stay_explicit(self):
        d=compare_costs([[110]],[[90]],[100],[True]);self.assertEqual(d['mean'],-20.)
        d=compare_costs([[1]],[[0]],[0],[False]);self.assertIsNone(d['mean'])
        self.assertIsNone(method_metrics([[1]],[0],[False])['pooled_saved_percent_all'])
        with self.assertRaises(ValueError):compare_costs([[1]],[[0]],[0],[True])
        with self.assertRaises(ValueError):compare_costs([[float('nan')]],[[0]],[100],[True])
