import unittest
try:
    import torch
    import numpy as np
    import sb3_contrib
except ImportError as exc:
    raise unittest.SkipTest('optional Torch/SB3 required: %s'%exc)
from test_common_control import environment
from wildfire_rl.common_control_rl import create_model,policy_digest,PPO_SETTINGS
from wildfire_rl.ppo_signal_rl import collect_initial,gradient_probe
from wildfire_rl.ppo_signal_diagnosis import episodic_returns


class GradientProbeTests(unittest.TestCase):
    def data(self):
        torch.set_num_threads(1)
        model=create_model(environment(),seed=17,settings=dict(PPO_SETTINGS,n_epochs=1))
        initial=policy_digest(model);data,rows=collect_initial(model)
        self.assertEqual(initial,policy_digest(model));self.assertEqual(model._n_updates,0)
        return model,data,rows

    def test_collection_changes_no_weights_and_complete_returns_match(self):
        model,data,rows=self.data()
        self.assertEqual(len(rows),16);self.assertEqual(sum(r['done'] for r in rows),4)
        np.testing.assert_allclose(episodic_returns(data['rewards']),data['returns'],atol=1e-6)
        model.env.close()

    def test_manual_global_first_adam_update_matches_actual_maskable_ppo(self):
        actual,data,_=self.data();state=np.random.get_state()
        # Inject a large critic target to exercise shared clipping, not just the no-clip path.
        data['returns']=data['returns']*10000
        data['advantages']=data['returns']-data['values']
        actual.rollout_buffer.returns=data['returns'].reshape(16,1).copy()
        actual.rollout_buffer.advantages=data['advantages'].reshape(16,1).copy()
        manual=create_model(seed=17,settings=dict(PPO_SETTINGS,n_epochs=1))
        report=gradient_probe(manual,data,'global')
        self.assertLess(report['actor']['clip_fraction'],.1)
        np.random.set_state(state);actual.train()
        for key,value in actual.policy.state_dict().items():
            torch.testing.assert_close(value,manual.policy.state_dict()[key],atol=2e-7,rtol=1e-5)
        actual.env.close()

    def test_separate_clipping_reveals_coupling_without_accepting_a_policy(self):
        original,data,_=self.data();data['returns']*=10000;data['advantages']=data['returns']-data['values']
        a=create_model(seed=17);b=create_model(seed=17)
        shared=gradient_probe(a,data,'global');separate=gradient_probe(b,data,'separate')
        self.assertLess(shared['actor']['gradient_after'],separate['actor']['gradient_after'])
        self.assertLess(shared['actor']['parameter_step_l2'],separate['actor']['parameter_step_l2'])
        original.env.close()
