"""Spatial metrics for comparing simulated cumulative burn with FEDS outlines."""

from __future__ import annotations

from typing import Any

import numpy as np

# Bump when a scored field changes meaning, so reports built on old metrics cannot mix with new ones.
METRICS_VERSION = "feds-spread-metrics/3"

ELLIPSE_REFERENCE_PROTOCOL = {
    "shape": "fixed 2:1 ellipse with the ignition point at its rear focus, unioned with the initial burn mask",
    "ignition_point": "leading edge of the initial FEDS active front along the heading (mean of front cells within half a cell of the most downwind one), placed at the rear focus",
    "heading": "first 12-hour gridMET wind-to direction; the ellipse centre lies downwind of the ignition point",
    "semi_major_growth": "180 m per 12 hours (one study-grid cell)",
    "semi_minor_growth": "semi-major axis divided by 2",
    "head_extent": "(1 + sqrt(3)/2) x semi-major, about 336 m per 12 hours downwind of the ignition point",
    "back_extent": "(1 - sqrt(3)/2) x semi-major, about 24 m per 12 hours upwind of the ignition point",
    "future_feds_used": False,
    "calibrated_from_future_feds": False,
    "purpose": "simple predeclared geometric reference, not a physical spread model",
}


def elliptical_growth_reference(
    initial_burn: Any,
    *,
    center_row: float,
    center_column: float,
    hours: float,
    downwind_degrees: float,
    cell_resolution_m: float = 180.0,
    semi_major_growth_m_per_12h: float = 180.0,
    length_to_breadth: float = 2.0,
) -> np.ndarray:
    """Build a fixed, downwind 2:1 ellipse reference from the initial burn mask.

    ``(center_row, center_column)`` is the ignition point and sits at the rear
    focus, so the ellipse centre lies ``c = sqrt(a^2 - b^2)`` downwind of it. The
    semi-major axis ``a`` grows one study-grid cell per 12 hours; with a 2:1 ratio
    the head reaches about 1.87a downwind and the back about 0.13a upwind. The
    baseline uses only the initial mask, the starting active-front centroid, and
    the first gridMET wind-to direction; it never reads a future FEDS perimeter.
    Use ``ellipse_ignition_point`` for the ignition point.
    """
    initial = np.asarray(initial_burn, dtype=bool)
    if initial.ndim != 2 or not initial.size:
        raise ValueError("Initial burn must be a nonempty 2-D mask.")
    numeric = (center_row, center_column, hours, downwind_degrees,
               cell_resolution_m, semi_major_growth_m_per_12h, length_to_breadth)
    if not all(np.isfinite(value) for value in numeric):
        raise ValueError("Ellipse parameters must be finite numbers.")
    if not (0 <= center_row <= initial.shape[0] - 1
            and 0 <= center_column <= initial.shape[1] - 1):
        raise ValueError("Ellipse center must fall inside the study grid.")
    if hours < 0 or cell_resolution_m <= 0 or semi_major_growth_m_per_12h <= 0:
        raise ValueError("Time and distance parameters must be positive (time may be zero).")
    if length_to_breadth < 1:
        raise ValueError("Ellipse length-to-breadth ratio must be at least one.")
    if hours == 0:
        return initial.copy()

    semi_major_m = semi_major_growth_m_per_12h * hours / 12.0
    semi_minor_m = semi_major_m / length_to_breadth
    focus_offset_m = float(np.sqrt(semi_major_m ** 2 - semi_minor_m ** 2))
    rows, columns = np.indices(initial.shape, dtype=np.float64)
    east_m = (columns - center_column) * cell_resolution_m
    north_m = (center_row - rows) * cell_resolution_m
    angle = np.deg2rad(downwind_degrees % 360.0)
    along_wind_m = east_m * np.sin(angle) + north_m * np.cos(angle) - focus_offset_m
    cross_wind_m = east_m * np.cos(angle) - north_m * np.sin(angle)
    ellipse = ((along_wind_m / semi_major_m) ** 2
               + (cross_wind_m / semi_minor_m) ** 2) <= 1.0
    return initial | ellipse


