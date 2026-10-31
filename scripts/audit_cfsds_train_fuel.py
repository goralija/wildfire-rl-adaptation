#!/usr/bin/env python3
"""Audit train-only CFSDS day pairs against the 2014b Canadian FBP fuel map.

This is a fuel-compatibility screen, not a simulator replay or physical validation.
It reports both the native 90 m CFSDS overlay and the 20x20 / 100 m Cell2Fire grid.
"""

from __future__ import annotations

import argparse
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
from rasterio.transform import Affine
from rasterio.windows import Window
from rasterio.warp import Resampling, reproject
from scipy.ndimage import binary_dilation

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_cfsds_case import build_fuel_mapping, daily_row, read_dbf_value_labels  # noqa: E402

NODATA_ARRIVAL = 4_000_000_000
MODEL_SIZE = 20
MODEL_CELL_M = 100.0
NONBURNABLE_GRID_VALUES = {101, 102, 105}
BAD_FUEL_CATEGORIES = {"water", "nonfuel", "ambiguous", "unmapped"}
FUEL_MAP_MEMBER = "nat_fbpfuels_2014b.tif"
FUEL_RAT_MEMBER = "nat_fbpfuels_2014b.tif.vat.dbf"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_label(label: str) -> str:
    return "".join(character for character in label.casefold() if character.isalnum())


def category_for_fuel(source_value: int, mapping: dict[int, int], labels: dict[str, Any]) -> str:
    """Classify an NRCan raster code using the same mapping as the case builder."""
    if source_value == 0 or source_value not in mapping:
        return "unmapped"
    label = str(labels[str(source_value)]["source_label"])
    key = normalized_label(label)
    if key == "water" or mapping[source_value] == 102:
        return "water"
    if key in {"nonfuel", "wetland", "urban"} or mapping[source_value] == 101:
        return "nonfuel"
    if key in {"vegnonfuel", "unknown"} or mapping[source_value] == 105:
        return "ambiguous"
    return "burnable"


def derive_day_pair_masks(arrival: np.ndarray, day: int) -> tuple[dict[str, np.ndarray], dict[str, int]]:
    """Mirror the converter's day n-1/day n masks and expose spot-pixel rejects."""
    valid = arrival < NODATA_ARRIVAL
    observed = (arrival == day) & valid
    previous = (arrival == day - 1) & valid
    target = observed & binary_dilation(previous, structure=np.ones((3, 3), dtype=bool))
    front = previous & binary_dilation(target, structure=np.ones((3, 3), dtype=bool))
    scar = (arrival > 0) & (arrival <= day - 1) & valid & ~front
    counts = {
        "observed_target_pixels": int(observed.sum()),
        "target_pixels_adjacent_to_previous_day": int(target.sum()),
        "disconnected_target_pixels": int(observed.sum() - target.sum()),
        "previous_day_pixels": int(previous.sum()),
        "active_front_pixels": int(front.sum()),
        "earlier_scar_pixels": int(scar.sum()),
    }
    return {"scar": scar, "front": front, "target": target}, counts


def model_grid_transform(candidate: dict[str, Any]) -> Affine:
    source_transform = Affine(*candidate["crop_transform"])
    source_width = float(candidate["raster_cellsize_m"][0])
    source_height = float(candidate["raster_cellsize_m"][1])
    rows, cols = candidate["native_crop_shape_rc"]
    offset_x = (cols * source_width - MODEL_SIZE * MODEL_CELL_M) / 2
    offset_y = (rows * source_height - MODEL_SIZE * MODEL_CELL_M) / 2
    return Affine(
        MODEL_CELL_M, 0, source_transform.c + offset_x,
        0, -MODEL_CELL_M, source_transform.f - offset_y,
    )


def reproject_mask(
    mask: np.ndarray,
    src_transform: Affine,
    src_crs: Any,
    dst_transform: Affine,
    dst_shape: tuple[int, int],
) -> np.ndarray:
    destination = np.zeros(dst_shape, dtype=np.float32)
    reproject(
        mask.astype(np.float32), destination,
        src_transform=src_transform, src_crs=src_crs,
        dst_transform=dst_transform, dst_crs=src_crs,
        src_nodata=None, dst_nodata=0,
        resampling=Resampling.average,
    )
    return np.clip(destination, 0.0, 1.0)


