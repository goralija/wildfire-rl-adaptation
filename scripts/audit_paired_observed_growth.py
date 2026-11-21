#!/usr/bin/env python3
"""ADR-045 frozen TRAIN no-op replay, then post-hoc exact-time FEDS diagnostics."""
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[name] = '1'
import numpy as np
from wildfire_rl.observed_growth_audit import (
    METHODS, growth_metrics, observed_envelope, paired_contrast,
    rasterize_observation, read_geometry_parts, require_train,
    summarize_endpoint, validate_time_alignment,
)
from wildfire_rl.feds_simfire_setup import load_case_inputs, SimFireParams

PLAN = ROOT/'configs/frozen/paired-observed-growth-v1.json'
MANIFEST = ROOT/'data/manifests/feds-episode-cohort-v1.json'
PAIRED = ROOT/'reports/synthetic/ca-simfire-paired-v1.json'
WEATHER = ROOT/'.local/gridmet/feds-episode-weather-v1.json'
INPUTS = ROOT/'.local/feds-simfire-cases'
TABLE = ROOT/'.local/b1-cases'
OLD_CA = ROOT/'.local/paired-v1-final/cases'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def write(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n'); temp.replace(path)


def context():
    plan = read(PLAN); paired = read(PAIRED); manifest = read(MANIFEST)
    for path, key in [(MANIFEST,'manifest_sha256'), (PAIRED,'paired_report_sha256'),
                      (WEATHER,'weather_sha256'), (TABLE/'table-98.json','sf_table_sha256'),
                      (ROOT/'configs/frozen/ca-simfire-paired-v1.json','paired_plan_sha256')]:
        if sha(path) != plan[key]: raise ValueError('Changed protocol input: '+str(path))
    by_id = {c['scenario_id']:c for c in manifest['cases']}
    cases = [by_id[sid] for sid in plan['cases']]
    for c in cases: require_train(c)
    if len(set(plan['cases'])) != 16 or plan['cases'] != paired['plan']['cases']:
        raise ValueError('Exactly the original16 selected TRAIN cases required')
    sources = dict(paired['guard']['source_sha256'])
    for f, digest in sources.items():
        if sha(ROOT/f) != digest: raise ValueError('Changed frozen model source: '+f)
    for f in ['src/wildfire_rl/observed_growth_audit.py', 'scripts/audit_paired_observed_growth.py',
              'src/wildfire_rl/gridmet_weather.py','src/wildfire_rl/feds_spread_metrics.py',
              'src/wildfire_rl/simfire_initial_state.py','src/wildfire_rl/simfire_timebase.py']:
        sources[f] = sha(ROOT/f)
    common = {'plan_sha256':sha(PLAN),'source_sha256':sources,
              'paired_report_sha256':sha(PAIRED),'weather_sha256':sha(WEATHER),
              'manifest_sha256':sha(MANIFEST)}
    return plan, paired, cases, common


def priority():
    if os.getpriority(os.PRIO_PROCESS,0) < 19: os.setpriority(os.PRIO_PROCESS,0,19)
    if os.getpriority(os.PRIO_PROCESS,0) < 19: raise RuntimeError('nice19 required')


def runtime(backend):
    import importlib.metadata as metadata
    packages = ['numpy','rasterio','pyproj','gymnasium','scipy']
    if backend == 'simfire': packages.append('simfire')
    return {'python':platform.python_version(),
            'packages':{p:metadata.version(p) for p in packages}}


def predict_case(job):
    sid, backend, plan, paired, guard, out = job
    out = Path(out)/backend; path = out/(sid+'.json')
    if path.exists():
        record = read(path)
        if record['guard'] != guard or sha(path.with_suffix('.npz')) != record['npz_sha256']:
            raise ValueError('Prediction resume mismatch')
        return record
    started = time.monotonic()
    inputs = load_case_inputs(sid, split='train', weather_path=WEATHER, input_root=INPUTS)
    alignment = validate_time_alignment(inputs['case'], inputs['weather'])
    original = read(TABLE/(sid+'.json'))
    if inputs['receipt_sha256'] != original['input_receipt_sha256']:
        raise ValueError('Original real inputs changed')
    initial = inputs['scar'] | inputs['front']; arrays = {'initial':initial}
    if backend == 'simfire':
        from wildfire_rl.feds_simfire_env import FedsSimFireEnv
        envs = [('simfire', FedsSimFireEnv(sim_params=SimFireParams(**plan['simfire_params']),
                    split='train', scenario_ids=[sid], budgets=(1,), max_budget=4,
                    line_placement='front_edge', weather_observation='previous',
                    input_root=INPUTS, weather_path=WEATHER))]
        if sha(TABLE/(sid+'.npz')) != original['mask_file_sha256']:
            raise ValueError('Original SF mask archive changed')
        with np.load(TABLE/(sid+'.npz'), allow_pickle=False) as z: expected = z['noop'].copy()
    else:
        from run_paired_simulators import bridge
        envs = [('ca'+str(rep), bridge(inputs,rep)) for rep in range(3)]
        old = read(OLD_CA/(sid+'.json'))
        if sha(OLD_CA/(sid+'.npz')) != old['npz_sha256']:
            raise ValueError('Original CA mask archive changed')
        with np.load(OLD_CA/(sid+'.npz'), allow_pickle=False) as z: expected = z['noop'].copy()
    for method, env in envs:
        if backend == 'simfire':
            env.reset(seed=0, options={'scenario_id':sid,'budget':1}); base = env
        else:
            env.reset(); base = env.env
        np.testing.assert_array_equal(base.cumulative_burned, initial)
        masks = [initial.copy()]
        for k in range(4):
            if not env.action_masks()[0]: raise ValueError('No-op missing')
            _, _, done, trunc, _ = env.step(0)
            if done != (k == 3) or trunc or base.remaining_budget != 1:
                raise ValueError('Full horizon or no-op budget mismatch')
            masks.append(base.cumulative_burned.copy())
            if (masks[-2] & ~masks[-1]).any(): raise ValueError('Cumulative damage lost')
        arrays[method] = np.stack(masks); env.close()
        if method in ('simfire','ca0'): np.testing.assert_array_equal(masks[-1], expected)
        if method in ('ca1','ca2'):
            prior = next(r for r in paired['robustness_rows']
                         if r['scenario_id'] == sid and r['replicate'] == int(method[-1]))
            if int((masks[-1]&~initial).sum()) != prior['results']['noop']['noop']:
                raise ValueError('Original CA robustness count mismatch')
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path.with_suffix('.npz'), **arrays)
    record = {'scenario_id':sid,'backend':backend,'guard':guard,'time_alignment':alignment,
              'input_receipt_sha256':inputs['receipt_sha256'],'npz_sha256':sha(path.with_suffix('.npz')),
              'archived_endpoint_check':'PASS','full_horizon_cumulative_check':'PASS',
              'seconds':time.monotonic()-started,'nice':os.getpriority(os.PRIO_PROCESS,0)}
    write(path,record); return record


