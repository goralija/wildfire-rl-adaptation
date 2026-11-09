#!/usr/bin/env python3
"""Run a reproducible no-op/reference comparison over manifest TRAIN cases.

VALIDATION is available only through ``--split validation`` together with
``--frozen-params``, a committed parameter-freeze record. TEST is never loaded.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifests/feds-episode-cohort-v1.json"
DEFAULT_OUT = ROOT / ".local/feds-noop-diagnostics"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _growth_summary(rows: list[dict]) -> dict:
    """Growth-only scores, stratified on whether FEDS grew beyond the initial mask.

    Growth IoU and recall are averaged only over growing timepoints, where every
    method is defined, so the rows stay paired across methods. Stalled timepoints
    are reported as counts of false growth instead of a ratio.
    """
    growing = [row for row in rows if row["observed_growth_cells"] > 0]
    stalled = [row for row in rows if row["observed_growth_cells"] == 0]
    growth_ious = [float(row["growth_iou"]) for row in growing]
    recalls = [float(row["growth_recall"]) for row in growing]
    hits = sum(row["growth_intersection_cells"] for row in rows)
    predicted = sum(row["predicted_growth_cells"] for row in rows)
    observed = sum(row["observed_growth_cells"] for row in rows)
    return {
        "growing_timepoints": len(growing),
        "mean_growth_iou": statistics.fmean(growth_ious) if growth_ious else None,
        "median_growth_iou": statistics.median(growth_ious) if growth_ious else None,
        "mean_growth_recall": statistics.fmean(recalls) if recalls else None,
        "pooled_growth_precision": hits / predicted if predicted else None,
        "pooled_growth_recall": hits / observed if observed else None,
        "growing_timepoints_without_predicted_growth": sum(
            row["predicted_growth_cells"] == 0 for row in growing),
        "stalled_timepoints": len(stalled),
        "stalled_timepoints_with_predicted_growth": sum(
            row["predicted_growth_cells"] > 0 for row in stalled),
        "mean_false_growth_cells_when_stalled": (
            statistics.fmean(row["predicted_growth_cells"] for row in stalled) if stalled else None),
    }


def summarize(results: list[dict]) -> dict:
    """Summarize paired no-op, persistence, and ellipse scores at all horizons."""
    metric_rows = {
        "simfire_noop": [],
        "persistence": [],
        "ellipse_reference": [],
    }
    for case in results:
        for row in case.get("trajectory", []):
            metric_rows["simfire_noop"].append(row)
            metric_rows["persistence"].append(row["persistence_reference"])
            metric_rows["ellipse_reference"].append(row["ellipse_reference"])

    summary = {}
    for name, rows in metric_rows.items():
        ious = [float(row["iou"]) for row in rows]
        area_errors = [
            abs(float(row["predicted_area_ha"]) - float(row["observed_area_ha"]))
            for row in rows
        ]
        summary[name] = {
            "scored_case_timepoints": len(rows),
            "mean_iou": statistics.fmean(ious) if ious else None,
            "median_iou": statistics.median(ious) if ious else None,
            "mean_absolute_area_error_ha": statistics.fmean(area_errors) if area_errors else None,
            "median_absolute_area_error_ha": statistics.median(area_errors) if area_errors else None,
            "edge_contact_timepoints": sum(bool(row["touches_map_edge"]) for row in rows),
            "edge_contact_cases": sum(
                any(bool(row["touches_map_edge"]) for row in case.get("trajectory", []))
                for case in results
            ) if name == "simfire_noop" else None,
            "growth": _growth_summary(rows),
        }

    noop = summary["simfire_noop"]
    comparisons = {}
    for baseline in ("persistence", "ellipse_reference"):
        reference = summary[baseline]
        comparisons[baseline] = {
            "mean_iou_delta_noop_minus_reference": (
                noop["mean_iou"] - reference["mean_iou"]
                if noop["mean_iou"] is not None and reference["mean_iou"] is not None else None
            ),
            "mean_area_error_delta_ha_noop_minus_reference": (
                noop["mean_absolute_area_error_ha"] - reference["mean_absolute_area_error_ha"]
                if noop["mean_absolute_area_error_ha"] is not None
                and reference["mean_absolute_area_error_ha"] is not None else None
            ),
            "mean_growth_iou_delta_noop_minus_reference": (
                noop["growth"]["mean_growth_iou"] - reference["growth"]["mean_growth_iou"]
                if noop["growth"]["mean_growth_iou"] is not None
                and reference["growth"]["mean_growth_iou"] is not None else None
            ),
        }
    return {"methods": summary, "paired_comparisons": comparisons}


def _run_one(job):
    """Run one case in a worker; failures are recorded, not raised."""
    import os

    os.environ.setdefault("OMP_NUM_THREADS", "1")
    from run_feds_noop_episode import run_episode

    scenario_id, params, seed, split = job
    try:
        return scenario_id, run_episode(scenario_id, seed=seed, split=split, **params), None
    except Exception as exc:  # retain cohort coverage and all failure detail
        return scenario_id, None, {
            "scenario_id": scenario_id,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wind-adjustment-factor", type=float, required=True)
    parser.add_argument("--internal-update-minutes", type=int, choices=(1, 3, 5, 10, 15), default=5)
    parser.add_argument("--active-cell-lifetime-minutes", type=int, default=90)
    parser.add_argument("--ros-multiplier", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--split", choices=("train", "validation"), default="train")
    parser.add_argument("--frozen-params", type=Path,
                        help="required for VALIDATION: JSON freeze record whose params match this run")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--resume", action="store_true", help="continue a matching partial report")
    args = parser.parse_args(argv)
    if not 0.0 <= args.wind_adjustment_factor <= 1.0:
        parser.error("wind-adjustment-factor must be in [0,1].")
    from wildfire_rl.feds_spread_metrics import ELLIPSE_REFERENCE_PROTOCOL, METRICS_VERSION

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("test_cases_loaded") is not False:
        parser.error("Refusing a manifest that includes TEST cases.")
    params = {
        "wind_adjustment_factor": args.wind_adjustment_factor,
        "internal_update_minutes": args.internal_update_minutes,
        "active_cell_lifetime_minutes": args.active_cell_lifetime_minutes,
        "ros_multiplier": args.ros_multiplier,
    }
    freeze_sha256 = None
    if args.split == "validation":
        if args.frozen_params is None:
            parser.error("VALIDATION requires --frozen-params from a committed TRAIN freeze.")
        freeze = json.loads(args.frozen_params.read_text(encoding="utf-8"))
        if freeze.get("frozen_params") != params or freeze.get("selected_on_split") != "train":
            parser.error("Requested parameters do not match the TRAIN freeze record.")
        freeze_sha256 = sha256_file(args.frozen_params)
    train_cases = [case for case in manifest["cases"] if case.get("split") == args.split]
    if len(train_cases) != manifest.get("case_counts_by_split", {}).get(args.split):
        parser.error("Manifest %s count is inconsistent." % args.split.upper())
    if len({case["scenario_id"] for case in train_cases}) != len(train_cases):
        parser.error("Manifest contains duplicate scenario IDs.")
    out = args.out or DEFAULT_OUT / (
        "%s-noop-waf-%g-life-%dm-ros-%g-step-%dm-seed-%d.json"
        % (args.split, args.wind_adjustment_factor, args.active_cell_lifetime_minutes,
           args.ros_multiplier, args.internal_update_minutes, args.seed)
    )
    manifest_hash = sha256_file(MANIFEST)
    configuration = {
        **params,
        "seed": args.seed,
        "manifest_sha256": manifest_hash,
        "split": args.split,
        "expected_scenarios": len(train_cases),
        "frozen_params_sha256": freeze_sha256,
        "metrics_version": METRICS_VERSION,
    }
    if out.exists():
        if not args.resume:
            parser.error("Output exists; choose another --out path or use --resume.")
        payload = json.loads(out.read_text(encoding="utf-8"))
        if payload.get("configuration") != configuration:
            parser.error("Existing partial report does not match this configuration.")
        if payload.get("status") == "complete":
            parser.error("The requested report is already complete.")
    else:
        if args.resume:
            parser.error("Cannot --resume because the output report does not exist.")
        payload = {
            "schema_version": "feds-simfire-train-noop-gate/1.1",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "status": "running",
            "configuration": configuration,
            "test_cases_loaded": False,
            "physical_validation": False,
            "scientific_result": False,
            "reference_protocol": {
                "persistence": "Hold the exact initial FEDS scar/front mask unchanged.",
                "ellipse": ELLIPSE_REFERENCE_PROTOCOL,
                "growth_metrics": "growth_* fields score only cells outside the initial mask; "
                                  "None where the denominator is empty",
            },
            "results": [],
            "errors": [],
        }
        atomic_write(out, payload)

    done = {result["scenario_id"] for result in payload["results"]}
    failed = {error["scenario_id"] for error in payload["errors"]}
    started = time.monotonic()
    pending = [case["scenario_id"] for case in train_cases
               if case["scenario_id"] not in done and case["scenario_id"] not in failed]
    jobs = [(scenario_id, params, args.seed, args.split) for scenario_id in pending]
    if args.workers > 1:
        from concurrent.futures import ProcessPoolExecutor

        executor = ProcessPoolExecutor(max_workers=args.workers)
        outcomes = executor.map(_run_one, jobs)
    else:
        executor = None
        outcomes = map(_run_one, jobs)
    for scenario_id, result, error in outcomes:
        if result is not None:
            payload["results"].append(result)
        else:
            payload["errors"].append(error)
        completed = len(payload["results"]) + len(payload["errors"])
        payload["status"] = "running"
        payload["updated_utc"] = datetime.now(timezone.utc).isoformat()
        payload["progress"] = {"completed": completed, "expected": len(train_cases)}
        payload["summary"] = summarize(payload["results"])
        atomic_write(out, payload)
        print("%d/%d %s: %s (%.1f min elapsed)" % (
            completed, len(train_cases), scenario_id,
            "OK" if scenario_id in {item["scenario_id"] for item in payload["results"]} else "ERROR",
            (time.monotonic() - started) / 60.0,
        ), flush=True)

    if executor is not None:
        executor.shutdown()
    complete_ids = {result["scenario_id"] for result in payload["results"]}
    error_ids = {error["scenario_id"] for error in payload["errors"]}
    missing = [case["scenario_id"] for case in train_cases if case["scenario_id"] not in complete_ids | error_ids]
    payload["status"] = "complete" if len(complete_ids) + len(error_ids) == len(train_cases) else "incomplete"
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    payload["progress"] = {
        "successful_scenarios": len(complete_ids),
        "failed_scenarios": len(error_ids),
        "missing_scenarios": missing,
        "expected": len(train_cases),
    }
    payload["summary"] = summarize(payload["results"])
    noop = payload["summary"]["methods"]["simfire_noop"]
    refs = payload["summary"]["methods"]
    payload["strict_screen"] = {
        "rule": "All split cases complete; no SimFire edge contacts; SimFire has higher mean IoU and lower mean absolute area error than both references.",
        "pass": bool(
            payload["status"] == "complete"
            and not payload["errors"]
            and noop["edge_contact_timepoints"] == 0
            and all(
                noop["mean_iou"] > refs[name]["mean_iou"]
                and noop["mean_absolute_area_error_ha"] < refs[name]["mean_absolute_area_error_ha"]
                for name in ("persistence", "ellipse_reference")
            )
        ),
        "note": "A TRAIN screening result only. Any candidate selected here still requires frozen VALIDATION evaluation before benchmark claims.",
    }
    atomic_write(out, payload)
    print(json.dumps({
        "output": str(out),
        "status": payload["status"],
        "progress": payload["progress"],
        "strict_screen": payload["strict_screen"],
        "summary": payload["summary"],
    }, indent=2))
    return 0 if payload["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
