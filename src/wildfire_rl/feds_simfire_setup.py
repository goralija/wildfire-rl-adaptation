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
FREEZE_ALLOWLIST = ROOT / "configs/frozen/validation-freeze-allowlist.json"
ALLOWED_SPLITS = ("train", "validation")
# "per_minute" (ADR-030 default) subtracts 980 ft per simulated minute and floors line
# burn amounts at zero, so a line holds iff the effective rate of spread reaching it (after
# ros_multiplier) stays below 980 ft/min, at any internal step and however long the line
# has waited. ros_multiplier works through the ignition threshold (pixel_scale / m), so the
# attenuation is scaled by 1 / m in the same units. "per_update" is
# pinned SimFire: a fixed 980 ft per update from R * update_rate (a line holds 980 ft/min
# at 1 min but only 196 at 5 min), with no floor, so an idle line banks negative burn.
FIRELINE_ATTENUATIONS = ("per_update", "per_minute")
# "last_write" is pinned SimFire: when several burning cells reach one target, the last
# sprite in list order sets its rate of spread. "max" uses the fastest approach instead,
# which does not depend on sprite order.
SPREAD_AGGREGATIONS = ("last_write", "max")
# ADR-030: "previous" (default) shows, at decision k, the latest gridMET daily record
# whose label is strictly earlier than segment k's label: the pre-start day for decision
# 0, otherwise the last earlier segment with an earlier day. Two 12h segments often share
# one daily record, so "the segment that just ran" can be the upcoming forcing and is
# not used. "upcoming_perfect_forecast" shows the ex-post forcing of the segment about to
# run and exists only as a labelled ablation.
WEATHER_OBSERVATIONS = ("previous", "upcoming_perfect_forecast")
WEATHER_REGENERATION_HINT = (
    "regenerate it with scripts/sample_gridmet_episode_weather.py (TASK-026 stage 1)"
)
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
    fireline_attenuation: str = "per_minute"
    spread_aggregation: str = "last_write"

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
        if self.fireline_attenuation not in FIRELINE_ATTENUATIONS:
            raise ValueError("fireline attenuation must be one of %s" % (FIRELINE_ATTENUATIONS,))
        if self.spread_aggregation not in SPREAD_AGGREGATIONS:
            raise ValueError("spread aggregation must be one of %s" % (SPREAD_AGGREGATIONS,))

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Exact rule behind each observation mode. "previous" changed meaning in TASK-023, so a
# receipt must state the rule, not only the mode name.
WEATHER_OBSERVATION_RULES = {
    "previous": "latest_daily_record_strictly_before_upcoming_segment_with_pre_start/v1",
    "upcoming_perfect_forecast": "upcoming_segment_forcing_perfect_forecast_ablation/v1",
}
# Settings a trained policy depends on; a training receipt states them and a benchmark
# refuses a checkpoint whose receipt differs (scripts/benchmark_feds_policies.py).
POLICY_SETTING_KEYS = (
    "weather_observation",
    "weather_observation_rule",
    "sim_params",
    "fireline_attenuation",
    "line_banking_floor",
    "line_placement",
    "observation_max_budget",
)


def line_banking_floor(params: "SimFireParams") -> str:
    """Whether line burn amounts are floored at zero (ADR-030 wrapper) or bank freely."""
    return "zero" if params.fireline_attenuation == "per_minute" else "none_pinned_simfire"


def policy_settings(params: "SimFireParams", *, weather_observation: str, line_placement: str,
                    observation_max_budget: int) -> Dict[str, Any]:
    """The receipt fields that bind a PPO checkpoint to its environment settings."""
    if weather_observation not in WEATHER_OBSERVATIONS:
        raise ValueError("weather observation must be one of %s" % (WEATHER_OBSERVATIONS,))
    return {
        "weather_observation": weather_observation,
        "weather_observation_rule": WEATHER_OBSERVATION_RULES[weather_observation],
        "sim_params": params.as_dict(),
        "fireline_attenuation": params.fireline_attenuation,
        "line_banking_floor": line_banking_floor(params),
        "line_placement": line_placement,
        "observation_max_budget": int(observation_max_budget),
    }


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


