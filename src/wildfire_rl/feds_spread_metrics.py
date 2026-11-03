"""Spatial metrics for comparing simulated cumulative burn with FEDS outlines."""

from __future__ import annotations

from typing import Any

import numpy as np


def binary_burn_metrics(
    predicted: Any,
    observed: Any,
    *,
    initial_burn: Any | None = None,
    cell_resolution_m: float = 180.0,
) -> dict[str, float | int | bool]:
    """Return overlap, area, and map-edge metrics for two aligned burn masks."""
    prediction = np.asarray(predicted, dtype=bool)
    target = np.asarray(observed, dtype=bool)
    if prediction.ndim != 2 or target.ndim != 2 or prediction.shape != target.shape:
        raise ValueError("Predicted and observed burn masks must be equally shaped 2-D arrays.")
    if not target.any():
        raise ValueError("Observed burn mask must contain at least one cell.")
    if not np.isfinite(cell_resolution_m) or cell_resolution_m <= 0:
        raise ValueError("Cell resolution must be a positive finite distance in meters.")
    initial = np.zeros_like(prediction) if initial_burn is None else np.asarray(initial_burn, dtype=bool)
    if initial.shape != prediction.shape:
        raise ValueError("Initial burn mask must match the predicted and observed grids.")

    true_positive = int(np.count_nonzero(prediction & target))
    predicted_count = int(prediction.sum())
    observed_count = int(target.sum())
    union_count = int(np.count_nonzero(prediction | target))
    edge = np.zeros_like(prediction)
    edge[0, :] = True
    edge[-1, :] = True
    edge[:, 0] = True
    edge[:, -1] = True
    edge_cells = int(np.count_nonzero(prediction & edge))
    new_burned_count = int(np.count_nonzero(prediction & ~initial))
    hectares_per_cell = float(cell_resolution_m * cell_resolution_m / 10000.0)
    return {
        "intersection_cells": true_positive,
        "union_cells": union_count,
        "predicted_burned_cells": predicted_count,
        "observed_burned_cells": observed_count,
        "new_burned_cells_since_initial": new_burned_count,
        "iou": true_positive / union_count if union_count else 1.0,
        "precision": true_positive / predicted_count if predicted_count else 0.0,
        "recall": true_positive / observed_count,
        "predicted_area_ha": predicted_count * hectares_per_cell,
        "observed_area_ha": observed_count * hectares_per_cell,
        "new_burned_area_ha": new_burned_count * hectares_per_cell,
        "edge_cells": edge_cells,
        "edge_cell_fraction": edge_cells / predicted_count if predicted_count else 0.0,
        "touches_map_edge": bool(edge_cells),
    }
