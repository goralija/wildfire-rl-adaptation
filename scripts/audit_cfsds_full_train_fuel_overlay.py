#!/usr/bin/env python3
"""Overlay the pinned 2014b fuel raster on every feasible full-screen TRAIN pair.

This is a class-compatibility diagnostic for the target-blind 20x20/100 m
windows in ``cfsds-train-full-day-pair-screen.csv``. It does not establish
historical fuel vintage, validate fire behaviour, build simulator cases, or
qualify a benchmark cohort.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import platform
import sys
import warnings
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window
from scipy.ndimage import binary_dilation

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_cfsds_train_fuel import (  # noqa: E402
    FUEL_MAP_MEMBER,
    FUEL_RAT_MEMBER,
    MODEL_CELL_M,
    MODEL_SIZE,
    category_grid,
    edge_cells,
    model_grid_transform,
    reproject_fuel,
    reproject_mask,
    read_dbf_value_labels,
    sha256_file,
    summarize_mask,
)
from build_cfsds_case import build_fuel_mapping  # noqa: E402
from cfsds_initial_state import NODATA_ARRIVAL, derive_pre_target_state_masks  # noqa: E402


DOMAIN_ID = "grid20_cell100m"


def raster_member_bytes(archive: zipfile.ZipFile, member: str) -> bytes:
    path = next((name for name in archive.namelist() if Path(name).name == member), None)
    if path is None:
        raise FileNotFoundError(f"CFSDS raster member {member} is absent")
    return archive.read(path)


def audit_one(
    row: dict[str, str],
    raw_root: Path,
    fuel_source: rasterio.io.DatasetReader,
    mapping: dict[int, int],
    labels: dict[str, Any],
    crop_shape: tuple[int, int],
) -> dict[str, Any]:
    event_id = row["event_id"]
    year = int(row["year"])
    day = int(row["target_doy"])
    raster_zip = raw_root / str(year) / f"{year}_fireDOYrasters.zip"
    member = row["source_raster_member"]
    with zipfile.ZipFile(raster_zip) as archive:
        raster_bytes = raster_member_bytes(archive, member)
    raster_hash = hashlib.sha256(raster_bytes).hexdigest()
    if raster_hash != row["source_raster_sha256"]:
        raise ValueError(f"{event_id}: raster hash differs from the full-screen receipt")

    with rasterio.open(io.BytesIO(raster_bytes)) as source:
        row_off = int(row[f"{DOMAIN_ID}_row_off"])
        col_off = int(row[f"{DOMAIN_ID}_col_off"])
        transform = rasterio.windows.transform(
            Window(col_off, row_off, crop_shape[1], crop_shape[0]), source.transform
        )
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Setting the shape on a NumPy array has been deprecated.*",
                category=DeprecationWarning,
            )
            crop = source.read(
                1,
                window=Window(col_off, row_off, crop_shape[1], crop_shape[0]),
            )
        if crop.shape != crop_shape:
            raise ValueError(f"{event_id}: expected crop {crop_shape}, received {crop.shape}")
        if source.crs is None:
            raise ValueError(f"{event_id}: source raster has no CRS")
        source_crs_text = source.crs.to_string()

        # Keep input-state construction independent of the target day. The
        # helper mirrors the state passed into Cell2Fire: prior scar plus the
        # safe-interior n-1 front; only the separate outcome mask reads day n.
        input_masks = derive_pre_target_state_masks(crop, day, edge_margin_cells=1)
        valid = (crop > 0) & (crop < day) & (crop < NODATA_ARRIVAL)
        observed_target = (crop == day) & (crop < NODATA_ARRIVAL)
        previous_day = (crop == day - 1) & valid
        target_mask = observed_target & binary_dilation(
            previous_day, structure=np.ones((3, 3), dtype=bool)
        )
        counts = {
            "observed_target_pixels": int(observed_target.sum()),
            "target_pixels_adjacent_to_previous_day": int(target_mask.sum()),
            "disconnected_target_pixels": int(observed_target.sum() - target_mask.sum()),
            "previous_day_pixels": int(previous_day.sum()),
            "active_front_pixels": int(input_masks["front"].sum()),
            "earlier_scar_pixels": int(input_masks["scar"].sum()),
        }
        masks = {**input_masks, "target": target_mask}
        model_transform = model_grid_transform({
            "crop_transform": list(transform)[:6],
            "raster_cellsize_m": [float(source.transform.a), float(-source.transform.e)],
            "native_crop_shape_rc": list(crop_shape),
        })
        native_fuel = reproject_fuel(fuel_source, transform, source.crs, crop.shape)
        model_fuel = reproject_fuel(
            fuel_source, model_transform, source.crs, (MODEL_SIZE, MODEL_SIZE)
        )
        native_categories = category_grid(native_fuel, mapping, labels)
        model_categories = category_grid(model_fuel, mapping, labels)
        model_fractions = {
            name: reproject_mask(mask, transform, source.crs, model_transform, (MODEL_SIZE, MODEL_SIZE))
            for name, mask in masks.items()
        }
        fuel_rows = [
            summarize_mask(
                name, masks[name], native_fuel, native_categories,
                model_fractions[name], model_fuel, model_categories,
            )
            for name in ("scar", "front", "target")
        ]

    input_rows = [item for item in fuel_rows if item["mask"] in {"scar", "front"}]
    target_row = next(item for item in fuel_rows if item["mask"] == "target")
    input_bad_native = sum(item["native_90m"]["excluded_or_unmapped_pixels"] for item in input_rows)
    input_bad_majority = sum(item["model_100m"]["excluded_or_unmapped_majority_cells"] for item in input_rows)
    input_fraction_bad_ha = sum(
        item["model_100m"]["excluded_or_unmapped_fractional_area_ha"] for item in input_rows
    )
    target_observed = counts["target_pixels_adjacent_to_previous_day"] > 0
    if input_bad_native or input_bad_majority:
        input_fuel_status = "FAIL_FUEL_CLASS_OVERLAP"
    elif input_fraction_bad_ha > 1e-6:
        input_fuel_status = "REVIEW_SUBCELL_FUEL_OVERLAP"
    else:
        input_fuel_status = "PASS_FUEL_CLASS_OVERLAY_ONLY"

    target_bad_native = target_row["native_90m"]["excluded_or_unmapped_pixels"]
    target_bad_majority = target_row["model_100m"]["excluded_or_unmapped_majority_cells"]
    target_fraction_bad_ha = target_row["model_100m"]["excluded_or_unmapped_fractional_area_ha"]
    if not target_observed:
        target_fuel_status = "NO_ADJACENT_TARGET_MASK_IN_CROP"
    elif target_bad_native or target_bad_majority:
        target_fuel_status = "FAIL_FUEL_CLASS_OVERLAP"
    elif target_fraction_bad_ha > 1e-6:
        target_fuel_status = "REVIEW_SUBCELL_FUEL_OVERLAP"
    else:
        target_fuel_status = "PASS_FUEL_CLASS_OVERLAY_ONLY"

    front_model = model_fractions["front"] >= 0.5
    target_model = model_fractions["target"] >= 0.5
    adjacent = bool(
        np.any(
            front_model
            & binary_dilation(target_model, structure=np.ones((3, 3), dtype=bool))
        )
    )
    target_edge = edge_cells(target_model)
    front_edge = edge_cells(front_model)
    model_pair_valid = bool(
        target_observed
        and target_model.any()
        and front_model.any()
        and adjacent
        and target_edge == 0
        and front_edge == 0
    )
    return {
        "event_id": event_id,
        "year": year,
        "split": "train",
        "input_doy": int(row["input_doy"]),
        "target_doy": day,
        "domain": DOMAIN_ID,
        "source_raster_member": member,
        "source_raster_sha256": raster_hash,
        "native_crop_shape_rc": list(crop_shape),
        "crs": source_crs_text,
        "target_observation_status": row["target_observation_status"],
        "target_pixels_full_raster": int(row["target_pixels_total"]),
        "target_adjacent_pixels_in_crop": counts["target_pixels_adjacent_to_previous_day"],
        "input_fireday_fuel_status": input_fuel_status,
        "input_excluded_native_pixels": input_bad_native,
        "input_excluded_model_majority_cells": input_bad_majority,
        "input_excluded_fractional_area_ha": round(input_fraction_bad_ha, 6),
        "target_fireday_fuel_status": target_fuel_status,
        "target_excluded_native_pixels": target_bad_native,
        "target_excluded_model_majority_cells": target_bad_majority,
        "target_excluded_fractional_area_ha": round(target_fraction_bad_ha, 6),
        "target_day_mask_observed": target_observed,
        "model_grid_pair_valid": model_pair_valid,
        "model_grid_front_edge_cells": front_edge,
        "model_grid_target_edge_cells": target_edge,
        "fuel_by_mask": fuel_rows,
        "fuel_map_vintage": "National FBP fuel-type grid v2014b; historical as-of validity unresolved",
        "suppression_status": "unknown; no agency record joined",
        "full_case_status": "not_assessed; fuel class overlay only",
    }


def audit(args: argparse.Namespace) -> dict[str, Any]:
    screen_doc = json.loads(args.screen_json.read_text(encoding="utf-8"))
    with args.screen_csv.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    expected_rows = int(screen_doc["candidate_pair_details"]["rows"])
    expected_hash = screen_doc["candidate_pair_details"]["sha256"]
    if len(rows) != expected_rows or sha256_file(args.screen_csv) != expected_hash:
        raise ValueError("Full-screen CSV row count or SHA256 does not match its JSON receipt")
    windows = [
        row for row in rows
        if row.get("split", "train") == "train"
        and row.get(f"{DOMAIN_ID}_window_found", "").casefold() == "true"
    ]

    with zipfile.ZipFile(args.fuel_zip) as archive:
        rat = read_dbf_value_labels(archive.read(FUEL_RAT_MEMBER))
    mapping, mapping_report = build_fuel_mapping(rat, args.lookup)
    fuel_vsi = f"/vsizip/{args.fuel_zip.resolve()}/{FUEL_MAP_MEMBER}"
    annual_hashes: dict[str, str] = {}
    with rasterio.open(fuel_vsi) as fuel_source:
        crop_shape = tuple(int(value) for value in screen_doc["domain_options"][DOMAIN_ID]["native_window_shape_rc"])
        cases = []
        for index, row in enumerate(rows, start=1):
            if row.get(f"{DOMAIN_ID}_window_found", "").casefold() != "true":
                cases.append({
                    "event_id": row["event_id"],
                    "year": int(row["year"]),
                    "split": "train",
                    "input_doy": int(row["input_doy"]),
                    "target_doy": int(row["target_doy"]),
                    "domain": DOMAIN_ID,
                    "input_fireday_fuel_status": "NOT_AUDITED_NO_WINDOW",
                    "target_fireday_fuel_status": "NOT_AUDITED_NO_WINDOW",
                    "model_grid_pair_valid": False,
                    "full_case_status": "not_assessed; target-blind window unavailable",
                })
                continue
            year = str(row["year"])
            if year not in annual_hashes:
                annual_hashes[year] = sha256_file(args.raw_root / year / f"{year}_fireDOYrasters.zip")
            try:
                cases.append(audit_one(row, args.raw_root, fuel_source, mapping, mapping_report, crop_shape))
            except Exception as exc:
                cases.append({
                    "event_id": row["event_id"],
                    "year": int(row["year"]),
                    "split": "train",
                    "input_doy": int(row["input_doy"]),
                    "target_doy": int(row["target_doy"]),
                    "domain": DOMAIN_ID,
                    "input_fireday_fuel_status": "ERROR",
                    "target_fireday_fuel_status": "ERROR",
                    "full_case_status": "not_assessed",
                    "error": f"{type(exc).__name__}: {exc}",
                })
            if index % 100 == 0:
                print(f"Processed full-screen rows: {index}/{len(rows)}", flush=True)
        fuel_metadata = {
            "member": FUEL_MAP_MEMBER,
            "raster_attribute_table_member": FUEL_RAT_MEMBER,
            "crs": fuel_source.crs.to_string(),
            "shape": [int(fuel_source.height), int(fuel_source.width)],
            "resolution_m": [float(value) for value in fuel_source.res],
            "nodata": fuel_source.nodata,
            "dtype": fuel_source.dtypes[0],
            "mapping_by_source_code": mapping_report,
        }

    input_counts = Counter(item.get("input_fireday_fuel_status", "UNKNOWN") for item in cases)
    target_counts = Counter(item.get("target_fireday_fuel_status", "UNKNOWN") for item in cases)
    target_observed = sum(bool(item.get("target_day_mask_observed")) for item in cases)
    errors = sum(item.get("input_fireday_fuel_status") == "ERROR" for item in cases)
    return {
        "schema": "cfsds-full-train-fuel-overlay/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Fuel-class spatial compatibility diagnostic for every feasible target-blind full-screen TRAIN day pair.",
        "scope": {
            "split": "train only; 2014-2018",
            "full_screen_pair_count": len(rows),
            "pre_target_windows_available": len(windows),
            "window_unavailable_count": len(rows) - len(windows),
            "fuel_overlay_attempted": sum(item.get("input_fireday_fuel_status") != "NOT_AUDITED_NO_WINDOW" for item in cases),
            "target_masks_observed_after_pair_selection": target_observed,
            "target_day_mapped_somewhere_in_source_raster": sum(
                row["target_observation_status"] == "mapped_pixels_observed" for row in rows
            ),
            "validation_or_test_rasters_opened": False,
            "firegrowth_group_tables_opened": False,
            "simulator_runs_performed": 0,
            "agent_training_performed": False,
            "full_case_or_benchmark_eligible": 0,
        },
        "method": {
            "pair_and_window_source": "All rows from the pinned target-independent full-screen CSV; no event/day selection was changed.",
            "domain": screen_doc["domain_options"][DOMAIN_ID]["grid"],
            "native_window_shape_rc": list(crop_shape),
            "fuel_resampling": "nearest-neighbour categorical lookup on native 90 m crop and 20x20/100 m model grid",
            "fire_mask_rule": "input scar and safe-interior day n-1 front use derive_pre_target_state_masks and read only days before n; adjacent day n target is built separately for post-selection outcome diagnostics; disconnected target pixels are counted separately",
            "spatial_class_gate": "Any excluded/unmapped fuel under a native observed pixel or model majority cell fails; sub-cell fractional overlap is separately marked review.",
            "status_meaning": {
                "PASS_FUEL_CLASS_OVERLAY_ONLY": "No excluded/unmapped class overlap under the audited masks; does not prove map age, historical correctness, fire-behaviour validity, or case eligibility.",
                "FAIL_FUEL_CLASS_OVERLAP": "One or more observed fire pixels or model majority cells overlap water, nonfuel, ambiguous, or unmapped source fuel.",
                "REVIEW_SUBCELL_FUEL_OVERLAP": "No native/majority failure, but area-weighted fire mask overlaps excluded fuel in model sub-cells.",
                "NO_ADJACENT_TARGET_MASK_IN_CROP": "No day-n pixel adjacent to the day-(n-1) footprint was observed inside this crop; this does not mean the full event had no target-day pixels.",
                "NOT_AUDITED_NO_WINDOW": "The fixed target-blind screen could not place the existing 20x20/100 m domain.",
            },
        },
        "provenance": {
            "full_screen_json": args.screen_json.as_posix(),
            "full_screen_json_sha256": sha256_file(args.screen_json),
            "full_screen_csv": args.screen_csv.as_posix(),
            "full_screen_csv_sha256": sha256_file(args.screen_csv),
            "cfsds_annual_raster_zip_sha256": annual_hashes,
            "fuel_zip": args.fuel_zip.name,
            "fuel_zip_sha256": sha256_file(args.fuel_zip),
            "fuel_map": fuel_metadata,
            "cell2fire_lookup": args.lookup.as_posix(),
            "cell2fire_lookup_sha256": sha256_file(args.lookup),
            "audit_script_sha256": sha256_file(Path(__file__)),
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "rasterio": rasterio.__version__,
            "gdal": rasterio.__gdal_version__,
        },
        "summary": {
            "input_fireday_fuel_status_counts": dict(sorted(input_counts.items())),
            "target_fireday_fuel_status_counts": dict(sorted(target_counts.items())),
            "target_observed_mask_count": target_observed,
            "model_grid_pairs_valid": sum(bool(item.get("model_grid_pair_valid")) for item in cases),
            "processing_errors": errors,
            "cases_eligible_for_full_replay_or_policy_evaluation": 0,
            "remaining_blockers": [
                "v2014b source snapshot/cutoff and per-pixel as-of validity are unresolved",
                "terrain/weather lineage and event-level suppression evidence are incomplete",
                "the pre-existing no-action replay gate failed and must be resolved before policy evaluation",
            ],
        },
        "_cases": cases,
        "limitations": [
            "This screen uses the existing 2014b map to test spatial class overlap only. It does not construct annual fuel maps or establish that 2014b represents the event year.",
            "The full-screen CSV's day and window selection is target independent, but target masks are inspected after selection as diagnostics.",
            "CFSDS day-of-burning labels are interpolated daily observations, not hourly truth or suppression records.",
            "A passing class overlay is not a simulator case pass and cannot be used as evidence that an RL agent would reduce real-world damage.",
            "No validation/test source, Firegrowth group table, simulator, benchmark, or training run was opened/performed.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw/cfsds-v1_1"))
    parser.add_argument("--screen-json", type=Path, default=Path("reports/real-fire-data/cfsds-train-full-day-pair-screen.json"))
    parser.add_argument("--screen-csv", type=Path, default=Path("reports/real-fire-data/cfsds-train-full-day-pair-screen.csv"))
    parser.add_argument("--fuel-zip", type=Path, default=Path("data/raw/cwfis-fuels/National_FBP_Fueltypes_version2014b.zip"))
    parser.add_argument("--lookup", type=Path, default=Path("external/firehose/data/Sub20x20/fbp_lookup_table.csv"))
    parser.add_argument("--out", type=Path, default=Path("reports/real-fire-data/cfsds-full-train-fuel-overlay.json"))
    args = parser.parse_args()
    report = audit(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    case_rows = report.pop("_cases")
    case_csv = args.out.with_suffix(".csv")
    with case_csv.open("w", newline="", encoding="utf-8") as stream:
        fields = (
            "event_id", "year", "input_doy", "target_doy", "domain",
            "target_observation_status", "target_pixels_full_raster",
            "target_adjacent_pixels_in_crop", "input_fireday_fuel_status",
            "input_excluded_native_pixels", "input_excluded_model_majority_cells",
            "input_excluded_fractional_area_ha",
            "target_fireday_fuel_status", "model_grid_pair_valid",
            "target_excluded_native_pixels", "target_excluded_model_majority_cells",
            "target_excluded_fractional_area_ha", "model_grid_front_edge_cells",
            "model_grid_target_edge_cells", "error",
        )
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(case_rows)
    report["case_table"] = {
        "file": case_csv.name,
        "rows": len(case_rows),
        "sha256": sha256_file(case_csv),
        "columns": list(fields),
    }
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": args.out.as_posix(),
        "case_csv": args.out.with_suffix(".csv").as_posix(),
        "pairs": report["scope"]["full_screen_pair_count"],
        "overlays": report["scope"]["fuel_overlay_attempted"],
        "input_status": report["summary"]["input_fireday_fuel_status_counts"],
        "target_status": report["summary"]["target_fireday_fuel_status_counts"],
        "errors": report["summary"]["processing_errors"],
        "full_case_eligible": 0,
    }, indent=2))
    return 1 if report["summary"]["processing_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
