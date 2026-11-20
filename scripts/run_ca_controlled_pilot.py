#!/usr/bin/env python3
"""Run only the fixed procedural development cases of ADR-039, never checkpoints."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[variable] = "1"

import gymnasium
import numpy as np
import scipy

from wildfire_rl.ca_controlled import (
    CAObservationV2, clustered_contrast, observed_policy, validate_plan,
)
from wildfire_rl.synthetic_env import (
    ACTIONS_PER_UNIT, CELL_AREA_HA, Curriculum, MAX_UNITS, SyntheticSuppressionEnv,
)

SOURCES = ["src/wildfire_rl/synthetic_ca.py", "src/wildfire_rl/synthetic_env.py",
           "src/wildfire_rl/synthetic_heuristics.py", "src/wildfire_rl/ca_controlled.py",
           "scripts/run_ca_controlled_pilot.py"]


def ensure_worker_nice():
    # macOS spawn does not reliably retain the parent's nice value.
    if hasattr(os, "getpriority"):
        if os.getpriority(os.PRIO_PROCESS, 0) < 19:
            os.setpriority(os.PRIO_PROCESS, 0, 19)
        if os.getpriority(os.PRIO_PROCESS, 0) < 19:
            raise RuntimeError("could not lower worker priority to nice 19")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def array_hash(array):
    a = np.ascontiguousarray(array)
    h = hashlib.sha256(str((a.shape, a.dtype.str)).encode())
    h.update(a.tobytes())
    return h.hexdigest()


def world_hash(spec):
    values = {name: array_hash(array) for name, array in {
        "fuel": spec.landscape.fuel, "elevation": spec.landscape.elevation,
        "ros_noise": spec.landscape.ros_noise, "scar": spec.scar, "front": spec.front,
    }.items()}
    values.update(weather=[asdict(w) for w in spec.weather.steps],
                  params=asdict(spec.params), seed=spec.seed, horizon=spec.horizon)
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def rollout(spec, policy_name, random_seed):
    env = CAObservationV2(SyntheticSuppressionEnv(map_shape=spec.landscape.shape))
    obs, _ = env.reset(options={"episode_spec": spec})
    base = env.unwrapped
    policy = observed_policy(policy_name, seed=random_seed)
    previous = base.fire.ever_burned.copy()
    previous_charge = base.line_charged.copy()
    total, done, decisions = 0.0, False, 0
    actions = []
    while not done:
        if not env.observation_space.contains(obs):
            raise AssertionError("observation outside versioned space")
        if not all(np.isfinite(v).all() for v in obs.values()):
            raise AssertionError("nonfinite observation")
        mask = env.action_masks().reshape(MAX_UNITS, ACTIONS_PER_UNIT)
        if not mask[:, 0].all():
            raise AssertionError("no-op must remain available")
        action = np.asarray(policy(obs, mask.ravel()), dtype=int)
        if (action.shape != (MAX_UNITS,) or (action < 0).any()
                or (action >= ACTIONS_PER_UNIT).any()
                or not mask[np.arange(MAX_UNITS), action].all()):
            raise AssertionError("policy returned an illegal action")
        actions.append(action.tolist())
        obs, reward, done, truncated, info = env.step(action)
        decisions += 1
        total += reward
        if truncated or info["invalid_actions"]:
            raise AssertionError("unexpected truncation or invalid action")
        if (previous & ~base.fire.ever_burned).any():
            raise AssertionError("cumulative damage was lost")
        if (previous_charge & ~base.line_charged).any():
            raise AssertionError("line charge was lost")
        previous = base.fire.ever_burned.copy()
        previous_charge = base.line_charged.copy()
    row = dict(info["episode_summary"])
    exact_damage = float(base.weights[(base.fire.ever_burned & ~base.prior_damage)
                                     | base.line_charged].sum())
    if not np.isclose(exact_damage, base.stats["agent_damage"], atol=1e-8):
        raise AssertionError("final union damage must match reward accounting")
    if not np.isclose(float(base.weights[base.line_charged].sum()), row["line_damage"]):
        raise AssertionError("line must be charged exactly once")
    expected = (row["saved_fraction"] - row["units_lost"] * base.unit_loss_penalty
                - row["close_calls"] * base.close_call_penalty)
    if not np.isclose(total, expected, atol=1e-9):
        raise AssertionError("return must reconcile with saved fraction and safety")
    if decisions < spec.horizon and base.fire.active:
        raise AssertionError("early termination while fire remains active")
    if policy_name == "noop":
        np.testing.assert_array_equal(base.fire.ever_burned, base.noop_final.ever_burned)
        if abs(row["saved_fraction"]) > 1e-12:
            raise AssertionError("no-op must save zero")
    row.update({
        "return": total, "decisions": decisions,
        "saved_ha_unweighted_line_charged": CELL_AREA_HA * (
            row["noop_new_cells"] - row["agent_new_cells"]
            - row["line_cells_in_noop_footprint"]),
        "final_damage_sha256": array_hash(base.fire.ever_burned),
        "noop_final_sha256": array_hash(base.noop_final.ever_burned),
        "line_sha256": array_hash(base.fire.line),
        "actions_sha256": hashlib.sha256(json.dumps(actions).encode()).hexdigest(),
        "actions": actions, "contract_checks": "PASS",
    })
    return row


def job(task):
    seed, plan, guard, folder = task
    path = Path(folder) / (str(seed) + ".json")
    if path.exists():
        data = json.loads(path.read_text())
        if data["guard"] != guard or data["base_seed"] != seed:
            raise ValueError("resume rejected: source/plan/runtime/seed changed")
        return data
    started = time.monotonic()
    if hasattr(os, "getpriority") and os.getpriority(os.PRIO_PROCESS, 0) < 19:
        raise RuntimeError("run with nice -n 19")
    values = plan["generator"]
    curriculum = Curriculum(shape=tuple(values["shape"]), horizons=tuple(values["horizons"]),
                            unit_counts=tuple(values["unit_counts"]),
                            min_noop_growth_cells=values["min_noop_growth_cells"],
                            max_attempts=values["max_attempts"])
    sampler = SyntheticSuppressionEnv(curriculum=curriculum)
    sampler.reset(options={"seed": seed})
    original = sampler.spec_now
    fingerprint = world_hash(original)
    rows = {}
    noop_hash = None
    for roster, units in plan["rosters"].items():
        spec = replace(original, units=[tuple(unit) for unit in units])
        if world_hash(spec) != fingerprint:
            raise AssertionError("roster changed the underlying fire")
        rows[roster] = {}
        for name in plan["policies"]:
            row = rollout(spec, name, seed + 771)
            if noop_hash is not None and row["noop_final_sha256"] != noop_hash:
                raise AssertionError("policies/rosters must share the same no-op fire")
            noop_hash = row["noop_final_sha256"]
            rows[roster][name] = row
    data = {"base_seed": seed, "guard": guard, "world_sha256": fingerprint,
            "worker_nice": os.getpriority(os.PRIO_PROCESS, 0),
            "episode_seed": original.seed, "sample_name": original.name,
            "noop_growth_cells": int(sampler.noop_footprint.sum()),
            "growth_resample_exhausted": int(sampler.noop_footprint.sum()) < 30,
            "seconds": time.monotonic() - started, "rows": rows}
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=1, allow_nan=False) + "\n")
    temporary.replace(path)
    return data


def summarize(cases, plan):
    rosters = list(plan["rosters"])
    matrices = {policy: np.array([[case["rows"][b][policy]["saved_fraction"]
                                  for b in rosters] for case in cases])
                for policy in plan["policies"]}
    heuristics = [p for p in plan["policies"] if p not in ("noop", "random")]
    best = max(heuristics, key=lambda name: matrices[name].mean())
    result = {"development_reference": best, "policies": {},
              "note": "Descriptive development pilot; no learned policy, no acceptance. "
                      "Intervals cluster by case, including all rosters."}
    for name in plan["policies"]:
        rows = [case["rows"][b][name] for case in cases for b in rosters]
        result["policies"][name] = {
            "mean_saved_fraction": float(matrices[name].mean()),
            "median_saved_fraction": float(np.median(matrices[name])),
            "by_roster": {b: float(matrices[name][:, i].mean()) for i, b in enumerate(rosters)},
            "mean_saved_ha_unweighted_line_charged": float(np.mean([
                row["saved_ha_unweighted_line_charged"] for row in rows])),
            "units_lost": sum(row["units_lost"] for row in rows),
            "close_calls": sum(row["close_calls"] for row in rows),
            "line_cells": sum(row["line_cells"] for row in rows),
            "edge_episodes": sum(row["edge_contact"] for row in rows),
            "vs_random": clustered_contrast(matrices[name], matrices["random"]),
            "vs_development_reference": clustered_contrast(matrices[name], matrices[best]),
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=ROOT / "configs/frozen/ca-controlled-pilot-v2.json")
    parser.add_argument("--case-limit", type=int, default=16)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    validate_plan(plan)
    if not 1 <= args.workers <= 4 or not 1 <= args.case_limit <= 16:
        parser.error("workers 1..4 and development case limit 1..16 required")
    report_path = args.out / ("development-%d.json" % args.case_limit)
    if report_path.exists():
        parser.error("report exists; retain it and choose a new output folder")
    folder = args.out / "cases"
    folder.mkdir(parents=True, exist_ok=True)
    runtime = {"python": platform.python_version(), "numpy": np.__version__,
               "scipy": scipy.__version__, "gymnasium": gymnasium.__version__}
    guard = {"plan_sha256": sha(args.plan), "source_sha256": {s: sha(ROOT / s) for s in SOURCES},
             "runtime": runtime}
    seeds = plan["case_seeds"]["development"][:args.case_limit]
    started = time.monotonic()
    cases = []
    with ProcessPoolExecutor(args.workers, initializer=ensure_worker_nice) as pool:
        for case in pool.map(job, [(s, plan, guard, str(folder)) for s in seeds]):
            cases.append(case)
            print("PASS case %s (%d/%d)" % (case["base_seed"], len(cases), len(seeds)), flush=True)
    report = {"schema_version": "ca-controlled-pilot-result/2.0", "date": "2026-11-21",
              "guard": guard, "code_commit": subprocess.check_output(
                  ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "plan": plan, "cases": cases, "summary": summarize(cases, plan),
              "execution_seconds": time.monotonic() - started,
              "checks": "PASS", "closed_splits": ["train", "test", "all real cases"]}
    report_path.write_text(json.dumps(report, indent=1, allow_nan=False) + "\n")
    print(json.dumps(report["summary"], indent=1), flush=True)


if __name__ == "__main__":
    main()