def require_validation_freeze(
    params: SimFireParams,
    freeze_record: Optional[Path],
    *,
    weather_path: Path = WEATHER,
    allowlist_path: Path = FREEZE_ALLOWLIST,
) -> str:
    """Accept VALIDATION only under a committed, allowlisted TRAIN freeze record.

    The record's sha256 must appear in the committed allowlist, it must have been
    selected on TRAIN, its ``frozen_params`` must state every simulator field and equal
    ``params`` (so a record cannot inherit a default it was not selected with) and it
    must name the gridMET file in use. Returns the hash.
    """
    if freeze_record is None:
        raise ValueError("VALIDATION requires a committed TRAIN freeze record.")
    digest = sha256_file(Path(freeze_record))
    allowlist = json.loads(Path(allowlist_path).read_text(encoding="utf-8"))
    if digest not in {item["sha256"] for item in allowlist.get("records", [])}:
        raise ValueError("Freeze record %s (sha256 %s) is not in the committed allowlist %s"
                         % (freeze_record, digest, allowlist_path))
    record = json.loads(Path(freeze_record).read_text(encoding="utf-8"))
    if record.get("selected_on_split") != "train":
        raise ValueError("VALIDATION requires parameters selected on TRAIN.")
    frozen = record.get("frozen_params", {})
    if set(frozen) != set(SimFireParams.__dataclass_fields__):
        raise ValueError("The freeze record must state every simulator field: %s"
                         % sorted(SimFireParams.__dataclass_fields__))
    if SimFireParams(**frozen) != params:
        raise ValueError("Simulator parameters do not match the TRAIN freeze record.")
    if record.get("weather_sha256") != sha256_file(Path(weather_path)):
        raise ValueError("The freeze record was not selected with this gridMET file.")
    return digest


def check_split_access(
    split: str,
    params: SimFireParams,
    freeze_record: Optional[Path] = None,
    *,
    weather_path: Path = WEATHER,
    allowlist_path: Path = FREEZE_ALLOWLIST,
) -> Optional[str]:
    """Refuse TEST always, VALIDATION without a matching freeze; return its hash."""
    if split not in ALLOWED_SPLITS:
        raise ValueError("Only TRAIN or VALIDATION cases can be loaded; TEST stays closed.")
    if split == "validation":
        return require_validation_freeze(
            params, freeze_record, weather_path=weather_path, allowlist_path=allowlist_path
        )
    return None


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


def record_forcing(record: dict, params: SimFireParams) -> Dict[str, float]:
    """SimFire proxy values for one daily gridMET record (segment or pre-start)."""
    values = record["gridmet_values"]
    return gridmet_proxy_to_simfire(
        wind_speed_m_s=values["vs"]["value"],
        wind_from_degrees=values["th"]["value"],
        fm100_percent=values["fm100"]["value"],
        wind_adjustment_factor=params.wind_adjustment_factor,
    )


def forcing_segments(weather: dict, params: SimFireParams) -> List[Dict[str, float]]:
    """Simulator forcing of the four 12h segments; the pre-start record is never forcing."""
    return [record_forcing(segment, params) for segment in weather["segments"]]


def _has_pre_start(weather: dict) -> bool:
    pre_start = weather.get("pre_start")
    segments = weather.get("segments") or []
    return (isinstance(pre_start, dict) and bool(segments)
            and set(pre_start.get("gridmet_values", {})) >= {"th", "vs", "fm100"}
            and str(pre_start.get("gridmet_daily_label_mst", "9999"))
            < str(segments[0].get("gridmet_daily_label_mst", "")))


def require_pre_start_weather(records: Dict[str, dict], weather_path: Path = WEATHER) -> None:
    """Refuse gridMET files that predate the ADR-030 pre-start observation record."""
    missing = sorted(key for key, record in records.items() if not _has_pre_start(record))
    if missing:
        raise ValueError(
            "gridMET file %s has no valid pre_start observation record for %d case(s) (first: %s); "
            "it predates the ADR-030 observation rule. Stage 1 regeneration is needed: %s."
            % (weather_path, len(missing), missing[0], WEATHER_REGENERATION_HINT)
        )


