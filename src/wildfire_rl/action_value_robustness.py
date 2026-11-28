"""ADR-061 checks of a fixed learner; no changes to its features or optimizer."""
import numpy as np
from .action_value import compare, fit_ridge


def summarize(saved, noop, references, base_positive):
    """Arrays are replicate x fire (x reference). Resampling unit stays fire."""
    saved, noop, refs = (np.asarray(v, float) for v in (saved, noop, references))
    base = np.asarray(base_positive)
    if (saved.ndim != 2 or noop.shape != saved.shape or not saved.shape[0]
            or refs.ndim != 3 or refs.shape[:2] != saved.shape or not refs.shape[2]
            or base.shape != saved.shape[1:] or base.dtype != bool
            or not all(np.isfinite(v).all() for v in (saved, noop, refs))
            or (noop < 0).any() or (saved > noop).any() or (refs > noop[:, :, None]).any()):
        raise ValueError('aligned finite replicate/fire counts required')
    joint = base & (noop > 0).all(axis=0)
    percent = np.divide(saved*100, noop, out=np.zeros_like(saved), where=noop > 0).mean(axis=0)
    ref_percent = np.divide(refs*100, noop[:, :, None], out=np.zeros_like(refs),
                            where=noop[:, :, None] > 0).mean(axis=0)
    result = compare(percent, np.full(len(percent), 100.), ref_percent.T, joint)
    p, r = percent[joint], ref_percent[joint]
    deleted = [float(np.delete(p, i).mean()-np.delete(r, i, axis=0).mean(axis=0).max())
               for i in range(len(p))] if len(p) > 1 else []
    result.update(primary_mask=joint.tolist(), replicate_count=saved.shape[0],
        mean_saved_ha_all=float(saved.mean()*3.24),
        pooled_saved_percent_all=float(saved.sum()/noop.sum()*100) if noop.sum() else None,
        delete_one_effect_delta_range_pp=[min(deleted), max(deleted)] if deleted else None)
    return result


def fit_fold(features, targets, masks, eligible, ids, held_out, references):
    """Remove the whole held-out fire before either fitting or baseline selection."""
    x, y, m, ok, refs = (np.asarray(v) for v in (features, targets, masks, eligible, references))
    if (not ids or len(set(ids)) != len(ids) or held_out not in ids or ok.shape != (len(ids),)
            or ok.dtype != bool or x.ndim != 3 or x.shape[:2] != (len(ids), 8)
            or y.shape != x.shape[:2] or m.shape != (len(ids), 9)
            or refs.ndim != 2 or refs.shape[0] != len(ids) or not refs.shape[1]
            or not np.isfinite(refs).all()):
        raise ValueError('aligned distinct fires and known held-out fire required')
    keep = ok & (np.arange(len(ids)) != ids.index(held_out))
    if not keep.any(): raise ValueError('no fitting fires')
    model = fit_ridge(x[keep], y[keep], m[keep], alpha=10.)
    selected = int(np.argmax(refs[keep].mean(axis=0)))
    return model, [sid for sid, k in zip(ids, keep) if k], selected
