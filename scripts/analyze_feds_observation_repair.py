#!/usr/bin/env python3
"""Paired registered v2 observation/mask ablations with nested TRAIN selection."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
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
PLAN=ROOT/'configs/frozen/feds-observation-repair-v2.json'


def prepare(dataset_path,table_path):
    import numpy as np
    from wildfire_rl.feds_observation_dataset import load_observation_case
    from wildfire_rl.feds_repaired_learning import repaired_features,REPRESENTATIONS
    from wildfire_rl.feds_b1_learning import case_arrays
    from wildfire_rl.feds_b1 import policy_sequence
    from wildfire_rl.feds_heuristics import make_heuristic
    plan=json.loads(PLAN.read_text());dataset=json.loads(dataset_path.read_text());_,cases=load_table(table_path)
    if dataset.get('split')!='train' or dataset.get('validation_used') is not False or dataset.get('test_cases_loaded') is not False:
        raise ValueError('closed split violation')
    settings=dataset['settings']
    if len(cases)!=98 or dataset['case_count']!=98 or settings['plan_sha256']!=sha256_file(PLAN) or settings['source_table_sha256']!=sha256_file(table_path) or sha256_file(table_path)!=plan['table_sha256'] or settings['weather_sha256']!=plan['weather_sha256']:
        raise ValueError('changed registered dataset/table/plan')
    items={item['scenario_id']:item for item in dataset['cases']}
    if len(items)!=98 or set(items)!={c['scenario_id'] for c in cases}:raise ValueError('incomplete/duplicate cohort')
    x={name:[] for name in REPRESENTATIONS};masks={name:[] for name in plan['mask_modes']}
    heuristic_names=plan['heuristics'];h={mode:{mask:[] for mask in masks} for mode in ('raw','charged')};blocked=[]
    for case in cases:
        record,observations,case_masks=load_observation_case(dataset_path.parent,items[case['scenario_id']],settings)
        blocked.extend([{'scenario_id':case['scenario_id'],**b} for b in record['blocked_nonfuel_sequences']])
        for name in x:x[name].append([repaired_features(o,name) for o in observations])
        for mask in masks:
            masks[mask].append(case_masks[mask]);scores={mode:[] for mode in h}
            for name in heuristic_names:
                if name=='advancing_front64':
                    rule=make_heuristic('advancing_front')
                    policy=lambda obs,mask:rule({**obs,'grid':obs['global_grid']},mask)
                else:policy=make_heuristic(name)
                actions=policy_sequence(policy,observations,case_masks[mask])
                matches=[row for row in case['outcomes'] if tuple(row['effective_actions'])==actions]
                if not matches:raise ValueError('missing heuristic outcome')
                for mode in h:
                    values={row[mode+'_saved_cells'] for row in matches}
                    if len(values)!=1:raise ValueError('nondeterministic matched outcome')
                    scores[mode].append(float(next(iter(values)))*3.24)
            for mode in h:h[mode][mask].append(scores[mode])
    gains={mode:case_arrays(cases,mode)[1] for mode in h}
    return plan,cases,{name:np.asarray(value) for name,value in x.items()},gains,{name:np.asarray(value,dtype=bool) for name,value in masks.items()},h,blocked


def run(job):
    import numpy as np
    from wildfire_rl.feds_observation_audit import nested_actions,action_gain
    from wildfire_rl.feds_repaired_learning import select_reference,legal_oracle
    from wildfire_rl.feds_b1_learning import paired_interval
    mode,mask_name,representation,x,gains,masks,ids,heuristics,plan=job
    started=time.monotonic();heuristics=np.asarray(heuristics);names=plan['heuristics']
    nonzero=[i for i,name in enumerate(names) if name!='noop'];reference_values=heuristics[:,nonzero]
    model=plan['model'];candidates=[(a,b) for a in model['alpha'] for b in model['bandwidth']]
    rows=[]
    for i,key in enumerate(ids):
        row=nested_actions(x,gains,masks,ids,i,'rbf',candidates)
        actions=row['actions'];value=action_gain(gains[i],actions)
        if sum(a!=0 for a in actions)>1 or not all(masks[i,k,a] for k,a in enumerate(actions)):raise ValueError('budget/legality failure')
        reference=nonzero[select_reference(reference_values,i)]
        rows.append({'scenario_id':key,**row,'saved_ha':value,'reference_name':names[reference],
                     'reference_saved_ha':float(heuristics[i,reference])})
    values=np.asarray([r['saved_ha'] for r in rows]);reference=np.asarray([r['reference_saved_ha'] for r in rows])
    deltas=values-reference;oracle=np.asarray([legal_oracle(gains[i],masks[i]) for i in range(len(ids))])
    gain=float(deltas.mean());gap=float((oracle-reference).mean());threshold=plan['continuation_threshold']
    return mode,mask_name,representation,{'primary':representation=='terrain536' and mask_name=='burnable_lines',
        'feature_count':int(x.shape[2]),'mean_saved_ha':float(values.mean()),'reference_mean_saved_ha':float(reference.mean()),
        'mean_gain_ha_vs_reference':gain,'oracle_mean_saved_ha':float(oracle.mean()),'oracle_gap_vs_reference_ha':gap,
        'fraction_of_oracle_gap':gain/gap if gap>0 else None,
        'descriptive_paired_bootstrap_95':paired_interval(deltas),'without_largest_absolute_delta_ha':float(np.delete(deltas,int(np.argmax(np.abs(deltas)))).mean()),
        'better_fires':int((deltas>1e-8).sum()),'worse_fires':int((deltas< -1e-8).sum()),
        'continuation_threshold_met':bool(gap>0 and gain>=threshold['mean_gain_ha_vs_reference'] and gain/gap>=threshold['fraction_of_oracle_gap']),
        'mean_gain_ha_vs_matched_advancing_front':float((values-heuristics[:,names.index('advancing_front')]).mean()),
        'out_of_fold':rows,'seconds':time.monotonic()-started}


def main():
    import numpy as np
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dataset',type=Path);p.add_argument('--table',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=4);a=p.parse_args()
    if a.out.exists() or not 1<=a.workers<=4:p.error('new output and1..4workers required')
    plan,cases,x,gains,masks,h,blocked=prepare(a.dataset,a.table);ids=[c['scenario_id'] for c in cases];started=time.monotonic()
    results={mode:{mask:{} for mask in masks} for mode in gains}
    jobs=[(mode,mask,rep,x[rep],gains[mode],masks[mask],ids,h[mode][mask],plan) for mode in gains for mask in masks for rep in x]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for future in as_completed([pool.submit(run,j) for j in jobs]):
            mode,mask,rep,row=future.result();results[mode][mask][rep]=row
            print(json.dumps({'mode':mode,'mask':mask,'representation':rep,'seconds':row['seconds']}),flush=True)
    previous=json.loads((ROOT/'reports/real-fire-data/feds-observation-offline-v1.json').read_text())
    for mode in gains:
        current=results[mode]['legacy']['legacy28'];old=previous['results'][mode]['nested_summary_rbf']
        for r,o in zip(current['out_of_fold'],old['out_of_fold']):
            if r['scenario_id']!=o['scenario_id'] or r['actions']!=o['actions'] or r['selected_config']!=o['selected_config'] or abs(r['saved_ha']-o['saved_ha'])>1e-7 or abs(r['inner_mean_saved_ha']-o['inner_mean_saved_ha'])>1e-7:
                raise ValueError('legacy RBF pipeline control differs from ADR035')
    reports={mode:{mask:{name:float(np.asarray(h[mode][mask])[:,j].mean()) for j,name in enumerate(plan['heuristics'])} for mask in masks} for mode in gains}
    files=[Path(__file__),ROOT/'src/wildfire_rl/feds_repaired_learning.py',ROOT/'src/wildfire_rl/feds_observation_audit.py',ROOT/'src/wildfire_rl/feds_observation_dataset.py']
    report={'schema_version':'feds-observation-repair-analysis/2.0','created_utc':datetime.now(timezone.utc).isoformat(),
        'label':'EXPLORATORY REUSED TRAIN; NO FINAL OR PHYSICAL VALIDATION','split':'train','validation_used':False,'test_cases_loaded':False,
        'case_count':98,'dataset_sha256':sha256_file(a.dataset),'source_table_sha256':sha256_file(a.table),'plan_sha256':sha256_file(PLAN),
        'legacy_pipeline_control':'PASS','results':results,'heuristic_mean_saved_ha':reports,'blocked_nonfuel_sequences':blocked,
        'primary':plan['primary'],'continuation_threshold':plan['continuation_threshold'],'uncertainty':plan['uncertainty'],
        'source_hashes':{str(path.relative_to(ROOT)):sha256_file(path) for path in files},'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'runtime':{'python':sys.version,'numpy':importlib.metadata.version('numpy')},'analysis_wall_minutes':(time.monotonic()-started)/60}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')

if __name__=='__main__':main()
