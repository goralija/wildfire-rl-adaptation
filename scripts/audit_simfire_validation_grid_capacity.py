#!/usr/bin/env python3
"""Compare the 2023 VALIDATION fire sizes to the current SimFire board capacity."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COHORT = ROOT / "data/manifests/simfire-fpa-fod-cohort-v2.json"
DEFAULT_OUTPUT = ROOT / "reports/real-fire-data/simfire-validation-grid-capacity-20261102.json"
COHORT_SHA256 = "f6c58b4685dcf24bf17f16c000b5d60d784f6ee49d85b43f750aef20939a4481"
M2_PER_ACRE = 4046.8564224


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, default=DEFAULT_COHORT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.cohort.is_file():
        raise FileNotFoundError("missing cohort manifest: {}".format(args.cohort))
    cohort_hash = sha256_file(args.cohort)
    if cohort_hash != COHORT_SHA256:
        raise ValueError("cohort manifest checksum differs from the frozen source")

    cohort = json.loads(args.cohort.read_text(encoding="utf-8"))
    cases = [
        row for row in cohort["cases"]
        if row.get("split") == "validation" and row.get("year") == 2023
    ]
    if len(cases) != 20:
        raise ValueError("expected the frozen 20-case 2023 VALIDATION cohort")

    audited = []
    grid_specs = set()
    manifest_hashes = {}
    for row in cases:
        manifest_path = ROOT / row["scenario_manifest"]
        if not manifest_path.is_file():
            raise FileNotFoundError("missing scenario manifest: {}".format(manifest_path))
        manifest_hash = sha256_file(manifest_path)
        manifest_hashes[row["scenario_manifest"]] = manifest_hash
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        grid = manifest["grid"]
        rows, columns, resolution = int(grid["rows"]), int(grid["columns"]), float(grid["resolution_m"])
        grid_specs.add((rows, columns, resolution))
        area_ha = float(row["reported_final_area_ha_reference_only"])
        area_m2 = area_ha * 10_000.0
        final_area_acres = area_m2 / M2_PER_ACRE
        board_area_m2 = rows * columns * resolution * resolution
        board_area_acres = board_area_m2 / M2_PER_ACRE
        minimum_square_side_cells = math.ceil(math.sqrt(area_m2) / resolution)
        audited.append({
            "scenario_id": row["scenario_id"],
            "source_record_id": row["source_record_id"],
            "state": row["state"],
            "year": row["year"],
            "grid_manifest": row["scenario_manifest"],
            "grid_rows": rows,
            "grid_columns": columns,
            "resolution_m": resolution,
            "current_grid_max_area_acres": round(board_area_acres, 2),
            "fpa_reported_final_area_ha_reference_only": area_ha,
            "fpa_reported_final_area_acres_reference_only": round(final_area_acres, 2),
            "board_capacity_as_percent_of_recorded_fire_area": round(board_area_acres / final_area_acres * 100.0, 2),
            "minimum_square_side_cells_to_fit_area_only": minimum_square_side_cells,
        })

    if len(grid_specs) != 1:
        raise ValueError("validation cases do not share a single grid shape/resolution")
    grid_rows, grid_columns, resolution_m = next(iter(grid_specs))
    board_capacity = grid_rows * grid_columns * resolution_m * resolution_m / M2_PER_ACRE
    fire_sizes = [r["fpa_reported_final_area_acres_reference_only"] for r in audited]
    larger_count = sum(size > board_capacity for size in fire_sizes)
    result = {
        "kind": "simfire_validation_grid_capacity_audit",
        "created_utc": "2026-11-02",
        "cohort": {
            "manifest": "data/manifests/simfire-fpa-fod-cohort-v2.json",
            "sha256": cohort_hash,
            "split": "validation",
            "year": 2023,
            "cases_screened": len(cases),
            "scenario_manifest_hashes": manifest_hashes,
        },
        "method": {
            "grid_source": "each frozen per-case scenario manifest",
            "fire_area_source": "reported_final_area_ha_reference_only in the frozen cohort manifest",
            "area_assumption": "all grid cells burnable; this is a theoretical board-area ceiling, not simulated area",
            "square_grid_fit": "minimum cell side assumes the fire area is a square; actual perimeter extent may need more cells",
        },
        "summary": {
            "grid_rows": grid_rows,
            "grid_columns": grid_columns,
            "resolution_m": resolution_m,
            "board_capacity_acres": round(board_capacity, 2),
            "fpa_fire_area_min_acres": round(min(fire_sizes), 2),
            "fpa_fire_area_median_acres": round(statistics.median(fire_sizes), 2),
            "fpa_fire_area_max_acres": round(max(fire_sizes), 2),
            "cases_larger_than_board_area": larger_count,
            "cases_screened": len(cases),
            "minimum_square_side_cells_range": [
                min(r["minimum_square_side_cells_to_fit_area_only"] for r in audited),
                max(r["minimum_square_side_cells_to_fit_area_only"] for r in audited),
            ],
            "whole_fire_extent_representable_on_current_grid_for_all_validation_cases": larger_count == 0,
        },
        "cases": audited,
        "safeguards": {
            "test_cases_read": False,
            "test_geometries_opened": False,
            "simulator_advanced": False,
            "agent_training": False,
            "policy_evaluation": False,
        },
        "interpretation": "The current 128x128 30 m validation crop holds at most about 3,644 acres if every cell burns. All 20 selected 2023 validation incidents have larger reported final areas. It can support a bounded local simulation, but cannot contain a whole selected incident or support a whole-fire historical-area claim.",
        "next_decision": "Before training, either expand the landscape extent and reacquire aligned fuel/elevation grids, or explicitly redefine the experiment as a bounded local-fireline problem and avoid whole-fire outcome claims.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        raise FileExistsError("refusing to overwrite existing receipt: {}".format(args.out))
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("validation_cases={} grid={}x{} at {}m capacity_acres={} cases_over_capacity={} test_opened=false training=false".format(
        len(cases), grid_rows, grid_columns, resolution_m, round(board_capacity, 2), larger_count
    ))
    print(args.out)


if __name__ == "__main__":
    main()
