"""TRAIN-only, budgeted Gymnasium wrapper for the pinned SimFire/FEDS setup.

This is a technical training environment. Its reward is simulated area burned, not
the post-hoc FEDS perimeter, and the provisional wind factor is not calibrated.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
from types import SimpleNamespace
from typing import Any, Dict, Optional, Sequence, Tuple

import gymnasium as gym
import numpy as np

from .gridmet_weather import gridmet_proxy_to_simfire
from .simfire_initial_state import compose_initial_fire_map, update_cumulative_burned
from .simfire_timebase import updates_for_duration


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data/manifests/feds-episode-cohort-v1.json"
WEATHER = ROOT / ".local/gridmet/feds-episode-weather-v1.json"
INPUT_ROOT = ROOT / ".local/feds-simfire-cases"
CONFIG_TEMPLATE = ROOT / "configs/simfire_feds_base.yml"

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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def build_action_mask(fire_map: Any, active_front: Any, remaining_budget: int) -> np.ndarray:
    """Keep no-op legal in every state; mask lines without budget or placement cells."""
    if type(remaining_budget) is not int or remaining_budget < 0:
        raise ValueError("remaining budget must be a nonnegative integer")
    mask = np.zeros(len(SECTOR_DIRECTIONS) + 1, dtype=bool)
    mask[0] = True
    if remaining_budget:
        for sector in range(len(SECTOR_DIRECTIONS)):
            mask[sector + 1] = bool(fireline_points(fire_map, active_front, sector))
    return mask


def cumulative_burn_mask(previous: Any, fire_map: Any) -> np.ndarray:
    """Preserve all prior damage even if SimFire later overwrites a cell with a line."""
    prior = np.asarray(previous, dtype=bool)
    state = np.asarray(fire_map)
    if prior.ndim != 2 or state.shape != prior.shape:
        raise ValueError("cumulative burn and fire map must be equally shaped 2-D arrays")
    return prior | np.isin(state, (SIMFIRE_BURNING, SIMFIRE_BURNED))


class FedsSimFireEnv(gym.Env):
    """A 48h TRAIN episode with four shared 12h decisions and a discrete crew budget.

    Actions are no-op plus eight directions around the current active-front centroid.
    Each non-no-op action places at most seven SimFire fireline cells and costs one
    budget unit. This deliberately simple action mapping enables PPO execution; it is
    not a field-validated line-construction model.
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        *,
        wind_adjustment_factor: float,
        budgets: Sequence[int] = (0, 2, 4),
        scenario_ids: Optional[Sequence[str]] = None,
        internal_update_minutes: int = 5,
        manifest_path: Path = MANIFEST,
        weather_path: Path = WEATHER,
        input_root: Path = INPUT_ROOT,
    ) -> None:
        if not np.isfinite(wind_adjustment_factor) or not 0.0 <= wind_adjustment_factor <= 1.0:
            raise ValueError("wind adjustment factor must be in [0, 1]")
        if not budgets or any(type(value) is not int or value < 0 for value in budgets):
            raise ValueError("budgets must be nonempty nonnegative integers")
        if internal_update_minutes not in (1, 3, 5, 10, 15):
            raise ValueError("internal update interval must be 1, 3, 5, 10, or 15 minutes")

        self.wind_adjustment_factor = float(wind_adjustment_factor)
        self.budgets = tuple(budgets)
        self.max_budget = max(1, max(self.budgets))
        self.internal_update_minutes = internal_update_minutes
        self.horizon_steps = 4
        self.block_count = 16

        manifest_path = Path(manifest_path)
        weather_path = Path(weather_path)
        input_root = Path(input_root)
        self.manifest_sha256 = sha256_file(manifest_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("test_cases_loaded") is not False:
            raise ValueError("Refusing an episode manifest that includes TEST cases")
        all_cases = {
            case["scenario_id"]: case
            for case in manifest["cases"]
            if case.get("split") == "train"
        }
        if not all_cases:
            raise ValueError("The FEDS manifest has no TRAIN episodes")
        if scenario_ids is not None:
            requested = tuple(scenario_ids)
            unknown = set(requested) - set(all_cases)
            if unknown:
                raise ValueError("Only manifest TRAIN scenario IDs are accepted: %s" % sorted(unknown))
            all_cases = {key: all_cases[key] for key in requested}
        self.cases = all_cases
        self.scenario_ids = tuple(all_cases)

        weather = json.loads(weather_path.read_text(encoding="utf-8"))
        if weather.get("test_cases_loaded") is not False:
            raise ValueError("Refusing gridMET records that include TEST cases")
        if weather.get("episode_manifest_sha256") != self.manifest_sha256:
            raise ValueError("gridMET file was built from a different episode manifest")
        train_weather = {
            item["scenario_id"]: item
            for item in weather["cases"]
            if item.get("split") == "train"
        }
        if set(self.scenario_ids) - set(train_weather):
            raise ValueError("At least one selected TRAIN case is missing gridMET forcing")
        self.weather_by_id = {key: train_weather[key] for key in self.scenario_ids}
        self.weather_sha256 = sha256_file(weather_path)
        self.input_root = input_root

        self.action_space = gym.spaces.Discrete(9)
        self.observation_space = gym.spaces.Dict({
            "grid": gym.spaces.Box(0.0, 1.0, shape=(4, 16, 16), dtype=np.float32),
            "budget": gym.spaces.Box(0.0, 1.0, shape=(2,), dtype=np.float32),
            "weather": gym.spaces.Box(-1.0, 1.0, shape=(4,), dtype=np.float32),
            "time": gym.spaces.Box(0.0, 1.0, shape=(1,), dtype=np.float32),
        })
        self._done = True

    def action_masks(self) -> np.ndarray:
        fire_map = self.simulation.fire_map
        front = fire_map == SIMFIRE_BURNING
        return build_action_mask(fire_map, front, self.remaining_budget)

    def _load_episode(self, scenario_id: str) -> None:
        import rasterio
        import yaml
        from simfire.enums import FuelModelRGB13, FuelModelToFuel
        from simfire.game.sprites import Fire
        from simfire.sim.simulation import FireSimulation
        from simfire.utils.config import Config
        from simfire.utils.layers import OperationalFuelLayer, OperationalTopographyLayer

        case = self.cases[scenario_id]
        weather = self.weather_by_id[scenario_id]
        expected_time = case["evaluation_reference"]["initial_state_time"]
        if weather.get("initial_state_time") != expected_time or len(weather.get("segments", [])) != 4:
            raise ValueError("TRAIN weather must match the initial time and four 12h segments")

        case_dir = self.input_root / scenario_id
        receipt_path = case_dir / "input-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if (receipt.get("scenario_id") != scenario_id or receipt.get("split") != "train"
                or receipt.get("test_cases_loaded") is not False
                or receipt.get("initial_state_time") != expected_time):
            raise ValueError("LANDFIRE/FEDS input receipt is not the requested TRAIN start")

        paths = (
            (case_dir / receipt["fuel"]["file"], receipt["fuel"]["sha256"]),
            (case_dir / receipt["terrain"]["file"], receipt["terrain"]["sha256"]),
            (case_dir / receipt["initial_feds_state"]["mask_file"],
             receipt["initial_feds_state"]["mask_sha256"]),
        )
        for path, expected_hash in paths:
            if not path.is_file() or sha256_file(path) != expected_hash:
                raise ValueError("Missing or changed verified TRAIN input: %s" % path)
        fuel_path, terrain_path, masks_path = (item[0] for item in paths)
        with rasterio.open(fuel_path) as source:
            fuel = source.read(1)
        with rasterio.open(terrain_path) as source:
            elevation = source.read(1)
        with np.load(masks_path) as masks:
            scar = masks["burn_scar"].astype(bool)
            front = masks["active_front"].astype(bool)
        if fuel.shape != (256, 256) or elevation.shape != fuel.shape:
            raise ValueError("Verified LANDFIRE rasters must match the 256x256 study grid")
        if scar.shape != fuel.shape or front.shape != fuel.shape or not front.any():
            raise ValueError("FEDS start masks are invalid")

        forcing = []
        for segment in weather["segments"]:
            values = segment["gridmet_values"]
            forcing.append(gridmet_proxy_to_simfire(
                wind_speed_m_s=values["vs"]["value"],
                wind_from_degrees=values["th"]["value"],
                fm100_percent=values["fm100"]["value"],
                wind_adjustment_factor=self.wind_adjustment_factor,
            ))
        self.forcing = forcing

        unsupported = sorted(set(int(value) for value in np.unique(fuel)) - set(FuelModelToFuel))
        unsupported_rgb = sorted(set(int(value) for value in np.unique(fuel)) - set(FuelModelRGB13))
        if unsupported or unsupported_rgb:
            raise ValueError("Pinned SimFire cannot map TRAIN LANDFIRE fuel codes: %s" % (unsupported or unsupported_rgb))

        base_config = yaml.safe_load(CONFIG_TEMPLATE.read_text(encoding="utf-8"))
        base_config["simulation"]["update_rate"] = self.internal_update_minutes
        base_config["fire"]["max_fire_duration"] = updates_for_duration(
            90, self.internal_update_minutes
        )
        rows, columns = fuel.shape
        front_rows, front_columns = np.where(front)
        base_config["fire"]["fire_initial_position"]["static"]["position"] = [
            int(front_columns[0]), int(front_rows[0])
        ]
        config = Config(config_dict=base_config)
        config.area.screen_size = (rows, columns)
        config.area.pixel_scale = 180.0 * 3.280839895
        layers = SimpleNamespace(layers=["fuel"], fuel=fuel, topography=elevation)
        config.terrain.fuel_layer = OperationalFuelLayer(layers)
        config.terrain.topography_layer = OperationalTopographyLayer(layers)
        config.wind.speed = np.full(
            (rows, columns), forcing[0]["wind_speed_midflame_ft_per_min_proxy"], dtype=np.float64
        )
        config.wind.direction = np.full(
            (rows, columns), forcing[0]["wind_direction_degrees_clockwise_north_to"], dtype=np.float64
        )
        config.environment.moisture = forcing[0]["fuel_moisture_fraction_proxy"]

        random.seed(0)
        np.random.seed(0)
        self.simulation = FireSimulation(config)
        initial_map = compose_initial_fire_map(scar, front)
        self.simulation.fire_map = initial_map.astype(np.int64)
        self.simulation.fire_manager.sprites = [
            Fire((int(column), int(row)), config.display.fire_size, headless=True)
            for row, column in zip(front_rows, front_columns)
        ]
        self.simulation.fire_manager.durations = [0] * len(self.simulation.fire_manager.sprites)
        self.simulation.fire_sprites = self.simulation.fire_manager.sprites
        self.cumulative_burned = update_cumulative_burned(scar, self.simulation.fire_map)
        self.fuel = fuel
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
        super().reset(seed=seed)
        if options:
            raise ValueError("reset options are not supported")
        index = int(self.np_random.integers(len(self.scenario_ids)))
        self.scenario_id = self.scenario_ids[index]
        self.initial_budget = int(self.np_random.choice(self.budgets))
        self.remaining_budget = self.initial_budget
        self.decision_index = 0
        self._load_episode(self.scenario_id)
        self._done = False
        return self._observation(), {
            "scenario_id": self.scenario_id,
            "split": "train",
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
            applied_points = fireline_points(self.simulation.fire_map, front, action - 1)
            if applied_points:
                self.simulation.update_mitigation([
                    (x, y, SIMFIRE_FIRELINE) for x, y in applied_points
                ])
                self.remaining_budget -= 1

        previous = self.cumulative_burned.copy()
        if self.simulation_active:
            current = self.forcing[self.decision_index]
            self.simulation.fire_manager.U[:] = current["wind_speed_midflame_ft_per_min_proxy"]
            self.simulation.fire_manager.U_dir[:] = current["wind_direction_degrees_clockwise_north_to"]
            self.simulation.fire_manager.environment.M_f = current["fuel_moisture_fraction_proxy"]
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
            "split": "train",
            "decision_step": self.decision_index,
            "remaining_budget": self.remaining_budget,
            "new_burned_cells": new_burned_cells,
            "cumulative_burned_cells": int(self.cumulative_burned.sum()),
            "fire_active": bool(self.simulation_active),
            "action_applied": bool(applied_points),
            "invalid_action": invalid,
            "feds_future_perimeters_used": False,
        }
        return self._observation(), float(reward), terminated, truncated, info
