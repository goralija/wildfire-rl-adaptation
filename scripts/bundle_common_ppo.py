#!/usr/bin/env python3
"""Local-only hashed B.1 bundle and inference replay; does not install or retrain."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pack(folder,out):
    report=json.loads((folder/'summary.json').read_text())
    out.mkdir(parents=True,exist_ok=False);files={}
    for pattern in ('src/**/*.py','scripts/*.py','requirements/*','configs/frozen/*.json',
                    'configs/*.yml','configs/*.yaml'):
        for path in ROOT.glob(pattern):
            if path.is_file():files[str(path.relative_to(ROOT))]=path
    for path in folder.iterdir():
        if path.is_file():files['.local/common-ppo-v1-final/'+path.name]=path
    for path in [ROOT/'data/manifests/feds-episode-cohort-v1.json',
                 ROOT/'.local/gridmet/feds-episode-weather-v1.json',ROOT/'.local/b1-cases/table-98.json']:
        files[str(path.relative_to(ROOT))]=path
    for sid in report['plan']['cases']:
        for path in (ROOT/'.local/feds-simfire-cases'/sid).iterdir():
            if path.is_file():files[str(path.relative_to(ROOT))]=path
        for backend in ('simfire','ca'):
            for suffix in ('.npz','.json'):
                path=ROOT/'.local/expanded-v1'/backend/(sid+suffix)
                files[str(path.relative_to(ROOT))]=path
        for directory in ('.local/b1-cases','.local/paired-v1-final/cases'):
            for suffix in ('.npz','.json'):
                path=ROOT/directory/(sid+suffix);files[str(path.relative_to(ROOT))]=path
    manifest=dict(format='common-ppo-local-bundle/1.0',summary_sha256=sha(folder/'summary.json'),
                  members={name:dict(sha256=sha(path),bytes=path.stat().st_size)
                           for name,path in sorted(files.items())})
    mp=out/'manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
    archive=out/'common-ppo-v1.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for name,path in sorted(files.items()):tar.add(path,arcname=name,recursive=False)
        tar.add(mp,arcname='manifest.json')
    restore=out/'restore';restore.mkdir()
    # Only regular files named by our own manifest; verify bytes before writing.
    with tarfile.open(archive,'r:gz') as tar:
        members=tar.getmembers()
        if {m.name for m in members}!=set(files)|{'manifest.json'}:raise ValueError('member mismatch')
        for member in members:
            name=Path(member.name)
            if name.is_absolute() or '..' in name.parts or not member.isfile():raise ValueError('unsafe bundle member')
            payload=tar.extractfile(member).read()
            if member.name!='manifest.json':
                expected=manifest['members'][member.name]
                if len(payload)!=expected['bytes'] or hashlib.sha256(payload).hexdigest()!=expected['sha256']:
                    raise ValueError('member hash mismatch')
            target=restore/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
    receipt=dict(status='PASS',bundle_sha256=sha(archive),bundle_bytes=archive.stat().st_size,
                 files=len(files),manifest_sha256=sha(mp),all_members_rehashed=True,
                 scope='Local only; dependencies must already exist; no fresh installation or training resume')
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)


def replay(folder,out):
    # Run this command from the extracted script to exercise restored source/inputs.
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
    from smoke_common_ppo import native_env,rollout,sha
    from wildfire_rl.common_control import CommonControlEnv
    from wildfire_rl.common_control_rl import load_policy_arrays
    import numpy as np
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    report=json.loads((folder/'summary.json').read_text())
    for path,digest in report['guard']['source_sha256'].items():
        if sha(ROOT/path)!=digest:raise ValueError('restored source hash mismatch')
    rows=[]
    for run in report['runs']:
        contract=dict(guard=report['guard'],backend=run['backend'],seed=run['seed'],
                      observation='v2/terrain536',reward=report['plan']['reward']['version'],
                      architecture=report['plan']['architecture'])
        model=load_policy_arrays(folder/('policy-%s-%d.npz'%(run['backend'],run['seed'])),contract)
        for original in run['replays']:
            sid=original['scenario_id'];native,_=native_env(run['backend'],sid)
            with np.load(folder/('reference-'+run['backend']+'-'+sid+'.npz'),allow_pickle=False) as ref:
                env=CommonControlEnv(native,ref['burned'][-1])
            record,arrays=rollout(env,model=model)
            if any(record[k]!=original[k] for k in record):raise ValueError('restored row mismatch')
            with np.load(folder/original['arrays'],allow_pickle=False) as old:
                for key in arrays:np.testing.assert_array_equal(arrays[key],old[key])
            env.close();rows.append(dict(backend=run['backend'],seed=run['seed'],scenario_id=sid,status='PASS'))
    result=dict(status='PASS',source_root=str(ROOT),checkpoint_paths=4,policy_replays=len(rows),
                cumulative_masks=len(rows)*5,all_weights_logits_features_masks_actions_exact=True,
                nice=os.getpriority(os.PRIO_PROCESS,0),rows=rows,
                scope='Restored source, inputs and numeric inference checkpoints with existing pinned libraries; no retraining')
    out.write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='rows'})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['pack','replay'])
    p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();(pack if a.command=='pack' else replay)(a.folder,a.out)
