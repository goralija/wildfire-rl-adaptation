#!/usr/bin/env python3
"""Paired evaluation of scripted tactics (and optionally a PPO checkpoint) on fixed
synthetic validation seeds of the ADR-028 environment. Simulator-only results.

Saved fraction is the primary outcome; close calls and units lost are a separate safety
block; return (saved minus safety penalties) is the training objective. Every policy is
contrasted with no-op, random and the best heuristic (paired bootstrap, 95% CI) by
``wildfire_rl.synthetic_stats``. ``--subset-from-seed 64`` adds the selection-free seeds."""

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

from wildfire_rl.synthetic_env import Curriculum, SyntheticSuppressionEnv  # noqa: E402
from wildfire_rl.synthetic_heuristics import HEURISTICS, make_random_policy, run_episode  # noqa: E402
from wildfire_rl.synthetic_stats import format_table, summarize_groups  # noqa: E402


def _curriculum(name: str) -> Curriculum:
    if name == "full":
        return Curriculum()
    if name == "short":
        return Curriculum(horizons=(12,), unit_counts=(2, 3))
    raise ValueError(name)


_MODELS = {}


def _predictor(path: str):
    """Deterministic masked PPO predictor; one loaded model per worker process."""
    if path not in _MODELS:
        import torch
        from sb3_contrib import MaskablePPO
        torch.set_num_threads(1)
        _MODELS[path] = MaskablePPO.load(path, device="cpu")
    model = _MODELS[path]

    def predict(obs, mask):
        action, _ = model.predict({k: v[None] for k, v in obs.items()},
                                  action_masks=mask[None], deterministic=True)
        return action[0]

    return predict


def _job(args):
    seed, policies, curriculum = args
    env = SyntheticSuppressionEnv(curriculum=_curriculum(curriculum))
    rows = {}
    for name in policies:
        if name.startswith("ppo="):
            rows[name] = run_episode(env, None, {"seed": seed}, predictor=_predictor(name[4:]))
            continue
        policy = make_random_policy(seed) if name == "random" else HEURISTICS[name]
        rows[name] = run_episode(env, policy, {"seed": seed})
    return seed, rows


def seed_groups(seeds, subsets):
    """Index groups over ``seeds``: all, plus one group per ``--subset-from-seed`` value."""
    groups = {"all": list(range(len(seeds)))}
    for first in subsets:
        groups["seeds_%d_to_%d" % (first, seeds[-1])] = [i for i, s in enumerate(seeds) if s >= first]
    return groups


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=128)
    parser.add_argument("--first-seed", type=int, default=0)
    parser.add_argument("--curriculum", default="full")
    parser.add_argument("--policies", default="noop,random,direct_flank,downwind_indirect,protect_urban")
    parser.add_argument("--workers", type=int, default=7)
    parser.add_argument("--subset-from-seed", type=int, action="append", default=[],
                        help="also report seeds >= this value (e.g. 64 for selection-free seeds)")
    parser.add_argument("--best-heuristic", default=None,
                        help="fix the reference tactic instead of the highest mean saved")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    policies = args.policies.split(",")
    seeds = list(range(args.first_seed, args.first_seed + args.seeds))
    with ProcessPoolExecutor(args.workers) as pool:
        results = dict(pool.map(_job, [(s, policies, args.curriculum) for s in seeds]))
    rows = {name: [results[s][name] for s in seeds] for name in policies}
    summary = summarize_groups(rows, seed_groups(seeds, args.subset_from_seed), main="all",
                               best_heuristic=args.best_heuristic)
    report = {"environment": "synthetic CA ADR-028 (simulator-only)", "curriculum": args.curriculum,
              "seeds": [seeds[0], seeds[-1] + 1], **summary,
              "per_seed": {str(s): results[s] for s in seeds}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1))
    for group, table in summary["groups"].items():
        print("== %s (best heuristic: %s)" % (group, table["best_heuristic"]))
        print("\n".join(format_table(table)))


if __name__ == "__main__":
    main()
