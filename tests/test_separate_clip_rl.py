"""Tests precede opt-in optimizer behavior; the frozen base class stays intact."""
import ast
import copy
import inspect
import hashlib
import importlib.metadata
from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import patch
try:
    import numpy as np
    import torch
    from sb3_contrib import MaskablePPO
except ImportError as exc:
    raise unittest.SkipTest('optional SB3/Torch required: %s'%exc)
from test_common_control import environment
from wildfire_rl.common_control_rl import create_model as base_model,policy_digest,save_policy_arrays,load_policy_arrays
from wildfire_rl.ppo_signal_rl import collect_initial,gradient_probe
from wildfire_rl.separate_clip_rl import SeparateClipPPO,clip_named_gradients,create_model,CLIPPING_VERSION,PINNED_TRAIN_AST_SHA256
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_separate_clip_pilot as runner


class SeparateClipTests(unittest.TestCase):
    def test_disjoint_bounds_isolate_actor_and_critic(self):
        def run(scale,critic_scale=1.):
            a=torch.nn.Parameter(torch.ones(2));b=torch.nn.Parameter(torch.ones(2))
            a.grad=torch.tensor([3.,4.])*scale;b.grad=torch.tensor([6.,8.])*critic_scale
            result=clip_named_gradients([('action_net.weight',a),('value_net.weight',b)],.5)
            self.assertLessEqual(float(a.grad.norm()),.500001);self.assertLessEqual(float(b.grad.norm()),.500001)
            return a.grad,b.grad,result
        a,b,r=run(1.);aa,bb,rr=run(100.)
        torch.testing.assert_close(a,aa,atol=1e-7,rtol=1e-6);torch.testing.assert_close(b,bb,atol=0,rtol=0)
        self.assertAlmostEqual(r['actor']['before'],5.);self.assertAlmostEqual(rr['actor']['before'],500.)
        self.assertAlmostEqual(r['critic']['before'],10.)
        aaa,bbb,_=run(1.,100.)
        torch.testing.assert_close(a,aaa,atol=0,rtol=0);torch.testing.assert_close(b,bbb,atol=1e-7,rtol=1e-6)

    def test_recorded_stop_prevents_more_training_steps(self):
        torch.set_num_threads(1)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);job=root/'job';job.mkdir();(root/'stop.json').write_text('{}')
            model=create_model(environment(),seed=17);cb=runner.LearningCallback(job,{},'fake',17,{})
            with self.assertRaisesRegex(RuntimeError,'global stop'):model.learn(16,callback=cb)
            self.assertFalse(cb.rows);self.assertFalse(model.policy.optimizer.state)

    def test_changed_first_buffer_is_refused_before_optimizer_update(self):
        torch.set_num_threads(1);batch,_=collect_initial(base_model(environment(),seed=29))
        batch['observations'][0,0]=1.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);job=root/'job';job.mkdir();np.savez_compressed(root/'probe-fake-29.npz',**batch)
            model=create_model(environment(),seed=29);before=policy_digest(model);cb=runner.LearningCallback(job,{},'fake',29,{})
            with patch.object(runner,'SIGNAL',root):
                with self.assertRaises(AssertionError):model.learn(16,callback=cb)
            self.assertEqual(policy_digest(model),before);self.assertEqual(model._n_updates,0)
            self.assertFalse(model.policy.optimizer.state);self.assertFalse(model.clip_history)

    def test_partial_job_and_duplicate_coordinator_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'guard.json').write_text('{}');partial=root/'job-simfire-17';partial.mkdir()
            with patch.object(runner,'context',return_value=({'model_seeds':[17]}, {},{},{})),\
                 patch.object(runner,'checked_preflight'),patch.object(runner,'ProcessPoolExecutor') as pool:
                with self.assertRaisesRegex(RuntimeError,'partial job'):runner.run(root)
                pool.assert_not_called();partial.rmdir();(root/'coordinator.lock').write_text('123')
                with self.assertRaises(FileExistsError):runner.run(root)
                pool.assert_not_called()

    def test_unknown_shared_empty_or_nonfinite_group_refused_before_mutation(self):
        a=torch.nn.Parameter(torch.ones(1));b=torch.nn.Parameter(torch.ones(1));a.grad=torch.ones(1);b.grad=torch.ones(1)
        for named in [[],[('action_net.weight',a)],[('unexpected',a),('value_net.weight',b)],
                      [('action_net.weight',a),('value_net.weight',a)]]:
            with self.assertRaises(ValueError):clip_named_gradients(named,.5)
        b.grad.fill_(float('nan'))
        with self.assertRaises(ValueError):clip_named_gradients([('action_net.weight',a),('value_net.weight',b)],.5)
        self.assertEqual(float(a.grad),1.)

    def test_train_source_matches_pinned271_with_only_clip_expression(self):
        original=ast.parse(textwrap.dedent(inspect.getsource(MaskablePPO.train)))
        candidate=ast.parse(textwrap.dedent(inspect.getsource(SeparateClipPPO.train)))
        expected=ast.parse('th.nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)').body[0]
        class Restore(ast.NodeTransformer):
            def visit_Expr(self,node):
                if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='_clip_gradients':
                    return copy.deepcopy(expected)
                return self.generic_visit(node)
        candidate=Restore().visit(candidate)
        restored=ast.dump(candidate,include_attributes=False)
        # Python3.12 adds an empty generic-type field to ordinary FunctionDef.
        canonical=restored.replace(', type_params=[]','')
        self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(),PINNED_TRAIN_AST_SHA256)
        # Modern environment tests tensor behavior, not compatibility with its
        # different upstream train method. The experiment guard requires2.7.1.
        if importlib.metadata.version('sb3-contrib')=='2.7.1':
            self.assertEqual(ast.dump(original,include_attributes=False),restored)

    def test_global_control_matches_upstream_weights_and_adam_after_two_epochs(self):
        torch.set_num_threads(1)
        class GlobalControl(SeparateClipPPO):
            def _clip_gradients(self):torch.nn.utils.clip_grad_norm_(self.policy.parameters(),self.max_grad_norm)
        a=base_model(environment(),seed=17);data,rows=collect_initial(a);state=np.random.get_state();a.train()
        from wildfire_rl.common_control_rl import PPO_SETTINGS
        b=GlobalControl('MlpPolicy',environment(),policy_kwargs=dict(net_arch=dict(pi=[64,64],vf=[64,64])),
            seed=17,device='cpu',verbose=0,**PPO_SETTINGS)
        other,other_rows=collect_initial(b)
        for key in data:np.testing.assert_array_equal(data[key],other[key])
        self.assertEqual(rows,other_rows);np.random.set_state(state);b.train()
        self.assertEqual(policy_digest(a),policy_digest(b))
        for key,values in a.policy.optimizer.state_dict()['state'].items():
            for name,tensor in values.items():torch.testing.assert_close(tensor,b.policy.optimizer.state_dict()['state'][key][name],atol=0,rtol=0)

    def test_first_separate_adam_step_matches_independent_probe(self):
        torch.set_num_threads(1)
        model=create_model(environment(),seed=29);batch,_=collect_initial(model)
        reference=base_model(seed=29);gradient_probe(reference,batch,'separate')
        model.n_epochs=1;model.train()
        self.assertEqual(policy_digest(model),policy_digest(reference));self.assertEqual(len(model.clip_history),1)
        for group in ('actor','critic'):self.assertLessEqual(model.clip_history[0][group]['after'],.500001)

    def test_masked_training_and_guarded_numeric_roundtrip(self):
        torch.set_num_threads(1);env=environment();model=create_model(env,seed=43);initial=policy_digest(model);model.learn(32)
        self.assertNotEqual(initial,policy_digest(model));self.assertTrue(model.clip_history)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'policy.npz';contract=dict(clipping=CLIPPING_VERSION,steps=32)
            save_policy_arrays(model,p,contract);restored=load_policy_arrays(p,contract)
            self.assertEqual(policy_digest(model),policy_digest(restored))
            with self.assertRaises(ValueError):load_policy_arrays(p,dict(clipping='global',steps=32))
            obs,_=env.reset()
            for k in range(4):
                mask=env.action_masks();action=int(restored.predict(obs,action_masks=mask,deterministic=True)[0])
                self.assertTrue(mask[action]);obs,_,done,trunc,info=env.step(action)
                self.assertEqual(done,k==3);self.assertFalse(trunc);self.assertFalse(info['invalid_action'])
