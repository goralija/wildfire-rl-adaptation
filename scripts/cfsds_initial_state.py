"""Target-blind window and initial-state rules for CFSDS day-pair cases.

Only arrival values strictly before target day ``n`` may determine the model
window and imported initial state. The observed day-n raster is evaluation
truth and must not be passed to these helpers.
"""

from __future__ import annotations

from typing import Any

import numpy as np

NODATA_ARRIVAL = 4_000_000_000
MIN_FRONT_CELLS = 3
FRONT_EDGE_MARGIN_CELLS = 1


def _box_sums(mask: np.ndarray, size: int) -> np.ndarray:
    integral = np.pad(mask.astype(np.int64), ((1, 0), (1, 0)))
    integral = integral.cumsum(axis=0).cumsum(axis=1)
    return integral[size:, size:] - integral[:-size, size:] - integral[size:, :-size] + integral[:-size, :-size]


def select_target_blind_window(
    arrival: np.ndarray,
    target_doy: int,
    *,
    tile_size: int = 23,
    nodata: int = NODATA_ARRIVAL,
    min_front_cells: int = MIN_FRONT_CELLS,
    edge_margin_cells: int = FRONT_EDGE_MARGIN_CELLS,
) -> dict[str, Any] | None:
    """Choose a crop using pre-target history and the day ``n-1`` front.

    The selected day-n mask is never calculated here. Select the eligible crop
    whose center is closest to the centroid of all valid day n-1 pixels. An
    eligible crop must contain the declared minimum number of day n-1 pixels
    inside its outermost native-raster ring; those interior pixels form the
    active boundary on the 20x20 model grid. Ties prefer more interior front,
    more pre-target history, then row/column order. Day n-1 pixels on the crop
    border remain historical burnt area, not active front.
    Whole-event front capture is diagnostic only. ``None`` means no window
    contains the declared minimum number of interior front pixels.
    """
    values = np.asarray(arrival)
    if values.ndim != 2:
        raise ValueError("arrival must be a two-dimensional raster")
    if not isinstance(target_doy, (int, np.integer)) or not 2 <= int(target_doy) <= 366:
        raise ValueError("target_doy must be an integer in [2, 366]")
    if tile_size <= 2 * edge_margin_cells or tile_size <= 0:
        raise ValueError("tile_size must be larger than twice the edge margin")
    if min_front_cells < 1:
        raise ValueError("min_front_cells must be positive")
    if edge_margin_cells < 0:
        raise ValueError("edge_margin_cells must be non-negative")
    if values.shape[0] < tile_size or values.shape[1] < tile_size:
        return None

    before_target = (values > 0) & (values < int(target_doy)) & (values < int(nodata))
    latest_day = before_target & (values == int(target_doy) - 1)
    total_front = int(latest_day.sum())
    if total_front < min_front_cells:
        return None

    all_front_counts = _box_sums(latest_day, tile_size)
    history_counts = _box_sums(before_target, tile_size)
    margin = int(edge_margin_cells)
    if margin:
        active_front_counts = _box_sums(
            latest_day[margin:-margin, margin:-margin], tile_size - 2 * margin
        )
    else:
        active_front_counts = all_front_counts
    eligible = active_front_counts >= min_front_cells
    if not eligible.any():
        return None

    front_rows, front_cols = np.nonzero(latest_day)
    front_center_row = float(front_rows.mean())
    front_center_col = float(front_cols.mean())
    rows, cols = np.indices(history_counts.shape)
    center_distance_sq = (
        rows + (tile_size - 1) / 2 - front_center_row
    ) ** 2 + (cols + (tile_size - 1) / 2 - front_center_col) ** 2
    min_distance = float(center_distance_sq[eligible].min())
    nearest = eligible & (center_distance_sq == min_distance)
    max_front = int(active_front_counts[nearest].max())
    front_best = nearest & (active_front_counts == max_front)
    max_history = int(history_counts[front_best].max())
    history_best = front_best & (history_counts == max_history)
    final_ties = history_best
    best_row, best_col = (int(value) for value in np.argwhere(final_ties)[0])
    selected_front = int(active_front_counts[best_row, best_col])
    all_front = int(all_front_counts[best_row, best_col])
    selected_history = int(history_counts[best_row, best_col])
    return {
        "row_off": best_row,
        "col_off": best_col,
        "pre_target_pixels_in_window": selected_history,
        "day_n_minus_1_front_pixels_in_window": selected_front,
        "day_n_minus_1_pixels_in_window": all_front,
        "day_n_minus_1_border_pixels_as_burnt_scar": all_front - selected_front,
        "day_n_minus_1_front_pixels_total": total_front,
        "day_n_minus_1_front_capture_ratio": round(selected_front / total_front, 6),
        "day_n_minus_1_centroid_to_window_center_px": round(min_distance ** 0.5, 6),
        "rule": "select target-blind crop whose center is nearest the centroid of all day n-1 pixels, requiring at least the minimum safe-interior front; ties maximize interior front then pre-target history; border-ring day n-1 pixels remain burnt scar",
    }


def derive_pre_target_state_masks(
    arrival: np.ndarray,
    target_doy: int,
    *,
    nodata: int = NODATA_ARRIVAL,
    edge_margin_cells: int = FRONT_EDGE_MARGIN_CELLS,
) -> dict[str, np.ndarray]:
    """Return historical scar and safe-interior day n-1 front, without day n.

    Pixels in the crop border are kept as burnt scar; this avoids initializing
    active flames on the edge of the model grid.
    """
    values = np.asarray(arrival)
    if values.ndim != 2:
        raise ValueError("arrival must be a two-dimensional raster")
    if not isinstance(target_doy, (int, np.integer)) or not 2 <= int(target_doy) <= 366:
        raise ValueError("target_doy must be an integer in [2, 366]")
    if edge_margin_cells < 0 or 2 * edge_margin_cells >= min(values.shape):
        raise ValueError("edge_margin_cells must leave a non-empty raster interior")
    valid = (values > 0) & (values < int(nodata))
    front = valid & (values == int(target_doy) - 1)
    if edge_margin_cells:
        front[:edge_margin_cells, :] = False
        front[-edge_margin_cells:, :] = False
        front[:, :edge_margin_cells] = False
        front[:, -edge_margin_cells:] = False
    scar = valid & (values < int(target_doy)) & ~front
    return {"scar": scar, "front": front}


def initial_state_cells(burnt: np.ndarray, burning: np.ndarray) -> list[tuple[str, int]]:
    """Serialize majority-cell masks as sorted one-based row-major importer rows."""
    scar = np.asarray(burnt, dtype=bool)
    front = np.asarray(burning, dtype=bool)
    if scar.ndim != 2 or front.ndim != 2 or scar.shape != front.shape:
        raise ValueError("burnt and burning masks must be same-shaped 2D arrays")
    if np.any(scar & front):
        raise ValueError("burnt and burning masks must not overlap")
    rows: list[tuple[str, int]] = []
    for row in range(scar.shape[0]):
        for col in range(scar.shape[1]):
            cell = row * scar.shape[1] + col + 1
            if scar[row, col]:
                rows.append(("burnt", cell))
            elif front[row, col]:
                rows.append(("burning", cell))
    return rows
