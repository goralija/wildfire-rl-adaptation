#!/usr/bin/env python3
"""Independent mask/return/table arithmetic for the frozen B.1 technical smoke."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(folder):
    report=json.loads((folder/'summary.json').read_text());counts=dict(native_paths=0,policy_paths=0,
        cumulative_masks=0,training_steps=0,reference_masks=0)
    assert report['status']=='PASS' and report['nice']==19 and report['numeric_threads']==1
    assert sha(ROOT/'configs/frozen/common-ppo-smoke-v1.json')==report['guard']['plan_sha256']
    for path,digest in report['guard']['source_sha256'].items():assert sha(ROOT/path)==digest,path
    for ref in report['references']:
        with np.load(folder/('reference-'+ref['backend']+'-'+ref['scenario_id']+'.npz'),allow_pickle=False) as a:
            assert a['burned'].shape==(5,256,256)
            assert not (a['burned'][:-1]&~a['burned'][1:]).any()
            assert ref['noop_new_cells']==int((a['burned'][-1]&~a['initial']).sum())
            counts['reference_masks']+=5
    for group,paths in [('native',report['native_paths'])]+[
            ('policy',[dict(row,backend=run['backend']) for row in run['replays']]) for run in report['runs']]:
        for row in paths:
            path=folder/row['arrays'];assert sha(path)==row['arrays_sha256']
            reference=folder/('reference-'+row['backend']+'-'+row['scenario_id']+'.npz')
            with np.load(path,allow_pickle=False) as a,np.load(reference,allow_pickle=False) as ref:
                initial=a['initial'];burned=a['burned'];line=a['line'];noop=ref['burned'][-1]
                np.testing.assert_array_equal(initial,ref['initial'])
                assert not (burned[:-1]&~burned[1:]).any()
                assert not (line[:-1]&~line[1:]).any()
                assert a['features'].shape==(4,536) and np.isfinite(a['features']).all()
                assert a['masks'].shape==(4,9) and a['masks'][:,0].all()
                assert not (initial&~burned).any()
                charged=[int(((b|(l&noop))&~initial).sum()) for b,l in zip(burned,line)]
                assert charged[0]==0
                total=0.
                for k,step in enumerate(row['rows']):
                    invalid=not a['masks'][k,step['requested_action']]
                    assert invalid==step['invalid']
                    assert step['effective_action']==(0 if invalid else step['requested_action'])
                    assert step['charged_damage_cells']==charged[k+1]
                    reward=-(charged[k+1]-charged[k])/100.-.01*invalid
                    np.testing.assert_allclose(reward,step['reward'],atol=1e-12,rtol=0)
                    total+=reward
                assert abs(total-row['return_'])<1e-12
                assert row['score']['charged_damage_cells']==charged[-1]
                if group=='native':
                    oldfolder=ROOT/('.local/b1-cases' if row['backend']=='simfire' else '.local/paired-v1-final/cases')
                    record=json.loads((oldfolder/(row['scenario_id']+'.json')).read_text())
                    oldnpz=oldfolder/(row['scenario_id']+'.npz')
                    assert sha(oldnpz)==record.get('npz_sha256',record.get('mask_file_sha256'))
                    actions=[s['effective_action'] for s in row['rows']]
                    index=next(i for i,r in enumerate(record['outcomes']) if r['effective_actions']==actions)
                    with np.load(oldnpz,allow_pickle=False) as old:
                        np.testing.assert_array_equal(burned[-1],old['agent_burned'][index])
                        np.testing.assert_array_equal(line[-1],old['line_cells'][index])
                counts[group+'_paths']+=1;counts['cumulative_masks']+=5
    initial={}
    for run in report['runs']:
        assert run['steps']==64 and run['completed_episodes']==16 and len(run['training'])==64
        expected=[report['plan']['cases'][k%3] for k in range(16)]
        assert run['schedule']==expected
        for row in run['training']:
            assert row['scenario_id']==expected[(row['step']-1)//4]
            assert row['done']==(row['step']%4==0)
            assert row['remaining_budget'] in (0,1) and np.isfinite(row['reward'])
        initial.setdefault(run['seed'],run['initial_policy_digest'])
        assert initial[run['seed']]==run['initial_policy_digest']
        assert run['final_policy_digest']!=run['initial_policy_digest']
        assert sha(folder/('policy-%s-%d.npz'%(run['backend'],run['seed'])))==run['checkpoint_sha256']
        counts['training_steps']+=64
    return dict(status='PASS',summary_sha256=sha(folder/'summary.json'),checks=counts,
                scope='Independent final whole masks vs old archives, incremental union/return arithmetic, schedule and byte hashes; no scientific ranking')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    result=verify(args.folder);args.out.write_text(json.dumps(result,indent=2)+'\n');print(result)
