#!/usr/bin/env python3
"""Independent complete post-run audit of ADR-055; no training or tuning."""
import argparse
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.local/matplotlib'))
import numpy as np
import torch
import run_centered_ppo_pilot as driver
from audit_paired_ppo_learning import close,describe
from wildfire_rl.common_control_rl import load_policy_arrays,policy_digest
from wildfire_rl.centered_pilot_audit import centered_training_ledger,centered_trajectory_score
from wildfire_rl.paired_learning_audit import trajectory_score,action_description
from wildfire_rl.paired_ppo_learning import completed_job

read=driver.read
sha=driver.sha


@lru_cache(maxsize=1024)
def endpoint(be,sid,actions):
    record,path=driver.old.table(be,sid)
    idx=next(i for i,r in enumerate(record['outcomes']) if r['effective_actions']==list(actions))
    with np.load(path,allow_pickle=False) as a:
        initial=a['initial'];noop=a['noop'];burned=a['agent_burned'][idx];line=a['line_cells'][idx]
    n=int((noop&~initial).sum());raw=int((burned&~initial).sum())
    charged=int(((burned|(line&noop))&~initial).sum())
    score=dict(noop_damage_cells=n,raw_damage_cells=raw,charged_damage_cells=charged,
        extra_line_charge_cells=charged-raw,line_cells_in_noop_footprint=int((line&noop&~initial).sum()),
        raw_saved_cells=n-raw,charged_saved_cells=n-charged)
    return score,burned,line


def independent_statistics(report,diagnosis):
    ids=report['plan']['evaluation_cases'];seeds=report['plan']['model_seeds']
    policies={(r['backend'],r['seed'],x['scenario_id'],x['checkpoint']):x for r in report['runs'] for x in r['rows']}
    originals={(r['backend'],r['seed'],x['scenario_id'],x['checkpoint']):x for r in report['runs'] for x in r['original_rows']}
    expected={(be,seed,sid,stage) for be in ('simfire','ca') for seed in seeds for sid in ids for stage in (0,512)}
    if set(policies)!=expected or set(originals)!=expected:raise ValueError('paired policy coverage differs')
    noop={be:{sid:endpoint(be,sid,(0,0,0,0))[0]['noop_damage_cells'] for sid in ids} for be in ('simfire','ca')}
    joint=[sid for sid in ids if min(noop[be][sid] for be in ('simfire','ca'))>0]
    if joint!=report['summary']['joint_positive_ids']:raise ValueError('joint denominators differ')
    bases=read(driver.PARENT/'preflight.json')['baselines'];bybase={(r['backend'],r['scenario_id'],r['method']):r for r in bases}
    changes={};front={};uniform={};verified={}
    for be in ('simfire','ca'):
        target=report['summary']['backends'][be];values={};n=noop[be]
        for name,rows,stage in [('centered512',policies,512),('original512',originals,512),('initial0',policies,0)]:
            values[name]={sid:tuple(math.fsum(rows[be,seed,sid,stage][key] for seed in seeds)/len(seeds)
                for key in ('charged_damage_cells','raw_damage_cells')) for sid in ids}
        for name in ('noop','advancing_front64','downwind','random_legal'):
            values[name]={sid:tuple(bybase[be,sid,name][key] for key in ('charged_damage_cells','raw_damage_cells')) for sid in ids}
        cases=diagnosis['references']['case_scores'][be]
        fitting=report['plan']['fitting_cases']
        # Select one sector using fitting45 ONLY; ties go to the lower integer id.
        selected=min(range(9),key=lambda a:(math.fsum(cases[sid][a]['charged_damage_cells'] for sid in fitting),a))
        if selected!=target['fitting_selected_sector']:raise ValueError('fit-only sector differs')
        values['exact_uniform']={};values['fitting_selected_fixed']={}
        for sid in ids:
            with np.load(driver.PARENT/'evaluation'/(be+'-'+sid+'.npz'),allow_pickle=False) as a:
                legal=[i for i in range(1,9) if a['masks'][0,i]] or [0]
            scores=[endpoint(be,sid,(action,0,0,0))[0] for action in legal]
            values['exact_uniform'][sid]=tuple(math.fsum(x[key] for x in scores)/len(scores)
                for key in ('charged_damage_cells','raw_damage_cells'))
            effective=cases[sid][selected]['effective_action']
            fixed=endpoint(be,sid,(effective,0,0,0))[0]
            values['fitting_selected_fixed'][sid]=(fixed['charged_damage_cells'],fixed['raw_damage_cells'])
        def check_metrics(v,t):
            positive=[sid for sid in ids if n[sid]>0]
            mean=lambda numbers:math.fsum(numbers)/len(numbers) if numbers else None
            checks=dict(mean_saved_percent_joint=mean([100*(n[s]-v[s][0])/n[s] for s in joint]),
                mean_saved_percent_own_positive=mean([100*(n[s]-v[s][0])/n[s] for s in positive]),
                pooled_saved_percent_all=100*math.fsum(n[s]-v[s][0] for s in ids)/math.fsum(n.values()),
                mean_charged_ha_all=3.24*mean([v[s][0] for s in ids]),
                mean_raw_ha_all=3.24*mean([v[s][1] for s in ids]),mean_saved_ha_all=3.24*mean([n[s]-v[s][0] for s in ids]))
            for k,x in checks.items():
                if x is None:
                    if t[k] is not None:raise ValueError('undefined percentage changed')
                else:close(x,t[k])
            if t['undefined_case_indices']!=[i for i,s in enumerate(ids) if not n[s]]:raise ValueError('zero denominator lost')
        for name,v in values.items():check_metrics(v,target['metrics'][name])
        for seed in seeds:
            v={sid:tuple(policies[be,seed,sid,512][key] for key in ('charged_damage_cells','raw_damage_cells')) for sid in ids}
            check_metrics(v,target['model_seeds'][str(seed)])
        c=values['centered512'];differences={}
        for name,v in values.items():
            if name=='centered512':continue
            d=[100*(v[s][0]-c[s][0])/n[s] for s in joint]
            describe(d,target['centered_minus_reference_pp'][name]);differences[name]=np.array(d)
        signal=all(target['centered_minus_reference_pp'][name]['ci95'][0]>0 for name in ('original512','exact_uniform'))
        if signal!=target['continuation_signal']:raise ValueError('continuation criterion differs')
        changes[be]=differences['original512'];front[be]=differences['advancing_front64'];uniform[be]=differences['exact_uniform']
        verified[be]=dict(joint_fires=len(joint),model_seeds=len(seeds),continuation_signal=signal)
    for key,values in [('ca_minus_sf_improvement_pp',changes),('ca_minus_sf_gap_to_front_pp',front),('ca_minus_sf_gap_to_uniform_pp',uniform)]:
        describe(values['ca']-values['simfire'],report['summary'][key])
    return verified