def reproject_fuel(
    fuel_source: rasterio.io.DatasetReader,
    transform: Affine,
    crs: Any,
    shape: tuple[int, int],
) -> np.ndarray:
    destination = np.zeros(shape, dtype=np.uint16)
    reproject(
        rasterio.band(fuel_source, 1), destination,
        src_transform=fuel_source.transform, src_crs=fuel_source.crs,
        src_nodata=fuel_source.nodata,
        dst_transform=transform, dst_crs=crs,
        dst_nodata=0, resampling=Resampling.nearest,
    )
    return destination


def category_grid(source_grid: np.ndarray, mapping: dict[int, int], labels: dict[str, Any]) -> np.ndarray:
    categories = np.full(source_grid.shape, "unmapped", dtype="U12")
    for value in np.unique(source_grid):
        source_value = int(value)
        categories[source_grid == value] = category_for_fuel(source_value, mapping, labels)
    return categories


def summarize_mask(
    mask_name: str,
    native_mask: np.ndarray,
    native_source_fuel: np.ndarray,
    native_categories: np.ndarray,
    model_fraction: np.ndarray,
    model_source_fuel: np.ndarray,
    model_categories: np.ndarray,
) -> dict[str, Any]:
    native_pixels = int(native_mask.sum())
    native_counts: Counter[str] = Counter(
        str(value) for value in native_categories[native_mask].tolist()
    )
    native_source_counts: Counter[str] = Counter(
        str(int(value)) for value in native_source_fuel[native_mask].tolist()
    )
    majority = model_fraction >= 0.5
    weighted_area_ha = model_fraction * (MODEL_CELL_M * MODEL_CELL_M / 10_000.0)
    model_counts: Counter[str] = Counter(
        str(value) for value in model_categories[majority].tolist()
    )
    fraction_area_by_category = {
        category: round(float(weighted_area_ha[model_categories == category].sum()), 6)
        for category in ("burnable", "water", "nonfuel", "ambiguous", "unmapped")
    }
    bad_native = sum(native_counts.get(category, 0) for category in BAD_FUEL_CATEGORIES)
    bad_majority = sum(model_counts.get(category, 0) for category in BAD_FUEL_CATEGORIES)
    bad_fractional_area = sum(fraction_area_by_category[key] for key in BAD_FUEL_CATEGORIES)
    return {
        "mask": mask_name,
        "native_90m": {
            "pixels": native_pixels,
            "pixels_by_fuel_category": dict(sorted(native_counts.items())),
            "pixels_by_source_fuel_code": dict(sorted(native_source_counts.items(), key=lambda item: int(item[0]))),
            "excluded_or_unmapped_pixels": int(bad_native),
        },
        "model_100m": {
            "area_equivalent_ha": round(float(weighted_area_ha.sum()), 6),
            "majority_cells": int(majority.sum()),
            "majority_cells_by_fuel_category": dict(sorted(model_counts.items())),
            "cells_with_any_fraction_by_fuel_category": {
                category: int(np.count_nonzero((model_fraction > 0) & (model_categories == category)))
                for category in ("burnable", "water", "nonfuel", "ambiguous", "unmapped")
            },
            "fractional_area_equivalent_ha_by_fuel_category": fraction_area_by_category,
            "excluded_or_unmapped_majority_cells": int(bad_majority),
            "excluded_or_unmapped_fractional_area_ha": round(float(bad_fractional_area), 6),
        },
        "strict_fuel_compatibility": not bool(bad_native or bad_majority),
    }


def edge_cells(mask: np.ndarray) -> int:
    edge = np.zeros(mask.shape, dtype=bool)
    edge[[0, -1], :] = True
    edge[:, [0, -1]] = True
    return int(np.count_nonzero(mask & edge))