def observed_weather_records(weather: dict, mode: str = "previous") -> List[dict]:
    """The daily gridMET record each of the four decisions observes (ADR-030).

    ``"previous"``: at decision k, the latest record among the pre-start day and the
    segments before k whose label is strictly earlier than segment k's label, so the
    upcoming segment's forcing is never observed, even when two segments share a day.
    ``"upcoming_perfect_forecast"``: segment k itself (labelled ablation only).
    """
    if mode not in WEATHER_OBSERVATIONS:
        raise ValueError("weather observation must be one of %s" % (WEATHER_OBSERVATIONS,))
    segments = list(weather["segments"])
    if mode == "upcoming_perfect_forecast":
        return segments
    if not _has_pre_start(weather):
        raise ValueError("gridMET record has no valid pre_start observation record; Stage 1 "
                         "regeneration is needed: %s." % WEATHER_REGENERATION_HINT)
    candidates = [weather["pre_start"], *segments]
    observed = []
    for decision, segment in enumerate(segments):
        label = segment["gridmet_daily_label_mst"]
        earlier = [record for record in candidates[:decision + 1]
                   if record["gridmet_daily_label_mst"] < label]
        observed.append(earlier[-1])
    return observed


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
    front_rows, front_columns = np.where(front)
    base_config["fire"]["fire_initial_position"]["static"]["position"] = [
        int(front_columns[0]), int(front_rows[0])
    ]
    # SimFire draws from the global ``random``/``np.random`` streams while it builds,
    # so they are seeded for a reproducible build and then restored: an episode reset
    # must not rewind the streams other code (e.g. SB3 minibatch shuffling) relies on.
    saved_random_state = random.getstate()
    saved_numpy_state = np.random.get_state()
    try:
        simulation = _construct_simulation(base_config, inputs, forcing, seed)
    finally:
        random.setstate(saved_random_state)
        np.random.set_state(saved_numpy_state)
    pixel_scale_ft = CELL_SIZE_M * FEET_PER_METER
    if params.ros_multiplier != 1.0:
        simulation.fire_manager.pixel_scale = pixel_scale_ft / params.ros_multiplier
    simulation.fire_map = compose_initial_fire_map(scar, front).astype(np.int64)
    install_spread_options(simulation.fire_manager, params)
    simulation.fire_manager.sprites = [
        Fire((int(column), int(row)), simulation.config.display.fire_size, headless=True)
        for row, column in zip(front_rows, front_columns)
    ]
    simulation.fire_manager.durations = [0] * len(simulation.fire_manager.sprites)
    simulation.fire_sprites = simulation.fire_manager.sprites
    cumulative = update_cumulative_burned(scar, simulation.fire_map)
    if not np.array_equal(cumulative, scar | front):
        raise AssertionError("The cumulative initial scar/front masks were not preserved.")
    return simulation, forcing, cumulative


def _construct_simulation(base_config: dict, inputs: Dict[str, Any], forcing: List[Dict[str, float]],
                          seed: int) -> Any:
    import numpy as np

    from simfire.sim.simulation import FireSimulation
    from simfire.utils.config import Config
    from simfire.utils.layers import OperationalFuelLayer, OperationalTopographyLayer

    fuel = inputs["fuel"]
    rows, columns = fuel.shape
    config = Config(config_dict=base_config)
    config.area.screen_size = (rows, columns)
    config.area.pixel_scale = CELL_SIZE_M * FEET_PER_METER
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
    return FireSimulation(config)


def apply_forcing(simulation: Any, segment: Dict[str, float]) -> None:
    """Set one 12h forcing segment on a live simulation."""
    simulation.fire_manager.U[:] = segment["wind_speed_midflame_ft_per_min_proxy"]
    simulation.fire_manager.U_dir[:] = segment["wind_direction_degrees_clockwise_north_to"]
    simulation.fire_manager.environment.M_f = segment["fuel_moisture_fraction_proxy"]


