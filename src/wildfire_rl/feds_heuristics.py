"""Matched heuristic policies for the budgeted FEDS/SimFire environment.

Every heuristic decides from the same observation dictionary and action mask that a
PPO policy receives, so no baseline sees the full-resolution map or FEDS outlines,
and every baseline sees exactly the weather the policy sees. With the environment's
default ``weather_observation="upcoming"`` that is the ex-post forcing of the next
12h; with ``"previous"`` it is the segment that just ran. Each heuristic spends a
budget unit at the first legal opportunity.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional

import numpy as np

from .feds_simfire_env import SECTOR_DIRECTIONS


Policy = Callable[[Dict[str, np.ndarray], np.ndarray], int]


def sector_for_vector(dx: float, dy: float) -> int:
    """Return the sector index (0..7) closest to a column/row direction vector."""
    if not np.isfinite(dx) or not np.isfinite(dy) or (dx == 0 and dy == 0):
        raise ValueError("direction vector must be finite and nonzero")
    best, best_score = 0, -np.inf
    for index, (sx, sy) in enumerate(SECTOR_DIRECTIONS):
        score = (sx * dx + sy * dy) / float(np.hypot(sx, sy))
        if score > best_score:
            best, best_score = index, score
    return best


def heading_vector(sin_heading: float, cos_heading: float) -> tuple:
    """Map a clockwise-from-north downwind heading to (column, row) components."""
    return float(sin_heading), float(-cos_heading)


def _first_legal(preferred: int, mask: np.ndarray) -> int:
    action = preferred + 1
    return action if bool(mask[action]) else 0


def noop_policy(_observation: Dict[str, np.ndarray], _mask: np.ndarray) -> int:
    return 0


def downwind_policy(observation: Dict[str, np.ndarray], mask: np.ndarray) -> int:
    """Build line ahead of the front in the current 12h downwind direction."""
    weather = np.asarray(observation["weather"], dtype=float)
    dx, dy = heading_vector(weather[1], weather[2])
    if dx == 0 and dy == 0:
        return 0
    return _first_legal(sector_for_vector(dx, dy), mask)


def advancing_front_policy(observation: Dict[str, np.ndarray], mask: np.ndarray) -> int:
    """Build line where the active front sits relative to the burned area.

    Uses the pooled burned and active-front channels only: the direction from the
    burned-area centroid to the active-front centroid. Falls back to downwind when
    the two centroids coincide.
    """
    grid = np.asarray(observation["grid"], dtype=float)
    burned, front = grid[0], grid[1]
    if front.sum() <= 0 or burned.sum() <= 0:
        return downwind_policy(observation, mask)
    rows, columns = np.indices(burned.shape, dtype=float)
    dx = float((front * columns).sum() / front.sum() - (burned * columns).sum() / burned.sum())
    dy = float((front * rows).sum() / front.sum() - (burned * rows).sum() / burned.sum())
    if np.hypot(dx, dy) < 1e-6:
        return downwind_policy(observation, mask)
    return _first_legal(sector_for_vector(dx, dy), mask)


def make_random_policy(seed: int) -> Policy:
    """Uniform choice among legal line actions; no-op only when nothing else is legal."""
    generator = np.random.default_rng(seed)

    def policy(_observation: Dict[str, np.ndarray], mask: np.ndarray) -> int:
        legal = np.flatnonzero(np.asarray(mask, dtype=bool)[1:]) + 1
        return int(generator.choice(legal)) if legal.size else 0

    return policy


HEURISTICS = {
    "noop": lambda seed: noop_policy,
    "random_legal": make_random_policy,
    "downwind": lambda seed: downwind_policy,
    "advancing_front": lambda seed: advancing_front_policy,
}


def make_heuristic(name: str, seed: Optional[int] = 0) -> Policy:
    if name not in HEURISTICS:
        raise ValueError("unknown heuristic %r" % name)
    return HEURISTICS[name](0 if seed is None else seed)
