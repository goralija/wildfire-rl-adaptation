"""Terrain536 encoder, extracted unchanged from the archived observation study."""
import numpy as np


def _legacy_features(observation):
    grid = np.asarray(observation["grid"], dtype=float)
    if grid.shape != (4, 16, 16):
        raise ValueError("expected the locked 4x16x16 observation")
    burned, front, lines, fuel = grid
    yy, xx = np.indices((16, 16), dtype=float)
    xx, yy = xx / 15, yy / 15

    def centroid(layer):
        weight = layer.sum()
        return ((float((layer * xx).sum() / weight), float((layer * yy).sum() / weight))
                if weight else (.5, .5))

    bx, by = centroid(burned)
    fx, fy = centroid(front)
    weather = np.asarray(observation["weather"], dtype=float)
    dx, dy = fx - bx, fy - by
    ahead_fuel = []
    for angle in np.arange(8) * np.pi / 4:
        projection = (xx-fx) * np.cos(angle) + (yy-fy) * np.sin(angle)
        region = projection > 0
        ahead_fuel.append(float(fuel[region].mean()) if region.any() else float(fuel.mean()))
    result = np.asarray([*weather, float(observation["time"][0]),
                         burned.mean(), front.mean(), lines.mean(), fuel.mean(), fuel.std(),
                         bx, by, fx, fy, dx, dy, dx * weather[1] - dy * weather[2],
                         float((fuel * front).sum() / front.sum()) if front.sum() else 0.,
                         *observation["budget"], *ahead_fuel])
    if not np.isfinite(result).all():
        raise ValueError("non-finite policy features")
    return result


def _centroid(layer):
    yy,xx=np.indices(layer.shape,dtype=float);xx/=layer.shape[1]-1;yy/=layer.shape[0]-1
    total=layer.sum()
    return (float((layer*xx).sum()/total),float((layer*yy).sum()/total)) if total else (.5,.5)


def terrain_features(obs):
    legacy=_legacy_features(obs)
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
    terrain=[*g[17:20].mean(axis=(1,2)),*g[17:20].std(axis=(1,2))]
    for k in range(8):
        t=patch[k,17:20];line=lines[k]
        terrain.extend([*t.mean(axis=(1,2)),*t.std(axis=(1,2)),
                        *(t[:,line].mean(axis=1) if line.any() else np.zeros(3))])
    return np.concatenate([result,np.asarray(terrain)])
