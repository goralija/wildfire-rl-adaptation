#!/usr/bin/env python3
"""Plan B (ADR-028 addendum): behaviour-cloning warm start from a scripted tactic.

Workers roll out the teacher (``protect_urban``, which falls back to ``direct_flank``)
on training seeds only (>= 500,000,000) and return (observation, mask, action) samples.
The MaskablePPO policy is fitted to the teacher's actions with a masked cross-entropy,
in rounds: collect, fit, discard. The saved model is then fine-tuned with
``train_synthetic_ppo.py --resume``. Documentation must say the policy starts from the
scripted tactic. No validation seed and no real case is used here.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np  # noqa: E402
import torch  # noqa: E402

from wildfire_rl.synthetic_env import Curriculum, SyntheticSuppressionEnv  # noqa: E402
from wildfire_rl.synthetic_heuristics import HEURISTICS  # noqa: E402

TRAINING_SEED_BASE = 500_000_000


def _collect(args):
    seed, teacher = args
    env = SyntheticSuppressionEnv(curriculum=Curriculum())
    policy = HEURISTICS[teacher]
    obs, _ = env.reset(options={"seed": TRAINING_SEED_BASE + seed})
    samples, done = [], False
    while not done:
        mask = env.action_masks()
        action = policy(env)
        if env.units and any(unit.active for unit in env.units):
            samples.append(({k: v.astype(np.float16) for k, v in obs.items()}, mask, action))
        obs, _, done, _, _ = env.step(action)
    return samples


def _batch(samples, device):
    obs = {k: torch.as_tensor(np.stack([s[0][k] for s in samples]).astype(np.float32),
                              device=device) for k in samples[0][0]}
    masks = torch.as_tensor(np.stack([s[1] for s in samples]), device=device)
    actions = torch.as_tensor(np.stack([s[2] for s in samples]), device=device)
    return obs, masks, actions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init", type=Path, required=True,
                        help="a MaskablePPO zip whose architecture to use (e.g. main-1 last_model)")
    parser.add_argument("--teacher", default="protect_urban")
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--episodes-per-round", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--keep-rounds", type=int, default=3,
                        help="fit on the samples of this many most recent rounds")
    parser.add_argument("--workers", type=int, default=7)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    from sb3_contrib import MaskablePPO

    torch.set_num_threads(4)
    model = MaskablePPO.load(args.init, device="cpu")
    policy = model.policy
    optimiser = torch.optim.Adam(policy.parameters(), lr=args.lr)
    recent = []
    log = []
    next_seed = 0
    with ProcessPoolExecutor(args.workers) as pool:
        for round_index in range(args.rounds):
            jobs = [(next_seed + i, args.teacher) for i in range(args.episodes_per_round)]
            next_seed += args.episodes_per_round
            recent.append([s for episode in pool.map(_collect, jobs) for s in episode])
            recent = recent[-args.keep_rounds:]
            samples = [s for batch in recent for s in batch]
            losses, agree = [], []
            for epoch in range(args.epochs):
                order = np.random.default_rng([round_index, epoch]).permutation(len(samples))
                for start in range(0, len(order), args.batch_size):
                    obs, masks, actions = _batch([samples[i] for i in order[start:start + args.batch_size]],
                                                 "cpu")
                    _, log_prob, _ = policy.evaluate_actions(obs, actions, action_masks=masks)
                    loss = -log_prob.mean()
                    optimiser.zero_grad()
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(policy.parameters(), 0.5)
                    optimiser.step()
                    losses.append(float(loss))
                    with torch.no_grad():
                        dist = policy.get_distribution(obs, action_masks=masks)
                        predicted = dist.get_actions(deterministic=True)
                        # Agreement only on slots with a real choice (more than "stay" legal).
                        choice = masks.view(masks.shape[0], actions.shape[1], -1).sum(-1) > 1
                        if choice.any():
                            agree.append(float((predicted == actions)[choice].float().mean()))
            row = {"round": round_index, "samples": len(samples),
                   "mean_loss": float(np.mean(losses)) if losses else None,
                   "slot_agreement": float(np.mean(agree)) if agree else None}
            log.append(row)
            print(json.dumps(row), flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    model.save(args.out)
    (args.out.parent / (args.out.stem + "-bc-log.json")).write_text(json.dumps(
        {"teacher": args.teacher, "training_seed_base": TRAINING_SEED_BASE, "rounds": log},
        indent=1))


if __name__ == "__main__":
    main()
