"""Small, leakage-safe primitives for event-specific CFSDS fuel-vintage work.

This module derives a *perimeter mask only*. It deliberately does not assign a
new FBP fuel class to burned pixels: that needs a provenance-safe base map and a
verified succession crosswalk.
"""

from __future__ import annotations

import numpy as np

NODATA_ARRIVAL = 4_000_000_000


def pre_target_burn_mask(
    arrival_day: np.ndarray,
    target_doy: int,
    *,
    nodata: int = NODATA_ARRIVAL,
) -> np.ndarray:
    """Return valid event pixels burned strictly before target day ``n``.

    CFSDS arrival rasters encode a day-of-year value per burned pixel. Day
    ``n-1`` is intentionally included because it is prior to ``n``; this also
    means a future fuel-succession rule must remain compatible with the
    simulator's imported day ``n-1`` front and older scar state.
    """
    values = np.asarray(arrival_day)
    if values.ndim != 2:
        raise ValueError("arrival_day must be a two-dimensional raster")
    if not isinstance(target_doy, (int, np.integer)) or not 1 <= int(target_doy) <= 366:
        raise ValueError("target_doy must be an integer in [1, 366]")
    if int(nodata) <= int(target_doy):
        raise ValueError("nodata must be greater than target_doy")

    valid = values < int(nodata)
    return (values > 0) & (values < int(target_doy)) & valid


def select_train_candidate(candidates: list[dict], event_id: str) -> dict:
    """Select exactly one train row and refuse validation/test rows."""
    matches = [row for row in candidates if str(row.get("event_id")) == event_id]
    if len(matches) != 1:
        raise ValueError(f"Expected one screen row for {event_id}, found {len(matches)}")
    candidate = matches[0]
    if candidate.get("split") != "train":
        raise ValueError(f"Refusing non-train event {event_id!r}")
    return candidate
