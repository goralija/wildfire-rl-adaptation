"""ADR-053 descriptive reference/signal arithmetic, separate from frozen PPO code."""
import numpy as np


def _costs(values):
    a=np.asarray(values,float)
    if a.ndim!=2 or a.shape[1]!=9 or not len(a) or not np.isfinite(a).all():
        raise ValueError('finite nonempty case-by-nine cost matrix required')
    return a


def uniform_line_expectation(costs,mask):
    c=np.asarray(costs,float);m=np.asarray(mask,bool)
    if c.shape!=(9,) or m.shape!=(9,) or not m[0] or not np.isfinite(c).all():
        raise ValueError('finite nine costs and legal no-op required')
    legal=np.flatnonzero(m[1:])+1
    return float(c[legal].mean()) if len(legal) else float(c[0])


def select_fixed_sector(fitting_costs):
    return int(_costs(fitting_costs).mean(axis=0).argmin())


def reference_metrics(noop,cost,joint):
    n=np.asarray(noop,float);c=np.asarray(cost,float);j=np.asarray(joint,bool)
    if (n.ndim!=1 or not len(n) or c.shape!=n.shape or j.shape!=n.shape
            or not np.isfinite(n).all() or not np.isfinite(c).all() or (n<0).any()
            or (c<0).any() or (j&(n<=0)).any()):raise ValueError('invalid reference counts/denominator')
    own=n>0
    pct=[float(100*(x-y)/x) if x>0 else None for x,y in zip(n,c)]
    return dict(mean_saved_percent_joint=float(((n[j]-c[j])/n[j]*100).mean()) if j.any() else None,
        mean_saved_percent_own_positive=float(((n[own]-c[own])/n[own]*100).mean()) if own.any() else None,
        pooled_saved_percent_all=float(100*(n-c).sum()/n.sum()) if n.sum()>0 else None,
        mean_charged_ha_all=float(c.mean()*3.24),mean_saved_ha_all=float((n-c).mean()*3.24),
        per_case_saved_percent=pct,undefined_case_indices=np.flatnonzero(~own).tolist())


def centered_rewards(rewards,noop_increments):
    r=np.asarray(rewards,float);n=np.asarray(noop_increments,float)
    if (r.ndim!=1 or n.shape!=r.shape or not np.isfinite(r).all()
            or not np.isfinite(n).all() or (n<0).any()):raise ValueError('finite aligned rewards and no-op increments required')
    return r+n/100.


def episodic_returns(rewards):
    r=np.asarray(rewards,float)
    if r.ndim!=1 or not len(r) or len(r)%4 or not np.isfinite(r).all():
        raise ValueError('complete finite four-step episodes required')
    return np.cumsum(r.reshape(-1,4)[:,::-1],axis=1)[:,::-1].reshape(-1)


def cost_decomposition(costs,masks):
    c=_costs(costs);m=np.asarray(masks,bool)
    if m.shape!=c.shape or not m[:,0].all():raise ValueError('aligned masks with legal no-op required')
    means=np.array([row[mask].mean() for row,mask in zip(c,m)])
    within=float(np.mean([row[mask].var() for row,mask in zip(c,m)]))
    between=float(means.var());total=within+between
    return dict(within_case_variance=within,between_case_variance=between,
                between_fraction=between/total if total else None,
                mean_case_range=float(np.mean([np.ptp(row[mask]) for row,mask in zip(c,m)])),
                definition='Equal fire weight; uniform over legal initial actions including no-op; diagnostic, not sampling uncertainty')
