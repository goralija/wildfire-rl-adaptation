"""Gymnasium bridge from the real FPA-FOD/LANDFIRE cohort to pinned SimFire.

This first adapter is an engineering baseline, not a validated fire-control model.
It deliberately labels the temporary atmosphere as demonstration-only and never
uses historical final area, perimeters, or response actions as observations/rewards.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import gymnasium as gym
import numpy as np
import rasterio
from gymnasium import spaces


ROOT = Path(__file__).resolve().parents[2]
SIMFIRE_ROOT = ROOT / "external/simfire"
SIMFIRE_COMMIT = "04905b19fe8c10dc08d64faddd00303e0561bb66"
COHORT_MANIFEST = ROOT / "data/manifests/simfire-fpa-fod-cohort-v2.json"
FUEL_CODES = (
    tuple(range(1, 14))
    + (0, 91, 92, 93, 98, 99, -32768, -9999, 32767)
)
FUEL_CHANNELS = {code: index for index, code in enumerate(FUEL_CODES)}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve_input_path(reference: str, manifest_path: Path) -> Path:
    path = Path(reference)
    if path.is_absolute():
        return path
    # Manifest paths are repository-relative; manifest parents are not.
    return ROOT / path


def _read_verified_raster(
    manifest: dict[str, Any], manifest_path: Path, input_key: str, shape: tuple[int, int]
) -> tuple[np.ndarray, Path]:
    row = manifest["inputs"][input_key]
    reference = row.get("path")
    expected_hash = row.get("sha256")
    if not reference or not expected_hash:
        raise ValueError("{} input has no local path and SHA-256 in {}".format(input_key, manifest_path))
    path = _resolve_input_path(reference, manifest_path)
    if not path.is_file():
        raise FileNotFoundError("Missing {} input: {}".format(input_key, path))
    actual_hash = _sha256(path)
    if actual_hash != expected_hash:
        raise ValueError("{} raster hash mismatch: {}".format(input_key, path))
    grid = manifest["grid"]
    bounds = [float(value) for value in grid["projected_bounds_m"]]
    with rasterio.open(path) as dataset:
        if dataset.crs is None or dataset.crs.to_string() != grid["crs"]:
            raise ValueError("{} raster CRS does not match {}".format(input_key, grid["crs"]))
        if (dataset.height, dataset.width) != shape or dataset.count != 1:
            raise ValueError("{} raster must have one {}x{} band".format(input_key, *shape))
        actual_bounds = [dataset.bounds.left, dataset.bounds.bottom, dataset.bounds.right, dataset.bounds.top]
        if not np.allclose(actual_bounds, bounds, atol=0.01):
            raise ValueError("{} raster bounds do not match its scenario manifest".format(input_key))
        values = dataset.read(1)
        if dataset.nodata is not None and np.any(values == dataset.nodata):
            raise ValueError("{} raster contains NoData cells".format(input_key))
        if not np.isfinite(values).all():
            raise ValueError("{} raster contains non-finite cells".format(input_key))
    return values, path


def _load_case(case_row: dict[str, Any], *, require_weather_mapping: bool = False) -> dict[str, Any]:
    manifest_path = ROOT / case_row["scenario_manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    shape = (int(manifest["grid"]["rows"]), int(manifest["grid"]["columns"]))
    fuel, fuel_path = _read_verified_raster(manifest, manifest_path, "fuel", shape)
    terrain, terrain_path = _read_verified_raster(manifest, manifest_path, "terrain", shape)
    unmapped = sorted(set(int(value) for value in np.unique(fuel)) - set(FUEL_CHANNELS))
    if unmapped:
        raise ValueError("Unrecognized FBFM13 codes in {}: {}".format(manifest["scenario_id"], unmapped))
    result = {
        "manifest": manifest,
        "manifest_path": manifest_path,
        "fuel": fuel,
        "terrain": terrain,
        "fuel_path": fuel_path,
        "terrain_path": terrain_path,
        "shape": shape,
    }
    if require_weather_mapping:
        mapping = manifest["fire_behavior"].get("weather_mapping")
        if not mapping or mapping.get("status") != "approximate_proxy":
            raise ValueError("{} has no explicit gridMET-to-SimFire weather proxy".format(manifest["scenario_id"]))
        mapping_path = _resolve_input_path(mapping["path"], manifest_path)
        if not mapping_path.is_file():
            raise FileNotFoundError("Missing mapped weather input: {}".format(mapping_path))
        if _sha256(mapping_path) != mapping.get("sha256"):
            raise ValueError("mapped weather checksum mismatch: {}".format(mapping_path))
        mapped_weather = json.loads(mapping_path.read_text(encoding="utf-8"))
        if mapped_weather.get("scenario_id") != manifest["scenario_id"]:
            raise ValueError("mapped weather scenario ID mismatch: {}".format(mapping_path))
        if mapped_weather.get("weather_source_sha256") != manifest["inputs"]["weather"].get("sha256"):
            raise ValueError("mapped weather does not cite the current source weather hash: {}".format(mapping_path))
        result["weather_mapping"] = mapped_weather
        result["weather_mapping_path"] = mapping_path
    return result


class SimFireCaseEnv(gym.Env):
    """Budgeted, single-cell fireline actions over the real incident cohort.

    Action 0 is always no-op. Other actions place one SimFire fireline point on a
    currently unburned, burnable 30 m cell. A point costs one budget unit. The action
    can be placed anywhere on the map, with no crew travel or line-construction delay;
    that is an explicit simplification of this first adapter.
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        split: str = "train",
        *,
        cohort_manifest: Path = COHORT_MANIFEST,
        fireline_budget: int = 32,
        decision_minutes: int = 30,
        horizon_decisions: int = 24,
        max_fire_duration_updates: int = 15,
        demo_wind_speed: float = 7.0,
        demo_wind_direction_deg: float = 90.0,
        demo_fuel_moisture: float = 0.03,
        weather_mode: str = "demonstration_only",
        weather_wind_adjustment_factor: float | None = None,
    ) -> None:
        super().__init__()
        if split not in {"train", "validation", "test"}:
            raise ValueError("split must be train, validation, or test")
        if fireline_budget < 0 or decision_minutes < 1 or horizon_decisions < 1:
            raise ValueError("budget must be nonnegative; time step and horizon must be positive")
        if max_fire_duration_updates < 1:
            raise ValueError("max_fire_duration_updates must be positive")
        if weather_mode not in {"demonstration_only", "gridmet_daily_proxy"}:
            raise ValueError("weather_mode must be demonstration_only or gridmet_daily_proxy")
        if weather_wind_adjustment_factor is not None and not 0.1 <= weather_wind_adjustment_factor <= 0.5:
            raise ValueError("weather_wind_adjustment_factor must be between 0.1 and 0.5")
        if not SIMFIRE_ROOT.is_dir():
            raise FileNotFoundError("Pinned SimFire source is missing: {}".format(SIMFIRE_ROOT))
        cohort = json.loads(cohort_manifest.read_text(encoding="utf-8"))
        selected = [row for row in cohort["cases"] if row["split"] == split]
        if not selected:
            raise ValueError("Cohort has no cases in split {!r}".format(split))
        self.cohort_id = cohort["cohort_id"]
        self.split = split
        self.case_rows = selected
        self.cases = [
            _load_case(row, require_weather_mapping=weather_mode == "gridmet_daily_proxy")
            for row in selected
        ]
        self.case_by_id = {case["manifest"]["scenario_id"]: case for case in self.cases}
        self.fireline_budget = int(fireline_budget)
        self.decision_minutes = int(decision_minutes)
        self.horizon_decisions = int(horizon_decisions)
        self.max_fire_duration_updates = int(max_fire_duration_updates)
        self.demo_wind_speed = float(demo_wind_speed)
        self.demo_wind_direction_deg = float(demo_wind_direction_deg) % 360.0
        self.demo_fuel_moisture = float(demo_fuel_moisture)
        self.weather_mode = weather_mode
        self.weather_wind_adjustment_factor = weather_wind_adjustment_factor
        rows, columns = self.cases[0]["shape"]
        if any(case["shape"] != (rows, columns) for case in self.cases):
            raise ValueError("All selected cases must share a common raster shape")
        self.rows, self.columns = rows, columns
        self.action_space = spaces.Discrete(rows * columns + 1)
        self.observation_space = spaces.Dict({
            "map": spaces.Box(0.0, 1.0, shape=(len(FUEL_CODES) + 2, rows, columns), dtype=np.float32),
            "state": spaces.Box(0.0, 1.0, shape=(7,), dtype=np.float32),
        })
        self._case: dict[str, Any] | None = None
        self.active_wind_speed_mph = self.demo_wind_speed
        self.active_wind_direction_deg = self.demo_wind_direction_deg
        self.active_fuel_moisture = self.demo_fuel_moisture
        self.active_weather_info: dict[str, Any] = {}
        self.simulation = None
        self._done = True

    @property
    def scenario_ids(self) -> tuple[str, ...]:
        return tuple(case["manifest"]["scenario_id"] for case in self.cases)

    def _new_simulation(self, case: dict[str, Any], seed: int):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".local/cache"))
        os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".local/matplotlib"))
        (ROOT / ".local/cache").mkdir(parents=True, exist_ok=True)
        (ROOT / ".local/matplotlib").mkdir(parents=True, exist_ok=True)
        if str(SIMFIRE_ROOT) not in sys.path:
            sys.path.insert(0, str(SIMFIRE_ROOT))
        import yaml
        from simfire.sim.simulation import FireSimulation
        from simfire.utils.config import Config
        from simfire.utils.layers import OperationalFuelLayer, OperationalTopographyLayer

        random.seed(seed)
        np.random.seed(seed % (2 ** 32))
        manifest = case["manifest"]
        config_path = SIMFIRE_ROOT / "configs/functional_config.yml"
        config_dict = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        config_dict["area"]["screen_size"] = [self.rows, self.columns]
        # SimFire's pixel_scale is feet per cell; match this dataset's projected 30 m grid.
        resolution_m = float(manifest["grid"]["resolution_m"])
        config_dict["area"]["pixel_scale"] = resolution_m * 3.280839895
        config_dict["terrain"]["fuel"]["type"] = "functional"
        config_dict["terrain"]["topography"]["type"] = "functional"
        config_dict["simulation"]["headless"] = True
        config_dict["simulation"]["record"] = False
        config_dict["simulation"]["save_data"] = False
        config_dict["simulation"]["sf_home"] = str(ROOT / ".local/simfire-agent-runs")
        config_dict["simulation"]["runtime"] = "24h"
        # SimFire's stock value is four one-minute updates. At this project's
        # 30 m cells, that can extinguish a spreading pixel before its
        # accumulated Rothermel ROS reaches the next cell. Keep this explicit
        # and long enough for slower, data-driven spread rates to cross a cell.
        config_dict["fire"]["max_fire_duration"] = self.max_fire_duration_updates
        config_dict["wind"]["function"] = "simple"
        config_dict["wind"]["simple"]["speed"] = self.active_wind_speed_mph
        config_dict["wind"]["simple"]["direction"] = self.active_wind_direction_deg
        config_dict["environment"]["moisture"] = self.active_fuel_moisture
        seed_row, seed_column = [int(value) for value in manifest["fire_behavior"]["seed_cell"]]
        config_dict["fire"]["fire_initial_position"]["static"]["position"] = [seed_column, seed_row]
        config = Config(config_dict=config_dict)
        source_layers = SimpleNamespace(layers=["fuel"], fuel=case["fuel"], topography=case["terrain"])
        config.terrain.fuel_layer = OperationalFuelLayer(source_layers)
        config.terrain.topography_layer = OperationalTopographyLayer(source_layers)
        return FireSimulation(config)

    def _burnable_mask(self) -> np.ndarray:
        assert self._case is not None
        cached = self._case.get("burnable_mask")
        if cached is not None:
            return cached
        from simfire.enums import FuelModelToFuel

        burnable_codes = [int(code) for code, fuel in FuelModelToFuel.items() if fuel.w_0 > 0.0]
        cached = np.isin(self._case["fuel"], burnable_codes)
        self._case["burnable_mask"] = cached
        return cached

    def _observation(self) -> dict[str, np.ndarray]:
        assert self._case is not None and self.simulation is not None
        observation_map = np.zeros((len(FUEL_CODES) + 2, self.rows, self.columns), dtype=np.float32)
        for code, channel in FUEL_CHANNELS.items():
            observation_map[channel] = self._case["fuel"] == code
        elevation = self._case["terrain"].astype(np.float32)
        # Use a fixed metre scale across scenarios, not per-map min/max scaling.
        observation_map[len(FUEL_CODES)] = np.clip(elevation / 5000.0, 0.0, 1.0)
        fire_map = np.asarray(self.simulation.fire_map, dtype=np.float32)
        observation_map[len(FUEL_CODES) + 1] = np.clip(fire_map, 0.0, 5.0) / 5.0
        observation_map = np.ascontiguousarray(observation_map)
        observation_state = np.asarray([
            self.remaining_budget / max(1, self.fireline_budget),
            self.steps / self.horizon_decisions,
            np.clip(self.active_wind_speed_mph / 30.0, 0.0, 1.0),
            (np.sin(np.deg2rad(self.active_wind_direction_deg)) + 1.0) / 2.0,
            (np.cos(np.deg2rad(self.active_wind_direction_deg)) + 1.0) / 2.0,
            np.clip(self.active_fuel_moisture / 0.3, 0.0, 1.0),
            1.0 if self.weather_mode == "demonstration_only" else 0.0,
        ], dtype=np.float32)
        return {"map": observation_map, "state": observation_state}

    def action_masks(self) -> np.ndarray:
        """Return a MaskablePPO-compatible mask; action zero is always available."""
        mask = np.zeros(self.action_space.n, dtype=bool)
        mask[0] = True
        if self._done or self.remaining_budget <= 0 or self.simulation is None:
            return mask
        burnable = self._burnable_mask()
        unburned = np.asarray(self.simulation.fire_map) == 0
        eligible = (burnable & unburned).reshape(-1)
        mask[1:] = eligible
        return mask

    def _info(self, *, delta_burned_cells: int = 0, placed_fireline: bool = False) -> dict[str, Any]:
        assert self._case is not None and self.simulation is not None
        fuel_codes = self._case["fuel"]
        burnable_cells = int(np.count_nonzero(self._burnable_mask()))
        return {
            "scenario_id": self._case["manifest"]["scenario_id"],
            "split": self.split,
            "cohort_id": self.cohort_id,
            "simfire_commit": SIMFIRE_COMMIT,
            "weather_mode": self.weather_mode,
            "historical_weather_context_used": self.weather_mode == "gridmet_daily_proxy",
            "weather_mapping_version": self.active_weather_info.get("mapping_version"),
            "weather_mapping_sha256": self._case["manifest"]["fire_behavior"].get("weather_mapping", {}).get("sha256"),
            "weather_source_sha256": self._case["manifest"]["inputs"]["weather"].get("sha256"),
            "weather_proxy_parameters": {
                "wind_speed_midflame_mph_proxy": self.active_wind_speed_mph,
                "wind_direction_degrees_clockwise_north_to": self.active_wind_direction_deg,
                "fuel_moisture_fraction_proxy": self.active_fuel_moisture,
                "wind_adjustment_factor": self.active_weather_info.get("derived_values", {}).get("wind_adjustment_factor"),
            } if self.weather_mode == "gridmet_daily_proxy" else None,
            "fuel_source_release": self._case["manifest"]["inputs"]["fuel"].get("source_release"),
            "grid_resolution_m": self._case["manifest"]["grid"]["resolution_m"],
            "simfire_pixel_scale_ft": float(self._case["manifest"]["grid"]["resolution_m"]) * 3.280839895,
            "fuel_codes_present": sorted(int(value) for value in np.unique(fuel_codes)),
            "burnable_cells": burnable_cells,
            "delta_burned_cells": int(delta_burned_cells),
            "cumulative_burned_cells": int(np.count_nonzero(self.ever_burned)),
            "cumulative_burned_area_ha": float(np.count_nonzero(self.ever_burned) *
                                                 float(self._case["manifest"]["grid"]["resolution_m"]) ** 2 / 10000.0),
            "placed_fireline": bool(placed_fireline),
            "fireline_budget_initial": self.fireline_budget,
            "fireline_budget_remaining": self.remaining_budget,
            "fireline_points_used": self.fireline_budget - self.remaining_budget,
            "decision": self.steps,
            "horizon_decisions": self.horizon_decisions,
            "decision_minutes": self.decision_minutes,
            "max_fire_duration_updates": self.max_fire_duration_updates,
            "max_fire_duration_minutes": self.max_fire_duration_updates * int(
                self.simulation.config.simulation.update_rate
            ),
            "simulated_minutes": int(getattr(self.simulation.fire_manager, "elapsed_time", 0)),
            "fuel_sha256": self._case["manifest"]["inputs"]["fuel"].get("sha256"),
            "terrain_sha256": self._case["manifest"]["inputs"]["terrain"].get("sha256"),
        }

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        options = options or {}
        scenario_id = options.get("scenario_id")
        if scenario_id is not None:
            try:
                self._case = self.case_by_id[str(scenario_id)]
            except KeyError as exc:
                raise ValueError("Scenario {} is not in the {} split".format(scenario_id, self.split)) from exc
        else:
            self._case = self.cases[int(self.np_random.integers(0, len(self.cases)))]
        if self.weather_mode == "gridmet_daily_proxy":
            mapping = self._case["weather_mapping"]
            parameters = mapping["simfire_parameters"]
            derived = mapping["derived_values"]
            factor = self.weather_wind_adjustment_factor
            if factor is None:
                factor = float(derived["wind_adjustment_factor"])
            self.active_wind_speed_mph = float(
                derived["wind_speed_assumed_20ft_reference_mph"]
            ) * factor
            self.active_wind_direction_deg = float(
                parameters["wind_direction_degrees_clockwise_north_to"]
            )
            self.active_fuel_moisture = float(parameters["fuel_moisture_fraction_proxy"])
            self.active_weather_info = deepcopy(mapping)
            self.active_weather_info.setdefault("derived_values", {})["wind_adjustment_factor"] = factor
        else:
            self.active_wind_speed_mph = self.demo_wind_speed
            self.active_wind_direction_deg = self.demo_wind_direction_deg
            self.active_fuel_moisture = self.demo_fuel_moisture
            self.active_weather_info = {}
        episode_seed = int(self.np_random.integers(0, 2 ** 32 - 1))
        self.simulation = self._new_simulation(self._case, episode_seed)
        self.remaining_budget = self.fireline_budget
        self.steps = 0
        self.ever_burned = np.isin(np.asarray(self.simulation.fire_map), [1, 2])
        self._done = False
        return self._observation(), self._info()

    def step(self, action: int):
        if self._done or self.simulation is None:
            raise RuntimeError("episode is finished; call reset() before step()")
        if not self.action_space.contains(action):
            raise ValueError("action must be an integer in the declared discrete action space")
        action = int(action)
        mask = self.action_masks()
        if not mask[action]:
            raise ValueError("masked action {}; use action_masks() before selecting a fireline cell".format(action))
        placed_fireline = action != 0
        if placed_fireline:
            cell_index = action - 1
            row, column = divmod(cell_index, self.columns)
            from simfire.enums import BurnStatus

            self.simulation.update_mitigation([(column, row, BurnStatus.FIRELINE)])
            self.remaining_budget -= 1
        previous_count = int(np.count_nonzero(self.ever_burned))
        _, active = self.simulation.run("{}m".format(self.decision_minutes))
        current = np.isin(np.asarray(self.simulation.fire_map), [1, 2])
        self.ever_burned |= current
        self.steps += 1
        delta_burned_cells = int(np.count_nonzero(self.ever_burned)) - previous_count
        burnable_cells = max(1, int(np.count_nonzero(self._burnable_mask())))
        reward = -float(delta_burned_cells) / float(burnable_cells)
        terminated = not bool(active)
        truncated = self.steps >= self.horizon_decisions and not terminated
        self._done = terminated or truncated
        return self._observation(), reward, terminated, truncated, self._info(
            delta_burned_cells=delta_burned_cells, placed_fireline=placed_fireline
        )
