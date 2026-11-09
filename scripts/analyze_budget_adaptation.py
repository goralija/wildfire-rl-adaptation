#!/usr/bin/env python3
"""Paired benchmark contrasts and the ADR-030 section 4 statistics plan.

Expects PPO policies named ``base-s<seed>`` and ``ft-b<budget>-s<seed>``. Every
contrast is paired by scenario on seed-averaged deltas; negative values mean less
added burned area.

* **Primary family (ADR-030 section 4), six tests:** base PPO minus random legal line
  and base PPO minus the best TRAIN heuristic, at B = 1, 2, 4. The best heuristic is the
  one with the largest mean reduction versus no-op at B = 2 in a separate TRAIN
  benchmark report (``--train-report``), never in the report being analysed; no-op and
  random legal line are not candidates. Exact two-sided sign-flip p-values with Holm
  correction across the six tests at alpha = .05.
* **Secondary:** fine-tuned at B minus the frozen base, and fine-tuned at B minus the
  matched-control fine-tune at the base budget.
* **Sanity checks only:** every contrast against no-op.

Every seed-averaged contrast carries the exact sign-flip p-value, the number of
scenarios whose seed-averaged damage changed, the mean without the scenario with the
largest absolute delta, and three intervals: ``scenario_bootstrap_95ci_ha`` resamples
scenarios after averaging over seeds (scenario variation only); ``seed_t95ci_ha`` is a
t-interval over per-seed means and ``two_level_bootstrap_95ci_ha`` resamples seeds and
then scenarios (both include seed-to-seed variation).
"""

from __future__ import annotations

import argparse
import hashlib
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


# Two-sided 95% Student t critical values by degrees of freedom.
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
        9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
        16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 21: 2.080, 22: 2.074,
        23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042}


def _seed_t_interval(per_seed_means):
    values = np.asarray(per_seed_means, dtype=float)
    if values.size < 2 or values.size - 1 not in T975:
        return None
    half = T975[values.size - 1] * values.std(ddof=1) / np.sqrt(values.size)
    return [float(values.mean() - half), float(values.mean() + half)]


def _two_level_bootstrap(matrix, draws=4000, seed=20261105):
    values = np.asarray(matrix, dtype=float)  # seeds x scenarios
    generator = np.random.default_rng(seed)
    seeds, scenarios = values.shape
    samples = np.empty(draws)
    for index in range(draws):
        rows = generator.integers(seeds, size=seeds)
        columns = generator.integers(scenarios, size=scenarios)
        samples[index] = values[np.ix_(rows, columns)].mean()
    return [float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))]


def _signed_sums(values):
    sums = np.zeros(1)
    for value in values:
        sums = np.concatenate((sums + value, sums - value))
    return sums


def sign_flip_test(deltas, exact_limit=22, draws=200000, seed=20261109):
    """Two-sided paired sign-flip test of a zero mean delta.

    Zero deltas cannot change sign and are dropped; ``scenarios_changed`` counts the
    rest. Up to ``exact_limit`` changed scenarios every one of the 2^n sign patterns is
    enumerated (the observed one included, so the smallest p is 2 / 2^n); above that a
    seeded Monte Carlo estimate (1 + hits) / (1 + draws) is returned.
    """
    values = np.asarray(deltas, dtype=float)
    # Seed-averaged hectare deltas that cancel exactly in cells can leave float residue
    # of about 1e-15; those scenarios did not change.
    zero = 1e-9 * max(1.0, float(np.abs(values).max())) if values.size else 0.0
    changed = values[np.abs(values) > zero]
    if changed.size == 0:
        return {"scenarios_changed": 0, "sign_flip_p_two_sided": 1.0, "sign_flip_method": "exact"}
    observed = abs(changed.sum())
    tolerance = 1e-9 * max(1.0, float(np.abs(changed).sum()))
    if changed.size <= exact_limit:
        half = changed.size // 2
        totals = _signed_sums(changed[:half])[:, None] + _signed_sums(changed[half:])[None, :]
        p_value = float(np.mean(np.abs(totals) >= observed - tolerance))
        method = "exact"
    else:
        generator = np.random.default_rng(seed)
        hits = 0
        for start in range(0, draws, 10000):
            signs = generator.choice((-1.0, 1.0), size=(min(10000, draws - start), changed.size))
            hits += int(np.count_nonzero(np.abs(signs @ changed) >= observed - tolerance))
        p_value = (1 + hits) / float(1 + draws)
        method = "monte_carlo"
    return {"scenarios_changed": int(changed.size), "sign_flip_p_two_sided": p_value,
            "sign_flip_method": method}


