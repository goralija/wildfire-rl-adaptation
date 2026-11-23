#!/usr/bin/env python3
"""Frozen TASK-044 reference, checkpoint and disposable first-gradient diagnosis."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.local/matplotlib'))
import numpy as np
import torch
import run_paired_ppo_learning as old
from smoke_common_ppo import rollout
from wildfire_rl.common_control_rl import create_model,load_policy_arrays,policy_digest
from wildfire_rl.feds_observation_dataset import load_observation_case
from wildfire_rl.paired_ppo_learning import completed_job,case_schedule,LazyTrainingCases
from wildfire_rl.paired_learning_audit import action_description
from wildfire_rl.ppo_signal_diagnosis import (uniform_line_expectation,select_fixed_sector,reference_metrics,
    episodic_returns,centered_rewards,cost_decomposition)
from wildfire_rl.ppo_signal_rl import collect_initial,gradient_probe,parameter_delta,saturation

PARENT=ROOT/'.local/paired-ppo-v1'
PLAN=ROOT/'configs/frozen/ppo-signal-diagnosis-v1.json'


def read(p):return json.loads(Path(p).read_text())


def write(p,r):old.write(Path(p),r)


def context():
    plan=read(PLAN);parent=read(PARENT/'analysis.json');g=plan['guards']
    for p,key in [(ROOT/'configs/frozen/paired-ppo-learning-v1.json','parent_plan_sha256'),
                  (ROOT/'reports/real-fire-data/paired-ppo-learning-v1.json','parent_report_sha256'),
                  (PARENT/'analysis.json','parent_analysis_sha256'),(PARENT/'preflight.json','parent_preflight_sha256')]:
        if old.sha(p)!=g[key]:raise ValueError('parent artifact changed')
    old.assert_guard(parent['guard'])
    for run in parent['runs']:
        if not completed_job(PARENT/('job-%s-%d'%(run['backend'],run['seed'])),run['guard']):raise ValueError('incomplete parent job')
    sources={p:old.sha(ROOT/p) for p in ('scripts/diagnose_ppo_signal.py','src/wildfire_rl/ppo_signal_diagnosis.py','src/wildfire_rl/ppo_signal_rl.py')}
    libraries={}
    for module in ('sb3_contrib.ppo_mask.ppo_mask','sb3_contrib.common.maskable.policies','torch.optim.adam'):
        p=Path(importlib.util.find_spec(module).origin);libraries[module]=dict(path=str(p),sha256=old.sha(p))
    guard=dict(plan_sha256=old.sha(PLAN),source_sha256=sources,parent_guard=parent['guard'],library_source=libraries)
    return plan,parent,guard


def check_sources(guard):
    if old.sha(PLAN)!=guard['plan_sha256']:raise ValueError('plan changed')
    for p,h in guard['source_sha256'].items():
        if old.sha(ROOT/p)!=h:raise ValueError('diagnostic source changed')


def setup_worker():
    old.setup_worker()


def ca_case(task):
    folder,sid,guard=task;out=Path(folder);check_sources(guard)
    target=out/'ca'/(sid+'.json')
    if target.exists():
        r=read(target)
        if r['guard']!=guard or old.sha(target.with_suffix('.npz'))!=r['npz_sha256']:raise ValueError('CA resume mismatch')
        return r
    started=time.monotonic();env=old.make_env(PARENT,'ca',sid);first,_=env.reset();mask=env.action_masks().copy()
    burned=[];lines=[];rows=[]
    with np.load(PARENT/'references'/('ca-'+sid+'.npz'),allow_pickle=False) as a:
        expected=a['burned'].copy();initial=a['initial'].copy()
    for action in range(9):
        effective=action if mask[action] else 0
        actual,arrays=rollout(env,sequence=[effective,0,0,0])
        np.testing.assert_array_equal(arrays['initial'],initial)
        if action==0:np.testing.assert_array_equal(arrays['burned'],expected)
        rows.append(dict(requested_action=action,effective_action=effective,
                         native_return=actual['return_'],**actual['score']))
        burned.append(arrays['burned']);lines.append(arrays['line'])
    env.close()
    np.savez_compressed(target.with_suffix('.npz'),initial=initial,burned=np.stack(burned),line=np.stack(lines),mask=mask)
    result=dict(scenario_id=sid,guard=guard,rows=rows,npz_sha256=old.sha(target.with_suffix('.npz')),
                seconds=time.monotonic()-started,status='PASS',nice=os.getpriority(os.PRIO_PROCESS,0))
    write(target,result);return result


def reference_rows(sid,be,mask,ca):
    if be=='ca':return ca[sid]['rows']
    rows=[]
    for a in range(9):
        effective=a if mask[a] else 0
        rows.append(dict(requested_action=a,effective_action=effective,**old.lookup('simfire',sid,[effective,0,0,0])))
    return rows


def references(plan,features,masks,ca):
    ids=plan['fitting_cases']+plan['evaluation_cases'];allrows={};costs={};raw={};noop={}
    for be in ('simfire','ca'):
        allrows[be]={sid:reference_rows(sid,be,masks[i],ca) if sid in ca or be=='simfire'
                     else [dict(requested_action=a,effective_action=a if masks[i,a] else 0,
                          **old.lookup('ca',sid,[a if masks[i,a] else 0,0,0,0])) for a in range(9)] for i,sid in enumerate(ids)}
        costs[be]=np.array([[r['charged_damage_cells'] for r in allrows[be][sid]] for sid in ids],float)
        raw[be]=np.array([[r['raw_damage_cells'] for r in allrows[be][sid]] for sid in ids],float)
        noop[be]=costs[be][:,0]
    result={};joint=(noop['simfire']>0)&(noop['ca']>0)
    for be in ('simfire','ca'):
        selected=select_fixed_sector(costs[be][:45]);byset={}
        for name,sl in [('fitting',slice(0,45)),('evaluation',slice(45,None))]:
            n=noop[be][sl];c=costs[be][sl];m=masks[sl];j=joint[sl]
            sector=[reference_metrics(n,c[:,a],j) for a in range(9)]
            uniform=np.array([uniform_line_expectation(row,mask) for row,mask in zip(c,m)])
            byset[name]=dict(ids=ids[sl],joint_positive_cases=int(j.sum()),
                sectors={str(a):sector[a] for a in range(9)},
                uniform_initial_line=reference_metrics(n,uniform,j),
                fitting_selected_sector=selected,selected_fixed_reference=sector[selected],
                cost_scale=cost_decomposition(c/100.,m),
                centered_cost_scale=cost_decomposition((c-n[:,None])/100.,m))
        result[be]=byset
    return dict(backends=result,case_scores=allrows,definition='Exact first-line uniform expectation; fixed sector selected only by charged fitting45, never evaluation16')


def probe(task):
    folder,be,seed,plan,parent,guard=task;out=Path(folder);check_sources(guard)
    schedule=case_schedule(plan['fitting_cases'],seed)
    env=LazyTrainingCases(schedule,lambda sid:old.make_env(PARENT,be,sid))
    model=create_model(env,seed=seed,settings=parent['plan']['ppo'])
    run=next(r for r in parent['runs'] if r['backend']==be and r['seed']==seed)
    if policy_digest(model)!=run['initial_policy_digest']:raise ValueError('initial probe weights differ')
    data,rows=collect_initial(model);env.close()
    original=read(PARENT/('job-%s-%d'%(be,seed))/'training.json')[:16]
    if rows!=original:raise ValueError('first16 native replay differs from original training')
    if not np.allclose(episodic_returns(data['rewards']),data['returns'],atol=1e-4,rtol=1e-6):
        raise ValueError('GAE gamma=lambda1 complete returns differ')
    increments=[]
    for i,row in enumerate(rows):
        with np.load(PARENT/'references'/(be+'-'+row['scenario_id']+'.npz'),allow_pickle=False) as a:
            k=i%4;increments.append(int((a['burned'][k+1]&~a['burned'][k]).sum()))
    shifted=centered_rewards(data['rewards'],increments);ret=episodic_returns(shifted)
    shifts=np.array(increments).reshape(4,4).sum(axis=1)/100.
    np.testing.assert_allclose(ret[::4]-episodic_returns(data['rewards'])[::4],shifts,atol=1e-10)
    data['noop_increments']=np.array(increments);data['centered_rewards']=shifted
    data['centered_returns']=ret.astype(np.float32);data['centered_advantages']=(ret-data['values']).astype(np.float32)
    checkpoint=PARENT/('job-%s-%d'%(be,seed))/'policy-0.npz';modes=[]
    for reward in ('original','centered'):
        batch=dict(data)
        if reward=='centered':batch.update(returns=data['centered_returns'],advantages=data['centered_advantages'])
        for clipping in ('global','separate'):
            disposable=load_policy_arrays(checkpoint,old.contract(parent['guard'],be,seed,0,parent['plan']))
            metrics=gradient_probe(disposable,batch,clipping);modes.append(dict(reward=reward,**metrics))
    target=out/('probe-%s-%d'%(be,seed));np.savez_compressed(target.with_suffix('.npz'),**data)
    result=dict(backend=be,seed=seed,status='PASS',guard=guard,rows=rows,
        replay_first16='PASS',initial_weights='PASS',no_collect_optimizer_update=True,
        reward_summary={name:dict(return_std=float(np.std(values)),max_abs_return=float(np.max(np.abs(values))))
                        for name,values in [('original',data['returns']),('centered',data['centered_returns'])]},
        modes=modes,arrays_sha256=old.sha(target.with_suffix('.npz')),weights_saved=False)
    write(target.with_suffix('.json'),result);return result


def policy_diagnostics(plan,parent,features,masks):
    result=[]
    for run in sorted(parent['runs'],key=lambda r:(r['backend'],r['seed'])):
        be,seed=run['backend'],run['seed'];initial=None;initial_p=None
        for stage in (0,512,2048):
            checkpoint=PARENT/('job-%s-%d'%(be,seed))/('policy-%d.npz'%stage)
            model=load_policy_arrays(checkpoint,old.contract(parent['guard'],be,seed,stage,parent['plan']))
            if stage==0:initial={k:v.detach().clone() for k,v in model.policy.state_dict().items()}
            tensor,_=model.policy.obs_to_tensor(features)
            with torch.no_grad():
                p=model.policy.get_distribution(tensor,action_masks=masks).distribution.probs.cpu().numpy()
                value=model.policy.predict_values(tensor).cpu().numpy().reshape(-1)
            if stage==0:initial_p=p.astype(float)/p.sum(axis=1,keepdims=True)
            q=p.astype(float)/p.sum(axis=1,keepdims=True)
            kl=(initial_p*(np.log(np.maximum(initial_p,1e-38))-np.log(np.maximum(q,1e-38)))).sum(1)
            sections={}
            for name,sl in [('fitting',slice(0,45)),('evaluation',slice(45,None))]:
                sections[name]=dict(**action_description(p[sl],masks[sl],p[sl].argmax(1)),
                    mean_kl_from_initial=float(kl[sl].mean()),actor_tanh=saturation(model,features[sl]),
                    value_prediction_min=float(value[sl].min()),value_prediction_max=float(value[sl].max()))
            result.append(dict(backend=be,seed=seed,checkpoint=stage,parameter_delta=parameter_delta(initial,model),sets=sections))
    return result


def execute(out):
    plan,parent,guard=context();out.mkdir(exist_ok=False,parents=True);(out/'ca').mkdir()
    write(out/'guard.json',guard);started=time.monotonic();ids=plan['fitting_cases']+plan['evaluation_cases']
    dataset=read(old.OBS/'dataset-98.json');items={r['scenario_id']:r for r in dataset['cases']};features=[];masks=[]
    from wildfire_rl.common_control import encoded_observation
    for sid in ids:
        _,observations,mask=load_observation_case(old.OBS,items[sid],dataset['settings'])
        features.append(encoded_observation(observations[0]));masks.append(mask['burnable_lines'][0])
    features=np.stack(features);masks=np.stack(masks)
    np.savez_compressed(out/'initial-features.npz',features=features,masks=masks)
    write(out/'status.json',dict(phase='CA fitting references',cases=45,pid=os.getpid()))
    with ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('spawn'),initializer=setup_worker) as pool:
        ca=list(pool.map(ca_case,[(str(out),sid,guard) for sid in plan['fitting_cases']]))
        write(out/'status.json',dict(phase='native rollout/gradient probes',pid=os.getpid()))
        probes=list(pool.map(probe,[(str(out),be,seed,plan,parent,guard) for be in ('simfire','ca') for seed in plan['model_seeds']]))
    ca={r['scenario_id']:r for r in ca}
    refs=references(plan,features,masks,ca);policies=policy_diagnostics(plan,parent,features,masks)
    check_sources(guard)
    result=dict(schema_version='ppo-signal-diagnosis-result/1.0',status='PASS',guard=guard,plan=plan,
        references=refs,probes=probes,policy_diagnostics=policies,
        initial_features=dict(min=float(features.min()),max=float(features.max()),
            fitting_constant_dimensions=int((features[:45].std(axis=0)==0).sum()),dimensions=536),
        ca_native_paths=405,sf_fitting_paths_reused=405,probe_native_steps=96,
        seconds=time.monotonic()-started,nice=os.getpriority(os.PRIO_PROCESS,0),
        scope='Diagnostic only; disposable one-step weights never performance-evaluated; prior learning criteria unchanged')
    write(out/'analysis.json',result);write(out/'status.json',dict(phase='complete',pid=os.getpid()))
    print('DIAGNOSIS PASS',result['seconds'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if os.getpriority(os.PRIO_PROCESS,0)<19:raise RuntimeError('nice19 required')
    execute(a.out.resolve())
