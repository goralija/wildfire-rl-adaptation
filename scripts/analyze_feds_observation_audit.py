#!/usr/bin/env python3
"""Nested TRAIN-only comparison of registered observation representations (ADR-035)."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from analyze_feds_b1 import load_table
from wildfire_rl.feds_simfire_setup import sha256_file
PLAN=ROOT/'configs/frozen/feds-observation-audit-v1.json'


def run_method(job):
    import numpy as np
    from wildfire_rl.feds_b1_learning import case_arrays, paired_interval
    from wildfire_rl.feds_observation_audit import audit_features, nested_actions, action_gain
    cases,mode,name,config,threshold=job
    started=time.monotonic()
    representation={'original28':'summary'}.get(config['features'],'directional' if '48 features' in config['features'] else 'full_grid')
    x=np.asarray([[audit_features(o,representation) for o in case['observations']] for case in cases])
    _,gains,masks=case_arrays(cases,mode);ids=[case['scenario_id'] for case in cases]
    kind='ridge' if 'ridge' in name else 'rbf'
    candidates=[(alpha,) for alpha in config['alpha']] if kind=='ridge' else [(alpha,b) for alpha in config['alpha'] for b in config['bandwidth']]
    rows=[]
    for i,case in enumerate(cases):
        row=nested_actions(x,gains,masks,ids,i,kind,candidates)
        # Outer outcomes are looked up only after the action sequence is fixed.
        row.update({'scenario_id':ids[i],'saved_ha':action_gain(gains[i],row['actions'])})
        matches=[r for r in case['outcomes'] if r['effective_actions']==row['actions']]
        if not matches or any(abs(r[mode+'_saved_cells']*3.24-row['saved_ha'])>1e-7 for r in matches):
            raise ValueError('OOF sequence/score mismatch')
        if sum(a!=0 for a in row['actions'])>1 or not all(masks[i,k,a] for k,a in enumerate(row['actions'])):
            raise ValueError('budget or legality violation')
        rows.append(row)
    baseline=np.asarray([c['references']['advancing_front'][mode+'_saved_cells']*3.24 for c in cases])
    oracle=np.asarray([max(r[mode+'_saved_cells'] for r in c['outcomes'])*3.24 for c in cases])
    deltas=np.asarray([r['saved_ha'] for r in rows])-baseline
    gain=float(deltas.mean());gap=float((oracle-baseline).mean());largest=int(np.argmax(np.abs(deltas)))
    return mode,name,{'feature_count':int(x.shape[2]),'mean_saved_ha':float(baseline.mean()+gain),
        'mean_gain_ha_vs_advancing_front':gain,'fraction_of_oracle_gap':gain/gap,
        'descriptive_paired_bootstrap_95':paired_interval(deltas),
        'without_largest_absolute_delta_ha':float(np.delete(deltas,largest).mean()),
        'largest_absolute_delta_fire':ids[largest],
        'better_fires':int((deltas>1e-8).sum()),'worse_fires':int((deltas< -1e-8).sum()),
        'continuation_threshold_met':bool(gain>=threshold['mean_gain_ha_vs_advancing_front'] and gain/gap>=threshold['fraction_of_oracle_gap']),
        'out_of_fold':rows,'seconds':time.monotonic()-started}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('table',type=Path)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=4)
    args=p.parse_args()
    if args.out.exists() or not 1<=args.workers<=4:p.error('new output and 1..4 workers required')
    plan=json.loads(PLAN.read_text())
    if sha256_file(args.table)!=plan['table_sha256']:p.error('unregistered table')
    table,cases=load_table(args.table)
    if len(cases)!=98 or table['settings']['weather_sha256']!=plan['weather_sha256']:p.error('changed cohort/weather')
    threshold=plan['continuation_threshold'];jobs=[(cases,mode,name,config,threshold) for mode in ('raw','charged') for name,config in plan['methods'].items()]
    started=time.monotonic();results={mode:{} for mode in ('raw','charged')}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(run_method,job) for job in jobs]):
            mode,name,row=future.result();results[mode][name]=row
            print(json.dumps({'mode':mode,'method':name,'seconds':row['seconds']}),flush=True)
    report={'schema_version':'feds-observation-audit-analysis/1.0','created_utc':datetime.now(timezone.utc).isoformat(),
        'label':'EXPLORATORY REUSED TRAIN; NESTED SELECTION; NOT FINAL OR PHYSICAL VALIDATION',
        'split':'train','case_count':98,'validation_used':False,'test_cases_loaded':False,
        'plan_sha256':sha256_file(PLAN),'table_sha256':sha256_file(args.table),'results':results,
        'uncertainty':plan['uncertainty'],'selection':plan['evaluation'],'continuation_threshold':threshold,
        'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_hashes':{str(path.relative_to(ROOT)):sha256_file(path) for path in [Path(__file__),ROOT/'src/wildfire_rl/feds_observation_audit.py']},
        'runtime':{'python':sys.version,'numpy':importlib.metadata.version('numpy')},'wall_minutes':(time.monotonic()-started)/60}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')

if __name__=='__main__':main()
