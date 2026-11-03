#!/usr/bin/env python3
"""Paired budget-adaptation contrasts from one policy benchmark report.

Expects PPO policies named ``base-s<seed>`` and ``ft-b<budget>-s<seed>``. For each
evaluation budget B with a fine-tuned policy, reports (all paired by scenario):

* fine-tuned at B minus the frozen base, per seed and seed-averaged;
* fine-tuned at B minus the matched-control fine-tune at the base budget;
* every policy minus no-op.

Negative values mean less added burned area. Bootstrap intervals resample scenarios
after averaging over seeds, so they reflect scenario variation only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import statistics

import numpy as np


def _bootstrap(values, draws=4000, seed=20261104):
    values = np.asarray(values, dtype=float)
    generator = np.random.default_rng(seed)
    samples = generator.choice(values, size=(draws, values.size), replace=True).mean(axis=1)
    return [float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))]


def contrasts(report: dict, base_budget: int = 2) -> dict:
    added = {}
    for row in report["episodes"]:
        added[(row["policy"], row["budget"], row["scenario_id"])] = row["added_burned_ha"]
    scenarios = sorted({row["scenario_id"] for row in report["episodes"]})
    policies = sorted({row["policy"] for row in report["episodes"]})
    seeds = sorted({int(m.group(1)) for p in policies for m in [re.fullmatch(r"base-s(\d+)", p)] if m})
    budgets = sorted({row["budget"] for row in report["episodes"]})

    def paired(policy_a, policy_b, budget):
        return [added[(policy_a, budget, s)] - added[(policy_b, budget, s)] for s in scenarios
                if (policy_a, budget, s) in added and (policy_b, budget, s) in added]

    def seed_averaged(fmt_a, fmt_b, budget):
        per_seed = {}
        stacked = []
        for seed in seeds:
            a, b = fmt_a.format(seed=seed), fmt_b.format(seed=seed)
            deltas = paired(a, b, budget)
            if len(deltas) == len(scenarios):
                per_seed[str(seed)] = statistics.fmean(deltas)
                stacked.append(deltas)
        if not stacked:
            return None
        scenario_means = np.mean(np.asarray(stacked), axis=0)
        return {
            "per_seed_mean_delta_ha": per_seed,
            "seed_averaged_mean_delta_ha": float(scenario_means.mean()),
            "scenario_bootstrap_95ci_ha": _bootstrap(scenario_means),
            "scenarios_better": int((scenario_means < 0).sum()),
            "scenarios_worse": int((scenario_means > 0).sum()),
            "scenarios": len(scenarios),
        }

    output = {"seeds": seeds, "budgets": budgets, "scenarios": len(scenarios), "by_budget": {}}
    for budget in budgets:
        entry = {}
        has_finetune = bool(seeds) and ("ft-b%d-s%d" % (budget, seeds[0])) in policies
        if has_finetune:
            entry["finetuned_minus_frozen_base"] = seed_averaged(
                "ft-b%d-s{seed}" % budget, "base-s{seed}", budget)
            if budget != base_budget:
                entry["finetuned_minus_matched_control"] = seed_averaged(
                    "ft-b%d-s{seed}" % budget, "ft-b%d-s{seed}" % base_budget, budget)
        if seeds:
            entry["frozen_base_minus_noop"] = seed_averaged("base-s{seed}", "noop", budget)
            if has_finetune:
                entry["finetuned_minus_noop"] = seed_averaged("ft-b%d-s{seed}" % budget, "noop", budget)
        heuristics = {}
        for policy in policies:
            if policy.startswith(("base-", "ft-")) or policy == "noop":
                continue
            deltas = paired(policy, "noop", budget)
            if deltas:
                heuristics[policy] = {
                    "mean_delta_ha_vs_noop": statistics.fmean(deltas),
                    "scenario_bootstrap_95ci_ha": _bootstrap(deltas),
                }
        entry["heuristics_minus_noop"] = heuristics
        noop = [added[("noop", budget, s)] for s in scenarios if ("noop", budget, s) in added]
        entry["noop_mean_added_ha"] = statistics.fmean(noop) if noop else None
        output["by_budget"][str(budget)] = entry
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = json.loads(args.report.read_text(encoding="utf-8"))
    if report.get("test_cases_loaded") is not False:
        parser.error("refusing a report that loaded TEST cases")
    result = {
        "source_split": report["split"],
        "sim_params": report["sim_params"],
        "params_gate_status": report.get("params_gate_status"),
        "contrasts": contrasts(report),
    }
    text = json.dumps(result, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
