#!/usr/bin/env python3
"""Screen annual CFSDS maps for compact 20x20 daily-front windows.

This is a data inventory and crop feasibility screen. It does not create
Cell2Fire inputs or claim that the model reproduces historical fire behavior.
"""

from __future__ import annotations

import argparse
import io
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window
from scipy.ndimage import binary_dilation


def box_sums(mask: np.ndarray, size: int) -> np.ndarray:
    integral = np.pad(mask.astype(np.int32), ((1, 0), (1, 0)))
    integral = integral.cumsum(axis=0).cumsum(axis=1)
    return integral[size:, size:] - integral[:-size, size:] - integral[size:, :-size] + integral[:-size, :-size]


def split_for_year(year: int) -> str:
    if year < 2014:
        return "ineligible_pre_fuel_map"
    if year <= 2018:
        return "train"
    if year <= 2021:
        return "validation"
    return "test"


def source_paths(root: Path, year: int) -> tuple[Path, Path]:
    year_dir = root / str(year)
    return (
        year_dir / f"{year}_fireDOYrasters.zip",
        year_dir / f"Firegrowth_groups_v1_1_{year}.zip",
    )


def parse_groups(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"Expected one group CSV in {path}, found {members}")
        with archive.open(members[0]) as stream:
            frame = pd.read_csv(stream)
    required = {"ID", "DOB", "fireday", "firearea", "ffmc", "bui", "ws", "rh", "fwi"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    frame["ID"] = frame["ID"].astype(str)
    frame["DOB"] = pd.to_numeric(frame["DOB"], errors="coerce").astype("Int64")
    return frame


def find_window(arrival: np.ndarray, day: int, tile_size: int) -> dict[str, int] | None:
    h, w = arrival.shape
    if h < tile_size or w < tile_size:
        return None
    nodata_mask = arrival >= 4_000_000_000
    observed_target = (arrival == day) & ~nodata_mask
    previous_day = (arrival == day - 1) & ~nodata_mask
    if not observed_target.any() or not previous_day.any():
        return None
    adjacent = np.ones((3, 3), dtype=bool)
    target = observed_target & binary_dilation(previous_day, structure=adjacent)
    front = previous_day & binary_dilation(target, structure=adjacent)
    if not target.any() or not front.any():
        return None
    # Reject day pairs containing disconnected/spot-fire target pixels.
    if int(target.sum()) != int(observed_target.sum()):
        return None

    target_windows = box_sums(target, tile_size)
    front_windows = box_sums(front, tile_size)
    inner_windows = box_sums(target[1:-1, 1:-1], tile_size - 2)
    inner_front_windows = box_sums(front[1:-1, 1:-1], tile_size - 2)
    if not target_windows.size or not inner_windows.size:
        return None
    edge_windows = target_windows - inner_windows
    front_edge_windows = front_windows - inner_front_windows
    valid = (inner_windows >= 5) & (front_windows >= 3)
    if not valid.any():
        return None
    capture_ppm = np.rint(target_windows / max(int(target.sum()), 1) * 1_000_000).astype(np.int64)
    score = (
        capture_ppm * 1_000_000_000
        - edge_windows.astype(np.int64) * 1_000_000
        - front_edge_windows.astype(np.int64) * 100_000
        + np.minimum(front_windows, 999).astype(np.int64) * 100
        + np.minimum(inner_windows, 999).astype(np.int64)
    )
    score[~valid] = -1
    row, col = np.unravel_index(int(np.argmax(score)), score.shape)
    capture = int(target_windows[row, col]) / max(int(target.sum()), 1)
    if capture < 0.95 or edge_windows[row, col] != 0 or front_edge_windows[row, col] != 0:
        return None
    crop = arrival[row:row + tile_size, col:col + tile_size]
    crop_valid = (crop > 0) & (crop <= day - 1) & (crop < 4_000_000_000)
    return {
        "row_off": int(row),
        "col_off": int(col),
        "target_pixels_in_tile": int(target_windows[row, col]),
        "target_pixels_interior": int(inner_windows[row, col]),
        "target_pixels_on_tile_edge": int(edge_windows[row, col]),
        "active_front_cells": int(front_windows[row, col]),
        "active_front_cells_on_tile_edge": int(front_edge_windows[row, col]),
        "scar_cells": int(np.count_nonzero(crop_valid) - front_windows[row, col]),
        "spot_target_pixels_rejected": 0,
        "target_pixels_in_whole_fire_day": int(target.sum()),
    }


def summarize_year(year: int, raw_root: Path, tile_size: int, top_per_year: int) -> dict[str, Any]:
    rasters_zip, groups_zip = source_paths(raw_root, year)
    if not rasters_zip.is_file() or not groups_zip.is_file():
        raise FileNotFoundError(f"Missing annual CFSDS files for {year}: {rasters_zip}, {groups_zip}")
    groups = parse_groups(groups_zip)
    per_event: dict[str, pd.DataFrame] = {
        name: group.sort_values("DOB")
        for name, group in groups.dropna(subset=["DOB"]).groupby("ID", sort=False)
    }
    annual = {
        "year": year,
        "group_rows": int(len(groups)),
        "fires_in_group_table": int(groups["ID"].nunique()),
        "group_rows_missing_bui": int(groups["bui"].isna().sum()),
        "raster_members": 0,
        "raster_matches": 0,
        "candidate_event_days": 0,
        "events_with_candidate_window": 0,
    }
    event_best: dict[str, dict[str, Any]] = {}
    with zipfile.ZipFile(rasters_zip) as archive:
        raster_names = [name for name in archive.namelist() if name.lower().endswith(".tif")]
        annual["raster_members"] = len(raster_names)
        for member in raster_names:
            event_id = Path(member).name.removesuffix("_krig.tif")
            if event_id not in per_event:
                continue
            annual["raster_matches"] += 1
            event_days = per_event[event_id]
            day_rows = {
                int(row.DOB): row
                for row in event_days.itertuples(index=False)
                if not pd.isna(row.DOB)
            }
            with rasterio.open(io.BytesIO(archive.read(member))) as src:
                arrival = src.read(1)
                observed_days = set(int(value) for value in np.unique(arrival) if 0 < value < 4_000_000_000)
                possible_days = sorted(day for day in observed_days if day - 1 in observed_days and day in day_rows and day - 1 in day_rows)
                if not possible_days:
                    continue
                for day in possible_days:
                    current_row = day_rows[day]
                    if pd.isna(current_row.firearea) or float(current_row.firearea) <= 0:
                        continue
                    annual["candidate_event_days"] += 1
                    window = find_window(arrival, day, tile_size)
                    if window is None:
                        continue
                    capture = window["target_pixels_in_tile"] / max(window["target_pixels_in_whole_fire_day"], 1)
                    candidate = {
                        "event_id": event_id,
                        "year": year,
                        "split": split_for_year(year),
                        "target_doy": day,
                        "target_fireday": int(current_row.fireday),
                        "cfsds_firearea_ha": float(current_row.firearea),
                        "target_ffmc": None if pd.isna(current_row.ffmc) else float(current_row.ffmc),
                        "target_bui": None if pd.isna(current_row.bui) else float(current_row.bui),
                        "target_ws_kmh": None if pd.isna(current_row.ws) else float(current_row.ws),
                        "target_rh_percent": None if pd.isna(current_row.rh) else float(current_row.rh),
                        "target_fwi": None if pd.isna(current_row.fwi) else float(current_row.fwi),
                        "source_raster": Path(member).name,
                        "raster_crs_wkt": src.crs.to_wkt() if src.crs else None,
                        "raster_cellsize_m": [float(src.transform.a), float(-src.transform.e)],
                        "native_crop_shape_rc": [tile_size, tile_size],
                        "simulator_grid_shape_rc": [20, 20],
                        "simulator_cell_size_m": 100,
                        "crop_transform": list(rasterio.windows.transform(Window(window["col_off"], window["row_off"], tile_size, tile_size), src.transform))[:6],
                        "target_growth_capture_ratio": round(capture, 6),
                        "suppression_status": "unknown",
                        "quality_status": "crop-screen-only; external fuel/terrain/hourly weather not yet aligned",
                        **window,
                    }
                    previous = event_best.get(event_id)
                    rank = (
                        window["target_pixels_in_tile"] / max(window["target_pixels_in_whole_fire_day"], 1),
                        -window["target_pixels_on_tile_edge"],
                        -window["active_front_cells_on_tile_edge"],
                        window["active_front_cells"],
                    )
                    if previous is None or rank > previous["_rank"]:
                        candidate["_rank"] = rank
                        event_best[event_id] = candidate
    annual["events_with_candidate_window"] = len(event_best)
    candidates = sorted(
        event_best.values(),
        key=lambda item: (
            item["target_growth_capture_ratio"],
            -item["target_pixels_on_tile_edge"],
            -item["active_front_cells_on_tile_edge"],
            item["active_front_cells"],
        ),
        reverse=True,
    )[:top_per_year]
    for item in candidates:
        item.pop("_rank", None)
    return {"annual": annual, "candidates": candidates}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw/cfsds-v1_1"))
    parser.add_argument("--years", nargs="+", type=int, default=list(range(2014, 2025)))
    parser.add_argument("--tile-size", type=int, default=23)
    parser.add_argument("--top-per-year", type=int, default=5)
    parser.add_argument("--out", type=Path, default=Path("reports/real-fire-data/cfsds-cohort-screen.json"))
    args = parser.parse_args()
    years = sorted(set(args.years))
    reports = [summarize_year(year, args.raw_root, args.tile_size, args.top_per_year) for year in years]
    annual = [item["annual"] for item in reports]
    candidates = [candidate for item in reports for candidate in item["candidates"]]
    counts = Counter(candidate["split"] for candidate in candidates)
    manifest = {
        "dataset": "Canadian Fire Spread Dataset (CFSDS)",
        "release": "v1.1",
        "screened_on": pd.Timestamp.now(tz="UTC").isoformat(),
        "purpose": "identify complete compact historical day-pair windows for a 20x20, 100m Cell2Fire policy grid",
        "not_a_result": "This is crop feasibility only. It is not an aligned simulator case, a physically validated replay, or evidence of policy benefit.",
        "split_rule_by_event_year": "2014-2018 train; 2019-2021 validation; 2022-2024 test. Pre-2014 events are excluded because the published benchmark reports no compatible nationwide FBP map vintage for those years. Each event_id remains in one split.",
        "native_window_cells": args.tile_size,
        "native_resolution_m": 90,
        "simulator_grid_cells": 20,
        "simulator_cell_size_m": 100,
        "window_rule": "reject disconnected spot growth; require at least 5 target-day pixels and 3 active-front pixels; target growth and active front must be wholly within the native window away from its edge, with at least 95% of target-day pixels represented",
        "suppression_status": "unknown unless an event-specific agency record is later joined",
        "annual": annual,
        "screening_candidates": candidates,
        "candidate_count_by_split": dict(counts),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "years": years,
        "fires_in_tables": sum(row["fires_in_group_table"] for row in annual),
        "daily_group_rows": sum(row["group_rows"] for row in annual),
        "rasters": sum(row["raster_members"] for row in annual),
        "matched_rasters": sum(row["raster_matches"] for row in annual),
        "screened_cases": len(candidates),
        "candidate_count_by_split": dict(counts),
        "report": str(args.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
