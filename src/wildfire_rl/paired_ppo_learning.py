"""ADR-051 design, bounded-memory scheduling and paired descriptive summaries."""
import hashlib
import json
from pathlib import Path
import gymnasium as gym
import numpy as np
from .common_control import FEATURE_DIM


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_design(plan):
    fitting=plan['fitting_cases'];evaluation=plan['evaluation_cases'];seeds=plan['model_seeds']
    if (not fitting or not evaluation or len(set(fitting))!=len(fitting)
            or len(set(evaluation))!=len(evaluation) or set(fitting)&set(evaluation)
            or len(set(seeds))!=len(seeds) or not seeds
            or plan['checkpoints']!=[0,512,2048] or plan['training_steps']!=2048):
        raise ValueError('invalid frozen fitting/evaluation/seed/checkpoint design')


def case_schedule(ids,seed):
    if not ids or len(set(ids))!=len(ids):raise ValueError('distinct cases required')
    return sorted(ids,key=lambda sid:hashlib.sha256(('TASK043:%d:%s'%(seed,sid)).encode()).hexdigest())


class LazyTrainingCases(gym.Env):
    """Keep one simulator in memory; exactly the same schedule in both backends."""
    observation_space=gym.spaces.Box(-np.inf,np.inf,(FEATURE_DIM,),dtype=np.float32)
    action_space=gym.spaces.Discrete(9)

    def __init__(self,ids,factory):
        if not ids or len(set(ids))!=len(ids):raise ValueError('distinct fitting cases required')
        self.ids=tuple(ids);self.factory=factory;self.active=None
        self.next_index=0;self.episode_schedule=[]

    def reset(self,*,seed=None,options=None):
        super().reset(seed=seed)
        if options:raise ValueError('training case cannot be overridden')
        self.close();sid=self.ids[self.next_index%len(self.ids)]
        self.active=self.factory(sid);obs,info=self.active.reset(seed=seed)
        if info['scenario_id']!=sid:raise ValueError('factory returned another case')
        self.next_index+=1;self.episode_schedule.append(sid)
        return obs,info

    def action_masks(self):
        if self.active is None:raise RuntimeError('reset required')
        return self.active.action_masks()

    def step(self,action):
        if self.active is None:raise RuntimeError('reset required')
        return self.active.step(action)

    def close(self):
        if self.active is not None:self.active.close();self.active=None


def completed_job(root,guard):
    root=Path(root);path=root/'done.json'
    if not path.exists():return False
    record=json.loads(path.read_text())
    if record['guard']!=guard:raise ValueError('completed job guard mismatch')
    if not record['files']:raise ValueError('empty completion receipt')
    for name,digest in record['files'].items():
        p=root/name
        if p.resolve().parent!=root.resolve() or not p.is_file() or sha(p)!=digest:
            raise ValueError('completed job file missing or changed')
    return True


def _description(values):
    a=np.asarray(values,float)
    if not len(a):return dict(n=0,mean=None,ci95=None)
    if not np.isfinite(a).all():raise ValueError('finite paired values required')
    rng=np.random.default_rng(0)
    sampled=a[rng.integers(len(a),size=(10000,len(a)))].mean(axis=1)
    return dict(n=len(a),mean=float(a.mean()),ci95=np.quantile(sampled,[.025,.975]).tolist())


