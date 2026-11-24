#!/usr/bin/env python3
"""Four-decision TRAIN smoke of the shared interface; no learning benchmark."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):os.environ[name]='1'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.local/matplotlib'))
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import numpy as np
from wildfire_rl.common_control import CommonControlEnv,FEATURE_DIM
from wildfire_rl.control_factory import native_env


def mask_sha(mask):return hashlib.sha256(np.asarray(mask,bool).tobytes()).hexdigest()


def check_case(backend,sid,policy):
    raw,inputs=native_env(backend,sid);raw.reset()
    initial=raw.unwrapped.cumulative_burned.copy();reference=[initial]
    for k in range(4):
        _,_,done,trunc,_=raw.step(0)
        if done!=(k==3) or trunc:raise ValueError('no-op horizon differs')
        reference.append(raw.unwrapped.cumulative_burned.copy())
    raw.close();raw,_=native_env(backend,sid);env=CommonControlEnv(raw,reference[-1]);obs,_=env.reset();rows=[]
    np.testing.assert_array_equal(initial,raw.unwrapped.cumulative_burned)
    for k in range(4):
        mask=env.action_masks();legal=np.flatnonzero(mask[1:])+1
        action=int(legal[0]) if policy=='first-legal' and len(legal) else 0
        obs,reward,done,trunc,info=env.step(action)
        if done!=(k==3) or trunc or info['invalid_action']:raise ValueError('control horizon/legality differs')
        if obs.shape!=(FEATURE_DIM,) or not np.isfinite(obs).all():raise ValueError('encoder contract differs')
        rows.append(dict(action=action,reward=reward,budget=info['remaining_budget'],
            burned_sha256=mask_sha(raw.unwrapped.cumulative_burned),line_sha256=mask_sha(env.ledger.line)))
    total=sum(x['reward'] for x in rows);score=env.ledger.score
    np.testing.assert_allclose(total,-score['charged_damage_cells']/100.,atol=1e-12,rtol=0)
    result=dict(backend=backend,scenario_id=sid,policy=policy,steps=4,feature_dim=FEATURE_DIM,
        input_receipt_sha256=inputs['receipt_sha256'],initial_sha256=mask_sha(initial),
        noop_trajectory_sha256=[mask_sha(x) for x in reference],return_=total,score=score,rows=rows,status='PASS')
    env.close();return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--backend',choices=['simfire','ca','both'],default='both')
    p.add_argument('--scenario-id',required=True);p.add_argument('--policy',choices=['noop','first-legal'],default='first-legal')
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError('choose a new output receipt')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    backends=('simfire','ca') if a.backend=='both' else (a.backend,)
    result=dict(status='PASS',scope='Technical TRAIN interface smoke, no training or physical validation',
                rows=[check_case(be,a.scenario_id,a.policy) for be in backends])
    with a.out.open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
    print('PASS',len(result['rows']),'backend(s), four full decisions each')
