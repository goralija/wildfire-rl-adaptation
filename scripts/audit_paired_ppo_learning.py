#!/usr/bin/env python3
"""Independent post-run audit and preregistered action/entropy diagnostics."""
import argparse
from collections import Counter
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
from wildfire_rl.common_control_rl import load_policy_arrays,policy_digest
from wildfire_rl.paired_learning_audit import trajectory_score,training_ledger,action_description
import run_paired_ppo_learning as runner


def read(path):return json.loads(Path(path).read_text())


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def close(a,b):
    if not np.allclose(a,b,atol=1e-10,rtol=1e-11):raise ValueError('independent number differs: %s != %s'%(a,b))


def describe(values,target):
    values=np.array(values,float)
    if len(values)!=target['n']:raise ValueError('paired sample size differs')
    if not len(values):
        if target['mean'] is not None or target['ci95'] is not None:raise ValueError('zero denominator must stay undefined')
        return
    close(math.fsum(values)/len(values),target['mean'])
    rng=np.random.default_rng(0);indices=rng.integers(0,len(values),(10000,len(values)))
    close(np.percentile(values[indices].mean(axis=1),[2.5,97.5]),target['ci95'])


def independent_statistics(report,baselines):
    """Do not call the training summary function: reconstruct each fire explicitly."""
    plan=report['plan'];ids=plan['evaluation_cases'];seeds=plan['model_seeds']
    policies={(r['backend'],row['scenario_id'],r['seed'],row['checkpoint']):row
              for r in report['runs'] for row in r['rows']}
    b={(r['backend'],r['scenario_id'],r['method']):r for r in baselines}
    joint=[sid for sid in ids if min(b[be,sid,'noop']['noop_damage_cells'] for be in ('simfire','ca'))>0]
    if joint!=report['summary']['joint_positive_ids']:raise ValueError('joint denominator differs')
    gaps={}
    for be in ('simfire','ca'):
        result=report['summary']['backends'][be]
        def check_metric(values,target):
            # values maps each fire to charged/raw cell counts, without seed replication.
            noop={sid:b[be,sid,'noop']['noop_damage_cells'] for sid in ids}
            fraction=[100*(noop[sid]-values[sid][0])/noop[sid] for sid in joint]
            close(math.fsum(fraction)/len(fraction),target['mean_saved_percent_joint'])
            close(100*math.fsum(noop[s]-values[s][0] for s in ids)/math.fsum(noop.values()),target['pooled_saved_percent_all'])
            close(3.24*math.fsum(values[s][0] for s in ids)/len(ids),target['mean_charged_ha_all'])
            close(3.24*math.fsum(values[s][1] for s in ids)/len(ids),target['mean_raw_ha_all'])
            close(3.24*math.fsum(noop[s]-values[s][0] for s in ids)/len(ids),target['mean_saved_ha_all'])
        bystage={}
        for stage in (0,512,2048):
            averaged={sid:tuple(math.fsum(policies[be,sid,seed,stage][key] for seed in seeds)/len(seeds)
                               for key in ('charged_damage_cells','raw_damage_cells')) for sid in ids}
            bystage[stage]=averaged
            check_metric(averaged,result['checkpoints'][str(stage)])
            for seed in seeds:
                check_metric({sid:(policies[be,sid,seed,stage]['charged_damage_cells'],policies[be,sid,seed,stage]['raw_damage_cells']) for sid in ids},
                             result['checkpoints'][str(stage)]['model_seeds'][str(seed)])
        for method in plan['heuristics']:
            check_metric({sid:(b[be,sid,method]['charged_damage_cells'],b[be,sid,method]['raw_damage_cells']) for sid in ids},result['heuristics'][method])
        n=lambda s:b[be,s,'noop']['noop_damage_cells']
        change=[100*(bystage[0][s][0]-bystage[2048][s][0])/n(s) for s in joint]
        gaps[be]=[100*(b[be,s,'advancing_front64']['charged_damage_cells']-bystage[2048][s][0])/n(s) for s in joint]
        describe(change,result['final_minus_initial_pp']);describe(gaps[be],result['final_minus_front_pp'])
        expected=all(result[key]['ci95'][0]>0 for key in ('final_minus_initial_pp','final_minus_front_pp'))
        if expected!=result['descriptive_positive_signal']:raise ValueError('frozen acceptance differs')
    describe(np.array(gaps['ca'])-gaps['simfire'],report['summary']['ca_minus_sf_relative_gap_pp'])
    return dict(status='PASS',joint_positive_cases=len(joint),all_case_denominator=len(ids),
                policy_rows=len(policies),baseline_rows=len(b),bootstrap_draws=10000,bootstrap_seed=0,
                model_seed_unit='average within fire, never independent fires')


