#!/usr/bin/env python3
"""ADR-051 guarded preflight and detached-capable three-worker TRAIN pilot."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import json
import multiprocessing
import os
from pathlib import Path
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):
    os.environ[k]='1'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.local/matplotlib'))
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import numpy as np
import torch
from stable_baselines3.common.callbacks import BaseCallback
import smoke_common_ppo as common
from wildfire_rl.common_control import CommonControlEnv,encoded_observation
from wildfire_rl.common_control_rl import create_model,save_policy_arrays,load_policy_arrays,policy_digest
from wildfire_rl.feds_b1 import action_sequences,policy_sequence
from wildfire_rl.feds_observation_dataset import load_observation_case,SHAPES
from wildfire_rl.feds_repaired_policies import make_repaired_heuristic
from wildfire_rl.feds_simfire_setup import load_case_inputs,MANIFEST,WEATHER
from wildfire_rl.paired_ppo_learning import (sha,validate_design,case_schedule,LazyTrainingCases,
    summarize_learning,completed_job)

PLAN=ROOT/'configs/frozen/paired-ppo-learning-v1.json'
EXPANDED=ROOT/'configs/frozen/expanded-observed-growth-v1.json'
OBS=ROOT/'.local/repair-observations'
CA_TABLE=ROOT/'.local/paired-v1-final/cases'


def setup_worker():
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    if os.getpriority(os.PRIO_PROCESS,0)<19:raise RuntimeError('worker nice19 required')


def read(path):return json.loads(Path(path).read_text())


def write(path,value):
    path=Path(path);tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def context():
    plan=read(PLAN);validate_design(plan);expanded=read(EXPANDED)
    expected=[x for x in expanded['cases'] if x not in expanded['previous_cases']]
    if plan['fitting_cases']!=expected or plan['evaluation_cases']!=expanded['previous_cases']:
        raise ValueError('frozen45/16 selection changed')
    sg=plan['split_guards']
    for path,key in [(MANIFEST,'cohort_sha256'),(EXPANDED,'expanded_plan_sha256'),
        (WEATHER,'weather_sha256'),(common.TABLE/'table-98.json','sf_table_sha256'),
        (OBS/'dataset-98.json','v2_dataset_sha256')]:
        if sha(path)!=sg[key]:raise ValueError('frozen input mismatch: '+str(path))
    _,old=common.context()
    sources=dict(old['source_sha256'])
    for f in ('scripts/run_paired_ppo_learning.py','src/wildfire_rl/paired_ppo_learning.py',
        'src/wildfire_rl/feds_b1.py','src/wildfire_rl/feds_heuristics.py',
        'src/wildfire_rl/feds_repaired_policies.py','src/wildfire_rl/feds_observation_dataset.py'):
        sources[f]=sha(ROOT/f)
    return plan,dict(plan_sha256=sha(PLAN),source_sha256=sources,runtime=old['runtime'],
                     source_commit=old['source_commit'])


def assert_guard(guard):
    plan,current=context()
    # Documentation/publication commits may advance without changing numerical code.
    if any(current[k]!=guard[k] for k in ('plan_sha256','source_sha256','runtime')):
        raise ValueError('numerical source/plan/runtime changed')
    return plan


def table(backend,sid):
    folder=common.TABLE if backend=='simfire' else CA_TABLE
    if backend=='simfire' and sha(folder/(sid+'.json'))!=read(EXPANDED)['sf_case_json_sha256'][sid]:
        raise ValueError('original SimFire case JSON changed')
    record=read(folder/(sid+'.json'));npz=folder/(sid+'.npz')
    if sha(npz)!=record.get('npz_sha256',record.get('mask_file_sha256')):
        raise ValueError('original action mask archive changed')
    return record,npz


def lookup(backend,sid,actions):
    record,_=table(backend,sid)
    matches=[r for r in record['outcomes'] if r['effective_actions']==list(actions)]
    if not matches:raise ValueError('missing B1 action path')
    for key in ('noop_damage_cells','raw_damage_cells','charged_damage_cells'):
        if len({r[key] for r in matches})!=1:raise ValueError('ambiguous B1 outcome')
    return dict(matches[0])


def reference(out,backend,sid):
    with np.load(out/'references'/(backend+'-'+sid+'.npz'),allow_pickle=False) as a:
        return a['burned'][-1].copy()


def make_env(out,backend,sid):
    env,_=common.native_env(backend,sid)
    return CommonControlEnv(env,reference(out,backend,sid))


def native_tree(job):
    out,backend,sid,guard=job;out=Path(out);assert_guard(guard)
    env=make_env(out,backend,sid);record,npz=table(backend,sid);rows=[]
    started=time.monotonic()
    with np.load(npz,allow_pickle=False) as old:
        for index,sequence in enumerate(action_sequences()):
            actual,arrays=common.rollout(env,sequence=sequence)
            actions=[r['effective_action'] for r in actual['rows']]
            # Nonfuel gating may collapse a legacy table path into no-op.
            match=next(i for i,r in enumerate(record['outcomes']) if r['effective_actions']==actions)
            np.testing.assert_array_equal(arrays['burned'][-1],old['agent_burned'][match])
            np.testing.assert_array_equal(arrays['line'][-1],old['line_cells'][match])
            expected=lookup(backend,sid,actions)
            for key,value in actual['score'].items():
                if expected[key]!=value:raise ValueError('native tree score mismatch')
            rows.append(dict(sequence=list(sequence),effective_actions=actions,score=actual['score'],
                             return_=actual['return_'],invalid_requests=actual['invalid_requests']))
    env.close();result=dict(backend=backend,scenario_id=sid,paths=rows,seconds=time.monotonic()-started,status='PASS')
    write(out/('tree-'+backend+'-'+sid+'.json'),result);return result


def preflight(out):
    plan,guard=context();out.mkdir(parents=True,exist_ok=False)
    (out/'references').mkdir();(out/'evaluation').mkdir();write(out/'guard.json',guard)
    inputs=[];started=time.monotonic()
    for sid in plan['fitting_cases']+plan['evaluation_cases']:
        data=load_case_inputs(sid,split='train')
        if data['receipt_sha256']!=plan['input_receipt_sha256'][sid]:raise ValueError('input receipt mismatch')
        for backend in ('simfire','ca'):
            p=common.ARCHIVE/backend/(sid+'.npz');r=read(p.with_suffix('.json'))
            if sha(p)!=r['npz_sha256']:raise ValueError('no-op archive changed')
            for name,h in r['guard']['common']['source_sha256'].items():
                if sha(ROOT/name)!=h:raise ValueError('frozen physics/source mismatch')
            with np.load(p,allow_pickle=False) as a:
                initial=a['initial'];burned=a['simfire' if backend=='simfire' else 'ca0']
                np.testing.assert_array_equal(initial,data['scar']|data['front'])
                if (burned[:-1]&~burned[1:]).any():raise ValueError('archived no-op damage lost')
                np.savez_compressed(out/'references'/(backend+'-'+sid+'.npz'),initial=initial,burned=burned)
        inputs.append(dict(scenario_id=sid,receipt_sha256=data['receipt_sha256']))
    dataset=read(OBS/'dataset-98.json');items={r['scenario_id']:r for r in dataset['cases']};baselines=[]
    for sid in plan['evaluation_cases']:
        _,sf,m=load_observation_case(OBS,items[sid],dataset['settings'])
        ca_record,ca_path=table('ca',sid)
        with np.load(ca_path,allow_pickle=False) as a:
            ca=[{key:a[key][k].copy() for key in SHAPES} for k in range(4)]
            cm=a['masks'].copy().astype(bool)
        for key in sf[0]:np.testing.assert_array_equal(sf[0][key],ca[0][key])
        np.testing.assert_array_equal(m['burnable_lines'][0],cm[0])
        for backend,observations,masks in [('simfire',sf,m['burnable_lines']),('ca',ca,cm)]:
            encoded=np.stack([encoded_observation(o) for o in observations])
            np.savez_compressed(out/'evaluation'/(backend+'-'+sid+'.npz'),features=encoded,masks=masks)
            for method in plan['heuristics']:
                actions=policy_sequence(make_repaired_heuristic(method),observations,masks)
                baselines.append(dict(backend=backend,scenario_id=sid,method=method,
                                      actions=list(actions),**lookup(backend,sid,actions)))
    jobs=[(str(out),b,sid,guard) for b in ('simfire','ca') for sid in plan['preflight']['full_native_tree_cases']]
    with ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('spawn'),initializer=setup_worker) as pool:
        trees=list(pool.map(native_tree,jobs))
    files={str(p.relative_to(out)):sha(p) for folder in ('references','evaluation') for p in (out/folder).iterdir()}
    result=dict(status='PASS',guard=guard,input_cases=inputs,baselines=baselines,
        trees=trees,seconds=time.monotonic()-started,files=files,initial_v2_features_masks_equal='PASS')
    write(out/'preflight.json',result);print('PREFLIGHT PASS',result['seconds'],flush=True)


def checked_preflight(out,guard):
    r=read(out/'preflight.json')
    if r['status']!='PASS' or r['guard']!=guard:raise ValueError('preflight guard mismatch')
    for name,h in r['files'].items():
        if sha(out/name)!=h:raise ValueError('preflight cache changed')
    return r


def contract(guard,backend,seed,stage,plan):
    return dict(guard=guard,backend=backend,seed=seed,checkpoint_steps=stage,
                architecture=plan['architecture'],reward=plan['control']['reward']['version'])


class LearningCallback(BaseCallback):
    def __init__(self,jobdir,guard,backend,seed,plan):
        super().__init__();self.jobdir=jobdir;self.guard=guard;self.backend=backend;self.seed=seed
        self.plan=plan;self.rows=[];self.started=time.time();self.saved=[]

    def save(self,stage):
        save_policy_arrays(self.model,self.jobdir/('policy-%d.npz'%stage),
                           contract(self.guard,self.backend,self.seed,stage,self.plan))
        self.saved.append(stage)

    def _on_rollout_start(self):
        if self.num_timesteps==512 and 512 not in self.saved:self.save(512)

    def _on_step(self):
        if (self.jobdir.parent/'stop.json').exists():raise RuntimeError('another job failed; stopping all workers')
        info=self.locals['infos'][0]
        if info['invalid_action'] or not np.isfinite(self.locals['rewards']).all():raise ValueError('illegal/nonfinite training')
        if info['remaining_budget'] not in (0,1):raise ValueError('invalid training budget')
        k=(self.num_timesteps-1)%4
        if bool(self.locals['dones'][0])!=(k==3):raise ValueError('training horizon mismatch')
        self.rows.append(dict(step=self.num_timesteps,scenario_id=info['scenario_id'],action=info['effective_action'],
            reward=float(self.locals['rewards'][0]),done=bool(self.locals['dones'][0]),
            charged_damage_cells=info['charged_damage_cells'],remaining_budget=info['remaining_budget']))
        if self.num_timesteps%64==0:
            write(self.jobdir/'status.json',dict(phase='training',pid=os.getpid(),steps=self.num_timesteps,
                target=self.plan['training_steps'],saved=self.saved,updated_unix=time.time(),elapsed_seconds=time.time()-self.started))
        return True


def train_job(job):
    out,backend,seed,guard=job;out=Path(out);plan=assert_guard(guard)
    jobdir=out/('job-%s-%d'%(backend,seed));jobguard=dict(common=guard,backend=backend,seed=seed)
    if completed_job(jobdir,jobguard):return read(jobdir/'result.json')
    if (out/'stop.json').exists():raise RuntimeError('run has a recorded stop condition')
    # A partial NPZ is not a resumable optimizer. Preserve it and require a new attempt.
    jobdir.mkdir(exist_ok=False);started=time.monotonic()
    write(jobdir/'status.json',dict(phase='starting',pid=os.getpid(),updated_unix=time.time()))
    try:
        schedule=case_schedule(plan['fitting_cases'],seed)
        env=LazyTrainingCases(schedule,lambda sid:make_env(out,backend,sid))
        model=create_model(env,seed=seed,settings=plan['ppo']);initial=policy_digest(model)
        cb=LearningCallback(jobdir,guard,backend,seed,plan);cb.model=model;cb.save(0)
        model.learn(plan['training_steps'],callback=cb);cb.save(2048)
        expected=[schedule[k%len(schedule)] for k in range(512)]
        if [r['scenario_id'] for r in cb.rows if r['done']]!=expected:raise ValueError('completed case schedule mismatch')
        if set(cb.saved)!={0,512,2048} or model.num_timesteps!=2048:raise ValueError('checkpoint/step count mismatch')
        diagnostics={k:float(v) for k,v in model.logger.name_to_value.items() if isinstance(v,(float,int,np.number))}
        if not all(np.isfinite(v) for v in diagnostics.values()):raise ValueError('nonfinite learning diagnostic')
        if policy_digest(model)==initial:raise ValueError('no learning update')
        env.close();write(jobdir/'training.json',cb.rows);rows=[]
        for stage in plan['checkpoints']:
            write(jobdir/'status.json',dict(phase='evaluating',checkpoint=stage,pid=os.getpid(),updated_unix=time.time()))
            restored=load_policy_arrays(jobdir/('policy-%d.npz'%stage),contract(guard,backend,seed,stage,plan))
            if stage==2048 and policy_digest(restored)!=policy_digest(model):raise ValueError('final restored weights differ')
            for sid in plan['evaluation_cases']:
                if (out/'stop.json').exists():raise RuntimeError('another job failed; stopping evaluation')
                with np.load(out/'evaluation'/(backend+'-'+sid+'.npz'),allow_pickle=False) as a:
                    features=a['features'].copy();masks=a['masks'].copy()
                def policy(obs,mask):
                    action=int(restored.predict(obs,action_masks=mask,deterministic=True)[0])
                    if not mask[action]:raise ValueError('invalid evaluation action')
                    return action
                actions=policy_sequence(policy,features,masks);score=lookup(backend,sid,actions)
                row=dict(backend=backend,scenario_id=sid,seed=seed,checkpoint=stage,actions=list(actions),**score)
                if stage==2048:
                    native=make_env(out,backend,sid);actual,arrays=common.rollout(native,model=restored);native.close()
                    if [r['effective_action'] for r in actual['rows']]!=list(actions):raise ValueError('native policy actions differ')
                    for key,value in actual['score'].items():
                        if score[key]!=value:raise ValueError('native final policy score differs')
                    rec,path=table(backend,sid);idx=next(i for i,r in enumerate(rec['outcomes']) if r['effective_actions']==list(actions))
                    with np.load(path,allow_pickle=False) as old:
                        np.testing.assert_array_equal(arrays['burned'][-1],old['agent_burned'][idx])
                        np.testing.assert_array_equal(arrays['line'][-1],old['line_cells'][idx])
                    name='native-'+sid+'.npz';np.savez_compressed(jobdir/name,**arrays)
                    row.update(native_whole_masks='PASS',arrays=name,arrays_sha256=sha(jobdir/name),native_return=actual['return_'])
                rows.append(row)
        assert_guard(guard)
        result=dict(backend=backend,seed=seed,guard=jobguard,initial_policy_digest=initial,final_policy_digest=policy_digest(model),
                    steps=2048,completed_episodes=512,schedule=expected,diagnostics=diagnostics,
                    rows=rows,seconds=time.monotonic()-started,nice=os.getpriority(os.PRIO_PROCESS,0),status='PASS')
        write(jobdir/'result.json',result)
        write(jobdir/'status.json',dict(phase='complete',steps=2048,pid=os.getpid(),updated_unix=time.time()))
        files={p.name:sha(p) for p in jobdir.iterdir() if p.is_file() and p.name!='status.json'}
        write(jobdir/'done.json',dict(guard=jobguard,files=files,status='PASS'));return result
    except BaseException:
        write(out/'stop.json',dict(backend=backend,seed=seed,error=traceback.format_exc(),updated_unix=time.time()))
        write(jobdir/'error.json',dict(error=traceback.format_exc(),pid=os.getpid(),updated_unix=time.time()))
        write(jobdir/'status.json',dict(phase='failed',pid=os.getpid(),updated_unix=time.time()))
        raise


def run(out):
    plan,current=context();guard=read(out/'guard.json');assert_guard(guard);pre=checked_preflight(out,guard)
    # O_EXCL prevents two coordinators from launching the same study.
    lock=out/'coordinator.lock'
    with lock.open('x') as f:f.write(str(os.getpid()))
    write(out/'status.json',dict(phase='running',pid=os.getpid(),started_unix=time.time(),jobs=6,workers=3))
    jobs=[(str(out),be,seed,guard) for be in ('simfire','ca') for seed in plan['model_seeds']]
    results=[]
    try:
        with ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('spawn'),initializer=setup_worker) as pool:
            futures=[pool.submit(train_job,j) for j in jobs]
            for future in as_completed(futures):
                result=future.result();results.append(result)
                write(out/'status.json',dict(phase='running',pid=os.getpid(),completed=len(results),jobs=6,updated_unix=time.time()))
        initial={}
        for r in results:
            initial.setdefault(r['seed'],r['initial_policy_digest'])
            if initial[r['seed']]!=r['initial_policy_digest']:raise ValueError('paired initial weights differ')
        rows=[row for r in results for row in r['rows']]
        summary=summarize_learning(rows,pre['baselines'],plan['evaluation_cases'],plan['model_seeds'])
        write(out/'analysis.json',dict(guard=guard,plan=plan,summary=summary,runs=results,status='PASS'))
        write(out/'status.json',dict(phase='complete',completed=6,jobs=6,pid=os.getpid(),updated_unix=time.time()))
    except BaseException:
        write(out/'error.json',dict(error=traceback.format_exc(),pid=os.getpid(),updated_unix=time.time()))
        write(out/'status.json',dict(phase='failed',completed=len(results),pid=os.getpid(),updated_unix=time.time()))
        raise
    finally:lock.unlink(missing_ok=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['preflight','run'])
    p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    if os.getpriority(os.PRIO_PROCESS,0)<19:raise RuntimeError('nice19 required')
    if args.command=='preflight':preflight(args.out.resolve())
    else:run(args.out.resolve())
