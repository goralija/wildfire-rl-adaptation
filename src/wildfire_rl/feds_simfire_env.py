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
    CELL_SIZE_M,
    FREEZE_ALLOWLIST,
    INPUT_ROOT,
    MANIFEST,
    WEATHER,
    WEATHER_OBSERVATIONS,
    SimFireParams,
    apply_forcing,
    build_simulation,
    check_split_access,
    load_case_inputs,
    load_split_cases,
    load_weather_records,
    observed_weather_records,
    record_forcing,
    require_pre_start_weather,
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


# One budget unit is one 20-person crew shift building about 1.26 km of line (ADR-025).
LINE_LENGTH_M = 1260.0


def _sector_vectors(sector: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    if type(sector) is not int or not 0 <= sector < len(SECTOR_DIRECTIONS):
        raise ValueError("sector must be an integer in [0, 7]")
    dx, dy = (int(value) for value in SECTOR_DIRECTIONS[sector])
    return (dx, dy), (-dy, dx)


def line_half_steps(sector: int) -> int:
    """Steps either side of the centre so every sector's line is about 1.26 km long."""
    _direction, tangent = _sector_vectors(sector)
    step_m = CELL_SIZE_M * float(np.hypot(*tangent))
    return int(round((LINE_LENGTH_M / step_m - 1.0) / 2.0))


def line_length_m(sector: int, half_steps: Optional[int] = None) -> float:
    """Extent of a sector line along its own direction, end cells included.

    A straight line of 7 cells spans 7 x 180 m = 1,260 m. A diagonal line of 5
    diagonal cells spans 5 x 254.6 m = 1,273 m; its 4 corner cells lie inside that
    extent. This is the front width the line blocks, which is what a crew-shift buys.
    """
    _direction, tangent = _sector_vectors(sector)
    steps = line_half_steps(sector) if half_steps is None else half_steps
    return (2 * steps + 1) * CELL_SIZE_M * float(np.hypot(*tangent))


def sector_line_cells(center_x: int, center_y: int, sector: int,
                      half_steps: Optional[int] = None) -> Tuple[Tuple[int, int], ...]:
    """Ordered (x, y) cells of a 4-connected line through an integer centre cell.

    The line runs perpendicular to the sector direction. On diagonal sectors each
    corner-only link gets one extra cell on the side away from the fire (positive
    projection on the sector direction), so SimFire's 8-connected spread cannot pass
    between consecutive cells and the standoff never shrinks.
    """
    (dx, dy), (tx, ty) = _sector_vectors(sector)
    steps = line_half_steps(sector) if half_steps is None else half_steps
    if type(steps) is not int or steps < 0:
        raise ValueError("line half-steps must be a nonnegative integer")
    fill = (tx, 0) if tx * dx > 0 else (0, ty)
    cells = []
    for offset in range(-steps, steps + 1):
        x, y = center_x + offset * tx, center_y + offset * ty
        cells.append((x, y))
        if tx and ty and offset < steps:
            cells.append((x + fill[0], y + fill[1]))
    return tuple(cells)


def _placeable(state: np.ndarray, cells: Sequence[Tuple[int, int]]) -> Tuple[Tuple[int, int], ...]:
    rows, columns = state.shape
    return tuple((x, y) for x, y in cells
                 if 0 <= y < rows and 0 <= x < columns and int(state[y, x]) == SIMFIRE_UNBURNED)


def _validated(fire_map: Any, active_front: Any) -> Tuple[np.ndarray, np.ndarray]:
    state = np.asarray(fire_map)
    front = np.asarray(active_front, dtype=bool)
    if state.ndim != 2 or front.shape != state.shape:
        raise ValueError("fire map and active front must have the same 2-D shape")
    return state, front


def fireline_points(
    fire_map: Any,
    active_front: Any,
    sector: int,
    *,
    radius: float = 6.0,
    half_length: Optional[int] = None,
) -> Tuple[Tuple[int, int], ...]:
    """Place one unit of line ahead of the current front centroid."""
    state, front = _validated(fire_map, active_front)
    _sector_vectors(sector)
    if not np.isfinite(radius) or radius < 0:
        raise ValueError("line radius must be nonnegative")
    rows, columns = np.nonzero(front)
    if rows.size == 0:
        return ()
    dx, dy = SECTOR_DIRECTIONS[sector]
    norm = float(np.hypot(dx, dy))
    center_x = int(np.floor(columns.mean() + radius * dx / norm + 0.5))
    center_y = int(np.floor(rows.mean() + radius * dy / norm + 0.5))
    return _placeable(state, sector_line_cells(center_x, center_y, sector, half_length))


def front_edge_line_points(
    fire_map: Any,
    active_front: Any,
    sector: int,
    *,
    standoff: int = 2,
    half_length: Optional[int] = None,
) -> Tuple[Tuple[int, int], ...]:
    """Place one unit of line just beyond the front's leading edge in one sector.

    The anchor is the active-front cell that lies furthest along the sector
    direction; the line centre sits ``standoff`` cell steps beyond it (diagonal steps
    on diagonal sectors, so fire needs the same number of 8-connected hops) and runs
    perpendicular to the sector. Only unburned cells receive line.
    """
    state, front = _validated(fire_map, active_front)
    (dx, dy), _tangent = _sector_vectors(sector)
    if type(standoff) is not int or standoff < 0:
        raise ValueError("line standoff must be a nonnegative integer")
    rows, columns = np.nonzero(front)
    if rows.size == 0:
        return ()
    lead = int(np.argmax(columns * dx + rows * dy))
    center_x = int(columns[lead]) + standoff * dx
    center_y = int(rows[lead]) + standoff * dy
    return _placeable(state, sector_line_cells(center_x, center_y, sector, half_length))


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

    Actions are no-op plus eight sector directions. Each non-no-op action spends one
    budget unit on one ~1.26 km line: 7 cells on an axis, or 5 diagonal cells plus 4
    corner cells on a diagonal, so every line is 4-connected. This deliberately simple
    action mapping is not a field-validated line-construction model. TRAIN is the
    default split; VALIDATION requires ``split="validation"`` and an allowlisted TRAIN
    freeze record matching ``sim_params``; TEST is refused.
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
        weather_observation: str = "previous",
        freeze_record: Optional[Path] = None,
        freeze_allowlist: Path = FREEZE_ALLOWLIST,
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
        self.freeze_record_sha256 = check_split_access(
            split, sim_params, freeze_record, weather_path=weather_path, allowlist_path=freeze_allowlist
        )
        if not budgets or any(type(value) is not int or value < 0 for value in budgets):
            raise ValueError("budgets must be nonempty nonnegative integers")
        if line_placement not in LINE_PLACEMENTS:
            raise ValueError("unknown line placement %r" % line_placement)
        if weather_observation not in WEATHER_OBSERVATIONS:
            raise ValueError("weather observation must be one of %s" % (WEATHER_OBSERVATIONS,))
        self.weather_observation = weather_observation

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
        # ADR-030: the observation rule needs the pre-start day, in either mode, so a
        # pre-ADR-030 file cannot silently fall back to showing a forcing day.
        require_pre_start_weather(self.weather_by_id, weather_path)
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
        self._set_observed_weather(inputs["weather"])

    def _set_observed_weather(self, weather: dict) -> None:
        """Fix, per decision, the daily record the policy observes (ADR-030)."""
        records = observed_weather_records(weather, self.weather_observation)
        self.observed_weather_labels = tuple(r["gridmet_daily_label_mst"] for r in records)
        self.observed_forcing = [record_forcing(r, self.sim_params) for r in records]

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
        # The terminal observation (after the last decision) repeats the last decision's.
        current = self.observed_forcing[min(self.decision_index, self.horizon_steps - 1)]
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
        applied_length_m = 0.0
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
                applied_length_m = line_length_m(action - 1)

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
            "line_length_m": applied_length_m,
            "invalid_action": invalid,
            "feds_future_perimeters_used": False,
        }
        return self._observation(), float(reward), terminated, truncated, info