def leave_largest_out(deltas, scenarios):
    """Mean delta without the one scenario whose absolute delta is largest."""
    values = np.asarray(deltas, dtype=float)
    if values.size < 2:
        return {"leave_largest_out_mean_delta_ha": None, "leave_largest_out_scenario": None}
    largest = int(np.argmax(np.abs(values)))
    return {"leave_largest_out_mean_delta_ha": float(np.delete(values, largest).mean()),
            "leave_largest_out_scenario": scenarios[largest]}


PRIMARY_FAMILY_SIZE = 6
PRIMARY_BUDGETS = (1, 2, 4)
HOLM_ALPHA = 0.05
SELECTION_BUDGET = 2
NOT_HEURISTIC_CANDIDATES = ("noop", "random_legal")


def holm_correction(p_values: dict, alpha: float = HOLM_ALPHA, family_size=None) -> dict:
    """Holm step-down correction; returns rank, adjusted p and rejection per test.

    ``family_size`` defaults to the number of tests; a larger value keeps missing tests
    in the family (conservative) instead of shrinking it.
    """
    size = len(p_values) if family_size is None else int(family_size)
    if size < len(p_values):
        raise ValueError("family size is smaller than the number of tests")
    order = sorted(p_values, key=lambda key: (p_values[key], key))
    result = {}
    running_max = 0.0
    rejecting = True
    for rank, key in enumerate(order, start=1):
        multiplier = size - rank + 1
        running_max = max(running_max, min(1.0, multiplier * p_values[key]))
        rejecting = rejecting and p_values[key] <= alpha / multiplier
        result[key] = {"holm_rank": rank, "holm_adjusted_p": running_max, "holm_reject": rejecting}
    return result


def _episode_index(report: dict) -> dict:
    return {(row["policy"], row["budget"], row["scenario_id"]): row["added_burned_ha"]
            for row in report["episodes"]}


def select_best_train_heuristic(train_report: dict, budget: int = SELECTION_BUDGET) -> dict:
    """The heuristic with the largest mean reduction versus no-op at ``budget`` on TRAIN.

    Candidates are the report's non-PPO policies except no-op and random legal line (its
    own primary contrast). Ties go to the alphabetically first name.
    """
    if train_report.get("split") != "train" or train_report.get("test_cases_loaded") is not False:
        raise ValueError("the best heuristic must be chosen from a TRAIN benchmark report "
                         "(split=train, test_cases_loaded=false), never from VALIDATION")
    added = _episode_index(train_report)
    scenarios = sorted({row["scenario_id"] for row in train_report["episodes"]})
    policies = sorted({row["policy"] for row in train_report["episodes"]})
    candidates = {}
    for policy in policies:
        if policy.startswith(("base-", "ft-")) or policy in NOT_HEURISTIC_CANDIDATES:
            continue
        deltas = [added[(policy, budget, s)] - added[("noop", budget, s)] for s in scenarios
                  if (policy, budget, s) in added and ("noop", budget, s) in added]
        if deltas:
            candidates[policy] = statistics.fmean(deltas)
    if not candidates:
        raise ValueError("the TRAIN report has no heuristic paired with no-op at B=%d" % budget)
    best = min(candidates, key=lambda name: (candidates[name], name))
    return {
        "best_heuristic": best,
        "budget": budget,
        "candidates_mean_delta_ha_vs_noop": candidates,
        "rule": "largest mean reduction versus no-op at B=%d on TRAIN; no-op and random_legal "
                "excluded; ties to the alphabetically first name" % budget,
        "source_split": "train",
    }


