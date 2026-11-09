"""Probabilistic cellular-automaton fire spread on FBFM13-coded 180 m grids.

This is a deliberately simple, documented training simulator. It is not Cell2Fire,
not SimFire and not physically validated (ADR-028). Spread from a burning cell to a
neighbour happens with ``p = 1 - exp(-R * dt / d)``, where ``R`` is a directional rate
of spread built from the target cell's tabulated Anderson (1982) rate, a wind factor
and a slope factor in the form of Alexandridis et al. (2008), and a fuel-moisture
damping term. All randomness comes from per-(episode seed, substep) generators, so two
rollouts of the same episode share common random numbers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np


CELL_SIZE_M = 180.0
SUBSTEP_MINUTES = 2.0

# Anderson (1982) INT-122 rate of spread for the 13 standard fuel models, chains/h at
# 8% dead fuel moisture, 5 mi/h midflame wind and no slope. 1 chain = 20.1168 m.
ANDERSON_ROS_CH_PER_H = {
    1: 78.0, 2: 35.0, 3: 104.0, 4: 75.0, 5: 18.0, 6: 32.0, 7: 20.0,
    8: 1.6, 9: 7.5, 10: 7.9, 11: 6.0, 12: 13.0, 13: 13.5,
}
REFERENCE_MIDFLAME_WIND_M_S = 5.0 * 0.44704
REFERENCE_MOISTURE = 0.08
MOISTURE_OF_EXTINCTION = 0.30

# Wind: Rothermel-style R(theta) = R_nowind * (1 + phi_w(U) * h(theta)), with
# phi_w(U) = phi_ref * (U / U_ref) ** WIND_EXPONENT and h = ((1 + cos theta) / 2) ** 2
# (head 1, flank 0.25, back 0). R_nowind is chosen so the head rate at U_ref equals the
# Anderson table. phi_ref per group is an assumption (ADR-028), not a fitted value.
WIND_PHI_REF = {"grass": 10.0, "shrub": 6.0, "timber": 4.0, "slash": 4.0, "urban": 2.0}
WIND_EXPONENT = 1.5
# Stochastic 8-neighbour contact spread runs ahead of the per-pair rate: a front cell has
# several burning neighbours and the front roughens. Measured on flat line fires at the
# tabled wind (FBFM 1, 2, 4, 5, 8, 10) the emergent head rate was 2.8-3.6x the pair rate;
# this factor brings it back to the table within about 20% (tests/test_synthetic_ca.py).
CONTACT_CALIBRATION = 0.31
# Slope: Alexandridis et al. (2008) p_s = exp(a * slope_degrees).
SLOPE_A = 0.078

URBAN = 91
SNOW = 92
AGRICULTURE = 93
WATER = 98
BARREN = 99
NONBURNABLE_CODES = (SNOW, AGRICULTURE, WATER, BARREN)
FUEL_GROUPS = {"grass": (1, 2, 3), "shrub": (4, 5, 6, 7), "timber": (8, 9, 10),
               "slash": (11, 12, 13)}
# Assumption (ADR-028): structures burn from neighbouring fire slowly and burn long.
URBAN_ROS_M_PER_MIN = 1.5
# Assumed minimum burning time of a 180 m cell (flaming plus smouldering edge).
RESIDENCE_MINUTES = {"grass": 30.0, "shrub": 60.0, "timber": 180.0, "slash": 240.0,
                     "urban": 180.0}

# Neighbour offsets (row, column); index k is the direction a fire moves from source to
# target. Compass bearing (clockwise from north) of each move.
OFFSETS = ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1))
OFFSET_BEARINGS = np.deg2rad(np.array((0, 45, 90, 135, 180, 225, 270, 315), dtype=float))
OFFSET_DISTANCE = np.array([CELL_SIZE_M * (2 ** 0.5 if r and c else 1.0) for r, c in OFFSETS])

UNBURNED, BURNING, BURNED = 0, 1, 2


def ros_m_per_min(code: int) -> float:
    return ANDERSON_ROS_CH_PER_H[code] * 20.1168 / 60.0


def fuel_group_of(code: int) -> Optional[str]:
    if code == URBAN:
        return "urban"
    for name, codes in FUEL_GROUPS.items():
        if code in codes:
            return name
    return None


def wind_phi_ref_grid(fuel: np.ndarray) -> np.ndarray:
    phi = np.zeros(fuel.shape, dtype=np.float64)
    for code in list(ANDERSON_ROS_CH_PER_H) + [URBAN]:
        phi[fuel == code] = WIND_PHI_REF[fuel_group_of(code)]
    return phi


def base_ros_grid(fuel: np.ndarray) -> np.ndarray:
    """Tabulated spread rate (m/min) of each cell's own fuel; 0 for non-burnable."""
    ros = np.zeros(fuel.shape, dtype=np.float64)
    for code in ANDERSON_ROS_CH_PER_H:
        ros[fuel == code] = ros_m_per_min(code)
    ros[fuel == URBAN] = URBAN_ROS_M_PER_MIN
    return ros


