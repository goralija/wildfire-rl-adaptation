#!/usr/bin/env python3
"""Verify the finite table against masks, input provenance and ADR-032 TRAIN means."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_feds_b1 import load_table
from wildfire_rl.feds_simfire_setup import sha256_file


def summarize(table_path, input_root):
    import numpy as np
    from wildfire_rl.line_damage import score_line_damage, HECTARES_PER_CELL

    table, cases = load_table(table_path)
    expected_inputs = {c["scenario_id"]: c for c in json.loads((ROOT /
        "reports/real-fire-data/feds-simfire-input-train-coverage-v1.json").read_text())["cases"]}
    for case in cases:
        key = case["scenario_id"]
        receipt = json.loads((input_root / key / "input-receipt.json").read_text())
        expected = expected_inputs[key]
        if any(receipt[k][field] != expected[public] for k, field, public in (
            ("fuel", "sha256", "fuel_sha256"), ("terrain", "sha256", "terrain_sha256"),
            ("initial_feds_state", "mask_sha256", "mask_sha256"))):
            raise ValueError("inputs differ from committed cohort for " + key)
        with np.load(table_path.parent / (key + ".npz"), allow_pickle=False) as masks:
            initial, noop = masks["initial"], masks["noop"]
            agent, line = masks["agent_burned"], masks["line_cells"]
            if len(agent) != 33 or len(line) != 33:
                raise ValueError("incomplete mask table")
            for i, row in enumerate(case["outcomes"]):
                actual = score_line_damage(initial, agent[i], noop, line[i])
                if any(row[k] != v for k, v in actual.items()):
                    raise ValueError("mask/metric mismatch for " + key)
    modes = {}
    for mode in ("raw", "charged"):
        scores = {}
        for policy in ("advancing_front", "downwind", "random_legal"):
            scores[policy] = float(np.mean([c["references"][policy][mode + "_saved_cells"]
                                           * HECTARES_PER_CELL for c in cases]))
        scores["oracle"] = float(np.mean([max(row[mode + "_saved_cells"] for row in c["outcomes"])
                                          * HECTARES_PER_CELL for c in cases]))
        modes[mode] = scores
    noop_mean = float(np.mean([c["outcomes"][0]["noop_damage_cells"] * HECTARES_PER_CELL
                              for c in cases]))
    reference_path = ROOT / "reports/real-fire-data/feds-simfire-budget-run-record-adr030-v1.json"
    reference = json.loads(reference_path.read_text())["benchmarks"]["train"]
    reference_values = {policy: -reference["family_mean_delta_ha_vs_noop"][policy]["1"]
                        for policy in ("advancing_front", "downwind", "random_legal")}
    reference_values["noop_mean_added_ha"] = reference["noop_mean_added_ha"]
    actual_values = {policy: modes["raw"][policy] for policy in reference_values if policy != "noop_mean_added_ha"}
    actual_values["noop_mean_added_ha"] = noop_mean
    differences = {key: actual_values[key] - value for key, value in reference_values.items()}
    if len(cases) == 98 and any(abs(v) > 1e-7 for v in differences.values()):
        raise ValueError("full-cohort means differ from ADR-032: " + str(differences))
    outcome_count = sum(len(c["outcomes"]) for c in cases)
    return {
        "schema_version": "feds-b1-table-check/1.0", "decision": "ADR-033",
        "label": "TRAIN EXPLORATION; NOT PHYSICAL VALIDATION", "split": "train",
        "case_count": len(cases), "outcome_count": outcome_count,
        "validation_used": False, "test_cases_loaded": False,
        "table_sha256": sha256_file(table_path),
        "summary_script_sha256": sha256_file(Path(__file__)),
        "settings": {k: v for k, v in table["settings"].items() if k not in ("weather_path", "input_root")},
        "checks": {"all_independent_references": "PASS", "all_mask_metrics_recomputed": "PASS",
                   "all_input_hashes_match_committed_cohort": "PASS",
                   "original_full_train_report_available": False,
                   "adr032_aggregate_match": "PASS" if len(cases) == 98 else "not a full cohort"},
        "noop_mean_added_ha": noop_mean, "mean_saved_ha": modes,
        "adr032_train_reference_sha256": sha256_file(reference_path),
        "adr032_actual_minus_reference_ha": differences,
        "edge_contact_outcomes": sum(r["edge_contact"] for c in cases for r in c["outcomes"]),
        "outcomes_burning_more_than_noop": sum(r["raw_saved_cells"] < 0 for c in cases for r in c["outcomes"]),
        "limits": ["The oracle sees all future rollout outcomes and is an unattainable upper bound for a policy without that information.",
                   "Aggregate agreement does not establish per-fire equality with the unavailable ADR-032 full report.",
                   "Line charge is an exploratory alternative; the locked reward and ADR-032 numbers are unchanged."],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("table", type=Path)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("output exists; choose a new report path")
    report = summarize(args.table, args.input_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({key: report[key] for key in ("case_count", "checks", "mean_saved_ha")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
