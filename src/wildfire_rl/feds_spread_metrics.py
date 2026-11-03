"""Spatial metrics for comparing simulated cumulative burn with FEDS outlines."""

from __future__ import annotations

from typing import Any

import numpy as np


def elliptical_growth_reference(
    initial_burn: Any,
    *,
    center_row: float,
    center_column: float,
    hours: float,
    downwind_degrees: float,
    cell_resolution_m: float = 180.0,
    head_advance_m_per_12h: float = 180.0,
    length_to_breadth: float = 2.0,
) -> np.ndarray:
    """Build a fixed, downwind 2:1 ellipse reference from the initial burn mask.

    The semi-major axis advances one study-grid cell per 12 hours. The baseline
    uses only the initial mask, the starting active-front centroid, and the first
    gridMET wind-to direction; it never reads a future FEDS perimeter.
    """
    initial = np.asarray(initial_burn, dtype=bool)
    if initial.ndim != 2 or not initial.size:
        raise ValueError("Initial burn must be a nonempty 2-D mask.")
    numeric = (center_row, center_column, hours, downwind_degrees,
               cell_resolution_m, head_advance_m_per_12h, length_to_breadth)
    if not all(np.isfinite(value) for value in numeric):
        raise ValueError("Ellipse parameters must be finite numbers.")
    if not (0 <= center_row <= initial.shape[0] - 1
            and 0 <= center_column <= initial.shape[1] - 1):
        raise ValueError("Ellipse center must fall inside the study grid.")
    if hours < 0 or cell_resolution_m <= 0 or head_advance_m_per_12h <= 0:
        raise ValueError("Time and distance parameters must be positive (time may be zero).")
    if length_to_breadth < 1:
        raise ValueError("Ellipse length-to-breadth ratio must be at least one.")
    if hours == 0:
        return initial.copy()

    semi_major_m = head_advance_m_per_12h * hours / 12.0
    semi_minor_m = semi_major_m / length_to_breadth
    rows, columns = np.indices(initial.shape, dtype=np.float64)
    east_m = (columns - center_column) * cell_resolution_m
    north_m = (center_row - rows) * cell_resolution_m
    angle = np.deg2rad(downwind_degrees % 360.0)
    along_wind_m = east_m * np.sin(angle) + north_m * np.cos(angle)
    cross_wind_m = east_m * np.cos(angle) - north_m * np.sin(angle)
    ellipse = ((along_wind_m / semi_major_m) ** 2
               + (cross_wind_m / semi_minor_m) ** 2) <= 1.0
    return initial | ellipse


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
