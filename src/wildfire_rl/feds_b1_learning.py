"""Small, TRAIN-only offline policies on the finite B=1 tree (ADR-033).

Fits hold out an entire fire. Feature scaling uses fitting fires only. Models
receive current observations/masks, never test-fire rewards or future weather.
Fitted Q iterates backwards through the four decision times; choosing a line
ends the decision problem, while no-op continues to the next state.
"""
from __future__ import annotations

import numpy as np

from .feds_b1 import action_sequences, policy_sequence
from .line_damage import HECTARES_PER_CELL

METHOD_NAMES = ("advancing_front", "downwind", "fixed_sequence", "ridge_q_alpha_1",
                "ridge_q_alpha_10", "ridge_q_alpha_100", "tabular_q", "nearest_neighbor_bc_5")


def observation_features(observation):
    grid = np.asarray(observation["grid"], dtype=float)
    if grid.shape != (4, 16, 16):
        raise ValueError("expected the locked 4x16x16 observation")
    burned, front, lines, fuel = grid
    yy, xx = np.indices((16, 16), dtype=float)
    xx, yy = xx / 15, yy / 15

    def centroid(layer):
        weight = layer.sum()
        return ((float((layer * xx).sum() / weight), float((layer * yy).sum() / weight))
                if weight else (.5, .5))

    bx, by = centroid(burned)
    fx, fy = centroid(front)
    weather = np.asarray(observation["weather"], dtype=float)
    dx, dy = fx - bx, fy - by
    ahead_fuel = []
    for angle in np.arange(8) * np.pi / 4:
        projection = (xx-fx) * np.cos(angle) + (yy-fy) * np.sin(angle)
        region = projection > 0
        ahead_fuel.append(float(fuel[region].mean()) if region.any() else float(fuel.mean()))
    result = np.asarray([*weather, float(observation["time"][0]),
                         burned.mean(), front.mean(), lines.mean(), fuel.mean(), fuel.std(),
                         bx, by, fx, fy, dx, dy, dx * weather[1] - dy * weather[2],
                         float((fuel * front).sum() / front.sum()) if front.sum() else 0.,
                         *observation["budget"], *ahead_fuel])
    if not np.isfinite(result).all():
        raise ValueError("non-finite policy features")
    return result


def case_arrays(cases, mode):
    if mode not in ("raw", "charged"):
        raise ValueError("unknown damage mode")
    features = np.asarray([[observation_features(o) for o in c["observations"]] for c in cases])
    masks = np.asarray([c["action_masks"] for c in cases], dtype=bool)
    gains = np.zeros((len(cases), 4, 9))
    for i, case in enumerate(cases):
        rows = {tuple(r["requested_actions"]): r for r in case["outcomes"]}
        if set(rows) != set(action_sequences()):
            raise ValueError("incomplete B=1 tree")
        for k in range(4):
            for action in range(1, 9):
                sequence = tuple(action if j == k else 0 for j in range(4))
                gains[i, k, action] = rows[sequence][mode + "_saved_cells"] * HECTARES_PER_CELL
    return features, gains, masks


def _key(feature):
    wind = int(np.floor((np.arctan2(feature[1], feature[2]) % (2*np.pi)) / (np.pi/4)))
    front = int(np.floor((np.arctan2(feature[15], feature[14]) % (2*np.pi)) / (np.pi/4)))
    size = int(np.digitize(feature[5], [.005, .02, .08]))
    return wind, front, size


class RidgeModel:
    def __init__(self, x, y, alpha):
        self.mean = x.mean(axis=0)
        self.scale = x.std(axis=0)
        self.scale[self.scale < 1e-9] = 1.
        design = self.design(x)
        penalty = np.eye(design.shape[1]) * alpha
        penalty[0, 0] = 0.
        self.coef = np.linalg.solve(design.T @ design + penalty, design.T @ y)

    def design(self, x):
        normalized = (np.atleast_2d(x) - self.mean) / self.scale
        return np.column_stack([np.ones(len(normalized)), normalized])

    def predict(self, x):
        return self.design(x) @ self.coef


