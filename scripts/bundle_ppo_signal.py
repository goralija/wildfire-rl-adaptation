#!/usr/bin/env python3
"""Portable local diagnosis bundle atop the verified TASK043 archive; no training."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):return json.loads(Path(p).read_text())


def extract_verified(archive,root):
    with tarfile.open(archive,'r:gz') as tar:
        manifest=json.loads(tar.extractfile('manifest.json').read());expected=manifest['members']
        if {m.name for m in tar.getmembers()}!=set(expected)|{'manifest.json'}:raise ValueError('members differ')
        for m in tar.getmembers():
            name=Path(m.name)
            if name.is_absolute() or '..' in name.parts or not m.isfile():raise ValueError('unsafe archive member')
            data=tar.extractfile(m).read()
            if m.name!='manifest.json':
                if len(data)!=expected[m.name]['bytes'] or hashlib.sha256(data).hexdigest()!=expected[m.name]['sha256']:
                    raise ValueError('member hash differs')
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    return len(expected)


def pack(folder,out):
    r=read(folder/'analysis.json');out.mkdir(exist_ok=False,parents=True);files={}
    for pattern in ('src/**/*.py','scripts/*.py','requirements/*','configs/frozen/*.json','configs/*.yml','configs/*.yaml'):
        for p in ROOT.glob(pattern):
            if p.is_file():files[str(p.relative_to(ROOT))]=p
    for p in folder.rglob('*'):
        if p.is_file():files['.local/signal-v1/'+str(p.relative_to(folder))]=p
    for sid in r['plan']['fitting_cases']+r['plan']['evaluation_cases']:
        for directory in ('.local/b1-cases','.local/repair-observations'):
            for suffix in ('.json','.npz'):
                p=ROOT/directory/(sid+suffix);files[str(p.relative_to(ROOT))]=p
    parent=ROOT.parent/'paired-ppo-learning/.local/paired-ppo-artifacts/paired-ppo-learning-v1.tar.gz'
    expected=read(ROOT/'reports/real-fire-data/paired-ppo-artifacts-v1.json')['bundle_sha256']
    if sha(parent)!=expected:raise ValueError('parent archive changed')
    files['parent/paired-ppo-learning-v1.tar.gz']=parent
    p=ROOT/'reports/real-fire-data/paired-ppo-learning-v1.json';files[str(p.relative_to(ROOT))]=p
    manifest=dict(format='ppo-signal-local-bundle/1.0',parent_sha256=expected,
        analysis_sha256=sha(folder/'analysis.json'),members={name:dict(bytes=p.stat().st_size,sha256=sha(p)) for name,p in sorted(files.items())})
    mp=out/'manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');archive=out/'ppo-signal-v1.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for name,p in sorted(files.items()):tar.add(p,arcname=name,recursive=False)
        tar.add(mp,arcname='manifest.json')
    restore=out/'restore';restore.mkdir()
    # Verify/extract old numerical dependencies first; overlay current diagnosis code.
    old_members=extract_verified(parent,restore);members=extract_verified(archive,restore)
    receipt=dict(status='PASS',bundle_bytes=archive.stat().st_size,bundle_sha256=sha(archive),
        files=members,parent_files=old_members,manifest_sha256=sha(mp),all_members_rehashed=True,
        scope='Local nested archive, parent inputs and numeric checkpoints included; existing pinned libraries, no fresh install or optimizer resume')
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)


def replay(folder,out):
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
    import numpy as np
    import diagnose_ppo_signal as d
    from verify_ppo_signal import verify,compare
    d.setup_worker();original=read(folder/'analysis.json');guard=original['guard'];plan=original['plan']
    d.check_sources(guard);parent=read(d.PARENT/'analysis.json')
    fresh=ROOT/'.local/signal-fresh-replay';fresh.mkdir(exist_ok=False);(fresh/'ca').mkdir()
    sid=plan['fitting_cases'][0]
    actual=d.ca_case((str(fresh),sid,guard));expected=read(folder/'ca'/(sid+'.json'))
    if actual['rows']!=expected['rows']:raise ValueError('fresh CA rows differ')
    with np.load(fresh/'ca'/(sid+'.npz'),allow_pickle=False) as a,np.load(folder/'ca'/(sid+'.npz'),allow_pickle=False) as b:
        for key in a.files:np.testing.assert_array_equal(a[key],b[key])
    for be in ('simfire','ca'):
        actual=d.probe((str(fresh),be,17,plan,parent,guard));expected=read(folder/('probe-%s-17.json'%be))
        if actual['rows']!=expected['rows']:raise ValueError('fresh initial rollout differs')
        for a,b in zip(actual['modes'],expected['modes']):compare(a,b)
        with np.load(fresh/('probe-%s-17.npz'%be),allow_pickle=False) as a,np.load(folder/('probe-%s-17.npz'%be),allow_pickle=False) as b:
            for key in a.files:np.testing.assert_array_equal(a[key],b[key])
    independent=verify(folder)
    result=dict(status='PASS',source_root=str(ROOT),fresh_ca_paths=9,fresh_rollout_steps=32,
        fresh_gradient_modes=8,independent_counts=independent['counts'],all_numeric_arrays_exact=True,
        scope='Extracted code and bundled dependencies; first fitting case all9CA paths, both seed17native first16rollouts, all405stored paths and24gradient modes re-audited. Existing libraries, no full training')
    out.write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['pack','replay'])
    p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    (pack if a.command=='pack' else replay)(a.folder.resolve(),a.out.resolve())
