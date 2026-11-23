"""Opt-in reward adapter is usable by the same masked PPO and safe NPZ loader."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

try:
    import torch
    import sb3_contrib
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest('optional SB3/Torch required: %s' % exc)

from test_common_control import environment
from test_centered_control import trajectory
from wildfire_rl.centered_control import CenteredControlEnv,REWARD_VERSION
from wildfire_rl.common_control_rl import create_model,save_policy_arrays,load_policy_arrays,policy_digest
from wildfire_rl.ppo_signal_rl import collect_initial
from wildfire_rl.ppo_signal_diagnosis import episodic_returns
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_centered_ppo_pilot as runner


class CenteredPPOTests(unittest.TestCase):
    def test_recorded_stop_prevents_collecting_more_training_steps(self):
        torch.set_num_threads(1)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);job=root/'job';job.mkdir();(root/'stop.json').write_text('{}')
            model=create_model(CenteredControlEnv(environment(),trajectory()),seed=43)
            callback=runner.LearningCallback(job,{},'fake',43,{})
            with self.assertRaisesRegex(RuntimeError,'global stop'):model.learn(16,callback=callback)
            self.assertFalse(callback.rows);self.assertFalse(model.policy.optimizer.state)

    def test_changed_first_rollout_stops_before_any_optimizer_update(self):
        torch.set_num_threads(1)
        raw,rows=collect_initial(create_model(environment(),seed=43))
        shifted,_=collect_initial(create_model(CenteredControlEnv(environment(),trajectory()),seed=43))
        probe=dict(raw)
        for key in ('rewards','returns','advantages'):probe['centered_'+key]=shifted[key]
        probe['observations']=probe['observations'].copy();probe['observations'][0,0]=1
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);job=root/'job';job.mkdir();oldjob=root/'job-fake-43';oldjob.mkdir()
            (oldjob/'training.json').write_text(json.dumps(rows));np.savez_compressed(root/'probe-fake-43.npz',**probe)
            model=create_model(CenteredControlEnv(environment(),trajectory()),seed=43)
            before=policy_digest(model);callback=runner.LearningCallback(job,{},'fake',43,{})
            with patch.object(runner,'SIGNAL',root),patch.object(runner,'PARENT',root):
                with self.assertRaises(AssertionError):model.learn(16,callback=callback)
            self.assertEqual(model._n_updates,0);self.assertFalse(model.policy.optimizer.state)
            self.assertEqual(before,policy_digest(model));self.assertFalse((job/'first-rollout.json').exists())

    def test_partial_job_and_duplicate_coordinator_refused_before_workers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'guard.json').write_text('{}')
            plan=dict(model_seeds=[17]);partial=root/'job-simfire-17';partial.mkdir()
            with patch.object(runner,'context',return_value=(plan,{}, {},{})),\
                 patch.object(runner,'checked_preflight'),patch.object(runner,'ProcessPoolExecutor') as pool:
                with self.assertRaisesRegex(RuntimeError,'partial job'):runner.run(root)
                pool.assert_not_called();partial.rmdir();(root/'coordinator.lock').write_text('123')
                with self.assertRaises(FileExistsError):runner.run(root)
                pool.assert_not_called()

    def test_initial_collection_preserves_actions_and_changes_only_rewards(self):
        torch.set_num_threads(1)
        raw=create_model(environment(),seed=17)
        original,rows=collect_initial(raw)
        centered=create_model(CenteredControlEnv(environment(),trajectory()),seed=17)
        shifted,newrows=collect_initial(centered)
        self.assertEqual(policy_digest(raw),policy_digest(centered))
        for key in ('observations','actions','action_masks','values','log_probs','episode_starts','permutation'):
            np.testing.assert_array_equal(original[key],shifted[key])
        for a,b in zip(rows,newrows):
            self.assertEqual({k:v for k,v in a.items() if k!='reward'},
                             {k:v for k,v in b.items() if k!='reward'})
        offset=np.tile(np.array([4,4,4,3])/100.,4)
        np.testing.assert_allclose(shifted['rewards'],original['rewards']+offset,atol=1e-8,rtol=0)
        np.testing.assert_allclose(shifted['returns'],episodic_returns(shifted['rewards']),atol=1e-7,rtol=0)
        self.assertFalse(centered.policy.optimizer.state)

    def test_bounded_training_roundtrip_and_reward_contract_guard(self):
        torch.set_num_threads(1)
        env=CenteredControlEnv(environment(),trajectory())
        model=create_model(env,seed=29);before=policy_digest(model)
        model.learn(32)
        self.assertNotEqual(before,policy_digest(model))
        self.assertEqual(model.num_timesteps,32)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'policy.npz';contract=dict(reward=REWARD_VERSION,steps=32)
            save_policy_arrays(model,path,contract)
            restored=load_policy_arrays(path,contract)
            self.assertEqual(policy_digest(model),policy_digest(restored))
            with self.assertRaises(ValueError):load_policy_arrays(path,dict(reward='common-charged-increment-v1',steps=32))
            obs,_=env.reset()
            for k in range(4):
                mask=env.action_masks();action=int(restored.predict(obs,action_masks=mask,deterministic=True)[0])
                self.assertTrue(mask[action]);obs,reward,done,trunc,info=env.step(action)
                self.assertEqual(done,k==3);self.assertFalse(trunc);self.assertTrue(np.isfinite(reward))
                self.assertFalse(info['invalid_action']);self.assertGreaterEqual(info['remaining_budget'],0)