def audit(folder):
    report=read(folder/'analysis.json');plan=report['plan'];guard=read(folder/'guard.json');pre=read(folder/'preflight.json')
    if report['status']!='PASS' or report['guard']!=guard or pre['guard']!=guard:raise ValueError('run guard differs')
    if read(ROOT/'configs/frozen/paired-ppo-learning-v1.json')!=plan:raise ValueError('plan differs')
    if sha(ROOT/'configs/frozen/paired-ppo-learning-v1.json')!=guard['plan_sha256']:raise ValueError('plan bytes differ')
    for path,digest in guard['source_sha256'].items():
        if sha(ROOT/path)!=digest:raise ValueError('training source changed: '+path)
    if (folder/'error.json').exists() or (folder/'stop.json').exists():raise ValueError('recorded run failure')
    for name,digest in pre['files'].items():
        if sha(folder/name)!=digest:raise ValueError('preflight arrays changed')
    counts=dict(completed_jobs=0,training_steps=0,training_episodes=0,checkpoints=0,
                policy_scores=0,native_paths=0,native_masks=0,reference_masks=0,preflight_tree_paths=0)
    for sid in plan['fitting_cases']+plan['evaluation_cases']:
        if sid in set(plan['fitting_cases'])&set(plan['evaluation_cases']):raise ValueError('fitting/evaluation overlap')
        for be in ('simfire','ca'):
            with np.load(folder/'references'/(be+'-'+sid+'.npz'),allow_pickle=False) as a:
                if a['burned'].shape!=(5,256,256) or (a['burned'][:-1]&~a['burned'][1:]).any():raise ValueError('invalid reference')
                np.testing.assert_array_equal(a['initial'],a['burned'][0]);counts['reference_masks']+=5
    archive={}
    for be in ('simfire','ca'):
        for sid in plan['evaluation_cases']:
            rec,path=runner.table(be,sid)
            with np.load(path,allow_pickle=False) as a:
                archive[be,sid]=(rec,{k:a[k].copy() for k in ('initial','noop','agent_burned','line_cells')})
    def endpoint(be,sid,actions):
        rec,a=archive[be,sid]
        idx=next(i for i,r in enumerate(rec['outcomes']) if r['effective_actions']==list(actions))
        initial=a['initial'];burned=a['agent_burned'][idx];line=a['line_cells'][idx];noop=a['noop']
        raw=int((burned&~initial).sum());charged=int(((burned|(line&noop))&~initial).sum());n=int((noop&~initial).sum())
        return dict(noop_damage_cells=n,raw_damage_cells=raw,charged_damage_cells=charged,
            extra_line_charge_cells=charged-raw,line_cells_in_noop_footprint=int((line&noop&~initial).sum()),
            raw_saved_cells=n-raw,charged_saved_cells=n-charged),burned,line
    for row in pre['baselines']:
        score,_,_=endpoint(row['backend'],row['scenario_id'],row['actions'])
        for key,value in score.items():
            if row[key]!=value:raise ValueError('baseline score differs')
    for tree in pre['trees']:
        for row in tree['paths']:
            score,_,_=endpoint(tree['backend'],tree['scenario_id'],row['effective_actions'])
            if row['score']!=score:raise ValueError('preflight tree score differs')
            close(row['return_'],-score['charged_damage_cells']/100.-.01*row['invalid_requests'])
            counts['preflight_tree_paths']+=1
    torch.set_num_threads(1);diagnostics=[];initials={}
    for run in sorted(report['runs'],key=lambda r:(r['backend'],r['seed'])):
        be,seed=run['backend'],run['seed'];job=folder/('job-%s-%d'%(be,seed))
        done=read(job/'done.json')
        if done['guard']!={'common':guard,'backend':be,'seed':seed} or read(job/'result.json')!=run:
            raise ValueError('job receipt/result differs')
        for name,digest in done['files'].items():
            if sha(job/name)!=digest:raise ValueError('job artifact changed')
        schedule=sorted(plan['fitting_cases'],key=lambda sid:hashlib.sha256(('TASK043:%d:%s'%(seed,sid)).encode()).hexdigest())
        schedule=[schedule[k%45] for k in range(512)]
        if run['schedule']!=schedule:raise ValueError('case schedule differs')
        tr=training_ledger(read(job/'training.json'),schedule)
        counts['completed_jobs']+=1;counts['training_steps']+=tr['steps'];counts['training_episodes']+=tr['episodes']
        for stage in (0,512,2048):
            model=load_policy_arrays(job/('policy-%d.npz'%stage),runner.contract(guard,be,seed,stage,plan))
            if stage==0:
                initials.setdefault(seed,policy_digest(model))
                if initials[seed]!=policy_digest(model) or policy_digest(model)!=run['initial_policy_digest']:
                    raise ValueError('paired initial weights differ')
            if stage==2048 and policy_digest(model)!=run['final_policy_digest']:raise ValueError('final weight digest differs')
            counts['checkpoints']+=1;probabilities=[];first_masks=[];first_actions=[]
            for sid in plan['evaluation_cases']:
                row=next(r for r in run['rows'] if r['scenario_id']==sid and r['checkpoint']==stage)
                with np.load(folder/'evaluation'/(be+'-'+sid+'.npz'),allow_pickle=False) as a:
                    features=a['features'].copy();masks=a['masks'].copy()
                tensor,_=model.policy.obs_to_tensor(features[0])
                with torch.no_grad():p=model.policy.get_distribution(tensor,action_masks=masks[0]).distribution.probs.cpu().numpy()[0]
                probabilities.append(p);first_masks.append(masks[0]);first_actions.append(int(p.argmax()))
                actions=[0]*4
                for k in range(4):
                    a=int(model.predict(features[k],action_masks=masks[k],deterministic=True)[0])
                    if not masks[k,a]:raise ValueError('illegal checkpoint action')
                    if a:actions[k]=a;break
                if row['actions']!=actions:raise ValueError('checkpoint decision replay differs')
                score,burned,line=endpoint(be,sid,actions)
                for key,value in score.items():
                    if row[key]!=value:raise ValueError('checkpoint score differs')
                counts['policy_scores']+=1
                if stage==2048:
                    path=job/row['arrays']
                    if sha(path)!=row['arrays_sha256']:raise ValueError('native replay bytes differ')
                    with np.load(path,allow_pickle=False) as a:
                        with np.load(folder/'references'/(be+'-'+sid+'.npz'),allow_pickle=False) as ref:
                            charges=[int(((b|(l&ref['burned'][-1]))&~a['initial']).sum()) for b,l in zip(a['burned'],a['line'])]
                            rewards=(-np.diff(charges)/100.).tolist()
                            actual=trajectory_score(a['initial'],a['burned'],a['line'],ref['burned'][-1],rewards)
                        if actual!=score:raise ValueError('native independent union score differs')
                        close(sum(rewards),row['native_return'])
                        np.testing.assert_array_equal(a['burned'][-1],burned);np.testing.assert_array_equal(a['line'][-1],line)
                        for k in range(4):
                            tensor,_=model.policy.obs_to_tensor(a['features'][k])
                            with torch.no_grad():logits=model.policy.get_distribution(tensor,action_masks=a['masks'][k]).distribution.logits.cpu().numpy()[0]
                            np.testing.assert_array_equal(logits,a['logits'][k])
                            if int(logits.argmax())!=actions[k]:raise ValueError('native action logits differ')
                    counts['native_paths']+=1;counts['native_masks']+=5
            diagnostics.append(dict(backend=be,seed=seed,checkpoint=stage,**action_description(probabilities,first_masks,first_actions)))
    stats=independent_statistics(report,pre['baselines'])
    if counts!={'completed_jobs':6,'training_steps':12288,'training_episodes':3072,'checkpoints':18,
                'policy_scores':288,'native_paths':96,'native_masks':480,'reference_masks':610,'preflight_tree_paths':132}:
        raise ValueError('audit coverage differs: '+str(counts))
    return dict(status='PASS',analysis_sha256=sha(folder/'analysis.json'),counts=counts,
        independent_statistics=stats,action_diagnostics=diagnostics,
        scope='Same frozen experiment, all seeds/checkpoints; descriptive TRAIN development, no physical validation',
        audit_source_sha256={f:sha(ROOT/f) for f in ('scripts/audit_paired_ppo_learning.py','src/wildfire_rl/paired_learning_audit.py')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    result=audit(args.folder);args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('action_diagnostics','audit_source_sha256')},indent=2))
