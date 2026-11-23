#!/usr/bin/env python3
"""ADR-055: one reward change, six matched512step models, detached handoff."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.local/matplotlib'))
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import numpy as np
import torch
from stable_baselines3.common.callbacks import BaseCallback
import run_paired_ppo_learning as old
from wildfire_rl.centered_control import CenteredControlEnv,REWARD_VERSION,compare_costs,method_metrics
from wildfire_rl.common_control_rl import create_model,save_policy_arrays,load_policy_arrays,policy_digest
from wildfire_rl.feds_b1 import policy_sequence
from wildfire_rl.feds_simfire_setup import load_case_inputs
from wildfire_rl.paired_ppo_learning import case_schedule,LazyTrainingCases,completed_job,_description
from wildfire_rl.ppo_signal_rl import parameter_delta
from wildfire_rl.ppo_signal_diagnosis import uniform_line_expectation

PLAN=ROOT/'configs/frozen/centered-ppo-pilot-v1.json'
PARENT=ROOT/'.local/paired-ppo-v1'
SIGNAL=ROOT/'.local/signal-v1'
read=old.read
sha=old.sha


def write(path,value):
    path=Path(path);tmp=path.with_name(path.name+'.%d.tmp'%os.getpid())
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def context():
    plan=read(PLAN);parent=read(PARENT/'analysis.json');diagnosis=read(SIGNAL/'analysis.json');g=plan['guards']
    for p,key in [(old.PLAN,'parent_plan_sha256'),(PARENT/'analysis.json','parent_analysis_sha256'),
        (PARENT/'preflight.json','parent_preflight_sha256'),
        (ROOT/'configs/frozen/ppo-signal-diagnosis-v1.json','diagnosis_plan_sha256'),
        (SIGNAL/'analysis.json','diagnosis_analysis_sha256')]:
        if sha(p)!=g[key]:raise ValueError('frozen artifact changed: '+str(p))
    old.assert_guard(parent['guard']);old.checked_preflight(PARENT,parent['guard'])
    pp=parent['plan']
    for key in ('fitting_cases','evaluation_cases','model_seeds','architecture','ppo','control'):
        if plan[key]!=pp[key]:raise ValueError('one-factor design differs: '+key)
    if plan['training_steps']!=512 or plan['checkpoints']!=[0,512] or plan['reward']['version']!=REWARD_VERSION:
        raise ValueError('frozen centered budget/reward changed')
    for run in parent['runs']:
        if not completed_job(PARENT/('job-%s-%d'%(run['backend'],run['seed'])),run['guard']):
            raise ValueError('parent job incomplete')
    for probe in diagnosis['probes']:
        path=SIGNAL/('probe-%s-%d.npz'%(probe['backend'],probe['seed']))
        if sha(path)!=probe['arrays_sha256']:raise ValueError('diagnostic first rollout changed')
    libraries={}
    for module,receipt in diagnosis['guard']['library_source'].items():
        path=Path(importlib.util.find_spec(module).origin);h=sha(path)
        if h!=receipt['sha256']:raise ValueError('optimizer/PPO library changed')
        libraries[module]=h
    sources={p:sha(ROOT/p) for p in ('scripts/run_centered_ppo_pilot.py','src/wildfire_rl/centered_control.py',
        'src/wildfire_rl/ppo_signal_rl.py','src/wildfire_rl/ppo_signal_diagnosis.py')}
    guard=dict(plan_sha256=sha(PLAN),source_sha256=sources,parent_guard=parent['guard'],
               diagnosis_guard=diagnosis['guard'],library_sha256=libraries)
    return plan,parent,diagnosis,guard


def assert_guard(guard):
    result=context()
    if result[-1]!=guard:raise ValueError('source/plan/runtime/artifacts changed')
    return result[:3]


def trajectory(backend,sid):
    with np.load(PARENT/'references'/(backend+'-'+sid+'.npz'),allow_pickle=False) as a:
        return a['burned'].copy()


def make_env(backend,sid):
    return CenteredControlEnv(old.make_env(PARENT,backend,sid),trajectory(backend,sid))


def rollout(env,sequence=None,model=None,centered=True):
    obs,_=env.reset();base=env.env if centered else env
    initial=env.unwrapped.cumulative_burned.copy()
    burned=[initial];lines=[np.zeros(initial.shape,bool)];features=[];masks=[];logits=[];rows=[]
    for k in range(4):
        mask=env.action_masks().copy();features.append(obs.copy());masks.append(mask)
        if model is None:action=int(sequence[k])
        else:
            tensor,_=model.policy.obs_to_tensor(obs)
            with torch.no_grad():
                logits.append(model.policy.get_distribution(tensor,action_masks=mask).distribution.logits.cpu().numpy()[0])
            action=int(model.predict(obs,action_masks=mask,deterministic=True)[0])
            if not mask[action]:raise ValueError('illegal deterministic action')
        obs,reward,done,trunc,info=env.step(action)
        if done!=(k==3) or trunc:raise ValueError('four full decisions required')
        if not np.isfinite(reward) or not env.observation_space.contains(obs):raise ValueError('invalid reward/observation')
        burned.append(env.unwrapped.cumulative_burned.copy());lines.append(base.ledger.line.copy())
        rows.append(dict(step=k,requested_action=action,effective_action=info['effective_action'],
            invalid=bool(info['invalid_action']),reward=reward,remaining_budget=info['remaining_budget'],
            charged_damage_cells=info['charged_damage_cells'],charged_increment_cells=info['charged_increment_cells'],
            original_reward=info.get('original_charged_reward',reward),noop_increment_cells=info.get('noop_increment_cells',0)))
    score=base.ledger.score;invalids=sum(r['invalid'] for r in rows);total=sum(r['reward'] for r in rows)
    target=((score['noop_damage_cells'] if centered else 0)-score['charged_damage_cells'])/100.-invalids*.01
    np.testing.assert_allclose(total,target,atol=1e-12,rtol=0)
    np.testing.assert_allclose(sum(r['original_reward'] for r in rows),-score['charged_damage_cells']/100.-invalids*.01,atol=1e-12,rtol=0)
    return dict(rows=rows,score=score,return_=total,invalid_requests=invalids),dict(
        initial=initial,burned=np.stack(burned),line=np.stack(lines),features=np.stack(features),
        masks=np.stack(masks),logits=np.array(logits),final_observation=obs)


def paired_paths(job):
    folder,backend,sid,guard=job;out=Path(folder);plan,_,_=assert_guard(guard)
    raw=old.make_env(PARENT,backend,sid);center=make_env(backend,sid);rows=[];arrays={}
    started=time.monotonic()
    for i,sequence in enumerate(plan['preflight']['requested_sequences']):
        a,aa=rollout(raw,sequence=sequence,centered=False);b,bb=rollout(center,sequence=sequence)
        for key in ('initial','burned','line','features','masks','final_observation'):
            np.testing.assert_array_equal(aa[key],bb[key])
        if a['score']!=b['score']:raise ValueError('centered physical score changed')
        for k,(ar,br) in enumerate(zip(a['rows'],b['rows'])):
            for key in ('requested_action','effective_action','invalid','remaining_budget','charged_damage_cells','charged_increment_cells'):
                if ar[key]!=br[key]:raise ValueError('paired transition differs')
            np.testing.assert_allclose(br['reward']-ar['reward'],br['noop_increment_cells']/100.,atol=1e-12,rtol=0)
        if sequence==[0,0,0,0]:
            np.testing.assert_array_equal(aa['burned'],trajectory(backend,sid))
        rows.append(dict(sequence=sequence,raw=a,centered=b,status='PASS'))
        for key in ('initial','burned','line','features','masks','final_observation'):arrays['path%d_%s'%(i,key)]=bb[key]
    raw.close();center.close();name='paths-'+backend+'-'+sid
    np.savez_compressed(out/(name+'.npz'),**arrays)
    result=dict(backend=backend,scenario_id=sid,guard=guard,paths=rows,arrays_sha256=sha(out/(name+'.npz')),
                seconds=time.monotonic()-started,status='PASS')
    write(out/(name+'.json'),result);return result


def preflight(out):
    plan,parent,diagnosis,guard=context();out.mkdir(parents=True,exist_ok=False);write(out/'guard.json',guard)
    started=time.monotonic();references=[]
    for sid in plan['fitting_cases']+plan['evaluation_cases']:
        inputs=load_case_inputs(sid,split='train')
        if inputs['receipt_sha256']!=parent['plan']['input_receipt_sha256'][sid]:raise ValueError('input receipt differs')
        for backend in ('simfire','ca'):
            a=trajectory(backend,sid);initial=inputs['scar']|inputs['front']
            if a.shape!=(5,)+initial.shape or not np.isin(a,[0,1]).all() or (a[:-1]&~a[1:]).any():
                raise ValueError('invalid full reference trajectory')
            np.testing.assert_array_equal(a[0],initial)
            references.append(dict(backend=backend,scenario_id=sid,
                sha256=sha(PARENT/'references'/(backend+'-'+sid+'.npz'))))
    jobs=[(str(out),be,sid,guard) for be in ('simfire','ca') for sid in plan['preflight']['cases']]
    with ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('spawn'),initializer=old.setup_worker) as pool:
        paths=list(pool.map(paired_paths,jobs))
    assert_guard(guard)
    files={p.name:sha(p) for p in out.iterdir() if p.name.startswith('paths-')}
    result=dict(status='PASS',guard=guard,reference_files=references,paired_paths=32,native_episodes=64,
        physics_features_masks_budget_horizon='PASS',per_step_and_episode_reward_identity='PASS',
        paths=paths,files=files,seconds=time.monotonic()-started)
    write(out/'preflight.json',result);print('PREFLIGHT PASS',result['seconds'],flush=True)


def checked_preflight(out,guard):
    pre=read(out/'preflight.json')
    if pre['status']!='PASS' or pre['guard']!=guard:raise ValueError('preflight guard mismatch')
    for name,h in pre['files'].items():
        if sha(out/name)!=h:raise ValueError('preflight archive changed')
    return pre


def contract(guard,backend,seed,stage,plan):
    return dict(guard=guard,backend=backend,seed=seed,checkpoint_steps=stage,
                architecture=plan['architecture'],reward=REWARD_VERSION)


class LearningCallback(BaseCallback):
    def __init__(self,jobdir,guard,backend,seed,plan):
        super().__init__();self.jobdir=jobdir;self.guard=guard;self.backend=backend;self.seed=seed
        self.plan=plan;self.rows=[];self.started=time.time();self.first_rollout=None

    def _on_step(self):
        if (self.jobdir.parent/'stop.json').exists():raise RuntimeError('global stop requested')
        info=self.locals['infos'][0];k=(self.num_timesteps-1)%4
        if info['invalid_action'] or not np.isfinite(self.locals['rewards']).all():raise ValueError('illegal/nonfinite PPO step')
        if info['remaining_budget'] not in (0,1) or bool(self.locals['dones'][0])!=(k==3):
            raise ValueError('budget/horizon mismatch')
        self.rows.append(dict(step=self.num_timesteps,scenario_id=info['scenario_id'],action=info['effective_action'],
            reward=float(self.locals['rewards'][0]),original_reward=info['original_charged_reward'],
            noop_increment_cells=info['noop_increment_cells'],charged_increment_cells=info['charged_increment_cells'],
            done=bool(self.locals['dones'][0]),remaining_budget=info['remaining_budget'],charged_damage_cells=info['charged_damage_cells']))
        if self.num_timesteps%16==0:
            write(self.jobdir/'status.json',dict(phase='training',pid=os.getpid(),steps=self.num_timesteps,target=512,
                first_rollout=self.first_rollout,updated_unix=time.time(),elapsed_seconds=time.time()-self.started))
        return True

    def _on_rollout_end(self):
        if self.num_timesteps!=16:return
        if self.model._n_updates!=0 or self.model.policy.optimizer.state:raise ValueError('first parity must precede update')
        b=self.model.rollout_buffer
        data={key:np.asarray(getattr(b,key)).reshape((16,)+tuple(getattr(b,key).shape[2:])).copy()
            for key in ('observations','actions','rewards','values','log_probs','advantages','returns','action_masks','episode_starts')}
        data['actions']=data['actions'].reshape(16);errors={}
        # Different order of float32 rounding is localized to reward-derived tensors.
        # An integer count divided by100 is compared with raw_float32+offset.
        with np.load(SIGNAL/('probe-%s-%d.npz'%(self.backend,self.seed)),allow_pickle=False) as probe:
            for key in ('observations','actions','action_masks','values','log_probs','episode_starts'):
                np.testing.assert_array_equal(data[key],probe[key])
            for key in ('rewards','returns','advantages'):
                expected=probe['centered_'+key]
                np.testing.assert_allclose(data[key],expected,atol=2e-5,rtol=1e-6)
                errors[key]=float(np.max(np.abs(data[key]-expected)))
        oldrows=read(PARENT/('job-%s-%d'%(self.backend,self.seed))/'training.json')[:16]
        for a,b in zip(self.rows,oldrows):
            for key in ('step','scenario_id','action','done','remaining_budget','charged_damage_cells'):
                if a[key]!=b[key]:raise ValueError('original first16 transition differs')
            if float(np.float32(a['original_reward']))!=b['reward']:raise ValueError('original first16 reward differs')
        np.savez_compressed(self.jobdir/'first-rollout.npz',**data)
        self.first_rollout=dict(status='PASS',exact_inputs_actions_masks_values_logprobs=True,
            max_reward_tensor_errors=errors,atol=2e-5,rtol=1e-6,before_optimizer_update=True,
            sha256=sha(self.jobdir/'first-rollout.npz'))
        write(self.jobdir/'first-rollout.json',self.first_rollout)


def policy_actions(model,backend,sid):
    with np.load(PARENT/'evaluation'/(backend+'-'+sid+'.npz'),allow_pickle=False) as a:
        features=a['features'].copy();masks=a['masks'].copy()
    def policy(obs,mask):
        action=int(model.predict(obs,action_masks=mask,deterministic=True)[0])
        if not mask[action]:raise ValueError('invalid masked action')
        return action
    return list(policy_sequence(policy,features,masks))


def policy_row(model,backend,seed,stage,sid):
    actions=policy_actions(model,backend,sid)
    return dict(backend=backend,seed=seed,checkpoint=stage,scenario_id=sid,actions=actions,
                **old.lookup(backend,sid,actions))


def train_job(job):
    folder,backend,seed,guard=job;out=Path(folder);plan,parent,_=assert_guard(guard)
    jobdir=out/('job-%s-%d'%(backend,seed));jobguard=dict(common=guard,backend=backend,seed=seed)
    if completed_job(jobdir,jobguard):return read(jobdir/'result.json')
    if (out/'stop.json').exists():raise RuntimeError('recorded stop condition')
    jobdir.mkdir(exist_ok=False);started=time.monotonic()
    write(jobdir/'status.json',dict(phase='starting',pid=os.getpid(),updated_unix=time.time()))
    try:
        schedule=case_schedule(plan['fitting_cases'],seed)
        env=LazyTrainingCases(schedule,lambda sid:make_env(backend,sid))
        model=create_model(env,seed=seed,settings=plan['ppo']);initial=policy_digest(model)
        oldrun=next(r for r in parent['runs'] if r['backend']==backend and r['seed']==seed)
        if initial!=oldrun['initial_policy_digest']:raise ValueError('initial weights differ from parent')
        initial_state={k:v.detach().clone() for k,v in model.policy.state_dict().items()}
        save_policy_arrays(model,jobdir/'policy-0.npz',contract(guard,backend,seed,0,plan))
        cb=LearningCallback(jobdir,guard,backend,seed,plan)
        model.learn(512,callback=cb)
        save_policy_arrays(model,jobdir/'policy-512.npz',contract(guard,backend,seed,512,plan))
        expected=[schedule[k%45] for k in range(128)]
        if [r['scenario_id'] for r in cb.rows if r['done']]!=expected or model.num_timesteps!=512 or not cb.first_rollout:
            raise ValueError('complete128episode schedule/checkpoint parity failed')
        original=read(PARENT/('job-%s-%d'%(backend,seed))/'training.json')[:512]
        if [r['scenario_id'] for r in cb.rows]!=[r['scenario_id'] for r in original]:raise ValueError('matched512 case schedule differs')
        diagnostics={k:float(v) for k,v in model.logger.name_to_value.items() if isinstance(v,(float,int,np.number))}
        if not all(np.isfinite(v) for v in diagnostics.values()) or policy_digest(model)==initial:
            raise ValueError('nonfinite/no learning update')
        deltas=parameter_delta(initial_state,model);env.close();write(jobdir/'training.json',cb.rows)
        rows=[];baselines=[];first=[]
        for stage in (0,512):
            restored=load_policy_arrays(jobdir/('policy-%d.npz'%stage),contract(guard,backend,seed,stage,plan))
            if policy_digest(restored)!=(initial if stage==0 else policy_digest(model)):
                raise ValueError('restored policy digest mismatch')
            original_model=load_policy_arrays(PARENT/('job-%s-%d'%(backend,seed))/('policy-%d.npz'%stage),
                old.contract(parent['guard'],backend,seed,stage,parent['plan']))
            for i,sid in enumerate(plan['evaluation_cases']):
                if (out/'stop.json').exists():raise RuntimeError('global stop requested')
                write(jobdir/'status.json',dict(phase='evaluating',pid=os.getpid(),checkpoint=stage,
                    case_index=i,steps=512,updated_unix=time.time()))
                row=policy_row(restored,backend,seed,stage,sid)
                baseline=policy_row(original_model,backend,seed,stage,sid);baselines.append(baseline)
                if stage==0 and row!=baseline:raise ValueError('initial greedy evaluation differs')
                if stage==512:
                    native=make_env(backend,sid);actual,arrays=rollout(native,model=restored);native.close()
                    if [r['effective_action'] for r in actual['rows']]!=row['actions'] or actual['score']!={k:row[k] for k in actual['score']}:
                        raise ValueError('native final policy actions/score differ')
                    record,path=old.table(backend,sid)
                    index=next(i for i,r in enumerate(record['outcomes']) if r['effective_actions']==row['actions'])
                    with np.load(path,allow_pickle=False) as a:
                        np.testing.assert_array_equal(arrays['burned'][-1],a['agent_burned'][index])
                        np.testing.assert_array_equal(arrays['line'][-1],a['line_cells'][index])
                    if actual['invalid_requests']:raise ValueError('native masked policy requested invalid action')
                    name='native-'+sid+'.npz';np.savez_compressed(jobdir/name,**arrays)
                    row.update(native_whole_masks='PASS',arrays=name,arrays_sha256=sha(jobdir/name),native_return=actual['return_'])
                    p=np.exp(arrays['logits'][0]);positive=p>0
                    first.append(dict(scenario_id=sid,action=row['actions'][0],probabilities=p.tolist(),
                        entropy=float(-(p[positive]*np.log(p[positive])).sum()),max_probability=float(p.max())))
                rows.append(row)
        assert_guard(guard)
        result=dict(backend=backend,seed=seed,guard=jobguard,initial_policy_digest=initial,
            final_policy_digest=policy_digest(model),steps=512,completed_episodes=128,schedule=expected,
            first_rollout=cb.first_rollout,parameter_deltas=deltas,diagnostics=diagnostics,
            first_action_diagnostics=first,rows=rows,original_rows=baselines,seconds=time.monotonic()-started,
            nice=os.getpriority(os.PRIO_PROCESS,0),status='PASS')
        write(jobdir/'result.json',result)
        write(jobdir/'status.json',dict(phase='complete',steps=512,pid=os.getpid(),updated_unix=time.time()))
        files={p.name:sha(p) for p in jobdir.iterdir() if p.is_file() and p.name!='status.json'}
        write(jobdir/'done.json',dict(guard=jobguard,files=files,status='PASS'));return result
    except BaseException:
        failure=dict(backend=backend,seed=seed,error=traceback.format_exc(),updated_unix=time.time())
        write(out/'stop.json',failure);write(jobdir/'error.json',failure)
        write(jobdir/'status.json',dict(phase='failed',pid=os.getpid(),updated_unix=time.time()));raise


def summarize(plan,results,diagnosis):
    ids=plan['evaluation_cases'];seeds=plan['model_seeds']
    p={(r['backend'],r['seed'],x['scenario_id'],x['checkpoint']):x for r in results for x in r['rows']}
    b={(r['backend'],r['seed'],x['scenario_id'],x['checkpoint']):x for r in results for x in r['original_rows']}
    n={be:np.array([old.lookup(be,sid,[0,0,0,0])['noop_damage_cells'] for sid in ids],float) for be in ('simfire','ca')}
    joint=(n['simfire']>0)&(n['ca']>0)
    result=dict(scope='Exploratory TRAIN development,16previously explored cases; no physical validation or heldout confirmation',
                joint_positive_ids=[sid for sid,yes in zip(ids,joint) if yes],backends={})
    changes={};frontgaps={};uniformgaps={}
    for be in ('simfire','ca'):
        costs={};raw={}
        for label,rows,stage in [('centered512',p,512),('original512',b,512),('initial0',p,0)]:
            costs[label]=np.array([[rows[be,seed,sid,stage]['charged_damage_cells'] for sid in ids] for seed in seeds],float)
            raw[label]=np.array([[rows[be,seed,sid,stage]['raw_damage_cells'] for sid in ids] for seed in seeds],float)
        for method in ('noop','advancing_front64','downwind','random_legal'):
            rows=[r for r in read(PARENT/'preflight.json')['baselines'] if r['backend']==be and r['method']==method]
            byid={r['scenario_id']:r for r in rows}
            costs[method]=np.array([byid[sid]['charged_damage_cells'] for sid in ids],float)
            raw[method]=np.array([byid[sid]['raw_damage_cells'] for sid in ids],float)
        references=diagnosis['references'];case_rows=references['case_scores'][be]
        selected=references['backends'][be]['evaluation']['fitting_selected_sector']
        uniform=[];uniform_raw=[]
        for sid in ids:
            with np.load(PARENT/'evaluation'/(be+'-'+sid+'.npz'),allow_pickle=False) as a:mask=a['masks'][0]
            uniform.append(uniform_line_expectation([r['charged_damage_cells'] for r in case_rows[sid]],mask))
            uniform_raw.append(uniform_line_expectation([r['raw_damage_cells'] for r in case_rows[sid]],mask))
        costs['exact_uniform']=np.array(uniform);raw['exact_uniform']=np.array(uniform_raw)
        costs['fitting_selected_fixed']=np.array([case_rows[sid][selected]['charged_damage_cells'] for sid in ids],float)
        raw['fitting_selected_fixed']=np.array([case_rows[sid][selected]['raw_damage_cells'] for sid in ids],float)
        c=costs['centered512'];comparisons={name:compare_costs(c,d,n[be],joint) for name,d in costs.items() if name!='centered512'}
        metrics={name:method_metrics(d,n[be],joint,raw[name]) for name,d in costs.items()}
        model_seeds={str(seed):method_metrics(c[k],n[be],joint,raw['centered512'][k]) for k,seed in enumerate(seeds)}
        lower=[comparisons[name]['ci95'][0] for name in ('original512','exact_uniform') if comparisons[name]['ci95']]
        result['backends'][be]=dict(metrics=metrics,centered_minus_reference_pp=comparisons,model_seeds=model_seeds,
            fitting_selected_sector=selected,zero_noop_ids=[sid for sid,v in zip(ids,n[be]) if not v],
            continuation_signal=bool(len(lower)==2 and min(lower)>0))
        changes[be]=(costs['original512'].mean(axis=0)[joint]-c.mean(axis=0)[joint])/n[be][joint]*100
        frontgaps[be]=(costs['advancing_front64'][joint]-c.mean(axis=0)[joint])/n[be][joint]*100
        uniformgaps[be]=(costs['exact_uniform'][joint]-c.mean(axis=0)[joint])/n[be][joint]*100
    result['ca_minus_sf_improvement_pp']=_description(changes['ca']-changes['simfire'])
    result['ca_minus_sf_gap_to_front_pp']=_description(frontgaps['ca']-frontgaps['simfire'])
    result['ca_minus_sf_gap_to_uniform_pp']=_description(uniformgaps['ca']-uniformgaps['simfire'])
    return result


def run(out):
    plan,parent,diagnosis,current=context();guard=read(out/'guard.json')
    if current!=guard:raise ValueError('preflight source/artifact guard differs')
    checked_preflight(out,guard)
    if (out/'stop.json').exists():raise RuntimeError('recorded stop; new documented attempt required')
    jobs=[(str(out),be,seed,guard) for be in ('simfire','ca') for seed in plan['model_seeds']]
    for _,be,seed,_ in jobs:
        path=out/('job-%s-%d'%(be,seed));g=dict(common=guard,backend=be,seed=seed)
        if path.exists() and not completed_job(path,g):raise RuntimeError('partial job; no optimizer resume: '+str(path))
    lock=out/'coordinator.lock'
    with lock.open('x') as f:f.write(str(os.getpid()))
    started=time.time();results=[]
    write(out/'status.json',dict(phase='running',pid=os.getpid(),started_unix=started,jobs=6,workers=3,target_per_job=512))
    try:
        with ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('spawn'),initializer=old.setup_worker) as pool:
            futures=[pool.submit(train_job,j) for j in jobs]
            try:
                for future in as_completed(futures):
                    results.append(future.result())
                    write(out/'status.json',dict(phase='running',pid=os.getpid(),started_unix=started,
                        completed=len(results),jobs=6,updated_unix=time.time()))
            except BaseException:
                write(out/'stop.json',dict(error=traceback.format_exc(),updated_unix=time.time()))
                for f in futures:f.cancel()
                raise
        results.sort(key=lambda r:(r['backend'],r['seed']))
        for seed in plan['model_seeds']:
            if len({r['initial_policy_digest'] for r in results if r['seed']==seed})!=1:
                raise ValueError('paired initialization differs')
        assert_guard(guard);summary=summarize(plan,results,diagnosis)
        write(out/'analysis.json',dict(guard=guard,plan=plan,summary=summary,runs=results,
            seconds=time.time()-started,status='PASS'))
        write(out/'status.json',dict(phase='complete',completed=6,jobs=6,pid=os.getpid(),updated_unix=time.time()))
    except BaseException:
        write(out/'error.json',dict(error=traceback.format_exc(),pid=os.getpid(),updated_unix=time.time()))
        write(out/'status.json',dict(phase='failed',completed=len(results),pid=os.getpid(),updated_unix=time.time()));raise
    finally:lock.unlink(missing_ok=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['preflight','run'])
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    if os.getpriority(os.PRIO_PROCESS,0)<19:raise RuntimeError('nice19 required')
    if args.command=='preflight':preflight(args.out.resolve())
    else:run(args.out.resolve())
