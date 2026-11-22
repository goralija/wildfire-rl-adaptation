import unittest
try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest(str(exc))
from wildfire_rl.paired_learning_audit import trajectory_score,training_ledger,action_description


class IndependentLearningAuditTests(unittest.TestCase):
    def test_trajectory_union_preserves_prior_without_double_charging(self):
        initial=np.eye(3,dtype=bool);noop=np.ones((3,3),bool)
        burned=np.stack([initial.copy() for _ in range(5)])
        line=np.zeros_like(burned);line[1:,0,1]=1;burned[2:,0,1]=1
        result=trajectory_score(initial,burned,line,noop,[-.01,0,0,0])
        self.assertEqual(result['charged_damage_cells'],1)
        self.assertEqual(result['raw_damage_cells'],1)
        self.assertEqual(result['extra_line_charge_cells'],0)

    def test_trajectory_rejects_erased_prior_or_changed_return(self):
        initial=np.eye(3,dtype=bool);burned=np.stack([initial]*5);line=np.zeros_like(burned)
        with self.assertRaises(ValueError):trajectory_score(initial,burned,line,initial,[1,0,0,0])
        burned[2,0,0]=0
        with self.assertRaises(ValueError):trajectory_score(initial,burned,line,initial,[0]*4)

    def test_training_float32_return_and_budget_are_audited(self):
        rows=[dict(step=k+1,scenario_id='a',done=k==3,action=1 if k==0 else 0,
                   remaining_budget=0,charged_damage_cells=(k+1)*7,
                   reward=float(np.float32(-.07))) for k in range(4)]
        self.assertEqual(training_ledger(rows,['a'])['episodes'],1)
        rows[2]['action']=2
        with self.assertRaises(ValueError):training_ledger(rows,['a'])
        rows[2]['action']=0;rows[1]['reward']=-1
        with self.assertRaises(ValueError):training_ledger(rows,['a'])

    def test_constant_greedy_choice_can_have_high_distribution_entropy(self):
        p=np.array([[.32,.34,.34],[.30,.36,.34]])
        # Argmax tie chooses first maximum, as the model's categorical mode does.
        p[0]=[.32,.341,.339]
        result=action_description(p,np.ones_like(p,bool),[1,1])
        self.assertEqual(result['distinct_greedy_actions'],1)
        self.assertGreater(result['mean_entropy_fraction_of_legal_uniform'],.99)
        self.assertLess(result['mean_max_probability'],.4)

    def test_distribution_must_be_normalized_and_respect_mask(self):
        with self.assertRaises(ValueError):action_description([[.5,.7]],[[1,1]],[1])
        with self.assertRaises(ValueError):action_description([[.5,.5]],[[1,0]],[0])
