#!/usr/bin/env python3
"""ADR057 final bounded optimizer pilot; original reward, separate clipping."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import hashlib
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
import run_centered_ppo_pilot as centered
from wildfire_rl.separate_clip_rl import create_model,CLIPPING_VERSION
from wildfire_rl.common_control_rl import save_policy_arrays,load_policy_arrays,policy_digest
from wildfire_rl.paired_ppo_learning import case_schedule,LazyTrainingCases,completed_job
from wildfire_rl.centered_control import compare_costs,method_metrics
from wildfire_rl.ppo_signal_rl import collect_initial,gradient_probe,parameter_delta

old=centered.old
PARENT=centered.PARENT
SIGNAL=centered.SIGNAL
CENTERED=ROOT/'.local/centered-ppo-v1'
PLAN=ROOT/'configs/frozen/separate-clip-pilot-v1.json'
read=centered.read
write=centered.write
sha=centered.sha
policy_actions=centered.policy_actions
policy_row=centered.policy_row
trajectory=centered.trajectory


def context():
    plan=read(PLAN);parent=read(PARENT/'analysis.json');diagnosis=read(SIGNAL/'analysis.json')
    previous=read(CENTERED/'analysis.json');centered.assert_guard(previous['guard'])
    centered.checked_preflight(CENTERED,previous['guard'])
    for run in previous['runs']:
        if not completed_job(CENTERED/('job-%s-%d'%(run['backend'],run['seed'])),run['guard']):raise ValueError('centered parent incomplete')
    for key in ('fitting_cases','evaluation_cases','model_seeds','architecture','ppo','control'):
        if plan[key]!=parent['plan'][key]:raise ValueError('one-factor design differs: '+key)
    if plan['training_steps']!=512 or plan['checkpoints']!=[0,512] or plan['change']['version']!=CLIPPING_VERSION:
        raise ValueError('frozen optimizer budget/version differs')
    paths={
        'parent_plan_sha256':old.PLAN,'parent_analysis_sha256':PARENT/'analysis.json',
        'parent_preflight_sha256':PARENT/'preflight.json',
        'diagnosis_plan_sha256':ROOT/'configs/frozen/ppo-signal-diagnosis-v1.json',
        'diagnosis_analysis_sha256':SIGNAL/'analysis.json',
        'centered_plan_sha256':centered.PLAN,'centered_analysis_sha256':CENTERED/'analysis.json',
        'centered_preflight_sha256':CENTERED/'preflight.json'}
    for key,path in paths.items():
        if sha(path)!=plan['guards'][key]:raise ValueError('frozen baseline changed: '+key)
    sources={p:sha(ROOT/p) for p in ('scripts/run_separate_clip_pilot.py','src/wildfire_rl/separate_clip_rl.py')}
    guard=dict(plan_sha256=sha(PLAN),source_sha256=sources,parent_guard=parent['guard'],centered_guard=previous['guard'])
    return plan,parent,diagnosis,guard


def assert_guard(guard):
    result=context()
    if result[-1]!=guard:raise ValueError('numerical source/plan/runtime/artifacts changed')
    return result[:3]


def make_env(backend,sid):return old.make_env(PARENT,backend,sid)


def rollout(env,sequence=None,model=None):
    return centered.rollout(env,sequence=sequence,model=model,centered=False)


def probe(job):
    folder,be,seed,guard=job;out=Path(folder);plan,parent,diagnosis=assert_guard(guard)
    schedule=case_schedule(plan['fitting_cases'],seed)
    env=LazyTrainingCases(schedule,lambda sid:make_env(be,sid));model=create_model(env,seed=seed,settings=plan['ppo'])
    run=next(r for r in parent['runs'] if r['backend']==be and r['seed']==seed)
    if policy_digest(model)!=run['initial_policy_digest']:raise ValueError('fresh initial policy differs')
    data,rows=collect_initial(model)
    with np.load(SIGNAL/('probe-%s-%d.npz'%(be,seed)),allow_pickle=False) as previous:
        for key,value in data.items():np.testing.assert_array_equal(value,previous[key])
    if rows!=read(PARENT/('job-%s-%d'%(be,seed))/'training.json')[:16]:raise ValueError('native first16 rows differ')
    initial={k:v.detach().clone() for k,v in model.policy.state_dict().items()}
    disposable=load_policy_arrays(PARENT/('job-%s-%d'%(be,seed))/'policy-0.npz',
        old.contract(parent['guard'],be,seed,0,parent['plan']))
    metrics=gradient_probe(disposable,data,'separate')
    model.n_epochs=1;model.train()
    if policy_digest(model)!=policy_digest(disposable) or len(model.clip_history)!=1:
        raise ValueError('separate Adam update differs from independent probe')
    expected=next(x for x in diagnosis['probes'] if x['backend']==be and x['seed']==seed)
    expected=next(x for x in expected['modes'] if x['reward']=='original' and x['clipping']=='separate')
    for key in ('policy_loss','value_loss','entropy_loss','total_loss','adam_eps','learning_rate'):
        np.testing.assert_allclose(metrics[key],expected[key],atol=1e-10,rtol=1e-8)
    delta=parameter_delta(initial,model)
    for group in ('actor','critic'):
        for key,value in metrics[group].items():np.testing.assert_allclose(value,expected[group][key],atol=1e-10,rtol=1e-8)
        np.testing.assert_allclose(delta[group]['delta_l2'],metrics[group]['parameter_step_l2'],atol=1e-10,rtol=1e-8)
    name='probe-%s-%d'%(be,seed);np.savez_compressed(out/(name+'.npz'),**data);env.close()
    result=dict(backend=be,seed=seed,status='PASS',initial_weights='PASS',original_first16_exact='PASS',
        independent_first_adam_exact='PASS',gradient_metrics=metrics,clip=model.clip_history[0],rows=rows,
        arrays_sha256=sha(out/(name+'.npz')),disposable_weights_saved=False)
    write(out/(name+'.json'),result);return result


def preflight(out):
    plan,parent,diagnosis,guard=context();out.mkdir(parents=True,exist_ok=False);write(out/'guard.json',guard);started=time.monotonic()
    jobs=[(str(out),be,seed,guard) for be in ('simfire','ca') for seed in plan['model_seeds']]
    with ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('spawn'),initializer=old.setup_worker) as pool:
        probes=list(pool.map(probe,jobs))
    assert_guard(guard);files={p.name:sha(p) for p in out.iterdir() if p.name.startswith('probe-')}
    result=dict(status='PASS',guard=guard,probes=probes,fresh_native_steps=96,fresh_native_episodes=24,
        first_updates=6,original_native_tree_reused='TASK043guarded132paths',
        paired_physics_invariance_reused='TASK045guarded32pairedpaths',files=files,seconds=time.monotonic()-started)
    write(out/'preflight.json',result);print('PREFLIGHT PASS',result['seconds'],flush=True)


def checked_preflight(out,guard):return centered.checked_preflight(out,guard)


def contract(guard,backend,seed,stage,plan):
    return dict(guard=guard,backend=backend,seed=seed,checkpoint_steps=stage,
        architecture=plan['architecture'],reward=plan['control']['reward']['version'],clipping=CLIPPING_VERSION)


class LearningCallback(BaseCallback):
    def __init__(self,jobdir,guard,backend,seed,plan):
        super().__init__();self.jobdir=jobdir;self.guard=guard;self.backend=backend;self.seed=seed
        self.plan=plan;self.rows=[];self.started=time.time();self.first_rollout=None

    def _on_step(self):
        if (self.jobdir.parent/'stop.json').exists():raise RuntimeError('global stop requested')
        info=self.locals['infos'][0];k=(self.num_timesteps-1)%4
        if info['invalid_action'] or not np.isfinite(self.locals['rewards']).all():raise ValueError('illegal/nonfinite PPO step')
        if info['remaining_budget'] not in (0,1) or bool(self.locals['dones'][0])!=(k==3):raise ValueError('budget/horizon mismatch')
        self.rows.append(dict(step=self.num_timesteps,scenario_id=info['scenario_id'],action=info['effective_action'],
            reward=float(self.locals['rewards'][0]),done=bool(self.locals['dones'][0]),
            remaining_budget=info['remaining_budget'],charged_damage_cells=info['charged_damage_cells']))
        if self.num_timesteps%16==0:
            write(self.jobdir/'status.json',dict(phase='training',pid=os.getpid(),steps=self.num_timesteps,target=512,
                clip_updates=len(self.model.clip_history),first_rollout=self.first_rollout,
                updated_unix=time.time(),elapsed_seconds=time.time()-self.started))
        return True

    def _on_rollout_end(self):
        if self.num_timesteps!=16:return
        if self.model._n_updates!=0 or self.model.policy.optimizer.state:raise ValueError('parity must precede optimizer update')
        b=self.model.rollout_buffer
        data={key:np.asarray(getattr(b,key)).reshape((16,)+tuple(getattr(b,key).shape[2:])).copy()
            for key in ('observations','actions','rewards','values','log_probs','advantages','returns','action_masks','episode_starts')}
        data['actions']=data['actions'].reshape(16)
        with np.load(SIGNAL/('probe-%s-%d.npz'%(self.backend,self.seed)),allow_pickle=False) as probe:
            for key,value in data.items():np.testing.assert_array_equal(value,probe[key])
        if self.rows!=read(PARENT/('job-%s-%d'%(self.backend,self.seed))/'training.json')[:16]:raise ValueError('native first16 transition differs')
        np.savez_compressed(self.jobdir/'first-rollout.npz',**data)
        self.first_rollout=dict(status='PASS',all_raw_buffer_fields_exact=True,before_optimizer_update=True,
                               sha256=sha(self.jobdir/'first-rollout.npz'))
        write(self.jobdir/'first-rollout.json',self.first_rollout)


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
        if not 0<len(model.clip_history)<=64:raise ValueError('optimizer update budget differs')
        write(jobdir/'clipping.json',model.clip_history)
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
            gradient_clip_updates=len(model.clip_history),clipping_receipt_sha256=sha(jobdir/'clipping.json'),
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
    # Reuse frozen descriptive arithmetic; rename the candidate explicitly.
    result=centered.summarize(plan,results,diagnosis);previous=read(CENTERED/'analysis.json')
    ids=plan['evaluation_cases'];seeds=plan['model_seeds'];oldrows={(x['backend'],x['seed'],r['scenario_id']):r
        for x in previous['runs'] for r in x['rows'] if r['checkpoint']==512}
    joint=np.array([sid in result['joint_positive_ids'] for sid in ids],bool)
    for be,item in result['backends'].items():
        item['metrics']['separate512']=item['metrics'].pop('centered512')
        item['separate_minus_reference_pp']=item.pop('centered_minus_reference_pp')
        n=np.array([old.lookup(be,sid,[0,0,0,0])['noop_damage_cells'] for sid in ids],float)
        candidate=np.array([[next(r for x in results if x['backend']==be and x['seed']==seed for r in x['rows']
            if r['scenario_id']==sid and r['checkpoint']==512)['charged_damage_cells'] for sid in ids] for seed in seeds],float)
        cost=np.array([[oldrows[be,seed,sid]['charged_damage_cells'] for sid in ids] for seed in seeds],float)
        raw=np.array([[oldrows[be,seed,sid]['raw_damage_cells'] for sid in ids] for seed in seeds],float)
        item['metrics']['centered512']=method_metrics(cost,n,joint,raw)
        item['separate_minus_reference_pp']['centered512']=compare_costs(candidate,cost,n,joint)
    result['phase_exit']='Last optimizer screen complete; TASK047closure/integration review next regardless of continuation signal; no automatic larger training'
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