def predictions(out, cases, common):
    """Verify both completed cohorts and freeze their receipts before FEDS is opened."""
    records = {}; arrays = {}; runtimes = {}
    for case in cases:
        sid = case['scenario_id']; arrays[sid] = {}; records[sid] = {}
        for backend in ('simfire','ca'):
            path = out/backend/(sid+'.json'); record = read(path)
            if record['guard']['common'] != common or sha(path.with_suffix('.npz')) != record['npz_sha256']:
                raise ValueError('Changed or incomplete frozen prediction')
            if backend in runtimes and runtimes[backend] != record['guard']['runtime']:
                raise ValueError('Mixed prediction runtimes within backend')
            runtimes[backend] = record['guard']['runtime']
            with np.load(path.with_suffix('.npz'),allow_pickle=False) as z:
                for key in z.files:
                    if key in arrays[sid]: np.testing.assert_array_equal(arrays[sid][key],z[key])
                    arrays[sid][key] = z[key].copy()
            records[sid][backend] = record
    freeze = {'status':'PASS','cases':[c['scenario_id'] for c in cases], 'common':common,
              'prediction_record_sha256':{str(p.relative_to(out)):sha(p) for backend in ('simfire','ca')
                 for p in sorted((out/backend).glob('*.json'))}}
    path = out/'predictions-frozen.json'
    if path.exists() and read(path) != freeze: raise ValueError('Prediction freeze changed')
    write(path,freeze)
    return records, arrays, freeze


