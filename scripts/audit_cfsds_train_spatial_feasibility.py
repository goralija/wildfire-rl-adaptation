#!/usr/bin/env python3
"""Compare target-blind domain footprints on the existing TRAIN-only shortlist.

This is a geometry feasibility audit. It does not emit Cell2Fire inputs or run
the simulator. Day-n truth is measured only after each crop is selected from
pre-target arrival history.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import warnings
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

try:
    from .cfsds_spatial_feasibility import (
        evaluate_target_blind_window,
        native_window_shape,
    )
except ImportError:  # pragma: no cover - direct CLI invocation
    from cfsds_spatial_feasibility import evaluate_target_blind_window, native_window_shape


GRID_OPTIONS: tuple[dict[str, Any], ...] = (
    {"id": "grid20_cell100m", "rows": 20, "cols": 20, "cell_size_m": 100},
    {"id": "grid20_cell150m", "rows": 20, "cols": 20, "cell_size_m": 150},
    {"id": "grid20_cell200m", "rows": 20, "cols": 20, "cell_size_m": 200},
    {"id": "grid20_cell300m", "rows": 20, "cols": 20, "cell_size_m": 300},
    {"id": "grid40_cell100m", "rows": 40, "cols": 40, "cell_size_m": 100},
)

DETAIL_KEYS = (
    "window_found",
    "window_unavailable_reason",
    "source_raster_shape_rc",
    "row_off",
    "col_off",
    "pre_target_pixels_in_window",
    "day_n_minus_1_front_pixels_total",
    "day_n_minus_1_front_pixels_in_window",
    "day_n_minus_1_front_pixels_in_safe_interior",
    "day_n_minus_1_front_capture_ratio",
    "target_pixels_total",
    "target_pixels_in_window",
    "target_pixels_in_safe_interior",
    "target_pixels_outside_window",
    "target_capture_ratio",
    "target_safe_interior_capture_ratio",
    "target_geometry_used_for_window_selection",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compact_domain_metrics(metric: dict[str, Any]) -> dict[str, Any]:
    """Keep case-level evidence while storing shared grid geometry once."""
    return {key: metric[key] for key in DETAIL_KEYS if key in metric}


def source_archive(raw_root: Path, year: int) -> Path:
    return raw_root / str(year) / f"{year}_fireDOYrasters.zip"


def locate_raster_member(archive: zipfile.ZipFile, event_id: str, expected_name: str) -> str:
    names = archive.namelist()
    exact = [name for name in names if Path(name).name == expected_name]
    if len(exact) == 1:
        return exact[0]
    by_event = [name for name in names if Path(name).name == f"{event_id}_krig.tif"]
    if len(by_event) != 1:
        raise ValueError(
            f"Expected one raster for {event_id}; exact={exact}, event matches={by_event}"
        )
    return by_event[0]


def summarize_option(rows: list[dict[str, Any]], option_id: str) -> dict[str, Any]:
    metrics = [row["domains"][option_id] for row in rows]
    valid = [metric for metric in metrics if metric["window_found"]]
    target_ratios = [
        metric["target_capture_ratio"]
        for metric in valid
        if metric["target_capture_ratio"] is not None
    ]
    interior_ratios = [
        metric["target_safe_interior_capture_ratio"]
        for metric in valid
        if metric["target_safe_interior_capture_ratio"] is not None
    ]
    front_ratios = [
        metric["day_n_minus_1_front_capture_ratio"] for metric in valid
    ]
    return {
        "candidate_pairs": len(rows),
        "pre_target_window_found": len(valid),
        "window_found_rate": round(len(valid) / len(rows), 6) if rows else None,
        "target_pairs_with_any_pixel_in_window": sum(
            int(metric["target_pixels_in_window"] > 0) for metric in valid
        ),
        "target_pairs_with_any_safe_interior_pixel": sum(
            int(metric["target_pixels_in_safe_interior"] > 0) for metric in valid
        ),
        "median_target_capture_ratio": (
            round(float(np.median(target_ratios)), 6) if target_ratios else None
        ),
        "p75_target_capture_ratio": (
            round(float(np.quantile(target_ratios, 0.75)), 6)
            if target_ratios
            else None
        ),
        "maximum_target_capture_ratio": round(max(target_ratios), 6) if target_ratios else None,
        "median_safe_interior_target_capture_ratio": (
            round(float(np.median(interior_ratios)), 6) if interior_ratios else None
        ),
        "median_day_n_minus_1_front_capture_ratio": (
            round(float(np.median(front_ratios)), 6) if front_ratios else None
        ),
        "target_metrics_are_post_selection_diagnostics": True,
    }


def audit(
    *,
    screen_path: Path,
    raw_root: Path,
    options: tuple[dict[str, Any], ...] = GRID_OPTIONS,
) -> dict[str, Any]:
    screen = json.loads(screen_path.read_text())
    if (
        screen.get("scope") != "train_only"
        or screen.get("heldout_splits_opened") is not False
    ):
        raise ValueError("Input shortlist must be the TRAIN-only target-blind screen")
    if (
        screen.get("target_geometry_used_for_crop_selection") is not False
        or screen.get("target_geometry_used_for_candidate_ranking") is not False
    ):
        raise ValueError("Input screen does not attest target-blind crop and candidate ranking")
    candidates = screen.get("screening_candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Input screen has no candidate pairs")
    if any(
        item.get("split") != "train"
        or not 2014 <= int(item.get("year", 0)) <= 2018
        or item.get("target_geometry_used_for_window_selection") is not False
        or item.get("target_geometry_used_for_candidate_ranking") is not False
        for item in candidates
    ):
        raise ValueError(
            "Candidates must be 2014–2018 TRAIN rows with explicit target-blind flags"
        )
    pair_keys = [
        (str(item["event_id"]), int(item["year"]), int(item["target_doy"]))
        for item in candidates
    ]
    if len(set(pair_keys)) != len(pair_keys):
        raise ValueError("Input shortlist contains duplicate TRAIN event/day pairs")

    archives: dict[int, zipfile.ZipFile] = {}
    archive_paths: dict[int, Path] = {}
    archive_hashes: dict[int, str] = {}
    try:
        results: list[dict[str, Any]] = []
        for candidate in candidates:
            event_id = str(candidate["event_id"])
            year = int(candidate["year"])
            doy = int(candidate["target_doy"])
            archive_path = source_archive(raw_root, year)
            if not archive_path.is_file():
                raise FileNotFoundError(f"Missing TRAIN arrival archive: {archive_path}")
            if year not in archives:
                archive_paths[year] = archive_path
                archive_hashes[year] = sha256_file(archive_path)
                archives[year] = zipfile.ZipFile(archive_path)
            member = locate_raster_member(
                archives[year], event_id, str(candidate["source_raster"])
            )
            raster_bytes = archives[year].read(member)
            with rasterio.open(io.BytesIO(raster_bytes)) as source:
                # Rasterio 1.4.4 sets ndarray.shape internally; NumPy 2.5 emits
                # a deprecation warning for that third-party operation.
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore",
                        message="Setting the shape on a NumPy array has been deprecated",
                        category=DeprecationWarning,
                    )
                    arrival = source.read(1)
                x_resolution = abs(float(source.transform.a))
                y_resolution = abs(float(source.transform.e))
                if not math.isclose(x_resolution, y_resolution, rel_tol=0, abs_tol=1e-6):
                    raise ValueError(
                        f"Non-square CFSDS cells for {event_id}: "
                        f"{x_resolution}x{y_resolution}"
                    )
                if not math.isclose(x_resolution, 90.0, rel_tol=0, abs_tol=1e-6):
                    raise ValueError(
                        f"Unexpected native CFSDS resolution for {event_id}: "
                        f"{x_resolution}m"
                    )
                domains = {
                    option["id"]: evaluate_target_blind_window(
                        arrival,
                        doy,
                        grid_rows=int(option["rows"]),
                        grid_cols=int(option["cols"]),
                        cell_size_m=float(option["cell_size_m"]),
                        native_cell_size_m=x_resolution,
                    )
                    for option in options
                }
                results.append(
                    {
                        "event_id": event_id,
                        "year": year,
                        "target_doy": doy,
                        "shortlist_rule": (
                            "existing 2014–2018 pre-target shortlist; event/day "
                            "membership is held fixed across domain options"
                        ),
                        "source_raster_member": member,
                        "source_raster_sha256": sha256_bytes(raster_bytes),
                        "domains": domains,
                    }
                )
    finally:
        for archive in archives.values():
            archive.close()

    option_summaries = {
        option["id"]: {
            "grid": option,
            "requested_extent_m": [
                option["rows"] * option["cell_size_m"],
                option["cols"] * option["cell_size_m"],
            ],
            "native_window_shape_rc": list(
                native_window_shape(
                    int(option["rows"]),
                    int(option["cols"]),
                    float(option["cell_size_m"]),
                )
            ),
            "realized_extent_m": [
                extent * 90
                for extent in native_window_shape(
                    int(option["rows"]),
                    int(option["cols"]),
                    float(option["cell_size_m"]),
                )
            ],
            "edge_margin_native_pixels": max(
                1, int(math.floor(option["cell_size_m"] / 90 + 0.5))
            ),
            "existing_20x20_checkpoint_compatible_by_tensor_shape": (
                option["rows"] == 20 and option["cols"] == 20
            ),
            "physical_cell_semantics_match_existing_100m_case": option["cell_size_m"] == 100,
            "summary": summarize_option(results, option["id"]),
        }
        for option in options
    }
    return {
        "dataset": "Canadian Fire Spread Dataset (CFSDS)",
        "release": "v1.1",
        "scope": "train_only",
        "event_years": [2014, 2015, 2016, 2017, 2018],
        "heldout_splits_opened": False,
        "candidate_pairs": len(results),
        "candidate_pairs_by_year": {
            str(year): sum(1 for row in results if row["year"] == year)
            for year in sorted({row["year"] for row in results})
        },
        "source_shortlist": {
            "path": screen_path.name,
            "sha256": sha256_file(screen_path),
            "window_and_candidate_geometry_selection_target_blind": True,
            "day_pair_membership_fully_target_independent": False,
            "day_pair_eligibility_requires_target_day_record_and_positive_firearea": True,
            "candidate_membership_reselected_per_domain": False,
        },
        "source_archives": [
            {"year": year, "filename": archive_paths[year].name, "sha256": archive_hashes[year]}
            for year in sorted(archive_paths)
        ],
        "code_sha256": {
            filename: sha256_file(Path(__file__).resolve().parent / filename)
            for filename in (
                "audit_cfsds_train_spatial_feasibility.py",
                "cfsds_spatial_feasibility.py",
                "cfsds_initial_state.py",
            )
        },
        "native_resolution_m": 90,
        "window_selection": {
            "source_information": (
                "valid CFSDS arrival values strictly before target_doy; "
                "day n-1 centroid"
            ),
            "minimum_safe_interior_front_pixels": 3,
            "safe_border": "approximately one model cell, converted to rounded native 90m pixels",
            "tie_breaking": (
                "nearest day n-1 centroid; then more interior n-1 pixels; "
                "then more pre-target history; then row/column order"
            ),
            "target_day_used_for_crop_or_candidate_selection": False,
        },
        "domain_options": option_summaries,
        "candidate_pairs_detail": [
            {
                **{key: row[key] for key in (
                    "event_id",
                    "year",
                    "target_doy",
                    "shortlist_rule",
                    "source_raster_member",
                    "source_raster_sha256",
                )},
                "domains": {
                    option_id: compact_domain_metrics(metric)
                    for option_id, metric in row["domains"].items()
                },
            }
            for row in results
        ],
        "interpretation_limits": [
            "This is a TRAIN-only geometry audit over the already shortlisted 25 event/day pairs, not a full CFSDS cohort audit.",
            "Day-n coverage is computed after target-blind window selection and is a feasibility diagnostic only; it did not choose a domain, crop, or event.",
            "Counts are native 90m raster pixels. The report does not resample maps into simulator cells or create FireCase inputs.",
            "20x20 grids at 150m or larger preserve tensor/action shape but change the physical meaning of each action and require a separate simulator/input contract review.",
            "40x40 at 100m changes tensor and action dimensions; the existing 20x20 Firehose checkpoint cannot be used unchanged.",
            "No fuel, DEM, weather, suppression, importer, no-action replay, simulator physics, calibration, RL training, or policy benefit is validated here.",
            "The audit cannot resolve the separate as-of-event fuel vintage and non-fuel historical-scar importer blockers.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--screen",
        type=Path,
        default=Path("reports/real-fire-data/cfsds-train-target-blind-window-screen.json"),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw/cfsds-v1_1"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("reports/real-fire-data/cfsds-train-spatial-feasibility.json"),
    )
    args = parser.parse_args()
    result = audit(screen_path=args.screen, raw_root=args.raw_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "scope": result["scope"],
        "candidate_pairs": result["candidate_pairs"],
        "heldout_splits_opened": result["heldout_splits_opened"],
        "options": {
            option_id: details["summary"]
            for option_id, details in result["domain_options"].items()
        },
        "report": str(args.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