def _per_minute_line_attenuation(fire_manager: Any, rate_of_spread: Any, fire_map: Any) -> Any:
    """SimFire's control-line attenuation, scaled by the internal update length, with
    line burn amounts floored at zero.

    Pinned SimFire subtracts the attenuation from every line cell on every update, even
    with no fire next to it, so an idle line "banks" a large negative burn amount and
    becomes a near-absolute barrier. Here the returned increment never takes a line
    cell's burn amount below zero, so an idle line stays at zero and a line cell ignites
    iff the rate of spread reaching it exceeds the attenuation (980 ft/min for fireline)
    long enough to accumulate one cell width, independent of the internal step and of
    how long ago the line was placed.

    ``ros_multiplier`` m acts on the ignition threshold (``pixel_scale / m``), so burn
    amounts are in units inflated by 1 / m. The attenuation is scaled by the same 1 / m
    (``_line_attenuation_scale``), so a line holds up to an *effective* spread of 980 ft/min
    for every m, not 980 * m.
    """
    import numpy as np
    from simfire.enums import BurnStatus, RoSAttenuation

    if not fire_manager.attenuate_line_ros:
        return type(fire_manager)._update_rate_of_spread(fire_manager, rate_of_spread, fire_map)
    scale = fire_manager.update_rate * getattr(fire_manager, "_line_attenuation_scale", 1.0)
    factor = np.zeros_like(rate_of_spread)
    factor[fire_map == BurnStatus.FIRELINE] = RoSAttenuation.FIRELINE * scale
    factor[fire_map == BurnStatus.SCRATCHLINE] = RoSAttenuation.SCRATCHLINE * scale
    factor[fire_map == BurnStatus.WETLINE] = RoSAttenuation.WETLINE * scale
    increment = rate_of_spread - factor
    line = np.isin(fire_map, (BurnStatus.FIRELINE, BurnStatus.SCRATCHLINE, BurnStatus.WETLINE))
    increment[line] = np.maximum(increment[line], -fire_manager.burn_amounts[line])
    return increment


def _max_ros_update(fire_manager: Any, fire_map: Any) -> Any:
    """``RothermelFireManager.update`` of the pinned SimFire commit, except that each
    target cell takes the maximum rate of spread over its burning neighbours instead
    of the last one written in sprite order."""
    import numpy as np
    from simfire.enums import GameStatus
    from simfire.game.managers import fire as simfire_fire

    fire_manager._prune_sprites(fire_map)
    fire_manager.durations = [duration + 1 for duration in fire_manager.durations]
    if not fire_manager.sprites:
        return fire_map, GameStatus.QUIT
    if fire_manager.max_time is not None and (
            fire_manager.update_rate > fire_manager.max_time
            or fire_manager.elapsed_time > fire_manager.max_time):
        return fire_map, GameStatus.QUIT
    all_params = [fire_manager._accrue_sprites(index, fire_map)
                  for index in range(len(fire_manager.sprites))]
    all_params = [item for item in all_params if item is not None]
    if not all_params:
        return fire_map, GameStatus.RUNNING
    flat = fire_manager._flatten_params(all_params)
    rate = simfire_fire.compute_rate_of_spread(*flat) * fire_manager.update_rate
    x_coords = flat[2].astype(int)
    y_coords = flat[3].astype(int)
    fastest = np.full(fire_manager.burn_amounts.shape, -np.inf)
    np.maximum.at(fastest, (y_coords, x_coords), rate)
    rate_of_spread = np.zeros_like(fire_manager.burn_amounts)
    reached = np.isfinite(fastest)
    rate_of_spread[reached] = fastest[reached]
    fire_manager.rate_of_spread = fire_manager._update_rate_of_spread(rate_of_spread, fire_map)
    fire_manager.burn_amounts += fire_manager.rate_of_spread
    fire_map = fire_manager._update_with_new_locs(y_coords, x_coords, fire_map)
    fire_manager.elapsed_time += fire_manager.update_rate
    return fire_map, GameStatus.RUNNING


def install_spread_options(fire_manager: Any, params: SimFireParams) -> None:
    """Bind the non-default spread options to one fire manager instance.

    Both defaults leave the pinned SimFire behaviour untouched; nothing is patched at
    class or module level, so other simulations in the process are unaffected.
    """
    from types import MethodType

    if params.fireline_attenuation == "per_minute":
        fire_manager._line_attenuation_scale = 1.0 / params.ros_multiplier
        fire_manager._update_rate_of_spread = MethodType(_per_minute_line_attenuation, fire_manager)
    if params.spread_aggregation == "max":
        import importlib.metadata

        if importlib.metadata.version("simfire") != "2.0.1":
            raise RuntimeError("max spread aggregation mirrors SimFire 2.0.1 (%s)" % SIMFIRE_COMMIT)
        fire_manager.update = MethodType(_max_ros_update, fire_manager)