def process_candidate(
    candidate: dict[str, Any],
    raw_root: Path,
    fuel_source: rasterio.io.DatasetReader,
    mapping: dict[int, int],
    labels: dict[str, Any],
    source_hashes: dict[str, dict[str, str]],
) -> dict[str, Any]:
    event_id = str(candidate["event_id"])
    year = int(candidate["year"])
    day = int(candidate["target_doy"])
    raster_zip = raw_root / str(year) / f"{year}_fireDOYrasters.zip"
    member = str(candidate["source_raster"])
    with zipfile.ZipFile(raster_zip) as archive:
        archive_member = next((name for name in archive.namelist() if Path(name).name == member), None)
        if archive_member is None:
            raise FileNotFoundError(f"{member} is absent from {raster_zip.name}")
        raster_bytes = archive.read(archive_member)
    if str(year) not in source_hashes["raster_zip"]:
        source_hashes["raster_zip"][str(year)] = sha256_file(raster_zip)
    group_zip = raw_root / str(year) / f"Firegrowth_groups_v1_1_{year}.zip"
    if str(year) not in source_hashes["groups_zip"]:
        source_hashes["groups_zip"][str(year)] = sha256_file(group_zip)

    with rasterio.open(io.BytesIO(raster_bytes)) as source:
        rows, cols = (int(value) for value in candidate["native_crop_shape_rc"])
        transform = Affine(*candidate["crop_transform"])
        with warnings.catch_warnings():
            # rasterio 1.4.x currently triggers this NumPy 2.5 deprecation when
            # reading a window; the returned crop shape is checked immediately.
            warnings.filterwarnings(
                "ignore",
                message="Setting the shape on a NumPy array has been deprecated.*",
                category=DeprecationWarning,
            )
            crop = source.read(1, window=Window(candidate["col_off"], candidate["row_off"], cols, rows))
        if crop.shape != (rows, cols):
            raise ValueError(f"{event_id}: CFSDS crop shape {crop.shape}, expected {(rows, cols)}")
        crs = source.crs
        if crs is None:
            raise ValueError(f"{event_id}: CFSDS source raster has no CRS")
        masks, pair_counts = derive_day_pair_masks(crop, day)
        model_transform = model_grid_transform(candidate)
        native_fuel = reproject_fuel(fuel_source, transform, crs, crop.shape)
        model_fuel = reproject_fuel(fuel_source, model_transform, crs, (MODEL_SIZE, MODEL_SIZE))
        native_categories = category_grid(native_fuel, mapping, labels)
        model_categories = category_grid(model_fuel, mapping, labels)
        model_fractions = {
            name: reproject_mask(mask, transform, crs, model_transform, (MODEL_SIZE, MODEL_SIZE))
            for name, mask in masks.items()
        }

        masks_summary = [
            summarize_mask(
                name, masks[name], native_fuel, native_categories,
                model_fractions[name], model_fuel, model_categories,
            )
            for name in ("scar", "front", "target")
        ]
        summary_row = daily_row(raw_root, event_id, year, day)
        reported_growth = float(candidate["cfsds_firearea_ha"])
        source_growth = float(summary_row["firearea"])
        growth_matches = bool(np.isclose(reported_growth, source_growth, rtol=0, atol=1e-5))
        native_bad = sum(row["native_90m"]["excluded_or_unmapped_pixels"] for row in masks_summary)
        model_bad = sum(row["model_100m"]["excluded_or_unmapped_majority_cells"] for row in masks_summary)
        fractional_bad_ha = sum(row["model_100m"]["excluded_or_unmapped_fractional_area_ha"] for row in masks_summary)
        fractional_review = fractional_bad_ha > 1e-6
        pair_ok = (
            pair_counts["observed_target_pixels"] > 0
            and pair_counts["active_front_pixels"] > 0
            and pair_counts["disconnected_target_pixels"] == 0
        )
        front_model = model_fractions["front"] >= 0.5
        target_model = model_fractions["target"] >= 0.5
        adjacent_model = bool(np.any(front_model & binary_dilation(target_model, structure=np.ones((3, 3), dtype=bool))))
        target_edge = edge_cells(target_model)
        front_edge = edge_cells(front_model)
        model_pair_ok = bool(target_model.any() and front_model.any() and adjacent_model and target_edge == 0 and front_edge == 0)
        errors = []
        if not growth_matches:
            errors.append("screen and annual group-table firearea differ")
        if not pair_ok:
            errors.append("CFSDS day-pair no longer matches the geometry screen")
        if not model_pair_ok:
            errors.append("majority-resampled target/front is missing, nonadjacent, or touches the model-grid edge")
        if native_bad or model_bad:
            fuel_status = "FAIL_FUEL_OVERLAP"
        elif fractional_review:
            fuel_status = "REVIEW_SUBCELL_FUEL_OVERLAP"
        else:
            fuel_status = "PASS_FUEL_ONLY"

        return {
            "event_id": event_id,
            "year": year,
            "target_doy": day,
            "target_fireday": int(candidate["target_fireday"]),
            "split": candidate["split"],
            "fuel_map_vintage": "National FBP fuel-type grid v2014b",
            "source_raster_member": archive_member,
            "source_raster_sha256": hashlib.sha256(raster_bytes).hexdigest(),
            "source_grid": {
                "rows": int(crop.shape[0]),
                "cols": int(crop.shape[1]),
                "cell_size_m": candidate["raster_cellsize_m"],
                "crs": crs.to_string(),
                "transform": list(transform)[:6],
            },
            "model_grid": {
                "rows": MODEL_SIZE,
                "cols": MODEL_SIZE,
                "cell_size_m": MODEL_CELL_M,
                "extent_m": MODEL_SIZE * MODEL_CELL_M,
                "transform": list(model_transform)[:6],
                "target_majority_edge_cells": target_edge,
                "front_majority_edge_cells": front_edge,
                "majority_target_front_adjacent": adjacent_model,
            },
            "screen_crosscheck": {
                "screen_growth_ha": reported_growth,
                "annual_group_table_growth_ha": source_growth,
                "growth_matches": growth_matches,
                "geometry_growth_capture_ratio": candidate["target_growth_capture_ratio"],
                "day_pair_counts": pair_counts,
                "day_pair_valid": pair_ok,
                "model_grid_pair_valid": model_pair_ok,
            },
            "fuel_by_mask": masks_summary,
            "fuel_status": fuel_status,
            "suppression_status": "unknown; no agency record joined",
            "full_case_status": "not_assessed; terrain, weather/FWI, suppression, and replay are outside this fuel-only audit",
            "screening_errors": errors,
            "model_grid_fractional_fuel_overlap_requires_review": fractional_review,
        }