def burn_minutes_grid(fuel: np.ndarray) -> np.ndarray:
    """How long a cell keeps burning: no-wind crossing time plus group residence time."""
    minutes = np.zeros(fuel.shape, dtype=np.float64)
    ros = base_ros_grid(fuel) / (1.0 + wind_phi_ref_grid(fuel))
    for code in list(ANDERSON_ROS_CH_PER_H) + [URBAN]:
        cells = fuel == code
        if not cells.any():
            continue
        crossing = 1.5 * CELL_SIZE_M / ros[cells][0]
        minutes[cells] = RESIDENCE_MINUTES[fuel_group_of(code)] + crossing
    return np.clip(minutes, 0.0, 12 * 60.0)


def moisture_factor(moisture: float) -> float:
    """Linear damping, 1 at the table's 8% and 0 at the assumed 30% extinction."""
    value = (MOISTURE_OF_EXTINCTION - moisture) / (MOISTURE_OF_EXTINCTION - REFERENCE_MOISTURE)
    return float(np.clip(value, 0.0, 1.5))


def diurnal_factor(local_hour: float) -> float:
    """Assumed day/night activity: 0.3 at night rising to 1.0 in early afternoon."""
    phase = np.sin(np.pi * (local_hour - 7.0) / 12.0)
    return float(0.3 + 0.7 * max(0.0, phase))


@dataclass
class Weather:
    """Forcing for one decision interval. ``wind_to_deg`` is where the wind blows to."""

    wind_midflame_m_s: float
    wind_to_deg: float
    moisture: float
    local_hour: float


@dataclass
class Landscape:
    fuel: np.ndarray
    elevation: np.ndarray
    ros_noise: Optional[np.ndarray] = None

    def __post_init__(self) -> None:
        if self.fuel.shape != self.elevation.shape or self.fuel.ndim != 2:
            raise ValueError("fuel and elevation must be equally shaped 2-D grids")
        self.fuel = np.asarray(self.fuel, dtype=np.int16)
        self.elevation = np.asarray(self.elevation, dtype=np.float64)
        if self.ros_noise is None:
            self.ros_noise = np.ones(self.fuel.shape)
        self.base_ros = base_ros_grid(self.fuel) * self.ros_noise
        self.phi_ref = wind_phi_ref_grid(self.fuel)
        self.nowind_ros = self.base_ros / (1.0 + self.phi_ref)
        self.burn_minutes = burn_minutes_grid(self.fuel)
        self.burnable = self.base_ros > 0
        self.urban = self.fuel == URBAN
        self.water = self.fuel == WATER
        self.spot_source = np.isin(self.fuel, FUEL_GROUPS["shrub"] + FUEL_GROUPS["timber"]
                                   + FUEL_GROUPS["slash"])
        rows, cols = self.fuel.shape
        padded = np.pad(self.elevation, 1, mode="edge")
        # Slope angle (degrees) seen when moving from a neighbour in direction k into a cell.
        self.slope_into = np.zeros((8, rows, cols))
        for k, (dr, dc) in enumerate(OFFSETS):
            source = padded[1 - dr:1 - dr + rows, 1 - dc:1 - dc + cols]
            self.slope_into[k] = np.degrees(np.arctan((self.elevation - source)
                                                      / OFFSET_DISTANCE[k]))
        self.slope_factor = np.exp(SLOPE_A * np.clip(self.slope_into, -25.0, 25.0))
        self.log_q_cache = {}
        gy, gx = np.gradient(self.elevation, CELL_SIZE_M)
        self.slope_percent = 100.0 * np.hypot(gx, gy)

    @property
    def shape(self) -> Tuple[int, int]:
        return self.fuel.shape


