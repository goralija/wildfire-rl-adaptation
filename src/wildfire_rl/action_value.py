"""ADR-059: one fixed, action-shared B1 ridge; no simulator or torch dependency."""
import numpy as np


def validate_split(fitting, evaluation):
    if (not fitting or not evaluation or len(set(fitting)) != len(fitting)
            or len(set(evaluation)) != len(evaluation) or set(fitting) & set(evaluation)):
        raise ValueError('distinct, disjoint fitting/evaluation fires required')


def action_features(observation):
    """Project the unchanged terrain536 layout, sharing columns across directions.

    Local37 + cone14 + local terrain9 + ahead fuel1 + angle2 + wind2 + front2
    + slope2 + global weather3/fuel14/front spread2/terrain6 = 94 columns.
    No full map, future state, reward or scenario identifier is accepted.
    """
    v = np.asarray(observation, float)
    if v.shape != (536,) or not np.isfinite(v).all():
        raise ValueError('finite terrain536 required')
    rows = []
    for k in range(8):
        dx, dy = np.cos(k*np.pi/4), np.sin(k*np.pi/4)
        local = v[162+37*k:162+37*(k+1)].copy()
        local[:2] -= v[156:158]  # line centre relative to observed front centroid
        terrain = v[464+9*k:464+9*(k+1)]
        def project(x, y): return [x*dx+y*dy, -x*dy+y*dx]
        rows.append(np.concatenate([local, v[42+14*k:42+14*(k+1)], terrain,
            [v[20+k], dx, dy], project(v[1], -v[2]), project(*v[160:162]),
            project(terrain[1], terrain[2]), v[:3], v[28:42], v[158:160], v[458:464]]))
    return np.asarray(rows)


def fitting_weights(masks):
    m = np.asarray(masks)
    if m.ndim != 2 or m.shape[1] != 9 or not np.isin(m, [0, 1]).all() or not m[:, 0].all():
        raise ValueError('binary nine-action masks with legal no-op required')
    count = m[:, 1:].sum(axis=1)
    return m[:, 1:] / np.maximum(count[:, None], 1)


def fit_ridge(features, targets, masks, alpha=10.):
    x, y = np.asarray(features, float), np.asarray(targets, float)
    w = fitting_weights(masks)
    if (x.ndim != 3 or x.shape[:2] != w.shape or y.shape != w.shape or
            not np.isfinite(x).all() or not np.isfinite(y).all() or alpha <= 0 or not w.any()):
        raise ValueError('finite fitting arrays and positive regularization required')
    mean = (x*w[:, :, None]).sum(axis=(0, 1))/w.sum()
    scale = np.sqrt(((x-mean)**2*w[:, :, None]).sum(axis=(0, 1))/w.sum())
    scale[scale < 1e-9] = 1.
    z = np.column_stack([np.ones(x.shape[0]*8), ((x-mean)/scale).reshape(-1, x.shape[2])])
    penalty = np.eye(z.shape[1])*alpha; penalty[0, 0] = 0.
    coef = np.linalg.solve(z.T @ (z*w.reshape(-1, 1)) + penalty, z.T @ (y*w).ravel())
    if not np.isfinite(coef).all(): raise ValueError('nonfinite fitted weights')
    return dict(mean=mean, scale=scale, coef=coef)


def select_action(model, features, mask):
    m = np.asarray(mask)
    fitting_weights(m[None, :])
    x = np.asarray(features, float)
    if x.shape != (8, len(model['mean'])) or not np.isfinite(x).all():
        raise ValueError('finite eight-candidate features required')
    values = np.column_stack([np.ones(8), (x-model['mean'])/model['scale']]) @ model['coef']
    if not np.isfinite(values).all(): raise ValueError('nonfinite prediction')
    scores = np.r_[0., values]; scores[~m.astype(bool)] = -np.inf
    return int(np.argmax(scores))  # no-op wins a zero tie


def reference_actions(observation, mask):
    v = np.asarray(observation, float)
    action_features(v); fitting_weights(np.asarray(mask)[None, :])
    directions = np.column_stack([np.cos(np.arange(8)*np.pi/4), np.sin(np.arange(8)*np.pi/4)])
    def sector(x, y):
        if x == y == 0: return 0
        a = int(np.argmax(directions @ [x, y])) + 1
        return a if mask[a] else 0
    wind = sector(v[1], -v[2])
    front = sector(*v[160:162]) if v[5] > 0 and np.hypot(*v[160:162])*63 >= 1e-6 else wind
    return dict(noop=0, advancing_front64=front, downwind=wind,
                **{'fixed_'+str(k): k if mask[k] else 0 for k in range(1, 9)})


def compare(saved, noop, references, joint):
    """Percentage by fire; paired bootstrap reselects the strongest fixed rule."""
    saved, noop, refs = (np.asarray(v, float) for v in (saved, noop, references))
    joint = np.asarray(joint)
    if (saved.ndim != 1 or noop.shape != saved.shape or refs.ndim != 2 or refs.shape[1:] != saved.shape
            or not refs.shape[0] or joint.shape != saved.shape or joint.dtype != bool or not joint.any()
            or not all(np.isfinite(v).all() for v in (saved, noop, refs)) or (noop < 0).any()
            or (saved > noop).any() or (refs > noop).any() or (noop[joint] <= 0).any()):
        raise ValueError('finite paired counts and positive primary denominators required')
    p = saved[joint]/noop[joint]*100; r = refs[:, joint]/noop[joint]*100
    means = r.mean(axis=1); best = float(means.max())
    samples = np.random.default_rng(0).integers(len(p), size=(10000, len(p)))
    differences = p[samples].mean(axis=1) - r[:, samples].mean(axis=2).max(axis=0)
    ci = np.quantile(differences, [.025, .975]).tolist()
    ratio = float(p.mean()/best) if best > 0 else None
    return dict(n=len(p), mean_saved_percent=float(p.mean()), best_reference_percent=best,
        reference_means_percent=means.tolist(), ratio_to_best=ratio,
        delta_best_pp=float(p.mean()-best), delta_best_ci95_pp=ci,
        near=bool(ratio is not None and ratio >= .9 and ci[0] >= -2.), better=bool(ci[0] > 0),
        mean_saved_ha_all=float(saved.mean()*3.24),
        pooled_saved_percent_all=float(saved.sum()/noop.sum()*100) if noop.sum() else None)