def contrasts(report: dict, base_budget: int = 2, best_heuristic=None) -> dict:
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

    def seed_averaged(fmt_a, fmt_b, budget, role):
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
            "role": role,
            "per_seed_mean_delta_ha": per_seed,
            "seed_averaged_mean_delta_ha": float(scenario_means.mean()),
            "scenario_bootstrap_95ci_ha": _bootstrap(scenario_means),
            "seed_t95ci_ha": _seed_t_interval(list(per_seed.values())),
            "two_level_bootstrap_95ci_ha": _two_level_bootstrap(stacked),
            "scenarios_better": int((scenario_means < 0).sum()),
            "scenarios_worse": int((scenario_means > 0).sum()),
            "scenarios": len(scenarios),
            **sign_flip_test(scenario_means),
            **leave_largest_out(scenario_means, scenarios),
        }

    output = {"seeds": seeds, "budgets": budgets, "scenarios": len(scenarios), "by_budget": {}}
    for budget in budgets:
        entry = {}
        has_finetune = bool(seeds) and ("ft-b%d-s%d" % (budget, seeds[0])) in policies
        if has_finetune:
            entry["finetuned_minus_frozen_base"] = seed_averaged(
                "ft-b%d-s{seed}" % budget, "base-s{seed}", budget, "secondary")
            if budget != base_budget:
                entry["finetuned_minus_matched_control"] = seed_averaged(
                    "ft-b%d-s{seed}" % budget, "ft-b%d-s{seed}" % base_budget, budget, "secondary")
        if seeds:
            entry["frozen_base_minus_noop"] = seed_averaged(
                "base-s{seed}", "noop", budget, "sanity_check")
            if has_finetune:
                entry["finetuned_minus_noop"] = seed_averaged(
                    "ft-b%d-s{seed}" % budget, "noop", budget, "sanity_check")
        heuristics = {}
        for policy in policies:
            if policy.startswith(("base-", "ft-")) or policy == "noop":
                continue
            deltas = paired(policy, "noop", budget)
            if deltas:
                ids = [s for s in scenarios if (policy, budget, s) in added and ("noop", budget, s) in added]
                heuristics[policy] = {
                    "role": "sanity_check",
                    "mean_delta_ha_vs_noop": statistics.fmean(deltas),
                    "scenario_bootstrap_95ci_ha": _bootstrap(deltas),
                    **sign_flip_test(deltas),
                    **leave_largest_out(deltas, ids),
                }
        entry["heuristics_minus_noop"] = heuristics
        noop = [added[("noop", budget, s)] for s in scenarios if ("noop", budget, s) in added]
        entry["noop_mean_added_ha"] = statistics.fmean(noop) if noop else None
        output["by_budget"][str(budget)] = entry
    if best_heuristic is not None:
        output["primary"] = _primary_family(seed_averaged, seeds, policies, best_heuristic)
    return output


def _primary_family(seed_averaged, seeds, policies, selection) -> dict:
    """ADR-030 section 4: six primary tests with Holm across all six."""
    best = selection["best_heuristic"]
    tests = {}
    for budget in PRIMARY_BUDGETS:
        for label, comparator in (("random_legal", "random_legal"), ("best_heuristic", best)):
            if not seeds or comparator not in policies:
                continue
            result = seed_averaged("base-s{seed}", comparator, budget, "primary")
            if result is not None:
                result["comparator"] = comparator
                tests["B%d_base_minus_%s" % (budget, label)] = result
    adjusted = holm_correction({key: value["sign_flip_p_two_sided"] for key, value in tests.items()},
                               alpha=HOLM_ALPHA, family_size=PRIMARY_FAMILY_SIZE)
    for key, value in tests.items():
        value.update(adjusted[key])
    return {
        "best_heuristic": best,
        "family_size": PRIMARY_FAMILY_SIZE,
        "alpha": HOLM_ALPHA,
        "correction": "Holm step-down across the six primary tests; missing tests stay in the family",
        "complete": len(tests) == PRIMARY_FAMILY_SIZE,
        "tests": tests,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--train-report", type=Path, required=True,
                        help="TRAIN benchmark report used only to choose the best heuristic at B=2")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = json.loads(args.report.read_text(encoding="utf-8"))
    if report.get("test_cases_loaded") is not False:
        parser.error("refusing a report that loaded TEST cases")
    if args.train_report.resolve() == args.report.resolve():
        parser.error("the TRAIN selection report must be a separate file from the analysed report")
    train_report = json.loads(args.train_report.read_text(encoding="utf-8"))
    try:
        selection = select_best_train_heuristic(train_report)
    except ValueError as exc:
        parser.error(str(exc))
    for key in ("sim_params", "line_placement", "weather_observation"):
        if train_report.get(key) != report.get(key):
            parser.error("the TRAIN selection report differs from the analysed report in %s" % key)
    selection["source_report"] = str(args.train_report)
    selection["source_report_sha256"] = hashlib.sha256(args.train_report.read_bytes()).hexdigest()
    result = {
        "source_split": report["split"],
        "sim_params": report["sim_params"],
        "params_gate_status": report.get("params_gate_status"),
        "best_heuristic_selection": selection,
        "contrast_roles": {
            "primary": "contrasts.primary (ADR-030 section 4, Holm across six tests)",
            "secondary": "fine-tuned minus frozen base and minus matched control",
            "sanity_check": "every contrast against no-op",
        },
        "contrasts": contrasts(report, best_heuristic=selection),
    }
    text = json.dumps(result, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