def shift(array: np.ndarray, dr: int, dc: int, fill=0) -> np.ndarray:
    """out[r, c] = array[r - dr, c - dc]; cells shifted in from outside get ``fill``."""
    out = np.full_like(array, fill)
    rows, cols = array.shape
    rs, re = max(dr, 0), rows + min(dr, 0)
    cs, ce = max(dc, 0), cols + min(dc, 0)
    out[rs:re, cs:ce] = array[rs - dr:re - dr, cs - dc:ce - dc]
    return out


@dataclass
class SpreadParams:
    """Domain-randomisable multipliers; defaults are the tabulated model."""

    spread_scale: float = 1.0
    spot_rate: float = 2e-4
    spot_mean_cells: float = 3.0


class FireState:
    """Mutable fire state for one rollout of one episode."""

    def __init__(self, landscape: Landscape, episode_seed: int, params: SpreadParams) -> None:
        self.landscape = landscape
        self.seed = int(episode_seed)
        self.params = params
        self.state = np.zeros(landscape.shape, dtype=np.int8)
        self.remaining = np.zeros(landscape.shape, dtype=np.float64)
        self.ever_burned = np.zeros(landscape.shape, dtype=bool)
        self.line = np.zeros(landscape.shape, dtype=bool)
        self.substep = 0
        self._log_q = None

    def copy(self) -> "FireState":
        other = FireState.__new__(FireState)
        other.__dict__.update(self.__dict__)
        for name in ("state", "remaining", "ever_burned", "line"):
            setattr(other, name, getattr(self, name).copy())
        return other

    def ignite(self, mask: np.ndarray) -> None:
        cells = np.asarray(mask, dtype=bool) & self.landscape.burnable & ~self.line
        cells &= self.state == UNBURNED
        self.state[cells] = BURNING
        self.remaining[cells] = self.landscape.burn_minutes[cells]
        self.ever_burned |= cells

    def mark_burned(self, mask: np.ndarray) -> None:
        cells = np.asarray(mask, dtype=bool)
        self.state[cells] = BURNED
        self.remaining[cells] = 0.0
        self.ever_burned |= cells

    @property
    def burning(self) -> np.ndarray:
        return self.state == BURNING

    @property
    def active(self) -> bool:
        return bool(self.burning.any())

    def set_weather(self, weather: Weather) -> None:
        """Precompute log(1 - p) per direction for the next decision interval.

        Results are cached on the landscape, so the agent and no-op rollouts of one
        episode (and repeated blocky gridMET-like hours) share the same arrays.
        """
        land = self.landscape
        speed = max(0.0, float(weather.wind_midflame_m_s))
        to = np.deg2rad(weather.wind_to_deg)
        scale = (CONTACT_CALIBRATION * self.params.spread_scale * moisture_factor(weather.moisture)
                 * diurnal_factor(weather.local_hour))
        self._wind = (speed, to)
        key = (speed, to, scale)
        cached = land.log_q_cache.get(key)
        if cached is None:
            cached = np.zeros((8,) + land.shape)
            phi = land.phi_ref * (speed / REFERENCE_MIDFLAME_WIND_M_S) ** WIND_EXPONENT
            for k in range(8):
                alignment = ((1.0 + np.cos(OFFSET_BEARINGS[k] - to)) / 2.0) ** 2
                rate = land.nowind_ros * scale * (1.0 + phi * alignment) * land.slope_factor[k]
                # log(1 - p) with p = 1 - exp(-rate dt / d)  =>  -rate dt / d
                cached[k] = -rate * SUBSTEP_MINUTES / OFFSET_DISTANCE[k]
            if len(land.log_q_cache) >= 64:
                land.log_q_cache.clear()
            land.log_q_cache[key] = cached
        self._log_q = cached

    def _uniform(self, flat_index: np.ndarray, purpose: int) -> np.ndarray:
        """Counter-based uniforms keyed on (seed, substep, cell, purpose).

        Two rollouts of the same episode read the same number for the same cell and
        substep, however different their burning sets are (common random numbers).
        """
        return hashed_uniform(self.seed, self.substep, flat_index, purpose)

    def step_substep(self) -> np.ndarray:
        """Advance 2 minutes; return the cells newly ignited in this substep."""
        if self._log_q is None:
            raise RuntimeError("set_weather must be called before stepping")
        land = self.landscape
        rows, cols = land.shape
        burning = self.burning
        new = np.zeros(land.shape, dtype=bool)
        if not burning.any():
            self.substep += 1
            return new

        # Only the burning cells' bounding box (plus one cell) can ignite by contact.
        row_hits = np.flatnonzero(burning.any(axis=1))
        col_hits = np.flatnonzero(burning.any(axis=0))
        r0, r1 = max(int(row_hits[0]) - 1, 0), min(int(row_hits[-1]) + 2, rows)
        c0, c1 = max(int(col_hits[0]) - 1, 0), min(int(col_hits[-1]) + 2, cols)
        padded = np.pad(burning, 1)
        any_line = bool(self.line.any())
        padded_line = np.pad(self.line, 1) if any_line else None
        log_no = np.zeros((r1 - r0, c1 - c0))
        for k, (dr, dc) in enumerate(OFFSETS):
            reach = padded[1 + r0 - dr:1 + r1 - dr, 1 + c0 - dc:1 + c1 - dc]
            if any_line and dr and dc:
                # A diagonal step between two orthogonally adjacent line cells is blocked.
                vertical = padded_line[1 + r0 - dr:1 + r1 - dr, 1 + c0:1 + c1]
                horizontal = padded_line[1 + r0:1 + r1, 1 + c0 - dc:1 + c1 - dc]
                reach = reach & ~(vertical & horizontal)
            log_no += reach * self._log_q[k, r0:r1, c0:c1]
        candidate = (self.state == UNBURNED) & land.burnable & ~self.line
        window = candidate[r0:r1, c0:c1] & (log_no < 0)
        wr, wc = np.nonzero(window)
        if wr.size:
            tr, tc = wr + r0, wc + c0
            u = self._uniform(tr * cols + tc, 0)
            hit = u < -np.expm1(log_no[wr, wc])
            new[tr[hit], tc[hit]] = True

        speed, to = self._wind
        if self.params.spot_rate > 0 and speed > 0:
            rate = self.params.spot_rate * (speed / REFERENCE_MIDFLAME_WIND_M_S) ** 2
            sr, sc = np.nonzero((burning & land.spot_source)[r0:r1, c0:c1])
            sr, sc = sr + r0, sc + c0
            if sr.size:
                flat = sr * cols + sc
                emit = self._uniform(flat, 1) < rate
                for r, c, f in zip(sr[emit], sc[emit], flat[emit]):
                    f = np.asarray([f])
                    dist = 1.0 - self.params.spot_mean_cells * np.log1p(-self._uniform(f, 2)[0])
                    u1, u2 = self._uniform(f, 3)[0], self._uniform(f, 4)[0]
                    angle = to + 0.35 * np.sqrt(-2.0 * np.log1p(-u1)) * np.cos(2 * np.pi * u2)
                    tr = int(round(r - dist * np.cos(angle)))
                    tc = int(round(c + dist * np.sin(angle)))
                    if 0 <= tr < rows and 0 <= tc < cols and candidate[tr, tc]:
                        new[tr, tc] = True

        self.substep += 1
        box = (slice(r0, r1), slice(c0, c1))
        burning_box = burning[box]
        remaining_box = self.remaining[box]
        remaining_box[burning_box] -= SUBSTEP_MINUTES
        state_box = self.state[box]
        state_box[burning_box & (remaining_box <= 0)] = BURNED
        self.state[new] = BURNING
        self.remaining[new] = land.burn_minutes[new]
        self.ever_burned |= new
        return new