def observations(out, cases, plan, common):
    """Cache selected projected geometry and masks, with full archive provenance."""
    folder = out/'observations'; manifest_path = folder/'manifest.json'
    if manifest_path.exists():
        manifest = read(manifest_path)
        if manifest['common'] != common: raise ValueError('Observation cache source mismatch')
        for file, digest in manifest['files'].items():
            if sha(folder/file) != digest: raise ValueError('Observation cache changed')
        records = {}
        for case in cases:
            sid = case['scenario_id']; records[sid] = read(folder/(sid+'.json'))
            with np.load(folder/(sid+'.npz'),allow_pickle=False) as z:
                for k,state in enumerate(records[sid]['states']):
                    state['mask'] = z[str(k)].copy() if str(k) in z.files else None
        return records, manifest
    # No fallback to remote byte ranges: only the two exact local TRAIN archives.
    from audit_feds_fpa_fle_crosswalk import _feds_file_path
    paths = {}
    for year, record in plan['archives'].items():
        local = ROOT/'.local/feds-conus'/record['file']
        if not local.is_file() or sha(local) != record['sha256']:
            raise ValueError('Missing or changed local TRAIN archive')
        path = _feds_file_path(int(year))  # Also validates pinned upstream MD5.
        if Path(path).resolve() != local.resolve(): raise ValueError('Local archive required')
        paths[int(year)] = path
    parts = read_geometry_parts(cases, paths)
    from pyproj import Transformer
    from shapely.geometry import mapping
    from shapely.ops import transform, unary_union
    folder.mkdir(parents=True,exist_ok=True); records = {}
    for case in cases:
        sid = case['scenario_id']; receipt = read(INPUTS/sid/'input-receipt.json')
        states = []; vectors = []
        for entry in parts[sid]:
            geom = None; invalid = False
            if entry['parts']:
                invalid = any(not p.is_valid or p.is_empty for p in entry['parts'])
                if not invalid:
                    project = Transformer.from_crs(entry['source_crs'],receipt['grid']['crs'],always_xy=True).transform
                    geom = transform(project,unary_union(entry['parts']))
            state = rasterize_observation(case,receipt['grid'],geom)
            if invalid: state['status'] = 'invalid'
            state.update(timestamp=entry['timestamp'],parts=len(entry['parts']))
            states.append(state)
            vectors.append({'timestamp':entry['timestamp'],'geometry':mapping(geom) if geom is not None else None})
        np.savez_compressed(folder/(sid+'.npz'),**{str(k):s['mask'] for k,s in enumerate(states) if s['mask'] is not None})
        metadata = {'scenario_id':sid,'grid':receipt['grid'],
                    'states':[{k:v for k,v in s.items() if k!='mask'} for s in states]}
        write(folder/(sid+'.json'),metadata)
        write(folder/(sid+'.vectors.json'),{'projected_crs':receipt['grid']['crs'], 'states':vectors})
        records[sid] = {'scenario_id':sid,'grid':receipt['grid'],'states':states}
    manifest = {'common':common,'archives':plan['archives'],'files':{p.name:sha(p) for p in sorted(folder.iterdir())}}
    write(manifest_path,manifest)
    return records,manifest


def time_pooled(rows, kind):
    complete = [r for r in rows if r['complete'] and any(
        r['metrics'][kind][str(h)]['simfire']['observed_growth_cells']>0 for h in (12,24,36,48))]
    result = {m:[] for m in METHODS}
    for row in complete:
        for method in METHODS:
            replicas = ('ca0','ca1','ca2') if method=='ca_mean3' else (method,)
            scores = []
            for rep in replicas:
                metrics = [row['metrics'][kind][str(h)][rep] for h in (12,24,36,48)]
                hit = sum(m['growth_intersection_cells'] for m in metrics)
                union = sum(m['predicted_growth_cells']+m['observed_growth_cells']-m['growth_intersection_cells'] for m in metrics)
                scores.append(hit/union)
            result[method].append(float(np.mean(scores)))
    return {'case_ids':[r['scenario_id'] for r in complete],
            'mean_case_time_pooled_iou':{m:float(np.mean(x)) if x else None for m,x in result.items()},
            'ca_mean3_minus_simfire':paired_contrast(result['ca_mean3'],result['simfire'])}


