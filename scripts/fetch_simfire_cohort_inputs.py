#!/usr/bin/env python3
"""Fetch real fuel/terrain/weather inputs for the pinned SimFire incident cohort."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FETCH_SCRIPT = ROOT / "scripts/fetch_simfire_real_inputs.py"


def _fetch_case(case: dict, skip_weather: bool) -> dict:
    manifest = ROOT / case["scenario_manifest"]
    output = ROOT / ".local/simfire-cohort-v2" / case["scenario_id"]
    command = [
        sys.executable,
        str(FETCH_SCRIPT),
        "--scenario-manifest",
        str(manifest),
        "--out",
        str(output),
    ]
    if skip_weather:
        command.append("--skip-weather")
    result = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True)
    if result.returncode:
        return {
            "scenario_id": case["scenario_id"],
            "ok": False,
            "error": (result.stderr or result.stdout)[-3000:],
        }
    try:
        receipt = json.loads((output / "input-receipt.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"scenario_id": case["scenario_id"], "ok": False, "error": str(exc)}
    return {
        "scenario_id": case["scenario_id"],
        "ok": True,
        "receipt": receipt,
        "receipt_path": str((output / "input-receipt.json").relative_to(ROOT)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cohort-manifest",
        type=Path,
        default=ROOT / "data/manifests/simfire-fpa-fod-cohort-v2.json",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        choices=("train", "validation", "test"),
        default=("train", "validation", "test"),
    )
    parser.add_argument("--limit", type=int, help="process only the first N selected cases")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument(
        "--skip-weather",
        action="store_true",
        help="acquire fuel/terrain if the weather archive endpoint is temporarily unavailable",
    )
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 6:
        parser.error("--workers must be between 1 and 6 to avoid overloading public services.")

    cohort_path = args.cohort_manifest.expanduser().resolve()
    cohort = json.loads(cohort_path.read_text(encoding="utf-8"))
    cases = [case for case in cohort["cases"] if case["split"] in args.splits]
    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be positive.")
        cases = cases[: args.limit]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_fetch_case, case, args.skip_weather): case for case in cases}
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            results.append(result)
            state = "OK" if result["ok"] else "FAILED"
            print("[{}/{}] {} {}".format(index, len(cases), state, result["scenario_id"]), flush=True)
            if not result["ok"]:
                print(result["error"], flush=True)

    case_by_id = {case["scenario_id"]: case for case in cohort["cases"]}
    report_cases = []
    for result in results:
        if not result["ok"]:
            report_cases.append(result)
            continue
        receipt = result["receipt"]
        case = case_by_id[result["scenario_id"]]
        case["input_receipt"] = result["receipt_path"]
        case["input_status"] = {
            "fuel": "verified",
            "terrain": "verified",
            "weather": "candidate" if receipt["weather"]["sha256"] else "not_fetched",
        }
        report_cases.append({
            "scenario_id": result["scenario_id"],
            "ok": True,
            "receipt": result["receipt_path"],
            "fuel": receipt["fuel"],
            "terrain": receipt["terrain"],
            "weather": receipt["weather"],
            "scenario_manifest_sha256": receipt["scenario_manifest_sha256"],
        })

    report = {
        "kind": "simfire_fpa_fod_cohort_input_acquisition",
        "scientific_result": False,
        "readiness": "fuel_terrain_ready_weather_open",
        "cohort_id": cohort["cohort_id"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_splits": list(args.splits),
        "requested_case_count": len(cases),
        "successful_case_count": sum(bool(row.get("ok")) for row in results),
        "failed_case_count": sum(not bool(row.get("ok")) for row in results),
        "fuel_terrain_verified_case_count": sum(bool(row.get("ok")) for row in results),
        "historical_weather_downloaded_case_count": sum(
            bool(row.get("ok")) and bool(row["receipt"]["weather"].get("sha256"))
            for row in results
        ),
        "historical_weather_mapped_case_count": 0,
        "cases_ready_for_historical_weather_training": 0,
        "weather_skipped": args.skip_weather,
        "raw_inputs_location": ".local/simfire-cohort-v2/ (git-ignored)",
        "cases": report_cases,
        "limitations": [
            "Fuel/terrain receipts verify retrieval, projected alignment, shape and source-code range; they do not validate physical fire spread.",
            "Weather remains a candidate historical input until the source clock, wind-height and dead-fuel-moisture mappings are resolved.",
            "A successful raster acquisition means fuel and terrain passed; it does not mean a complete historical-weather scenario is ready for training.",
            "Any failed case remains in the cohort as not ready; do not silently replace it with a synthetic map.",
        ],
    }
    report_path = ROOT / "reports/real-fire-data/simfire-cohort-v2-input-acquisition.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    cohort["input_acquisition_report"] = report_path.relative_to(ROOT).as_posix()
    cohort["input_acquisition_summary"] = {
        "successful_cases": report["successful_case_count"],
        "failed_cases": report["failed_case_count"],
        "fuel_terrain_verified": report["successful_case_count"],
        "weather_fetched": sum(
            bool(item.get("ok")) and bool(item["receipt"]["weather"].get("sha256"))
            for item in results
        ),
        "weather_mapping": "open",
        "historical_weather_training_ready": 0,
    }
    cohort_path.write_text(json.dumps(cohort, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(report_path),
        "requested": report["requested_case_count"],
        "succeeded": report["successful_case_count"],
        "failed": report["failed_case_count"],
    }, indent=2))
    return 1 if report["failed_case_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