_MASK64 = np.uint64(0xFFFFFFFFFFFFFFFF)


def _splitmix64(x: np.ndarray) -> np.ndarray:
    x = (x + np.uint64(0x9E3779B97F4A7C15)) & _MASK64
    x = ((x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)) & _MASK64
    x = ((x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)) & _MASK64
    return x ^ (x >> np.uint64(31))


def hashed_uniform(seed: int, substep: int, flat_index: np.ndarray, purpose: int) -> np.ndarray:
    """Deterministic uniforms in [0, 1) from a splitmix64 hash of the full key."""
    with np.errstate(over="ignore"):
        key = _splitmix64(np.uint64(int(seed) & 0xFFFFFFFFFFFFFFFF) + np.uint64(0))
        key = _splitmix64(key ^ np.uint64(int(substep) * 8 + int(purpose)))
        x = _splitmix64(np.asarray(flat_index, dtype=np.uint64) ^ key)
    return (x >> np.uint64(11)).astype(np.float64) * (1.0 / 9007199254740992.0)


def initial_state_from_masks(landscape: Landscape, episode_seed: int, params: SpreadParams,
                             scar: np.ndarray, front: np.ndarray) -> FireState:
    """Shared perimeter-to-state rule for synthetic and real starts.

    Scar cells are burned out; front cells burn with their full burn time. Both count
    as prior damage, which the reward never credits or charges.
    """
    fire = FireState(landscape, episode_seed, params)
    scar = np.asarray(scar, dtype=bool) & ~np.asarray(front, dtype=bool)
    fire.mark_burned(scar)
    fire.ignite(front)
    return fire


