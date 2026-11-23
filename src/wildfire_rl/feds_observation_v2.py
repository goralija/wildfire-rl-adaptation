"""Explicit, opt-in observation repair; frozen SimFire dynamics stay unchanged."""
from __future__ import annotations
import gymnasium as gym
import numpy as np
from .feds_simfire_env import line_points_for
from .feds_simfire_setup import CELL_SIZE_M

OBSERVATION_VERSION='simfire-categorical-local-v2'


class SimFireObservationV2(gym.Wrapper):
    observation_version=OBSERVATION_VERSION

    def __init__(self,env,*,mask_nonfuel_lines=True):
        super().__init__(env)
        self.mask_nonfuel_lines=bool(mask_nonfuel_lines);self._static=None
        self.observation_space=gym.spaces.Dict({**env.observation_space.spaces,
            'global_grid':gym.spaces.Box(-1.,1.,shape=(20,64,64),dtype=np.float32),
            'action_patches':gym.spaces.Box(-1.,1.,shape=(8,20,17,17),dtype=np.float32),
            'candidate_line_masks':gym.spaces.Box(0.,1.,shape=(8,17,17),dtype=np.float32),
            'candidate_centres':gym.spaces.Box(0.,1.,shape=(8,2),dtype=np.float32)})

    def candidate_points(self):
        base=self.env.unwrapped;state=base.simulation.fire_map
        return [line_points_for(base._placement(),state,state==1,k) for k in range(8)]

    def action_masks(self,*,mask_nonfuel_lines=None):
        gate=self.mask_nonfuel_lines if mask_nonfuel_lines is None else bool(mask_nonfuel_lines)
        base=self.env.unwrapped;mask=base.action_masks().copy()
        if gate:
            for action,points in enumerate(self.candidate_points(),1):
                if mask[action]:mask[action]=any(1<=int(base.fuel[y,x])<=13 for x,y in points)
        mask[0]=True
        return mask

    def _static_channels(self):
        if self._static is None:
            base=self.env.unwrapped;fuel=base.fuel
            elevation=base._input_cache[base.scenario_id]['elevation'].astype(np.float32)
            if fuel.shape!=(256,256) or elevation.shape!=fuel.shape:raise ValueError('v2 requires the locked native grid')
            if not np.isfinite(elevation).all():raise ValueError('nonfinite elevation')
            categories=[(fuel==k).astype(np.float32) for k in range(1,14)]
            categories.append((~((fuel>=1)&(fuel<=13))).astype(np.float32))
            gy,gx=np.gradient(elevation,CELL_SIZE_M)
            self._static=np.stack(categories+[np.clip(elevation/5000.,-1.,1.),
                                              np.clip(gx,-1.,1.),np.clip(gy,-1.,1.)])
        return self._static

    def observation(self,legacy):
        base=self.env.unwrapped;state=base.simulation.fire_map
        native=np.concatenate([np.stack([base.cumulative_burned,state==1,np.isin(state,(3,4,5))]).astype(np.float32),
                               self._static_channels()],axis=0)
        global_grid=native.reshape(20,64,4,64,4).mean(axis=(2,4)).astype(np.float32)
        padded=np.pad(native,((0,0),(8,8),(8,8)))
        padded[16]=1.;padded[16,8:-8,8:-8]=native[16]
        patches=np.zeros((8,20,17,17),dtype=np.float32);lines=np.zeros((8,17,17),dtype=np.float32)
        centres=np.zeros((8,2),dtype=np.float32)
        rows,columns=np.nonzero(state==1)
        fallback=(int(np.floor(columns.mean()+.5)),int(np.floor(rows.mean()+.5))) if rows.size else (128,128)
        for k,points in enumerate(self.candidate_points()):
            if points:
                cx=int(np.floor(np.mean([x for x,y in points])+.5));cy=int(np.floor(np.mean([y for x,y in points])+.5))
            else:cx,cy=fallback
            centres[k]=[cx/255.,cy/255.];patches[k]=padded[:,cy:cy+17,cx:cx+17]
            for x,y in points:
                rx,ry=x-cx+8,y-cy+8
                if not (0<=rx<17 and 0<=ry<17):raise ValueError('candidate exceeds declared patch')
                lines[k,ry,rx]=1.
        return {**legacy,'global_grid':global_grid,'action_patches':patches,
                'candidate_line_masks':lines,'candidate_centres':centres}

    def reset(self,**kwargs):
        legacy,info=self.env.reset(**kwargs);self._static=None
        return self.observation(legacy),{**info,'observation_version':self.observation_version}

    def step(self,action):
        if not self.action_space.contains(action):raise ValueError('action outside space')
        action=int(action);invalid=not bool(self.action_masks()[action])
        nonfuel=invalid and bool(self.env.unwrapped.action_masks()[action])
        legacy,reward,terminated,truncated,info=self.env.step(0 if invalid else action)
        if invalid:reward-=.01
        return self.observation(legacy),float(reward),terminated,truncated,{
            **info,'invalid_action':bool(invalid or info.get('invalid_action',False)),
            'v2_blocked_nonfuel':bool(nonfuel),'requested_action':action,
            'observation_version':self.observation_version}
