#!/usr/bin/env python3
"""Capture current v2 observations on verified frozen TRAIN no-op paths (ADR-037)."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import json
import importlib.metadata
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from analyze_feds_b1 import load_table
from wildfire_rl.feds_simfire_setup import sha256_file,SimFireParams,load_case_inputs
PLAN=ROOT/'configs/frozen/feds-observation-repair-v2.json'


def write_json(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n');tmp.replace(path)


def collect(job):
    import numpy as np
    from wildfire_rl.feds_simfire_env import FedsSimFireEnv
    from wildfire_rl.feds_observation_v2 import SimFireObservationV2
    case,settings,out,table_dir=job;key=case['scenario_id'];out=Path(out)
    path=out/(key+'.json');npz=path.with_suffix('.npz')
    if path.exists():
        old=json.loads(path.read_text())
        current=load_case_inputs(key,weather_path=Path(settings['weather_path']),input_root=Path(settings['input_root']))
        if old['settings']!=settings or sha256_file(npz)!=old['npz_sha256'] or current['receipt_sha256']!=old['input_receipt_sha256']:
            raise ValueError('changed resume source/input/masks')
        return {'scenario_id':key,'resumed':True,'seconds':old['seconds']}
    started=time.monotonic()
    base=FedsSimFireEnv(sim_params=SimFireParams(**settings['params']),split='train',budgets=(1,),max_budget=4,
        scenario_ids=[key],line_placement='front_edge',weather_observation='previous',weather_path=Path(settings['weather_path']),input_root=Path(settings['input_root']))
    env=SimFireObservationV2(base,mask_nonfuel_lines=False)
    observation,_=env.reset(seed=0,options={'scenario_id':key,'budget':1})
    observations=[];legacy_masks=[];burnable_masks=[];blocked=[]
    with np.load(Path(table_dir)/(key+'.npz'),allow_pickle=False) as expected:
        if not np.array_equal(base.cumulative_burned,expected['initial']):raise ValueError('initial damage mismatch')
        old_lines=expected['line_cells'];lookup={tuple(row['requested_actions']):i for i,row in enumerate(case['outcomes'])}
        for k in range(4):
            for name in ('grid','weather','budget','time'):
                if not np.array_equal(observation[name],np.asarray(case['observations'][k][name],dtype=np.float32)):
                    raise ValueError('legacy observation changed: '+key+' '+name)
            old_mask=env.action_masks();new_mask=env.action_masks(mask_nonfuel_lines=True)
            if not np.array_equal(old_mask,case['action_masks'][k]) or not new_mask[0] or np.any(new_mask & ~old_mask):
                raise ValueError('mask mismatch')
            for sector,points in enumerate(env.candidate_points()):
                seq=tuple(sector+1 if step==k else 0 for step in range(4));index=lookup[seq]
                native=np.zeros((256,256),dtype=bool)
                for x,y in points:native[y,x]=True
                if not np.array_equal(native,old_lines[index]):raise ValueError('candidate line geometry changed')
                cx,cy=np.rint(observation['candidate_centres'][sector]*255).astype(int)
                local=np.zeros_like(native);yy,xx=np.nonzero(observation['candidate_line_masks'][sector])
                local[yy+cy-8,xx+cx-8]=True
                if not np.array_equal(native,local):raise ValueError('patch line coordinates changed')
                if old_mask[sector+1] and not new_mask[sector+1]:
                    blocked.append({'decision':k,'action':sector+1,'raw_saved_cells':case['outcomes'][index]['raw_saved_cells'],
                                    'charged_saved_cells':case['outcomes'][index]['charged_saved_cells']})
            observations.append(observation);legacy_masks.append(old_mask);burnable_masks.append(new_mask)
            observation,_,done,truncated,_=env.step(0)
            if bool(done or truncated)!=(k==3):raise ValueError('four decision horizon changed')
        if not np.array_equal(base.cumulative_burned,expected['noop']):raise ValueError('whole no-op mask changed')
    arrays={name:np.stack([o[name] for o in observations]) for name in observations[0]}
    arrays.update(mask_legacy=np.stack(legacy_masks),mask_burnable_lines=np.stack(burnable_masks))
    np.savez_compressed(npz,**arrays)
    record={'schema_version':'feds-observation-v2-case/1.0','scenario_id':key,'split':'train','settings':settings,
        'input_receipt_sha256':base._input_cache[key]['receipt_sha256'],'npz_sha256':sha256_file(npz),
        'legacy_and_candidate_and_whole_mask_check':'PASS','blocked_nonfuel_sequences':blocked,
        'seconds':time.monotonic()-started}
    write_json(path,record);env.close()
    return {'scenario_id':key,'resumed':False,'seconds':record['seconds']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('table',type=Path)
    p.add_argument('--weather',type=Path,required=True);p.add_argument('--input-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--case-limit',type=int);p.add_argument('--workers',type=int,default=4)
    a=p.parse_args()
    if not 1<=a.workers<=4 or a.case_limit is not None and a.case_limit<1:p.error('1..4 workers and positive limit required')
    plan=json.loads(PLAN.read_text());table,cases=load_table(a.table)
    if len(cases)!=98 or sha256_file(a.table)!=plan['table_sha256'] or sha256_file(a.weather)!=plan['weather_sha256']:
        p.error('changed registered cohort/artifacts')
    if a.case_limit:cases=cases[:a.case_limit]
    paths=[Path(__file__)]+[ROOT/'src/wildfire_rl'/name for name in ('feds_observation_v2.py','feds_simfire_env.py','feds_simfire_setup.py','simfire_initial_state.py','simfire_timebase.py','gridmet_weather.py')]
    distribution=importlib.metadata.distribution('simfire')
    native={name:sha256_file(Path(distribution.locate_file('simfire/'+name))) for name in ('world/rothermel.py','game/managers/fire.py','utils/layers.py','sim/simulation.py')}
    reference=json.loads((ROOT/'reports/real-fire-data/feds-observation-verification-v1.json').read_text())['native_runtime']['engine_source_hashes']
    if native!=reference:p.error('native source differs from the verified frozen engine')
    settings={'plan_sha256':sha256_file(PLAN),'source_table_sha256':sha256_file(a.table),'weather_sha256':sha256_file(a.weather),
        'params':table['settings']['params'],'native_source_hashes':native,'numpy_version':importlib.metadata.version('numpy'),'source_hashes':{str(path.relative_to(ROOT)):sha256_file(path) for path in paths},
        'weather_path':str(a.weather.resolve()),'input_root':str(a.input_root.resolve())}
    a.out.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        jobs=[(c,settings,str(a.out),str(a.table.parent)) for c in cases]
        for done,f in enumerate(as_completed([pool.submit(collect,job) for job in jobs]),1):
            print(json.dumps({'done':done,'total':len(cases),**f.result()}),flush=True)
    record={'schema_version':'feds-observation-v2-dataset/1.0','created_utc':datetime.now(timezone.utc).isoformat(),
        'split':'train','validation_used':False,'test_cases_loaded':False,'case_count':len(cases),'settings':settings,
        'cases':[{'scenario_id':c['scenario_id'],'file':c['scenario_id']+'.json','sha256':sha256_file(a.out/(c['scenario_id']+'.json'))} for c in cases],
        'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'wall_minutes':(time.monotonic()-started)/60}
    write_json(a.out/('dataset-%d.json'%len(cases)),record)

if __name__=='__main__':main()
