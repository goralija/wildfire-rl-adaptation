"""Budgeted wildfire-suppression environment on the synthetic CA (ADR-028).

Units are finite, arrive over time from a staging distance, move and build line at
bounded rates and can be lost. The reward is the weighted damage the agent prevents
relative to a no-op rollout of the same episode on the same random numbers,
normalised so that an episode's return is the fraction of no-op damage saved.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import gymnasium as gym
import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_cdt

from .synthetic_ca import (
    BURNED,
    BURNING,
    CELL_SIZE_M,
    OFFSET_DISTANCE,
    OFFSETS,
    SUBSTEP_MINUTES,
    UNBURNED,
    FireState,
    Landscape,
    SpreadParams,
    WeatherSeries,
    damage_weights,
    generate_landscape,
    generate_weather,
    initial_state_from_masks,
)


DECISION_MINUTES = 60.0
SUBSTEPS_PER_DECISION = int(DECISION_MINUTES / SUBSTEP_MINUTES)
TAIL_DECISIONS = 12
MAX_UNITS = 4
ACTIONS_PER_UNIT = 17  # 0 stay, 1-8 move in OFFSETS direction, 9-16 build line and advance
URBAN_WEIGHT = 50.0
UNIT_LOSS_PENALTY = 1.0
CLOSE_CALL_PENALTY = 0.1
RETREAT_RADIUS = 2
SAFE_DISTANCE = 5
PATCH = 7  # half-width of the full-resolution crop around each unit (15x15)
MAP_POOL = 2

HAND_CREW, DOZER = 0, 1


CHAINS_PER_HOUR_TO_M_PER_MIN = 20.1168 / 60.0


@dataclass(frozen=True)
class UnitType:
    name: str
    travel_m_per_min: float
    # Sustained line production in chains/hour on gentle slope, by FBFM13 code.
    line_ch_per_h: Dict[int, float]
    max_slope_percent: float

    def line_m_per_min(self, fuel_code: int, slope_percent: float) -> float:
        rate = self.line_ch_per_h.get(int(fuel_code), 0.0) * CHAINS_PER_HOUR_TO_M_PER_MIN
        if self.name == "dozer":
            # PMS 410-1 p. A-34 uphill slope classes, relative to the 0-25% class.
            if slope_percent > self.max_slope_percent:
                return 0.0
            rate *= 1.0 if slope_percent <= 25 else 0.6 if slope_percent <= 40 else 0.3
        return rate


# Sources (checked 2026-11-04; details in docs/research/SYNTHETIC_CA_ENV.md):
# - hand crew: NWCG Fireline Handbook PMS 410-1 (2004) App. A p. A-30, sustained line for a
#   20-person Type II crew (FM8/FM9 use the conifer rows); urban (91) is an assumption.
# - dozer: same, p. A-34, Type II single pass, uphill, 0-25% slope class midpoint; working
#   limit 45% (across-slope limit quoted in the Baboon Fire 2020 dozer report).
# - travel: Sullivan et al. 2020 (Fire 3:52) measured ~5 km/h for loaded hotshots on trail;
#   3 km/h off-trail is an assumption. Dozer 2.5 km/h is an assumption below the D6R's
#   3.8 km/h first gear.
UNIT_TYPES = {
    HAND_CREW: UnitType(
        name="hand_crew_20",
        travel_m_per_min=50.0,
        line_ch_per_h={1: 18, 2: 16, 3: 3, 4: 3, 5: 4, 6: 4, 7: 2, 8: 5, 9: 16, 10: 4,
                       11: 9, 12: 4, 13: 3, 91: 6},
        max_slope_percent=1000.0,
    ),
    DOZER: UnitType(
        name="dozer",
        travel_m_per_min=42.0,
        line_ch_per_h={1: 105, 2: 105, 3: 87.5, 4: 47.5, 5: 87.5, 6: 67.5, 7: 67.5,
                       8: 87.5, 9: 67.5, 10: 15, 11: 32.5, 12: 32.5, 13: 15, 91: 30},
        max_slope_percent=45.0,
    ),
}


@dataclass
class Unit:
    kind: int
    arrival_minute: float
    row: int = -1
    col: int = -1
    active: bool = False
    lost: bool = False
    progress_m: float = 0.0
    # What ``progress_m`` accumulates for: ("build", row, col) or ("move", row, col). It is
    # keyed to the cell, so changing heading while building the same cell keeps progress.
    progress_key: Optional[Tuple[str, int, int]] = None
    action: int = 0
    line_cells: int = 0
    retreats: int = 0
    close_calls: int = 0

    @property
    def spec(self) -> UnitType:
        return UNIT_TYPES[self.kind]


@dataclass
class EpisodeSpec:
    """Everything that defines one episode before any action."""

    landscape: Landscape
    weather: WeatherSeries
    scar: np.ndarray
    front: np.ndarray
    units: List[Tuple[int, float]]
    horizon: int
    seed: int
    params: SpreadParams = field(default_factory=SpreadParams)
    start_minute: float = 0.0
    name: str = "synthetic"
    variant: int = 0


@dataclass
class Curriculum:
    horizons: Sequence[int] = (12, 24, 48)
    unit_counts: Sequence[int] = (2, 3, 4)
    dozer_share: float = 0.4
    pregrow_hours: Tuple[float, float] = (2.0, 12.0)
    spread_scale: Tuple[float, float] = (0.3, 1.2)
    spot_rate: Tuple[float, float] = (0.0, 4e-4)
    wind_adjustment: Tuple[float, float] = (0.1, 0.5)
    blocky_weather_share: float = 0.5
    shape: Tuple[int, int] = (128, 128)
    # Fires whose no-op rollout adds fewer cells carry no learning signal; resample them.
    min_noop_growth_cells: int = 30
    max_attempts: int = 16


def _blocky(series: WeatherSeries, block: int) -> WeatherSeries:
    """gridMET-like forcing: hold each 12h block's first values, keep local hour."""
    steps = []
    for index, weather in enumerate(series.steps):
        anchor = series.steps[(index // block) * block]
        steps.append(type(weather)(anchor.wind_midflame_m_s, anchor.wind_to_deg,
                                   anchor.moisture, weather.local_hour))
    return WeatherSeries(steps)


def sample_synthetic_episode(seed: int, curriculum: Curriculum, attempt: int = 0) -> EpisodeSpec:
    rng = np.random.default_rng([7, int(seed), int(attempt)])
    episode_seed = int(seed) * 64 + int(attempt)
    landscape = generate_landscape(rng, curriculum.shape)
    horizon = int(rng.choice(curriculum.horizons))
    start_hour = float(rng.uniform(0.0, 24.0))
    pregrow = float(rng.uniform(*curriculum.pregrow_hours))
    total = int(np.ceil(pregrow)) + horizon + TAIL_DECISIONS
    weather = generate_weather(rng, total, DECISION_MINUTES, start_hour,
                               wind_adjustment=float(rng.uniform(*curriculum.wind_adjustment)))
    if rng.random() < curriculum.blocky_weather_share:
        weather = _blocky(weather, 12)
    lo, hi = np.log(curriculum.spread_scale)
    params = SpreadParams(spread_scale=float(np.exp(rng.uniform(lo, hi))),
                          spot_rate=float(rng.uniform(*curriculum.spot_rate)))

    rows, cols = landscape.shape
    centre = landscape.burnable.copy()
    centre[: rows // 3] = False
    centre[2 * rows // 3:] = False
    centre[:, : cols // 3] = False
    centre[:, 2 * cols // 3:] = False
    candidates = np.argwhere(centre & ~landscape.urban)
    if not len(candidates):
        candidates = np.argwhere(landscape.burnable)
    r, c = candidates[int(rng.integers(len(candidates)))]
    ignition = np.zeros(landscape.shape, dtype=bool)
    ignition[r, c] = True

    # Pre-grow without suppression, then reduce to (scar, front) exactly like a real start.
    fire = FireState(landscape, episode_seed + 2 ** 40, params)
    fire.ignite(ignition)
    pre_steps = int(np.ceil(pregrow))
    for hour in range(pre_steps):
        fire.set_weather(weather.at(hour))
        for _ in range(SUBSTEPS_PER_DECISION):
            fire.step_substep()
    scar = fire.ever_burned & ~fire.burning
    front = fire.burning
    if not front.any():
        front = ignition
        scar = np.zeros_like(ignition)
    remaining = WeatherSeries(weather.steps[pre_steps:])

    units = sample_units(rng, curriculum)
    return EpisodeSpec(landscape=landscape, weather=remaining, scar=scar, front=front,
                       units=units, horizon=horizon, seed=episode_seed, params=params,
                       name="synthetic-%d-%d" % (int(seed), int(attempt)))


def sample_units(rng: np.random.Generator, curriculum: Curriculum) -> List[Tuple[int, float]]:
    count = int(rng.choice(curriculum.unit_counts))
    kinds = [DOZER if rng.random() < curriculum.dozer_share else HAND_CREW for _ in range(count)]
    arrivals = sorted(float(rng.uniform(0.0, 180.0)) for _ in range(count))
    return list(zip(kinds, arrivals))


def order_units(units: Sequence[Tuple[int, float]]) -> List[Tuple[int, float]]:
    """Stable slot order: dozers first, then hand crews, each by arrival time."""
    return sorted(units, key=lambda item: (item[0] != DOZER, item[1]))[:MAX_UNITS]


class SyntheticSuppressionEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, *, curriculum: Optional[Curriculum] = None,
                 seed_offset: int = 1_000_000, episode_specs: Optional[Sequence] = None,
                 unit_loss_penalty: float = UNIT_LOSS_PENALTY,
                 close_call_penalty: float = CLOSE_CALL_PENALTY,
                 urban_weight: float = URBAN_WEIGHT, auto_retreat: bool = True,
                 map_shape: Tuple[int, int] = (128, 128), reuse_fires: int = 1) -> None:
        self.curriculum = curriculum or Curriculum()
        self.seed_offset = int(seed_offset)
        self.episode_specs = list(episode_specs) if episode_specs is not None else None
        self.unit_loss_penalty = float(unit_loss_penalty)
        self.close_call_penalty = float(close_call_penalty)
        self.urban_weight = float(urban_weight)
        self.auto_retreat = auto_retreat
        self.map_shape = tuple(map_shape)
        rows, cols = self.map_shape
        self.map_channels = 9 + MAX_UNITS
        self.unit_features = 12 + 3 * (2 * PATCH + 1) ** 2
        self.action_space = gym.spaces.MultiDiscrete([ACTIONS_PER_UNIT] * MAX_UNITS)
        self.observation_space = gym.spaces.Dict({
            "map": gym.spaces.Box(-1.0, 1.0, shape=(self.map_channels, rows // MAP_POOL,
                                                     cols // MAP_POOL), dtype=np.float32),
            "units": gym.spaces.Box(-1.0, 1.0, shape=(MAX_UNITS * self.unit_features,),
                                    dtype=np.float32),
            "globals": gym.spaces.Box(-1.0, 1.0, shape=(9,), dtype=np.float32),
        })
        self._episode_counter = 0
        self.reuse_fires = int(reuse_fires)
        self._reusable = None
        self._reuse_left = 0
        self.spec_now: Optional[EpisodeSpec] = None

    def set_curriculum(self, **changes) -> None:
        """Replace curriculum fields (used by the training script between stages)."""
        values = dict(self.curriculum.__dict__)
        values.update(changes)
        self.curriculum = Curriculum(**values)
        self._reusable, self._reuse_left = None, 0

    # ------------------------------------------------------------------ episode set-up
    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None):
        super().reset(seed=seed)
        options = dict(options or {})
        self._episode_counter += 1
        if "episode_spec" in options:
            return self._start(options["episode_spec"])
        if self.episode_specs is not None:
            index = options.get("index", (self._episode_counter - 1) % len(self.episode_specs))
            return self._start(self.episode_specs[index])
        base = options.get("seed")
        if base is None and self._reuse_left > 0 and self._reusable is not None:
            # Same fire and no-op rollout, new unit set and staging: cheap training reset.
            self._reuse_left -= 1
            spec, noop = self._reusable
            variant = spec.variant + 1
            rng = np.random.default_rng([13, spec.seed, variant])
            spec = dataclasses.replace(spec, units=sample_units(rng, self.curriculum),
                                       variant=variant)
            self._reusable = (spec, noop)
            return self._start(spec, noop)
        training = base is None
        if base is None:
            base = self.seed_offset + int(self.np_random.integers(0, 2 ** 31 - 1))
        for attempt in range(self.curriculum.max_attempts):
            result = self._start(sample_synthetic_episode(int(base), self.curriculum, attempt))
            grown = int((self.noop_final.ever_burned & ~self.prior_damage).sum())
            if grown >= self.curriculum.min_noop_growth_cells:
                break
        if training and self.reuse_fires > 1:
            self._reusable = (self.spec_now, (list(self.noop_damage), self.noop_final))
            self._reuse_left = self.reuse_fires - 1
        return result

    def _start(self, spec: EpisodeSpec, noop_cache=None):
        if spec.landscape.shape != self.map_shape:
            raise ValueError("episode landscape must match the environment map shape")
        self.spec_now = spec
        self.land = spec.landscape
        self.weights = damage_weights(self.land, self.urban_weight)
        start = initial_state_from_masks(self.land, spec.seed, spec.params, spec.scar, spec.front)
        self.prior_damage = start.ever_burned.copy()
        self.fire = start
        self.minute = 0.0
        self.decision = 0
        self.units = [Unit(kind=k, arrival_minute=a) for k, a in order_units(spec.units)]

        # No-op rollout on identical random numbers, including the post-horizon tail. It does
        # not depend on units, so a reused fire keeps its rollout.
        if noop_cache is not None:
            self.noop_damage, noop = list(noop_cache[0]), noop_cache[1]
        else:
            noop = start.copy()
            self.noop_damage = []
            for index in range(spec.horizon + TAIL_DECISIONS):
                self.noop_damage.append(self._advance(noop, index, units=None))
        self.noop_total = float(sum(self.noop_damage))
        self.norm = max(self.noop_total, 20.0)
        self.noop_final = noop
        self.stats = {"agent_damage": 0.0, "units_lost": 0, "retreats": 0, "line_cells": 0,
                      "edge_contact": False}
        return self._observation(), self._info()

    def _staging_cell(self, slot: int, unit: Unit) -> Tuple[int, int]:
        """A passable cell 2-4 km beyond the fire at arrival time, keyed per episode and slot."""
        rows, cols = self.land.shape
        rng = np.random.default_rng([11, self.spec_now.seed, self.spec_now.variant, slot])
        burning = np.argwhere(self.fire.ever_burned)
        centre = burning.mean(axis=0) if len(burning) else np.array([rows / 2, cols / 2])
        radius = np.sqrt(len(burning) / np.pi) + rng.uniform(11.0, 22.0)
        for _ in range(200):
            angle = rng.uniform(0, 2 * np.pi)
            r = int(round(centre[0] + radius * np.sin(angle)))
            c = int(round(centre[1] + radius * np.cos(angle)))
            if (0 <= r < rows and 0 <= c < cols and self._passable(unit.kind, r, c, staging=True)
                    and not self._threat(r, c)):
                return r, c
            radius *= 0.97
        r, c = np.clip(np.round(centre).astype(int), 0, [rows - 1, cols - 1])
        return int(r), int(c)

    # ------------------------------------------------------------------ physics helpers
    def _passable(self, kind: int, r: int, c: int, staging: bool = False) -> bool:
        if self.land.water[r, c]:
            return False
        state = self.fire.state[r, c]
        if state == BURNING:
            return False
        if staging and self.fire.ever_burned[r, c]:
            return False
        if kind == DOZER and self.land.slope_percent[r, c] > UNIT_TYPES[DOZER].max_slope_percent:
            return False
        return True

    def _buildable(self, r: int, c: int) -> bool:
        return bool(self.land.burnable[r, c] and self.fire.state[r, c] == UNBURNED
                    and not self.fire.line[r, c])

    def _target(self, unit: Unit, k: int) -> Optional[Tuple[int, int]]:
        dr, dc = OFFSETS[k]
        r, c = unit.row + dr, unit.col + dc
        rows, cols = self.land.shape
        if 0 <= r < rows and 0 <= c < cols and self._passable(unit.kind, r, c):
            return r, c
        return None

    def _unit_mask(self, unit: Unit) -> np.ndarray:
        mask = np.zeros(ACTIONS_PER_UNIT, dtype=bool)
        mask[0] = True
        if not unit.active:
            return mask
        here_buildable = self._buildable(unit.row, unit.col)
        for k in range(8):
            target_ok = self._target(unit, k) is not None
            mask[1 + k] = target_ok
            mask[9 + k] = here_buildable or target_ok
        return mask

    def action_masks(self) -> np.ndarray:
        slots = [self._unit_mask(unit) for unit in self.units]
        while len(slots) < MAX_UNITS:
            slots.append(np.eye(ACTIONS_PER_UNIT, dtype=bool)[0])
        return np.concatenate(slots)

    def _threat(self, r: int, c: int, radius: int = 2) -> int:
        """Burning cells within ``radius`` cells (Chebyshev) of (r, c)."""
        burning = self.fire.burning
        return int(burning[max(r - radius, 0):r + radius + 1,
                           max(c - radius, 0):c + radius + 1].sum())

    def _is_refuge(self, r: int, c: int) -> bool:
        fire = self.fire
        return bool(fire.state[r, c] == BURNED or not self.land.burnable[r, c] or fire.line[r, c])

    def _fire_distance(self) -> np.ndarray:
        """Chessboard distance (cells) to the nearest burning cell, cached per substep."""
        key = self.fire.substep
        if getattr(self, "_distance_key", None) != key:
            burning = self.fire.burning
            if burning.any():
                self._distance = distance_transform_cdt(~burning, metric="chessboard")
            else:
                self._distance = np.full(burning.shape, 10 ** 6)
            self._distance_key = key
        return self._distance

    def _passable_grid(self, kind: int) -> np.ndarray:
        grid = ~self.land.water & ~self.fire.burning
        if kind == DOZER:
            grid &= self.land.slope_percent <= UNIT_TYPES[DOZER].max_slope_percent
        return grid

    def _retreat(self, unit: Unit) -> None:
        """LCES-style automatic escape once fire is within RETREAT_RADIUS cells.

        The unit heads for the nearest reachable safe cell: a refuge (black, non-burnable
        or line) or a cell at least SAFE_DISTANCE cells from any burning cell. The route is
        a breadth-first search over passable cells, so the unit does not walk into a
        pocket that the fire is closing.
        """
        r, c = unit.row, unit.col
        if self._is_refuge(r, c) or not self._threat(r, c, RETREAT_RADIUS):
            return
        distance = self._fire_distance()
        passable = self._passable_grid(unit.kind)
        refuge = ((self.fire.state == BURNED) | ~self.land.burnable | self.fire.line) & passable
        safe = (refuge | (distance >= SAFE_DISTANCE)) & passable
        # Breadth-first distance from the safe set, restricted to passable cells.
        hops = np.full(passable.shape, -1, dtype=np.int32)
        frontier = safe.copy()
        hops[frontier] = 0
        step = 0
        while frontier.any() and hops[r, c] < 0 and step < 4 * max(passable.shape):
            step += 1
            grown = binary_dilation(frontier, structure=np.ones((3, 3), dtype=bool))
            frontier = grown & passable & (hops < 0)
            hops[frontier] = step
        if hops[r, c] <= 0:
            return
        rows, cols = passable.shape
        for dr, dc in sorted(OFFSETS, key=lambda o: -distance[min(max(r + o[0], 0), rows - 1),
                                                             min(max(c + o[1], 0), cols - 1)]):
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < cols and 0 <= hops[rr, cc] < hops[r, c]:
                unit.row, unit.col = rr, cc
                unit.progress_m, unit.progress_key = 0.0, None
                unit.retreats += 1
                return

    def _overrun(self, unit: Unit) -> None:
        """Fire reached the unit's cell: a close call if an adjacent cell is open, else loss.

        At 180 m cells the flame (at most ~6 m long in the Anderson table) occupies a small
        part of a cell, so a unit with an open neighbour is displaced, not killed. Being
        surrounded is an entrapment and the unit is lost.
        """
        rows, cols = self.land.shape
        distance = self._fire_distance()
        best, best_score = None, None
        for dr, dc in OFFSETS:
            rr, cc = unit.row + dr, unit.col + dc
            if 0 <= rr < rows and 0 <= cc < cols and self._passable(unit.kind, rr, cc):
                score = (0 if self._is_refuge(rr, cc) else 1, -int(distance[rr, cc]))
                if best_score is None or score < best_score:
                    best, best_score = (rr, cc), score
        if best is None:
            unit.active = False
            unit.lost = True
            return
        unit.row, unit.col = best
        unit.progress_m, unit.progress_key = 0.0, None
        unit.close_calls += 1

    @staticmethod
    def _key_progress(unit: Unit, key: Tuple[str, int, int]) -> None:
        """Keep accumulated metres only while the unit works toward the same cell."""
        if unit.progress_key != key:
            unit.progress_m, unit.progress_key = 0.0, key

    def _unit_substep(self, unit: Unit) -> None:
        if not unit.active:
            return
        if self.auto_retreat:
            # Assumption (ADR-028): escape along a prepared route, partly by vehicle, covers
            # up to two cells (360 m) per 2-minute substep.
            before = (unit.row, unit.col)
            self._retreat(unit)
            if (unit.row, unit.col) != before:
                self._retreat(unit)
                return
        action = unit.action
        if action == 0:
            return
        k = (action - 1) % 8
        building = action >= 9
        dt = SUBSTEP_MINUTES
        if building and self._buildable(unit.row, unit.col):
            self._key_progress(unit, ("build", unit.row, unit.col))
            rate = unit.spec.line_m_per_min(self.land.fuel[unit.row, unit.col],
                                            self.land.slope_percent[unit.row, unit.col])
            unit.progress_m += rate * dt
            if unit.progress_m >= CELL_SIZE_M:
                self.fire.line[unit.row, unit.col] = True
                unit.line_cells += 1
                unit.progress_m, unit.progress_key = 0.0, None
            return
        target = self._target(unit, k)
        if target is None:
            unit.progress_m, unit.progress_key = 0.0, None
            return
        self._key_progress(unit, ("move",) + tuple(int(v) for v in target))
        slope = abs(self.land.elevation[target] - self.land.elevation[unit.row, unit.col])
        # Slope slowdown roughly matching Sullivan et al. 2020 (x0.6 at 15 deg, x0.4 at 30 deg).
        slowdown = np.exp(-2.0 * slope / OFFSET_DISTANCE[k])
        unit.progress_m += unit.spec.travel_m_per_min * slowdown * dt
        if unit.progress_m >= OFFSET_DISTANCE[k]:
            unit.row, unit.col = target
            unit.progress_m, unit.progress_key = 0.0, None

    def _advance(self, fire: FireState, index: int, units: Optional[List[Unit]]) -> float:
        """Run one decision interval; return weighted new damage."""
        spec = self.spec_now
        fire.set_weather(spec.weather.at(index))
        damage = 0.0
        for sub in range(SUBSTEPS_PER_DECISION):
            minute = index * DECISION_MINUTES + sub * SUBSTEP_MINUTES
            if units is not None:
                for slot, unit in enumerate(units):
                    if not unit.active and not unit.lost and minute >= unit.arrival_minute:
                        unit.row, unit.col = self._staging_cell(slot, unit)
                        unit.active = True
                    self._unit_substep(unit)
            new = fire.step_substep()
            damage += float(self.weights[new].sum())
            if units is not None:
                for unit in units:
                    if unit.active and fire.state[unit.row, unit.col] == BURNING:
                        self._overrun(unit)
        return damage

    # ------------------------------------------------------------------ gym API
    def step(self, action):
        action = np.asarray(action, dtype=int).reshape(-1)
        if action.shape != (MAX_UNITS,):
            raise ValueError("action must have one entry per unit slot")
        mask = self.action_masks().reshape(MAX_UNITS, ACTIONS_PER_UNIT)
        invalid = 0
        for slot, unit in enumerate(self.units):
            chosen = int(action[slot])
            if not mask[slot, chosen]:
                chosen, invalid = 0, invalid + 1
            unit.action = chosen

        lost_before = sum(unit.lost for unit in self.units)
        calls_before = sum(unit.close_calls for unit in self.units)
        damage = self._advance(self.fire, self.decision, self.units)
        reward = (self.noop_damage[self.decision] - damage) / self.norm
        self.stats["agent_damage"] += damage
        self.decision += 1
        terminated = False
        if not self.fire.active:
            future = sum(self.noop_damage[self.decision:])
            reward += future / self.norm
            terminated = True
        elif self.decision >= self.spec_now.horizon:
            # Units withdraw; lines stay; both rollouts continue for the tail on shared numbers.
            for unit in self.units:
                unit.active = False
            for index in range(self.decision, self.decision + TAIL_DECISIONS):
                tail = self._advance(self.fire, index, units=None)
                reward += (self.noop_damage[index] - tail) / self.norm
                self.stats["agent_damage"] += tail
            terminated = True
        lost_now = sum(unit.lost for unit in self.units) - lost_before
        calls_now = sum(unit.close_calls for unit in self.units) - calls_before
        reward -= self.unit_loss_penalty * lost_now + self.close_call_penalty * calls_now
        self.stats["close_calls"] = self.stats.get("close_calls", 0) + calls_now
        self.stats["units_lost"] += lost_now
        self.stats["retreats"] = sum(unit.retreats for unit in self.units)
        self.stats["line_cells"] = int(self.fire.line.sum())
        edge = self.fire.ever_burned
        self.stats["edge_contact"] = bool(edge[0].any() or edge[-1].any() or edge[:, 0].any()
                                          or edge[:, -1].any())
        info = self._info()
        info["invalid_actions"] = invalid
        if terminated:
            info["episode_summary"] = self.summary()
        return self._observation(), float(reward), terminated, False, info

    def summary(self) -> dict:
        noop_urban = float((self.noop_final.ever_burned & ~self.prior_damage & self.land.urban).sum())
        agent_urban = float((self.fire.ever_burned & ~self.prior_damage & self.land.urban).sum())
        return {
            "name": self.spec_now.name,
            "seed": self.spec_now.seed,
            "horizon": self.spec_now.horizon,
            "noop_damage": self.noop_total,
            "agent_damage_to_now": self.stats["agent_damage"],
            "saved_fraction": (self.noop_total - self.stats["agent_damage"]) / self.norm,
            "noop_new_cells": int((self.noop_final.ever_burned & ~self.prior_damage).sum()),
            "agent_new_cells": int((self.fire.ever_burned & ~self.prior_damage).sum()),
            "noop_urban_cells": noop_urban,
            "agent_urban_cells": agent_urban,
            "units_lost": int(self.stats["units_lost"]),
            "retreats": int(self.stats["retreats"]),
            "close_calls": int(self.stats.get("close_calls", 0)),
            "line_cells": int(self.stats["line_cells"]),
            "edge_contact": self.stats["edge_contact"],
        }

    def _info(self) -> dict:
        return {"decision": self.decision, "units_active": sum(u.active for u in self.units),
                "fire_active": self.fire.active}

    # ------------------------------------------------------------------ observation
    def _pool(self, values: np.ndarray, how: str = "mean") -> np.ndarray:
        rows, cols = values.shape
        blocks = values.reshape(rows // MAP_POOL, MAP_POOL, cols // MAP_POOL, MAP_POOL)
        return blocks.max(axis=(1, 3)) if how == "max" else blocks.mean(axis=(1, 3))

    def _observation(self) -> Dict[str, np.ndarray]:
        land, fire = self.land, self.fire
        burning = fire.burning.astype(np.float32)
        ros = np.clip(np.log1p(land.base_ros) / np.log1p(60.0), 0.0, 1.0)
        elevation = land.elevation - land.elevation.mean()
        elevation = np.clip(elevation / 600.0, -1.0, 1.0)
        layers = [
            self._pool(burning, "max"),
            self._pool(fire.ever_burned.astype(np.float32)),
            self._pool(fire.line.astype(np.float32), "max"),
            self._pool(land.urban.astype(np.float32), "max"),
            self._pool(ros),
            self._pool((~land.burnable).astype(np.float32)),
            self._pool(land.water.astype(np.float32), "max"),
            self._pool(np.clip(land.slope_percent / 100.0, 0.0, 1.0)),
            self._pool(elevation),
        ]
        rows, cols = land.shape
        for slot in range(MAX_UNITS):
            plane = np.zeros((rows // MAP_POOL, cols // MAP_POOL), dtype=np.float32)
            if slot < len(self.units) and self.units[slot].active:
                unit = self.units[slot]
                plane[unit.row // MAP_POOL, unit.col // MAP_POOL] = 1.0
            layers.append(plane)
        grid = np.stack(layers).astype(np.float32)

        unit_rows = []
        burning_cells = np.argwhere(fire.burning)
        urban_cells = np.argwhere(land.urban & ~fire.ever_burned)
        blocked = (~land.burnable | fire.line).astype(np.float32)
        for slot in range(MAX_UNITS):
            features = np.zeros(self.unit_features, dtype=np.float32)
            if slot < len(self.units):
                unit = self.units[slot]
                features[0] = float(unit.active)
                features[1] = float(unit.lost)
                features[2] = float(unit.kind == DOZER)
                features[3] = float(np.clip((unit.arrival_minute - self.decision * DECISION_MINUTES)
                                            / 180.0, -1.0, 1.0))
                if unit.active:
                    features[4] = unit.row / rows * 2 - 1
                    features[5] = unit.col / cols * 2 - 1
                    features[6] = min(unit.progress_m / CELL_SIZE_M, 1.0)
                    features[7] = unit.action / (ACTIONS_PER_UNIT - 1)
                    here = np.array((unit.row, unit.col))
                    for offset, cells in ((8, burning_cells), (10, urban_cells)):
                        if len(cells):
                            delta = cells - here
                            nearest = delta[np.argmin(np.abs(delta).sum(axis=1))]
                            features[offset:offset + 2] = np.clip(nearest / 64.0, -1.0, 1.0)
                    crop = []
                    for layer in (burning, fire.ever_burned.astype(np.float32), blocked):
                        padded = np.pad(layer, PATCH, constant_values=1.0 if layer is blocked else 0.0)
                        crop.append(padded[unit.row:unit.row + 2 * PATCH + 1,
                                           unit.col:unit.col + 2 * PATCH + 1].ravel())
                    features[12:] = np.concatenate(crop)
            unit_rows.append(features)
        units = np.concatenate(unit_rows).astype(np.float32)

        weather = self.spec_now.weather.at(self.decision)
        direction = np.deg2rad(weather.wind_to_deg)
        hour = np.deg2rad(weather.local_hour * 15.0)
        globals_ = np.asarray((
            np.clip(weather.wind_midflame_m_s / 8.0, 0.0, 1.0),
            np.sin(direction), np.cos(direction),
            np.clip(weather.moisture / 0.3, 0.0, 1.0),
            np.sin(hour), np.cos(hour),
            self.decision / max(self.spec_now.horizon, 1),
            sum(u.active for u in self.units) / MAX_UNITS,
            np.clip(burning.sum() / 500.0, 0.0, 1.0),
        ), dtype=np.float32)
        return {"map": grid, "units": units, "globals": globals_}
