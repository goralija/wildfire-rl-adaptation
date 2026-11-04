"""Scripted suppression tactics for the synthetic CA environment (ADR-028).

They read only what the agent's observation also encodes: the current fire, line,
fuel, units and current weather. None of them sees the no-op rollout or future weather.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple

import numpy as np

from .synthetic_ca import OFFSETS
from .synthetic_env import ACTIONS_PER_UNIT, MAX_UNITS, SyntheticSuppressionEnv, Unit

STANDOFF_CELLS = 3
INDIRECT_STANDOFF_CELLS = 8


def _direction_toward(mask: np.ndarray, unit: Unit, target: Tuple[float, float],
                      build: bool) -> int:
    """Allowed move/build action whose step lands closest to ``target`` (0 if none helps)."""
    best, best_distance = 0, np.hypot(target[0] - unit.row, target[1] - unit.col)
    base = 9 if build else 1
    for k, (dr, dc) in enumerate(OFFSETS):
        if not mask[base + k]:
            continue
        distance = np.hypot(target[0] - unit.row - dr, target[1] - unit.col - dc)
        if distance < best_distance - 1e-9:
            best, best_distance = base + k, distance
    return best


def _heading_action(mask: np.ndarray, heading: Tuple[float, float], build: bool) -> int:
    """Allowed action whose offset best matches a unit vector (row, col)."""
    base = 9 if build else 1
    scores = []
    for k, (dr, dc) in enumerate(OFFSETS):
        norm = np.hypot(dr, dc)
        scores.append(((dr * heading[0] + dc * heading[1]) / norm, base + k))
    for score, action in sorted(scores, reverse=True):
        if score > 0 and mask[action]:
            return action
    return 0


def _fire_geometry(env: SyntheticSuppressionEnv):
    burning = np.argwhere(env.fire.burning)
    burned = np.argwhere(env.fire.ever_burned)
    centre = burned.mean(axis=0) if len(burned) else None
    return burning, burned, centre


def _wind_vector(env: SyntheticSuppressionEnv) -> np.ndarray:
    weather = env.spec_now.weather.at(env.decision)
    bearing = np.deg2rad(weather.wind_to_deg)
    return np.array((-np.cos(bearing), np.sin(bearing)))  # (row, col), north is -row


def _nearest(cells: np.ndarray, point: Tuple[int, int]) -> Tuple[np.ndarray, float]:
    delta = cells - np.asarray(point)
    distance = np.hypot(delta[:, 0], delta[:, 1])
    index = int(np.argmin(distance))
    return cells[index], float(distance[index])


def noop_policy(env: SyntheticSuppressionEnv) -> np.ndarray:
    return np.zeros(MAX_UNITS, dtype=int)


def make_random_policy(seed: int) -> Callable[[SyntheticSuppressionEnv], np.ndarray]:
    rng = np.random.default_rng(seed)

    def policy(env: SyntheticSuppressionEnv) -> np.ndarray:
        mask = env.action_masks().reshape(MAX_UNITS, ACTIONS_PER_UNIT)
        return np.array([rng.choice(np.flatnonzero(row)) for row in mask])

    return policy


def direct_flank_policy(env: SyntheticSuppressionEnv) -> np.ndarray:
    """Approach to a short standoff from the front, then build line around the fire,
    each unit circling towards the downwind side (alternating sense by slot)."""
    mask = env.action_masks().reshape(MAX_UNITS, ACTIONS_PER_UNIT)
    actions = np.zeros(MAX_UNITS, dtype=int)
    burning, _, centre = _fire_geometry(env)
    if not len(burning):
        return actions
    wind = _wind_vector(env)
    for slot, unit in enumerate(env.units):
        if not unit.active:
            continue
        nearest, distance = _nearest(burning, (unit.row, unit.col))
        if distance > STANDOFF_CELLS + 1.5:
            away = np.array((unit.row, unit.col)) - nearest
            away = away / max(np.hypot(*away), 1e-9)
            target = nearest + STANDOFF_CELLS * away
            actions[slot] = _direction_toward(mask[slot], unit, tuple(target), build=False)
            continue
        radial = np.array((unit.row, unit.col)) - centre
        radial = radial / max(np.hypot(*radial), 1e-9)
        tangent = np.array((-radial[1], radial[0]))
        if np.dot(tangent, wind) < 0:
            tangent = -tangent
        if slot % 2:
            tangent = -tangent if np.dot(radial, wind) < -0.3 else tangent
        # Pull slightly outward when too close so the line keeps its standoff.
        if distance < STANDOFF_CELLS:
            tangent = tangent + 0.7 * radial
        actions[slot] = _heading_action(mask[slot], tuple(tangent / np.hypot(*tangent)), build=True)
    return actions


def downwind_indirect_policy(env: SyntheticSuppressionEnv) -> np.ndarray:
    """Build an indirect line across the wind, well ahead of the head."""
    mask = env.action_masks().reshape(MAX_UNITS, ACTIONS_PER_UNIT)
    actions = np.zeros(MAX_UNITS, dtype=int)
    burning, burned, centre = _fire_geometry(env)
    if not len(burning):
        return actions
    wind = _wind_vector(env)
    lateral = np.array((-wind[1], wind[0]))
    extent = float(np.max((burned - centre) @ wind)) if len(burned) else 0.0
    anchor = centre + (extent + INDIRECT_STANDOFF_CELLS) * wind
    for slot, unit in enumerate(env.units):
        if not unit.active:
            continue
        side = (-1) ** slot
        start = anchor + side * (1 + slot // 2) * 2.0 * lateral
        position = np.array((unit.row, unit.col))
        along = float((position - anchor) @ wind)
        if abs(along) > 1.5 or np.hypot(*(position - start)) > 25:
            actions[slot] = _direction_toward(mask[slot], unit, tuple(start), build=False)
        else:
            actions[slot] = _heading_action(mask[slot], tuple(side * lateral), build=True)
    return actions


def protect_urban_policy(env: SyntheticSuppressionEnv) -> np.ndarray:
    """Ring threatened settlements with line; otherwise fall back to direct flanking."""
    land, fire = env.land, env.fire
    urban = np.argwhere(land.urban & ~fire.ever_burned)
    burning, _, _ = _fire_geometry(env)
    if not len(urban) or not len(burning):
        return direct_flank_policy(env)
    mask = env.action_masks().reshape(MAX_UNITS, ACTIONS_PER_UNIT)
    actions = direct_flank_policy(env)
    target_urban, distance = _nearest(urban, tuple(_nearest(burning, tuple(urban.mean(0)))[0]))
    if distance > 30:
        return actions
    near = urban[np.hypot(*(urban - target_urban).T) < 8]
    centre = near.mean(axis=0)
    radius = float(np.max(np.hypot(*(near - centre).T))) + 2.0
    for slot, unit in enumerate(env.units):
        if not unit.active:
            continue
        radial = np.array((unit.row, unit.col)) - centre
        r = np.hypot(*radial)
        if abs(r - radius) > 1.5:
            target = centre + radius * radial / max(r, 1e-9)
            actions[slot] = _direction_toward(mask[slot], unit, tuple(target), build=False)
        else:
            tangent = np.array((-radial[1], radial[0])) / max(r, 1e-9)
            if slot % 2:
                tangent = -tangent
            actions[slot] = _heading_action(mask[slot], tuple(tangent), build=True)
    return actions


HEURISTICS: Dict[str, Callable] = {
    "noop": noop_policy,
    "direct_flank": direct_flank_policy,
    "downwind_indirect": downwind_indirect_policy,
    "protect_urban": protect_urban_policy,
}


def run_episode(env: SyntheticSuppressionEnv, policy: Callable, options: dict,
                predictor: Optional[Callable] = None) -> dict:
    """Run one episode; ``predictor(obs, mask)`` overrides ``policy`` when given."""
    obs, _ = env.reset(options=options)
    done, total = False, 0.0
    while not done:
        if predictor is not None:
            action = predictor(obs, env.action_masks())
        else:
            action = policy(env)
        obs, reward, done, _, info = env.step(action)
        total += reward
    summary = dict(info["episode_summary"])
    summary["return"] = total
    return summary