def damage_weights(landscape: Landscape, urban_weight: float) -> np.ndarray:
    weights = np.where(landscape.burnable, 1.0, 0.0)
    weights[landscape.urban] = urban_weight
    return weights


# --------------------------------------------------------------------------------------
# Procedural landscapes and weather (training and validation only)
# --------------------------------------------------------------------------------------

def fractal_noise(rng: np.random.Generator, shape: Tuple[int, int], octaves: int = 5,
                  persistence: float = 0.55) -> np.ndarray:
    """Sum of bilinearly upsampled random grids, scaled to [0, 1]."""
    rows, cols = shape
    total = np.zeros(shape)
    amplitude = 1.0
    for octave in range(octaves):
        size = 2 ** (octave + 2)
        coarse = rng.random((size + 1, size + 1))
        y = np.linspace(0, size, rows)
        x = np.linspace(0, size, cols)
        y0 = np.floor(y).astype(int).clip(0, size - 1)
        x0 = np.floor(x).astype(int).clip(0, size - 1)
        fy = (y - y0)[:, None]
        fx = (x - x0)[None, :]
        a = coarse[y0][:, x0]
        b = coarse[y0][:, x0 + 1]
        c = coarse[y0 + 1][:, x0]
        d = coarse[y0 + 1][:, x0 + 1]
        total += amplitude * ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy)
        amplitude *= persistence
    total -= total.min()
    return total / max(total.max(), 1e-9)


# Assumed (not data-derived) prior over landscape regimes: group weights for
# grass, shrub, timber, slash.
REGIMES = {
    "grassland": (0.70, 0.20, 0.08, 0.02),
    "shrubland": (0.25, 0.60, 0.12, 0.03),
    "forest": (0.10, 0.20, 0.62, 0.08),
    "mixed": (0.35, 0.30, 0.30, 0.05),
}


