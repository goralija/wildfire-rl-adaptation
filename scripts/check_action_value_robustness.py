#!/usr/bin/env python3
"""ADR-061: frozen-policy physical replicates and fixed-algorithm fire-level LOO."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import numpy as np
import run_action_value_pilot as base
from wildfire_rl.action_value import action_features, reference_actions, select_action
from wildfire_rl.action_value_robustness import fit_fold, summarize

PLAN = ROOT/'configs/frozen/action-value-robustness-v1.json'
ACTIVE_OUT = None
read, write, sha = base.read, base.write, base.sha


def guard():
    g = base.guard()
    g['source_sha256'].update({str(p.relative_to(ROOT)): sha(p) for p in (PLAN, Path(__file__))})
    return g


def assert_guard(out):
    if read(out/'guard.json') != guard(): raise ValueError('numerical source/runtime changed')


def validate_parent(parent, plan):
    if sha(base.PLAN) != plan['parent_plan_sha256']: raise ValueError('parent design changed')
    for name, digest in plan['parent_files_sha256'].items():
        if sha(parent/name) != digest: raise ValueError('parent record changed')
    p = read(base.PLAN); ids = p['fitting_cases']+p['evaluation_cases']
    hashes = {sid: sha(parent/'cases'/(sid+'.npz')) for sid in ids}
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    if digest != plan['parent_case_set_sha256']: raise ValueError('parent cases changed')
    for be, digest in plan['frozen_models_sha256'].items():
        if sha(parent/(be+'-model.npz')) != digest: raise ValueError('frozen model changed')
    for name, digest in read(parent/'guard.json')['source_sha256'].items():
        if sha(ROOT/name) != digest: raise ValueError('parent numerical source changed')
    return p


def collect(job):
    out, parent, archive, sid, rep = Path(job[0]), Path(job[1]), Path(job[2]), job[3], job[4]
    assert_guard(out); old = base.load_case(parent, sid)
    p = archive/'.local/expanded-v1/ca'/(sid+'.npz'); receipt = read(p.with_suffix('.json'))
    if sha(p) != receipt['npz_sha256']: raise ValueError('CA reference archive changed')
    with np.load(p, allow_pickle=False) as a: reference = a['ca'+str(rep)].copy()
    raw, inputs = base.native_env('ca', sid, spread_replicate=rep)
    if inputs['receipt_sha256'] != read(base.PLAN)['input_receipt_sha256'][sid]: raise ValueError('input receipt changed')
    if sha(base.WEATHER) != read(base.PLAN)['weather_sha256']: raise ValueError('weather changed')
    obs, _ = raw.reset(); obs = base.encoded_observation(obs); mask = raw.action_masks().copy()
    np.testing.assert_array_equal(obs, old['ca_obs']); np.testing.assert_array_equal(mask, old['ca_mask'])
    np.testing.assert_array_equal(raw.unwrapped.cumulative_burned, reference[0])
    env = base.CommonControlEnv(raw, reference[-1]); scores = []; burned = []; lines = []
    score, states, line = base.rollout(env, 0); np.testing.assert_array_equal(states, reference)
    for a in range(9):
        if a and mask[a]: score, states, line = base.rollout(env, a)
        elif a: score, states, line = scores[0], reference, lines[0]
        scores.append(dict(score)); burned.append(states[-1].copy()); lines.append(line.copy())
    env.close(); target = out/'replicates'/(sid+'-r'+str(rep)+'.npz')
    np.savez_compressed(target, obs=obs, mask=mask, reference=reference, burned=np.stack(burned),
                        line=np.stack(lines), saved=np.array([s['charged_saved_cells'] for s in scores]),
                        noop=np.array(scores[0]['noop_damage_cells']))
    write(target.with_suffix('.json'), dict(scenario_id=sid, replicate=rep, sha256=sha(target),
                                          reference_sha256=sha(p), status='PASS'))
    return sid, rep


def safe_collect(job):
    try: return collect(job)
    except Exception:
        import traceback
        print('replicate ERROR', job[3:], flush=True); traceback.print_exc(); raise


def replicate_case(out, sid, rep):
    p = out/'replicates'/(sid+'-r'+str(rep)+'.npz')
    if sha(p) != read(p.with_suffix('.json'))['sha256']: raise ValueError('replicate changed')
    with np.load(p, allow_pickle=False) as a: return {k: a[k].copy() for k in a.files}


def references(obs, mask, saved, names):
    actions = reference_actions(obs, mask)
    values = {name: float(saved[a]) for name, a in actions.items()}
    values['uniform_legal_exact'] = float(saved[1:][mask[1:]].mean()) if mask[1:].any() else 0.
    return np.array([values[n] for n in names])


def frozen_arm(out, parent, p, cases):
    with np.load(parent/'ca-model.npz', allow_pickle=False) as a: model = {k: a[k].copy() for k in a.files}
    names = read(PLAN)['primary']['references']; ids = p['evaluation_cases']
    saved = []; noops = []; refs = []; rows = []; old_actions = {r['scenario_id']: r['action']
        for r in read(parent/'analysis.json')['backends']['ca']['cases']}
    for rep in range(3):
        sr, nr, rr = [], [], []
        for sid in ids:
            c = ({k: cases[sid]['ca_'+k] for k in ('obs', 'mask', 'saved', 'noop')}
                 if rep == 0 else replicate_case(out, sid, rep))
            action = select_action(model, action_features(c['obs']), c['mask'])
            if action != old_actions[sid]: raise ValueError('frozen initial action differs across replicates')
            sr.append(float(c['saved'][action])); nr.append(float(c['noop']))
            rr.append(references(c['obs'], c['mask'], c['saved'], names))
            rows.append(dict(scenario_id=sid, replicate=rep, action=action, saved_cells=sr[-1], noop_cells=nr[-1]))
        saved.append(sr); noops.append(nr); refs.append(rr)
    saved, noops, refs = map(np.asarray, (saved, noops, refs))
    base_positive = np.array([cases[s]['simfire_noop'] > 0 for s in ids])
    metrics = summarize(saved, noops, refs, base_positive)
    per_rep = [summarize(saved[r:r+1], noops[r:r+1], refs[r:r+1],
                         np.array(metrics['primary_mask'])) for r in range(3)]
    original = read(parent/'analysis.json')['backends']['ca']['metrics']['mean_saved_percent']
    # Reproduce the old14 summary separately if any new replicate zero changes the new joint set.
    np.testing.assert_allclose(summarize(saved[:1], noops[:1], refs[:1], base_positive)['mean_saved_percent'], original, atol=1e-12)
    return dict(metrics=metrics, per_replicate=per_rep, reference_names=names, cases=rows)


def crossfit_arm(out, p, cases):
    ids = p['fitting_cases']+p['evaluation_cases']; names = p['references'] if 'references' in p else read(PLAN)['primary']['references']
    eligible = np.array([cases[s]['simfire_noop'] > 0 and cases[s]['ca_noop'] > 0 for s in ids])
    result = {}
    for be in ('simfire', 'ca'):
        x = np.array([action_features(cases[s][be+'_obs']) for s in ids])
        masks = np.array([cases[s][be+'_mask'] for s in ids])
        noops = np.array([cases[s][be+'_noop'] for s in ids], float)
        gains = np.array([cases[s][be+'_saved'] for s in ids], float)
        targets = gains[:, 1:]/np.maximum(noops[:, None], 1)
        reference_values = np.array([references(cases[s][be+'_obs'], masks[i], gains[i], names) for i, s in enumerate(ids)])
        ref_percent = reference_values/np.maximum(noops[:, None], 1)*100
        rows = []; selected = []; fit_reference = []
        for i, sid in enumerate(ids):
            model, fitting_ids, chosen = fit_fold(x, targets, masks, eligible, ids, sid, ref_percent)
            action = select_action(model, x[i], masks[i]); path = out/'folds'/(be+'-'+sid+'.npz')
            np.savez_compressed(path, **model)
            rows.append(dict(scenario_id=sid, action=action, fitting_ids=fitting_ids,
                model_sha256=sha(path), fitting_reference=names[chosen], saved_cells=float(gains[i, action]),
                noop_cells=float(noops[i]), reference_saved_cells=reference_values[i].tolist()))
            selected.append(gains[i, action]); fit_reference.append(reference_values[i, chosen])
        values = np.column_stack([reference_values, fit_reference])
        metrics = summarize(np.array(selected)[None, :], noops[None, :], values[None, :, :], eligible)
        result[be] = dict(metrics=metrics, reference_names=names+['fit_selected_reference'], cases=rows)
    return result


def main():
    global ACTIVE_OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--parent', type=Path, default=ROOT/'.local/action-value-v2')
    parser.add_argument('--archive', type=Path, default=ROOT.parent/'separate-clip-pilot')
    parser.add_argument('--pilot', action='store_true', help='first evaluation case, both new spreads; no fitting/scoring')
    args = parser.parse_args(); out = args.out.resolve(); parent = args.parent.resolve()
    base.setup_worker(); plan = read(PLAN); p = validate_parent(parent, plan)
    if out.exists(): raise FileExistsError('choose new output; completed/partial runs are preserved')
    out.mkdir(parents=True); (out/'replicates').mkdir(); (out/'folds').mkdir(); ACTIVE_OUT = out
    write(out/'guard.json', guard()); started = time.monotonic()
    status = dict(pid=os.getpid(), phase='collecting', started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    write(out/'status.json', status)
    def deadline(_signal, _frame):
        for child in multiprocessing.active_children(): child.terminate()
        raise TimeoutError('30 minute limit')
    signal.signal(signal.SIGALRM, deadline); signal.alarm(1800)
    jobs = [(str(out), str(parent), str(args.archive.resolve()), sid, r)
            for sid in (p['evaluation_cases'][:1] if args.pilot else p['evaluation_cases']) for r in (1, 2)]
    with ProcessPoolExecutor(3, mp_context=multiprocessing.get_context('spawn'), initializer=base.setup_worker) as pool:
        futures = [pool.submit(safe_collect, job) for job in jobs]
        for index, future in enumerate(as_completed(futures), 1):
            sid, r = future.result(); print('replicate PASS', sid, r, flush=True)
            status['completed_replicates'] = index; write(out/'status.json', status)
    assert_guard(out)
    if args.pilot:
        status.update(phase='pilot_complete', seconds=time.monotonic()-started); write(out/'status.json', status); return
    status['phase'] = 'crossfitting'; write(out/'status.json', status)
    cases = {s: base.load_case(parent, s) for s in p['fitting_cases']+p['evaluation_cases']}
    frozen = frozen_arm(out, parent, p, cases); folds = crossfit_arm(out, p, cases)
    validate_parent(parent, plan); assert_guard(out)
    write(out/'analysis.json', dict(scope='Exploratory TRAIN robustness; no independent holdout',
        guard=read(out/'guard.json'), frozen_ca=frozen, crossfit=folds, parent_audit_sha256=sha(parent/'audit.json')))
    status.update(phase='complete', seconds=time.monotonic()-started); write(out/'status.json', status)
    print('COMPLETE', flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as error:
        import traceback
        if ACTIVE_OUT is not None:
            status = read(ACTIVE_OUT/'status.json'); status.update(phase='failed', error=str(error))
            write(ACTIVE_OUT/'status.json', status)
        traceback.print_exc(); sys.exit(1)
