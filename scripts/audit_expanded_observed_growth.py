#!/usr/bin/env python3
"""ADR-047: all61 eligible TRAIN starts, unchanged frozen dynamics and metrics."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from pathlib import Path
import sys
import time
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'),str(ROOT/'scripts')]
import audit_paired_observed_growth as base
import numpy as np
from wildfire_rl.expanded_growth_audit import (
    select_eligible_cases, reuse_prediction, trace_noop, subgroup_summaries,
)
from wildfire_rl.feds_simfire_setup import load_case_inputs

PLAN = ROOT/'configs/frozen/expanded-observed-growth-v1.json'
PAIRED_PLAN = ROOT/'configs/frozen/ca-simfire-paired-v1.json'
PREVIOUS_REPORT = ROOT/'reports/real-fire-data/paired-observed-growth-v1.json'
PREVIOUS = ROOT/'.local/previous-growth'


def context():
    plan = base.read(PLAN); previous = base.read(PREVIOUS_REPORT)
    for file,key in [(PAIRED_PLAN,'paired_plan_sha256'),(PREVIOUS_REPORT,'previous_report_sha256'),
                     (base.MANIFEST,'manifest_sha256'),(base.WEATHER,'weather_sha256'),
                     (base.TABLE/'table-98.json','sf_table_sha256')]:
        if base.sha(file)!=plan[key]: raise ValueError('Changed frozen input: '+str(file))
    cases = select_eligible_cases(base.read(PAIRED_PLAN),base.read(base.MANIFEST))
    ids = [c['scenario_id'] for c in cases]
    if len(ids)!=61 or ids!=plan['cases'] or plan['previous_cases']!=previous['plan']['cases']:
        raise ValueError('The complete frozen61-case frame is required')
    if plan['simfire_params']!=previous['plan']['simfire_params']:
        raise ValueError('Frozen simulator parameters changed')
    sources = dict(previous['common']['source_sha256'])
    for f,h in sources.items():
        if base.sha(ROOT/f)!=h: raise ValueError('Previous numerical source changed: '+f)
    for f in ['src/wildfire_rl/expanded_growth_audit.py','scripts/audit_expanded_observed_growth.py']:
        sources[f] = base.sha(ROOT/f)
    common = {**previous['common'],'plan_sha256':base.sha(PLAN),'source_sha256':sources,
              'previous_report_sha256':base.sha(PREVIOUS_REPORT)}
    return plan,previous,cases,common


def predict_case(job):
    sid,backend,plan,previous,guard,out = job
    folder = Path(out)/backend;path = folder/(sid+'.json')
    if path.exists():
        record=base.read(path)
        if record['guard']!=guard or base.sha(path.with_suffix('.npz'))!=record['npz_sha256']:
            raise ValueError('Expanded resume mismatch')
        return record
    if base.sha(base.TABLE/(sid+'.json'))!=plan['sf_case_json_sha256'][sid]:
        raise ValueError('Original case record changed')
    inputs = load_case_inputs(sid,split='train',weather_path=base.WEATHER,input_root=base.INPUTS)
    if inputs['receipt_sha256']!=plan['input_receipt_sha256'][sid]:
        raise ValueError('Frozen input receipt changed')
    if sid in plan['previous_cases']:
        expected={**plan['previous_predictions'][sid][backend],
                  'input_receipt_sha256':inputs['receipt_sha256']}
        return reuse_prediction(PREVIOUS/backend/(sid+'.json'),path,expected,guard)
    if backend=='simfire':
        return base.predict_case((sid,backend,plan,previous,guard,out))
    from run_paired_simulators import bridge
    started=time.monotonic();initial=inputs['scar']|inputs['front'];arrays={'initial':initial}
    for rep in range(3):
        env=bridge(inputs,rep);arrays['ca'+str(rep)]=trace_noop(env,initial);env.close()
    repeated=False
    if sid==plan['pilot_new_cases'][0]:
        for rep in range(3):
            env=bridge(inputs,rep);np.testing.assert_array_equal(trace_noop(env,initial),arrays['ca'+str(rep)]);env.close()
        repeated=True
    folder.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(path.with_suffix('.npz'),**arrays)
    record={'scenario_id':sid,'backend':backend,'guard':guard,
            'time_alignment':base.validate_time_alignment(inputs['case'],inputs['weather']),
            'input_receipt_sha256':inputs['receipt_sha256'],'npz_sha256':base.sha(path.with_suffix('.npz')),
            'archived_endpoint_check':'NOT_APPLICABLE_NEW_CA_CASE',
            'full_horizon_cumulative_check':'PASS','compute_reused':False,
            'all3_replicates_first_case_replay':'PASS' if repeated else 'not_selected',
            'nice':os.getpriority(os.PRIO_PROCESS,0),
            'seconds':time.monotonic()-started}
    base.write(path,record);return record


def score(out,plan,previous,cases,common):
    target=out/'expanded-summary.json'
    if target.exists():raise FileExistsError('Final expanded summary is immutable')
    if not (out/'analysis.json').exists():
        base.score(out,plan,previous,cases,common)
    report=base.read(out/'analysis.json')
    if report['common']!=common or report['plan']!=plan:
        raise ValueError('Changed base analysis')
    groups=subgroup_summaries(report['rows'],plan['previous_cases'])
    result={'schema_version':'expanded-growth-description/1.0','task':'TASK-042',
            'source_analysis_sha256':base.sha(out/'analysis.json'),'common':common,
            'scope':'Frozen61 compatible TRAIN starts, primaryCA0, all3 replicas and predeclared strata; no physical validation',
            'all_cases':report['summary']['raw']['48'],'fully_covered':report['fully_covered_48h'],
            **groups}
    base.write(target,result)
    print(json.dumps({'case_count':len(cases),'complete':len(result['all_cases']['complete_ids']),
                      'fully_covered':len(result['fully_covered']['complete_ids']),
                      'groups':{k:len(v['complete_ids']) for k,v in groups['growth_groups'].items()},
                      'methods':result['all_cases']['methods']},indent=2),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=('predict','score'),required=True)
    p.add_argument('--backend',choices=('simfire','ca'))
    p.add_argument('--pilot',action='store_true')
    p.add_argument('--workers',type=int,default=3)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if not 1<=args.workers<=3:p.error('At most3workers plus coordinator')
    plan,previous,cases,common=context();base.priority()
    args.out.mkdir(parents=True,exist_ok=True)
    if args.stage=='score':
        if args.pilot:p.error('Scoring requires all61 cases')
        score(args.out,plan,previous,cases,common);return
    if args.backend is None:p.error('Prediction backend required')
    ids=plan['pilot_new_cases'] if args.pilot else plan['cases']
    guard={'common':common,'runtime':base.runtime(args.backend),'backend':args.backend}
    jobs=[(sid,args.backend,plan,previous,guard,str(args.out)) for sid in ids]
    started=time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers,initializer=base.priority) as pool:
        for k,future in enumerate(as_completed([pool.submit(predict_case,j) for j in jobs]),1):
            r=future.result();print(json.dumps({'done':k,'total':len(jobs),'case':r['scenario_id'],
                'reused':r.get('compute_reused',False),'case_seconds':r['seconds']}),flush=True)
    print(json.dumps({'status':'PASS','backend':args.backend,'cases':len(ids),'seconds':time.monotonic()-started}),flush=True)


if __name__=='__main__':main()
