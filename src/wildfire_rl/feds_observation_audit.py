"""TRAIN-only nested observation ablation, ADR-035. No simulator changes."""
from __future__ import annotations

import hashlib
import numpy as np

from .feds_b1_learning import observation_features, RidgeModel, _with_noop_lower_bound


def audit_features(observation, kind):
    summary=observation_features(observation)
    if kind=='summary':return summary
    grid=np.asarray(observation['grid'],dtype=float)
    if kind=='full_grid':
        return np.concatenate([grid.ravel(),np.asarray(observation['weather']),
                               np.asarray(observation['time']),np.asarray(observation['budget'])])
    if kind!='directional':raise ValueError('unknown observation representation')
    front,fuel=grid[1],grid[3]
    yy,xx=np.indices(front.shape,dtype=float);xx/=15;yy/=15
    total=front.sum()
    fx=float((front*xx).sum()/total) if total else .5
    fy=float((front*yy).sum()/total) if total else .5
    rx,ry=xx-fx,yy-fy;radius=np.hypot(rx,ry)
    result=[]
    for angle in np.arange(8)*np.pi/4:
        projection=rx*np.cos(angle)+ry*np.sin(angle)
        region=(projection>=radius/np.sqrt(2)) & (radius>0)
        weight=front*region;mass=weight.sum()
        near=region & (radius<=2/15);far=region & (radius>2/15)
        def mean(mask):return float(fuel[mask].mean()) if mask.any() else 0.
        active=region & (front>0)
        result.extend([float(mass/total) if total else 0.,
                       float(projection[active].max()/np.sqrt(2)) if active.any() else 0.,
                       mean(region),float((fuel*weight).sum()/mass) if mass else 0.,
                       mean(near),mean(far)])
    return np.concatenate([summary,np.asarray(result)])


class RBFModel:
    def __init__(self,x,y,alpha,bandwidth):
        if alpha<=0 or bandwidth<=0:raise ValueError('positive kernel parameters required')
        self.mean=x.mean(axis=0);self.scale=x.std(axis=0);self.scale[self.scale<1e-9]=1.
        self.x=(x-self.mean)/self.scale
        distance=self.distances(self.x,self.x)
        positive=distance[distance>1e-12]
        self.distance_scale=float(np.median(positive)) if positive.size else 1.
        self.bandwidth=bandwidth;self.y_mean=y.mean(axis=0)
        kernel=np.exp(-distance/(2*bandwidth**2*self.distance_scale))
        self.coef=np.linalg.solve(kernel+alpha*np.eye(len(x)),y-self.y_mean)

    @staticmethod
    def distances(a,b):
        return np.maximum(0.,(a*a).sum(axis=1)[:,None]+(b*b).sum(axis=1)[None,:]-2*a@b.T)

    def predict(self,x):
        normalized=(np.atleast_2d(x)-self.mean)/self.scale
        distance=self.distances(normalized,self.x)
        return np.exp(-distance/(2*self.bandwidth**2*self.distance_scale))@self.coef+self.y_mean


def fit_models(x,gains,masks,kind,config):
    models=[None]*4;future=np.zeros(len(x))
    for k in reversed(range(4)):
        targets=gains[:,k].copy();targets[:,0]=future
        if kind=='rbf':model=RBFModel(x[:,k],targets,*config)
        elif kind=='ridge':model=RidgeModel(x[:,k],targets,config[0])
        else:raise ValueError('unknown Q model')
        models[k]=model
        q=_with_noop_lower_bound(model.predict(x[:,k]))
        future=np.where(masks[:,k],q,-np.inf).max(axis=1)
    return models


def predict_sequence(models,x,masks):
    actions=[0]*4
    for k in range(4):
        if not masks[k,0]:raise ValueError('no-op must stay legal')
        q=_with_noop_lower_bound(models[k].predict(x[k]))[0]
        action=int(np.argmax(np.where(masks[k],q,-np.inf)))
        if action:
            actions[k]=action
            break
    return actions


def inner_folds(ids):
    if len(set(ids))!=len(ids) or len(ids)<4:raise ValueError('unique fitting fire IDs required')
    order=sorted(range(len(ids)),key=lambda i:hashlib.sha256(('TASK034:'+ids[i]).encode()).hexdigest())
    return [order[k::4] for k in range(4)]


def action_gain(gains,actions):
    for k,action in enumerate(actions):
        if action:return float(gains[k,action])
    return 0.


def nested_actions(x,gains,masks,ids,heldout,kind,candidates):
    if len(set(ids))!=len(ids) or not 0<=heldout<len(ids):raise ValueError('invalid fire IDs/index')
    train=np.array([i for i in range(len(ids)) if i!=heldout])
    if len(train)<8:raise ValueError('at least eight fitting fires required')
    folds=inner_folds([ids[i] for i in train]);scores=[]
    for config in candidates:
        values=[]
        for validation_positions in folds:
            validation=train[validation_positions]
            fit=np.array([i for i in train if i not in set(validation)])
            models=fit_models(x[fit],gains[fit],masks[fit],kind,config)
            for i in validation:
                actions=predict_sequence(models,x[i],masks[i])
                values.append(action_gain(gains[i],actions))
        scores.append(float(np.mean(values)))
    winner=int(np.argmax(scores));chosen=candidates[winner]
    models=fit_models(x[train],gains[train],masks[train],kind,chosen)
    return {'actions':predict_sequence(models,x[heldout],masks[heldout]),
            'selected_config':list(chosen),'inner_mean_saved_ha':scores[winner]}
