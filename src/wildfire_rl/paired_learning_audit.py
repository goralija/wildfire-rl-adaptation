"""Independent arithmetic checks; never changes the frozen training implementation."""
from collections import Counter
import numpy as np


def trajectory_score(initial,burned,line,noop,rewards):
    initial=np.asarray(initial);burned=np.asarray(burned);line=np.asarray(line);noop=np.asarray(noop)
    if (initial.ndim!=2 or noop.shape!=initial.shape or burned.shape!=(5,*initial.shape)
            or line.shape!=burned.shape or len(rewards)!=4):raise ValueError('invalid trajectory shapes')
    if any(not np.isin(a,[0,1]).all() for a in (initial,burned,line,noop)):raise ValueError('binary masks required')
    initial=initial.astype(bool);burned=burned.astype(bool);line=line.astype(bool);noop=noop.astype(bool)
    if (not np.array_equal(burned[0],initial) or line[0].any() or (initial&~burned).any()
            or (burned[:-1]&~burned[1:]).any() or (line[:-1]&~line[1:]).any()):
        raise ValueError('lost prior/cumulative damage or lines')
    raw=[int((b&~initial).sum()) for b in burned]
    charged=[int(((b|(l&noop))&~initial).sum()) for b,l in zip(burned,line)]
    expected=-np.diff(charged)/100.
    if not np.allclose(expected,rewards,atol=1e-12,rtol=0):raise ValueError('incremental charged return differs')
    return dict(noop_damage_cells=int((noop&~initial).sum()),raw_damage_cells=raw[-1],
                charged_damage_cells=charged[-1],extra_line_charge_cells=charged[-1]-raw[-1],
                line_cells_in_noop_footprint=int((line[-1]&noop&~initial).sum()),
                raw_saved_cells=int((noop&~initial).sum())-raw[-1],
                charged_saved_cells=int((noop&~initial).sum())-charged[-1])


def training_ledger(rows,schedule):
    if len(rows)!=4*len(schedule):raise ValueError('training row count differs')
    budget=1;previous=0;episodes=0
    for i,row in enumerate(rows):
        k=i%4
        if not k:budget=1;previous=0
        if (row['step']!=i+1 or row['scenario_id']!=schedule[i//4]
                or bool(row['done'])!=(k==3)):raise ValueError('training schedule/horizon differs')
        action=row['action']
        if action not in range(9) or action and not budget:raise ValueError('action after budget exhaustion')
        budget-=bool(action)
        if row['remaining_budget']!=budget:raise ValueError('training budget differs')
        charged=row['charged_damage_cells']
        expected=-(charged-previous)/100.
        if charged<previous or not np.isclose(expected,row['reward'],rtol=1e-6,atol=1e-7):
            raise ValueError('training charged reward differs (float32 tolerance)')
        previous=charged;episodes+=bool(row['done'])
    return dict(steps=len(rows),episodes=episodes)


def action_description(probabilities,masks,actions):
    p=np.asarray(probabilities,float);m=np.asarray(masks,bool);actions=np.asarray(actions,int)
    if (p.ndim!=2 or p.shape!=m.shape or actions.shape!=(len(p),) or not len(p)
            or not np.isfinite(p).all() or (p<0).any() or not np.allclose(p.sum(1),1,atol=1e-6)
            or (p[~m]>1e-7).any() or not m[np.arange(len(p)),actions].all()
            or not np.array_equal(p.argmax(1),actions)):raise ValueError('invalid masked action distribution')
    entropy=-(p*np.log(np.maximum(p,np.finfo(float).tiny))).sum(axis=1)
    maximum=np.log(m.sum(axis=1));valid=maximum>0
    counts=Counter(int(a) for a in actions)
    return dict(action_counts={str(k):v for k,v in sorted(counts.items())},distinct_greedy_actions=len(counts),
                dominant_action_count=max(counts.values()),cases=len(p),
                mean_entropy_nats=float(entropy.mean()),
                mean_entropy_fraction_of_legal_uniform=float((entropy[valid]/maximum[valid]).mean()) if valid.any() else None,
                mean_max_probability=float(p.max(axis=1).mean()))
