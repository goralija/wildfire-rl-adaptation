"""Explicit first-pass mapping of daily gridMET context into SimFire parameters.

This is a documented scenario proxy, not a reconstruction of hourly ignition weather.
"""

from __future__ import annotations

from typing import Any


MAPPING_VERSION = "gridmet-daily-simfire-proxy/1.0"
DEFAULT_WIND_ADJUSTMENT_FACTOR = 0.3


def _value(weather: dict[str, Any], key: str, expected_unit: str) -> float:
    item = weather["values"][key]
    if item.get("unit") != expected_unit:
        raise ValueError("{} must be in {}, got {!r}".format(key, expected_unit, item.get("unit")))
    return float(item["value"])


def simard_equilibrium_moisture_percent(temperature_c: float, relative_humidity_percent: float) -> float:
    """Return the Simard (1968) equilibrium moisture estimate in percent."""
    rh = float(relative_humidity_percent)
    temperature = float(temperature_c)
    if not 0.0 <= rh <= 100.0:
        raise ValueError("relative humidity must be between 0 and 100 percent")
    if rh < 10.0:
        estimate = 0.03 + 0.2626 * rh - 0.00104 * rh * temperature
    elif rh < 50.0:
        estimate = 1.76 + 0.1601 * rh - 0.02660 * temperature
    else:
        estimate = 21.06 - 0.4944 * rh + 0.005565 * rh * rh - 0.00063 * rh * temperature
    return max(0.0, estimate)


def map_gridmet_daily_weather(
    weather: dict[str, Any], *, wind_adjustment_factor: float = DEFAULT_WIND_ADJUSTMENT_FACTOR
) -> dict[str, Any]:
    """Convert daily weather context to a stationary, assumption-labeled SimFire proxy.

    Assumptions are stored beside derived values: gridMET 10-m speed is used as a proxy
    for the 20-ft surface reference; a partially-sheltered WAF is applied; meteorological
    wind-from direction is reversed to SimFire's direction-of-spread convention; and a
    dry-side fine-fuel EMC estimate from daily max temperature/min RH is held constant for
    the episode. The 100-hour NFDRS value remains context and is not substituted for EMC.
    """
    factor = float(wind_adjustment_factor)
    if not 0.1 <= factor <= 0.5:
        raise ValueError("wind adjustment factor must be between 0.1 and 0.5 for this sensitivity profile")

    wind_speed_m_s = _value(weather, "wind_speed_10m", "m/s")
    wind_from_deg = _value(weather, "wind_from_direction_10m", "Degrees Clockwise from north")
    max_temperature_k = _value(weather, "daily_max_air_temperature", "K")
    min_rh_percent = _value(weather, "daily_min_relative_humidity", "%")
    fm100_percent = _value(weather, "dead_fuel_moisture_100hr_model_g", "Percent")
    if wind_speed_m_s < 0.0:
        raise ValueError("gridMET wind speed cannot be negative")
    if not 0.0 <= wind_from_deg <= 360.0:
        raise ValueError("gridMET wind direction must be between 0 and 360 degrees")

    max_temperature_c = max_temperature_k - 273.15
    emc_percent = simard_equilibrium_moisture_percent(max_temperature_c, min_rh_percent)
    reference_wind_mph = wind_speed_m_s * 2.2369362921
    return {
        "mapping_version": MAPPING_VERSION,
        "scenario_id": weather["scenario_id"],
        "date": weather["date"],
        "weather_source_sha256": weather.get("sha256"),
        "simfire_parameters": {
            "wind_speed_midflame_mph_proxy": reference_wind_mph * factor,
            "wind_direction_degrees_clockwise_north_to": (wind_from_deg + 180.0) % 360.0,
            "fuel_moisture_fraction_proxy": emc_percent / 100.0,
        },
        "derived_values": {
            "wind_speed_10m_m_s": wind_speed_m_s,
            "wind_speed_assumed_20ft_reference_mph": reference_wind_mph,
            "wind_adjustment_factor": factor,
            "wind_from_direction_degrees": wind_from_deg,
            "wind_toward_direction_degrees": (wind_from_deg + 180.0) % 360.0,
            "daily_max_temperature_k": max_temperature_k,
            "daily_max_temperature_c": max_temperature_c,
            "daily_min_relative_humidity_percent": min_rh_percent,
            "simard_equilibrium_moisture_percent_proxy": emc_percent,
            "simfire_fuel_moisture_fraction_proxy": emc_percent / 100.0,
        },
        "assumptions": [
            "Treat gridMET daily 10-m wind speed as a proxy for the 20-ft surface reference; no site-specific height profile is available.",
            "Use wind adjustment factor {:.2f}, the NWCG partially-sheltered reference value, as an assumed scenario; sheltering is not measured for these cases.".format(factor),
            "Reverse meteorological wind-from direction by 180 degrees because SimFire's spread calculation uses the direction toward which wind pushes spread.",
            "Hold one representative daily weather condition constant during the 12-hour maximum episode; this is not an hourly replay or aligned to FPA-FOD discovery HHMM.",
            "Estimate a dry-side equilibrium fine-fuel moisture proxy with Simard (1968), using separate daily maximum-temperature and minimum-RH fields; those extrema may not occur together and equilibrium is not actual measured fuel moisture.",
            "Do not use gridMET NFDRS model-G 100-hour fuel moisture as if it were SimFire fine-fuel moisture; it remains in the raw context record.",
        ],
        "sensitivity": {
            "wind_adjustment_factors": [0.1, 0.3, 0.5],
            "factor_note": "0.3 is the nominal partial-shelter scenario; 0.1 and 0.5 provide simple lower/upper WAF sensitivity cases, not measured local shelter classes.",
            "wind_speed_mph_by_factor": {
                "0.1": reference_wind_mph * 0.1,
                "0.3": reference_wind_mph * 0.3,
                "0.5": reference_wind_mph * 0.5,
            },
            "fuel_moisture_alternatives": [
                {"name": "fixed_demo_moisture", "fraction": 0.03},
                {"name": "gridmet_model_g_fm100_context_only", "percent": fm100_percent, "fraction_if_experimentally_substituted": fm100_percent / 100.0},
            ],
        },
    }
