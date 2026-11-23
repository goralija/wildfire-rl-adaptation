"""Opt-in reward v2: same charged cost, action-independent case offset at gamma1."""
import gymnasium as gym
import numpy as np
from .paired_ppo_learning import _description

REWARD_VERSION='common-centered-charged-increment-v2'


class CenteredControlEnv(gym.Wrapper):
    def __init__(self,env,noop_trajectory):
        super().__init__(env)
        a=np.asarray(noop_trajectory)
        if (a.ndim!=3 or len(a)!=5 or not np.isin(a,[0,1]).all()
                or (a[:-1].astype(bool)&~a[1:].astype(bool)).any()):
            raise ValueError('five binary cumulative no-op states required')
        self.reference=a.astype(bool).copy();self.decision=0

    def action_masks(self):return self.env.action_masks()

    def reset(self,*,seed=None,options=None):
        obs,info=self.env.reset(seed=seed,options=options)
        initial=self.env.ledger.initial.astype(bool)
        if (initial.shape!=self.reference[0].shape or not np.array_equal(initial,self.reference[0])
                or not np.array_equal(self.env.ledger.noop,self.reference[-1])):
            raise ValueError('no-op reference does not match this case/backend')
        self.counts=np.array([int((b&~initial).sum()) for b in self.reference])
        self.decision=0
        return obs,dict(info,base_common_contract=info['common_contract'],common_contract=REWARD_VERSION)

    def step(self,action):
        obs,raw,done,trunc,info=self.env.step(action)
        k=self.decision;increment=int(self.counts[k+1]-self.counts[k])
        # Count arithmetic avoids cancellation between two large float rewards.
        reward=(increment-info['charged_increment_cells'])/100.-.01*info['invalid_action']
        self.decision+=1
        return obs,float(reward),done,trunc,dict(info,base_common_contract=info['common_contract'],
            common_contract=REWARD_VERSION,original_charged_reward=raw,noop_increment_cells=increment,
            noop_cumulative_new_cells=int(self.counts[k+1]))


def _values(cost,noop,joint):
    c=np.asarray(cost,float);n=np.asarray(noop,float);j=np.asarray(joint,bool)
    if c.ndim==1:c=c[None,:]
    if (c.ndim!=2 or not len(c) or c.shape[1:]!=n.shape or n.ndim!=1 or not len(n)
            or j.shape!=n.shape or not np.isfinite(c).all() or not np.isfinite(n).all()
            or (c<0).any() or (n<0).any() or (j&(n<=0)).any()):raise ValueError('invalid paired damage/denominator')
    return c,n,j


def compare_costs(centered,baseline,noop,joint):
    c,n,j=_values(centered,noop,joint);b,_,_=_values(baseline,noop,joint)
    if b.shape[1:]!=c.shape[1:]:raise ValueError('paired fires differ')
    # Average paired model seeds within a fire; each fire appears once in bootstrap.
    values=(b.mean(axis=0)[j]-c.mean(axis=0)[j])/n[j]*100
    return _description(values)


def method_metrics(cost,noop,joint,raw=None):
    c,n,j=_values(cost,noop,joint);d=c.mean(axis=0);positive=n>0
    result=dict(mean_saved_percent_joint=float(((n[j]-d[j])/n[j]*100).mean()) if j.any() else None,
        mean_saved_percent_own_positive=float(((n[positive]-d[positive])/n[positive]*100).mean()) if positive.any() else None,
        pooled_saved_percent_all=float((n-d).sum()/n.sum()*100) if n.sum()>0 else None,
        mean_charged_ha_all=float(d.mean()*3.24),mean_saved_ha_all=float((n-d).mean()*3.24),
        undefined_case_indices=np.flatnonzero(~positive).tolist())
    if raw is not None:
        r,_,_=_values(raw,noop,joint)
        if r.shape!=c.shape or (r>c).any():raise ValueError('raw damage exceeds charged damage')
        result['mean_raw_ha_all']=float(r.mean()*3.24)
    return result
