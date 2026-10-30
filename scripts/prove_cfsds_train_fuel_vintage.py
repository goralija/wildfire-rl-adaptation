#!/usr/bin/env python3
"""Audit pre-target perimeter masking for one explicitly TRAIN-only CFSDS case.

The output is a temporal leakage check, not an annual fuel raster. No fuel class
is changed until a safe base vintage and an authoritative succession crosswalk
are available.
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_cfsds_train_fuel import derive_day_pair_masks, sha256_file  # noqa: E402
from cfsds_fuel_vintage import (  # noqa: E402
    NODATA_ARRIVAL,
    pre_target_burn_mask,
    select_train_candidate,
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def portable_path(path: Path) -> str:
    resolved = path.resolve()
    roots = [ROOT]
    if ROOT.parent.name == ".worktrees":
        roots.append(ROOT.parent.parent)
    for base in roots:
        try:
            return resolved.relative_to(base.resolve()).as_posix()
        except ValueError:
            continue
    return str(path)


def build_report(candidate: dict[str, Any], raw_root: Path, screen_path: Path) -> dict[str, Any]:
    event_id = str(candidate["event_id"])
    year = int(candidate["year"])
    target_doy = int(candidate["target_doy"])
    raster_zip = raw_root / str(year) / f"{year}_fireDOYrasters.zip"
    member_name = str(candidate["source_raster"])

    with zipfile.ZipFile(raster_zip) as archive:
        member = next((name for name in archive.namelist()
                       if Path(name).name == member_name), None)
        if member is None:
            raise FileNotFoundError(f"{member_name} is absent from {raster_zip}")
        raster_bytes = archive.read(member)

    rows, cols = (int(value) for value in candidate["native_crop_shape_rc"])
    row_off, col_off = int(candidate["row_off"]), int(candidate["col_off"])
    with rasterio.open(io.BytesIO(raster_bytes)) as source:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Setting the shape on a NumPy array has been deprecated.*",
                category=DeprecationWarning,
            )
            full_arrival = source.read(1)
        crop = full_arrival[row_off:row_off + rows, col_off:col_off + cols]
        if crop.shape != (rows, cols):
            raise ValueError(f"{event_id}: crop shape {crop.shape}, expected {(rows, cols)}")
        nodata = int(source.nodata) if source.nodata is not None else NODATA_ARRIVAL

    mask = pre_target_burn_mask(full_arrival, target_doy, nodata=nodata)
    valid = full_arrival < nodata
    target = (full_arrival == target_doy) & valid
    future = (full_arrival > target_doy) & valid
    crop_mask = mask[row_off:row_off + rows, col_off:col_off + cols]
    crop_valid = crop < nodata
    day_n_minus_one = (crop == target_doy - 1) & crop_valid
    crop_target = (crop == target_doy) & crop_valid
    crop_future = (crop > target_doy) & crop_valid
    # This reproduces the existing builder's target-aware front only to report
    # its size. It is not used to construct the pre-target fuel mask and is a
    # known future-information path that must be fixed before agent evaluation.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Setting the shape on a NumPy array has been deprecated.*",
            category=DeprecationWarning,
        )
        state_masks, state_counts = derive_day_pair_masks(crop, target_doy)

    target_or_future_excluded = not bool(np.any(mask & (target | future)))
    only_valid_pre_target = bool(np.all((full_arrival[mask] > 0) & (full_arrival[mask] < target_doy)))
    if not target_or_future_excluded or not only_valid_pre_target:
        raise AssertionError(f"{event_id}: pre-target mask failed temporal leakage checks")

    return {
        "schema": "cfsds-train-fuel-vintage-mask-proof/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Prove a TRAIN-only CFSDS pre-target perimeter mask excludes target-day and later event pixels.",
        "scope": {
            "event_id": event_id,
            "split": "train",
            "year": year,
            "target_doy": target_doy,
            "arrival_raster_shape_rc": [int(full_arrival.shape[0]), int(full_arrival.shape[1])],
            "native_crop_shape_rc": [rows, cols],
            "validation_or_test_rasters_opened": False,
            "simulator_replay_or_training": False,
        },
        "source": {
            "screen_report": portable_path(screen_path),
            "screen_report_sha256": sha256_file(screen_path),
            "arrival_archive": portable_path(raster_zip),
            "arrival_archive_sha256": sha256_file(raster_zip),
            "arrival_raster_member": member_name,
            "arrival_raster_member_sha256": sha256_bytes(raster_bytes),
            "arrival_raster_nodata": nodata,
        },
        "mask_rule": "valid arrival_day > 0 and arrival_day < target_doy; day n-1 is included; day n and later are excluded",
        "measurements": {
            "pre_target_event_pixels_full_raster": int(mask.sum()),
            "pre_target_event_pixels_model_crop": int(crop_mask.sum()),
            "day_n_minus_1_pixels": int(day_n_minus_one.sum()),
            "day_n_minus_1_active_front_pixels": int(state_masks["front"].sum()),
            "earlier_scar_pixels_after_front_separation": int(state_counts["earlier_scar_pixels"]),
            "target_day_n_pixels_full_raster": int(target.sum()),
            "target_day_n_pixels_model_crop": int(crop_target.sum()),
            "future_after_day_n_pixels_full_raster": int(future.sum()),
            "future_after_day_n_pixels_model_crop": int(crop_future.sum()),
        },
        "checks": {
            "every_selected_pixel_is_valid_and_before_target": only_valid_pre_target,
            "target_day_n_and_future_excluded": target_or_future_excluded,
            "day_n_minus_1_included_as_prior_perimeter": bool(np.all(crop_mask[day_n_minus_one])),
        },
        "fuel_map": {
            "generated": False,
            "status": "BLOCKED_BASE_VINTAGE_AND_SUCCESSION_RULES_UNVERIFIED",
            "reason": [
                "The 2014b base-map metadata has no verified per-pixel temporal cutoff.",
                "W.I.S.E. identifies a v20191114 succession ruleset, but its exact class tree has not yet been transcribed and validated for this project.",
                "Applying a generic non-fuel code would conflict with the simulator's current imported historical scar/front contract.",
            ],
            "no_fuel_class_was_reclassified": True,
        },
        "methodology_boundary": {
            "published_source": "https://doi.org/10.1071/WF26072",
            "official_v20191114_legend": "https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/FBP_FuelLayer_wBurnScars.pdf",
            "published_annual_map_step": "W.I.S.E. describes applying the v20191114 burn-scar succession rules to annual maps built from 2014/2019/2024 releases.",
            "published_daily_mask_step": "W.I.S.E. describes reclassifying the same-fire perimeter before day n as non-fuel for a day-n simulation.",
            "succession_tree_status": "Referenced in W.I.S.E. Figure 2; not transcribed/validated in this project. The official one-page CanFG-with-burn-scars PDF is a fuel-class legend.",
            "existing_project_front_rule": "The current builder selects day n-1 cells adjacent to target day n; this reveals target geometry through the initial state and must be replaced before an unbiased benchmark.",
            "target_aware_front_count_is_diagnostic_only": True,
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "rasterio": rasterio.__version__,
        },
        "limitations": [
            "This is a same-event temporal-mask proof, not a complete annual fuel map or a claim about cross-event historical fire coverage.",
            "CFSDS day-of-burning is a satellite-hotspot interpolation, not an hourly ground-truth perimeter.",
            "The existing target-aware initial-front rule is not leakage-free even though this fuel mask excludes target/future pixels.",
            "No validation/test input, target, or outcome was used.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-id", default="2018_747", help="must be an event explicitly marked train in the screen")
    parser.add_argument("--raw-root", type=Path, default=ROOT / "data/raw/cfsds-v1_1")
    parser.add_argument("--screen", type=Path, default=ROOT / "reports/real-fire-data/cfsds-cohort-screen.json")
    parser.add_argument("--out", type=Path, default=ROOT / "reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json")
    args = parser.parse_args()

    screen = json.loads(args.screen.read_text())
    candidate = select_train_candidate(screen.get("screening_candidates", []), args.event_id)
    report = build_report(candidate, args.raw_root, args.screen)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
