import unittest
try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest(str(exc))
from wildfire_rl.ppo_signal_diagnosis import (uniform_line_expectation,select_fixed_sector,
    reference_metrics,episodic_returns,centered_rewards,cost_decomposition)


class SignalDiagnosisTests(unittest.TestCase):
    def test_uniform_is_expectation_over_legal_lines_not_one_seed(self):
        costs=np.arange(9,dtype=float)*10
        mask=np.array([1,1,0,1,0,0,0,0,0],bool)
        self.assertEqual(uniform_line_expectation(costs,mask),20.)
        mask[1:]=False
        self.assertEqual(uniform_line_expectation(costs,mask),0.)
        mask[0]=False
        with self.assertRaises(ValueError):uniform_line_expectation(costs,mask)

    def test_fixed_sector_uses_fitting_only_and_lowest_tie(self):
        fit=np.ones((3,9))*10;fit[:,3]=5;fit[:,7]=5
        self.assertEqual(select_fixed_sector(fit),3)
        with self.assertRaises(ValueError):select_fixed_sector(np.zeros((0,9)))

    def test_zero_noop_stays_undefined_and_negative_savings_remain(self):
        r=reference_metrics([0,100,200],[10,120,100],[False,True,True])
        self.assertEqual(r['undefined_case_indices'],[0])
        self.assertAlmostEqual(r['mean_saved_percent_joint'],15.)
        self.assertAlmostEqual(r['pooled_saved_percent_all'],100*70/300)
        self.assertEqual(r['per_case_saved_percent'],[None,-20.,50.])

    def test_centering_preserves_action_order_and_fixed_horizon_sum(self):
        noop=np.array([10,20,0,0]*2)
        original=np.array([-5.,-4.,-3.,-2.,-1.,-2.,-3.,-4.])
        shifted=centered_rewards(original,noop)
        returns=episodic_returns(original);new=episodic_returns(shifted)
        np.testing.assert_allclose(new[::4]-returns[::4],[.3,.3])
        self.assertEqual(np.argsort(returns[::4]).tolist(),np.argsort(new[::4]).tolist())
        with self.assertRaises(ValueError):episodic_returns([0,1,2])
        with self.assertRaises(ValueError):centered_rewards([0],[-1])

    def test_case_centering_removes_only_between_case_offset(self):
        costs=np.stack([np.arange(9)+1000,np.arange(9)+10]).astype(float)
        masks=np.ones_like(costs,bool)
        raw=cost_decomposition(costs,masks)
        shifted=cost_decomposition(costs-costs[:,0,None],masks)
        self.assertAlmostEqual(raw['within_case_variance'],shifted['within_case_variance'])
        self.assertGreater(raw['between_case_variance'],10000)
        self.assertAlmostEqual(shifted['between_case_variance'],0.)

    def test_nonfinite_or_bad_shape_rejected(self):
        with self.assertRaises(ValueError):uniform_line_expectation(np.zeros(8),np.ones(8))
        with self.assertRaises(ValueError):select_fixed_sector(np.full((2,9),np.nan))
        with self.assertRaises(ValueError):reference_metrics([0],[np.nan],[False])
