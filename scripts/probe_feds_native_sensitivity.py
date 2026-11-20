#!/usr/bin/env python3
"""Small registered TRAIN sensitivity probe; never changes locked results (ADR-035)."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from dataclasses import replace
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from analyze_feds_b1 import load_table
from wildfire_rl.feds_simfire_setup import sha256_file,SimFireParams
PLAN=ROOT/'configs/frozen/feds-observation-audit-v1.json'


def probe(job):
    import numpy as np
    from wildfire_rl.feds_simfire_env import FedsSimFireEnv,line_points_for
    from wildfire_rl.feds_heuristics import make_heuristic
    case,variant,policy_name,params,weather,input_root,out=job
    started=time.monotonic();params=SimFireParams(**params)
    if variant.startswith('max'):params=replace(params,spread_aggregation='max')
    if variant=='one_minute':params=replace(params,internal_update_minutes=1)
    env=FedsSimFireEnv(sim_params=params,split='train',budgets=(1,),max_budget=4,
        scenario_ids=[case['scenario_id']],line_placement='front_edge',weather_observation='previous',
        weather_path=Path(weather),input_root=Path(input_root))
    obs,_=env.reset(seed=0,options={'scenario_id':case['scenario_id'],'budget':1})
    if 'reverse' in variant:
        manager=env.simulation.fire_manager
        manager.sprites=list(reversed(manager.sprites));manager.durations=list(reversed(manager.durations))
        env.simulation.fire_sprites=manager.sprites
    initial=env.cumulative_burned.copy();lines=np.zeros_like(initial)
    policy=make_heuristic(policy_name,seed=0);actions=[]
    for k in range(4):
        action=int(policy(obs,env.action_masks()))
        if not env.action_masks()[action]:raise ValueError('illegal scripted action')
        if action:
            for x,y in line_points_for('front_edge',env.simulation.fire_map,env.simulation.fire_map==1,action-1):
                lines[y,x]=True
        obs,_,done,truncated,info=env.step(action);actions.append(action)
        if bool(done or truncated)!=(k==3):raise ValueError('wrong decision horizon')
    burned=env.cumulative_burned.copy()
    if np.any(initial & ~burned) or sum(a!=0 for a in actions)>1:raise ValueError('damage/budget invariant')
    filename=case['scenario_id']+'--'+variant+'--'+policy_name+'.npz'
    path=Path(out)/filename;np.savez_compressed(path,initial=initial,burned=burned,lines=lines)
    env.close()
    return {'scenario_id':case['scenario_id'],'variant':variant,'policy':policy_name,
        'actions':actions,'new_damage_cells':int((burned & ~initial).sum()),
        'edge_contact':bool(burned[0,:].any() or burned[-1,:].any() or burned[:,0].any() or burned[:,-1].any()),
        'mask_file':filename,'mask_sha256':sha256_file(path),'seconds':time.monotonic()-started}


def main():
    import numpy as np
    from wildfire_rl.line_damage import score_line_damage
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('table',type=Path)
    p.add_argument('--input-root',type=Path,required=True);p.add_argument('--weather',type=Path,required=True)
    p.add_argument('--local-out',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--workers',type=int,default=4);a=p.parse_args()
    if a.out.exists() or a.local_out.exists() or not 1<=a.workers<=4:p.error('new outputs and 1..4 workers required')
    plan=json.loads(PLAN.read_text());table,cases=load_table(a.table)
    if len(cases)!=98 or sha256_file(a.table)!=plan['table_sha256'] or sha256_file(a.weather)!=plan['weather_sha256']:
        p.error('changed cohort/artifacts')
    chosen=[cases[0],sorted(cases,key=lambda c:(-c['outcomes'][0]['noop_damage_cells'],c['scenario_id']))[0]]
    a.local_out.mkdir(parents=True);started=time.monotonic();rows=[]
    jobs=[(c,v,p,table['settings']['params'],str(a.weather.resolve()),str(a.input_root.resolve()),str(a.local_out.resolve()))
          for c in chosen for v in plan['native_audit']['variants'] for p in plan['native_audit']['policies']]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for future in as_completed([pool.submit(probe,j) for j in jobs]):
            row=future.result();rows.append(row);print(json.dumps({'done':len(rows),'total':len(jobs),**row}),flush=True)
    checks=[]
    for case in chosen:
        key=case['scenario_id']
        for variant in plan['native_audit']['variants']:
            pair={r['policy']:r for r in rows if r['scenario_id']==key and r['variant']==variant}
            with np.load(a.local_out/pair['noop']['mask_file'],allow_pickle=False) as n, \
                 np.load(a.local_out/pair['advancing_front']['mask_file'],allow_pickle=False) as agent:
                score=score_line_damage(n['initial'],agent['burned'],n['burned'],agent['lines'])
                checks.append({'scenario_id':key,'variant':variant,**score})
            if variant=='locked':
                with np.load(a.table.parent/(key+'.npz'),allow_pickle=False) as expected:
                    for policy in plan['native_audit']['policies']:
                        row=pair[policy];reference=case['references'][policy]
                        if row['actions']!=reference['actions'] or row['new_damage_cells']!=reference['raw_damage_cells']:
                            raise ValueError('locked reference mismatch')
                        index=next(i for i,r in enumerate(case['outcomes']) if r['effective_actions']==row['actions'])
                        with np.load(a.local_out/row['mask_file'],allow_pickle=False) as actual:
                            if not np.array_equal(actual['burned'],expected['agent_burned'][index]):raise ValueError('locked whole-mask mismatch')
    report={'schema_version':'feds-native-sensitivity/1.0','created_utc':datetime.now(timezone.utc).isoformat(),
        'label':'TWO DIAGNOSTIC TRAIN CASES; ALTERNATIVES NOT CALIBRATED; NOT POLICY OR PHYSICAL VALIDATION',
        'split':'train','validation_used':False,'test_cases_loaded':False,'selected_cases':[c['scenario_id'] for c in chosen],
        'selection_rule':plan['native_audit']['cases'],'locked_reference_check':'PASS','rows':rows,'paired_damage_scores':checks,
        'plan_sha256':sha256_file(PLAN),'table_sha256':sha256_file(a.table),'source_sha256':sha256_file(Path(__file__)),
        'source_hashes':{str(p.relative_to(ROOT)):sha256_file(p) for p in [ROOT/'src/wildfire_rl/feds_simfire_setup.py',ROOT/'src/wildfire_rl/feds_simfire_env.py',ROOT/'src/wildfire_rl/feds_heuristics.py']},
        'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'wall_minutes':(time.monotonic()-started)/60,'limits':['Two purposefully selected fires do not establish cohort-average sensitivity.',
        'Reversing only initial sprites is a finite perturbation, not a test of every possible traversal order.',
        'Alternative max/1-minute dynamics require a new gate before any policy claim; old locked results remain as recorded.']}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')

if __name__=='__main__':main()
