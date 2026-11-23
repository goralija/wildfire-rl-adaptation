#!/usr/bin/env python3
"""Independent reference/trajectory arithmetic and disposable-probe reproduction."""
import argparse
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.local/matplotlib'))
import numpy as np
import torch
import diagnose_ppo_signal as driver
from wildfire_rl.paired_learning_audit import trajectory_score
from wildfire_rl.common_control_rl import load_policy_arrays
from wildfire_rl.ppo_signal_rl import gradient_probe


def close(a,b):
    if not np.allclose(a,b,atol=1e-8,rtol=1e-7):raise ValueError('numbers differ: %s != %s'%(a,b))


def check_float32_returns(expected,actual):
    # SB3 stores GAE/returns in float32; subtracting/adding values can leave ulps
    # near a small return. Keep this tolerance local, not on cell counts/metrics.
    np.testing.assert_allclose(expected,actual,atol=1e-6,rtol=1e-6)


def compare(a,b):
    if isinstance(a,dict):
        if set(a)!=set(b):raise ValueError('keys differ')
        for k in a:compare(a[k],b[k])
    elif isinstance(a,(float,int)) and not isinstance(a,bool):close(a,b)
    elif a!=b:raise ValueError('metadata differs')


def verify(folder):
    report=driver.read(folder/'analysis.json');plan,parent,guard=driver.context()
    if report['guard']!=guard or report['plan']!=plan:raise ValueError('diagnosis guard/plan mismatch')
    if plan['fitting_cases']!=parent['plan']['fitting_cases'] or plan['evaluation_cases']!=parent['plan']['evaluation_cases']:
        raise ValueError('fitting/evaluation selection changed')
    if set(plan['fitting_cases'])&set(plan['evaluation_cases']):raise ValueError('fitting/evaluation overlap')
    counts=dict(ca_paths=0,ca_cumulative_masks=0,fitting_initial_parity=0,gradient_modes=0,old_training_rows=0,models=0)
    torch.set_num_threads(1)
    with np.load(folder/'initial-features.npz',allow_pickle=False) as a:
        features=a['features'].copy();masks=a['masks'].copy()
    for i,sid in enumerate(plan['fitting_cases']):
        record=driver.read(folder/'ca'/(sid+'.json'));path=folder/'ca'/(sid+'.npz')
        if record['guard']!=guard or driver.old.sha(path)!=record['npz_sha256']:raise ValueError('CA case changed')
        env=driver.old.make_env(driver.PARENT,'ca',sid);ob,_=env.reset()
        np.testing.assert_array_equal(ob,features[i]);np.testing.assert_array_equal(env.action_masks(),masks[i]);env.close()
        counts['fitting_initial_parity']+=1
        oldrec,oldpath=driver.old.table('simfire',sid)
        with np.load(path,allow_pickle=False) as a,np.load(oldpath,allow_pickle=False) as sf:
            np.testing.assert_array_equal(a['mask'],masks[i])
            with np.load(driver.PARENT/'references'/('ca-'+sid+'.npz'),allow_pickle=False) as ref:
                np.testing.assert_array_equal(a['burned'][0],ref['burned']);noop=ref['burned'][-1].copy()
            for k,row in enumerate(record['rows']):
                action=k if masks[i,k] else 0
                if row['requested_action']!=k or row['effective_action']!=action:raise ValueError('reference legality differs')
                charge=[int(((b|(l&noop))&~a['initial']).sum()) for b,l in zip(a['burned'][k],a['line'][k])]
                rewards=-np.diff(charge)/100.
                score=trajectory_score(a['initial'],a['burned'][k],a['line'][k],noop,rewards)
                for name,value in score.items():
                    if row[name]!=value:raise ValueError('independent CA union score differs')
                close(sum(rewards),row['native_return'])
                idx=next(j for j,r in enumerate(oldrec['outcomes']) if r['effective_actions']==[action,0,0,0])
                np.testing.assert_array_equal(a['line'][k,-1],sf['line_cells'][idx])
                counts['ca_paths']+=1;counts['ca_cumulative_masks']+=5
    ids=plan['fitting_cases']+plan['evaluation_cases'];cost={};noop={}
    for be in ('simfire','ca'):
        rows=report['references']['case_scores'][be]
        cost[be]=np.array([[r['charged_damage_cells'] for r in rows[sid]] for sid in ids],float)
        noop[be]=cost[be][:,0]
        for i,sid in enumerate(ids):
            if be=='ca' and i<45:continue
            rec,path=driver.old.table(be,sid)
            with np.load(path,allow_pickle=False) as a:
                n=int((a['noop']&~a['initial']).sum())
                for action,row in enumerate(rows[sid]):
                    eff=action if masks[i,action] else 0
                    idx=next(j for j,r in enumerate(rec['outcomes']) if r['effective_actions']==[eff,0,0,0])
                    d=int(((a['agent_burned'][idx]|(a['line_cells'][idx]&a['noop']))&~a['initial']).sum())
                    if row['charged_damage_cells']!=d or row['noop_damage_cells']!=n:raise ValueError('reused score differs')
    joint=(noop['simfire']>0)&(noop['ca']>0)
    for be in ('simfire','ca'):
        chosen=min(range(9),key=lambda k:sum(cost[be][:45,k]))
        for name,sl in [('fitting',slice(0,45)),('evaluation',slice(45,None))]:
            target=report['references']['backends'][be][name];c=cost[be][sl];n=noop[be][sl];m=masks[sl];j=joint[sl]
            if target['fitting_selected_sector']!=chosen:raise ValueError('sector not selected only on fitting')
            uniform=np.array([sum(row[a] for a in range(1,9) if mask[a])/sum(mask[1:])
                              if mask[1:].any() else row[0] for row,mask in zip(c,m)])
            for values,metric in [(uniform,target['uniform_initial_line'])]+[(c[:,a],target['sectors'][str(a)]) for a in range(9)]:
                close(np.mean(100*(n[j]-values[j])/n[j]),metric['mean_saved_percent_joint'])
                close(100*sum(n-values)/sum(n),metric['pooled_saved_percent_all'])
                close(3.24*np.mean(n-values),metric['mean_saved_ha_all'])
                close(3.24*np.mean(values),metric['mean_charged_ha_all'])
            for centered,key in [(False,'cost_scale'),(True,'centered_cost_scale')]:
                matrix=(c-n[:,None] if centered else c)/100.
                means=[row[mask].mean() for row,mask in zip(matrix,m)]
                within=np.mean([row[mask].var() for row,mask in zip(matrix,m)]);between=np.var(means)
                close(within,target[key]['within_case_variance']);close(between,target[key]['between_case_variance'])
    for p in report['probes']:
        be,seed=p['backend'],p['seed'];path=folder/('probe-%s-%d.npz'%(be,seed))
        if driver.old.sha(path)!=p['arrays_sha256']:raise ValueError('probe arrays changed')
        original=driver.read(driver.PARENT/('job-%s-%d'%(be,seed))/'training.json')[:16]
        if p['rows']!=original:raise ValueError('original training rows differ')
        counts['old_training_rows']+=16
        with np.load(path,allow_pickle=False) as a:data={k:a[k].copy() for k in a.files}
        original_returns=np.array([sum(data['rewards'][i:(i//4+1)*4]) for i in range(16)])
        shifted=data['rewards']+data['noop_increments']/100.
        shifted_returns=np.array([sum(shifted[i:(i//4+1)*4]) for i in range(16)])
        check_float32_returns(shifted_returns,data['centered_returns']);check_float32_returns(original_returns,data['returns'])
        for mode in p['modes']:
            model=load_policy_arrays(driver.PARENT/('job-%s-%d'%(be,seed))/'policy-0.npz',
                driver.old.contract(parent['guard'],be,seed,0,parent['plan']))
            batch=dict(data)
            if mode['reward']=='centered':batch.update(returns=data['centered_returns'],advantages=data['centered_advantages'])
            actual=gradient_probe(model,batch,mode['clipping']);expected={k:v for k,v in mode.items() if k!='reward'}
            compare(actual,expected);counts['gradient_modes']+=1
    for row in report['policy_diagnostics']:
        be,seed,stage=row['backend'],row['seed'],row['checkpoint'];job=driver.PARENT/('job-%s-%d'%(be,seed))
        with np.load(job/'policy-0.npz',allow_pickle=False) as a,np.load(job/('policy-%d.npz'%stage),allow_pickle=False) as b:
            for group,keys in [('actor',[k for k in a.files if k.startswith(('mlp_extractor.policy_net.','action_net.'))]),
                               ('critic',[k for k in a.files if k.startswith(('mlp_extractor.value_net.','value_net.'))])]:
                change=np.sqrt(sum(np.square(b[k].astype(float)-a[k].astype(float)).sum() for k in keys))
                base=np.sqrt(sum(np.square(a[k].astype(float)).sum() for k in keys))
                close(change,row['parameter_delta'][group]['delta_l2']);close(change/base,row['parameter_delta'][group]['relative_l2'])
        counts['models']+=1
    return dict(status='PASS',counts=counts,analysis_sha256=driver.old.sha(folder/'analysis.json'),
                scope='Independent full CA trajectories/geometry, fit-only reference selection, complete first-rollout rows,24disposable gradient reproductions and18parameter-delta checks')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=verify(a.folder);a.out.write_text(json.dumps(r,indent=2)+'\n');print(r)
