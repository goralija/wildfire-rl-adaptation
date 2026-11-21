#!/usr/bin/env python3
"""ADR-043 common-control comparison. TRAIN only, no PPO checkpoint loading."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[key]='1'
import numpy as np
import gymnasium
import scipy
from wildfire_rl.paired_simulators import CABridgeEnv,summarize_pair,fraction
from wildfire_rl.feds_observation_v2 import SimFireObservationV2
from wildfire_rl.feds_simfire_setup import (load_case_inputs,record_forcing,observed_weather_records,
    SimFireParams,WEATHER,INPUT_ROOT)
from wildfire_rl.synthetic_real_cases import weather_from_segments,episode_start_utc,crop_centre_lonlat
from wildfire_rl.feds_repaired_learning import repaired_features
from wildfire_rl.feds_repaired_policies import make_repaired_heuristic
from wildfire_rl.feds_b1 import action_sequences,policy_sequence
from wildfire_rl.feds_observation_audit import nested_actions,fit_models,predict_sequence
from wildfire_rl.feds_b1_learning import _with_noop_lower_bound
from wildfire_rl.feds_observation_dataset import load_observation_case
from wildfire_rl.line_damage import score_line_damage
from wildfire_rl.feds_simfire_env import line_length_m
from analyze_feds_b1 import load_table

SOURCES=['scripts/run_paired_simulators.py','src/wildfire_rl/paired_simulators.py',
 'src/wildfire_rl/synthetic_ca.py','src/wildfire_rl/synthetic_real_cases.py',
 'src/wildfire_rl/feds_simfire_env.py','src/wildfire_rl/feds_simfire_setup.py',
 'src/wildfire_rl/feds_observation_v2.py','src/wildfire_rl/feds_observation_audit.py',
 'src/wildfire_rl/feds_repaired_learning.py','src/wildfire_rl/line_damage.py']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,data):
    path=Path(path);temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,indent=1,allow_nan=False)+'\n');temp.replace(path)


def lower_priority():
    if os.getpriority(os.PRIO_PROCESS,0)<19:os.setpriority(os.PRIO_PROCESS,0,19)
    if os.getpriority(os.PRIO_PROCESS,0)<19:raise RuntimeError('nice19 required')


def seed_for(sid,rep):return int.from_bytes(hashlib.sha256(('TASK040:'+sid+':'+str(rep)).encode()).digest()[:8],'big')%(2**31)


def bridge(inputs,rep):
    lon,_=crop_centre_lonlat(inputs['receipt']['grid'],0,0,size=256)
    hours=weather_from_segments(inputs['weather']['segments'],episode_start_utc(inputs['weather']),
                                lon,decisions=48,wind_adjustment=.1).steps
    params=SimFireParams(wind_adjustment_factor=.1)
    observed=[record_forcing(r,params) for r in observed_weather_records(inputs['weather'],'previous')]
    # Confirm the physical wind/moisture agree with the frozen SimFire forcing.
    for k in range(4):
        expected=record_forcing(inputs['weather']['segments'][k],params)
        actual=hours[k*12]
        if not np.isclose(actual.wind_midflame_m_s*196.8503937007874,expected['wind_speed_midflame_ft_per_min_proxy']):
            raise ValueError('forcing speed mismatch')
        if not np.isclose(actual.wind_to_deg,expected['wind_direction_degrees_clockwise_north_to']):
            raise ValueError('forcing direction mismatch')
        if not np.isclose(actual.moisture,expected['fuel_moisture_fraction_proxy']):raise ValueError('moisture mismatch')
    return SimFireObservationV2(CABridgeEnv(inputs,hours,observed,seed=seed_for(inputs['scenario_id'],rep)))


def rollout(env,sequence=None,policy=None,capture=False):
    obs,_=env.reset();base=env.env;initial=base.cumulative_burned.copy()
    observations=[];masks=[];actions=[];length=0.
    for k in range(4):
        mask=env.action_masks()
        if not mask[0]:raise AssertionError('no-op missing')
        if capture:observations.append(obs);masks.append(mask.copy())
        requested=int(sequence[k] if sequence is not None else policy(obs,mask,k))
        action=requested if mask[requested] else 0
        previous=base.cumulative_burned.copy()
        obs,_,done,trunc,info=env.step(action)
        if not env.observation_space.contains(obs) or (previous&~base.cumulative_burned).any():
            raise AssertionError('observation/cumulative damage failure')
        if trunc or done!=(k==3) or info['invalid_action']:raise AssertionError('horizon/legality failure')
        if base.remaining_budget<0:raise AssertionError('negative budget')
        length+=info['line_length_m'];actions.append(action)
    if sum(a!=0 for a in actions)>1 or length>max(line_length_m(k) for k in range(8))+1e-4:
        raise AssertionError('common line capacity exceeded')
    return {'initial':initial,'burned':base.cumulative_burned.copy(),'line':base.fire.line.copy(),
            'actions':actions,'line_length_m':length,'observations':observations,'masks':masks,
            'edge_contact':bool(base.cumulative_burned[0].any() or base.cumulative_burned[-1].any()
                                or base.cumulative_burned[:,0].any() or base.cumulative_burned[:,-1].any())}


def case_job(task):
    sid,plan,guard,folder,sf_case,sf_obs,sf_masks=task
    path=Path(folder)/(sid+'.json')
    if path.exists():
        record=json.loads(path.read_text())
        if record['guard']!=guard or record['npz_sha256']!=sha(path.with_suffix('.npz')):
            raise ValueError('resume source/plan/arrays mismatch')
        return record
    started=time.monotonic()
    inputs=load_case_inputs(sid,split='train',weather_path=WEATHER,input_root=INPUT_ROOT)
    if inputs['receipt_sha256']!=sf_case['input_receipt_sha256']:raise ValueError('input receipt changed')
    env=bridge(inputs,0);noop=rollout(env,sequence=[0]*4,capture=True)
    expected_initial=np.asarray(inputs['scar'],bool)|np.asarray(inputs['front'],bool)
    np.testing.assert_array_equal(noop['initial'],expected_initial)
    for key in sf_obs[0]:np.testing.assert_array_equal(noop['observations'][0][key],sf_obs[0][key])
    np.testing.assert_array_equal(noop['masks'][0],sf_masks[0])
    outcomes=[];burned=[];lines=[]
    for sequence in action_sequences():
        result=noop if not any(sequence) else rollout(env,sequence=sequence)
        score=score_line_damage(noop['initial'],result['burned'],noop['burned'],result['line'])
        outcomes.append({'requested_actions':list(sequence),'effective_actions':result['actions'],
                         'line_length_m':result['line_length_m'],'edge_contact':result['edge_contact'],**score})
        burned.append(result['burned']);lines.append(result['line'])
    repeated=rollout(env,sequence=[0]*4)
    np.testing.assert_array_equal(noop['burned'],repeated['burned'])
    arrays={key:np.stack([o[key] for o in noop['observations']]) for key in noop['observations'][0]}
    arrays.update(masks=np.array(noop['masks']),initial=noop['initial'],noop=noop['burned'],
                  agent_burned=np.stack(burned),line_cells=np.stack(lines))
    np.savez_compressed(path.with_suffix('.npz'),**arrays)
    record={'scenario_id':sid,'guard':guard,'input_receipt_sha256':inputs['receipt_sha256'],
            'outcomes':outcomes,'npz_sha256':sha(path.with_suffix('.npz')),
            'initial_observation_and_mask_match':'PASS','noop_replay':'PASS',
            'native_urban_cells_harmonized':int((inputs['fuel']==91).sum()),
            'seconds':time.monotonic()-started,'nice':os.getpriority(os.PRIO_PROCESS,0)}
    write(path,record);env.close();return record


def selected_sf(table,observations,plan):
    if sha(table)!=plan['table_sha256'] or sha(WEATHER)!=plan['weather_sha256']:
        raise ValueError('original table/weather mismatch')
    if sha(observations)!=plan['observation_dataset_sha256']:raise ValueError('original v2 dataset changed')
    _,cases=load_table(table);byid={c['scenario_id']:c for c in cases}
    dataset=json.loads(observations.read_text());items={c['scenario_id']:c for c in dataset['cases']}
    result={}
    for sid in plan['cases']:
        _,obs,masks=load_observation_case(observations.parent,items[sid],dataset['settings'])
        result[sid]=(byid[sid],obs,masks['burnable_lines'])
    return result


def gains_from(rows):
    result=np.zeros((4,9))
    for r in rows:
        for k,a in enumerate(r['requested_actions']):
            if a:result[k,a]=r['charged_saved_cells']*3.24
    return result


def outcome(rows,actions):
    matches=[r for r in rows if r['effective_actions']==list(actions)]
    if not matches:raise ValueError('missing matching outcome')
    values={r['charged_damage_cells'] for r in matches}
    if len(values)!=1:raise ValueError('ambiguous matching damage')
    return matches[0]


def compact(sid,row,actions):
    return {'scenario_id':sid,'noop':row['noop_damage_cells'],'damage':row['charged_damage_cells'],
            'raw_damage':row['raw_damage_cells'],'actions':list(actions),'edge_contact':row.get('edge_contact')}


def robust_job(task):
    sid,rep,plan,guard,models,folder=task
    path=Path(folder)/('%s-rep%d.json'%(sid,rep))
    if path.exists():
        old=json.loads(path.read_text())
        if old['guard']!=guard:raise ValueError('robustness resume mismatch')
        return old
    inputs=load_case_inputs(sid,split='train',weather_path=WEATHER,input_root=INPUT_ROOT)
    env=bridge(inputs,rep);noop=rollout(env,sequence=[0]*4);rows={}
    for name in plan['heuristics']+['matched_rbf']:
        if name=='noop':r=noop
        elif name=='matched_rbf':
            def policy(obs,mask,k):
                q=_with_noop_lower_bound(models[k].predict(repaired_features(obs,'terrain536')))[0]
                return int(np.argmax(np.where(mask,q,-np.inf)))
            r=rollout(env,policy=policy)
        else:
            rule=make_repaired_heuristic(name);r=rollout(env,policy=lambda o,m,k:rule(o,m))
        score=score_line_damage(noop['initial'],r['burned'],noop['burned'],r['line'])
        rows[name]=compact(sid,{**score,'edge_contact':r['edge_contact']},r['actions'])
    result={'scenario_id':sid,'replicate':rep,'guard':guard,'results':rows,'nice':os.getpriority(os.PRIO_PROCESS,0)}
    write(path,result);env.close();return result


def analyze(out,plan,guard,sf,records):
    ids=plan['cases'];methods=plan['heuristics']+['matched_rbf','oracle']
    results={'sf':{m:[] for m in methods},'ca':{m:[] for m in methods}}
    bundles={};models_ca=[];configs={'sf':[],'ca':[]};growth_masks=[]
    for backend in ('sf','ca'):
        x=[];gains=[];masks=[];obslist=[];cases=[]
        for sid in ids:
            if backend=='sf':
                case,obs,mask=sf[sid]
            else:
                case=records[sid]
                with np.load(out/'cases'/(sid+'.npz'),allow_pickle=False) as data:
                    obs=[{key:data[key][k] for key in sf[sid][1][0]} for k in range(4)]
                    mask=data['masks'].copy()
            x.append([repaired_features(o,'terrain536') for o in obs]);gains.append(gains_from(case['outcomes']))
            masks.append(mask);obslist.append(obs);cases.append(case)
        x=np.array(x);gains=np.array(gains);masks=np.array(masks,dtype=bool)
        bundles[backend]=(x,gains,masks,obslist,cases)
        for i,sid in enumerate(ids):
            for name in plan['heuristics']:
                actions=policy_sequence(make_repaired_heuristic(name),obslist[i],masks[i])
                row=outcome(cases[i]['outcomes'],actions)
                results[backend][name].append(compact(sid,row,actions))
            cfg=plan['learned'];candidates=[(a,b) for a in cfg['alpha'] for b in cfg['bandwidth']]
            fit=nested_actions(x,gains,masks,ids,i,'rbf',candidates);configs[backend].append(fit)
            row=outcome(cases[i]['outcomes'],fit['actions'])
            results[backend]['matched_rbf'].append(compact(sid,row,fit['actions']))
            fitting=np.array([j for j in range(len(ids)) if j!=i])
            if backend=='ca':models_ca.append(fit_models(x[fitting],gains[fitting],masks[fitting],'rbf',fit['selected_config']))
            best=max((r for r in cases[i]['outcomes'] if all(masks[i,k,a] for k,a in enumerate(r['requested_actions']))),key=lambda r:r['charged_saved_cells'])
            results[backend]['oracle'].append(compact(sid,best,best['effective_actions']))
    # Growth footprint diagnostics are independent of any policy choice.
    for sid in ids:
        with np.load(out/'cases'/(sid+'.npz'),allow_pickle=False) as ca,np.load(Path(plan['_table_dir'])/(sid+'.npz'),allow_pickle=False) as original:
            np.testing.assert_array_equal(ca['initial'],original['initial'])
            a=original['noop']&~original['initial'];b=ca['noop']&~ca['initial'];union=int((a|b).sum())
            growth_masks.append({'scenario_id':sid,'sf_new_cells':int(a.sum()),'ca_new_cells':int(b.sum()),
                'new_mask_iou':float((a&b).sum()/union) if union else None,
                'sf_noop_edge':bool(original['noop'][0].any() or original['noop'][-1].any() or original['noop'][:,0].any() or original['noop'][:,-1].any()),
                'ca_noop_edge':bool(ca['noop'][0].any() or ca['noop'][-1].any() or ca['noop'][:,0].any() or ca['noop'][:,-1].any())})
    summary={m:summarize_pair(results['sf'][m],results['ca'][m]) for m in methods}
    robust_dir=out/'robustness';robust_dir.mkdir(exist_ok=True)
    jobs=[(sid,rep,plan,guard,models_ca[i],str(robust_dir)) for i,sid in enumerate(ids) for rep in (1,2)]
    with ProcessPoolExecutor(3,initializer=lower_priority) as pool:robust=list(pool.map(robust_job,jobs))
    robustness={}
    for rep in (1,2):
        rows={r['scenario_id']:r for r in robust if r['replicate']==rep}
        robustness[str(rep)]={m:summarize_pair(results['sf'][m],[rows[sid]['results'][m] for sid in ids]) for m in methods if m!='oracle'}
    return {'results':results,'summary':summary,'growth_masks':growth_masks,'model_fits':configs,
            'robustness':robustness,'robustness_rows':robust}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=['collect','analyze'],required=True)
    p.add_argument('--case-limit',type=int,default=16);p.add_argument('--workers',type=int,default=3)
    p.add_argument('--table',type=Path,default=ROOT/'.local/b1-cases/table-98.json')
    p.add_argument('--observations',type=Path,default=ROOT/'.local/repair-observations/dataset-98.json')
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if not 1<=a.workers<=3 or not 1<=a.case_limit<=16:p.error('one to three workers, one to sixteen cases')
    lower_priority();plan_path=ROOT/'configs/frozen/ca-simfire-paired-v1.json';plan=json.loads(plan_path.read_text())
    sf=selected_sf(a.table,a.observations,plan)
    guard={'plan_sha256':sha(plan_path),'table_sha256':sha(a.table),'observations_sha256':sha(a.observations),
           'weather_sha256':sha(WEATHER),'source_sha256':{f:sha(ROOT/f) for f in SOURCES},
           'runtime':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'gymnasium':gymnasium.__version__}}
    a.out.mkdir(parents=True,exist_ok=True);guard_path=a.out/'guard.json'
    if guard_path.exists() and json.loads(guard_path.read_text())!=guard:raise ValueError('output guard changed')
    write(guard_path,guard);started=time.monotonic()
    if a.stage=='collect':
        folder=a.out/'cases';folder.mkdir(exist_ok=True)
        jobs=[(sid,plan,guard,str(folder),*sf[sid]) for sid in plan['cases'][:a.case_limit]]
        with ProcessPoolExecutor(a.workers,initializer=lower_priority) as pool:
            records=[]
            for r in pool.map(case_job,jobs):
                records.append(r);print('PASS %s %.2fs'%(r['scenario_id'],r['seconds']),flush=True)
        write(a.out/('collection-%d.json'%a.case_limit),{'guard':guard,'cases':records,'seconds':time.monotonic()-started})
    else:
        final=a.out/'analysis.json'
        if final.exists():raise FileExistsError('keep existing final result')
        records={}
        for sid in plan['cases']:
            path=a.out/'cases'/(sid+'.json');r=json.loads(path.read_text())
            if r['guard']!=guard or sha(path.with_suffix('.npz'))!=r['npz_sha256']:raise ValueError('case guard failed')
            records[sid]=r
        run_plan={**plan,'_table_dir':str(a.table.parent)}
        result=analyze(a.out,run_plan,guard,sf,records)
        report={'schema_version':'ca-simfire-paired-result/1.0','date':'2026-11-21','plan':plan,'guard':guard,
                'scope':'Common line-control vegetation bridge, not native PPO ranking or physical validation',
                'seconds':time.monotonic()-started,'case_count':16,'collection_case_seconds':{k:v['seconds'] for k,v in records.items()},
                'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                'checks':'PASS','validation_used':False,'test_cases_loaded':False,**result}
        write(final,report);print(json.dumps(report['summary'],indent=1),flush=True)


if __name__=='__main__':main()
