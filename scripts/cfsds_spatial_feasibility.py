"""Target-blind spatial window selection and post-selection coverage metrics."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

try:
    from .cfsds_initial_state import NODATA_ARRIVAL, select_target_blind_window
except ImportError:  # pragma: no cover - direct script imports
    from cfsds_initial_state import NODATA_ARRIVAL, select_target_blind_window


def native_window_shape(
    grid_rows: int,
    grid_cols: int,
    cell_size_m: float,
    native_cell_size_m: float = 90.0,
) -> tuple[int, int]:
    """Return source-pixel dimensions covering the requested model footprint."""
    if grid_rows <= 0 or grid_cols <= 0:
        raise ValueError("grid dimensions must be positive")
    if not math.isfinite(cell_size_m) or cell_size_m <= 0:
        raise ValueError("cell_size_m must be finite and positive")
    if not math.isfinite(native_cell_size_m) or native_cell_size_m <= 0:
        raise ValueError("native_cell_size_m must be finite and positive")
    return (
        math.ceil(grid_rows * cell_size_m / native_cell_size_m),
        math.ceil(grid_cols * cell_size_m / native_cell_size_m),
    )


def _interior(mask: np.ndarray, margin: int) -> np.ndarray:
    if margin < 0 or 2 * margin >= min(mask.shape):
        raise ValueError("edge margin must leave a non-empty window interior")
    if margin == 0:
        return mask
    return mask[margin:-margin, margin:-margin]


def _adjacent_to(mask: np.ndarray, neighbors: np.ndarray) -> np.ndarray:
    """Return cells in mask with an 8-neighbour in neighbors, without SciPy."""
    padded = np.pad(neighbors.astype(bool), 1, mode="constant", constant_values=False)
    adjacent = np.zeros(mask.shape, dtype=bool)
    rows, cols = mask.shape
    for row_shift in range(3):
        for col_shift in range(3):
            adjacent |= padded[row_shift:row_shift + rows, col_shift:col_shift + cols]
    return mask & adjacent


def evaluate_target_blind_window(
    arrival: np.ndarray,
    target_doy: int,
    *,
    grid_rows: int,
    grid_cols: int,
    cell_size_m: float,
    native_cell_size_m: float = 90.0,
    nodata: int = NODATA_ARRIVAL,
    min_front_pixels: int = 3,
) -> dict[str, Any]:
    """Select a pre-target window, then measure the hidden target diagnostically.

    The crop and active-front selection are completed before the day-n mask is
    derived. Target metrics never affect the selected origin or input-state
    counts. Metrics count native raster pixels, not simulator cells.
    """
    values = np.asarray(arrival)
    if values.ndim != 2:
        raise ValueError("arrival must be a two-dimensional raster")
    if not isinstance(target_doy, (int, np.integer)) or not 2 <= int(target_doy) <= 366:
        raise ValueError("target_doy must be an integer in [2, 366]")

    tile_rows, tile_cols = native_window_shape(
        grid_rows, grid_cols, cell_size_m, native_cell_size_m
    )
    if tile_rows != tile_cols:
        raise ValueError("spatial feasibility currently requires a square model grid")
    # Keep the safe border approximately one model cell wide in source pixels.
    edge_margin = max(1, int(math.floor(cell_size_m / native_cell_size_m + 0.5)))
    selected = select_target_blind_window(
        values,
        int(target_doy),
        tile_size=tile_rows,
        nodata=nodata,
        min_front_cells=min_front_pixels,
        edge_margin_cells=edge_margin,
    )
    if selected is None:
        return {
            "window_found": False,
            "window_unavailable_reason": (
                "source_raster_smaller_than_requested_window"
                if values.shape[0] < tile_rows or values.shape[1] < tile_cols
                else "no_window_meets_minimum_safe_interior_front"
            ),
            "source_raster_shape_rc": [int(values.shape[0]), int(values.shape[1])],
            "grid_rows": grid_rows,
            "grid_cols": grid_cols,
            "cell_size_m": cell_size_m,
            "requested_extent_m": [grid_rows * cell_size_m, grid_cols * cell_size_m],
            "native_window_shape_rc": [tile_rows, tile_cols],
            "realized_extent_m": [tile_rows * native_cell_size_m, tile_cols * native_cell_size_m],
            "edge_margin_native_pixels": edge_margin,
            "minimum_safe_interior_front_pixels": min_front_pixels,
            "target_geometry_used_for_window_selection": False,
        }

    row, col = int(selected["row_off"]), int(selected["col_off"])
    crop = values[row:row + tile_rows, col:col + tile_cols]
    valid = (crop > 0) & (crop < int(nodata))
    pre_target = valid & (crop < int(target_doy))
    previous_day = valid & (crop == int(target_doy) - 1)
    interior_previous = _interior(previous_day, edge_margin)

    # Target-specific truth is touched only after the target-blind crop is fixed.
    target = (values == int(target_doy)) & (values > 0) & (values < int(nodata))
    target_crop = (crop == int(target_doy)) & (crop > 0) & (crop < int(nodata))
    target_interior = _interior(target_crop, edge_margin)
    adjacent_target = _adjacent_to(
        target,
        (values == int(target_doy) - 1) & (values > 0) & (values < int(nodata)),
    )
    adjacent_target_crop = _adjacent_to(
        target_crop,
        previous_day,
    )

    target_total = int(target.sum())
    target_inside = int(target_crop.sum())
    front_total = int(((values == int(target_doy) - 1) & (values > 0) & (values < int(nodata))).sum())
    front_inside = int(previous_day.sum())
    native_pixel_area_ha = (native_cell_size_m * native_cell_size_m) / 10_000
    return {
        "window_found": True,
        "source_raster_shape_rc": [int(values.shape[0]), int(values.shape[1])],
        "grid_rows": grid_rows,
        "grid_cols": grid_cols,
        "cell_size_m": cell_size_m,
        "requested_extent_m": [grid_rows * cell_size_m, grid_cols * cell_size_m],
        "native_window_shape_rc": [tile_rows, tile_cols],
        "realized_extent_m": [tile_rows * native_cell_size_m, tile_cols * native_cell_size_m],
        "edge_margin_native_pixels": edge_margin,
        "row_off": row,
        "col_off": col,
        "pre_target_pixels_in_window": int(pre_target.sum()),
        "day_n_minus_1_front_pixels_total": front_total,
        "day_n_minus_1_front_pixels_in_window": front_inside,
        "day_n_minus_1_front_pixels_in_safe_interior": int(interior_previous.sum()),
        "day_n_minus_1_front_capture_ratio": round(front_inside / front_total, 8) if front_total else None,
        "day_n_minus_1_centroid_to_window_center_px": selected[
            "day_n_minus_1_centroid_to_window_center_px"
        ],
        "target_pixels_total": target_total,
        "target_pixels_in_window": target_inside,
        "target_pixels_in_safe_interior": int(target_interior.sum()),
        "target_pixels_in_edge_ring": target_inside - int(target_interior.sum()),
        "target_pixels_outside_window": target_total - target_inside,
        "target_capture_ratio": round(target_inside / target_total, 8) if target_total else None,
        "target_safe_interior_capture_ratio": round(int(target_interior.sum()) / target_total, 8) if target_total else None,
        "target_pixels_adjacent_to_previous_day_total": int(adjacent_target.sum()),
        "target_adjacent_pixels_in_window": int(adjacent_target_crop.sum()),
        "target_nonadjacent_pixels_in_window": target_inside - int(adjacent_target_crop.sum()),
        "target_area_total_ha_native_pixel_equivalent": round(target_total * native_pixel_area_ha, 4),
        "target_area_in_window_ha_native_pixel_equivalent": round(target_inside * native_pixel_area_ha, 4),
        "front_capture_ratio_is_native_pixel_count": True,
        "target_geometry_used_for_window_selection": False,
    }
