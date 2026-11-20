"""Opt-in CA observation contract and observation-only scripted comparators.

The current hourly forcing is perfectly known to every policy. No future series or
counterfactual footprint is included. This is a synthetic modelling assumption.
"""
from types import SimpleNamespace

import gymnasium as gym
import numpy as np

from .synthetic_ca import Weather
from .synthetic_env import MAX_UNITS, SyntheticSuppressionEnv, Unit
from .synthetic_heuristics import HEURISTICS

OBSERVATION_VERSION = "ca-native-current-v2"


class CAObservationV2(gym.Wrapper):
    """Keep legacy keys; add exact native categories, unit state and current forcing."""

    def __init__(self, env: SyntheticSuppressionEnv):
        super().__init__(env)
        rows, cols = env.map_shape
        spaces = dict(env.observation_space.spaces)
        spaces.update({
            "native": gym.spaces.Box(-1, 1, (21, rows, cols), dtype=np.float32),
            "unit_state": gym.spaces.Box(-1, np.inf, (MAX_UNITS, 9), dtype=np.float32),
            "forcing": gym.spaces.Box(
                np.array([0, 0, 0, 0], dtype=np.float32),
                np.array([np.inf, 360, 1, 24], dtype=np.float32), dtype=np.float32),
        })
        self.observation_space = gym.spaces.Dict(spaces)

    def action_masks(self):
        return self.env.action_masks()

    def _wrap(self, obs):
        env = self.env
        land, fire = env.land, env.fire
        layers = [fire.burning, fire.ever_burned, fire.line, land.urban, land.water]
        layers += [land.fuel == code for code in range(1, 14)]
        layers += [~land.burnable, np.clip(land.elevation / 5000, -1, 1),
                   np.clip(land.slope_percent / 1000, 0, 1)]
        units = np.zeros((MAX_UNITS, 9), dtype=np.float32)
        for slot, unit in enumerate(env.units):
            units[slot] = [1, unit.active, unit.lost, unit.kind == 1,
                           unit.arrival_minute, unit.row, unit.col, unit.progress_m,
                           unit.action]
        weather = env.spec_now.weather.at(env.decision)
        return dict(obs, native=np.stack(layers).astype(np.float32), unit_state=units,
                    forcing=np.array([weather.wind_midflame_m_s, weather.wind_to_deg,
                                      weather.moisture, weather.local_hour], dtype=np.float32))

    def _info(self, info):
        return dict(info, observation_version=OBSERVATION_VERSION,
                    weather_contract="perfect-current-forcing")

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        return self._wrap(obs), self._info(info)

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        return self._wrap(obs), reward, terminated, truncated, self._info(info)


class _CurrentWeather:
    def __init__(self, forcing):
        self.current = Weather(*(float(x) for x in forcing))

    def at(self, index):
        if index != 0:
            raise IndexError("observation exposes only current forcing")
        return self.current


def observation_view(obs, mask):
    """Minimal facade for existing fixed rules, reconstructed solely from observation.

    Decision is zero because the facade contains one current weather record, not a
    timeline. The rules never use the actual decision number for any other purpose.
    """
    native = obs["native"]
    units = []
    for row in obs["unit_state"]:
        if not row[0]:
            continue
        unit = Unit(kind=int(row[3]), arrival_minute=float(row[4]),
                    row=int(row[5]), col=int(row[6]), active=bool(row[1]),
                    lost=bool(row[2]), progress_m=float(row[7]), action=int(row[8]))
        units.append(unit)
    return SimpleNamespace(
        fire=SimpleNamespace(burning=native[0] > .5, ever_burned=native[1] > .5,
                             line=native[2] > .5),
        land=SimpleNamespace(urban=native[3] > .5), units=units, decision=0,
        spec_now=SimpleNamespace(weather=_CurrentWeather(obs["forcing"])),
        action_masks=lambda: np.asarray(mask, dtype=bool).copy(),
    )


def observed_policy(name, seed=0):
    """All policies have the same (observation, mask) interface; no live-env access."""
    if name == "random":
        rng = np.random.default_rng(seed)

        def random_policy(obs, mask):
            slots = np.asarray(mask).reshape(MAX_UNITS, -1)
            return np.array([rng.choice(np.flatnonzero(row)) for row in slots])
        return random_policy
    rule = HEURISTICS[name]
    return lambda obs, mask: rule(observation_view(obs, mask))


def validate_plan(plan):
    if plan["schema_version"] != "ca-controlled-pilot/2.0":
        raise ValueError("unsupported plan")
    if plan["observation_version"] != OBSERVATION_VERSION:
        raise ValueError("observation version mismatch")
    seen = set()
    for split in ("train", "development", "test"):
        seeds = plan["case_seeds"][split]
        if not seeds or len(set(seeds)) != len(seeds) or seen.intersection(seeds):
            raise ValueError("case splits must be nonempty, unique and disjoint")
        seen.update(seeds)
    previous = []
    for name, count in (("B2", 2), ("B3", 3), ("B4", 4)):
        roster = plan["rosters"][name]
        if len(roster) != count or roster[:len(previous)] != previous:
            raise ValueError("rosters must be nested")
        if roster != [[1, 0]] + [[0, 60 * i] for i in range(1, count)]:
            raise ValueError("unexpected unit types or arrivals")
        previous = roster


def clustered_contrast(candidate, reference):
    """Descriptive paired interval; keep every roster of a case in one cluster."""
    a, b = np.asarray(candidate, float), np.asarray(reference, float)
    if a.shape != b.shape or a.ndim != 2 or not len(a):
        raise ValueError("matched nonempty case by roster matrices required")
    delta = (a - b).mean(axis=1)
    if not np.isfinite(delta).all():
        raise ValueError("finite outcomes required")
    rng = np.random.default_rng(0)
    samples = delta[rng.integers(len(delta), size=(10000, len(delta)))].mean(axis=1)
    return {"mean": float(delta.mean()), "ci95": np.quantile(samples, [.025, .975]).tolist(),
            "n_cases": len(delta)}
