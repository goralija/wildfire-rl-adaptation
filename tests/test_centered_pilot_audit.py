"""Independent audit catches reward/accounting corruption without retraining."""
import unittest
try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest('optional NumPy required: %s'%exc)
from wildfire_rl.centered_pilot_audit import centered_training_ledger,centered_trajectory_score


def example():
    initial=np.zeros((3,3),bool);initial[0,0]=True
    reference=np.repeat(initial[None],5,axis=0)
    burned=reference.copy();line=np.zeros_like(reference)
    for k in range(1,5):reference[k,1,:min(k,3)]=True
    burned[1:,2,2]=True;line[1:,1,0]=True
    return initial,burned,line,reference


class CenteredAuditTests(unittest.TestCase):
    def test_union_keeps_prior_and_rewards_include_private_noop_offset(self):
        initial,burned,line,reference=example()
        score=centered_trajectory_score(initial,burned,line,reference,[-.01,.01,.01,0])
        self.assertEqual(score['raw_damage_cells'],1)
        self.assertEqual(score['charged_damage_cells'],2)
        self.assertEqual(score['charged_saved_cells'],1)
        with self.assertRaises(ValueError):centered_trajectory_score(initial,burned,line,reference,[0,.01,.01,0])
        bad=burned.copy();bad[2:,0,0]=False
        with self.assertRaises(ValueError):centered_trajectory_score(initial,bad,line,reference,[-.01,.01,.01,0])

    def test_invalid_penalty_is_counted_once_and_zero_noop_stays_zero(self):
        initial,burned,line,reference=example()
        score=centered_trajectory_score(initial,burned,line,reference,[-.01,0,.01,0],[False,True,False,False])
        self.assertEqual(score['charged_saved_cells'],1)
        reference=np.repeat(initial[None],5,axis=0)
        self.assertEqual(centered_trajectory_score(initial,burned,np.zeros_like(line),reference,[-.01,0,0,0])['noop_damage_cells'],0)

    def test_training_checks_exact_float32_increment_and_full_horizon(self):
        initial,burned,line,reference=example();rows=[]
        for k,(n,c) in enumerate(zip([1,1,1,0],[2,0,0,0])):
            rows.append(dict(step=k+1,scenario_id='case',action=int(k==0),done=k==3,
                remaining_budget=0,charged_damage_cells=2,charged_increment_cells=c,
                noop_increment_cells=n,original_reward=-c/100.,reward=float(np.float32((n-c)/100.))))
        self.assertEqual(centered_training_ledger(rows,['case'],{'case':reference}),dict(steps=4,episodes=1))
        for field,value in [('remaining_budget',1),('reward',.02),('noop_increment_cells',0),('done',True)]:
            changed=[dict(r) for r in rows];changed[1][field]=value
            with self.assertRaises(ValueError):centered_training_ledger(changed,['case'],{'case':reference})
        with self.assertRaises(ValueError):centered_training_ledger(rows[:3],['case'],{'case':reference})

    def test_nonbinary_reference_or_lost_noop_damage_refused(self):
        initial,burned,line,reference=example();bad=reference.astype(float);bad[1,1,0]=.5
        with self.assertRaises(ValueError):centered_trajectory_score(initial,burned,line,bad,[-.01,.01,.01,0])
        bad=reference.copy();bad[2,1,0]=False
        with self.assertRaises(ValueError):centered_trajectory_score(initial,burned,line,bad,[-.01,.01,.01,0])
