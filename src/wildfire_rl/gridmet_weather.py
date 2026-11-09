"""Small, explicit daily gridMET sampling and SimFire proxy conversions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
from typing import Any


GRIDMET_MST = timezone(timedelta(hours=-7), name="MST")
METERS_PER_SECOND_TO_FEET_PER_MINUTE = 196.8503937007874


def feds_timestamp_to_utc(value: str) -> datetime:
    """Parse FEDS timestamps, preserving the declared assumption that naive `t` is UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def gridmet_day_for_utc(value: datetime) -> str:
    """Map a UTC instant to the gridMET daily label using its fixed MST day boundary."""
    if value.tzinfo is None:
        raise ValueError("An aware UTC datetime is required.")
    return value.astimezone(GRIDMET_MST).date().isoformat()


def direction_from_to_simfire_direction(direction_from_degrees: float) -> float:
    """Convert meteorological wind-from azimuth to SimFire's downwind azimuth."""
    return (float(direction_from_degrees) + 180.0) % 360.0


def gridmet_proxy_to_simfire(
    *,
    wind_speed_m_s: float,
    wind_from_degrees: float,
    fm100_percent: float,
    wind_adjustment_factor: float,
) -> dict[str, float]:
    """Return transparent candidate inputs; caller must select factor on TRAIN only."""
    import math

    values = (wind_speed_m_s, wind_from_degrees, fm100_percent, wind_adjustment_factor)
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError("gridMET and wind-adjustment inputs must be finite numbers.")
    if wind_speed_m_s < 0 or not 0 <= fm100_percent <= 100:
        raise ValueError("gridMET wind speed must be nonnegative and fm100 must be 0..100 percent.")
    if not 0.0 <= wind_adjustment_factor <= 1.0:
        raise ValueError("wind_adjustment_factor must be in [0,1].")
    return {
        "wind_speed_midflame_ft_per_min_proxy": (
            float(wind_speed_m_s) * METERS_PER_SECOND_TO_FEET_PER_MINUTE
            * float(wind_adjustment_factor)
        ),
        "wind_direction_degrees_clockwise_north_to": direction_from_to_simfire_direction(
            wind_from_degrees
        ),
        "fuel_moisture_fraction_proxy": float(fm100_percent) / 100.0,
    }


def select_gridmet_nearest_cell(
    longitude_values: Any, latitude_values: Any, longitude: float, latitude: float
) -> tuple[int, int, float, float]:
    """Select the nearest cell in gridMET's rectilinear lon/lat coordinates."""
    import numpy as np

    longitudes = np.asarray(longitude_values, dtype=float)
    latitudes = np.asarray(latitude_values, dtype=float)
    if longitudes.ndim != 1 or latitudes.ndim != 1 or not len(longitudes) or not len(latitudes):
        raise ValueError("gridMET longitude and latitude coordinates must be non-empty 1-D arrays.")
    column = int(np.argmin(np.abs(longitudes - float(longitude))))
    row = int(np.argmin(np.abs(latitudes - float(latitude))))
    return row, column, float(longitudes[column]), float(latitudes[row])


def great_circle_distance_km(
    longitude_a: float, latitude_a: float, longitude_b: float, latitude_b: float
) -> float:
    """Haversine distance between two WGS84 points, in kilometres."""
    lon_a, lat_a, lon_b, lat_b = (
        math.radians(float(value)) for value in (longitude_a, latitude_a, longitude_b, latitude_b)
    )
    half_chord = (
        math.sin((lat_b - lat_a) / 2) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin((lon_b - lon_a) / 2) ** 2
    )
    return 2 * 6371.0088 * math.asin(math.sqrt(min(1.0, half_chord)))


def select_case_gridmet_cell(
    longitude_values: Any,
    latitude_values: Any,
    longitude: float,
    latitude: float,
    *,
    max_distance_km: float = 5.0,
) -> dict[str, float | int]:
    """Select one case's own gridMET cell and refuse a cell far from the case location."""
    row, column, cell_longitude, cell_latitude = select_gridmet_nearest_cell(
        longitude_values, latitude_values, longitude, latitude
    )
    distance_km = great_circle_distance_km(longitude, latitude, cell_longitude, cell_latitude)
    if not distance_km <= max_distance_km:
        raise ValueError(
            "Nearest gridMET cell is %.1f km from the case location (limit %.1f km)."
            % (distance_km, max_distance_km)
        )
    return {
        "row": row,
        "column": column,
        "longitude": cell_longitude,
        "latitude": cell_latitude,
        "distance_km": distance_km,
    }


def episode_weather_midpoints(initial_state_time: str) -> list[dict[str, str]]:
    """Create the four 12-hour segment midpoints for a fixed 48-hour episode."""
    start = feds_timestamp_to_utc(initial_state_time)
    segments = []
    for index in range(4):
        begin = start + timedelta(hours=12 * index)
        end = begin + timedelta(hours=12)
        midpoint = begin + timedelta(hours=6)
        segments.append({
            "segment": str(index),
            "start_utc": begin.isoformat(),
            "end_utc": end.isoformat(),
            "midpoint_utc": midpoint.isoformat(),
            "gridmet_daily_label_mst": gridmet_day_for_utc(midpoint),
        })
    return segments