def generate_landscape(rng: np.random.Generator, shape: Tuple[int, int] = (128, 128)) -> Landscape:
    rows, cols = shape
    relief = rng.uniform(30.0, 1200.0)
    elevation = 1000.0 + relief * fractal_noise(rng, shape, octaves=6)
    regime = list(REGIMES)[int(rng.integers(len(REGIMES)))]
    weights = np.asarray(REGIMES[regime]) * rng.uniform(0.6, 1.4, 4)
    weights /= weights.sum()

    # Higher ground tends to timber, lower ground to grass, with independent noise.
    height = (elevation - elevation.min()) / max(np.ptp(elevation), 1e-9)
    score = 0.55 * height + 0.45 * fractal_noise(rng, shape)
    order = np.argsort(score, axis=None)
    fuel = np.zeros(rows * cols, dtype=np.int16)
    bounds = np.concatenate(([0], np.cumsum(weights) * rows * cols)).astype(int)
    groups = ("grass", "shrub", "timber", "slash")
    within = fractal_noise(rng, shape).ravel()
    for index, group in enumerate(groups):
        cells = order[bounds[index]:bounds[index + 1]]
        codes = FUEL_GROUPS[group]
        pick = np.minimum((within[cells] * len(codes)).astype(int), len(codes) - 1)
        fuel[cells] = np.asarray(codes)[pick]
    fuel = fuel.reshape(shape)

    low = height < np.quantile(height, rng.uniform(0.0, 0.15))
    fuel[low & (fractal_noise(rng, shape) > 0.5)] = AGRICULTURE
    high = height > np.quantile(height, rng.uniform(0.93, 1.0))
    fuel[high] = BARREN
    for _ in range(int(rng.integers(0, 3))):
        _draw_river(rng, fuel)
    for _ in range(int(rng.integers(0, 5))):
        _draw_settlement(rng, fuel, height)
    noise = np.exp(rng.normal(0.0, 0.25, shape))
    return Landscape(fuel=fuel, elevation=elevation, ros_noise=noise)


def _draw_river(rng: np.random.Generator, fuel: np.ndarray) -> None:
    rows, cols = fuel.shape
    r, c = float(rng.integers(rows)), 0.0
    heading = rng.uniform(-0.5, 0.5)
    if rng.random() < 0.5:
        r, c = 0.0, float(rng.integers(cols))
        heading += np.pi / 2
    width = int(rng.integers(1, 3))
    for _ in range(4 * max(rows, cols)):
        rr, cc = int(r), int(c)
        if not (0 <= rr < rows and 0 <= cc < cols):
            break
        fuel[max(rr - width // 2, 0):rr + width - width // 2,
             max(cc - width // 2, 0):cc + width - width // 2] = WATER
        heading += rng.normal(0.0, 0.15)
        r += np.sin(heading)
        c += np.cos(heading)


def _draw_settlement(rng: np.random.Generator, fuel: np.ndarray, height: np.ndarray) -> None:
    rows, cols = fuel.shape
    candidates = np.argwhere((height < np.quantile(height, 0.6)) & (fuel != WATER))
    if not len(candidates):
        return
    r, c = candidates[int(rng.integers(len(candidates)))]
    radius = rng.uniform(1.5, 5.0)
    yy, xx = np.ogrid[:rows, :cols]
    blob = (yy - r) ** 2 + (xx - c) ** 2 <= radius ** 2
    blob &= rng.random(fuel.shape) < 0.85
    fuel[blob & (fuel != WATER)] = URBAN


@dataclass
class WeatherSeries:
    """One Weather per decision step."""

    steps: list = field(default_factory=list)

    def at(self, index: int) -> Weather:
        return self.steps[min(index, len(self.steps) - 1)]


def generate_weather(rng: np.random.Generator, decisions: int, decision_minutes: float,
                     start_hour: float, wind_adjustment: float = 0.4) -> WeatherSeries:
    """Synthetic 10 m wind with diurnal cycle and a random-walk direction."""
    base_speed = float(np.clip(rng.lognormal(np.log(4.0), 0.5), 0.5, 15.0))
    direction = rng.uniform(0.0, 360.0)
    moisture = rng.uniform(0.04, 0.20)
    steps = []
    for index in range(decisions):
        hour = (start_hour + index * decision_minutes / 60.0) % 24.0
        day = max(0.0, np.sin(np.pi * (hour - 7.0) / 12.0))
        speed10 = base_speed * (0.6 + 0.6 * day) * np.exp(rng.normal(0.0, 0.1))
        direction = (direction + rng.normal(0.0, 6.0)) % 360.0
        steps.append(Weather(wind_midflame_m_s=wind_adjustment * speed10,
                             wind_to_deg=direction, moisture=moisture - 0.02 * day,
                             local_hour=hour))
    return WeatherSeries(steps)
