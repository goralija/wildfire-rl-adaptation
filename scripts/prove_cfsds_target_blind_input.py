#!/usr/bin/env python3
"""Prove that a TRAIN FireCase crop and InitialState do not depend on day-n shape."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import platform
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.transform import Affine
from rasterio.warp import Resampling, reproject
from rasterio.windows import Window

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cfsds_initial_state import (  # noqa: E402
    NODATA_ARRIVAL,
    derive_pre_target_state_masks,
    initial_state_cells,
    select_target_blind_window,
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def portable_path(path: Path) -> str:
    resolved = path.resolve()
    for base in (ROOT, ROOT.parent.parent if ROOT.parent.name == ".worktrees" else ROOT):
        try:
            return resolved.relative_to(base.resolve()).as_posix()
        except ValueError:
            continue
    return str(path)


def model_fraction(mask: np.ndarray, source_transform: Affine, source_crs: Any, model_transform: Affine) -> np.ndarray:
    fraction = np.zeros((20, 20), dtype=np.float32)
    reproject(
        mask.astype(np.float32), fraction,
        src_transform=source_transform, src_crs=source_crs,
        dst_transform=model_transform, dst_crs=source_crs,
        src_nodata=None, dst_nodata=0,
        resampling=Resampling.average,
    )
    return np.clip(fraction, 0.0, 1.0)


def build_report(event_id: str, target_doy: int, raw_root: Path) -> dict[str, Any]:
    try:
        year_text, _ = event_id.split("_", maxsplit=1)
        year = int(year_text)
    except (ValueError, TypeError) as exc:
        raise ValueError("event_id must have the form TRAIN_YEAR_eventnumber") from exc
    if not 2014 <= year <= 2018:
        raise ValueError(f"Refusing non-train event year {year}")
    if not isinstance(target_doy, int) or not 2 <= target_doy <= 366:
        raise ValueError("target_doy must be an integer in [2, 366]")
    day = target_doy
    archive_path = raw_root / str(year) / f"{year}_fireDOYrasters.zip"
    source_raster = f"{event_id}_krig.tif"
    with zipfile.ZipFile(archive_path) as archive:
        member = next(
            (name for name in archive.namelist() if Path(name).name == source_raster),
            None,
        )
        if member is None:
            raise FileNotFoundError(f"{source_raster} is missing from {archive_path}")
        raster_payload = archive.read(member)

    with rasterio.open(io.BytesIO(raster_payload)) as source:
        arrival = source.read(1)
        raster_transform = source.transform
        source_crs_object = source.crs
        source_crs = source_crs_object.to_string() if source_crs_object else None

    selected = select_target_blind_window(arrival, day, tile_size=23)
    if selected is None:
        raise ValueError(f"No target-blind 23x23 crop exists for {event_id} DOB={day}")
    row, col = int(selected["row_off"]), int(selected["col_off"])
    crop = arrival[row:row + 23, col:col + 23]
    masks = derive_pre_target_state_masks(crop, day)
    masks["target"] = (crop == day) & (crop < NODATA_ARRIVAL)
    crop_transform = rasterio.windows.transform(Window(col, row, 23, 23), raster_transform)
    model_transform = Affine(
        100, 0, crop_transform.c + (23 * 90 - 20 * 100) / 2,
        0, -100, crop_transform.f - (23 * 90 - 20 * 100) / 2,
    )
    model_fraction_before = {
        name: model_fraction(mask, crop_transform, source_crs_object, model_transform)
        for name, mask in masks.items()
    }
    model_burnt_before = model_fraction_before["scar"] >= 0.5
    model_front_before = model_fraction_before["front"] >= 0.5
    model_target_before = model_fraction_before["target"] >= 0.5
    rows_before = initial_state_cells(model_burnt_before, model_front_before)

    original_target = (arrival == day) & (arrival < NODATA_ARRIVAL)
    altered = arrival.copy()
    altered[original_target] = NODATA_ARRIVAL
    pretarget_pixels = (arrival > 0) & (arrival < day) & (arrival < NODATA_ARRIVAL)
    empty_positions = np.argwhere((arrival == 0) | (arrival >= NODATA_ARRIVAL))
    target_count = int(original_target.sum())
    if target_count == 0:
        raise ValueError(f"No target-day pixels exist for {event_id} DOY={day}")
    if len(empty_positions) < target_count:
        raise ValueError("Could not construct an alternate target-mask fixture")
    for target_row, target_col in empty_positions[:target_count]:
        altered[int(target_row), int(target_col)] = day

    alternate = select_target_blind_window(altered, day, tile_size=23)
    if alternate is None:
        raise AssertionError("Changing target geometry unexpectedly removed the pre-target crop")
    alt_row, alt_col = int(alternate["row_off"]), int(alternate["col_off"])
    alternate_crop = altered[alt_row:alt_row + 23, alt_col:alt_col + 23]
    alternate_masks = derive_pre_target_state_masks(alternate_crop, day)
    alternate_masks["target"] = (alternate_crop == day) & (alternate_crop < NODATA_ARRIVAL)
    alternate_transform = rasterio.windows.transform(Window(alt_col, alt_row, 23, 23), raster_transform)
    model_fraction_after = {
        name: model_fraction(mask, alternate_transform, source_crs_object, model_transform)
        for name, mask in alternate_masks.items()
    }
    model_burnt_after = model_fraction_after["scar"] >= 0.5
    model_front_after = model_fraction_after["front"] >= 0.5
    model_target_after = model_fraction_after["target"] >= 0.5
    rows_after = initial_state_cells(model_burnt_after, model_front_after)
    same_window = (row, col) == (alt_row, alt_col)
    same_initial_state = rows_before == rows_after
    same_pre_target_mask = bool(np.array_equal(pretarget_pixels, (altered > 0) & (altered < day) & (altered < NODATA_ARRIVAL)))
    if not (same_window and same_initial_state and same_pre_target_mask):
        raise AssertionError("Target-mask perturbation changed pre-target inputs")

    crop_target = (crop == day) & (crop < NODATA_ARRIVAL)
    crop_previous = (crop == day - 1) & (crop < NODATA_ARRIVAL)
    front_rows, front_cols = np.nonzero(masks["front"])
    front_x, front_y = [], []
    for front_row, front_col in zip(front_rows, front_cols):
        x, y = crop_transform * (float(front_col) + 0.5, float(front_row) + 0.5)
        front_x.append(x)
        front_y.append(y)
    center_x, center_y = float(np.mean(front_x)), float(np.mean(front_y))
    center_lon, center_lat = Transformer.from_crs(
        source_crs_object, "EPSG:4326", always_xy=True
    ).transform(center_x, center_y)
    front_edge_model_cells = int(
        model_front_before[[0, -1], :].sum() + model_front_before[:, [0, -1]].sum()
        - model_front_before[[0, -1], :][:, [0, -1]].sum()
    )
    return {
        "schema": "cfsds-target-blind-input-invariance/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Train-only proof that crop selection and imported initial state are invariant to day-n target-mask changes.",
        "scope": {
            "event_id": event_id,
            "split": "train",
            "year": year,
            "target_doy": day,
            "source_raster_shape_rc": [int(arrival.shape[0]), int(arrival.shape[1])],
            "validation_or_test_rasters_opened": False,
            "simulator_replay_or_training": False,
            "weather_response_or_weather_csv_checked": False,
        },
        "source": {
            "arrival_archive": portable_path(archive_path),
            "arrival_archive_sha256": sha256_file(archive_path),
            "arrival_raster_member": source_raster,
            "arrival_raster_member_sha256": sha256_bytes(raster_payload),
            "crs": source_crs,
        },
        "rule": {
            "version": "cfsds-pretarget-window-front-v1",
            "crop": selected["rule"],
            "active_front": "valid day n-1 pixels in the selected 23x23 crop's one-pixel interior ring",
            "border": "day n-1 pixels on the native crop border are retained as burnt scar, not active front",
            "scar": "all other valid burned pixels strictly before day n",
            "weather_location_basis": "intended lookup point from the safe-interior day n-1 front centroid; actual weather response is outside this proof",
            "intended_weather_lookup_point_wgs84": {"lat": center_lat, "lon": center_lon},
            "target_mask_used_to_choose_crop_or_initial_state": False,
        },
        "selection": {
            "target_blind_crop_row_col": [row, col],
            "target_blind_crop_transform": [
                float(crop_transform.a), float(crop_transform.b), float(crop_transform.c),
                float(crop_transform.d), float(crop_transform.e), float(crop_transform.f),
            ],
            "target_blind_crop_pretarget_pixels": selected["pre_target_pixels_in_window"],
            "target_blind_crop_day_n_minus_1_pixels": selected["day_n_minus_1_pixels_in_window"],
            "target_blind_active_front_pixels": selected["day_n_minus_1_front_pixels_in_window"],
            "target_blind_day_n_minus_1_border_pixels_as_scar": selected["day_n_minus_1_border_pixels_as_burnt_scar"],
            "whole_event_day_n_minus_1_pixels": selected["day_n_minus_1_front_pixels_total"],
            "active_front_capture_fraction": selected["day_n_minus_1_front_capture_ratio"],
            "target_pixels_whole_event": target_count,
            "target_pixels_in_target_blind_crop": int(crop_target.sum()),
            "target_growth_capture_ratio": round(int(crop_target.sum()) / max(target_count, 1), 6),
            "all_day_n_minus_1_pixels_in_crop": int(crop_previous.sum()),
            "pre_target_scar_pixels": int(masks["scar"].sum()),
            "model_grid_cells": {
                "burnt": int(model_burnt_before.sum()),
                "burning": int(model_front_before.sum()),
                "target_truth": int(model_target_before.sum()),
                "initial_state_rows": len(rows_before),
                "active_front_edge_cells": front_edge_model_cells,
                "target_initial_overlap_cells_diagnostic": int(
                    np.count_nonzero(model_target_before & (model_burnt_before | model_front_before))
                ),
            },
        },
        "target_perturbation": {
            "original_target_pixels": target_count,
            "modified_target_pixels": int(((altered == day) & (altered < NODATA_ARRIVAL)).sum()),
            "target_geometry_changed": not np.array_equal(original_target, (altered == day)),
            "crop_offset_unchanged": same_window,
            "pre_target_mask_unchanged": same_pre_target_mask,
            "serialized_initial_state_rows_unchanged": same_initial_state,
            "model_grid_burnt_mask_unchanged": bool(np.array_equal(model_burnt_before, model_burnt_after)),
            "model_grid_active_front_mask_unchanged": bool(np.array_equal(model_front_before, model_front_after)),
            "model_grid_target_truth_changed": not np.array_equal(model_target_before, model_target_after),
            "initial_state_row_count": len(rows_before),
            "status": "PASS_TARGET_MASK_INVARIANCE",
        },
        "limitations": [
            "This proves input-geometry invariance for one TRAIN event, not fire-behavior validity or agent benefit.",
            "The active day-n-1 cells are a daily-front proxy; CFSDS does not identify which cells were flaming at an exact hour.",
            "Target-day coverage is reported only after the target-blind crop is fixed; a low capture ratio makes the event unsuitable for the fixed-size reality-check grid.",
            "This proof fixes one TRAIN event/day for an invariance check; it does not validate how a cohort chooses event-days.",
            "Weather response location/content is not checked; the reported front centroid is only the intended query point.",
        ],
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "rasterio": rasterio.__version__,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-id", default="2018_747")
    parser.add_argument("--target-doy", type=int, default=228)
    parser.add_argument("--raw-root", type=Path, default=ROOT / "data/raw/cfsds-v1_1")
    parser.add_argument("--out", type=Path, default=ROOT / "reports/real-fire-data/cfsds-target-blind-input-invariance.json")
    args = parser.parse_args()
    report = build_report(args.event_id, args.target_doy, args.raw_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
