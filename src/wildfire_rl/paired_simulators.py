"""ADR-043 common vegetation/line-control bridge, distinct from native CA units."""
from types import SimpleNamespace
import gymnasium as gym
import numpy as np
from .feds_simfire_env import FedsSimFireEnv,line_points_for,placed_line_length_m
from .synthetic_ca import Landscape,SpreadParams,initial_state_from_masks


class CABridgeEnv(FedsSimFireEnv):
    """Reuse the exact SimFire action geometry/legacy observation, never its dynamics."""
    def __init__(self,inputs,hourly_weather,observed_forcing,seed=0):
        if inputs['split']!='train':raise ValueError('bridge only accepts TRAIN')
        self.fuel=np.asarray(inputs['fuel'])
        elevation=np.asarray(inputs['elevation'])
        if self.fuel.shape!=(256,256) or elevation.shape!=self.fuel.shape or not np.isfinite(elevation).all():
            raise ValueError('same finite native grid required')
        burnable=(self.fuel>=1)&(self.fuel<=13)
        if np.any(np.asarray(inputs['front'],bool)&~burnable):raise ValueError('unsupported initial front')
        self.land=Landscape(np.where(burnable,self.fuel,99),elevation)
        self.inputs=inputs;self.hourly_weather=hourly_weather;self.observed_forcing=observed_forcing
        if len(hourly_weather)!=48 or len(observed_forcing)!=4:raise ValueError('48h and four observations required')
        self.seed_value=int(seed);self.scenario_id=inputs['scenario_id'];self.split='train'
        self._input_cache={self.scenario_id:inputs};self.block_count=16;self.horizon_steps=4
        self.line_placement='front_edge';self.max_budget=4
        self.action_space=gym.spaces.Discrete(9)
        self.reset()
        obs=self._observation()
        self.observation_space=gym.spaces.Dict({k:gym.spaces.Box(-1,1,v.shape,dtype=np.float32) for k,v in obs.items()})

    def _sync(self):
        state=self.fire.state.copy();state[self.fire.line]=3
        self.simulation=SimpleNamespace(fire_map=state)
        self.cumulative_burned=self.fire.ever_burned

    def reset(self,*,seed=None,options=None):
        gym.Env.reset(self,seed=seed)
        self.fire=initial_state_from_masks(self.land,self.seed_value,SpreadParams(),
                                           self.inputs['scar'],self.inputs['front'])
        self.initial_budget=self.remaining_budget=1;self.decision_index=0;self._done=False
        self._sync()
        return self._observation(),{'scenario_id':self.scenario_id,'split':'train'}

    def step(self,action):
        if self._done:raise RuntimeError('reset required')
        if not self.action_space.contains(action):raise ValueError('invalid action')
        action=int(action);invalid=not self.action_masks()[action]
        action=0 if invalid else action;points=()
        if action:
            points=line_points_for('front_edge',self.simulation.fire_map,self.fire.burning,action-1)
            if points:
                for x,y in points:self.fire.line[y,x]=True
                self.remaining_budget-=1
        previous=self.fire.ever_burned.copy()
        for hour in range(self.decision_index*12,(self.decision_index+1)*12):
            if not self.fire.active:continue
            self.fire.set_weather(self.hourly_weather[hour])
            for _ in range(30):self.fire.step_substep()
        self.decision_index+=1;self._done=self.decision_index==4;self._sync()
        if (previous&~self.cumulative_burned).any():raise AssertionError('lost cumulative damage')
        added=int((self.cumulative_burned&~previous).sum())
        return self._observation(),-added/100.-.01*invalid,self._done,False,{
            'invalid_action':bool(invalid),'remaining_budget':self.remaining_budget,
            'line_cells_applied':len(points),'line_length_m':placed_line_length_m(action-1,len(points)) if points else 0.,
            'decision_step':self.decision_index,'fire_active':self.fire.active}


def fraction(saved,noop):
    return float(saved)/float(noop) if noop>0 else None


def summarize_pair(sf,ca):
    if len(sf)!=len(ca) or not sf or [r['scenario_id'] for r in sf]!=[r['scenario_id'] for r in ca]:
        raise ValueError('same ordered paired cases required')
    a=np.array([[r['noop'],r['damage']] for r in sf],float)
    b=np.array([[r['noop'],r['damage']] for r in ca],float)
    if not np.isfinite(a).all() or not np.isfinite(b).all() or (a<0).any() or (b<0).any():
        raise ValueError('finite nonnegative damage counts required')
    joint=(a[:,0]>0)&(b[:,0]>0)
    x=(a[joint,0]-a[joint,1])/a[joint,0]
    y=(b[joint,0]-b[joint,1])/b[joint,0]
    delta=y-x;ci=None
    if len(delta):
        rng=np.random.default_rng(0)
        ci=np.quantile(delta[rng.integers(len(delta),size=(10000,len(delta)))].mean(1),[.025,.975]).tolist()
    return {'cases':len(a),'joint_positive_cases':int(joint.sum()),
            'sf_zero_noop_cases':int((a[:,0]==0).sum()),'ca_zero_noop_cases':int((b[:,0]==0).sum()),
            'joint_case_ids':[r['scenario_id'] for r,ok in zip(sf,joint) if ok],
            'sf_mean_fraction_joint':float(x.mean()) if len(x) else None,
            'ca_mean_fraction_joint':float(y.mean()) if len(y) else None,
            'ca_minus_sf_fraction_joint':float(delta.mean()) if len(delta) else None,
            'ca_minus_sf_descriptive_ci95':ci,
            'sf_pooled_fraction_all':fraction((a[:,0]-a[:,1]).sum(),a[:,0].sum()),
            'ca_pooled_fraction_all':fraction((b[:,0]-b[:,1]).sum(),b[:,0].sum()),
            'sf_mean_noop_ha':float(a[:,0].mean()*3.24),'ca_mean_noop_ha':float(b[:,0].mean()*3.24),
            'sf_mean_saved_ha':float((a[:,0]-a[:,1]).mean()*3.24),
            'ca_mean_saved_ha':float((b[:,0]-b[:,1]).mean()*3.24)}
