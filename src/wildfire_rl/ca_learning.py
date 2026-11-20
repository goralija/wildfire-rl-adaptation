"""Deterministic v2 policy preprocessing and bounded TRAIN episode cycling."""
from collections import OrderedDict
from dataclasses import replace
import hashlib
import json

import gymnasium as gym
import numpy as np

from .ca_controlled import CAObservationV2, clustered_contrast, validate_plan
from .synthetic_env import Curriculum, SyntheticSuppressionEnv

ENCODER_VERSION = "ca-geometric-local-v1"
REWARD_VERSION = "ca-line-charged-safety-v1"
GEO = 27
TOKEN_DIM = GEO + 21 * 7 * 7
GLOBAL_DIM = 27


def encoded_space():
    return gym.spaces.Dict({
        "tokens": gym.spaces.Box(-np.inf, np.inf, (4, TOKEN_DIM), dtype=np.float32),
        "global": gym.spaces.Box(-np.inf, np.inf, (GLOBAL_DIM,), dtype=np.float32),
    })


def encode_observation(obs):
    """No teacher actions, future series, simulator state or no-op labels are read.

    Geometry is centre offset, nearest-front offset/unit vector/distance, radial
    unit vector and nearest unburned-urban offset/distance; all in row/column order.
    """
    native, units = obs["native"], obs["unit_state"]
    rows, cols = native.shape[1:]
    burning = np.argwhere(native[0] > .5)
    burned = np.argwhere(native[1] > .5)
    urban = np.argwhere((native[3] > .5) & (native[1] < .5))
    centre = burned.mean(0) if len(burned) else np.array([rows / 2, cols / 2])
    padded = np.pad(native, ((0, 0), (3, 3), (3, 3)))
    padded[18] = np.pad(native[18], 3, constant_values=1)
    tokens = np.zeros((4, TOKEN_DIM), np.float32)
    for slot, state in enumerate(units):
        raw = state.copy()
        raw[4] /= 180
        raw[5:7] /= max(rows, cols)
        raw[7] /= 180
        raw[8] /= 16
        tokens[slot, :9] = raw
        tokens[slot, 9 + slot] = 1
        if not state[1]:
            continue
        r, c = int(state[5]), int(state[6])
        here = np.array([r, c])
        radial = here - centre
        near_delta, near_direction, distance = np.zeros(2), np.zeros(2), 0.0
        if len(burning):
            delta = burning - here
            closest = delta[np.argmin(np.linalg.norm(delta, axis=1))]
            distance = float(np.linalg.norm(closest))
            near_delta = closest / 16
            near_direction = closest / max(distance, 1e-9)
        urban_delta, urban_distance = np.zeros(2), 0.0
        if len(urban):
            delta = urban - here
            closest = delta[np.argmin(np.linalg.norm(delta, axis=1))]
            urban_delta = closest / 16
            urban_distance = float(np.linalg.norm(closest)) / 16
        tokens[slot, 13:GEO] = np.concatenate([
            radial / max(rows, cols), near_delta, near_direction, [distance / 16],
            radial / max(float(np.linalg.norm(radial)), 1e-9), urban_delta,
            [urban_distance, bool(len(burning)), bool(len(urban))],
        ])
        tokens[slot, GEO:] = padded[:, r:r + 7, c:c + 7].ravel()
    global_ = np.concatenate([obs["globals"], native[3:19].mean(axis=(1, 2)),
                              [units[:, 0].sum() / 4, units[:, 2].sum() / 4]])
    return {"tokens": tokens, "global": global_.astype(np.float32)}


def discounted_returns(rewards, gamma):
    values, total = [], 0.0
    for reward in reversed(rewards):
        total = float(reward) + gamma * total
        values.append(total)
    return np.array(values[::-1], np.float32)


def learning_contrast(candidate, reference):
    a, b = np.asarray(candidate, float), np.asarray(reference, float)
    if a.ndim != 3 or b.shape != a.shape[1:]:
        raise ValueError("model seed x case x roster and matched case x roster required")
    return clustered_contrast(a.mean(axis=0), b)


def validate_learning_plan(plan, root):
    if plan["schema_version"] != "ca-learning-pilot/1.0":
        raise ValueError("unknown learning plan")
    if plan["encoder_version"] != ENCODER_VERSION or plan["reward_version"] != REWARD_VERSION:
        raise ValueError("encoder/reward contract mismatch")
    path = root / plan["scenario_plan"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != plan["scenario_plan_sha256"]:
        raise ValueError("scenario plan hash mismatch")
    validate_plan(json.loads(path.read_text()))
    if plan["model_seeds"] != [17, 29, 43] or plan["ppo"]["steps"] != 4096:
        raise ValueError("registered seed/step budget changed")


class EpisodeBank:
    """Small per-process LRU. Cache no-op for units-independent reward, never policy."""
    def __init__(self, scenario_plan, capacity=4):
        self.plan, self.capacity = scenario_plan, capacity
        self.cache = OrderedDict()

    def get(self, seed, roster):
        if seed not in self.plan["case_seeds"]["train"]:
            raise ValueError("training bank refuses development/test seeds")
        if seed not in self.cache:
            env = SyntheticSuppressionEnv(curriculum=Curriculum(
                horizons=(12,), unit_counts=(4,), min_noop_growth_cells=30, max_attempts=16))
            env.reset(options={"seed": seed})
            self.cache[seed] = (env.spec_now, (list(env.noop_damage), env.noop_final))
            env.land.log_q_cache.clear()
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)
        self.cache.move_to_end(seed)
        spec, noop = self.cache[seed]
        return replace(spec, units=[tuple(u) for u in self.plan["rosters"][roster]]), noop


class CATrainingEnv(gym.Env):
    """Policy preprocessing wrapper; underlying v2 and physics remain unchanged."""
    def __init__(self, scenario_plan, rank=0, stride=1):
        self.plan = scenario_plan
        self.bank = EpisodeBank(scenario_plan)
        self.raw = CAObservationV2(SyntheticSuppressionEnv())
        self.action_space = self.raw.action_space
        self.observation_space = encoded_space()
        self.rank, self.stride, self.counter = rank, stride, 0
        self.seen = set()

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        index = (self.rank + self.stride * self.counter) % (32 * 3)
        self.counter += 1
        case_seed = self.plan["case_seeds"]["train"][index // 3]
        roster = list(self.plan["rosters"])[index % 3]
        spec, noop = self.bank.get(case_seed, roster)
        # A cached spatial distance belongs to the old fire, even at an equal substep.
        if hasattr(self.raw.env, "_distance_key"):
            del self.raw.env._distance_key
        obs, info = self.raw.env._start(spec, noop_cache=noop)
        self.last_native = self.raw._wrap(obs)
        self.seen.add((case_seed, roster))
        return encode_observation(self.last_native), self.raw._info(info)

    def action_masks(self):
        return self.raw.action_masks()

    def training_manifest(self):
        return sorted(self.seen)

    def step(self, action):
        obs, reward, terminated, truncated, info = self.raw.step(action)
        self.last_native = obs
        return encode_observation(obs), reward, terminated, truncated, info

    def close(self):
        self.raw.close()
