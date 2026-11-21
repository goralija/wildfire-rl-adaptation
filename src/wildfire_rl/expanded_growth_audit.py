"""Selection, guarded reuse and predeclared strata for the61-case TRAIN audit."""
import hashlib
import json
import math
from pathlib import Path
import shutil
import numpy as np

from .observed_growth_audit import require_train, summarize_endpoint


def select_eligible_cases(paired_plan, manifest):
    qc = paired_plan['input_qc']['cases']
    if len({r['scenario_id'] for r in qc}) != len(qc):
        raise ValueError('Duplicate input QC record')
    eligible = [r for r in qc if r['eligible']]
    for row in eligible:
        if any(row[key] != 0 for key in ('front_unsupported_common_vegetation',
                                        'unknown_fuel_count','elevation_filled_cells')):
            raise ValueError('The frozen eligible inputs changed; do not silently exclude')
    by_id = {c['scenario_id']:c for c in manifest['cases']}
    selected = []
    for row in sorted(eligible,key=lambda r:r['scenario_id']):
        case = by_id[row['scenario_id']]
        require_train(case)
        selected.append(case)
    return selected


def growth_group(initial_cells, observed_new_cells):
    counts = (initial_cells,observed_new_cells)
    if any(not math.isfinite(float(x)) or int(x) != x for x in counts):
        raise ValueError('Finite integer cell counts required')
    if initial_cells <= 0 or observed_new_cells < 0:
        raise ValueError('Positive initial damage and nonnegative observed growth required')
    if observed_new_cells == 0: return 'zero_growth'
    # Integer comparison gives an exact .10 boundary without float rounding.
    return 'near_stalled' if 10*observed_new_cells < initial_cells else 'growing'


def _sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reuse_prediction(previous, target, expected, guard):
    previous, target = Path(previous), Path(target)
    record = json.loads(previous.read_text())
    old_guard = record['guard']
    if (record['scenario_id'] != previous.stem or target.stem != previous.stem
            or _sha(previous) != expected['record_sha256']
            or _sha(previous.with_suffix('.npz')) != expected['npz_sha256']
            or record['npz_sha256'] != expected['npz_sha256']
            or old_guard['runtime'] != expected['runtime']
            or old_guard['runtime'] != guard['runtime']
            or old_guard['backend'] != guard['backend']
            or record['input_receipt_sha256'] != expected['input_receipt_sha256']):
        raise ValueError('Original prediction, input or runtime changed')
    old, new = old_guard['common'], guard['common']
    if any(old[key] != new[key] for key in ('weather_sha256','manifest_sha256')):
        raise ValueError('Original weather or manifest changed')
    if any(new['source_sha256'].get(f) != h for f,h in old['source_sha256'].items()):
        raise ValueError('Original numerical sources changed')
    if target.exists() or target.with_suffix('.npz').exists():
        raise FileExistsError('Reuse must not overwrite predictions')
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(previous.with_suffix('.npz'),target.with_suffix('.npz'))
    result = {**record,'guard':guard,'compute_reused':True,
              'reused_from':{'task':'TASK-041','record_sha256':expected['record_sha256'],
                             'npz_sha256':expected['npz_sha256'],'original_guard':old_guard}}
    target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


def trace_noop(env, initial):
    env.reset();base = env.env if hasattr(env,'env') else env
    np.testing.assert_array_equal(base.cumulative_burned,initial)
    masks = [np.asarray(initial,bool).copy()]
    for k in range(4):
        if not env.action_masks()[0]: raise ValueError('No-op missing')
        _,_,done,trunc,_ = env.step(0)
        if done != (k==3) or trunc or base.remaining_budget != 1:
            raise ValueError('No-op changed budget or full horizon')
        masks.append(base.cumulative_burned.copy())
        if (masks[-2]&~masks[-1]).any(): raise ValueError('Cumulative damage lost')
    return np.stack(masks)


def subgroup_summaries(rows, previous_ids):
    classified = {}
    for row in rows:
        if row['complete']:
            r = row['metrics']['raw']['48']['simfire']
            classified[row['scenario_id']] = growth_group(r['initial_cells'],r['observed_growth_cells'])
    groups = ('zero_growth','near_stalled','growing')
    def group(name): return [r for r in rows if classified.get(r['scenario_id']) == name]
    return {'classification':classified,
            'unclassified_missing_ids':[r['scenario_id'] for r in rows if not r['complete']],
            'previous_cases':summarize_endpoint([r for r in rows if r['scenario_id'] in previous_ids]),
            'new_cases':summarize_endpoint([r for r in rows if r['scenario_id'] not in previous_ids]),
            'growth_groups':{name:summarize_endpoint(group(name)) for name in groups},
            'growth_groups_fully_covered':{name:summarize_endpoint(group(name),fully_covered=True) for name in groups}}
