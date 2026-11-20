"""Exploratory line-footprint accounting; the locked SimFire reward is unchanged.

A new line cell inside the paired no-op burn footprint is consumed, rather than
saved. Count a union with agent damage, never charge prior damage or count twice.
"""
import numpy as np

HECTARES_PER_CELL = 3.24


def score_line_damage(initial_burned, agent_burned, noop_burned, line_cells):
    arrays = [np.asarray(mask) for mask in
              (initial_burned, agent_burned, noop_burned, line_cells)]
    shape = arrays[0].shape
    if len(shape) != 2 or any(mask.shape != shape or
                             not np.all((mask == 0) | (mask == 1)) for mask in arrays):
        raise ValueError("damage masks must be binary, equally shaped 2-D arrays")
    initial, agent, noop, line = (mask.astype(bool) for mask in arrays)
    agent_new = agent & ~initial
    noop_new = noop & ~initial
    footprint = line & noop_new
    raw = int(agent_new.sum())
    charged = int((agent_new | footprint).sum())
    return {
        "noop_damage_cells": int(noop_new.sum()),
        "raw_damage_cells": raw,
        "line_cells_in_noop_footprint": int(footprint.sum()),
        "extra_line_charge_cells": charged - raw,
        "charged_damage_cells": charged,
        "raw_saved_cells": int(noop_new.sum()) - raw,
        "charged_saved_cells": int(noop_new.sum()) - charged,
    }
