#!/usr/bin/env python3
"""Final, one-time test of locked policies on the 119 local real FEDS cases (ADR-028).

Each case uses its real LANDFIRE fuel and elevation, its gridMET weather and its real
initial FEDS perimeter; spread is computed by the synthetic CA. Every policy sees the same
case, units (``DEFAULT_UNITS``), horizon (48h) and random numbers. Ex-train and
ex-validation cases are reported separately. The outcome is simulated, not observed:
the real fires had no agent in them. Refuses to run without ``--policy-locked``.

Saved fraction is the primary outcome; close calls and units lost are a separate safety
block; return (saved minus safety penalties) is the training objective. Every policy is
contrasted with no-op, random and the comparator heuristic (paired bootstrap, 95% CI)
by ``wildfire_rl.synthetic_stats``, for each group including the no-edge, in-crop subset.
The comparator is fixed up front with ``--comparator-heuristic`` (the synthetic acceptance
comparator), never chosen on these cases. This run is descriptive: acceptance (ADR-030
section 5) is decided on the synthetic seeds, so no pass/fail is printed here. The
per-case results are written before any summary, so a summary error cannot lose the run.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("OMP_NUM_THREADS", "1")

from wildfire_rl.synthetic_env import SyntheticSuppressionEnv  # noqa: E402
from wildfire_rl.synthetic_heuristics import HEURISTICS, make_random_policy, run_episode  # noqa: E402
from wildfire_rl.synthetic_real_cases import load_real_episode_specs  # noqa: E402
from wildfire_rl.synthetic_stats import (  # noqa: E402
    format_table, real_case_groups, summarize_groups, validate_comparator)

_CASES = {}


def _cases():
    if "all" not in _CASES:
        _CASES["all"] = {spec.name: (spec, meta) for spec, meta in load_real_episode_specs()}
    return _CASES["all"]


def _job(args):
    scenario_id, policies = args
    from evaluate_synthetic_policies import _predictor
    spec, meta = _cases()[scenario_id]
    env = SyntheticSuppressionEnv()
    rows = {}
    for name in policies:
        options = {"episode_spec": spec}
        if name.startswith("ppo="):
            rows[name] = run_episode(env, None, options, predictor=_predictor(name[4:]))
        else:
            policy = make_random_policy(spec.seed) if name == "random" else HEURISTICS[name]
            rows[name] = run_episode(env, policy, options)
    return scenario_id, meta, rows


def _sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policies", required=True,
                        help="comma list, e.g. noop,random,direct_flank,ppo=path/best_model.zip")
    parser.add_argument("--policy-locked", action="store_true")
    parser.add_argument("--comparator-heuristic", required=True,
                        help="reference tactic fixed before the run (the synthetic acceptance "
                             "comparator), e.g. direct_flank; never chosen on the real cases")
    parser.add_argument("--workers", type=int, default=7)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not args.policy_locked:
        parser.error("the real-case test runs once, after the policy is locked: pass --policy-locked")
    policies = args.policies.split(",")
    try:
        validate_comparator(args.comparator_heuristic, policies)
    except ValueError as exc:
        parser.error(str(exc))
    ids = list(_cases())
    with ProcessPoolExecutor(args.workers) as pool:
        results = list(pool.map(_job, [(i, policies) for i in ids]))

    receipt = {
        "environment": "synthetic CA ADR-028 on real FEDS/LANDFIRE/gridMET starts (simulated outcome)",
        "policies": policies,
        "comparator_heuristic": args.comparator_heuristic,
        "checkpoints": {p: _sha256(p[4:]) for p in policies if p.startswith("ppo=")},
        "test_2024_loaded": False,
        "per_case": {sid: {"metadata": meta, "results": rows} for sid, meta, rows in results},
    }
    # Persist the one-time run before summarising it.
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=1, default=str))
    by_policy = {name: [r[2][name] for r in results] for name in policies}
    summary = summarize_groups(by_policy, real_case_groups(results), main="all",
                               best_heuristic=args.comparator_heuristic, acceptance=False)
    receipt.update(summary)
    args.out.write_text(json.dumps(receipt, indent=1, default=str))
    for group, table in summary["groups"].items():
        cases = 0 if table.get("empty") else table["policies"][policies[0]]["episodes"]
        print("== %s (%d cases, comparator: %s; descriptive, no acceptance verdict)"
              % (group, cases, table["best_heuristic"]))
        print("\n".join(format_table(table)))


if __name__ == "__main__":
    main()
