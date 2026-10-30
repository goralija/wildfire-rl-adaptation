import importlib.util
import tempfile
from pathlib import Path
import unittest


@unittest.skipUnless(importlib.util.find_spec('sb3_contrib'), 'optional RL extra not installed')
class GymTests(unittest.TestCase):
    def make_env(self, **kwargs):
        from wildfire_rl.gym_env import GridFireEnv
        from wildfire_rl.simulator import Scenario
        return GridFireEnv(Scenario(rows=3, cols=3, ignition=(4,), priority=(0,),
                                    spread_probability=1, warmup_steps=0, horizon=8),
                           **kwargs)

    def test_gym_contract_and_seeded_reset(self):
        import numpy as np
        from gymnasium.utils.env_checker import check_env
        env = self.make_env(budgets=(0, 1), scenario_seeds=(20, 21))
        check_env(env, skip_render_check=True)
        a, _ = env.reset(seed=4)
        b, _ = env.reset(seed=4)
        for key in a:
            np.testing.assert_array_equal(a[key], b[key])
        self.assertTrue(env.observation_space.contains(a))

    def test_zero_budget_mask_and_invalid_gym_action_advance_as_noop(self):
        env = self.make_env(budgets=(0,))
        env.reset(seed=1)
        self.assertEqual(env.action_masks().tolist(), [False] * 9 + [True])
        obs, reward, terminated, truncated, info = env.step(0)
        self.assertTrue(info['invalid_action'])
        self.assertEqual(info['interventions'], 0)
        self.assertEqual(info['burned_cells'], 5)
        self.assertFalse(terminated or truncated)

    def test_masks_save_load_and_short_learning(self):
        from sb3_contrib import MaskablePPO
        env = self.make_env(budgets=(1,))
        model = MaskablePPO('MultiInputPolicy', env, n_steps=8, batch_size=8,
                            n_epochs=1, seed=3, device='cpu', verbose=0,
                            policy_kwargs=dict(net_arch=[16]))
        model.learn(16)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'smoke'
            model.save(path)
            loaded = MaskablePPO.load(path, env=env)
            obs, _ = env.reset(seed=8)
            action, _ = loaded.predict(obs, action_masks=env.action_masks(), deterministic=True)
            self.assertTrue(env.action_masks()[int(action)])

    def test_fire_extinguished_during_warmup_yields_one_terminal_transition(self):
        from wildfire_rl.gym_env import GridFireEnv
        from wildfire_rl.simulator import Scenario
        env = GridFireEnv(Scenario(rows=2, cols=2, ignition=(0,),
                                  spread_probability=0, warmup_steps=3), budgets=(0,))
        env.reset(seed=1)
        obs, reward, terminated, truncated, info = env.step(env.engine.noop)
        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertEqual(reward, 0)
        self.assertEqual(info['burned_cells'], 1)
        with self.assertRaises(RuntimeError):
            env.step(env.engine.noop)