def ellipse_ignition_point(active_front: Any, downwind_degrees: float) -> tuple[float, float]:
    """Return the leading edge of the active front along the downwind heading.

    The front centroid can sit inside the burn scar (a ring-shaped front), where a
    small ellipse adds no new cells. The reference instead starts at the front's
    leading edge: the mean of the front cells within half a cell of the most
    downwind one, so ties along a straight front stay centred.
    """
    front = np.asarray(active_front, dtype=bool)
    if front.ndim != 2 or not front.any():
        raise ValueError("Active front must be a 2-D mask with at least one cell.")
    if not np.isfinite(downwind_degrees):
        raise ValueError("Ellipse heading must be finite.")
    rows, columns = np.nonzero(front)
    angle = np.deg2rad(float(downwind_degrees) % 360.0)
    # Same axes as elliptical_growth_reference: east = +column, north = -row.
    along_wind = columns * np.sin(angle) - rows * np.cos(angle)
    leading = along_wind >= along_wind.max() - 0.5
    return float(rows[leading].mean()), float(columns[leading].mean())


def growth_overlap_metrics(
    intersection_cells: int,
    predicted_growth_cells: int,
    observed_growth_cells: int,
) -> dict[str, float | None]:
    """Return IoU, precision and recall of new growth from cell counts.

    A ratio whose denominator is empty is ``None`` rather than 0 or 1: when
    neither mask grows, a 1.0 would reward a static prediction on every stalled
    fire, and a 0.0 would penalise a correct one.
    """
    counts = (intersection_cells, predicted_growth_cells, observed_growth_cells)
    if any(int(value) != value or value < 0 for value in counts):
        raise ValueError("Growth cell counts must be non-negative integers.")
    if intersection_cells > min(predicted_growth_cells, observed_growth_cells):
        raise ValueError("Growth intersection cannot exceed either growth mask.")
    union_cells = predicted_growth_cells + observed_growth_cells - intersection_cells
    return {
        "growth_iou": intersection_cells / union_cells if union_cells else None,
        "growth_precision": (intersection_cells / predicted_growth_cells
                             if predicted_growth_cells else None),
        "growth_recall": (intersection_cells / observed_growth_cells
                          if observed_growth_cells else None),
    }


def binary_burn_metrics(
    predicted: Any,
    observed: Any,
    *,
    initial_burn: Any | None = None,
    cell_resolution_m: float = 180.0,
) -> dict[str, float | int | bool | None]:
    """Return overlap, area, and map-edge metrics for two aligned burn masks.

    The full-mask ``iou``/``precision``/``recall`` include the initial burn that
    prediction and observation share. The ``growth_*`` fields score only cells
    outside ``initial_burn``; initial cells missing from the observed outline are
    outside that domain as well. See ``growth_overlap_metrics`` for empty cases.
    """
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
    observed_growth_count = int(np.count_nonzero(target & ~initial))
    growth_hit_count = int(np.count_nonzero(prediction & target & ~initial))
    hectares_per_cell = float(cell_resolution_m * cell_resolution_m / 10000.0)
    return {
        "intersection_cells": true_positive,
        "union_cells": union_count,
        "predicted_burned_cells": predicted_count,
        "observed_burned_cells": observed_count,
        "new_burned_cells_since_initial": new_burned_count,
        "predicted_growth_cells": new_burned_count,
        "observed_growth_cells": observed_growth_count,
        "growth_intersection_cells": growth_hit_count,
        "iou": true_positive / union_count if union_count else 1.0,
        "precision": true_positive / predicted_count if predicted_count else 0.0,
        "recall": true_positive / observed_count,
        "predicted_area_ha": predicted_count * hectares_per_cell,
        "observed_area_ha": observed_count * hectares_per_cell,
        "new_burned_area_ha": new_burned_count * hectares_per_cell,
        "edge_cells": edge_cells,
        "edge_cell_fraction": edge_cells / predicted_count if predicted_count else 0.0,
        "touches_map_edge": bool(edge_cells),
        **growth_overlap_metrics(growth_hit_count, new_burned_count, observed_growth_count),
    }
