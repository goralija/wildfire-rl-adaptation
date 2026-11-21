"""One PPO architecture for both common-line backends; numeric inference only."""
import hashlib
import json
import random
from pathlib import Path

import gymnasium as gym
import numpy as np
import torch
from sb3_contrib import MaskablePPO

from .common_control import FEATURE_DIM

PPO_SETTINGS=dict(n_steps=16,batch_size=16,n_epochs=2,learning_rate=.0001,
                  gamma=1.,gae_lambda=1.,clip_range=.1,ent_coef=.001,
                  vf_coef=.5,max_grad_norm=.5,target_kl=.03)


class ShapeOnlyEnv(gym.Env):
    observation_space=gym.spaces.Box(-np.inf,np.inf,(FEATURE_DIM,),dtype=np.float32)
    action_space=gym.spaces.Discrete(9)

    def reset(self,*,seed=None,options=None):
        super().reset(seed=seed)
        return np.zeros(FEATURE_DIM,np.float32),{}

    def step(self,action):
        raise RuntimeError('shape-only environment cannot generate data')


def create_model(env=None,seed=0,settings=None):
    return MaskablePPO('MlpPolicy',ShapeOnlyEnv() if env is None else env,
                       policy_kwargs=dict(net_arch=dict(pi=[64,64],vf=[64,64])),
                       seed=seed,device='cpu',verbose=0,**(PPO_SETTINGS if settings is None else settings))


def policy_digest(model):
    digest=hashlib.sha256()
    for key,value in sorted(model.policy.state_dict().items()):
        a=value.detach().cpu().numpy()
        digest.update(key.encode());digest.update(str(a.dtype).encode())
        digest.update(str(a.shape).encode());digest.update(a.tobytes())
    return digest.hexdigest()


def save_policy_arrays(model,path,contract):
    path=Path(path)
    if path.suffix!='.npz':raise ValueError('NPZ suffix required')
    if path.exists() or path.with_suffix('.json').exists():raise FileExistsError('checkpoint exists')
    arrays={k:v.detach().cpu().numpy() for k,v in model.policy.state_dict().items()}
    if not all(np.isfinite(a).all() for a in arrays.values()):raise ValueError('nonfinite weights')
    np.savez_compressed(path,**arrays)
    receipt=dict(format='common-line-policy-npz/1.0',contract=contract,
                 sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                 policy_digest=policy_digest(model),inference_only=True,
                 tensors={k:dict(shape=list(v.shape),dtype=str(v.dtype)) for k,v in arrays.items()})
    path.with_suffix('.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    return receipt


def load_policy_arrays(path,expected_contract):
    """Guard metadata and bytes first; load only numeric arrays, never pickle."""
    path=Path(path);receipt=json.loads(path.with_suffix('.json').read_text())
    if (receipt.get('format')!='common-line-policy-npz/1.0'
            or receipt.get('contract')!=expected_contract or receipt.get('inference_only') is not True):
        raise ValueError('checkpoint contract mismatch')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=receipt['sha256']:
        raise ValueError('checkpoint hash mismatch')
    rng=random.getstate(),np.random.get_state(),torch.random.get_rng_state()
    try:model=create_model()
    finally:
        random.setstate(rng[0]);np.random.set_state(rng[1]);torch.random.set_rng_state(rng[2])
    state=model.policy.state_dict();replacement={}
    with np.load(path,allow_pickle=False) as arrays:
        if set(arrays.files)!=set(state) or set(receipt['tensors'])!=set(state):
            raise ValueError('checkpoint keys mismatch')
        for key,tensor in state.items():
            value=arrays[key]
            expected=dict(shape=list(tensor.shape),dtype=str(tensor.numpy().dtype))
            if (receipt['tensors'][key]!=expected or list(value.shape)!=expected['shape']
                    or str(value.dtype)!=expected['dtype'] or not np.isfinite(value).all()):
                raise ValueError('checkpoint tensor mismatch')
            replacement[key]=torch.from_numpy(value.copy())
    model.policy.load_state_dict(replacement,strict=True)
    if policy_digest(model)!=receipt['policy_digest']:raise ValueError('policy digest mismatch')
    return model
