"""TRAIN-only, budgeted Gymnasium wrapper for the pinned SimFire/FEDS setup.

This is a technical training environment. Its reward is simulated area burned, not
the post-hoc FEDS perimeter, and the provisional wind factor is not calibrated.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple

import gymnasium as gym
import numpy as np

from .feds_simfire_setup import (
    INPUT_ROOT,
    MANIFEST,
    WEATHER,
    SimFireParams,
    apply_forcing,
    build_simulation,
    load_case_inputs,
    load_split_cases,
    load_weather_records,
    sha256_file,
)


SIMFIRE_UNBURNED = 0
SIMFIRE_BURNING = 1
SIMFIRE_BURNED = 2
SIMFIRE_FIRELINE = 3
SECTOR_DIRECTIONS = (
    (1.0, 0.0),
    (1.0, 1.0),
    (0.0, 1.0),
    (-1.0, 1.0),
    (-1.0, 0.0),
    (-1.0, -1.0),
    (0.0, -1.0),
    (1.0, -1.0),
)


def fireline_points(
    fire_map: Any,
    active_front: Any,
    sector: int,
    *,
    radius: float = 6.0,
    half_length: int = 3,
) -> Tuple[Tuple[int, int], ...]:
    """Place a short, fixed-length line ahead of the current front centroid."""
    state = np.asarray(fire_map)
    front = np.asarray(active_front, dtype=bool)
    if state.ndim != 2 or front.shape != state.shape:
        raise ValueError("fire map and active front must have the same 2-D shape")
    if type(sector) is not int or not 0 <= sector < len(SECTOR_DIRECTIONS):
        raise ValueError("sector must be an integer in [0, 7]")
    if not np.isfinite(radius) or radius < 0 or type(half_length) is not int or half_length < 0:
        raise ValueError("line radius and half-length must be nonnegative")
    rows, columns = np.nonzero(front)
    if rows.size == 0:
        return ()

    dx, dy = SECTOR_DIRECTIONS[sector]
    norm = float(np.hypot(dx, dy))
    dx, dy = dx / norm, dy / norm
    center_x = float(columns.mean()) + radius * dx
    center_y = float(rows.mean()) + radius * dy
    tangent_x, tangent_y = -dy, dx
    points = []
    seen = set()
    for offset in range(-half_length, half_length + 1):
        x = int(round(center_x + offset * tangent_x))
        y = int(round(center_y + offset * tangent_y))
        point = (x, y)
        if point in seen:
            continue
        seen.add(point)
        if 0 <= y < state.shape[0] and 0 <= x < state.shape[1]:
            if int(state[y, x]) == SIMFIRE_UNBURNED:
                points.append(point)
    return tuple(points)


def front_edge_line_points(
    fire_map: Any,
    active_front: Any,
    sector: int,
    *,
    standoff: int = 2,
    half_length: int = 3,
) -> Tuple[Tuple[int, int], ...]:
    """Place a short line just beyond the front's leading edge in one sector.

    The anchor is the active-front cell that lies furthest along the sector
    direction; the line centre sits ``standoff`` cells beyond it and runs
    perpendicular to the sector. Only unburned cells receive line.
    """
    state = np.asarray(fire_map)
    front = np.asarray(active_front, dtype=bool)
    if state.ndim != 2 or front.shape != state.shape:
        raise ValueError("fire map and active front must have the same 2-D shape")
    if type(sector) is not int or not 0 <= sector < len(SECTOR_DIRECTIONS):
        raise ValueError("sector must be an integer in [0, 7]")
    if type(standoff) is not int or standoff < 0 or type(half_length) is not int or half_length < 0:
        raise ValueError("line standoff and half-length must be nonnegative integers")
    rows, columns = np.nonzero(front)
    if rows.size == 0:
        return ()
    dx, dy = SECTOR_DIRECTIONS[sector]
    norm = float(np.hypot(dx, dy))
    dx, dy = dx / norm, dy / norm
    projection = columns * dx + rows * dy
    lead = int(np.argmax(projection))
    center_x = float(columns[lead]) + standoff * dx
    center_y = float(rows[lead]) + standoff * dy
    tangent_x, tangent_y = -dy, dx
    points = []
    seen = set()
    for offset in range(-half_length, half_length + 1):
        x = int(round(center_x + offset * tangent_x))
        y = int(round(center_y + offset * tangent_y))
        if (x, y) in seen:
            continue
        seen.add((x, y))
        if 0 <= y < state.shape[0] and 0 <= x < state.shape[1]:
            if int(state[y, x]) == SIMFIRE_UNBURNED:
                points.append((x, y))
    return tuple(points)


LINE_PLACEMENTS = {
    "centroid": fireline_points,
    "front_edge": front_edge_line_points,
}


def line_points_for(placement: str, fire_map: Any, active_front: Any, sector: int):
    if placement not in LINE_PLACEMENTS:
        raise ValueError("unknown line placement %r" % placement)
    return LINE_PLACEMENTS[placement](fire_map, active_front, sector)


def build_action_mask(
    fire_map: Any,
    active_front: Any,
    remaining_budget: int,
    *,
    placement: str = "centroid",
) -> np.ndarray:
    """Keep no-op legal in every state; mask lines without budget or placement cells."""
    if type(remaining_budget) is not int or remaining_budget < 0:
        raise ValueError("remaining budget must be a nonnegative integer")
    mask = np.zeros(len(SECTOR_DIRECTIONS) + 1, dtype=bool)
    mask[0] = True
    if remaining_budget:
        for sector in range(len(SECTOR_DIRECTIONS)):
            mask[sector + 1] = bool(line_points_for(placement, fire_map, active_front, sector))
    return mask


def cumulative_burn_mask(previous: Any, fire_map: Any) -> np.ndarray:
    """Preserve all prior damage even if SimFire later overwrites a cell with a line."""
    prior = np.asarray(previous, dtype=bool)
    state = np.asarray(fire_map)
    if prior.ndim != 2 or state.shape != prior.shape:
        raise ValueError("cumulative burn and fire map must be equally shaped 2-D arrays")
    return prior | np.isin(state, (SIMFIRE_BURNING, SIMFIRE_BURNED))


class FedsSimFireEnv(gym.Env):
    """A 48h episode with four shared 12h decisions and a discrete crew budget.

    Actions are no-op plus eight sector directions. Each non-no-op action places at
    most seven SimFire fireline cells (one budget unit). This deliberately simple
    action mapping is not a field-validated line-construction model. TRAIN is the
    default split; VALIDATION requires ``split="validation"``; TEST is refused.
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        *,
        wind_adjustment_factor: Optional[float] = None,
        budgets: Sequence[int] = (0, 2, 4),
        scenario_ids: Optional[Sequence[str]] = None,
        internal_update_minutes: int = 5,
        sim_params: Optional[SimFireParams] = None,
        split: str = "train",
        line_placement: str = "centroid",
        max_budget: Optional[int] = None,
        manifest_path: Path = MANIFEST,
        weather_path: Path = WEATHER,
        input_root: Path = INPUT_ROOT,
    ) -> None:
        if sim_params is None:
            if wind_adjustment_factor is None:
                raise ValueError("either sim_params or wind_adjustment_factor is required")
            sim_params = SimFireParams(
                wind_adjustment_factor=float(wind_adjustment_factor),
                internal_update_minutes=internal_update_minutes,
            )
        if not budgets or any(type(value) is not int or value < 0 for value in budgets):
            raise ValueError("budgets must be nonempty nonnegative integers")
        if line_placement not in LINE_PLACEMENTS:
            raise ValueError("unknown line placement %r" % line_placement)

        self.sim_params = sim_params
        self.wind_adjustment_factor = sim_params.wind_adjustment_factor
        self.internal_update_minutes = sim_params.internal_update_minutes
        self.split = split
        self.line_placement = line_placement
        self.budgets = tuple(budgets)
        # Observation scaling must match across training and evaluation runs.
        self.max_budget = max(1, max(self.budgets)) if max_budget is None else int(max_budget)
        if self.max_budget < max(self.budgets):
            raise ValueError("max_budget must cover every sampled budget")
        self.horizon_steps = 4
        self.block_count = 16

        manifest_path = Path(manifest_path)
        weather_path = Path(weather_path)
        self.manifest_path = manifest_path
        self.weather_path = weather_path
        self.manifest_sha256 = sha256_file(manifest_path)
        all_cases = load_split_cases(split, manifest_path)
        if scenario_ids is not None:
            requested = tuple(scenario_ids)
            unknown = set(requested) - set(all_cases)
            if unknown:
                raise ValueError("Only manifest %s scenario IDs are accepted: %s"
                                 % (split.upper(), sorted(unknown)))
            all_cases = {key: all_cases[key] for key in requested}
        self.cases = all_cases
        self.scenario_ids = tuple(all_cases)
        weather = load_weather_records(split, manifest_path=manifest_path, weather_path=weather_path)
        if set(self.scenario_ids) - set(weather):
            raise ValueError("At least one selected case is missing gridMET forcing")
        self.weather_by_id = {key: weather[key] for key in self.scenario_ids}
        self.weather_sha256 = sha256_file(weather_path)
        self.input_root = Path(input_root)
        self._input_cache: Dict[str, Dict[str, Any]] = {}

        self.action_space = gym.spaces.Discrete(9)
        self.observation_space = gym.spaces.Dict({
            "grid": gym.spaces.Box(0.0, 1.0, shape=(4, 16, 16), dtype=np.float32),
            "budget": gym.spaces.Box(0.0, 1.0, shape=(2,), dtype=np.float32),
            "weather": gym.spaces.Box(-1.0, 1.0, shape=(4,), dtype=np.float32),
            "time": gym.spaces.Box(0.0, 1.0, shape=(1,), dtype=np.float32),
        })
        self._done = True

    def _placement(self) -> str:
        return getattr(self, "line_placement", "centroid")

    def action_masks(self) -> np.ndarray:
        fire_map = self.simulation.fire_map
        front = fire_map == SIMFIRE_BURNING
        return build_action_mask(fire_map, front, self.remaining_budget, placement=self._placement())

    def _load_episode(self, scenario_id: str) -> None:
        inputs = self._input_cache.get(scenario_id)
        if inputs is None:
            inputs = load_case_inputs(
                scenario_id,
                split=self.split,
                manifest_path=self.manifest_path,
                weather_path=self.weather_path,
                input_root=self.input_root,
                cases=self.cases,
                weather_records=self.weather_by_id,
            )
            self._input_cache[scenario_id] = inputs
        self.simulation, self.forcing, self.cumulative_burned = build_simulation(
            inputs, self.sim_params, seed=0
        )
        self.fuel = inputs["fuel"]
        self.simulation_active = True

    def _pool(self, values: np.ndarray) -> np.ndarray:
        rows, columns = values.shape
        if rows % self.block_count or columns % self.block_count:
            raise ValueError("Observation grid dimensions must be divisible by the pooling grid")
        row_size = rows // self.block_count
        column_size = columns // self.block_count
        return values.reshape(
            self.block_count, row_size, self.block_count, column_size
        ).mean(axis=(1, 3))

    def _observation(self) -> Dict[str, np.ndarray]:
        fire_map = self.simulation.fire_map
        grid = np.stack((
            self._pool(self.cumulative_burned.astype(np.float32)),
            self._pool((fire_map == SIMFIRE_BURNING).astype(np.float32)),
            self._pool(np.isin(fire_map, (3, 4, 5)).astype(np.float32)),
            self._pool(np.clip(self.fuel.astype(np.float32) / 13.0, 0.0, 1.0)),
        )).astype(np.float32)
        current = self.forcing[min(self.decision_index, self.horizon_steps - 1)]
        direction = np.deg2rad(current["wind_direction_degrees_clockwise_north_to"])
        weather = np.asarray((
            np.clip(current["wind_speed_midflame_ft_per_min_proxy"] / 3000.0, 0.0, 1.0),
            np.sin(direction),
            np.cos(direction),
            np.clip(current["fuel_moisture_fraction_proxy"] / 0.3, 0.0, 1.0),
        ), dtype=np.float32)
        budget = np.asarray((
            self.initial_budget / float(self.max_budget),
            self.remaining_budget / float(self.max_budget),
        ), dtype=np.float32)
        time = np.asarray((self.decision_index / float(self.horizon_steps),), dtype=np.float32)
        return {"grid": grid, "budget": budget, "weather": weather, "time": time}

    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None):
        """Sample a case and budget, or pin them with ``options`` for paired evaluation."""
        super().reset(seed=seed)
        options = dict(options or {})
        unknown = set(options) - {"scenario_id", "budget"}
        if unknown:
            raise ValueError("unsupported reset options: %s" % sorted(unknown))
        if "scenario_id" in options:
            if options["scenario_id"] not in self.cases:
                raise ValueError("scenario is not in this environment's %s set" % self.split.upper())
            self.scenario_id = options["scenario_id"]
        else:
            index = int(self.np_random.integers(len(self.scenario_ids)))
            self.scenario_id = self.scenario_ids[index]
        if "budget" in options:
            budget = options["budget"]
            if type(budget) is not int or budget < 0 or budget > self.max_budget:
                raise ValueError("budget must be an integer in [0, max_budget]")
            self.initial_budget = budget
        else:
            self.initial_budget = int(self.np_random.choice(self.budgets))
        self.remaining_budget = self.initial_budget
        self.decision_index = 0
        self._load_episode(self.scenario_id)
        self._done = False
        return self._observation(), {
            "scenario_id": self.scenario_id,
            "split": self.split,
            "budget": self.initial_budget,
            "test_cases_loaded": False,
        }

    def step(self, action: int):
        if self._done:
            raise RuntimeError("episode is done; call reset")
        if not self.action_space.contains(action):
            raise ValueError("action is outside the 9-action space")
        action = int(action)
        mask = self.action_masks()
        invalid = not bool(mask[action])
        action = 0 if invalid else action
        applied_points = ()
        if action and self.remaining_budget > 0:
            front = self.simulation.fire_map == SIMFIRE_BURNING
            applied_points = line_points_for(
                self._placement(), self.simulation.fire_map, front, action - 1
            )
            if applied_points:
                self.simulation.update_mitigation([
                    (x, y, SIMFIRE_FIRELINE) for x, y in applied_points
                ])
                self.remaining_budget -= 1

        previous = self.cumulative_burned.copy()
        if self.simulation_active:
            apply_forcing(self.simulation, self.forcing[self.decision_index])
            _fire_map, self.simulation_active = self.simulation.run("12h")
            self.cumulative_burned = cumulative_burn_mask(
                self.cumulative_burned, self.simulation.fire_map
            )
        new_burned_cells = int(np.count_nonzero(self.cumulative_burned & ~previous))
        reward = -new_burned_cells / 100.0
        if invalid:
            reward -= 0.01
        self.decision_index += 1
        terminated = self.decision_index >= self.horizon_steps
        truncated = False
        self._done = terminated
        info = {
            "scenario_id": self.scenario_id,
            "split": getattr(self, "split", "train"),
            "decision_step": self.decision_index,
            "remaining_budget": self.remaining_budget,
            "new_burned_cells": new_burned_cells,
            "cumulative_burned_cells": int(self.cumulative_burned.sum()),
            "fire_active": bool(self.simulation_active),
            "action_applied": bool(applied_points),
            "line_cells_applied": len(applied_points),
            "invalid_action": invalid,
            "feds_future_perimeters_used": False,
        }
        return self._observation(), float(reward), terminated, truncated, info
