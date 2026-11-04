#!/usr/bin/env python3
"""MaskablePPO on the ADR-028 synthetic CA environment with periodic validation.

Training episodes use generator seeds >= 1,000,000. Validation uses fixed seeds
(default 0-63) after every ``--eval-every`` steps; the best checkpoint is chosen by
validation mean return only. No real FEDS case is loaded. Simulator-only results.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np  # noqa: E402
import torch  # noqa: E402
from sb3_contrib import MaskablePPO  # noqa: E402
from stable_baselines3.common.callbacks import BaseCallback  # noqa: E402
from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor  # noqa: E402

from wildfire_rl.synthetic_env import Curriculum, SyntheticSuppressionEnv  # noqa: E402

STAGES = {
    # name: (curriculum changes, share of total steps)
    "A": dict(horizons=(12, 24), unit_counts=(2, 3)),
    "B": dict(horizons=(12, 24, 48), unit_counts=(2, 3, 4)),
}


# Each prepared training fire (landscape, start, no-op rollout) serves this many episodes
# with freshly sampled units; validation never reuses.
REUSE_FIRES = 4


def make_env(rank: int, seed: int):
    def thunk():
        env = SyntheticSuppressionEnv(curriculum=Curriculum(**STAGES["A"]),
                                      seed_offset=1_000_000 + 10_000_000 * rank,
                                      reuse_fires=REUSE_FIRES if rank < 100 else 1)
        env.reset(seed=seed * 1000 + rank)
        return env
    return thunk


def evaluate(model, vec, seeds, curriculum) -> dict:
    """Deterministic paired evaluation on fixed synthetic validation seeds."""
    vec.env_method("set_curriculum", **curriculum)
    n = vec.num_envs
    rows = []
    queue = list(seeds)
    while queue:
        batch = queue[:n]
        queue = queue[n:]
        obs = [vec.env_method("reset", options={"seed": s}, indices=[i])[0][0]
               for i, s in enumerate(batch)]
        done = [False] * len(batch)
        totals = [0.0] * len(batch)
        while not all(done):
            for i in range(len(batch)):
                if done[i]:
                    continue
                mask = vec.env_method("action_masks", indices=[i])[0]
                action, _ = model.predict({k: v[None] for k, v in obs[i].items()},
                                          action_masks=mask[None], deterministic=True)
                ob, reward, term, trunc, info = vec.env_method("step", action[0], indices=[i])[0]
                obs[i] = ob
                totals[i] += reward
                if term or trunc:
                    done[i] = True
                    summary = dict(info["episode_summary"])
                    summary["return"] = totals[i]
                    rows.append(summary)
    return {
        "mean_return": float(np.mean([r["return"] for r in rows])),
        "mean_saved_fraction": float(np.mean([r["saved_fraction"] for r in rows])),
        "units_lost": int(sum(r["units_lost"] for r in rows)),
        "close_calls": int(sum(r["close_calls"] for r in rows)),
        "episodes": len(rows),
    }


class ValidationCallback(BaseCallback):
    def __init__(self, eval_vec, seeds, every, out_dir: Path, stage_b_at: int):
        super().__init__()
        self.eval_vec, self.seeds, self.every, self.out_dir = eval_vec, seeds, every, out_dir
        self.stage_b_at = stage_b_at
        self.next_eval = every
        self.best = -np.inf
        self.stage = "A"
        self.log = out_dir / "validation.jsonl"
        self.started = time.time()

    def _on_step(self) -> bool:
        if self.stage == "A" and self.num_timesteps >= self.stage_b_at:
            self.training_env.env_method("set_curriculum", **STAGES["B"])
            self.stage = "B"
        if self.num_timesteps >= self.next_eval:
            self.next_eval += self.every
            result = evaluate(self.model, self.eval_vec, self.seeds, STAGES["B"])
            result.update(steps=int(self.num_timesteps), stage=self.stage,
                          minutes=round((time.time() - self.started) / 60.0, 1))
            if result["mean_return"] > self.best:
                self.best = result["mean_return"]
                self.model.save(self.out_dir / "best_model.zip")
                result["best"] = True
            self.model.save(self.out_dir / "last_model.zip")
            with self.log.open("a") as handle:
                handle.write(json.dumps(result) + "\n")
            print("validation", json.dumps(result), flush=True)
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=200_000)
    parser.add_argument("--envs", type=int, default=6)
    parser.add_argument("--eval-envs", type=int, default=2)
    parser.add_argument("--eval-every", type=int, default=50_000)
    parser.add_argument("--eval-seeds", type=int, default=64)
    parser.add_argument("--stage-b-share", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(2)

    vec = VecMonitor(SubprocVecEnv([make_env(i, args.seed) for i in range(args.envs)]))
    eval_vec = SubprocVecEnv([make_env(100 + i, args.seed) for i in range(args.eval_envs)])
    if args.resume:
        model = MaskablePPO.load(args.resume, env=vec, device="cpu")
    else:
        model = MaskablePPO(
            "MultiInputPolicy", vec, n_steps=256, batch_size=512, n_epochs=4,
            learning_rate=3e-4, gamma=0.995, gae_lambda=0.95, ent_coef=0.01,
            clip_range=0.2, policy_kwargs=dict(normalize_images=False,
                                               net_arch=dict(pi=[256, 256], vf=[256, 256])),
            seed=args.seed, device="cpu", verbose=0,
        )
    receipt = {"created_utc": datetime.now(timezone.utc).isoformat(), "args": vars(args),
               "stages": STAGES, "environment": "synthetic CA ADR-028 v4", "reuse_fires": REUSE_FIRES,
               "real_cases_loaded": False}
    (args.out / "receipt.json").write_text(json.dumps(receipt, indent=1, default=str))
    callback = ValidationCallback(eval_vec, list(range(args.eval_seeds)), args.eval_every,
                                  args.out, int(args.stage_b_share * args.steps))
    model.learn(total_timesteps=args.steps, callback=callback, reset_num_timesteps=not args.resume)
    model.save(args.out / "final_model.zip")
    vec.close()
    eval_vec.close()


if __name__ == "__main__":
    main()
