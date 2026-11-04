#!/usr/bin/env python3
"""Paired evaluation of scripted tactics (and optionally a PPO checkpoint) on fixed
synthetic validation seeds of the ADR-028 environment. Simulator-only results."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np  # noqa: E402

from wildfire_rl.synthetic_env import Curriculum, SyntheticSuppressionEnv  # noqa: E402
from wildfire_rl.synthetic_heuristics import HEURISTICS, make_random_policy, run_episode  # noqa: E402


def _curriculum(name: str) -> Curriculum:
    if name == "full":
        return Curriculum()
    if name == "short":
        return Curriculum(horizons=(12,), unit_counts=(2, 3))
    raise ValueError(name)


def _job(args):
    seed, policies, curriculum = args
    env = SyntheticSuppressionEnv(curriculum=_curriculum(curriculum))
    rows = {}
    for name in policies:
        policy = make_random_policy(seed) if name == "random" else HEURISTICS[name]
        rows[name] = run_episode(env, policy, {"seed": seed})
    return seed, rows


def paired_ci(a, b, rng, draws=4000):
    diff = np.asarray(a) - np.asarray(b)
    boots = [rng.choice(diff, diff.size).mean() for _ in range(draws)]
    return float(diff.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=128)
    parser.add_argument("--first-seed", type=int, default=0)
    parser.add_argument("--curriculum", default="full")
    parser.add_argument("--policies", default="noop,random,direct_flank,downwind_indirect,protect_urban")
    parser.add_argument("--workers", type=int, default=7)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    policies = args.policies.split(",")
    seeds = range(args.first_seed, args.first_seed + args.seeds)
    with ProcessPoolExecutor(args.workers) as pool:
        results = dict(pool.map(_job, [(s, policies, args.curriculum) for s in seeds]))
    rng = np.random.default_rng(0)
    table = {}
    for name in policies:
        rows = [results[s][name] for s in seeds]
        saved = [r["saved_fraction"] for r in rows]
        table[name] = {
            "mean_saved_fraction": float(np.mean(saved)),
            "median_saved_fraction": float(np.median(saved)),
            "mean_return": float(np.mean([r["return"] for r in rows])),
            "units_lost": int(sum(r["units_lost"] for r in rows)),
            "urban_cells_burned": float(sum(r["agent_urban_cells"] for r in rows)),
            "noop_urban_cells_burned": float(sum(r["noop_urban_cells"] for r in rows)),
            "new_cells_burned": int(sum(r["agent_new_cells"] for r in rows)),
            "noop_new_cells_burned": int(sum(r["noop_new_cells"] for r in rows)),
            "edge_contact_episodes": int(sum(r["edge_contact"] for r in rows)),
            "line_cells": int(sum(r["line_cells"] for r in rows)),
        }
        if "random" in policies and name != "random":
            table[name]["return_minus_random_ci95"] = paired_ci(
                [r["return"] for r in rows], [results[s]["random"]["return"] for s in seeds], rng)
    report = {"environment": "synthetic CA ADR-028 (simulator-only)", "curriculum": args.curriculum,
              "seeds": [seeds.start, seeds.stop], "policies": table,
              "per_seed": {str(s): results[s] for s in seeds}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1))
    for name, row in table.items():
        print(name, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()})


if __name__ == "__main__":
    main()