class TabularModel:
    def __init__(self, x, y):
        self.fallback = y.mean(axis=0)
        self.values = {key: y[[i for i, row in enumerate(x) if _key(row) == key]].mean(axis=0)
                       for key in {_key(row) for row in x}}

    def predict(self, x):
        return np.asarray([self.values.get(_key(row), self.fallback) for row in np.atleast_2d(x)])


def fit_q(x, gains, masks, method):
    models = [None] * 4
    future = np.zeros(len(x))
    for k in reversed(range(4)):
        targets = gains[:, k].copy()
        targets[:, 0] = future
        if method == "tabular_q":
            model = TabularModel(x[:, k], targets)
        else:
            model = RidgeModel(x[:, k], targets, float(method.rsplit("_", 1)[1]))
        models[k] = model
        q = model.predict(x[:, k])
        future = np.max(np.where(masks[:, k], q, -np.inf), axis=1)
    return models


def _score(case, actions, mode):
    rows = [row for row in case["outcomes"] if tuple(row["effective_actions"]) == tuple(actions)]
    # A hand-authored fixture may include the requested illegal sequence only.
    if not rows:
        rows = [row for row in case["outcomes"] if tuple(row["requested_actions"]) == tuple(actions)]
    values = {row[mode + "_saved_cells"] for row in rows}
    if len(values) != 1:
        raise ValueError("missing or non-deterministic sequence outcome")
    return float(next(iter(values))) * HECTARES_PER_CELL


def evaluate_fold(training_cases, heldout, mode, method):
    if not training_cases or heldout["scenario_id"] in {c["scenario_id"] for c in training_cases}:
        raise ValueError("fit and held-out fire IDs must be disjoint")
    if method not in METHOD_NAMES:
        raise ValueError("unknown method")
    if method in ("advancing_front", "downwind"):
        from .feds_heuristics import make_heuristic
        policy = make_heuristic(method)
    elif method == "fixed_sequence":
        means = [np.mean([c["outcomes"][i][mode + "_saved_cells"] for c in training_cases])
                 for i in range(33)]
        chosen = action_sequences()[int(np.argmax(means))]
        policy = lambda o, m: chosen[int(round(float(o["time"][0]) * 4))]
    else:
        x, gains, masks = case_arrays(training_cases, mode)
        if method == "nearest_neighbor_bc_5":
            means = x.mean(axis=0)
            scales = x.std(axis=0)
            scales[scales < 1e-9] = 1.
            labels = np.zeros((len(x), 4), dtype=int)
            for k in range(4):
                possible = np.where(masks[:, k:], gains[:, k:], -np.inf)
                best = np.argmax(possible.reshape(len(x), -1), axis=1)
                labels[:, k] = np.where(best // 9 == 0, best % 9, 0)

            def policy(o, m):
                k = int(round(float(o["time"][0]) * 4))
                distance = np.sum(((x[:, k] - observation_features(o)) / scales[k]) ** 2, axis=1)
                neighbors = np.argsort(distance, kind="stable")[:5]
                counts = np.bincount(labels[neighbors, k], minlength=9)
                return int(np.argmax(np.where(m, counts, -1)))
        else:
            models = fit_q(x, gains, masks, method)

            def policy(o, m):
                k = int(round(float(o["time"][0]) * 4))
                q = models[k].predict(observation_features(o))[0]
                return int(np.argmax(np.where(m, q, -np.inf)))
    actions = policy_sequence(policy, heldout["observations"], heldout["action_masks"])
    return {"scenario_id": heldout["scenario_id"], "actions": list(actions),
            "saved_ha": _score(heldout, actions, mode)}


def paired_interval(values, *, seed=0, samples=10000):
    values = np.asarray(values, dtype=float)
    if not len(values) or not np.isfinite(values).all():
        raise ValueError("paired effects must be finite and nonempty")
    rng = np.random.default_rng(seed)
    means = values[rng.integers(len(values), size=(samples, len(values)))].mean(axis=1)
    return np.percentile(means, [2.5, 97.5]).tolist()
