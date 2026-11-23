#!/usr/bin/env python3
"""Local-only full TASK045 archive and inference/native replay; no training."""
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
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.local/matplotlib'))
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from bundle_ppo_signal import extract_verified


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pack(folder,out):
    report=read(folder/'analysis.json')
    if report['status']!='PASS':raise ValueError('complete run required')
    out.mkdir(exist_ok=False,parents=True);files={}
    for pattern in ('src/**/*.py','scripts/*.py','requirements/*','configs/frozen/*.json','configs/*.yml','configs/*.yaml'):
        for p in ROOT.glob(pattern):
            if p.is_file():files[str(p.relative_to(ROOT))]=p
    for p in folder.rglob('*'):
        if p.is_file():files['.local/centered-ppo-v1/'+str(p.relative_to(folder))]=p
    parent=ROOT.parent/'ppo-signal-diagnosis/.local/signal-artifacts/ppo-signal-v1.tar.gz'
    expected=read(ROOT/'reports/real-fire-data/ppo-signal-artifacts-v1.json')['bundle_sha256']
    if sha(parent)!=expected:raise ValueError('verified diagnosis archive changed')
    files['parent/ppo-signal-v1.tar.gz']=parent
    for name in ('ppo-signal-artifacts-v1.json','paired-ppo-artifacts-v1.json'):
        p=ROOT/'reports/real-fire-data'/name;files[str(p.relative_to(ROOT))]=p
    manifest=dict(format='centered-ppo-local-bundle/1.0',parent_sha256=expected,
        analysis_sha256=sha(folder/'analysis.json'),members={name:dict(bytes=p.stat().st_size,sha256=sha(p)) for name,p in sorted(files.items())})
    mp=out/'manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');archive=out/'centered-ppo-v1.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for name,p in sorted(files.items()):tar.add(p,arcname=name,recursive=False)
        tar.add(mp,arcname='manifest.json')
    restore=out/'restore';restore.mkdir()
    diagnosis_members=extract_verified(parent,restore)
    old=restore/'parent/paired-ppo-learning-v1.tar.gz'
    old_expected=read(ROOT/'reports/real-fire-data/paired-ppo-artifacts-v1.json')['bundle_sha256']
    if sha(old)!=old_expected:raise ValueError('embedded original PPO archive changed')
    original_members=extract_verified(old,restore)
    # Dependency source first, diagnosis second, current source last.
    extract_verified(parent,restore);members=extract_verified(archive,restore)
    receipt=dict(status='PASS',bundle_bytes=archive.stat().st_size,bundle_sha256=sha(archive),files=members,
        diagnosis_parent_files=diagnosis_members,original_parent_files=original_members,
        manifest_sha256=sha(mp),all_members_rehashed=True,
        scope='Local nested archive with numeric checkpoints and inputs; existing pinned libraries; no upload, fresh install or optimizer resume')
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)


def setup_worker():
    import run_centered_ppo_pilot as d
    d.old.setup_worker()


def replay_job(task):
    folder,run,plan,guard=task;folder=Path(folder)
    import numpy as np
    import run_centered_ppo_pilot as d
    from wildfire_rl.common_control_rl import load_policy_arrays
    be,seed=run['backend'],run['seed'];job=folder/('job-%s-%d'%(be,seed));scores=0;paths=0
    for stage in (0,512):
        model=load_policy_arrays(job/('policy-%d.npz'%stage),d.contract(guard,be,seed,stage,plan))
        for row in [r for r in run['rows'] if r['checkpoint']==stage]:
            sid=row['scenario_id'];actions=d.policy_actions(model,be,sid)
            if actions!=row['actions']:raise ValueError('restored decisions differ')
            scores+=1
            if stage==0:continue
            env=d.make_env(be,sid);actual,arrays=d.rollout(env,model=model);env.close()
            if [r['effective_action'] for r in actual['rows']]!=actions:raise ValueError('native actions differ')
            if actual['return_']!=row['native_return']:raise ValueError('native return differs')
            for key,value in actual['score'].items():
                if row[key]!=value:raise ValueError('native score differs')
            with np.load(job/row['arrays'],allow_pickle=False) as old:
                if set(old.files)!=set(arrays):raise ValueError('native array keys differ')
                for key in arrays:np.testing.assert_array_equal(arrays[key],old[key])
            paths+=1
    return dict(backend=be,seed=seed,checkpoints=2,policy_decisions=scores,native_paths=paths,status='PASS')


def replay(folder,out):
    import run_centered_ppo_pilot as d
    from audit_centered_ppo_pilot import audit
    report=read(folder/'analysis.json');d.assert_guard(report['guard'])
    tasks=[(str(folder),run,report['plan'],report['guard']) for run in report['runs']]
    with ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('spawn'),initializer=setup_worker) as pool:
        rows=list(pool.map(replay_job,tasks))
    verified=audit(folder)
    result=dict(status='PASS',source_root=str(ROOT),checkpoints=sum(x['checkpoints'] for x in rows),
        policy_decisions=sum(x['policy_decisions'] for x in rows),native_paths=sum(x['native_paths'] for x in rows),
        cumulative_states=sum(x['native_paths']*5 for x in rows),all_numeric_arrays_exact=True,
        independent_counts=verified['counts'],rows=rows,
        scope='Extracted source/inputs/all12numeric models,192checkpoint decisions,96fresh native final paths; existing libraries, no retraining')
    out.write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='rows'})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['pack','replay'])
    p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if os.getpriority(os.PRIO_PROCESS,0)<19:raise RuntimeError('nice19 required')
    (pack if a.command=='pack' else replay)(a.folder.resolve(),a.out.resolve())
