#!/usr/bin/env python3
"""Frozen ADR-049 contract/native/train/replay checks; never a learning benchmark."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.local/matplotlib'))
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import numpy as np
import torch
from stable_baselines3.common.callbacks import BaseCallback
from wildfire_rl.common_control import CommonControlEnv,CyclingCases,encoded_observation
from wildfire_rl.common_control_rl import create_model,save_policy_arrays,load_policy_arrays,policy_digest,PPO_SETTINGS
from wildfire_rl.feds_simfire_env import FedsSimFireEnv
from wildfire_rl.feds_observation_v2 import SimFireObservationV2
from wildfire_rl.feds_simfire_setup import load_case_inputs,SimFireParams,WEATHER,INPUT_ROOT
from wildfire_rl.line_damage import score_line_damage
from run_paired_simulators import bridge,SOURCES

PLAN=ROOT/'configs/frozen/common-ppo-smoke-v1.json'
ARCHIVE=ROOT/'.local/expanded-v1'
TABLE=ROOT/'.local/b1-cases'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def context():
    plan=json.loads(PLAN.read_text())
    if sha(WEATHER)!=plan['weather_sha256'] or sha(TABLE/'table-98.json')!=plan['table_sha256']:
        raise ValueError('frozen weather/table mismatch')
    if plan['ppo']!=PPO_SETTINGS:raise ValueError('PPO settings differ from plan')
    sources=set(SOURCES+['scripts/smoke_common_ppo.py','src/wildfire_rl/common_control.py',
        'src/wildfire_rl/common_control_rl.py','src/wildfire_rl/feds_b1_learning.py',
        'src/wildfire_rl/simfire_initial_state.py','src/wildfire_rl/simfire_timebase.py'])
    runtime=dict(python=platform.python_version(),packages={k:importlib.metadata.version(k) for k in (
        'numpy','torch','stable-baselines3','sb3-contrib','simfire','gymnasium','scipy')})
    if runtime['packages']!={'numpy':'1.26.4','torch':'2.3.1','stable-baselines3':'2.7.1',
                            'sb3-contrib':'2.7.1','simfire':'2.0.1','gymnasium':'1.1.1','scipy':'1.13.1'}:
        raise ValueError('use same pinned runtime for both backends')
    return plan,dict(plan_sha256=sha(PLAN),source_sha256={k:sha(ROOT/k) for k in sorted(sources)},
                     runtime=runtime,source_commit=subprocess.check_output(
                         ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())


def native_env(backend,sid):
    inputs=load_case_inputs(sid,split='train',weather_path=WEATHER,input_root=INPUT_ROOT)
    if backend=='ca':return bridge(inputs,0),inputs
    return SimFireObservationV2(FedsSimFireEnv(split='train',scenario_ids=[sid],budgets=(1,),
        max_budget=4,line_placement='front_edge',weather_observation='previous',
        sim_params=SimFireParams(wind_adjustment_factor=.1),weather_path=WEATHER,input_root=INPUT_ROOT)),inputs


def references(plan,out):
    cases={'simfire':{},'ca':{}};records=[];initial_obs={}
    for backend in cases:
        for sid in plan['cases']:
            env,inputs=native_env(backend,sid)
            archived=json.loads((ARCHIVE/backend/(sid+'.json')).read_text())
            archived_npz=ARCHIVE/backend/(sid+'.npz')
            if sha(archived_npz)!=archived['npz_sha256']:raise ValueError('archive bytes changed')
            # The input receipt is also bound to the original TRAIN action table.
            original=json.loads((TABLE/(sid+'.json')).read_text())
            if inputs['receipt_sha256']!=original['input_receipt_sha256']:
                raise ValueError('input receipt changed')
            raw,_=env.reset();initial=env.unwrapped.cumulative_burned.copy()
            np.testing.assert_array_equal(initial,inputs['scar']|inputs['front'])
            initial_obs[backend,sid]=raw,env.action_masks().copy()
            trajectory=[initial]
            for k in range(4):
                _,_,done,trunc,_=env.step(0)
                assert not trunc and done==(k==3)
                trajectory.append(env.unwrapped.cumulative_burned.copy())
            trajectory=np.stack(trajectory)
            with np.load(archived_npz,allow_pickle=False) as old:
                np.testing.assert_array_equal(initial,old['initial'])
                np.testing.assert_array_equal(trajectory,old['simfire' if backend=='simfire' else 'ca0'])
            np.savez_compressed(out/('reference-'+backend+'-'+sid+'.npz'),initial=initial,burned=trajectory)
            cases[backend][sid]=CommonControlEnv(env,trajectory[-1])
            records.append(dict(backend=backend,scenario_id=sid,input_receipt_sha256=inputs['receipt_sha256'],
                                archive_npz_sha256=sha(archived_npz),whole_noop_trajectory='PASS',
                                noop_new_cells=int((trajectory[-1]&~initial).sum())))
            print('reference PASS',backend,sid,flush=True)
    for sid in plan['cases']:
        a,ma=initial_obs['simfire',sid];b,mb=initial_obs['ca',sid]
        if set(a)!=set(b):raise ValueError('v2 keys differ')
        for key in a:np.testing.assert_array_equal(a[key],b[key])
        np.testing.assert_array_equal(encoded_observation(a),encoded_observation(b))
        np.testing.assert_array_equal(ma,mb)
    return cases,records


def rollout(env,sequence=None,model=None):
    obs,_=env.reset();initial=env.unwrapped.cumulative_burned.copy()
    burned=[initial];lines=[np.zeros(initial.shape,bool)];features=[];masks=[];logits=[];rows=[]
    for k in range(4):
        mask=env.action_masks();features.append(obs.copy());masks.append(mask.copy())
        if model is None:action=int(sequence[k])
        else:
            tensor,_=model.policy.obs_to_tensor(obs)
            with torch.no_grad():
                logits.append(model.policy.get_distribution(tensor,action_masks=mask).distribution.logits.cpu().numpy()[0])
            action=int(model.predict(obs,action_masks=mask,deterministic=True)[0])
            if not mask[action]:raise ValueError('policy selected invalid action')
        obs,reward,done,trunc,info=env.step(action)
        assert done==(k==3) and not trunc
        if not env.observation_space.contains(obs):raise ValueError('observation outside contract')
        burned.append(env.unwrapped.cumulative_burned.copy());lines.append(env.ledger.line.copy())
        rows.append(dict(step=k,requested_action=action,effective_action=info['effective_action'],
                         invalid=bool(info['invalid_action']),reward=reward,remaining_budget=info['remaining_budget'],
                         charged_damage_cells=info['charged_damage_cells']))
    score=score_line_damage(initial,burned[-1],env._noop_final,lines[-1])
    total=sum(r['reward'] for r in rows);invalids=sum(r['invalid'] for r in rows)
    np.testing.assert_allclose(total,-score['charged_damage_cells']/100.-invalids*.01,atol=1e-12,rtol=0)
    return dict(rows=rows,score=score,return_=total,invalid_requests=invalids),dict(
        initial=initial,burned=np.stack(burned),line=np.stack(lines),
        features=np.array(features),masks=np.array(masks),logits=np.array(logits))


class TrainingReceipt(BaseCallback):
    def __init__(self):super().__init__();self.rows=[]

    def _on_step(self):
        info=self.locals['infos'][0]
        if info['invalid_action']:raise ValueError('masked PPO requested invalid action')
        if not np.isfinite(self.locals['rewards']).all():raise ValueError('nonfinite reward')
        self.rows.append(dict(step=self.num_timesteps,scenario_id=info['scenario_id'],
            action=info['effective_action'],reward=float(self.locals['rewards'][0]),
            done=bool(self.locals['dones'][0]),remaining_budget=info['remaining_budget'],
            charged_damage_cells=info['charged_damage_cells']))
        return True


def execute(out):
    plan,guard=context()
    out.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    started=time.monotonic();write(out/'guard.json',guard)
    cases,refs=references(plan,out);native=[]
    for backend,byid in cases.items():
        for sid,env in byid.items():
            for i,seq in enumerate(plan['native_checks']['sequences']):
                record,arrays=rollout(env,sequence=seq)
                # Fresh wrapper reward must agree with the independent original table.
                folder=TABLE if backend=='simfire' else ROOT/'.local/paired-v1-final/cases'
                archive=json.loads((folder/(sid+'.json')).read_text())
                actions=[r['effective_action'] for r in record['rows']]
                expected=[r for r in archive['outcomes'] if r['effective_actions']==actions]
                if not expected:raise ValueError('missing original action path')
                for row in expected:
                    for key in record['score']:
                        if row[key]!=record['score'][key]:raise ValueError('original score mismatch: '+key)
                name='native-%s-%s-%d.npz'%(backend,sid,i)
                np.savez_compressed(out/name,**arrays)
                native.append(dict(backend=backend,scenario_id=sid,sequence=seq,arrays=name,
                                   arrays_sha256=sha(out/name),**record))
            print('native PASS',backend,sid,flush=True)
    write(out/'native.json',dict(references=refs,initial_v2_features_masks_equal='PASS',paths=native))
    runs=[];initial_hashes={}
    for backend,byid in cases.items():
        for seed in plan['model_seeds']:
            schedule=CyclingCases(byid);model=create_model(schedule,seed=seed,settings=plan['ppo'])
            initial_hash=policy_digest(model)
            if seed in initial_hashes and initial_hashes[seed]!=initial_hash:raise ValueError('initial PPO weights differ')
            initial_hashes[seed]=initial_hash;callback=TrainingReceipt();t=time.monotonic()
            model.learn(plan['steps_per_run'],callback=callback)
            completed=[r['scenario_id'] for r in callback.rows if r['done']]
            expected=[plan['cases'][k%3] for k in range(16)]
            if completed!=expected or model.num_timesteps!=64:raise ValueError('training schedule mismatch')
            logs={k:float(v) for k,v in model.logger.name_to_value.items() if isinstance(v,(float,int,np.number))}
            if not all(np.isfinite(v) for v in logs.values()):raise ValueError('nonfinite training diagnostic')
            if policy_digest(model)==initial_hash:raise ValueError('no parameter update')
            contract=dict(guard=guard,backend=backend,seed=seed,observation='v2/terrain536',
                          reward=plan['reward']['version'],architecture=plan['architecture'])
            path=out/('policy-%s-%d.npz'%(backend,seed));receipt=save_policy_arrays(model,path,contract)
            restored=load_policy_arrays(path,contract);replays=[]
            for sid,env in byid.items():
                first,aa=rollout(env,model=model);second,bb=rollout(env,model=restored)
                if first!=second:raise ValueError('checkpoint replay row mismatch')
                for key in aa:np.testing.assert_array_equal(aa[key],bb[key])
                name='policy-replay-%s-%d-%s.npz'%(backend,seed,sid)
                np.savez_compressed(out/name,**aa)
                replays.append(dict(scenario_id=sid,arrays=name,arrays_sha256=sha(out/name),
                                    exact_checkpoint_replay='PASS',**first))
            result=dict(backend=backend,seed=seed,steps=model.num_timesteps,completed_episodes=len(completed),
                        schedule=completed,initial_policy_digest=initial_hash,final_policy_digest=policy_digest(model),
                        checkpoint_sha256=receipt['sha256'],training=callback.rows,diagnostics=logs,
                        replays=replays,seconds=time.monotonic()-t)
            runs.append(result);write(out/('run-%s-%d.json'%(backend,seed)),result)
            print('PPO/replay PASS',backend,seed,result['seconds'],flush=True)
    for byid in cases.values():
        for env in byid.values():env.close()
    result=dict(schema_version='common-ppo-technical/1.0',task='TASK-040 B.1',plan=plan,guard=guard,
                status='PASS',scope='Technical TRAIN smoke only; no learning ranking or physical validation',
                references=refs,native_paths=native,runs=runs,
                initial_observations_and_masks='PASS',initial_weights_paired='PASS',
                nice=os.getpriority(os.PRIO_PROCESS,0),numeric_threads=1,seconds=time.monotonic()-started)
    write(out/'summary.json',result)
    print('ALL PASS',result['seconds'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if os.getpriority(os.PRIO_PROCESS,0)<19:raise RuntimeError('run with nice -n 19')
    execute(args.out)
