"""Geometry and grid helpers for observed FEDS starts on the SimFire study grid."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GridSpec:
    crs: str
    rows: int
    columns: int
    resolution_m: float
    bounds_m: tuple[float, float, float, float]


def utm_crs_for_lon_lat(longitude: float, latitude: float) -> str:
    """Return the local UTM CRS for a WGS84 coordinate."""
    if not (-180.0 <= longitude <= 180.0 and -80.0 <= latitude <= 84.0):
        raise ValueError("UTM projection is only defined here for lon [-180,180], lat [-80,84].")
    zone = min(60, max(1, int((longitude + 180.0) // 6.0) + 1))
    epsg = (32600 if latitude >= 0 else 32700) + zone
    return f"EPSG:{epsg}"


def centered_grid_spec(
    center_x: float,
    center_y: float,
    *,
    crs: str,
    rows: int = 256,
    columns: int = 256,
    resolution_m: float = 180.0,
) -> GridSpec:
    """Build a fixed-resolution square grid centered on an observed perimeter."""
    if rows <= 0 or columns <= 0 or resolution_m <= 0:
        raise ValueError("Grid dimensions and resolution must be positive.")
    width = columns * resolution_m
    height = rows * resolution_m
    return GridSpec(
        crs=crs,
        rows=rows,
        columns=columns,
        resolution_m=resolution_m,
        bounds_m=(center_x - width / 2, center_y - height / 2,
                  center_x + width / 2, center_y + height / 2),
    )


def grid_covers_geometry(spec: GridSpec, geometry: Any, *, tolerance_m: float = 1e-6) -> bool:
    """Check that a projected geometry's full bounding box fits inside the grid."""
    xmin, ymin, xmax, ymax = spec.bounds_m
    gxmin, gymin, gxmax, gymax = geometry.bounds
    return (
        gxmin >= xmin - tolerance_m
        and gymin >= ymin - tolerance_m
        and gxmax <= xmax + tolerance_m
        and gymax <= ymax + tolerance_m
    )


def rasterize_observed_masks(spec: GridSpec, perimeter: Any, active_front: Any):
    """Rasterize an already-burned perimeter and its same-time active FEDS front."""
    import numpy as np
    from affine import Affine
    from rasterio.features import rasterize

    if not grid_covers_geometry(spec, perimeter) or not grid_covers_geometry(spec, active_front):
        raise ValueError("The complete initial perimeter/front does not fit inside the fixed map.")
    xmin, _, _, ymax = spec.bounds_m
    transform = Affine(spec.resolution_m, 0, xmin, 0, -spec.resolution_m, ymax)
    scar = rasterize(
        [(perimeter, 1)],
        out_shape=(spec.rows, spec.columns),
        transform=transform,
        fill=0,
        all_touched=True,
        dtype="uint8",
    ).astype(bool)
    front = rasterize(
        [(active_front, 1)],
        out_shape=(spec.rows, spec.columns),
        transform=transform,
        fill=0,
        all_touched=True,
        dtype="uint8",
    ).astype(bool)
    if not scar.any():
        raise ValueError("Initial FEDS perimeter rasterized to an empty burn scar.")
    if not front.any():
        raise ValueError("Initial FEDS active front rasterized to zero 180 m cells.")
    return scar, front, transform
