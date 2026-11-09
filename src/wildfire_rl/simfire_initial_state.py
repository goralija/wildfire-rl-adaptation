"""Small, testable helpers for importing observed FEDS scar/front masks into SimFire."""

from __future__ import annotations


SIMFIRE_UNBURNED = 0
SIMFIRE_BURNING = 1
SIMFIRE_BURNED = 2


def compose_initial_fire_map(burn_scar_mask: object, active_front_mask: object):
    """Encode a multi-cell observed scar and active front using SimFire v2 statuses.

    FEDS `lf_perimeter` supplies the already-burned interior; `lf_fireline` supplies
    the active front at the exact same timestamp. The front overrides the scar status
    so its cells can spread outward on the first simulator update.
    """
    import numpy as np

    scar = np.asarray(burn_scar_mask, dtype=bool)
    front = np.asarray(active_front_mask, dtype=bool)
    if scar.ndim != 2 or front.ndim != 2 or scar.shape != front.shape:
        raise ValueError("burn-scar and active-front masks must have the same two-dimensional shape")
    if not np.any(front):
        raise ValueError("initial state must include at least one active-front cell")

    fire_map = np.full(scar.shape, SIMFIRE_UNBURNED, dtype=np.uint8)
    fire_map[scar] = SIMFIRE_BURNED
    fire_map[front] = SIMFIRE_BURNING
    return fire_map


def update_cumulative_burned(cumulative_burned_mask: object, fire_map: object):
    """Keep the historical scar and every SimFire burning/burned cell in total area."""
    import numpy as np

    previous = np.asarray(cumulative_burned_mask, dtype=bool)
    current = np.asarray(fire_map)
    if previous.ndim != 2 or current.ndim != 2 or previous.shape != current.shape:
        raise ValueError("cumulative-burn and SimFire state arrays must have the same two-dimensional shape")
    return previous | np.isin(current, (SIMFIRE_BURNING, SIMFIRE_BURNED))