def score(out, plan, paired, cases, common):
    target = out/'analysis.json'
    if target.exists(): raise FileExistsError('Use a new output; final analysis is immutable')
    pred_records, arrays, freeze = predictions(out,cases,common)
    obs, obs_manifest = observations(out,cases,plan,common)
    from wildfire_rl.feds_spread_metrics import ellipse_ignition_point, elliptical_growth_reference
    from wildfire_rl.feds_simfire_setup import record_forcing
    rows = []
    for case in cases:
        sid = case['scenario_id']; data = arrays[sid]; initial = data['initial']
        inputs = load_case_inputs(sid,split='train',weather_path=WEATHER,input_root=INPUTS)
        observed = obs[sid]['states']; masks = [s['mask'] for s in observed]
        if masks[0] is not None: np.testing.assert_array_equal(masks[0],inputs['scar'])
        complete = all(s['status']=='ok' for s in observed)
        row = {'scenario_id':sid,'complete':complete,'fully_covered':all(s['fully_covered'] for s in observed),
               'time_alignment':pred_records[sid]['simfire']['time_alignment'],
               'observations':[{k:v for k,v in s.items() if k!='mask'} for s in observed],
               'initial_front_on_nonfuel':int((inputs['front'] & ~np.isin(inputs['fuel'],range(1,14))).sum()),
               'initial_front_outside_scar':int((inputs['front'] & ~inputs['scar']).sum())}
        if not complete:
            rows.append(row); continue
        envelope = observed_envelope(masks)
        direction = record_forcing(inputs['weather']['segments'][0],SimFireParams(**plan['simfire_params']))['wind_direction_degrees_clockwise_north_to']
        centre = ellipse_ignition_point(inputs['front'],direction)
        data['persistence'] = np.stack([initial]*5)
        data['ellipse'] = np.stack([elliptical_growth_reference(initial,center_row=centre[0],center_column=centre[1],hours=h,downwind_degrees=direction) for h in (0,12,24,36,48)])
        row['metrics'] = {'raw':{},'envelope':{}}
        row['observation_diagnostics'] = []
        for k in range(1,5):
            for kind,targets in [('raw',masks),('envelope',envelope)]:
                row['metrics'][kind][str(k*12)] = {method:growth_metrics(initial,data[method][k],targets[k])
                                                  for method in METHODS if method!='ca_mean3'}
            growth = masks[k] & ~initial
            row['observation_diagnostics'].append({'hours':k*12,
                'lost_since_previous_observation_cells':int((masks[k-1]&~masks[k]).sum()),
                'envelope_extra_cells':int((envelope[k]&~masks[k]).sum()),
                'observed_new_cells_on_nonfuel':int((growth & ~np.isin(inputs['fuel'],range(1,14))).sum()),
                'observed_new_cells':int(growth.sum())})
        row['observed_growth_at_least_10percent'] = bool(masks[-1].sum() >= 1.10*initial.sum())
        rows.append(row)
    summaries = {kind:{str(h):summarize_endpoint(rows,kind=kind,horizon=h) for h in (12,24,36,48)}
                 for kind in ('raw','envelope')}
    import importlib.metadata as metadata
    result = {'schema_version':'paired-observed-growth-result/1.0','date':plan['date'],
              'plan':plan,'common':common,'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'scoring_runtime':{'python':platform.python_version(),
                  'packages':{p:metadata.version(p) for p in ('numpy','fiona','shapely','pyproj','rasterio')}},
              'scope':'Exploratory frozen TRAIN diagnostic, not physical validation or no-suppression ground truth',
              'prediction_freeze_sha256':sha(out/'predictions-frozen.json'),
              'observation_manifest_sha256':sha(out/'observations/manifest.json'),
              'prediction_records':pred_records,'rows':rows,'summary':summaries,
              'fully_covered_48h':summarize_endpoint(rows,fully_covered=True),
              'observed_at_least_10percent_48h':summarize_endpoint([r for r in rows if r.get('observed_growth_at_least_10percent')]),
              'time_pooled':{kind:time_pooled(rows,kind) for kind in ('raw','envelope')},
              'validation_used':False,'test_cases_loaded':False,'parameter_search':False,'policy_training':False}
    write(target,result)
    print(json.dumps({'complete_cases':sum(r['complete'] for r in rows),
                      'observed_positive':len(summaries['raw']['48']['observed_positive_ids']),
                      'methods':summaries['raw']['48']['methods']},indent=2),flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('predict','score'),required=True)
    parser.add_argument('--backend',choices=('simfire','ca'))
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--case-limit',type=int,choices=(2,16),default=16)
    args = parser.parse_args()
    if not 1<=args.workers<=3: parser.error('At most3workers plus coordinator')
    plan,paired,cases,common = context(); args.out.mkdir(parents=True,exist_ok=True)
    priority()
    if args.stage=='score':
        if args.case_limit!=16: parser.error('Scoring requires all16 original cases')
        score(args.out,plan,paired,cases,common); return
    if args.backend is None: parser.error('Prediction backend required')
    guard = {'common':common,'runtime':runtime(args.backend),'backend':args.backend}
    jobs = [(c['scenario_id'],args.backend,plan,paired,guard,str(args.out)) for c in cases[:args.case_limit]]
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers,initializer=priority) as pool:
        for i,future in enumerate(as_completed([pool.submit(predict_case,j) for j in jobs]),1):
            r = future.result();print(json.dumps({'done':i,'total':len(jobs),'case':r['scenario_id'],'seconds':r['seconds']}),flush=True)
    print(json.dumps({'status':'PASS','backend':args.backend,'cases':len(jobs),'seconds':time.monotonic()-started}),flush=True)


if __name__=='__main__': main()
