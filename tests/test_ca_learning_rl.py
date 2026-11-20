import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    import torch
    import sb3_contrib
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest("optional SB3/Torch required: %s" % exc)

from wildfire_rl.ca_learning import CATrainingEnv
from wildfire_rl.ca_learning_rl import create_model, save_policy_arrays, load_policy_arrays


class SafeLearningSmokeTest(unittest.TestCase):
    def test_default_bc_model_has_the_registered_two_rollout_slots(self):
        torch.set_num_threads(1)
        from stable_baselines3.common.vec_env import DummyVecEnv
        root = Path(__file__).resolve().parents[1]
        plan = json.loads((root/'configs/frozen/ca-controlled-pilot-v2.json').read_text())
        model = create_model(overrides={'n_steps':4,'batch_size':4,'n_epochs':1})
        self.assertEqual(model.n_envs,2)
        vec = DummyVecEnv([lambda:CATrainingEnv(plan,rank=0,stride=2),
                           lambda:CATrainingEnv(plan,rank=1,stride=2)])
        model.set_env(vec)
        model.learn(8)
        self.assertEqual(model.num_timesteps,8)
        vec.close()

    def test_positive_saved_damage_cannot_hide_worse_safety_in_one_seed(self):
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
        from run_ca_learning_pilot import summarize
        names = ['B2','B3','B4']
        baseline = {'plan':{'rosters':dict.fromkeys(names)},'cases':[]}
        cases = []
        for _ in range(2):
            baseline['cases'].append({'rows':{b:{'direct_flank':dict(
                saved_fraction=.1,close_calls=0,units_lost=0)} for b in names}})
            cases.append({'rows':{b:{'%s-%d'%(p,s):dict(saved_fraction=.2,
                close_calls=0,units_lost=0) for p in ('bc','ppo') for s in (17,29,43)}
                for b in names}})
        plan = {'model_seeds':[17,29,43]}
        self.assertTrue(summarize(cases,baseline,plan,None)['phases']['ppo']['continuation_signal'])
        cases[0]['rows']['B2']['ppo-43']['close_calls'] = 1
        result = summarize(cases,baseline,plan,None)
        self.assertGreater(result['phases']['ppo']['vs_reference']['ci95'][0],0)
        self.assertFalse(result['phases']['ppo']['continuation_signal'])
        self.assertTrue(result['phases']['bc']['continuation_signal'])

    def test_masked_learning_and_numeric_checkpoint_roundtrip(self):
        torch.set_num_threads(1)
        root = Path(__file__).resolve().parents[1]
        plan = json.loads((root / "configs/frozen/ca-controlled-pilot-v2.json").read_text())
        env = CATrainingEnv(plan)
        model = create_model(env, seed=7, overrides={"n_steps":8,"batch_size":8,"n_epochs":1})
        model.learn(8)
        obs, _ = env.reset()
        obs, _, _, _, _ = env.step(np.zeros(4,dtype=int))
        mask = env.action_masks()
        self.assertGreater(int(mask.sum()),4)
        action = model.predict(obs, action_masks=mask, deterministic=True)[0]
        self.assertTrue(mask.reshape(4,17)[np.arange(4),action].all())
        contract = {"observation":"test-v2","encoder":"test","plan_sha":"abc"}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'weights.npz'
            save_policy_arrays(model, path, contract)
            torch_state = torch.random.get_rng_state().clone()
            numpy_state = np.random.get_state()
            loaded = load_policy_arrays(path, contract)
            self.assertTrue(torch.equal(torch_state,torch.random.get_rng_state()))
            np.testing.assert_array_equal(numpy_state[1],np.random.get_state()[1])
            for key,value in model.policy.state_dict().items():
                self.assertTrue(torch.equal(value,loaded.policy.state_dict()[key]),key)
            np.testing.assert_array_equal(action, loaded.predict(obs, action_masks=mask,
                                                                deterministic=True)[0])
            with patch('numpy.load', side_effect=AssertionError('must reject before reading')):
                with self.assertRaises(ValueError):
                    load_policy_arrays(path, dict(contract, encoder='legacy'))
            with path.open('ab') as handle:
                handle.write(b'tamper')
            with self.assertRaises(ValueError):
                load_policy_arrays(path, contract)