def summarize_learning(policies,baselines,ids,seeds):
    if not ids or not seeds or len(set(ids))!=len(ids) or len(set(seeds))!=len(seeds):raise ValueError('distinct ids/seeds required')
    p={};b={}
    for row in policies:
        key=(row['backend'],row['scenario_id'],row['seed'],row['checkpoint'])
        if key in p:raise ValueError('duplicate policy row')
        p[key]=row
    for row in baselines:
        key=(row['backend'],row['scenario_id'],row['method'])
        if key in b:raise ValueError('duplicate baseline row')
        b[key]=row
    for row in policies+baselines:
        for key in ('noop_damage_cells','charged_damage_cells'):
            if not np.isfinite(row[key]) or row[key]<0:raise ValueError('finite nonnegative damage required')
    expected={(be,sid,seed,stage) for be in ('simfire','ca') for sid in ids for seed in seeds for stage in (0,512,2048)}
    if set(p)!=expected:raise ValueError('missing or unexpected policy row')
    methods=sorted({row['method'] for row in baselines})
    if not {'noop','advancing_front64'}<=set(methods):raise ValueError('fixed references missing')
    if set(b)!={(be,sid,m) for be in ('simfire','ca') for sid in ids for m in methods}:
        raise ValueError('missing or unexpected heuristic row')
    noop={be:np.array([b[be,sid,'noop']['noop_damage_cells'] for sid in ids],float) for be in ('simfire','ca')}
    if any(b[be,sid,'noop']['charged_damage_cells']!=b[be,sid,'noop']['noop_damage_cells']
           for be in ('simfire','ca') for sid in ids):raise ValueError('no-op outcome must equal its reference')
    for (be,sid,seed,stage),row in p.items():
        if row['noop_damage_cells']!=b[be,sid,'noop']['noop_damage_cells']:raise ValueError('policy no-op differs')
    for (be,sid,m),row in b.items():
        if row['noop_damage_cells']!=b[be,sid,'noop']['noop_damage_cells']:raise ValueError('heuristic no-op differs')
    joint=(noop['simfire']>0)&(noop['ca']>0);result=dict(joint_positive_ids=[s for s,k in zip(ids,joint) if k],backends={})
    gaps={}
    for be in ('simfire','ca'):
        n=noop[be];stage_damage={};metrics={}
        def metric(d,raw=None):
            return dict(mean_saved_percent_joint=float(((n[joint]-d[joint])/n[joint]*100).mean()) if joint.any() else None,
                pooled_saved_percent_all=float((n-d).sum()/n.sum()*100) if n.sum()>0 else None,
                mean_charged_ha_all=float(d.mean()*3.24),mean_saved_ha_all=float((n-d).mean()*3.24),
                mean_raw_ha_all=float((d if raw is None else raw).mean()*3.24))
        for stage in (0,512,2048):
            byseed=np.array([[p[be,sid,seed,stage]['charged_damage_cells'] for sid in ids] for seed in seeds],float)
            raw=np.array([[p[be,sid,seed,stage].get('raw_damage_cells',p[be,sid,seed,stage]['charged_damage_cells'])
                           for sid in ids] for seed in seeds],float)
            stage_damage[stage]=byseed.mean(axis=0)
            metrics[str(stage)]={**metric(stage_damage[stage],raw.mean(axis=0)),
                'model_seeds':{str(seed):metric(d,r) for seed,d,r in zip(seeds,byseed,raw)}}
        heuristics={m:metric(np.array([b[be,sid,m]['charged_damage_cells'] for sid in ids],float),
            np.array([b[be,sid,m].get('raw_damage_cells',b[be,sid,m]['charged_damage_cells']) for sid in ids],float)) for m in methods}
        front=np.array([b[be,sid,'advancing_front64']['charged_damage_cells'] for sid in ids],float)
        initial_delta=(stage_damage[0][joint]-stage_damage[2048][joint])/n[joint]*100
        gaps[be]=(front[joint]-stage_damage[2048][joint])/n[joint]*100
        di=_description(initial_delta);dh=_description(gaps[be])
        result['backends'][be]=dict(checkpoints=metrics,heuristics=heuristics,
            zero_noop_ids=[sid for sid,v in zip(ids,n) if not v],
            final_minus_initial_pp=di,final_minus_front_pp=dh,
            descriptive_positive_signal=bool(di['ci95'] and dh['ci95'] and min(di['ci95'][0],dh['ci95'][0])>0))
    result['ca_minus_sf_relative_gap_pp']=_description(gaps['ca']-gaps['simfire'])
    result['scope']='Exploratory TRAIN development; seeds averaged within fire; descriptive intervals, no physical validation'
    return result