def parameter_deltas(initial,final):
    result={}
    for group,prefixes in [('actor',('mlp_extractor.policy_net.','action_net.')),('critic',('mlp_extractor.value_net.','value_net.'))]:
        keys=[k for k in initial if k.startswith(prefixes)]
        norm=lambda rows:math.sqrt(math.fsum(float(np.square(a.astype(np.float64)).sum()) for a in rows))
        delta=norm([final[k]-initial[k] for k in keys]);base=norm([initial[k] for k in keys]);count=sum(initial[k].size for k in keys)
        result[group]=dict(delta_l2=delta,delta_rms=delta/math.sqrt(count),relative_l2=delta/base,parameters=count)
    return result


def audit(folder):
    report=read(folder/'analysis.json');guard=report['guard'];plan,parent,diagnosis=driver.assert_guard(guard)
    pre=driver.checked_preflight(folder,guard)
    if report['status']!='PASS' or read(folder/'status.json')['phase']!='complete':raise ValueError('run not complete')
    if any((folder/n).exists() for n in ('coordinator.lock','stop.json','error.json')):raise ValueError('run locked/stopped/failed')
    counts=dict(completed_jobs=0,training_steps=0,training_episodes=0,centered_checkpoints=0,original_checkpoints=0,
        policy_scores=0,original_policy_scores=0,native_paths=0,cumulative_states=0,reference_states=0,preflight_paths=0,first_rollout_steps=0)
    for sid in plan['fitting_cases']+plan['evaluation_cases']:
        for be in ('simfire','ca'):
            ref=driver.trajectory(be,sid)
            if ref.shape[0]!=5 or (ref[:-1]&~ref[1:]).any():raise ValueError('reference not cumulative')
            counts['reference_states']+=5
    for item in pre['paths']:
        be,sid=item['backend'],item['scenario_id'];ref=driver.trajectory(be,sid)
        with np.load(folder/('paths-'+be+'-'+sid+'.npz'),allow_pickle=False) as a:
            for k,path in enumerate(item['paths']):
                initial,burned,line=[a['path%d_%s'%(k,key)] for key in ('initial','burned','line')]
                rows=path['centered']['rows'];rewards=[r['reward'] for r in rows];invalid=[r['invalid'] for r in rows]
                actual=centered_trajectory_score(initial,burned,line,ref,rewards,invalid)
                if actual!=path['centered']['score'] or actual!=path['raw']['score']:raise ValueError('preflight physical score differs')
                close(math.fsum(rewards),path['centered']['return_'])
                close(path['raw']['return_'],-actual['charged_damage_cells']/100.-.01*sum(invalid))
                masks=a['path%d_masks'%k]
                for j,row in enumerate(rows):
                    legal=bool(masks[j,row['requested_action']])
                    if row['invalid']==legal or not masks[j,0] or row['effective_action']!=(row['requested_action'] if legal else 0):
                        raise ValueError('preflight legality differs')
                counts['preflight_paths']+=1
    torch.set_num_threads(1);diagnostics=[];paired={}
    for run in report['runs']:
        be,seed=run['backend'],run['seed'];job=folder/('job-%s-%d'%(be,seed))
        if not completed_job(job,dict(common=guard,backend=be,seed=seed)) or read(job/'result.json')!=run:raise ValueError('completion receipt differs')
        if run['steps']!=512 or run['completed_episodes']!=128 or run['nice']!=19:raise ValueError('frozen budget/runtime differs')
        ordered=sorted(plan['fitting_cases'],key=lambda sid:hashlib.sha256(('TASK043:%d:%s'%(seed,sid)).encode()).hexdigest())
        schedule=[ordered[k%45] for k in range(128)]
        if run['schedule']!=schedule:raise ValueError('schedule differs')
        rows=read(job/'training.json');refs={sid:driver.trajectory(be,sid) for sid in ordered}
        summary=centered_training_ledger(rows,schedule,refs)
        for k in ('steps','episodes'):counts['training_'+k]+=summary[k]
        original_rows=read(driver.PARENT/('job-%s-%d'%(be,seed))/'training.json')[:512]
        if [r['scenario_id'] for r in rows]!=[r['scenario_id'] for r in original_rows]:raise ValueError('matched original schedule differs')
        with np.load(job/'first-rollout.npz',allow_pickle=False) as a,np.load(driver.SIGNAL/('probe-%s-%d.npz'%(be,seed)),allow_pickle=False) as b:
            for key in ('observations','actions','action_masks','values','log_probs','episode_starts'):np.testing.assert_array_equal(a[key],b[key])
            for key in ('rewards','returns','advantages'):np.testing.assert_allclose(a[key],b['centered_'+key],atol=2e-5,rtol=1e-6)
            np.testing.assert_array_equal(a['rewards'],[r['reward'] for r in rows[:16]])
        if run['first_rollout']['status']!='PASS' or not run['first_rollout']['before_optimizer_update']:raise ValueError('first parity absent')
        counts['first_rollout_steps']+=16;counts['completed_jobs']+=1
        initial=None
        for stage in (0,512):
            model=load_policy_arrays(job/('policy-%d.npz'%stage),driver.contract(guard,be,seed,stage,plan));counts['centered_checkpoints']+=1
            original=load_policy_arrays(driver.PARENT/('job-%s-%d'%(be,seed))/('policy-%d.npz'%stage),
                driver.old.contract(parent['guard'],be,seed,stage,parent['plan']));counts['original_checkpoints']+=1
            state={k:v.detach().numpy().copy() for k,v in model.policy.state_dict().items()}
            if stage==0:
                initial=state;paired.setdefault(seed,policy_digest(model))
                if policy_digest(model)!=policy_digest(original) or policy_digest(model)!=paired[seed] or policy_digest(model)!=run['initial_policy_digest']:
                    raise ValueError('matched initial weights differ')
            else:
                if policy_digest(model)!=run['final_policy_digest']:raise ValueError('final policy digest differs')
                deltas=parameter_deltas(initial,state)
                for group in deltas:
                    for key,value in deltas[group].items():close(value,run['parameter_deltas'][group][key])
            probabilities=[];first_masks=[];first_actions=[]
            for sid in plan['evaluation_cases']:
                with np.load(driver.PARENT/'evaluation'/(be+'-'+sid+'.npz'),allow_pickle=False) as a:
                    features=a['features'].copy();masks=a['masks'].copy()
                def actions_for(policy):
                    actions=[0]*4
                    for k in range(4):
                        action=int(policy.predict(features[k],action_masks=masks[k],deterministic=True)[0])
                        if not masks[k,action]:raise ValueError('illegal checkpoint action')
                        if action:actions[k]=action;break
                    return actions
                row=next(x for x in run['rows'] if x['checkpoint']==stage and x['scenario_id']==sid)
                oldrow=next(x for x in run['original_rows'] if x['checkpoint']==stage and x['scenario_id']==sid)
                for policy,target,key in [(model,row,'policy_scores'),(original,oldrow,'original_policy_scores')]:
                    actions=actions_for(policy)
                    if actions!=target['actions']:raise ValueError('checkpoint actions differ')
                    score,_,_=endpoint(be,sid,tuple(actions))
                    for k,value in score.items():
                        if target[k]!=value:raise ValueError('independent policy score differs')
                    counts[key]+=1
                tensor,_=model.policy.obs_to_tensor(features[0])
                with torch.no_grad():p=model.policy.get_distribution(tensor,action_masks=masks[0]).distribution.probs.numpy()[0]
                probabilities.append(p);first_masks.append(masks[0]);first_actions.append(row['actions'][0])
                if stage!=512:continue
                if row.get('native_whole_masks')!='PASS' or sha(job/row['arrays'])!=row['arrays_sha256']:raise ValueError('native receipt differs')
                score,expected_burned,expected_line=endpoint(be,sid,tuple(row['actions']))
                ref=refs.get(sid)
                if ref is None:ref=driver.trajectory(be,sid)
                with np.load(job/row['arrays'],allow_pickle=False) as a:
                    initial_mask=a['initial'];charges=[int(((b|(l&ref[-1]))&~initial_mask).sum()) for b,l in zip(a['burned'],a['line'])]
                    n=[int((x&~initial_mask).sum()) for x in ref];rewards=(np.diff(n)-np.diff(charges))/100.
                    actual=centered_trajectory_score(initial_mask,a['burned'],a['line'],ref,rewards)
                    if actual!=score:raise ValueError('native union score differs')
                    close(math.fsum(rewards),row['native_return'])
                    np.testing.assert_array_equal(a['burned'][-1],expected_burned);np.testing.assert_array_equal(a['line'][-1],expected_line)
                    np.testing.assert_array_equal(initial_mask,ref[0])
                    if not a['masks'][:,0].all():raise ValueError('no-op became illegal')
                    for k in range(4):
                        tensor,_=model.policy.obs_to_tensor(a['features'][k])
                        with torch.no_grad():logits=model.policy.get_distribution(tensor,action_masks=a['masks'][k]).distribution.logits.numpy()[0]
                        np.testing.assert_array_equal(logits,a['logits'][k])
                        if int(logits.argmax())!=row['actions'][k]:raise ValueError('native logits/action differ')
                    saved=next(x for x in run['first_action_diagnostics'] if x['scenario_id']==sid)
                    np.testing.assert_array_equal(np.exp(a['logits'][0]),saved['probabilities'])
                counts['native_paths']+=1;counts['cumulative_states']+=5
            diagnostics.append(dict(backend=be,seed=seed,checkpoint=stage,**action_description(probabilities,first_masks,first_actions)))
    stats=independent_statistics(report,diagnosis)
    expected=dict(completed_jobs=6,training_steps=3072,training_episodes=768,centered_checkpoints=12,original_checkpoints=12,
        policy_scores=192,original_policy_scores=192,native_paths=96,cumulative_states=480,reference_states=610,preflight_paths=32,first_rollout_steps=96)
    if counts!=expected:raise ValueError('audit coverage differs: '+str(counts))
    return dict(status='PASS',analysis_sha256=sha(folder/'analysis.json'),counts=counts,independent_statistics=stats,
        action_diagnostics=diagnostics,numerical_source_unchanged=True,
        audit_source_sha256={p:sha(ROOT/p) for p in ('scripts/audit_centered_ppo_pilot.py','src/wildfire_rl/centered_pilot_audit.py')},
        scope='All six512models and original512references; no retraining; descriptive TRAIN, not physical validation')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if os.getpriority(os.PRIO_PROCESS,0)<19:raise RuntimeError('nice19 required')
    result=audit(a.folder.resolve());a.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('action_diagnostics','audit_source_sha256')},indent=2))
