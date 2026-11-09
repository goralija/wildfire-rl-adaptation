"""Convert physical fire-cell lifetimes to SimFire update counts."""

from __future__ import annotations

import math


def updates_for_duration(duration_minutes: float, update_minutes: float) -> int:
    """Return enough whole simulator updates to preserve a physical duration."""
    if not math.isfinite(duration_minutes) or not math.isfinite(update_minutes):
        raise ValueError("Durations must be finite.")
    if duration_minutes <= 0 or update_minutes <= 0:
        raise ValueError("Durations and update intervals must be positive.")
    return max(1, int(math.ceil(duration_minutes / update_minutes)))
