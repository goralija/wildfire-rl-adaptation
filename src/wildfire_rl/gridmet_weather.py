"""Small, explicit daily gridMET sampling and SimFire proxy conversions."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import math
from typing import Any


GRIDMET_MST = timezone(timedelta(hours=-7), name="MST")
METERS_PER_SECOND_TO_FEET_PER_MINUTE = 196.8503937007874
# TASK-027 / ADR-030 addendum: FEDS (fireatlas v1.4.1) assigns each VIIRS detection to
# AM or PM by local solar hour (UTC + Lon/15) and writes the label as hour 0 or 12; the
# SNPP overpasses are near 01:30 and 13:30 local solar time.
FEDS_TIME_REFERENCE = "feds_t_viirs_overpass_local_solar/v1"
VIIRS_OVERPASS_LOCAL_SOLAR_HOUR = {0: 1.5, 12: 13.5}


def feds_overpass_utc(value: str, longitude: float) -> datetime:
    """UTC instant of the VIIRS overpass that a naive FEDS `t` label (00:00/12:00) names."""
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        raise ValueError("FEDS `t` is a naive AM/PM label; a zoned time is not a FEDS label.")
    if parsed.minute or parsed.second or parsed.microsecond or (
            parsed.hour not in VIIRS_OVERPASS_LOCAL_SOLAR_HOUR):
        raise ValueError("FEDS `t` must be 00:00 (AM) or 12:00 (PM), got %r." % value)
    if not -180.0 <= float(longitude) <= 180.0:
        raise ValueError("longitude must be in [-180, 180].")
    midnight = datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc)
    overpass = midnight + timedelta(
        hours=VIIRS_OVERPASS_LOCAL_SOLAR_HOUR[parsed.hour] - float(longitude) / 15.0
    )
    # fireatlas v1.4.1 dates `t` by the UTC acquisition date (CONUS longitudes satisfy it).
    if overpass.date() != parsed.date():
        raise ValueError("Overpass of %r at longitude %.2f falls on another UTC date."
                         % (value, float(longitude)))
    return overpass


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


def episode_weather_midpoints(initial_state_time: str, *, longitude: float) -> list[dict[str, str]]:
    """Four 12-hour segments from the FEDS start overpass at ``longitude`` (48h episode)."""
    start = feds_overpass_utc(initial_state_time, longitude)
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


def pre_start_weather_day(initial_state_time: str, *, longitude: float) -> dict[str, str]:
    """The gridMET day before segment 0's daily label, as an observation-only record.

    ADR-030: at decision 0 policies observe initial conditions, never the forcing of
    the segment about to run. Segment 0's daily label usually covers the start, so the
    initial condition is the previous gridMET day. Its fields mirror a segment's: the
    interval is that MST day expressed in UTC and the midpoint is MST noon.
    """
    first = episode_weather_midpoints(initial_state_time, longitude=longitude)[0]
    label = date.fromisoformat(first["gridmet_daily_label_mst"]) - timedelta(days=1)
    begin = datetime(label.year, label.month, label.day, tzinfo=GRIDMET_MST)
    return {
        "segment": "pre_start",
        "start_utc": begin.astimezone(timezone.utc).isoformat(),
        "end_utc": (begin + timedelta(days=1)).astimezone(timezone.utc).isoformat(),
        "midpoint_utc": (begin + timedelta(hours=12)).astimezone(timezone.utc).isoformat(),
        "gridmet_daily_label_mst": label.isoformat(),
    }
