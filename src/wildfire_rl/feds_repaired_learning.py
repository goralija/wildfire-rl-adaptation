"""Fixed current-information representations for ADR-037 paired ablations."""
from __future__ import annotations
import numpy as np
from .feds_b1_learning import observation_features

REPRESENTATIONS=('legacy28','categorical154','local458','terrain536')


def _centroid(layer):
    yy,xx=np.indices(layer.shape,dtype=float);xx/=layer.shape[1]-1;yy/=layer.shape[0]-1
    total=layer.sum()
    return (float((layer*xx).sum()/total),float((layer*yy).sum()/total)) if total else (.5,.5)


def repaired_features(obs,representation):
    if representation not in REPRESENTATIONS:raise ValueError('unknown representation')
    legacy=observation_features(obs)
    if representation=='legacy28':return legacy
    g=np.asarray(obs['global_grid'],dtype=float)
    if g.shape!=(20,64,64) or not np.isfinite(g).all():raise ValueError('invalid v2 global observation')
    categories=g[3:17].reshape(14,16,4,16,4).mean(axis=(2,4))
    front=np.asarray(obs['grid'],dtype=float)[1];fx,fy=_centroid(front)
    yy,xx=np.indices((16,16),dtype=float);rx,ry=xx/15-fx,yy/15-fy;radius=np.hypot(rx,ry)
    hist=[*categories.mean(axis=(1,2))]
    for angle in np.arange(8)*np.pi/4:
        cone=((rx*np.cos(angle)+ry*np.sin(angle))>=radius/np.sqrt(2)) & (radius>0)
        hist.extend(categories[:,cone].mean(axis=1) if cone.any() else np.zeros(14))
    result=np.concatenate([legacy,np.asarray(hist)])
    if representation=='categorical154':return result
    bx,by=_centroid(g[0]);fx,fy=_centroid(g[1]);yy,xx=np.indices((64,64),dtype=float);xx/=63;yy/=63
    mass=g[1].sum()
    sx=np.sqrt((g[1]*(xx-fx)**2).sum()/mass) if mass else 0.
    sy=np.sqrt((g[1]*(yy-fy)**2).sum()/mass) if mass else 0.
    fine=[bx,by,fx,fy,sx,sy,fx-bx,fy-by]
    patch=np.asarray(obs['action_patches'],dtype=float);lines=np.asarray(obs['candidate_line_masks'],dtype=bool)
    centres=np.asarray(obs['candidate_centres'],dtype=float)
    local=[]
    for k in range(8):
        p=patch[k];line=lines[k];lcount=int(line.sum())
        line_hist=p[3:17,line].mean(axis=1) if lcount else np.zeros(14)
        count=p[1].sum();px,py=_centroid(p[1]);px=(px-.5)*2;py=(py-.5)*2
        fpoints=np.argwhere(p[1]>0);lpoints=np.argwhere(line)
        distance=float(np.sqrt(((fpoints[:,None]-lpoints[None,:])**2).sum(axis=2)).min()/24.) if len(fpoints) and len(lpoints) else 1.
        local.extend([*centres[k],lcount/9.,*line_hist,*p[:3].mean(axis=(1,2)),
                      px if count else 0.,py if count else 0.,distance,*p[3:17].mean(axis=(1,2))])
    result=np.concatenate([result,np.asarray(fine),np.asarray(local)])
    if representation=='local458':return result
    terrain=[*g[17:20].mean(axis=(1,2)),*g[17:20].std(axis=(1,2))]
    for k in range(8):
        t=patch[k,17:20];line=lines[k]
        terrain.extend([*t.mean(axis=(1,2)),*t.std(axis=(1,2)),
                        *(t[:,line].mean(axis=1) if line.any() else np.zeros(3))])
    return np.concatenate([result,np.asarray(terrain)])


def legal_oracle(gains,mask):
    gains=np.asarray(gains,dtype=float);mask=np.asarray(mask,dtype=bool)
    if gains.shape!=(4,9) or mask.shape!=gains.shape or not mask[:,0].all():raise ValueError('invalid B1 gains/mask')
    return float(max(0.,np.max(np.where(mask[:,1:],gains[:,1:],-np.inf))))


def select_reference(values,heldout):
    values=np.asarray(values,dtype=float)
    if values.ndim!=2 or len(values)<2 or not 0<=heldout<len(values) or not np.isfinite(values).all():
        raise ValueError('invalid reference scores/index')
    fitting=np.delete(values,heldout,axis=0)
    return int(np.argmax(fitting.mean(axis=0)))
