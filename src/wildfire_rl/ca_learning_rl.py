"""Small SB3 policy architecture and pickle-free inference checkpoints."""
import hashlib
import json
import random
from pathlib import Path

import gymnasium as gym
import numpy as np
import torch
from torch import nn
from sb3_contrib import MaskablePPO
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

from .ca_learning import TOKEN_DIM, GLOBAL_DIM, encoded_space


class UnitExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space):
        super().__init__(observation_space, features_dim=288)
        self.units = nn.Sequential(nn.Linear(TOKEN_DIM,64), nn.Tanh(),
                                   nn.Linear(64,64), nn.Tanh())
        self.global_net = nn.Sequential(nn.Linear(GLOBAL_DIM,32), nn.Tanh())

    def forward(self, observations):
        tokens = self.units(observations["tokens"]).flatten(start_dim=1)
        return torch.cat([tokens, self.global_net(observations["global"])],dim=1)


class ShapeOnlyEnv(gym.Env):
    observation_space = encoded_space()
    action_space = gym.spaces.MultiDiscrete([17]*4)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        return {key:np.zeros(space.shape,np.float32)
                for key,space in self.observation_space.spaces.items()}, {}

    def step(self, action):
        raise RuntimeError("shape-only environment cannot generate training data")


def create_model(env=None, seed=0, overrides=None):
    kwargs = dict(n_steps=32,batch_size=32,n_epochs=4,learning_rate=.0001,
                  gamma=.99,gae_lambda=.95,clip_range=.1,ent_coef=.001,
                  vf_coef=.5,max_grad_norm=.5,target_kl=.03)
    kwargs.update(overrides or {})
    return MaskablePPO('MultiInputPolicy', env if env is not None else ShapeOnlyEnv(),
                       policy_kwargs=dict(features_extractor_class=UnitExtractor,
                                          net_arch=dict(pi=[64],vf=[64])),
                       seed=seed,device='cpu',verbose=0,**kwargs)


def save_policy_arrays(model, path, contract):
    path = Path(path)
    if path.exists() or path.with_suffix('.json').exists():
        raise FileExistsError("checkpoint exists")
    arrays = {key:value.detach().cpu().numpy() for key,value in model.policy.state_dict().items()}
    if not all(np.isfinite(value).all() for value in arrays.values()):
        raise ValueError("nonfinite policy weights")
    np.savez_compressed(path,**arrays)
    receipt = {'format':'ca-policy-array-npz/1.0','contract':contract,
               'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
               'tensors':{k:{'shape':list(v.shape),'dtype':str(v.dtype)} for k,v in arrays.items()}}
    path.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def load_policy_arrays(path, expected_contract):
    """Reject provenance mismatch before np.load; never unpickle Torch/SB3 objects."""
    path = Path(path)
    receipt = json.loads(path.with_suffix('.json').read_text())
    if receipt.get('format')!='ca-policy-array-npz/1.0' or receipt['contract']!=expected_contract:
        raise ValueError("checkpoint contract mismatch")
    if hashlib.sha256(path.read_bytes()).hexdigest()!=receipt['sha256']:
        raise ValueError("checkpoint hash mismatch")
    # Inference reconstruction must not reset the caller's training random stream.
    rng = random.getstate(), np.random.get_state(), torch.random.get_rng_state()
    try:
        model = create_model()
    finally:
        random.setstate(rng[0])
        np.random.set_state(rng[1])
        torch.random.set_rng_state(rng[2])
    state = model.policy.state_dict()
    with np.load(path,allow_pickle=False) as arrays:
        if set(arrays.files)!=set(state) or set(receipt['tensors'])!=set(state):
            raise ValueError("checkpoint keys mismatch")
        replacement = {}
        for key, tensor in state.items():
            value = arrays[key]
            if (list(value.shape)!=list(tensor.shape) or str(value.dtype)!=str(tensor.numpy().dtype)
                    or receipt['tensors'][key]!={'shape':list(value.shape),'dtype':str(value.dtype)}
                    or not np.isfinite(value).all()):
                raise ValueError("checkpoint tensor mismatch")
            replacement[key] = torch.from_numpy(value.copy())
    model.policy.load_state_dict(replacement,strict=True)
    return model
