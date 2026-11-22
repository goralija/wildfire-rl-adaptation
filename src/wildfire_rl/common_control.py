"""Opt-in common-line PPO input and charged return, never a physics change.

The same-backend no-op endpoint is privileged reward bookkeeping. It is absent
from observations and action masks. Historical raw rewards remain untouched.
"""
import gymnasium as gym
import numpy as np

from .feds_repaired_learning import repaired_features
from .line_damage import score_line_damage

CONTRACT_VERSION='common-charged-increment-v1'
FEATURE_DIM=536


class ChargedLedger:
    def __init__(self,initial,noop):
        initial=np.asarray(initial)
        self.initial=initial.copy()
        self.noop=np.asarray(noop).copy()
        empty=np.zeros(initial.shape,bool)
        self.score=score_line_damage(initial,initial,self.noop,empty)
        if self.score['charged_damage_cells']:
            raise ValueError('initial new damage must be zero')
        self.burned=initial.astype(bool).copy()
        self.line=empty

    def update(self,burned,line):
        # Validate shape/binary values before coercion, including the initial mask.
        score=score_line_damage(self.initial,burned,self.noop,line)
        burned=np.asarray(burned,dtype=bool);line=np.asarray(line,dtype=bool)
        if (self.burned&~burned).any() or (self.line&~line).any():
            raise ValueError('cumulative damage/lines cannot disappear')
        increment=score['charged_damage_cells']-self.score['charged_damage_cells']
        if increment<0:raise ValueError('charged damage cannot decrease')
        self.burned=burned.copy();self.line=line.copy();self.score=score
        return increment


def encoded_observation(obs):
    result=np.asarray(repaired_features(obs,'terrain536'),dtype=np.float32)
    if result.shape!=(FEATURE_DIM,) or not np.isfinite(result).all():
        raise ValueError('finite terrain536 observation required')
    return result


class CommonControlEnv(gym.Wrapper):
    """Wrap one fixed-case v2 backend, preserving its public legality/geometry."""
    def __init__(self,env,noop_final):
        super().__init__(env)
        if env.action_space!=gym.spaces.Discrete(9):raise ValueError('nine actions required')
        self.observation_space=gym.spaces.Box(-np.inf,np.inf,(FEATURE_DIM,),dtype=np.float32)
        self._noop_final=np.asarray(noop_final).copy()
        self._done=True

    def action_masks(self):
        mask=np.asarray(self.env.action_masks(),dtype=bool).copy()
        if mask.shape!=(9,) or not mask[0]:raise ValueError('no-op must remain legal')
        return mask

    def reset(self,*,seed=None,options=None):
        obs,info=self.env.reset(seed=seed,options=options)
        base=self.unwrapped
        if base.initial_budget!=1 or base.remaining_budget!=1 or base.decision_index!=0:
            raise ValueError('common B1 reset required')
        self.ledger=ChargedLedger(base.cumulative_burned,self._noop_final)
        self._line=np.zeros(base.cumulative_burned.shape,bool)
        self._done=False;self._steps=0
        return encoded_observation(obs),dict(info,common_contract=CONTRACT_VERSION)

    def step(self,action):
        if self._done:raise RuntimeError('episode is done; call reset')
        if not self.action_space.contains(action):raise ValueError('action outside Discrete9')
        requested=int(action);invalid=not bool(self.action_masks()[requested])
        effective=0 if invalid else requested
        points=self.env.candidate_points()[effective-1] if effective else ()
        before=self.unwrapped.remaining_budget
        obs,_raw_reward,done,truncated,info=self.env.step(effective)
        count=int(info['line_cells_applied'])
        if info['invalid_action'] or count!=len(points):
            raise ValueError('v2 legality/geometry disagrees with backend')
        for x,y in points:self._line[y,x]=True
        if self.unwrapped.remaining_budget!=before-int(bool(points)):
            raise ValueError('line budget invariant failed')
        increment=self.ledger.update(self.unwrapped.cumulative_burned,self._line)
        self._steps+=1
        if truncated or bool(done)!=(self._steps==4):raise ValueError('four complete decisions required')
        self._done=bool(done)
        reward=-increment/100.-.01*invalid
        return encoded_observation(obs),float(reward),done,truncated,dict(
            info,**self.ledger.score,common_contract=CONTRACT_VERSION,
            scenario_id=self.unwrapped.scenario_id,split='train',
            requested_action=requested,effective_action=effective,invalid_action=invalid,
            charged_increment_cells=increment)


class CyclingCases(gym.Env):
    """One rollout slot with an explicit, reproducible case schedule."""
    def __init__(self,cases):
        if not cases:raise ValueError('at least one case required')
        self.cases=dict(cases);self.ids=tuple(cases);self.next_index=0
        first=next(iter(self.cases.values()))
        self.observation_space=first.observation_space;self.action_space=first.action_space
        for env in self.cases.values():
            if env.observation_space!=self.observation_space or env.action_space!=self.action_space:
                raise ValueError('case spaces must agree')
        self.active=None;self.episode_schedule=[]

    def reset(self,*,seed=None,options=None):
        super().reset(seed=seed)
        options=dict(options or {})
        if set(options)-{'scenario_id'}:raise ValueError('unsupported case options')
        sid=options.get('scenario_id',self.ids[self.next_index%len(self.ids)])
        if sid not in self.cases:raise ValueError('unknown case')
        if not options:self.next_index+=1
        self.active=self.cases[sid]
        obs,info=self.active.reset(seed=seed)
        self.episode_schedule.append(sid)
        return obs,dict(info,common_case_id=sid)

    def action_masks(self):
        if self.active is None:raise RuntimeError('reset required')
        return self.active.action_masks()

    def step(self,action):
        if self.active is None:raise RuntimeError('reset required')
        return self.active.step(action)

    def close(self):
        for env in self.cases.values():env.close()
