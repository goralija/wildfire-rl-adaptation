#!/usr/bin/env python3
"""Local-only TASK-043 bundle and full restored inference/native replay."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):return json.loads(Path(p).read_text())


def pack(folder,out):
    report=read(folder/'analysis.json');plan=report['plan'];files={};out.mkdir(exist_ok=False,parents=True)
    for pattern in ('src/**/*.py','scripts/*.py','requirements/*','configs/frozen/*.json','configs/*.yml','configs/*.yaml'):
        for p in ROOT.glob(pattern):
            if p.is_file():files[str(p.relative_to(ROOT))]=p
    for p in folder.rglob('*'):
        if p.is_file():files['.local/paired-ppo-v1/'+str(p.relative_to(folder))]=p
    for p in [ROOT/'data/manifests/feds-episode-cohort-v1.json',ROOT/'.local/gridmet/feds-episode-weather-v1.json',
              ROOT/'.local/b1-cases/table-98.json',ROOT/'.local/repair-observations/dataset-98.json']:
        files[str(p.relative_to(ROOT))]=p
    for sid in plan['fitting_cases']+plan['evaluation_cases']:
        for p in (ROOT/'.local/feds-simfire-cases'/sid).iterdir():
            if p.is_file():files[str(p.relative_to(ROOT))]=p
        for be in ('simfire','ca'):
            for suffix in ('.json','.npz'):
                p=ROOT/'.local/expanded-v1'/be/(sid+suffix);files[str(p.relative_to(ROOT))]=p
    for sid in plan['evaluation_cases']:
        for d in ('.local/b1-cases','.local/paired-v1-final/cases','.local/repair-observations'):
            for suffix in ('.json','.npz'):
                p=ROOT/d/(sid+suffix);files[str(p.relative_to(ROOT))]=p
    manifest=dict(format='paired-ppo-local-bundle/1.0',analysis_sha256=sha(folder/'analysis.json'),
        members={name:dict(sha256=sha(p),bytes=p.stat().st_size) for name,p in sorted(files.items())})
    mp=out/'manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
    archive=out/'paired-ppo-learning-v1.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for name,p in sorted(files.items()):tar.add(p,arcname=name,recursive=False)
        tar.add(mp,arcname='manifest.json')
    restore=out/'restore';restore.mkdir()
    with tarfile.open(archive,'r:gz') as tar:
        if {m.name for m in tar.getmembers()}!=set(files)|{'manifest.json'}:raise ValueError('bundle members differ')
        for m in tar.getmembers():
            name=Path(m.name)
            if name.is_absolute() or '..' in name.parts or not m.isfile():raise ValueError('unsafe bundle member')
            data=tar.extractfile(m).read()
            if m.name!='manifest.json':
                expected=manifest['members'][m.name]
                if len(data)!=expected['bytes'] or hashlib.sha256(data).hexdigest()!=expected['sha256']:
                    raise ValueError('bundle member hash differs')
            target=restore/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    receipt=dict(status='PASS',bundle_sha256=sha(archive),bundle_bytes=archive.stat().st_size,files=len(files),
                 manifest_sha256=sha(mp),all_members_rehashed=True,
                 scope='Local only; existing pinned libraries required; no fresh installation or training resume')
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)


def setup_worker():
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
    # Set these before importing Torch/numerical libraries in spawned workers.
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    if os.getpriority(os.PRIO_PROCESS,0)<19:raise RuntimeError('nice19 required')


def replay_job(task):
    folder,run,plan,guard=task;folder=Path(folder)
    import numpy as np
    import run_paired_ppo_learning as driver
    from wildfire_rl.common_control_rl import load_policy_arrays
    from smoke_common_ppo import rollout
    be,seed=run['backend'],run['seed'];job=folder/('job-%s-%d'%(be,seed));checkpoints=0;scores=0;paths=0
    for stage in plan['checkpoints']:
        model=load_policy_arrays(job/('policy-%d.npz'%stage),driver.contract(guard,be,seed,stage,plan));checkpoints+=1
        for row in [r for r in run['rows'] if r['checkpoint']==stage]:
            sid=row['scenario_id'];actions=[0]*4
            with np.load(folder/'evaluation'/(be+'-'+sid+'.npz'),allow_pickle=False) as a:
                for k in range(4):
                    action=int(model.predict(a['features'][k],action_masks=a['masks'][k],deterministic=True)[0])
                    if action:actions[k]=action;break
            if actions!=row['actions']:raise ValueError('restored checkpoint decisions differ')
            scores+=1
            if stage==2048:
                env=driver.make_env(folder,be,sid);actual,arrays=rollout(env,model=model);env.close()
                if [r['effective_action'] for r in actual['rows']]!=actions:raise ValueError('restored native actions differ')
                for key,value in actual['score'].items():
                    if row[key]!=value:raise ValueError('restored native score differs')
                if actual['return_']!=row['native_return']:raise ValueError('restored return differs')
                with np.load(job/row['arrays'],allow_pickle=False) as old:
                    for key in arrays:np.testing.assert_array_equal(arrays[key],old[key])
                paths+=1
    return dict(backend=be,seed=seed,checkpoints=checkpoints,policy_decisions=scores,native_paths=paths,status='PASS')


def replay(folder,out):
    report=read(folder/'analysis.json');guard=report['guard']
    for path,digest in guard['source_sha256'].items():
        if sha(ROOT/path)!=digest:raise ValueError('restored source differs')
    jobs=[(str(folder),r,report['plan'],guard) for r in report['runs']]
    with ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('spawn'),initializer=setup_worker) as pool:
        rows=list(pool.map(replay_job,jobs))
    result=dict(status='PASS',source_root=str(ROOT),checkpoints=sum(r['checkpoints'] for r in rows),
        policy_decisions=sum(r['policy_decisions'] for r in rows),native_paths=sum(r['native_paths'] for r in rows),
        cumulative_masks=sum(r['native_paths']*5 for r in rows),
        all_logits_features_masks_actions_exact=True,nice=os.getpriority(os.PRIO_PROCESS,0),rows=rows,
        scope='Extracted source, inputs, all18 numeric inference checkpoints and all96 native final paths; existing libraries, no retraining')
    out.write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='rows'})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['pack','replay'])
    p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.command=='replay' and os.getpriority(os.PRIO_PROCESS,0)<19:raise RuntimeError('nice19 required')
    (pack if a.command=='pack' else replay)(a.folder.resolve(),a.out.resolve())
