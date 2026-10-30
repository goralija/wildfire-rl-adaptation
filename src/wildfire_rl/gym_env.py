"""Optional modern Gymnasium adapter; incompatible with legacy Firehose weights."""

import gymnasium as gym
import numpy as np

from .simulator import GridFire, Scenario


class GridFireEnv(gym.Env):
    metadata = {'render_modes': []}

    def __init__(self, scenario: Scenario, budgets=(0, 2, 4, 8),
                 scenario_seeds=tuple(range(32)), priority_weight=0):
        for values in (budgets, scenario_seeds):
            if not values or any(type(v) is not int or v < 0 for v in values):
                raise ValueError('budgets and scenario seeds must be nonnegative integers')
        self.scenario = scenario
        self.budgets = tuple(budgets)
        self.scenario_seeds = tuple(scenario_seeds)
        self.priority_weight = priority_weight
        n = scenario.rows * scenario.cols
        self.action_space = gym.spaces.Discrete(n + 1)
        self.observation_space = gym.spaces.Dict({
            'grid': gym.spaces.Box(0, 1, shape=(4, n), dtype=np.float32),
            'budget': gym.spaces.Box(0, 1, shape=(2,), dtype=np.float32),
            'time': gym.spaces.Box(0, 1, shape=(1,), dtype=np.float32),
        })

    def _observation(self):
        env = self.engine
        n = env.noop
        return dict(grid=np.asarray([
            np.asarray(env.state) / 4,
            np.minimum(env.age, self.scenario.burn_duration) / self.scenario.burn_duration,
            [int(i in env.ever_burned) for i in range(n)],
            [int(i in self.scenario.priority) for i in range(n)],
        ], dtype=np.float32), budget=np.asarray(
            [env.budget, env.remaining_budget], dtype=np.float32) / max(1, max(self.budgets)),
                    time=np.asarray([env.steps / self.scenario.horizon], dtype=np.float32))

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if options:
            raise ValueError('reset options are not supported; use constructor scenario_seeds')
        budget = int(self.np_random.choice(self.budgets))
        scenario_seed = int(self.np_random.choice(self.scenario_seeds))
        self.engine = GridFire(self.scenario, budget, self.priority_weight)
        self.engine.reset(scenario_seed)
        self._done = False
        return self._observation(), self.engine.metrics()

    def action_masks(self):
        return np.asarray(self.engine.action_masks(), dtype=bool)

    def step(self, action):
        if self._done:
            raise RuntimeError('episode is done; call reset')
        if not self.action_space.contains(action):
            raise ValueError('action is outside Discrete space')
        action = int(action)
        invalid = not self.action_masks()[action]
        # Gym checkers may sample masked cells. Such actions are explicit penalized
        # no-ops here; the strict simulator API raises instead. Learning uses masks.
        # A fire can end during the action-free warmup. Expose its terminal
        # transition once so an RL collector can reset rather than crash.
        if self.engine.terminated:
            reward = 0.0
        else:
            reward = self.engine.step(self.engine.noop if invalid else action)
        if invalid:
            reward -= 1 / self.engine.fuel_count
        info = self.engine.metrics() | dict(invalid_action=invalid)
        self._done = self.engine.terminated or self.engine.truncated
        return self._observation(), reward, self.engine.terminated, self.engine.truncated, info
