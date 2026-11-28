#!/usr/bin/env python3
"""Read-only recomputation of ADR-059 masks, fit-only weights and paired statistics."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from wildfire_rl.action_value import action_features, fit_ridge


def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(out):
    plan = read(ROOT/'configs/frozen/action-value-pilot-v1.json')
    freeze, analysis = read(out/'fit-freeze.json'), read(out/'analysis.json')
    if analysis['freeze_sha256'] != sha(out/'fit-freeze.json'): raise ValueError('freeze changed')
    if read(out/'status.json')['phase'] != 'complete': raise ValueError('run incomplete')
    if freeze['guard'] != analysis['guard']: raise ValueError('source guard differs')
    for name, digest in freeze['guard']['source_sha256'].items():
        if sha(ROOT/name) != digest: raise ValueError('source changed: '+name)
    fitting, evaluation = plan['fitting_cases'], plan['evaluation_cases']
    if set(fitting) & set(evaluation): raise ValueError('fitting/evaluation leakage')
    cases = {}; checked = 0
    for sid in fitting+evaluation:
        p = out/'cases'/(sid+'.npz')
        if sha(p) != read(p.with_suffix('.json'))['sha256']: raise ValueError('case hash differs')
        with np.load(p, allow_pickle=False) as a: c = {key: a[key].copy() for key in a.files}
        cases[sid] = c
        for field in ('obs', 'mask'): np.testing.assert_array_equal(c['simfire_'+field], c['ca_'+field])
        for be in plan['backends']:
            states = c[be+'_reference']; initial, noop = states[0], states[-1]
            if states.shape != (5, 256, 256) or (states[:-1] & ~states[1:]).any():
                raise ValueError('no-op horizon or cumulative damage differs')
            n = int((noop & ~initial).sum())
            if n != c[be+'_noop'] or not c[be+'_mask'][0]: raise ValueError('no-op count/mask differs')
            for a, (burned, line) in enumerate(zip(c[be+'_burned'], c[be+'_line'])):
                if (initial & ~burned).any(): raise ValueError('past damage erased')
                charged = int(((burned & ~initial) | (line & noop & ~initial)).sum())
                if n-charged != c[be+'_saved'][a]: raise ValueError('independent charged score differs')
                if not c[be+'_mask'][a] and c[be+'_saved'][a] != 0: raise ValueError('illegal action has outcome')
                checked += 1
    keep = [s for s in fitting if cases[s]['simfire_noop'] > 0 and cases[s]['ca_noop'] > 0]
    if freeze['fitting_ids'] != keep: raise ValueError('wrong fitting cases')
    joint = [s for s in evaluation if cases[s]['simfire_noop'] > 0 and cases[s]['ca_noop'] > 0]
    if analysis['joint_positive_ids'] != joint: raise ValueError('wrong primary cases')
    boot = np.random.default_rng(0).integers(len(joint), size=(10000, len(joint)))
    for be in plan['backends']:
        path = out/(be+'-model.npz')
        if sha(path) != freeze['models'][be]: raise ValueError('frozen model changed')
        with np.load(path, allow_pickle=False) as a: model = {key: a[key].copy() for key in a.files}
        refit = fit_ridge(np.array([action_features(cases[s][be+'_obs']) for s in keep]),
                          np.array([cases[s][be+'_saved'][1:]/cases[s][be+'_noop'] for s in keep]),
                          np.array([cases[s][be+'_mask'] for s in keep]), alpha=10.)
        for key in refit: np.testing.assert_allclose(refit[key], model[key], rtol=1e-12, atol=1e-12)
        rows = analysis['backends'][be]['cases']
        if [r['scenario_id'] for r in rows] != evaluation: raise ValueError('development rows differ')
        for row in rows:
            c = cases[row['scenario_id']]; x = action_features(c[be+'_obs'])
            values = np.r_[0., model['coef'][0] + ((x-model['mean'])/model['scale']) @ model['coef'][1:]]
            values[~c[be+'_mask']] = -np.inf
            a = int(np.argmax(values))
            if a != row['action'] or c[be+'_saved'][a] != row['saved_cells']: raise ValueError('policy row differs')
        primary = [r for r in rows if r['scenario_id'] in joint]
        agent = np.array([r['saved_cells']/r['noop_cells']*100 for r in primary])
        refs = np.array([[r['reference_saved_cells'][name]/r['noop_cells']*100 for name in plan['references']]
                         for r in primary])
        deltas = agent[boot].mean(axis=1) - refs[boot].mean(axis=1).max(axis=1)
        m = analysis['backends'][be]['metrics']; best = refs.mean(axis=0).max()
        np.testing.assert_allclose(m['mean_saved_percent'], agent.mean(), atol=1e-12)
        np.testing.assert_allclose(m['best_reference_percent'], best, atol=1e-12)
        np.testing.assert_allclose(m['delta_best_ci95_pp'], np.quantile(deltas, [.025, .975]), atol=1e-12)
        near = best > 0 and agent.mean()/best >= .9 and np.quantile(deltas, .025) >= -2.
        if m['near'] != near or m['better'] != (np.quantile(deltas, .025) > 0): raise ValueError('decision differs')
    return dict(status='PASS',cases=len(cases),mask_outcomes=checked,fitted_models=2,
                development_paths=32,analysis_sha256=sha(out/'analysis.json'),
                audit_source_sha256=sha(Path(__file__)),scope='Stored-mask/fit/statistic audit; native replay is in runner')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args(); result = audit(args.out)
    with args.receipt.open('x') as f: json.dump(result, f, indent=2)
    print(json.dumps(result))
