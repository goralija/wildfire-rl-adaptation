#!/usr/bin/env python3
"""Local viewer: run a locked policy on one real FEDS start in the synthetic CA (ADR-028).

Serves a page on localhost. Pick a real case (99 ex-train, 20 ex-validation) and a policy;
the page shows the policy's episode next to the no-op rollout of the same case (same
weather and random numbers), hour by hour, with units, line and the observed FEDS
perimeters as an outline. Outcomes are simulated; FEDS outlines show what the real
(suppressed) fire did. TEST 2024 is never loaded.
"""

from __future__ import annotations

import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import threading
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
os.chdir(ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np  # noqa: E402

from wildfire_rl.feds_simfire_setup import load_case_inputs, load_split_cases  # noqa: E402
from wildfire_rl.synthetic_ca import (  # noqa: E402
    AGRICULTURE, BARREN, BURNING, FUEL_GROUPS, SNOW, URBAN, WATER,
)
from wildfire_rl.synthetic_env import DECISION_MINUTES, SyntheticSuppressionEnv  # noqa: E402
from wildfire_rl.synthetic_heuristics import HEURISTICS, make_random_policy  # noqa: E402
from wildfire_rl.synthetic_real_cases import CROP, build_real_episode  # noqa: E402

HECTARES_PER_CELL = 3.24
LOCKED = ROOT / ".local/synthetic/locked"
MODELS = {
    "policy-v1 (BC + PPO, zaključan)": LOCKED / "policy-v1.zip",
    "bc-2 (samo imitacija)": LOCKED / "bc2.zip",
    "main-1 (PPO od nule)": LOCKED / "main1-best.zip",
}
HEURISTIC_LABELS = {
    "direct_flank": "heuristika: bočni napad",
    "protect_urban": "heuristika: zaštita naselja",
    "downwind_indirect": "heuristika: indirektna linija",
    "random": "nasumično",
    "noop": "bez intervencije (no-op)",
}
LOCK = threading.Lock()
_CACHE = {}


def _b64(array) -> str:
    return base64.b64encode(np.ascontiguousarray(array, dtype=np.uint8).tobytes()).decode("ascii")


def _cases():
    if "cases" not in _CACHE:
        rows = []
        for split in ("train", "validation"):
            for scenario_id, case in load_split_cases(split).items():
                rows.append({"id": scenario_id, "split": split,
                             "name": case["event"]["name"].title(),
                             "state": case["event"]["state"],
                             "year": case["event"]["year"]})
        _CACHE["cases"] = rows
    return _CACHE["cases"]


def _policies():
    names = [label for label, path in MODELS.items() if path.exists()]
    return names + [HEURISTIC_LABELS[k] for k in ("direct_flank", "protect_urban",
                                                  "downwind_indirect", "random", "noop")]


def _fuel_classes(fuel: np.ndarray) -> np.ndarray:
    out = np.full(fuel.shape, 7, dtype=np.uint8)
    for code, groups in ((1, "grass"), (2, "shrub"), (3, "timber"), (4, "slash")):
        out[np.isin(fuel, FUEL_GROUPS[groups])] = code
    out[fuel == URBAN] = 5
    out[fuel == WATER] = 6
    out[np.isin(fuel, (SNOW, AGRICULTURE, BARREN))] = 7
    return out


def _load_case(scenario_id: str):
    key = ("case", scenario_id)
    if key not in _CACHE:
        split = next(c["split"] for c in _cases() if c["id"] == scenario_id)
        inputs = load_case_inputs(scenario_id, split=split)
        spec, meta = build_real_episode(inputs)
        from run_feds_noop_episode import load_observed_timeline
        targets = load_observed_timeline(inputs["case"], inputs["receipt"]["grid"])
        r0, c0 = meta["crop_offset_row"], meta["crop_offset_col"]
        observed = {int(t["hours_since_start"]): t["mask"][r0:r0 + CROP, c0:c0 + CROP]
                    for t in targets}
        _CACHE[key] = (spec, meta, observed)
    return _CACHE[key]


def _actor(label: str, spec):
    for name, path in MODELS.items():
        if name == label:
            from evaluate_synthetic_policies import _predictor
            return None, _predictor(str(path))
    for key, name in HEURISTIC_LABELS.items():
        if name == label:
            policy = make_random_policy(spec.seed) if key == "random" else HEURISTICS[key]
            return policy, None
    raise ValueError("unknown policy %r" % label)


def _frame(env) -> dict:
    fire = env.fire
    state = np.zeros(fire.state.shape, dtype=np.uint8)
    state[fire.line & ~fire.ever_burned] = 4
    state[fire.ever_burned] = 2
    state[env.prior_damage] = 3
    state[fire.state == BURNING] = 1
    weather = env.spec_now.weather.at(min(env.decision, len(env.spec_now.weather.steps) - 1))
    return {
        "state": _b64(state),
        "units": [{"row": u.row, "col": u.col, "kind": "dozer" if u.kind == 1 else "crew",
                   "active": u.active, "lost": u.lost, "arrival": u.arrival_minute,
                   "close_calls": u.close_calls} for u in env.units],
        "new_cells": int((fire.ever_burned & ~env.prior_damage).sum()),
        "urban_cells": int((fire.ever_burned & ~env.prior_damage & env.land.urban).sum()),
        "line_cells": int(fire.line.sum()),
        "wind_ms": round(weather.wind_midflame_m_s, 2),
        "wind_to": round(weather.wind_to_deg, 1),
        "moisture": round(weather.moisture, 3),
        "local_hour": round(weather.local_hour, 1),
    }


def _rollout(spec, label: str) -> dict:
    env = SyntheticSuppressionEnv()
    policy, predictor = _actor(label, spec)
    obs, _ = env.reset(options={"episode_spec": spec})
    frames = [_frame(env)]
    total, done = 0.0, False
    while not done:
        action = predictor(obs, env.action_masks()) if predictor else policy(env)
        obs, reward, done, _, info = env.step(action)
        total += reward
        frames.append(_frame(env))
    summary = dict(info["episode_summary"])
    summary["return"] = total
    summary["hours_per_frame"] = DECISION_MINUTES / 60.0
    summary["final_frame_includes_tail"] = env.decision >= spec.horizon
    return {"frames": frames, "summary": summary}


def run(scenario_id: str, label: str) -> dict:
    with LOCK:
        spec, meta, observed = _load_case(scenario_id)
        noop_key = ("noop", scenario_id)
        if noop_key not in _CACHE:
            _CACHE[noop_key] = _rollout(spec, HEURISTIC_LABELS["noop"])
        agent = _rollout(spec, label)
        noop = _CACHE[noop_key]
    return {
        "case": scenario_id, "split": meta["split"], "policy": label,
        "size": CROP, "hectares_per_cell": HECTARES_PER_CELL, "horizon": spec.horizon,
        "fuel": _b64(_fuel_classes(spec.landscape.fuel)),
        "observed": {str(h): _b64(m) for h, m in sorted(observed.items())},
        "agent": agent, "noop": noop,
        "metadata": {k: meta[k] for k in ("initial_burned_cells", "initial_cells_outside_crop",
                                          "start_utc") if k in meta},
    }


PAGE = (ROOT / "scripts/synthetic_case_viewer.html")


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: bytes, kind: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, status: int = 200) -> None:
        self._send(json.dumps(payload).encode("utf-8"), "application/json", status)

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        url = urlparse(self.path)
        query = parse_qs(url.query)
        try:
            if url.path == "/":
                self._send(PAGE.read_bytes(), "text/html; charset=utf-8")
            elif url.path == "/api/cases":
                self._json({"cases": _cases(), "policies": _policies()})
            elif url.path == "/api/run":
                self._json(run(query["case"][0], query["policy"][0]))
            else:
                self._send(b"not found", "text/plain", 404)
        except Exception as error:  # surface errors to the page
            self._json({"error": "%s: %s" % (type(error).__name__, error)}, 500)

    def log_message(self, fmt, *args) -> None:
        sys.stderr.write("viewer: " + fmt % args + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    _cases()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print("viewer on http://127.0.0.1:%d" % args.port, flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
