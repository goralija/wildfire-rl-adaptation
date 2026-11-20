#!/usr/bin/env python3
"""ADR-041: fixed TRAIN demonstrations, final BC/PPO and descriptive development only."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from functools import partial
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'

import gymnasium
import numpy as np
import scipy
import torch
import sb3_contrib
import stable_baselines3
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import SubprocVecEnv

from wildfire_rl.ca_controlled import CAObservationV2, observed_policy
from wildfire_rl.ca_learning import (CATrainingEnv, EpisodeBank, encode_observation,
    discounted_returns, learning_contrast, validate_learning_plan)
from wildfire_rl.ca_learning_rl import create_model, save_policy_arrays, load_policy_arrays
from wildfire_rl.synthetic_env import Curriculum, SyntheticSuppressionEnv, CELL_AREA_HA
from run_ca_controlled_pilot import world_hash, array_hash

SOURCES = ['src/wildfire_rl/synthetic_ca.py','src/wildfire_rl/synthetic_env.py',
    'src/wildfire_rl/synthetic_heuristics.py','src/wildfire_rl/ca_controlled.py',
    'src/wildfire_rl/ca_learning.py','src/wildfire_rl/ca_learning_rl.py',
    'scripts/run_ca_controlled_pilot.py','scripts/run_ca_learning_pilot.py']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value,indent=1,allow_nan=False)+'\n')


def lower_priority():
    torch.set_num_threads(1)
    if os.getpriority(os.PRIO_PROCESS,0)<19:
        os.setpriority(os.PRIO_PROCESS,0,19)
    if os.getpriority(os.PRIO_PROCESS,0)<19:
        raise RuntimeError('nice19 required')


def make_contract(plan, plan_path):
    return {'observation_version':plan['observation_version'],
            'encoder_version':plan['encoder_version'],'reward_version':plan['reward_version'],
            'plan_sha256':sha(plan_path),
            'source_sha256':{p:sha(ROOT/p) for p in SOURCES},
            'architecture':plan['architecture'],
            'runtime':{'python':platform.python_version(),'numpy':np.__version__,
                       'scipy':scipy.__version__,'gymnasium':gymnasium.__version__,
                       'torch':torch.__version__,'sb3':stable_baselines3.__version__,
                       'sb3_contrib':sb3_contrib.__version__}}


def demonstration_job(task):
    seed, scenario, contract, folder = task
    target = Path(folder)/('%d.npz'%seed)
    meta = target.with_suffix('.json')
    if target.exists() or meta.exists():
        old = json.loads(meta.read_text())
        if old['contract']!=contract or old['sha256']!=sha(target):
            raise ValueError('demonstration resume mismatch')
        return old
    bank = EpisodeBank(scenario)
    tokens, globals_, masks, actions, returns, episodes = [],[],[],[],[],[]
    for roster in scenario['rosters']:
        spec, noop = bank.get(seed, roster)
        raw = CAObservationV2(SyntheticSuppressionEnv())
        obs, _ = raw.env._start(spec, noop_cache=noop)
        obs = raw._wrap(obs)
        teacher = observed_policy('direct_flank')
        rewards, done, total = [],False,0.
        while not done:
            encoded = encode_observation(obs)
            mask = raw.action_masks()
            action = teacher(obs,mask)
            if not mask.reshape(4,17)[np.arange(4),action].all():
                raise AssertionError('illegal teacher action')
            tokens.append(encoded['tokens']); globals_.append(encoded['global'])
            masks.append(mask); actions.append(action)
            obs,reward,done,trunc,info = raw.step(action)
            if trunc or info['invalid_actions']:
                raise AssertionError('teacher contract failure')
            rewards.append(reward);total += reward
        row = info['episode_summary']
        if not np.isclose(total,row['saved_fraction']-row['units_lost']-.1*row['close_calls']):
            raise AssertionError('teacher reward accounting')
        returns.extend(discounted_returns(rewards,.99))
        episodes.append({'roster':roster,'world_sha256':world_hash(spec),
                         'steps':len(rewards),'summary':row,'return':total})
    np.savez_compressed(target,tokens=np.array(tokens),global_=np.array(globals_),
                        masks=np.array(masks),actions=np.array(actions),returns=np.array(returns))
    result = {'seed':seed,'contract':contract,'sha256':sha(target),'states':len(tokens),
              'episodes':episodes,'worker_nice':os.getpriority(os.PRIO_PROCESS,0)}
    write(meta,result)
    return result


def make_train_env(scenario, rank):
    lower_priority()
    return CATrainingEnv(scenario,rank=rank,stride=2)


class Progress(BaseCallback):
    def _on_step(self):
        if self.num_timesteps%1024==0:
            print('PPO steps %d'%self.num_timesteps,flush=True)
        return True


def train_seed(seed, plan, scenario, contract, out):
    folder = out/('seed-%d'%seed)
    folder.mkdir(exist_ok=True)
    receipt_path = folder/'training.json'
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt['contract']!=contract:
            raise ValueError('training resume contract mismatch')
        for phase in ('bc','ppo'):
            if sha(folder/(phase+'.npz'))!=receipt['checkpoints'][phase]['sha256']:
                raise ValueError('training resume checkpoint mismatch')
        return receipt
    if any(folder.glob('*.npz')):
        raise ValueError('incomplete run retained; use a new output folder')
    started = time.monotonic()
    data = []
    for case in scenario['case_seeds']['train']:
        path = out/'demonstrations'/('%d.npz'%case)
        meta = json.loads(path.with_suffix('.json').read_text())
        if meta['contract']!=contract or meta['sha256']!=sha(path):
            raise ValueError('demonstration guard failure')
        with np.load(path,allow_pickle=False) as arrays:
            data.append({k:arrays[k].copy() for k in arrays.files})
    arrays = {key:np.concatenate([d[key] for d in data]) for key in data[0]}
    del data
    inputs = {key:torch.from_numpy(arrays[source]).float()
              for key,source in [('tokens','tokens'),('global','global_')]}
    masks = torch.from_numpy(arrays['masks'])
    actions = torch.from_numpy(arrays['actions']).long()
    targets = torch.from_numpy(arrays['returns']).float()
    model = create_model(seed=seed,overrides={k:v for k,v in plan['ppo'].items()
                                            if k not in ('steps','envs')})
    optimiser = torch.optim.Adam(model.policy.parameters(),lr=plan['bc']['learning_rate'])
    logs = []
    for epoch in range(plan['bc']['epochs']):
        order = np.random.default_rng([seed,epoch]).permutation(len(actions))
        losses = []
        for start in range(0,len(order),plan['bc']['batch_size']):
            index = order[start:start+plan['bc']['batch_size']]
            obs = {k:v[index] for k,v in inputs.items()}
            values, log_prob, _ = model.policy.evaluate_actions(obs,actions[index],
                                                               action_masks=masks[index])
            loss = -log_prob.mean()+.1*torch.mean((values.flatten()-targets[index])**2)
            if not torch.isfinite(loss):
                raise ValueError('nonfinite BC loss')
            optimiser.zero_grad();loss.backward()
            torch.nn.utils.clip_grad_norm_(model.policy.parameters(),.5)
            optimiser.step();losses.append(float(loss.detach()))
        logs.append({'epoch':epoch+1,'loss':float(np.mean(losses))})
    agreed, choices = 0,0
    with torch.no_grad():
        for start in range(0,len(actions),64):
            sl = slice(start,start+64)
            pred = model.policy.get_distribution({k:v[sl] for k,v in inputs.items()},
                action_masks=masks[sl]).get_actions(deterministic=True)
            choice = masks[sl].reshape(-1,4,17).sum(-1)>1
            agreed += int(((pred==actions[sl])&choice).sum())
            choices += int(choice.sum())
    print('seed%d BC agreement %.4f'%(seed,agreed/max(choices,1)),flush=True)
    bc_prediction = model.predict({k:v[0].numpy() for k,v in inputs.items()},
        action_masks=arrays['masks'][0],deterministic=True)[0]
    checkpoints = {'bc':save_policy_arrays(model,folder/'bc.npz',contract)}
    reloaded = load_policy_arrays(folder/'bc.npz',contract)
    np.testing.assert_array_equal(bc_prediction,reloaded.predict(
        {k:v[0].numpy() for k,v in inputs.items()},action_masks=arrays['masks'][0],
        deterministic=True)[0])
    del reloaded, inputs, masks, actions, targets, arrays, optimiser
    bc_seconds = time.monotonic()-started
    vec = SubprocVecEnv([partial(make_train_env,scenario,rank) for rank in range(2)],
                        start_method='spawn')
    try:
        model.set_env(vec)
        model.learn(plan['ppo']['steps'],callback=Progress())
        seen = vec.env_method('training_manifest')
        checkpoints['ppo'] = save_policy_arrays(model,folder/'ppo.npz',contract)
    finally:
        vec.close()
    result = {'seed':seed,'contract':contract,'checkpoints':checkpoints,
              'bc_epochs':logs,'bc_choice_agreement':agreed/max(choices,1),
              'bc_choices':choices,'bc_seconds':bc_seconds,'seconds':time.monotonic()-started,
              'ppo_steps':model.num_timesteps,'train_cases_rosters_seen':seen,
              'bc_roundtrip':'PASS','parent_nice':os.getpriority(os.PRIO_PROCESS,0)}
    if result['ppo_steps']!=4096:
        raise AssertionError('fixed step count mismatch')
    write(receipt_path,result)
    return result


_MODELS = {}


def evaluate_job(task):
    seed, baseline_case, scenario, contract, out = task
    path = Path(out)/'evaluation'/('%d.json'%seed)
    if path.exists():
        old = json.loads(path.read_text())
        if old['contract']!=contract:
            raise ValueError('evaluation resume mismatch')
        return old
    sampler = SyntheticSuppressionEnv(curriculum=Curriculum(horizons=(12,),unit_counts=(4,)))
    sampler.reset(options={'seed':seed})
    original = sampler.spec_now
    if world_hash(original)!=baseline_case['world_sha256']:
        raise ValueError('development world mismatch against locked baseline')
    rows = {}
    for roster,units in scenario['rosters'].items():
        spec = replace(original,units=[tuple(u) for u in units])
        rows[roster] = {}
        for model_seed in (17,29,43):
            for phase in ('bc','ppo'):
                key = '%s-%d'%(phase,model_seed)
                if key not in _MODELS:
                    _MODELS[key] = load_policy_arrays(Path(out)/('seed-%d'%model_seed)/(phase+'.npz'),contract)
                model = _MODELS[key]
                env = CAObservationV2(SyntheticSuppressionEnv())
                obs,_ = env.reset(options={'episode_spec':spec})
                total,done,steps = 0.,False,0
                actions = []
                previous = env.env.fire.ever_burned.copy()
                while not done:
                    mask = env.action_masks().reshape(4,17)
                    if not mask[:,0].all() or not env.observation_space.contains(obs):
                        raise AssertionError('observation/no-op contract')
                    action = model.predict(encode_observation(obs),action_masks=mask.ravel(),
                                           deterministic=True)[0]
                    if not mask[np.arange(4),action].all():
                        raise AssertionError('illegal model action')
                    actions.append(action.tolist())
                    obs,reward,done,trunc,info = env.step(action)
                    if trunc or info['invalid_actions'] or (previous&~env.env.fire.ever_burned).any():
                        raise AssertionError('rollout contract')
                    previous = env.env.fire.ever_burned.copy()
                    total += reward;steps += 1
                base = env.env
                row = dict(info['episode_summary'])
                exact = float(base.weights[(base.fire.ever_burned&~base.prior_damage)|base.line_charged].sum())
                if not np.isclose(exact,row['agent_damage_to_now']):
                    raise AssertionError('final union damage mismatch')
                if not np.isclose(total,row['saved_fraction']-row['units_lost']-.1*row['close_calls']):
                    raise AssertionError('reward/safety mismatch')
                if steps<spec.horizon and base.fire.active:
                    raise AssertionError('budget/unit exhaustion terminated active fire')
                if array_hash(base.noop_final.ever_burned)!=baseline_case['rows'][roster]['noop']['noop_final_sha256']:
                    raise ValueError('no-op mismatch')
                row.update({'return':total,'actions':actions,'decisions':steps,
                    'final_damage_sha256':array_hash(base.fire.ever_burned),
                    'line_sha256':array_hash(base.fire.line),'checks':'PASS',
                    'saved_ha_unweighted_line_charged':CELL_AREA_HA*(row['noop_new_cells']-
                        row['agent_new_cells']-row['line_cells_in_noop_footprint'])})
                rows[roster][key] = row
    result = {'base_seed':seed,'contract':contract,'world_sha256':world_hash(original),
              'rows':rows,'worker_nice':os.getpriority(os.PRIO_PROCESS,0)}
    write(path,result)
    return result


def summarize(cases, baseline, plan, training):
    rosters = list(baseline['plan']['rosters'])
    reference = np.array([[c['rows'][b]['direct_flank']['saved_fraction'] for b in rosters]
                          for c in baseline['cases']])
    ref_calls = sum(c['rows'][b]['direct_flank']['close_calls'] for c in baseline['cases'] for b in rosters)
    ref_losses = sum(c['rows'][b]['direct_flank']['units_lost'] for c in baseline['cases'] for b in rosters)
    result = {'reference':'direct_flank','reference_saved':float(reference.mean()),
              'reference_close_calls':ref_calls,'reference_units_lost':ref_losses,'phases':{}}
    matrices = {}
    for phase in ('bc','ppo'):
        per_seed, matrix = {},[]
        for seed in plan['model_seeds']:
            key = '%s-%d'%(phase,seed)
            a = np.array([[c['rows'][b][key]['saved_fraction'] for b in rosters] for c in cases])
            rows = [c['rows'][b][key] for c in cases for b in rosters]
            calls,losses = sum(r['close_calls'] for r in rows),sum(r['units_lost'] for r in rows)
            per_seed[str(seed)] = {'mean_saved_fraction':float(a.mean()),
                'close_calls':calls,'units_lost':losses,'by_roster':dict(zip(rosters,a.mean(0).tolist())),
                'safety_noninferior':calls<=ref_calls and losses<=ref_losses}
            matrix.append(a)
        matrix = np.array(matrix);matrices[phase] = matrix
        contrast = learning_contrast(matrix,reference)
        safe = all(s['safety_noninferior'] for s in per_seed.values())
        result['phases'][phase] = {'mean_saved_fraction':float(matrix.mean()),
            'vs_reference':contrast,'per_seed':per_seed,'safety_all_seeds':safe,
            'continuation_signal':contrast['ci95'][0]>0 and safe,
            'by_roster':dict(zip(rosters,matrix.mean(axis=(0,1)).tolist()))}
    result['ppo_vs_bc'] = learning_contrast(matrices['ppo'],matrices['bc'].mean(0))
    result['note'] = 'Exploratory reused development; case-cluster interval after model-seed averaging. No final acceptance.'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['collect','train','evaluate'],required=True)
    parser.add_argument('--plan',type=Path,default=ROOT/'configs/frozen/ca-learning-pilot-v1.json')
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    lower_priority()
    plan = json.loads(args.plan.read_text());validate_learning_plan(plan,ROOT)
    scenario = json.loads((ROOT/plan['scenario_plan']).read_text())
    contract = make_contract(plan,args.plan)
    args.out.mkdir(parents=True,exist_ok=True)
    guard_path = args.out/'contract.json'
    if guard_path.exists() and json.loads(guard_path.read_text())!=contract:
        raise ValueError('output source/plan/runtime mismatch')
    write(guard_path,contract)
    started = time.monotonic()
    if args.stage=='collect':
        folder = args.out/'demonstrations';folder.mkdir(exist_ok=True)
        with ProcessPoolExecutor(3,initializer=lower_priority) as pool:
            records = list(pool.map(demonstration_job,[(s,scenario,contract,str(folder))
                            for s in scenario['case_seeds']['train']]))
        write(args.out/'collection.json',{'contract':contract,'cases':records,
              'seconds':time.monotonic()-started,'states':sum(c['states'] for c in records)})
        print('COLLECT PASS %d cases %d states'%(len(records),sum(c['states'] for c in records)),flush=True)
    elif args.stage=='train':
        records = [train_seed(seed,plan,scenario,contract,args.out) for seed in plan['model_seeds']]
        write(args.out/'training.json',{'contract':contract,'runs':records,'seconds':time.monotonic()-started})
        print('TRAIN PASS all three seeds',flush=True)
    else:
        final = args.out/'development.json'
        if final.exists():
            raise FileExistsError('retain existing evaluation; no overwrite')
        baseline_path = ROOT/'reports/synthetic/ca-controlled-development-v2.json'
        baseline = json.loads(baseline_path.read_text())
        for source,h in baseline['guard']['source_sha256'].items():
            if sha(ROOT/source)!=h:
                raise ValueError('locked baseline source mismatch')
        for name,version in baseline['guard']['runtime'].items():
            if contract['runtime'][name]!=version:
                raise ValueError('locked baseline runtime mismatch')
        training = json.loads((args.out/'training.json').read_text())
        if training['contract']!=contract:
            raise ValueError('training contract mismatch')
        folder = args.out/'evaluation';folder.mkdir(exist_ok=True)
        with ProcessPoolExecutor(3,initializer=lower_priority) as pool:
            cases = list(pool.map(evaluate_job,[(c['base_seed'],c,scenario,contract,str(args.out))
                                               for c in baseline['cases']]))
        report = {'schema_version':'ca-learning-pilot-result/1.0','date':'2026-11-21',
            'contract':contract,'plan':plan,'training':training,'cases':cases,
            'summary':summarize(cases,baseline,plan,training),'baseline_sha256':sha(baseline_path),
            'seconds':time.monotonic()-started,'code_commit':subprocess.check_output(
                ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'checks':'PASS',
            'closed':['procedural test','real VALIDATION','TEST 2024']}
        write(final,report);print(json.dumps(report['summary'],indent=1),flush=True)


if __name__=='__main__':
    main()
