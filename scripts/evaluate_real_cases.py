#!/usr/bin/env python3
"""Final, one-time test of locked policies on the 119 local real FEDS cases (ADR-028).

Each case uses its real LANDFIRE fuel and elevation, its gridMET weather and its real
initial FEDS perimeter; spread is computed by the synthetic CA. Every policy sees the same
case, units (``DEFAULT_UNITS``), horizon (48h) and random numbers. Ex-train and
ex-validation cases are reported separately. The outcome is simulated, not observed:
the real fires had no agent in them. Refuses to run without ``--policy-locked``.
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

import numpy as np  # noqa: E402

from wildfire_rl.synthetic_env import SyntheticSuppressionEnv  # noqa: E402
from wildfire_rl.synthetic_heuristics import HEURISTICS, make_random_policy, run_episode  # noqa: E402
from wildfire_rl.synthetic_real_cases import load_real_episode_specs  # noqa: E402

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


def _paired(a, b, rng, draws=4000):
    diff = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    if not diff.size:
        return None
    boots = [rng.choice(diff, diff.size).mean() for _ in range(draws)]
    return [float(diff.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]


def _sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policies", required=True,
                        help="comma list, e.g. noop,random,direct_flank,ppo=path/best_model.zip")
    parser.add_argument("--policy-locked", action="store_true")
    parser.add_argument("--workers", type=int, default=7)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not args.policy_locked:
        parser.error("the real-case test runs once, after the policy is locked: pass --policy-locked")
    policies = args.policies.split(",")
    ids = list(_cases())
    with ProcessPoolExecutor(args.workers) as pool:
        results = list(pool.map(_job, [(i, policies) for i in ids]))

    rng = np.random.default_rng(0)
    groups = {"ex_train": [r for r in results if r[1]["split"] == "train"],
              "ex_validation": [r for r in results if r[1]["split"] == "validation"]}
    groups["all"] = results
    groups["all_in_crop"] = [r for r in results if not r[1].get("initial_cells_outside_crop")]
    summary = {}
    for group, rows in groups.items():
        table = {}
        for name in policies:
            saved = [r[2][name]["saved_fraction"] for r in rows]
            table[name] = {
                "cases": len(rows),
                "mean_saved_fraction": float(np.mean(saved)),
                "median_saved_fraction": float(np.median(saved)),
                "mean_return": float(np.mean([r[2][name]["return"] for r in rows])),
                "units_lost": int(sum(r[2][name]["units_lost"] for r in rows)),
                "close_calls": int(sum(r[2][name].get("close_calls", 0) for r in rows)),
                "new_cells_burned": int(sum(r[2][name]["agent_new_cells"] for r in rows)),
                "noop_new_cells_burned": int(sum(r[2][name]["noop_new_cells"] for r in rows)),
                "urban_cells_burned": float(sum(r[2][name]["agent_urban_cells"] for r in rows)),
                "noop_urban_cells_burned": float(sum(r[2][name]["noop_urban_cells"] for r in rows)),
                "edge_contact_cases": int(sum(r[2][name]["edge_contact"] for r in rows)),
            }
            for other in policies:
                if other != name and (name.startswith("ppo=") or other == "noop"):
                    table[name]["saved_minus_%s_ci95" % other] = _paired(
                        saved, [r[2][other]["saved_fraction"] for r in rows], rng)
        summary[group] = table
    receipt = {
        "environment": "synthetic CA ADR-028 on real FEDS/LANDFIRE/gridMET starts (simulated outcome)",
        "policies": policies,
        "checkpoints": {p: _sha256(p[4:]) for p in policies if p.startswith("ppo=")},
        "test_2024_loaded": False,
        "summary": summary,
        "per_case": {sid: {"metadata": meta, "results": rows} for sid, meta, rows in results},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=1, default=str))
    for group in ("ex_train", "ex_validation"):
        print(group)
        for name, row in summary[group].items():
            print("  ", name, {k: (round(v, 4) if isinstance(v, float) else v)
                               for k, v in row.items() if not k.endswith("ci95")})


if __name__ == "__main__":
    main()
