import random
import unittest

from wildfire_rl.simulator import GridFire, Scenario
from wildfire_rl.policies import choose_action


class SimulatorTests(unittest.TestCase):
    def scenario(self, **kwargs):
        values = dict(rows=3, cols=3, ignition=(4,), priority=(0,),
                      spread_probability=1.0, burn_duration=2, warmup_steps=0,
                      horizon=10)
        return Scenario(**(values | kwargs))

    def test_spread_is_synchronous(self):
        env = GridFire(self.scenario(), budget=0)
        env.reset(seed=3)
        env.step(env.noop)
        self.assertEqual(env.ever_burned, {1, 3, 4, 5, 7})

    def test_extinguishing_does_not_erase_damage(self):
        env = GridFire(self.scenario(), budget=1)
        env.reset(seed=3)
        env.step(4)
        self.assertEqual(env.metrics()['burned_cells'], 1)
        self.assertTrue(env.terminated)
        self.assertEqual(env.metrics()['interventions'], 1)

    def test_budget_exhaustion_does_not_end_episode(self):
        env = GridFire(self.scenario(), budget=1)
        env.reset(seed=3)
        env.step(0)
        self.assertFalse(env.terminated or env.truncated)
        self.assertEqual(env.action_masks(), [False] * 9 + [True])
        env.step(env.noop)
        self.assertGreater(env.metrics()['burned_cells'], 5)
        self.assertEqual(env.remaining_budget, 0)

    def test_invalid_actions_do_not_spend_budget_or_advance_time(self):
        env = GridFire(self.scenario(nonfuel=(0,), priority=(2,)), budget=2)
        env.reset(seed=4)
        for action in (-1, 0, 10):
            with self.assertRaises(ValueError):
                env.step(action)
        env.step(1)
        before = (env.steps, env.remaining_budget)
        with self.assertRaises(ValueError):
            env.step(1)
        self.assertEqual((env.steps, env.remaining_budget), before)

    def test_horizon_is_truncation_not_containment(self):
        env = GridFire(self.scenario(horizon=1), budget=0)
        env.reset(seed=4)
        env.step(env.noop)
        self.assertTrue(env.truncated)
        self.assertFalse(env.terminated)
        with self.assertRaises(RuntimeError):
            env.step(env.noop)

    def test_reward_tracks_incremental_damage_and_priority(self):
        env = GridFire(self.scenario(priority=(1,)), budget=0, priority_weight=2)
        env.reset(seed=4)
        reward = env.step(env.noop)
        self.assertAlmostEqual(reward, -4 / 9 - 2)
        self.assertEqual(env.metrics()['priority_burned_fraction'], 1)

    def test_barriers_do_not_count_as_fuel(self):
        env = GridFire(self.scenario(nonfuel=(0, 2), priority=(1,)), budget=0)
        env.reset(seed=3)
        self.assertAlmostEqual(env.metrics()['burned_fraction'], 1 / 7)

    def test_reset_replays_same_seed(self):
        env = GridFire(self.scenario(spread_probability=.45), budget=2)
        def rollout():
            env.reset(seed=91)
            result = []
            while not (env.terminated or env.truncated):
                env.step(env.noop)
                result.append(tuple(env.state))
            return result
        self.assertEqual(rollout(), rollout())

    def test_policy_rng_cannot_change_fire_randomness(self):
        a = GridFire(self.scenario(spread_probability=.5), budget=0)
        b = GridFire(self.scenario(spread_probability=.5), budget=0)
        a.reset(seed=13)
        b.reset(seed=13)
        rng = random.Random(17)
        while not (a.terminated or a.truncated):
            for _ in range(31):
                rng.random()
            a.step(a.noop)
            b.step(b.noop)
            self.assertEqual(a.state, b.state)

    def test_baselines_choose_only_available_actions(self):
        for policy in ('none', 'random', 'min_l2', 'max_l2', 'priority'):
            env = GridFire(self.scenario(warmup_steps=1), budget=2)
            env.reset(seed=0)
            rng = random.Random(2)
            while not (env.terminated or env.truncated):
                action = choose_action(env, policy, rng)
                self.assertTrue(env.action_masks()[action])
                env.step(action)
            self.assertLessEqual(env.metrics()['interventions'], 2)

    def test_invalid_scenarios_and_budgets(self):
        for kwargs in ({'rows': 0}, {'spread_probability': 2},
                       {'ignition': (9,)}, {'nonfuel': (4,)},
                       {'priority': (0,), 'nonfuel': (0,)}, {'horizon': 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.scenario(**kwargs)
        with self.assertRaises(ValueError):
            GridFire(self.scenario(), budget=-1)


if __name__ == '__main__':
    unittest.main()
