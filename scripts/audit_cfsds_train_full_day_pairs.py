#!/usr/bin/env python3
"""Audit every 2014–2018 CFSDS raster using an outcome-independent day rule.

For each fire, select the earliest arrival day with at least three valid native
pixels as the observed input day and the following calendar day as the target.
The target mask is scored only after this pair has been fixed. No group-table
weather, fire-area, target-record, or target-geometry fields enter selection.
This is a TRAIN-only geometry screen, not a FireCase builder or simulator run.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import io
import json
import math
import warnings
import zipfile
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

try:
    from .cfsds_initial_state import NODATA_ARRIVAL
    from .cfsds_spatial_feasibility import (
        evaluate_target_blind_window,
        native_window_shape,
    )
except ImportError:  # pragma: no cover - direct CLI invocation
    from cfsds_initial_state import NODATA_ARRIVAL
    from cfsds_spatial_feasibility import (
        evaluate_target_blind_window,
        native_window_shape,
    )


GRID_OPTIONS: tuple[dict[str, Any], ...] = (
    {"id": "grid20_cell100m", "rows": 20, "cols": 20, "cell_size_m": 100},
    {"id": "grid20_cell150m", "rows": 20, "cols": 20, "cell_size_m": 150},
    {"id": "grid20_cell200m", "rows": 20, "cols": 20, "cell_size_m": 200},
    {"id": "grid20_cell300m", "rows": 20, "cols": 20, "cell_size_m": 300},
    {"id": "grid40_cell100m", "rows": 40, "cols": 40, "cell_size_m": 100},
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def earliest_day_with_minimum_pixels(
    arrival: np.ndarray,
    *,
    min_pixels: int = 3,
    nodata: int = NODATA_ARRIVAL,
) -> int | None:
    """Choose the first arrival day with enough observed native raster cells."""
    values = np.asarray(arrival)
    if values.ndim != 2:
        raise ValueError("arrival must be a two-dimensional raster")
    if min_pixels < 1:
        raise ValueError("min_pixels must be positive")
    valid = values[(values > 0) & (values < int(nodata))]
    if not valid.size:
        return None
    days, counts = np.unique(valid, return_counts=True)
    eligible = days[counts >= min_pixels]
    return int(eligible[0]) if eligible.size else None


def no_window(reason: str, shape: tuple[int, int]) -> dict[str, Any]:
    return {
        "window_found": False,
        "window_unavailable_reason": reason,
        "source_raster_shape_rc": [int(shape[0]), int(shape[1])],
        "target_geometry_used_for_window_selection": False,
    }


def summarize_domain(
    candidates: list[dict[str, Any]], option_id: str
) -> dict[str, Any]:
    domain_rows = [row["domains"][option_id] for row in candidates]
    valid_windows = [row for row in domain_rows if row["window_found"]]
    target_mapped = [
        case
        for case in candidates
        if case.get("target_observation_status") == "mapped_pixels_observed"
    ]
    scored = [
        row["target_capture_ratio"]
        for row in domain_rows
        if row["window_found"] and row.get("target_capture_ratio") is not None
    ]
    safe_scored = [
        row["target_safe_interior_capture_ratio"]
        for row in domain_rows
        if row["window_found"]
        and row.get("target_safe_interior_capture_ratio") is not None
    ]
    front = [
        row["day_n_minus_1_front_capture_ratio"]
        for row in valid_windows
        if row.get("day_n_minus_1_front_capture_ratio") is not None
    ]
    unavailable_reasons = Counter(
        row.get("window_unavailable_reason", "unspecified")
        for row in domain_rows
        if not row["window_found"]
    )
    return {
        "candidate_pairs": len(domain_rows),
        "pre_target_window_found": len(valid_windows),
        "window_found_rate": round(len(valid_windows) / len(domain_rows), 6)
        if domain_rows
        else None,
        "window_unavailable_reasons": dict(sorted(unavailable_reasons.items())),
        "target_observed_pairs": len(target_mapped),
        "target_unobserved_pairs": sum(
            row.get("target_observation_status") != "mapped_pixels_observed"
            for row in candidates
        ),
        "target_observed_but_window_unavailable": sum(
            case.get("target_observation_status") == "mapped_pixels_observed"
            and not domain["window_found"]
            for case, domain in zip(candidates, domain_rows, strict=True)
        ),
        "observed_target_pairs_with_any_pixel_in_window": sum(
            int(domain.get("target_pixels_in_window", 0)) > 0
            for case, domain in zip(candidates, domain_rows, strict=True)
            if case.get("target_observation_status") == "mapped_pixels_observed"
        ),
        "observed_target_pairs_with_any_safe_interior_pixel": sum(
            int(domain.get("target_pixels_in_safe_interior", 0)) > 0
            for case, domain in zip(candidates, domain_rows, strict=True)
            if case.get("target_observation_status") == "mapped_pixels_observed"
        ),
        "target_capture_ratio_denominator": len(scored),
        "median_target_capture_ratio_among_observed_targets": round(
            float(np.median(scored)), 6
        )
        if scored
        else None,
        "p75_target_capture_ratio_among_observed_targets": round(
            float(np.quantile(scored, 0.75)), 6
        )
        if scored
        else None,
        "maximum_target_capture_ratio_among_observed_targets": round(max(scored), 6)
        if scored
        else None,
        "median_safe_interior_target_capture_ratio_among_observed_targets": round(
            float(np.median(safe_scored)), 6
        )
        if safe_scored
        else None,
        "median_day_n_minus_1_front_capture_ratio": round(float(np.median(front)), 6)
        if front
        else None,
        "target_metrics_are_post_selection_diagnostics": True,
        "capture_ratios_exclude_pairs_without_mapped_target_pixels": True,
    }


def scan(*, raw_root: Path) -> dict[str, Any]:
    years = tuple(range(2014, 2019))
    archives: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    counts_by_year: dict[str, dict[str, int]] = {}
    for year in years:
        archive_path = raw_root / str(year) / f"{year}_fireDOYrasters.zip"
        if not archive_path.is_file():
            raise FileNotFoundError(f"Missing TRAIN arrival archive: {archive_path}")
        archives.append(
            {
                "year": year,
                "filename": archive_path.name,
                "sha256": sha256_file(archive_path),
            }
        )
        year_counts = Counter()
        with zipfile.ZipFile(archive_path) as archive:
            members = sorted(
                name
                for name in archive.namelist()
                if name.lower().endswith(".tif")
            )
            year_counts["rasters_scanned"] = len(members)
            for index, member in enumerate(members, start=1):
                raster_bytes = archive.read(member)
                with rasterio.open(io.BytesIO(raster_bytes)) as source:
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            "ignore",
                            message="Setting the shape on a NumPy array has been deprecated",
                            category=DeprecationWarning,
                        )
                        arrival = source.read(1)
                    cell_x, cell_y = abs(float(source.transform.a)), abs(
                        float(source.transform.e)
                    )
                    if not math.isclose(cell_x, cell_y, rel_tol=0, abs_tol=1e-6):
                        raise ValueError(
                            f"Non-square CFSDS cells for {member}: {cell_x}x{cell_y}"
                        )
                    if not math.isclose(cell_x, 90.0, rel_tol=0, abs_tol=1e-6):
                        raise ValueError(
                            f"Unexpected CFSDS native resolution for {member}: {cell_x}m"
                        )
                    event_id = Path(member).name.removesuffix("_krig.tif")
                    valid_count = int(
                        ((arrival > 0) & (arrival < NODATA_ARRIVAL)).sum()
                    )
                    input_doy = earliest_day_with_minimum_pixels(arrival)
                    inv = {
                        "event_id": event_id,
                        "year": year,
                        "source_raster_member": member,
                        "source_raster_sha256": sha256_bytes(raster_bytes),
                        "source_raster_shape_rc": [int(x) for x in arrival.shape],
                        "valid_arrival_pixels_total": valid_count,
                    }
                    if input_doy is None:
                        inv.update(
                            {
                                "pair_status": "no_pair",
                                "pair_exclusion_reason": "no_day_has_at_least_three_valid_pixels",
                            }
                        )
                        inventory.append(inv)
                        year_counts["rasters_without_pair"] += 1
                        continue

                    year_counts["rasters_with_pair"] += 1
                    year_length = 366 if calendar.isleap(year) else 365
                    if input_doy > year_length:
                        raise ValueError(
                            f"Invalid input DOY {input_doy} in {year} raster {member}"
                        )
                    target_date = date(year, 1, 1) + timedelta(days=input_doy)
                    target_in_same_archive = input_doy < year_length
                    target_doy = input_doy + 1 if target_in_same_archive else None
                    if target_in_same_archive:
                        target_pixels = int((arrival == target_doy).sum())
                        target_status = (
                            "mapped_pixels_observed"
                            if target_pixels > 0
                            else "no_mapped_pixels_on_next_day"
                        )
                    else:
                        target_pixels = None
                        target_status = "next_day_outside_annual_archive"

                    # Removing target-day and later observations must not change
                    # the pair already selected from the earliest qualifying day.
                    counterfactual = arrival.copy()
                    counterfactual[(counterfactual > input_doy) & (counterfactual < NODATA_ARRIVAL)] = NODATA_ARRIVAL
                    invariant_doy = earliest_day_with_minimum_pixels(counterfactual)
                    if invariant_doy != input_doy:
                        raise AssertionError(
                            f"Pair selection depends on future pixels for {event_id}"
                        )

                    if target_doy is None:
                        domains = {
                            option["id"]: no_window(
                                "target_crosses_annual_archive_boundary", arrival.shape
                            )
                            for option in GRID_OPTIONS
                        }
                    else:
                        domains = {
                            option["id"]: evaluate_target_blind_window(
                                arrival,
                                target_doy,
                                grid_rows=int(option["rows"]),
                                grid_cols=int(option["cols"]),
                                cell_size_m=float(option["cell_size_m"]),
                                native_cell_size_m=cell_x,
                            )
                            for option in GRID_OPTIONS
                        }

                    input_date = date(year, 1, 1) + timedelta(days=input_doy - 1)
                    case = {
                        **inv,
                        "pair_status": "pair_selected",
                        "input_doy": input_doy,
                        "input_calendar_date": input_date.isoformat(),
                        "target_doy": target_doy,
                        "target_calendar_date": target_date.isoformat(),
                        "target_observation_status": target_status,
                        "target_pixels_total": target_pixels,
                        "input_pixels_on_selected_day": int((arrival == input_doy).sum()),
                        "selection_invariant_after_target_and_future_pixel_removal": True,
                        "pair_selection_uses_target_geometry": False,
                        "pair_selection_uses_group_table_or_firearea": False,
                        "target_metrics_are_post_selection_diagnostics": True,
                        "domains": domains,
                    }
                    candidates.append(case)
                if index % 100 == 0:
                    print(f"Scanned {year}: {index}/{len(members)} CFSDS rasters")
        counts_by_year[str(year)] = dict(sorted(year_counts.items()))

    domain_summaries: dict[str, Any] = {}
    for option in GRID_OPTIONS:
        tile_shape = native_window_shape(
            int(option["rows"]), int(option["cols"]), float(option["cell_size_m"])
        )
        domain_summaries[option["id"]] = {
            "grid": option,
            "requested_extent_m": [
                int(option["rows"]) * int(option["cell_size_m"]),
                int(option["cols"]) * int(option["cell_size_m"]),
            ],
            "native_window_shape_rc": list(tile_shape),
            "realized_extent_m": [tile_shape[0] * 90, tile_shape[1] * 90],
            "safe_edge_margin_native_pixels": max(
                1, int(math.floor(float(option["cell_size_m"]) / 90 + 0.5))
            ),
            "existing_20x20_checkpoint_compatible_by_tensor_shape": (
                int(option["rows"]) == 20 and int(option["cols"]) == 20
            ),
            "physical_cell_semantics_match_existing_100m_case": int(
                option["cell_size_m"]
            )
            == 100,
            "summary": summarize_domain(candidates, option["id"]),
        }

    return {
        "dataset": "Canadian Fire Spread Dataset (CFSDS)",
        "release": "v1.1",
        "scope": "train_only",
        "event_years": list(years),
        "heldout_splits_opened": False,
        "selection_rule": {
            "input_day": "earliest DOY whose raster has at least three valid native 90m fire-arrival pixels",
            "target_day": "the next calendar day after the selected input day",
            "valid_arrival_predicate": f"0 < arrival_doy < {NODATA_ARRIVAL}",
            "minimum_input_day_pixels": 3,
            "requires_target_day_raster_pixels": False,
            "requires_group_table_row_or_positive_firearea": False,
            "target_geometry_used_for_pair_membership": False,
            "window_rule": "for each fixed domain, select a crop from input-day and older pixels only; require at least three input-day pixels in the safe interior; then score target pixels",
            "selection_invariance_check": "remove all arrival pixels after the selected input day and reselect; selected input day must remain identical",
        },
        "source_archives": archives,
        "raster_scan_summary": {
            "rasters_scanned": sum(
                values["rasters_scanned"] for values in counts_by_year.values()
            ),
            "rasters_with_selected_day_pair": len(candidates),
            "rasters_without_pair": len(inventory),
            "selected_pairs_by_year": {
                str(year): sum(1 for row in candidates if row["year"] == year)
                for year in years
            },
            "per_year": counts_by_year,
            "target_observation_status_counts": dict(
                sorted(Counter(row["target_observation_status"] for row in candidates).items())
            ),
            "target_observation_status_counts_by_year": {
                str(year): dict(
                    sorted(
                        Counter(
                            row["target_observation_status"]
                            for row in candidates
                            if row["year"] == year
                        ).items()
                    )
                )
                for year in years
            },
        },
        "domain_options": domain_summaries,
        "_candidate_pairs": candidates,
        "rasters_without_pair_detail": inventory,
        "interpretation_limits": [
            "The pair rule is applied to every arrival TIFF in the 2014–2018 TRAIN archives; group tables and other split years are not opened.",
            "A selected pair is a geometrically defined observation opportunity, not a qualified simulator case. Rasters with no pair are still listed with an explicit reason.",
            "A next-day map with zero assigned pixels is retained and labelled no_mapped_pixels_on_next_day; it is not silently excluded and its capture ratio is undefined.",
            "Target capture is calculated only after pair and target-blind crop selection; it is not used to select events, days, domain, or window.",
            "The three-pixel rule is a minimum raster-observation gate only. A domain can still fail to fit three input-day pixels in its safe interior.",
            "Counts are native 90m arrival pixels. No resampling to simulator cells, fuel/DEM/weather alignment, FireCase generation, C++ replay, calibration, benchmark, RL training, or physical validation is performed.",
            "20x20 grids at 150m or larger change the physical meaning of actions; 40x40 at 100m changes checkpoint tensor/action dimensions. This screen adopts no domain.",
            "CFSDS daily interpolated arrival labels are not exact sub-daily flame-front ground truth; suppression and burn-out attribution remain unknown.",
            "A target date crossing the annual archive boundary is retained as unobservable; no neighboring-year archive is read.",
            "This screen does not resolve as-of-event fuel provenance, non-fuel scar import, complete terrain/weather provenance, suppression evidence, or the failed no-action gate.",
        ],
        "code_sha256": {
            filename: sha256_file(Path(__file__).resolve().parent / filename)
            for filename in (
                "audit_cfsds_train_full_day_pairs.py",
                "cfsds_spatial_feasibility.py",
                "cfsds_initial_state.py",
            )
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw/cfsds-v1_1"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("reports/real-fire-data/cfsds-train-full-day-pair-screen.json"),
    )
    args = parser.parse_args()
    result = scan(raw_root=args.raw_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    candidates = result.pop("_candidate_pairs")
    case_csv = args.out.with_suffix(".csv")
    base_columns = (
        "event_id",
        "year",
        "source_raster_member",
        "source_raster_sha256",
        "source_raster_shape_rc",
        "valid_arrival_pixels_total",
        "input_doy",
        "input_calendar_date",
        "input_pixels_on_selected_day",
        "target_doy",
        "target_calendar_date",
        "target_observation_status",
        "target_pixels_total",
        "selection_invariant_after_target_and_future_pixel_removal",
    )
    metric_columns = (
        "window_found",
        "window_unavailable_reason",
        "row_off",
        "col_off",
        "day_n_minus_1_front_pixels_total",
        "day_n_minus_1_front_pixels_in_safe_interior",
        "day_n_minus_1_front_capture_ratio",
        "target_pixels_in_window",
        "target_pixels_in_safe_interior",
        "target_capture_ratio",
        "target_safe_interior_capture_ratio",
    )
    columns = list(base_columns) + [
        f"{option['id']}_{key}"
        for option in GRID_OPTIONS
        for key in metric_columns
    ]
    with case_csv.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for case in candidates:
            row = {key: case.get(key) for key in base_columns}
            row["source_raster_shape_rc"] = json.dumps(case["source_raster_shape_rc"])
            for option in GRID_OPTIONS:
                prefix = f"{option['id']}_"
                metrics = case["domains"][option["id"]]
                row.update(
                    {
                        prefix + key: metrics.get(key)
                        for key in metric_columns
                    }
                )
            writer.writerow(row)
    result["candidate_pair_details"] = {
        "file": case_csv.name,
        "sha256": sha256_file(case_csv),
        "format": "CSV; one row per selected TRAIN fire/day pair, domain metrics in fixed prefixed columns",
        "rows": len(candidates),
        "domain_metrics_per_pair": len(GRID_OPTIONS),
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "scope": result["scope"],
                "raster_scan_summary": result["raster_scan_summary"],
                "candidate_pair_details": result["candidate_pair_details"],
                "domain_summaries": {
                    key: value["summary"]
                    for key, value in result["domain_options"].items()
                },
                "report": str(args.out),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
