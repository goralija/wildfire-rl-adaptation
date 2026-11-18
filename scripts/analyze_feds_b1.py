#!/usr/bin/env python3
"""LOO-by-fire offline evaluation of the preregistered B=1 TRAIN menu (ADR-033).

All method comparisons are exploratory. Bootstrap bands describe the existing OOF
fire deltas, without refitting bootstrap samples or creating an independent test.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from wildfire_rl.feds_simfire_setup import load_split_cases, sha256_file


def load_table(path):
    record = json.loads(path.read_text())
    if record.get("split") != "train" or record.get("validation_used") is not False or \
            record.get("test_cases_loaded") is not False:
        raise ValueError("only the TRAIN exploration table is accepted")
    plan = ROOT / "configs/frozen/feds-b1-exploration-v1.json"
    if record["settings"]["plan_sha256"] != sha256_file(plan):
        raise ValueError("table does not match the registered exploration plan")
    allowed = set(load_split_cases("train"))
    cases = []
    for item in record["cases"]:
        if item["scenario_id"] not in allowed:
            raise ValueError("non-TRAIN fire in table")
        case_path = path.parent / item["file"]
        if case_path.resolve().parent != path.parent.resolve() or sha256_file(case_path) != item["sha256"]:
            raise ValueError("changed or invalid case file")
        case = json.loads(case_path.read_text())
        if case["scenario_id"] != item["scenario_id"] or case["split"] != "train" or \
                case["settings"] != record["settings"] or case["reference_check"] != "PASS":
            raise ValueError("case identity/settings/reference mismatch")
        if sha256_file(case_path.with_suffix(".npz")) != case["mask_file_sha256"]:
            raise ValueError("changed mask artifact")
        cases.append(case)
    if len(cases) != record["case_count"] or len({c["scenario_id"] for c in cases}) != len(cases):
        raise ValueError("incomplete or duplicate fire list")
    return record, cases


def analyze(cases):
    import numpy as np
    from wildfire_rl.feds_b1_learning import METHOD_NAMES, evaluate_fold, paired_interval
    from wildfire_rl.line_damage import HECTARES_PER_CELL
    result = {}
    for mode in ("raw", "charged"):
        methods = {}
        for method in METHOD_NAMES:
            rows = [evaluate_fold(cases[:i] + cases[i+1:], case, mode, method)
                    for i, case in enumerate(cases)]
            methods[method] = {"mean_saved_ha": float(np.mean([r["saved_ha"] for r in rows])),
                               "out_of_fold": rows}
        baseline = np.asarray([r["saved_ha"] for r in methods["advancing_front"]["out_of_fold"]])
        oracle = np.asarray([max(r[mode + "_saved_cells"] for r in c["outcomes"])
                             * HECTARES_PER_CELL for c in cases])
        oracle_gap = float(np.mean(oracle - baseline))
        for method, entry in methods.items():
            deltas = np.asarray([r["saved_ha"] for r in entry["out_of_fold"]]) - baseline
            gain = float(deltas.mean())
            largest = int(np.argmax(np.abs(deltas)))
            entry.update({"mean_gain_ha_vs_advancing_front": gain,
                          "descriptive_paired_bootstrap_95": paired_interval(deltas),
                          "better_fires": int((deltas > 1e-8).sum()),
                          "worse_fires": int((deltas < -1e-8).sum()),
                          "without_largest_absolute_delta_ha": float(np.delete(deltas, largest).mean()),
                          "fraction_of_oracle_gap": gain / oracle_gap if oracle_gap > 0 else None,
                          "continuation_threshold_met": bool(gain >= 30 and oracle_gap > 0 and
                                                              gain / oracle_gap >= .25)})
        result[mode] = {"oracle_mean_saved_ha": float(oracle.mean()),
                        "oracle_gap_vs_advancing_front_ha": oracle_gap, "methods": methods}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("table", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("output exists; use a new report path")
    record, cases = load_table(args.table)
    if len(cases) != 98:
        parser.error("the registered offline analysis requires all 98 TRAIN fires")
    source_files = [Path(__file__), ROOT / "src/wildfire_rl/feds_b1_learning.py",
                    ROOT / "src/wildfire_rl/feds_b1.py", ROOT / "src/wildfire_rl/line_damage.py"]
    report = {"schema_version": "feds-b1-offline-analysis/1.0",
              "created_utc": datetime.now(timezone.utc).isoformat(),
              "label": "EXPLORATORY TRAIN LOO; NO FINAL VALIDATION OR PHYSICAL VALIDATION",
              "case_count": len(cases), "split": "train", "validation_used": False,
              "test_cases_loaded": False, "table_sha256": sha256_file(args.table),
              "table_settings": {k: v for k, v in record["settings"].items()
                                 if k not in ("weather_path", "input_root")},
              "local_artifact_paths_omitted": True,
              "source_hashes": {str(p.relative_to(ROOT)): sha256_file(p) for p in source_files},
              "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                                       text=True).strip(),
              "runtime": {"python": sys.version, "numpy": importlib.metadata.version("numpy")},
              "uncertainty": "paired percentile bootstrap of fixed OOF fire effects, 10000 resamples, seed 0; no model refit; folds share fit fires; descriptive only",
              "selection_warning": "all methods reported; choosing a method from these same LOO results is exploratory selection, not an independent performance estimate",
              "results": analyze(cases)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    for mode, values in report["results"].items():
        print(mode, "oracle", round(values["oracle_mean_saved_ha"], 2))
        for method, row in values["methods"].items():
            print(method, round(row["mean_gain_ha_vs_advancing_front"], 2),
                  row["continuation_threshold_met"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
