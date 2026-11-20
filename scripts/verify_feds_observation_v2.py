#!/usr/bin/env python3
"""Technical replay checks of recorded v2 decisions; not a new performance sample."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from analyze_feds_b1 import load_table
from wildfire_rl.feds_simfire_setup import SimFireParams,sha256_file


def replay(job):
    import numpy as np
    from wildfire_rl.feds_simfire_env import FedsSimFireEnv
    from wildfire_rl.feds_observation_v2 import SimFireObservationV2
    from wildfire_rl.feds_repaired_policies import make_repaired_heuristic
    from wildfire_rl.line_damage import score_line_damage
    c,kind,sequence,params,input_root,weather,table_dir,local_out=job;started=time.monotonic()
    base=FedsSimFireEnv(sim_params=SimFireParams(**params),split='train',budgets=(1,),max_budget=4,scenario_ids=[c['scenario_id']],
        line_placement='front_edge',weather_observation='previous',input_root=Path(input_root),weather_path=Path(weather))
    env=SimFireObservationV2(base,mask_nonfuel_lines=True)
    obs,_=env.reset(seed=0,options={'scenario_id':c['scenario_id'],'budget':1})
    initial=base.cumulative_burned.copy();lines=np.zeros_like(initial);actions=[];blocked_count=0
    policy=make_repaired_heuristic('advancing_front64')
    for k in range(4):
        requested=int(policy(obs,env.action_masks())) if kind=='fine_heuristic' else sequence[k]
        allowed=bool(env.action_masks()[requested]);points=env.candidate_points()[requested-1] if requested and allowed else ()
        before=base.remaining_budget;obs,_,done,truncated,info=env.step(requested)
        if bool(done or truncated)!=(k==3):raise ValueError('horizon invariant')
        if requested and not allowed:
            if kind!='blocked_nonfuel' or not info['v2_blocked_nonfuel'] or base.remaining_budget!=before:raise ValueError('blocked budget mismatch')
            blocked_count+=1
        for x,y in points:lines[y,x]=True
        actions.append(requested if allowed else 0)
    if sum(a!=0 for a in actions)>1 or np.any(initial & ~base.cumulative_burned):raise ValueError('budget/damage invariant')
    if kind=='blocked_nonfuel' and blocked_count!=1:raise ValueError('masked action not exercised')
    matches=[(i,r) for i,r in enumerate(c['outcomes']) if r['effective_actions']==actions]
    if not matches:raise ValueError('missing original outcome')
    with np.load(Path(table_dir)/(c['scenario_id']+'.npz'),allow_pickle=False) as expected:
        if not np.array_equal(base.cumulative_burned,expected['agent_burned'][matches[0][0]]):raise ValueError('native whole-mask mismatch')
        score=score_line_damage(initial,base.cumulative_burned,expected['noop'],lines)
        if any(score[key]!=matches[0][1][key] for key in score):raise ValueError('native score mismatch')
    if kind!='blocked_nonfuel' and actions!=sequence:raise ValueError('live heuristic differs from recorded decisions')
    file=c['scenario_id']+'--'+kind+'.npz';path=Path(local_out)/file
    np.savez_compressed(path,initial=initial,burned=base.cumulative_burned,lines=lines)
    env.close()
    return {'scenario_id':c['scenario_id'],'kind':kind,'actions':actions,'score':score,'blocked_actions':blocked_count,
            'whole_mask_and_score_check':'PASS','mask_file':file,'mask_sha256':sha256_file(path),'seconds':time.monotonic()-started}


def main():
    p=argparse.ArgumentParser();p.add_argument('--table',type=Path,required=True);p.add_argument('--analysis',type=Path,required=True)
    p.add_argument('--heuristics',type=Path,required=True);p.add_argument('--weather',type=Path,required=True);p.add_argument('--input-root',type=Path,required=True)
    p.add_argument('--local-out',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=4);a=p.parse_args()
    if a.out.exists() or a.local_out.exists() or not 1<=a.workers<=4:p.error('new outputs and1..4workers required')
    table,cases=load_table(a.table);analysis=json.loads(a.analysis.read_text());h=json.loads(a.heuristics.read_text())
    if analysis['source_table_sha256']!=sha256_file(a.table) or h['analysis_sha256']!=sha256_file(a.analysis):p.error('changed artifacts')
    rows=analysis['results']['charged']['burnable_lines']['terrain536']['out_of_fold'];by_id={c['scenario_id']:c for c in cases};by_row={r['scenario_id']:r for r in rows}
    high=max(rows,key=lambda r:r['saved_ha']-r['reference_saved_ha'])['scenario_id']
    low=min(rows,key=lambda r:r['saved_ha']-r['reference_saved_ha'])['scenario_id']
    selected=list(dict.fromkeys([cases[0]['scenario_id'],high,low]));fine={r['scenario_id']:r for r in h['results']['charged']['burnable_lines']['advancing_front64']['per_fire']}
    jobs=[];a.local_out.mkdir(parents=True)
    common=(table['settings']['params'],str(a.input_root.resolve()),str(a.weather.resolve()),str(a.table.parent.resolve()),str(a.local_out.resolve()))
    for key in selected:
        jobs.append((by_id[key],'primary_sequence',by_row[key]['actions'],*common));jobs.append((by_id[key],'fine_heuristic',fine[key]['actions'],*common))
    blocked=analysis['blocked_nonfuel_sequences'][0];sequence=[0]*4;sequence[blocked['decision']]=blocked['action']
    jobs.append((by_id[blocked['scenario_id']],'blocked_nonfuel',sequence,*common))
    started=time.monotonic();results=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for future in as_completed([pool.submit(replay,j) for j in jobs]):
            row=future.result();results.append(row);print(json.dumps({'done':len(results),'total':len(jobs),**row}),flush=True)
    report={'schema_version':'feds-observation-repair-native-check/2.0','created_utc':datetime.now(timezone.utc).isoformat(),
        'label':'POST-RESULT TECHNICAL REPLAY CHECK; NOT A NEW PERFORMANCE SAMPLE','split':'train','validation_used':False,'test_cases_loaded':False,
        'selection':'First ID plus primary largest positive/negative charged differences; one blocked action. These are verification paths, not extra evaluation evidence.',
        'source_table_sha256':sha256_file(a.table),'analysis_sha256':sha256_file(a.analysis),'source_sha256':sha256_file(Path(__file__)),
        'results':results,'all_checks':'PASS','wall_minutes':(time.monotonic()-started)/60}
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')

if __name__=='__main__':main()
