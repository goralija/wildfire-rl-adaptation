#!/usr/bin/env python3
"""Exhaustive TRAIN-only B=1 table, with paired raw/line-charged outcomes (ADR-033).

Never opens future FEDS geometries, VALIDATION, TEST or PPO checkpoints. All 33
sequences run to the same 48h horizon. Local per-case files support guarded resume.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from wildfire_rl.feds_b1 import action_sequences, audit_reference
from wildfire_rl.feds_simfire_setup import MANIFEST, SimFireParams, load_split_cases, sha256_file


def json_write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def rollout(env, scenario_id, sequence=None, policy=None, capture=False):
    import numpy as np
    from wildfire_rl.feds_simfire_env import line_points_for
    observation, _ = env.reset(seed=0, options={"scenario_id": scenario_id, "budget": 1})
    initial = env.cumulative_burned.copy()
    lines = np.zeros_like(initial)
    observations, masks, actions, legal = [], [], [], []
    for k in range(4):
        mask = env.action_masks()
        if capture:
            observations.append({key: value.tolist() for key, value in observation.items()})
            masks.append(mask.tolist())
        requested = int(sequence[k] if sequence is not None else policy(observation, mask))
        allowed = bool(mask[requested])
        action = requested if allowed else 0
        legal.append(allowed)
        if action:
            points = line_points_for(env.line_placement, env.simulation.fire_map,
                                    env.simulation.fire_map == 1, action - 1)
            for x, y in points:
                lines[y, x] = True
        observation, _, done, truncated, _ = env.step(action)
        if bool(done or truncated) != (k == 3):
            raise ValueError("episode did not keep the four-decision horizon")
        actions.append(action)
    return {"initial": initial, "burned": env.cumulative_burned.copy(), "lines": lines,
            "actions": actions, "legal": legal, "observations": observations, "masks": masks}


def run_case(job):
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import numpy as np
    from wildfire_rl.feds_heuristics import HEURISTICS, make_heuristic
    from wildfire_rl.feds_simfire_env import FedsSimFireEnv
    from wildfire_rl.line_damage import score_line_damage

    scenario_id, settings, out_dir = job
    case_path = Path(out_dir) / (scenario_id + ".json")
    mask_path = case_path.with_suffix(".npz")
    if case_path.exists():
        previous = json.loads(case_path.read_text())
        if previous["settings"] != settings or not mask_path.is_file() or \
                sha256_file(mask_path) != previous["mask_file_sha256"]:
            raise ValueError("resume settings/mask mismatch for " + scenario_id)
        from wildfire_rl.feds_simfire_setup import load_case_inputs
        current = load_case_inputs(scenario_id, split="train",
                                   weather_path=Path(settings["weather_path"]),
                                   input_root=Path(settings["input_root"]))
        if current["receipt_sha256"] != previous["input_receipt_sha256"]:
            raise ValueError("resume input receipt changed for " + scenario_id)
        return {"scenario_id": scenario_id, "resumed": True, "seconds": previous["seconds"]}
    started = time.monotonic()
    env = FedsSimFireEnv(sim_params=SimFireParams(**settings["params"]), split="train",
                         budgets=(1,), max_budget=4, scenario_ids=[scenario_id],
                         line_placement="front_edge", weather_observation="previous",
                         weather_path=Path(settings["weather_path"]),
                         input_root=Path(settings["input_root"]))
    sequences = action_sequences()
    noop = rollout(env, scenario_id, sequences[0], capture=True)
    outcomes, burned, line_masks = [], [], []
    for index, sequence in enumerate(sequences):
        result = noop if index == 0 else rollout(env, scenario_id, sequence)
        score = score_line_damage(noop["initial"], result["burned"], noop["burned"], result["lines"])
        edge = result["burned"][0, :].any() or result["burned"][-1, :].any() or \
            result["burned"][:, 0].any() or result["burned"][:, -1].any()
        outcomes.append({"requested_actions": list(sequence), "effective_actions": result["actions"],
                         "legal": result["legal"], "edge_contact": bool(edge), **score})
        burned.append(result["burned"])
        line_masks.append(result["lines"])
    repeated = rollout(env, scenario_id, sequences[0])
    if not np.array_equal(noop["burned"], repeated["burned"]):
        raise ValueError("no-op is not deterministic for " + scenario_id)
    references = {}
    for name in HEURISTICS:
        result = rollout(env, scenario_id, policy=make_heuristic(name, seed=0))
        score = score_line_damage(noop["initial"], result["burned"], noop["burned"], result["lines"])
        audit_reference(outcomes, result["actions"], score["raw_damage_cells"])
        # Stronger than area equality: the independent rollout must match the full mask.
        matching = next(i for i, row in enumerate(outcomes)
                        if row["effective_actions"] == result["actions"])
        if not np.array_equal(burned[matching], result["burned"]):
            raise ValueError("reference burn-mask mismatch for " + scenario_id)
        references[name] = {"actions": result["actions"], **score}
    receipt = env._input_cache[scenario_id]
    np.savez_compressed(mask_path, initial=noop["initial"], noop=noop["burned"],
                        agent_burned=np.stack(burned), line_cells=np.stack(line_masks))
    record = {"schema_version": "feds-b1-case/1.0", "scenario_id": scenario_id,
              "split": "train", "settings": settings,
              "input_receipt_sha256": receipt["receipt_sha256"],
              "observations": noop["observations"], "action_masks": noop["masks"],
              "outcomes": outcomes, "references": references, "reference_check": "PASS",
              "mask_file_sha256": sha256_file(mask_path), "seconds": time.monotonic() - started}
    json_write(case_path, record)
    env.close()
    return {"scenario_id": scenario_id, "resumed": False, "seconds": record["seconds"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weather", type=Path, required=True)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--case-limit", type=int)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args(argv)
    if not 1 <= args.workers <= 4 or args.case_limit is not None and args.case_limit < 1:
        parser.error("use 1–4 workers and a positive case limit")
    plan_path = ROOT / "configs/frozen/feds-b1-exploration-v1.json"
    plan = json.loads(plan_path.read_text())
    frozen_path = ROOT / plan["params_file"]
    params = json.loads(frozen_path.read_text())["frozen_params"]
    weather = json.loads(args.weather.read_text())
    if any(c["split"] != "train" for c in weather["cases"]):
        parser.error("the weather file must contain TRAIN records only")
    ids = sorted(load_split_cases("train"))
    if set(ids) != {c["scenario_id"] for c in weather["cases"]}:
        parser.error("weather must cover exactly the TRAIN cohort")
    ids = ids[:args.case_limit] if args.case_limit else ids
    source_paths = [ROOT / "src/wildfire_rl" / name for name in
                    ("feds_b1.py", "line_damage.py", "feds_simfire_env.py",
                     "feds_simfire_setup.py", "gridmet_weather.py", "feds_heuristics.py")]
    source_paths.append(Path(__file__))
    settings = {"params": params, "weather_path": str(args.weather.resolve()),
                "weather_sha256": sha256_file(args.weather),
                "input_root": str(args.input_root.resolve()),
                "manifest_sha256": sha256_file(MANIFEST), "plan_sha256": sha256_file(plan_path),
                "source_hashes": {str(p.relative_to(ROOT)): sha256_file(p) for p in source_paths}}
    args.out.mkdir(parents=True, exist_ok=True)
    jobs = [(scenario_id, settings, str(args.out)) for scenario_id in ids]
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_case, job) for job in jobs]
        for done, future in enumerate(as_completed(futures), 1):
            print(json.dumps({"done": done, "total": len(jobs), **future.result()}), flush=True)
    summary = {"schema_version": "feds-b1-table/1.0", "created_utc": datetime.now(timezone.utc).isoformat(),
               "label": "TRAIN EXPLORATION; NOT PHYSICAL VALIDATION", "split": "train",
               "validation_used": False, "test_cases_loaded": False, "case_count": len(ids),
               "settings": settings, "code_commit": subprocess.check_output(
                   ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               "cases": [{"scenario_id": key, "file": key + ".json",
                          "sha256": sha256_file(args.out / (key + ".json"))} for key in ids],
               "wall_clock_minutes": (time.monotonic() - started) / 60}
    json_write(args.out / ("table-%d.json" % len(ids)), summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
