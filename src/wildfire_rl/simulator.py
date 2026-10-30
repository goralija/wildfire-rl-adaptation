"""Small synchronous cellular automaton for pipeline tests, not fire prediction."""

from dataclasses import dataclass
from hashlib import blake2b
from math import isfinite

FUEL, FIRE, BURNED, TREATED, NONFUEL = range(5)


@dataclass(frozen=True)
class Scenario:
    rows: int = 20
    cols: int = 20
    ignition: tuple[int, ...] = (210,)
    nonfuel: tuple[int, ...] = ()
    priority: tuple[int, ...] = ()
    spread_probability: float = 0.35
    burn_duration: int = 3
    warmup_steps: int = 2
    horizon: int = 80

    def __post_init__(self):
        for name in ('rows', 'cols', 'burn_duration', 'horizon'):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f'{name} must be a positive integer')
        if type(self.warmup_steps) is not int or self.warmup_steps < 0:
            raise ValueError('warmup_steps must be a nonnegative integer')
        if not isfinite(self.spread_probability) or not 0 <= self.spread_probability <= 1:
            raise ValueError('spread_probability must be in [0, 1]')
        for name in ('ignition', 'nonfuel', 'priority'):
            cells = getattr(self, name)
            if len(set(cells)) != len(cells) or any(
                type(i) is not int or not 0 <= i < self.rows * self.cols for i in cells
            ):
                raise ValueError(f'invalid or duplicate {name} cells')
        if not self.ignition or set(self.ignition) & set(self.nonfuel):
            raise ValueError('ignition must contain burnable cells')
        if set(self.priority) & set(self.nonfuel):
            raise ValueError('priority cells must be burnable')


class GridFire:
    def __init__(self, scenario: Scenario, budget: int, priority_weight: float = 0):
        if type(budget) is not int or budget < 0:
            raise ValueError('budget must be a nonnegative integer')
        if not isfinite(priority_weight) or priority_weight < 0:
            raise ValueError('priority_weight must be finite and nonnegative')
        self.scenario = scenario
        self.budget = budget
        self.priority_weight = priority_weight
        self.noop = scenario.rows * scenario.cols
        self.fuel_count = self.noop - len(scenario.nonfuel)

    def reset(self, seed: int = 0):
        self.seed = seed
        self.state = [FUEL] * self.noop
        self.age = [0] * self.noop
        for i in self.scenario.nonfuel:
            self.state[i] = NONFUEL
        for i in self.scenario.ignition:
            self.state[i] = FIRE
        self.ever_burned = set(self.scenario.ignition)
        self.remaining_budget = self.budget
        self.steps = self.tick = 0
        for _ in range(self.scenario.warmup_steps):
            self._spread()
        self._update_done()
        return list(self.state)

    def neighbors(self, cell):
        row, col = divmod(cell, self.scenario.cols)
        for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
            r, c = row + dr, col + dc
            if 0 <= r < self.scenario.rows and 0 <= c < self.scenario.cols:
                yield r * self.scenario.cols + c

    def _spread(self):
        burning = [i for i, status in enumerate(self.state) if status == FIRE]
        newly_burning = set()
        for source in burning:
            for target in self.neighbors(source):
                if self.state[target] != FUEL:
                    continue
                # Common random numbers keyed by edge and time. Different policies
                # cannot shift a shared sequential RNG by taking different actions.
                key = f'{self.seed}:{self.tick}:{source}:{target}'.encode()
                draw = int.from_bytes(blake2b(key, digest_size=8).digest(), 'big') / 2**64
                if draw < self.scenario.spread_probability:
                    newly_burning.add(target)
            self.age[source] += 1
        for source in burning:
            if self.age[source] >= self.scenario.burn_duration:
                self.state[source] = BURNED
        for target in newly_burning:
            self.state[target] = FIRE
        self.ever_burned.update(newly_burning)
        self.tick += 1

    def action_masks(self):
        return [self.remaining_budget > 0 and status in (FUEL, FIRE)
                for status in self.state] + [True]

    def _update_done(self):
        self.terminated = FIRE not in self.state
        self.truncated = self.steps >= self.scenario.horizon and not self.terminated

    def step(self, action: int) -> float:
        if self.terminated or self.truncated:
            raise RuntimeError('episode is done; call reset')
        if type(action) is not int or not 0 <= action <= self.noop:
            raise ValueError('action must be a cell index or the no-op index')
        if not self.action_masks()[action]:
            raise ValueError('invalid cell or exhausted intervention budget')
        previous = set(self.ever_burned)
        if action != self.noop:
            self.state[action] = TREATED
            self.remaining_budget -= 1
        self._spread()
        self.steps += 1
        self._update_done()
        new_damage = self.ever_burned - previous
        priority_damage = len(new_damage & set(self.scenario.priority))
        return (-len(new_damage) / self.fuel_count
                - self.priority_weight * priority_damage / max(1, len(self.scenario.priority)))

    def metrics(self):
        priority_burned = len(self.ever_burned & set(self.scenario.priority))
        return dict(burned_cells=len(self.ever_burned),
                    burned_fraction=len(self.ever_burned) / self.fuel_count,
                    priority_burned_cells=priority_burned,
                    priority_burned_fraction=priority_burned / max(1, len(self.scenario.priority)),
                    interventions=self.budget - self.remaining_budget,
                    steps=self.steps, terminated=self.terminated, truncated=self.truncated)
