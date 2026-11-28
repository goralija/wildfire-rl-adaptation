#!/usr/bin/env python3
"""Recompute new spread masks, OOF exclusions/weights and fire-level statistics."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import audit_action_value_pilot as parent_audit
import check_action_value_robustness as run
from wildfire_rl.action_value import action_features, fit_ridge


def prediction(model, obs, mask):
    x = action_features(obs)
    values = np.r_[0., model['coef'][0]+((x-model['mean'])/model['scale']) @ model['coef'][1:]]
    values[~mask] = -np.inf
    return int(np.argmax(values))


def load_model(path, digest):
    if run.sha(path) != digest: raise ValueError('model hash changed')
    with np.load(path, allow_pickle=False) as a: return {k: a[k].copy() for k in a.files}


def statistics(saved, noop, refs, base, metrics):
    joint = base & (noop > 0).all(axis=0)
    p = (saved[:, joint]/noop[:, joint]*100).mean(axis=0)
    r = (refs[:, joint]/noop[:, joint, None]*100).mean(axis=0)
    draws = np.random.default_rng(0).integers(len(p), size=(10000, len(p)))
    distribution = p[draws].mean(axis=1)-r[draws].mean(axis=1).max(axis=1)
    ci = np.quantile(distribution, [.025, .975]); best = r.mean(axis=0).max()
    np.testing.assert_allclose(metrics['mean_saved_percent'], p.mean(), atol=1e-12)
    np.testing.assert_allclose(metrics['best_reference_percent'], best, atol=1e-12)
    np.testing.assert_allclose(metrics['delta_best_ci95_pp'], ci, atol=1e-12)
    np.testing.assert_allclose(metrics['mean_saved_ha_all'], saved.mean()*3.24, atol=1e-12)
    np.testing.assert_allclose(metrics['pooled_saved_percent_all'], saved.sum()/noop.sum()*100, atol=1e-12)
    if metrics['primary_mask'] != joint.tolist() or metrics['n'] != len(p): raise ValueError('resampling unit differs')
    if metrics['near'] != (best > 0 and p.mean()/best >= .9 and ci[0] >= -2.): raise ValueError('near rule differs')
    if metrics['better'] != (ci[0] > 0): raise ValueError('better rule differs')
    deleted = [np.delete(p, i).mean()-np.delete(r, i, axis=0).mean(axis=0).max() for i in range(len(p))]
    np.testing.assert_allclose(metrics['delete_one_effect_delta_range_pp'], [min(deleted), max(deleted)], atol=1e-12)


def audit(out, parent):
    parent_check = parent_audit.audit(parent); run.assert_guard(out)
    if run.read(out/'status.json')['phase'] != 'complete': raise ValueError('run incomplete')
    p = run.validate_parent(parent, run.read(run.PLAN)); result = run.read(out/'analysis.json')
    ids = p['fitting_cases']+p['evaluation_cases']; names = p['references']
    cases = {s: run.base.load_case(parent, s) for s in ids}; checked = 0
    model = load_model(parent/'ca-model.npz', run.read(run.PLAN)['frozen_models_sha256']['ca'])
    saved, noops, refs = [], [], []
    for rep in range(3):
        sr, nr, rr = [], [], []
        for sid in p['evaluation_cases']:
            c = ({k: cases[sid]['ca_'+k] for k in ('obs', 'mask', 'saved', 'noop')}
                 if rep == 0 else run.replicate_case(out, sid, rep))
            if rep:
                np.testing.assert_array_equal(c['obs'], cases[sid]['ca_obs'])
                np.testing.assert_array_equal(c['mask'], cases[sid]['ca_mask'])
                initial, noop = c['reference'][0], c['reference'][-1]
                if (c['reference'][:-1] & ~c['reference'][1:]).any(): raise ValueError('no-op loses past damage')
                for a, (burned, line) in enumerate(zip(c['burned'], c['line'])):
                    if (initial & ~burned).any(): raise ValueError('agent erases past damage')
                    n = int((noop & ~initial).sum())
                    charged = int(((burned & ~initial) | (line & noop & ~initial)).sum())
                    if n != c['noop'] or n-charged != c['saved'][a]: raise ValueError('new mask score differs')
                    checked += 1
            a = prediction(model, c['obs'], c['mask'])
            row = next(r for r in result['frozen_ca']['cases'] if r['scenario_id'] == sid and r['replicate'] == rep)
            if row['action'] != a or row['saved_cells'] != c['saved'][a] or row['noop_cells'] != c['noop']:
                raise ValueError('frozen model result differs')
            sr.append(c['saved'][a]); nr.append(c['noop']); rr.append(run.references(c['obs'], c['mask'], c['saved'], names))
        saved.append(sr); noops.append(nr); refs.append(rr)
    base = np.array([cases[s]['simfire_noop'] > 0 for s in p['evaluation_cases']])
    statistics(np.array(saved), np.array(noops), np.array(refs), base, result['frozen_ca']['metrics'])
    eligible = np.array([cases[s]['simfire_noop'] > 0 and cases[s]['ca_noop'] > 0 for s in ids])
    folds = 0
    for be in ('simfire', 'ca'):
        x = np.array([action_features(cases[s][be+'_obs']) for s in ids])
        masks = np.array([cases[s][be+'_mask'] for s in ids]); noop = np.array([cases[s][be+'_noop'] for s in ids])
        gains = np.array([cases[s][be+'_saved'] for s in ids])
        targets = gains[:, 1:]/np.maximum(noop[:, None], 1)
        values = np.array([run.references(cases[s][be+'_obs'], masks[i], gains[i], names) for i, s in enumerate(ids)])
        selected, extra = [], []; rows = result['crossfit'][be]['cases']
        if [r['scenario_id'] for r in rows] != ids: raise ValueError('missing/duplicate folds')
        for i, (sid, row) in enumerate(zip(ids, rows)):
            keep = eligible & (np.arange(len(ids)) != i)
            if row['fitting_ids'] != [s for s, k in zip(ids, keep) if k]: raise ValueError('held-out leak')
            fitted = fit_ridge(x[keep], targets[keep], masks[keep], alpha=10.)
            stored = load_model(out/'folds'/(be+'-'+sid+'.npz'), row['model_sha256'])
            for key in fitted: np.testing.assert_allclose(stored[key], fitted[key], atol=1e-12, rtol=1e-12)
            j = int(np.argmax((values[keep]/noop[keep, None]*100).mean(axis=0)))
            if row['fitting_reference'] != names[j]: raise ValueError('baseline uses held-out fire')
            a = prediction(stored, cases[sid][be+'_obs'], masks[i])
            if row['action'] != a or row['saved_cells'] != gains[i, a]: raise ValueError('OOF outcome differs')
            selected.append(gains[i, a]); extra.append(values[i, j]); folds += 1
        statistics(np.array(selected)[None, :], noop[None, :], np.column_stack([values, extra])[None, :, :],
                   eligible, result['crossfit'][be]['metrics'])
    return dict(status='PASS',parent_mask_outcomes=parent_check['mask_outcomes'],new_mask_outcomes=checked,
                frozen_paths=48,fold_models=folds,analysis_sha256=run.sha(out/'analysis.json'),
                auditor_sha256=run.sha(Path(__file__)),scope='Stored masks, fit-only refits and separate statistics; no new physical validation')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--parent', type=Path, default=ROOT/'.local/action-value-v2')
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args(); receipt = audit(args.out, args.parent)
    with args.receipt.open('x') as f: json.dump(receipt, f, indent=2)
    print(json.dumps(receipt))
