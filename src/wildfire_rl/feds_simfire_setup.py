"""Shared, split-guarded construction of one FEDS/LANDFIRE SimFire episode.

The no-op runner, the budgeted Gymnasium environment and the paired benchmark all
build the same simulator state from the same verified inputs through this module.
TEST cases are never accepted. VALIDATION cases are accepted only when the caller
asks for them explicitly, after TRAIN parameters have been frozen.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import random
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from .gridmet_weather import gridmet_proxy_to_simfire
from .simfire_initial_state import compose_initial_fire_map, update_cumulative_burned
from .simfire_timebase import updates_for_duration


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data/manifests/feds-episode-cohort-v1.json"
WEATHER = ROOT / ".local/gridmet/feds-episode-weather-v1.json"
INPUT_ROOT = ROOT / ".local/feds-simfire-cases"
CONFIG_TEMPLATE = ROOT / "configs/simfire_feds_base.yml"
ALLOWED_SPLITS = ("train", "validation")
CELL_SIZE_M = 180.0
FEET_PER_METER = 3.280839895
SIMFIRE_COMMIT = "04905b19fe8c10dc08d64faddd00303e0561bb66"


@dataclass(frozen=True)
class SimFireParams:
    """Shared simulator settings; one set applies to every case of a run."""

    wind_adjustment_factor: float
    internal_update_minutes: int = 5
    active_cell_lifetime_minutes: int = 90
    ros_multiplier: float = 1.0

    def __post_init__(self) -> None:
        import math

        if not math.isfinite(self.wind_adjustment_factor) or not 0.0 <= self.wind_adjustment_factor <= 1.0:
            raise ValueError("wind adjustment factor must be in [0, 1]")
        if self.internal_update_minutes not in (1, 3, 5, 10, 15):
            raise ValueError("internal update interval must be 1, 3, 5, 10, or 15 minutes")
        if type(self.active_cell_lifetime_minutes) is not int or self.active_cell_lifetime_minutes <= 0:
            raise ValueError("active-cell lifetime must be a positive integer number of minutes")
        if not math.isfinite(self.ros_multiplier) or not 0.0 < self.ros_multiplier <= 10.0:
            raise ValueError("rate-of-spread multiplier must be in (0, 10]")

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_split_cases(split: str, manifest_path: Path = MANIFEST) -> Dict[str, dict]:
    """Return manifest cases for one allowed split, refusing any TEST content."""
    if split not in ALLOWED_SPLITS:
        raise ValueError("Only TRAIN or VALIDATION cases can be loaded; TEST stays closed.")
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("test_cases_loaded") is not False:
        raise ValueError("Refusing an episode manifest that includes TEST cases")
    cases = {case["scenario_id"]: case for case in manifest["cases"] if case.get("split") == split}
    if not cases:
        raise ValueError("The FEDS manifest has no %s episodes" % split.upper())
    return cases


def load_weather_records(
    split: str,
    *,
    manifest_path: Path = MANIFEST,
    weather_path: Path = WEATHER,
) -> Dict[str, dict]:
    if split not in ALLOWED_SPLITS:
        raise ValueError("Only TRAIN or VALIDATION weather can be loaded; TEST stays closed.")
    weather = json.loads(Path(weather_path).read_text(encoding="utf-8"))
    if weather.get("test_cases_loaded") is not False:
        raise ValueError("Refusing gridMET records that include TEST cases")
    if weather.get("episode_manifest_sha256") != sha256_file(manifest_path):
        raise ValueError("gridMET file was built from a different episode manifest")
    return {item["scenario_id"]: item for item in weather["cases"] if item.get("split") == split}


def load_case_inputs(
    scenario_id: str,
    *,
    split: str = "train",
    manifest_path: Path = MANIFEST,
    weather_path: Path = WEATHER,
    input_root: Path = INPUT_ROOT,
    cases: Optional[Dict[str, dict]] = None,
    weather_records: Optional[Dict[str, dict]] = None,
) -> Dict[str, Any]:
    """Load checksum-verified rasters, start masks and raw forcing for one case."""
    import numpy as np
    import rasterio

    cases = cases if cases is not None else load_split_cases(split, manifest_path)
    if scenario_id not in cases:
        raise ValueError("Scenario %s is not a manifest %s case" % (scenario_id, split.upper()))
    case = cases[scenario_id]
    records = weather_records if weather_records is not None else load_weather_records(
        split, manifest_path=manifest_path, weather_path=weather_path
    )
    weather = records.get(scenario_id)
    expected_time = case["evaluation_reference"]["initial_state_time"]
    if weather is None or weather.get("split") != split:
        raise ValueError("A unique %s gridMET record is required" % split.upper())
    if weather.get("initial_state_time") != expected_time or len(weather.get("segments", [])) != 4:
        raise ValueError("gridMET record must match the initial time and four 12h segments")

    case_dir = Path(input_root) / scenario_id
    receipt_path = case_dir / "input-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (receipt.get("scenario_id") != scenario_id or receipt.get("split") != split
            or receipt.get("test_cases_loaded") is not False
            or receipt.get("initial_state_time") != expected_time):
        raise ValueError("LANDFIRE/FEDS input receipt is not the requested %s start" % split.upper())
    paths = (
        (case_dir / receipt["fuel"]["file"], receipt["fuel"]["sha256"]),
        (case_dir / receipt["terrain"]["file"], receipt["terrain"]["sha256"]),
        (case_dir / receipt["initial_feds_state"]["mask_file"],
         receipt["initial_feds_state"]["mask_sha256"]),
    )
    for path, expected_hash in paths:
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise ValueError("Missing or changed verified simulator input: %s" % path)
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
    return {
        "scenario_id": scenario_id,
        "split": split,
        "case": case,
        "weather": weather,
        "receipt": receipt,
        "receipt_sha256": sha256_file(receipt_path),
        "fuel": fuel,
        "elevation": elevation,
        "scar": scar,
        "front": front,
    }


def forcing_segments(weather: dict, params: SimFireParams) -> List[Dict[str, float]]:
    forcing = []
    for segment in weather["segments"]:
        values = segment["gridmet_values"]
        forcing.append(gridmet_proxy_to_simfire(
            wind_speed_m_s=values["vs"]["value"],
            wind_from_degrees=values["th"]["value"],
            fm100_percent=values["fm100"]["value"],
            wind_adjustment_factor=params.wind_adjustment_factor,
        ))
    return forcing


def build_simulation(inputs: Dict[str, Any], params: SimFireParams, *, seed: int = 0):
    """Construct a FireSimulation holding the observed multi-cell FEDS start state.

    Returns ``(simulation, forcing, cumulative_burned)``. ``ros_multiplier`` scales
    SimFire's per-cell ignition threshold after the slope grid has been computed,
    which is equivalent to scaling every Rothermel rate of spread by that factor.
    """
    import os

    import numpy as np
    import yaml

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".local/mpl-cache"))
    os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".local/cache"))
    (ROOT / ".local/mpl-cache").mkdir(parents=True, exist_ok=True)
    (ROOT / ".local/cache").mkdir(parents=True, exist_ok=True)

    from simfire.enums import FuelModelRGB13, FuelModelToFuel
    from simfire.game.sprites import Fire
    from simfire.sim.simulation import FireSimulation
    from simfire.utils.config import Config
    from simfire.utils.layers import OperationalFuelLayer, OperationalTopographyLayer

    fuel = inputs["fuel"]
    scar = inputs["scar"]
    front = inputs["front"]
    codes = set(int(value) for value in np.unique(fuel))
    unsupported = sorted((codes - set(FuelModelToFuel)) | (codes - set(FuelModelRGB13)))
    if unsupported:
        raise ValueError("Pinned SimFire cannot map LANDFIRE fuel codes: %s" % unsupported)

    forcing = forcing_segments(inputs["weather"], params)
    base_config = yaml.safe_load(CONFIG_TEMPLATE.read_text(encoding="utf-8"))
    base_config["simulation"]["update_rate"] = params.internal_update_minutes
    base_config["fire"]["max_fire_duration"] = updates_for_duration(
        params.active_cell_lifetime_minutes, params.internal_update_minutes
    )
    rows, columns = fuel.shape
    front_rows, front_columns = np.where(front)
    base_config["fire"]["fire_initial_position"]["static"]["position"] = [
        int(front_columns[0]), int(front_rows[0])
    ]
    config = Config(config_dict=base_config)
    config.area.screen_size = (rows, columns)
    pixel_scale_ft = CELL_SIZE_M * FEET_PER_METER
    config.area.pixel_scale = pixel_scale_ft
    layers = SimpleNamespace(layers=["fuel"], fuel=fuel, topography=inputs["elevation"])
    config.terrain.fuel_layer = OperationalFuelLayer(layers)
    config.terrain.topography_layer = OperationalTopographyLayer(layers)
    config.wind.speed = np.full(
        (rows, columns), forcing[0]["wind_speed_midflame_ft_per_min_proxy"], dtype=np.float64
    )
    config.wind.direction = np.full(
        (rows, columns), forcing[0]["wind_direction_degrees_clockwise_north_to"], dtype=np.float64
    )
    config.environment.moisture = forcing[0]["fuel_moisture_fraction_proxy"]

    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    simulation = FireSimulation(config)
    if params.ros_multiplier != 1.0:
        simulation.fire_manager.pixel_scale = pixel_scale_ft / params.ros_multiplier
    simulation.fire_map = compose_initial_fire_map(scar, front).astype(np.int64)
    simulation.fire_manager.sprites = [
        Fire((int(column), int(row)), config.display.fire_size, headless=True)
        for row, column in zip(front_rows, front_columns)
    ]
    simulation.fire_manager.durations = [0] * len(simulation.fire_manager.sprites)
    simulation.fire_sprites = simulation.fire_manager.sprites
    cumulative = update_cumulative_burned(scar, simulation.fire_map)
    if not np.array_equal(cumulative, scar | front):
        raise AssertionError("The cumulative initial scar/front masks were not preserved.")
    return simulation, forcing, cumulative


def apply_forcing(simulation: Any, segment: Dict[str, float]) -> None:
    """Set one 12h forcing segment on a live simulation."""
    simulation.fire_manager.U[:] = segment["wind_speed_midflame_ft_per_min_proxy"]
    simulation.fire_manager.U_dir[:] = segment["wind_direction_degrees_clockwise_north_to"]
    simulation.fire_manager.environment.M_f = segment["fuel_moisture_fraction_proxy"]
