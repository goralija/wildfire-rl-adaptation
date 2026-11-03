#!/usr/bin/env python3
"""Paired budgeted policy benchmark on the FEDS/SimFire environment.

Every policy is run on the same scenarios, budgets, 48h horizon, simulator
parameters and observations. Damage is cumulative SimFire-burned area added after
the observed FEDS start (cells, then hectares). VALIDATION requires a committed
TRAIN parameter freeze record; TEST is never loaded. This is a simulator benchmark,
not physical validation of suppression effectiveness.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

HECTARES_PER_CELL = 180.0 * 180.0 / 10000.0


def _policy_for(spec: str, seed: int):
    """``heuristic:<name>`` or ``ppo:<checkpoint.zip>``."""
    kind, _, value = spec.partition(":")
    if kind == "heuristic":
        from wildfire_rl.feds_heuristics import make_heuristic

        return make_heuristic(value, seed=seed)
    if kind == "ppo":
        import torch
        from sb3_contrib import MaskablePPO

        torch.set_num_threads(1)
        model = MaskablePPO.load(value, device="cpu")

        def policy(observation, mask):
            action, _state = model.predict(observation, action_masks=mask, deterministic=True)
            return int(action)

        return policy
    raise ValueError("policy spec must be heuristic:<name> or ppo:<checkpoint>")


def _run_job(job):
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    from wildfire_rl.feds_simfire_env import FedsSimFireEnv
    from wildfire_rl.feds_simfire_setup import SimFireParams

    scenario_id, budgets, policies, params, split, placement, seed = job
    env = FedsSimFireEnv(
        sim_params=SimFireParams(**params),
        budgets=tuple(sorted(set(budgets) | {0})),
        scenario_ids=[scenario_id],
        split=split,
        line_placement=placement,
        max_budget=4,
    )
    rows = []
    for name, spec in policies.items():
        policy = _policy_for(spec, seed)
        for budget in budgets:
            observation, info = env.reset(seed=seed, options={"scenario_id": scenario_id, "budget": budget})
            initial_cells = int(env.cumulative_burned.sum())
            actions, applied, invalid = [], 0, 0
            done = False
            while not done:
                action = policy(observation, env.action_masks())
                observation, _reward, terminated, truncated, step_info = env.step(action)
                actions.append(int(action))
                applied += int(step_info["action_applied"])
                invalid += int(step_info["invalid_action"])
                done = bool(terminated or truncated)
            added = int(env.cumulative_burned.sum()) - initial_cells
            rows.append({
                "scenario_id": scenario_id,
                "policy": name,
                "budget": budget,
                "actions": actions,
                "lines_applied": applied,
                "invalid_actions": invalid,
                "budget_left": int(env.remaining_budget),
                "initial_burned_cells": initial_cells,
                "added_burned_cells": added,
                "added_burned_ha": added * HECTARES_PER_CELL,
            })
    return rows


def paired_summary(rows: list, reference: str = "noop") -> dict:
    """Mean added hectares per policy and budget, and paired deltas against a reference."""
    by_key = {(row["scenario_id"], row["policy"], row["budget"]): row for row in rows}
    policies = sorted({row["policy"] for row in rows})
    budgets = sorted({row["budget"] for row in rows})
    scenarios = sorted({row["scenario_id"] for row in rows})
    summary = {}
    for policy in policies:
        summary[policy] = {}
        for budget in budgets:
            values = [by_key[(s, policy, budget)]["added_burned_ha"] for s in scenarios
                      if (s, policy, budget) in by_key]
            deltas = [
                by_key[(s, policy, budget)]["added_burned_ha"] - by_key[(s, reference, budget)]["added_burned_ha"]
                for s in scenarios
                if (s, policy, budget) in by_key and (s, reference, budget) in by_key
            ]
            entry = {
                "episodes": len(values),
                "mean_added_ha": statistics.fmean(values) if values else None,
                "median_added_ha": statistics.median(values) if values else None,
            }
            if deltas:
                entry.update(_paired_bootstrap(deltas))
                entry["reference"] = reference
                entry["episodes_better_than_reference"] = sum(delta < 0 for delta in deltas)
                entry["episodes_worse_than_reference"] = sum(delta > 0 for delta in deltas)
            summary[policy][str(budget)] = entry
    return summary


def _paired_bootstrap(deltas: list, draws: int = 4000, seed: int = 20261104) -> dict:
    import numpy as np

    values = np.asarray(deltas, dtype=float)
    generator = np.random.default_rng(seed)
    samples = generator.choice(values, size=(draws, values.size), replace=True).mean(axis=1)
    return {
        "mean_delta_ha_vs_reference": float(values.mean()),
        "bootstrap_95ci_delta_ha": [float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("train", "validation"), default="train")
    parser.add_argument("--params", type=Path, required=True,
                        help="JSON with frozen_params (and selected_on_split=train for VALIDATION)")
    parser.add_argument("--budgets", default="0,1,2,4")
    parser.add_argument("--policy", action="append", default=[],
                        help="name=heuristic:<name> or name=ppo:<checkpoint>; repeatable")
    parser.add_argument("--line-placement", choices=("centroid", "front_edge"), default="front_edge")
    parser.add_argument("--scenario-limit", type=int)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("output exists; choose a new path")

    from wildfire_rl.feds_simfire_setup import load_split_cases, sha256_file

    freeze = json.loads(args.params.read_text(encoding="utf-8"))
    params = freeze["frozen_params"]
    if args.split == "validation" and freeze.get("selected_on_split") != "train":
        parser.error("VALIDATION benchmarks require parameters selected on TRAIN.")
    budgets = [int(value) for value in args.budgets.split(",")]
    policies = dict(item.split("=", 1) for item in args.policy) or {
        "noop": "heuristic:noop",
        "random_legal": "heuristic:random_legal",
        "downwind": "heuristic:downwind",
        "advancing_front": "heuristic:advancing_front",
    }
    if "noop" not in policies:
        policies["noop"] = "heuristic:noop"
    scenarios = sorted(load_split_cases(args.split))
    if args.scenario_limit:
        scenarios = scenarios[: args.scenario_limit]
    jobs = [(scenario, budgets, policies, params, args.split, args.line_placement, args.seed)
            for scenario in scenarios]

    started = time.monotonic()
    rows, errors = [], []
    if args.workers > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed

        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(_run_job, job): job[0] for job in jobs}
            for future in as_completed(futures):
                try:
                    rows.extend(future.result())
                except Exception as exc:
                    errors.append({"scenario_id": futures[future], "error": "%s: %s" % (type(exc).__name__, exc)})
                print("%d/%d done (%.1f min)" % (len(rows) // max(1, len(policies) * len(budgets)) + len(errors),
                                                  len(jobs), (time.monotonic() - started) / 60), flush=True)
    else:
        for job in jobs:
            try:
                rows.extend(_run_job(job))
            except Exception as exc:
                errors.append({"scenario_id": job[0], "error": "%s: %s" % (type(exc).__name__, exc)})

    payload = {
        "schema_version": "feds-simfire-policy-benchmark/1.0",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SIMULATOR BENCHMARK; NOT PHYSICAL VALIDATION OF SUPPRESSION",
        "split": args.split,
        "test_cases_loaded": False,
        "params_file_sha256": sha256_file(args.params),
        "sim_params": params,
        "params_gate_status": freeze.get("gate_status"),
        "line_placement": args.line_placement,
        "budgets": budgets,
        "policies": policies,
        "seed": args.seed,
        "scenario_count": len(scenarios),
        "errors": errors,
        "runtime_minutes": (time.monotonic() - started) / 60.0,
        "summary": paired_summary(rows),
        "episodes": sorted(rows, key=lambda row: (row["scenario_id"], row["policy"], row["budget"])),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "errors": len(errors), "summary": payload["summary"]}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