def audit(args: argparse.Namespace) -> dict[str, Any]:
    cohort = json.loads(args.cohort.read_text())
    screen = json.loads(args.screen.read_text())
    expected = cohort["selection"]["candidate_day_pairs_by_split"]["train"]
    expected_by_key = {(str(item["event_id"]), int(item["target_doy"])): item for item in expected}
    screen_by_key = {
        (str(item["event_id"]), int(item["target_doy"])): item
        for item in screen["screening_candidates"]
        if item.get("split") == "train"
    }
    missing = sorted(set(expected_by_key) - set(screen_by_key))
    if missing:
        raise ValueError(f"Train cohort candidates missing from crop screen: {missing}")
    candidates = [screen_by_key[key] for key in sorted(expected_by_key)]

    with zipfile.ZipFile(args.fuel_zip) as archive:
        rat = read_dbf_value_labels(archive.read(FUEL_RAT_MEMBER))
    mapping, mapping_report = build_fuel_mapping(rat, args.lookup)
    fuel_vsi = f"/vsizip/{args.fuel_zip.resolve()}/{FUEL_MAP_MEMBER}"
    yearly_source_hashes: dict[str, dict[str, str]] = {"raster_zip": {}, "groups_zip": {}}
    with rasterio.open(fuel_vsi) as fuel_source:
        results = []
        for candidate in candidates:
            try:
                results.append(process_candidate(candidate, args.raw_root, fuel_source, mapping, mapping_report, yearly_source_hashes))
            except Exception as exc:  # retain the candidate and make the failure auditable
                results.append({
                    "event_id": str(candidate["event_id"]),
                    "year": int(candidate["year"]),
                    "target_doy": int(candidate["target_doy"]),
                    "split": str(candidate.get("split", "unknown")),
                    "fuel_map_vintage": "National FBP fuel-type grid v2014b",
                    "fuel_status": "ERROR",
                    "full_case_status": "not_assessed",
                    "suppression_status": "unknown; no agency record joined",
                    "error": f"{type(exc).__name__}: {exc}",
                })
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

    status_counts = Counter(str(item["fuel_status"]) for item in results)
    error_count = sum(item["fuel_status"] == "ERROR" for item in results)
    return {
        "schema": "cfsds-train-fuel-qc/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "strict train-only fuel compatibility screen before additional simulator cases or any calibration",
        "scope": {
            "split": "train only",
            "candidate_count_expected": len(expected),
            "candidate_count_audited": len(results),
            "all_split_cohort_metadata_loaded": True,
            "all_split_crop_screen_metadata_loaded": True,
            "validation_or_test_rasters_opened": False,
            "validation_or_test_candidates_fuel_audited": False,
            "simulator_runs_performed": 0,
            "agent_training_performed": False,
        },
        "method": {
            "cfsds_reference": "Barber et al. 2024, CFSDS v1.1; https://doi.org/10.1038/s41597-024-03436-4",
            "fuel_qc_reference": "Bennett et al. 2026, W.I.S.E. assessment; https://doi.org/10.1071/WF26072",
            "published_filter_inspiration": "Bennett et al. report filtering burned-pixel overlap with water/non-fuel and ambiguous FBP classes; this project implements a separate, stricter project-specific train gate and does not claim to reproduce W.I.S.E.",
            "native_rule": "CFSDS day n-1 scar/front and day n target are reconstructed from day-of-burning values, then compared against 2014b fuel classes resampled nearest-neighbour to the native 90 m crop.",
            "model_rule": "The same masks are area-averaged to the centered 20x20, 100 m model grid; the 2014b categorical map is nearest-neighbour resampled, matching build_cfsds_case.py. Initial-state and target majority cells on non-burnable/ambiguous/unmapped classes fail the fuel gate.",
            "fractional_rule": "Sub-50% observed coverage on excluded fuel is reported in hectares and marked review; it is not silently rounded into a pass.",
            "categories": {
                "burnable": "mapped FBP class supported by the pinned Cell2Fire lookup table",
                "water": "source label Water or simulator grid code 102",
                "nonfuel": "source label Non-fuel/Wetland/Urban or simulator grid code 101",
                "ambiguous": "Vegetated Non-fuel/Unknown or simulator grid code 105",
                "unmapped": "no-data, unrecognised source class, or missing map coverage",
            },
            "fuel_status_meaning": {
                "PASS_FUEL_ONLY": "no native-pixel or model-majority overlap with excluded/unmapped fuel; not a full-case pass",
                "FAIL_FUEL_OVERLAP": "at least one native fire pixel or model-majority state/target cell overlaps excluded/unmapped fuel",
                "REVIEW_SUBCELL_FUEL_OVERLAP": "no majority-cell failure, but fractional model-grid fire coverage overlaps excluded/unmapped fuel",
                "ERROR": "source data or processing check failed; candidate is retained with error detail",
            },
        },
        "input_provenance": {
            "cohort_manifest": "data/manifests/cfsds-v1_1-pilot-cohort.json",
            "cohort_manifest_sha256": sha256_file(args.cohort),
            "crop_screen": "reports/real-fire-data/cfsds-cohort-screen.json",
            "crop_screen_sha256": sha256_file(args.screen),
            "fuel_map_zip": args.fuel_zip.name,
            "fuel_map_zip_sha256": sha256_file(args.fuel_zip),
            "fuel_map": fuel_metadata,
            "cell2fire_lookup": "external/firehose/data/Sub20x20/fbp_lookup_table.csv",
            "cell2fire_lookup_sha256": sha256_file(args.lookup),
            "cfsds_annual_source_zip_sha256": yearly_source_hashes,
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
            "fuel_status_counts": dict(sorted(status_counts.items())),
            "candidate_processing_errors": error_count,
            "cases_with_unknown_suppression": len(results),
            "eligible_for_full_replay_or_policy_evaluation": 0,
            "reason_full_replay_gate_remains_open": "This audit checks fuel only; suppression, terrain, weather/FWI, crop extent, and no-action behavior remain separate gates.",
        },
        "cases": results,
        "limitations": [
            "The 2014b map is the available training-period vintage; this does not establish that it represents historical annual fuel succession for every event.",
            "Native CFSDS pixels and the 100 m Cell2Fire policy cells have different spatial supports; both are reported rather than treated as interchangeable.",
            "CFSDS day-of-burning is a satellite-hotspot interpolation and not hourly ground truth.",
            "Suppression status remains unknown for every candidate; a fuel-pass does not imply an unsuppressed event or a complete simulator case.",
            "The combined crop-screen JSON contains all splits and was loaded to select train rows; no validation/test fuel or source rasters were opened, and no validation/test candidate received a fuel overlay.",
            "No simulator replay was run, and no model parameters were calibrated.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw/cfsds-v1_1"))
    parser.add_argument("--cohort", type=Path, default=Path("data/manifests/cfsds-v1_1-pilot-cohort.json"))
    parser.add_argument("--screen", type=Path, default=Path("reports/real-fire-data/cfsds-cohort-screen.json"))
    parser.add_argument("--fuel-zip", type=Path, default=Path("data/raw/cwfis-fuels/National_FBP_Fueltypes_version2014b.zip"))
    parser.add_argument("--lookup", type=Path, default=Path("external/firehose/data/Sub20x20/fbp_lookup_table.csv"))
    parser.add_argument("--out", type=Path, default=Path("reports/real-fire-data/cfsds-train-fuel-qc.json"))
    args = parser.parse_args()
    report = audit(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "report": args.out.as_posix(),
        "candidates": report["scope"]["candidate_count_audited"],
        "fuel_status_counts": report["summary"]["fuel_status_counts"],
        "errors": report["summary"]["candidate_processing_errors"],
        "full_replay_eligible": report["summary"]["eligible_for_full_replay_or_policy_evaluation"],
    }, indent=2))
    return 1 if report["summary"]["candidate_processing_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
