"""Independent post-run integer-cell audit; frozen training source stays unchanged."""
import math
import numpy as np
from .paired_learning_audit import trajectory_score


def reference_counts(reference):
    a=np.asarray(reference)
    if (a.ndim!=3 or len(a)!=5 or not np.isin(a,[0,1]).all()
            or (a[:-1].astype(bool)&~a[1:].astype(bool)).any()):
        raise ValueError('five binary cumulative no-op states required')
    a=a.astype(bool)
    return np.array([int((x&~a[0]).sum()) for x in a])


def centered_trajectory_score(initial,burned,line,reference,rewards,invalid=None):
    counts=reference_counts(reference);reference=np.asarray(reference,bool)
    initial=np.asarray(initial,bool);burned=np.asarray(burned);line=np.asarray(line)
    if initial.shape!=reference[0].shape or not np.array_equal(initial,reference[0]):raise ValueError('initial reference differs')
    if burned.shape!=reference.shape or line.shape!=reference.shape:raise ValueError('trajectory dimensions differ')
    invalid=np.zeros(4,bool) if invalid is None else np.asarray(invalid)
    if invalid.shape!=(4,) or not np.isin(invalid,[0,1]).all():raise ValueError('four invalid flags required')
    charges=np.array([int(((b.astype(bool)|(l.astype(bool)&reference[-1]))&~initial).sum()) for b,l in zip(burned,line)])
    expected=(np.diff(counts)-np.diff(charges))/100.-.01*invalid
    if np.shape(rewards)!=(4,) or not np.allclose(rewards,expected,atol=1e-12,rtol=0):
        raise ValueError('centered increment/penalty differs')
    score=trajectory_score(initial,burned,line,reference[-1],-np.diff(charges)/100.)
    if not np.isclose(math.fsum(rewards),(counts[-1]-charges[-1])/100.-.01*invalid.sum(),atol=1e-12,rtol=0):
        raise ValueError('centered final return differs')
    return score


def centered_training_ledger(rows,schedule,references):
    if len(rows)!=4*len(schedule):raise ValueError('training length differs')
    counts={sid:reference_counts(references[sid]) for sid in set(schedule)}
    for i,row in enumerate(rows):
        k=i%4;sid=schedule[i//4]
        if k==0:budget=1;previous=0
        if row['step']!=i+1 or row['scenario_id']!=sid or bool(row['done'])!=(k==3):raise ValueError('schedule/horizon differs')
        action=row['action']
        if action not in range(9) or (action and not budget):raise ValueError('action exceeds budget')
        budget-=bool(action)
        charged=row['charged_damage_cells'];inc=charged-previous;noop=int(counts[sid][k+1]-counts[sid][k])
        reward=float(np.float32((noop-inc)/100.))
        if (row['remaining_budget']!=budget or inc<0 or row['charged_increment_cells']!=inc
                or row['noop_increment_cells']!=noop or row['original_reward']!=-inc/100.
                or row['reward']!=reward):raise ValueError('training centered reward/accounting differs')
        previous=charged
    return dict(steps=len(rows),episodes=len(schedule))
