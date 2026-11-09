"""Real FEDS/LANDFIRE/gridMET cases as episodes of the synthetic CA (ADR-028).

The manifest's FEDS cases (118 after ADR-030 §6: 98 ex-TRAIN, 20 ex-VALIDATION) supply
the landscape, the observed initial state and the historical forcing. Spread is computed by the synthetic
CA, so these episodes are the final test of locked policies and the input of the
calibration-gap diagnostic, never a training or tuning set. TEST cases are refused
before any file is opened.

File access, split guards and checksum verification are delegated to
``feds_simfire_setup``; this module only converts verified inputs.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.ndimage import distance_transform_edt

from .feds_simfire_setup import (
    ALLOWED_SPLITS,
    INPUT_ROOT,
    MANIFEST,
    WEATHER,
    load_case_inputs,
    load_split_cases,
    load_weather_records,
)
from .synthetic_ca import Landscape, SpreadParams, Weather, WeatherSeries
from .synthetic_env import DECISION_MINUTES, DOZER, HAND_CREW, TAIL_DECISIONS, EpisodeSpec


CROP = 128
HORIZON = 48
# Midflame/10 m wind ratio: the middle of the training curriculum's 0.1-0.5 range.
REAL_WIND_ADJUSTMENT = 0.3
VALID_FUEL_CODES = frozenset(list(range(1, 14)) + [91, 92, 93, 98, 99])
UNKNOWN_FUEL_CODE = 99  # nodata and unknown codes become barren (non-burnable)
# LANDFIRE elevation is in metres; anything below this is a nodata fill (-9999 seen).
ELEVATION_NODATA_BELOW = -1000.0
DEFAULT_UNITS: List[Tuple[int, float]] = [(DOZER, 30.0), (HAND_CREW, 60.0),
                                          (HAND_CREW, 90.0), (DOZER, 120.0)]


def _check_splits(splits: Sequence[str]) -> Tuple[str, ...]:
    splits = tuple(splits)
    if not splits or any(split not in ALLOWED_SPLITS for split in splits):
        raise ValueError("Only TRAIN or VALIDATION cases can be loaded; TEST stays closed.")
    return splits


def stable_case_seed(scenario_id: str) -> int:
    """Deterministic episode seed (SHA-256, not Python's per-process ``hash``)."""
    digest = hashlib.sha256(scenario_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % (2 ** 31)


def crop_window(mask: np.ndarray, size: int = CROP) -> Tuple[int, int]:
    """Top-left (row, col) of a ``size`` square centred on the mask centroid, kept inside."""
    mask = np.asarray(mask, dtype=bool)
    rows, cols = mask.shape
    if size > rows or size > cols:
        raise ValueError("crop is larger than the tile")
    cells = np.argwhere(mask)
    centre = cells.mean(axis=0) if len(cells) else np.array([(rows - 1) / 2, (cols - 1) / 2])
    # A window starting at r0 is centred on r0 + (size - 1) / 2.
    r0 = int(np.clip(np.round(centre[0] - (size - 1) / 2), 0, rows - size))
    c0 = int(np.clip(np.round(centre[1] - (size - 1) / 2), 0, cols - size))
    return r0, c0


def map_fuel_codes(fuel: np.ndarray) -> Tuple[np.ndarray, Dict[int, int]]:
    """Keep FBFM13 codes; send nodata/unknown codes to barren. Returns (codes, unknown counts)."""
    fuel = np.asarray(fuel)
    valid = np.isin(fuel, sorted(VALID_FUEL_CODES))
    codes, counts = np.unique(fuel[~valid], return_counts=True)
    mapped = np.where(valid, fuel, UNKNOWN_FUEL_CODE).astype(np.int16)
    return mapped, {int(code): int(count) for code, count in zip(codes, counts)}


def fill_elevation_nodata(elevation: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Replace nodata elevation with the nearest valid cell; return (filled, nodata mask)."""
    elevation = np.asarray(elevation, dtype=np.float64)
    bad = ~np.isfinite(elevation) | (elevation < ELEVATION_NODATA_BELOW)
    if not bad.any():
        return elevation.copy(), bad
    if bad.all():
        raise ValueError("elevation tile has no valid cells")
    _, (rows, cols) = distance_transform_edt(bad, return_indices=True)
    return elevation[rows, cols], bad


def parse_utc(value: str) -> datetime:
    """Zoned ISO time as aware UTC. A naive FEDS `t` is an overpass label, not UTC (TASK-027)."""
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None:
        raise ValueError("A zoned time is required; naive FEDS `t` is not a UTC instant: %r"
                         % value)
    return moment.astimezone(timezone.utc)


def episode_start_utc(weather_record: dict) -> datetime:
    """The episode start: segment 0's start, the FEDS start overpass in UTC."""
    return parse_utc(weather_record["segments"][0]["start_utc"])


def local_solar_hour(moment: datetime, longitude: float) -> float:
    """Mean local solar hour: UTC hour plus longitude / 15."""
    moment = moment.astimezone(timezone.utc)
    utc_hour = moment.hour + moment.minute / 60.0 + moment.second / 3600.0
    return float((utc_hour + longitude / 15.0) % 24.0)


def weather_from_segments(segments: Sequence[dict], start_utc: datetime, longitude: float,
                          decisions: int = HORIZON + TAIL_DECISIONS,
                          wind_adjustment: float = REAL_WIND_ADJUSTMENT) -> WeatherSeries:
    """One Weather per 60-min decision from gridMET 12h segments.

    A segment holds from its ``start_utc`` (inclusive) to ``end_utc`` (exclusive); after
    the last one its values are held. Only ``local_hour`` changes within a segment.
    """
    spans = []
    for segment in segments:
        values = segment["gridmet_values"]
        spans.append((parse_utc(segment["start_utc"]), parse_utc(segment["end_utc"]),
                      float(values["vs"]["value"]), float(values["th"]["value"]),
                      float(values["fm100"]["value"])))
    if not spans:
        raise ValueError("gridMET record has no segments")
    spans.sort(key=lambda span: span[0])
    if start_utc < spans[0][0]:
        raise ValueError("episode starts before the first gridMET segment")
    steps = []
    for index in range(decisions):
        moment = start_utc + timedelta(minutes=index * DECISION_MINUTES)
        chosen = spans[-1]
        for span in spans:
            if span[0] <= moment < span[1]:
                chosen = span
                break
        _, _, speed10, wind_from, fm100 = chosen
        steps.append(Weather(wind_midflame_m_s=wind_adjustment * speed10,
                             wind_to_deg=(wind_from + 180.0) % 360.0,
                             moisture=fm100 / 100.0,
                             local_hour=local_solar_hour(moment, longitude)))
    return WeatherSeries(steps)


def crop_centre_lonlat(grid: dict, r0: int, c0: int, size: int = CROP) -> Tuple[float, float]:
    """Longitude/latitude of the crop centre from the receipt's projected grid."""
    from pyproj import Transformer

    a, _, x0, _, e, y0 = grid["raster_transform"][:6]
    x = x0 + (c0 + size / 2.0) * a
    y = y0 + (r0 + size / 2.0) * e
    to_lonlat = Transformer.from_crs(grid["crs"], "EPSG:4326", always_xy=True)
    lon, lat = to_lonlat.transform(x, y)
    return float(lon), float(lat)


def build_real_episode(inputs: Dict[str, Any],
                       unit_protocol: Sequence[Tuple[int, float]] = DEFAULT_UNITS,
                       horizon: int = HORIZON,
                       ) -> Tuple[EpisodeSpec, Dict[str, Any]]:
    """Convert one verified ``load_case_inputs`` result into an EpisodeSpec and metadata."""
    split = inputs["split"]
    _check_splits((split,))
    scenario_id = inputs["scenario_id"]
    scar_tile, front_tile = inputs["scar"], inputs["front"]
    initial_tile = scar_tile | front_tile
    r0, c0 = crop_window(initial_tile)
    window = (slice(r0, r0 + CROP), slice(c0, c0 + CROP))

    fuel_tile, unknown_tile = map_fuel_codes(inputs["fuel"])
    _, unknown_crop = map_fuel_codes(inputs["fuel"][window])
    elevation_tile, elevation_bad = fill_elevation_nodata(inputs["elevation"])
    fuel = fuel_tile[window]
    landscape = Landscape(fuel=fuel, elevation=elevation_tile[window])
    scar = scar_tile[window].astype(bool)
    front = front_tile[window].astype(bool)

    # Local hour from the crop centre, not the FPA-FOD discovery point (evaluation-only).
    grid = inputs["receipt"]["grid"]
    longitude, latitude = crop_centre_lonlat(grid, r0, c0)
    # load_case_inputs has matched the record to initial_state_time.
    start = episode_start_utc(inputs["weather"])
    weather = weather_from_segments(inputs["weather"]["segments"], start, longitude,
                                    horizon + TAIL_DECISIONS)

    spec = EpisodeSpec(landscape=landscape, weather=weather, scar=scar, front=front,
                       units=[(int(kind), float(minute)) for kind, minute in unit_protocol],
                       horizon=int(horizon), seed=stable_case_seed(scenario_id),
                       params=SpreadParams(), name=scenario_id)
    codes, counts = np.unique(fuel, return_counts=True)
    out_of_crop = int(initial_tile.sum() - (scar | front).sum())
    metadata = {
        "scenario_id": scenario_id,
        "split": split,
        "crop_offset_row": r0,
        "crop_offset_col": c0,
        "crop_size": CROP,
        "fuel_code_histogram": {int(code): int(count) for code, count in zip(codes, counts)},
        "unknown_fuel_codes_crop": unknown_crop,
        "unknown_fuel_codes_tile": unknown_tile,
        "elevation_nodata_cells_tile": int(elevation_bad.sum()),
        "elevation_nodata_cells_crop": int(elevation_bad[window].sum()),
        "initial_burned_cells": int((scar | front).sum()),
        "initial_scar_cells": int(scar.sum()),
        "initial_front_cells": int(front.sum()),
        # Front cells the CA cannot ignite (non-burnable or remapped fuel).
        "front_on_nonburnable_cells": int((front & ~landscape.burnable).sum()),
        "initial_cells_outside_crop": out_of_crop,
        "initial_outside_crop_flag": bool(out_of_crop),
        "longitude": longitude,
        "latitude": latitude,
        "lonlat_source": "crop centre from receipt grid (not the FPA-FOD discovery point)",
        "start_time_utc": start.isoformat(),
        "wind_adjustment": REAL_WIND_ADJUSTMENT,
        "seed": spec.seed,
        "input_receipt_sha256": inputs["receipt_sha256"],
    }
    return spec, metadata


def load_real_episode_specs(splits: Sequence[str] = ("train", "validation"),
                            unit_protocol: Sequence[Tuple[int, float]] = DEFAULT_UNITS, *,
                            manifest_path: Path = MANIFEST, weather_path: Path = WEATHER,
                            input_root: Path = INPUT_ROOT,
                            scenario_ids: Optional[Sequence[str]] = None,
                            ) -> List[Tuple[EpisodeSpec, Dict[str, Any]]]:
    """Load verified real cases as ``(EpisodeSpec, metadata)``, in manifest order per split.

    ``scenario_ids`` restricts loading to the named cases (unknown names raise).
    """
    splits = _check_splits(splits)
    wanted = set(scenario_ids) if scenario_ids is not None else None
    found = set()
    episodes = []
    for split in splits:
        cases = load_split_cases(split, manifest_path)
        records = load_weather_records(split, manifest_path=manifest_path,
                                       weather_path=weather_path)
        for scenario_id in cases:
            if wanted is not None and scenario_id not in wanted:
                continue
            inputs = load_case_inputs(scenario_id, split=split, manifest_path=manifest_path,
                                      weather_path=weather_path, input_root=input_root,
                                      cases=cases, weather_records=records)
            episodes.append(build_real_episode(inputs, unit_protocol))
            found.add(scenario_id)
    if wanted is not None and wanted - found:
        raise ValueError("Not TRAIN/VALIDATION manifest cases: %s" % sorted(wanted - found))
    return episodes
