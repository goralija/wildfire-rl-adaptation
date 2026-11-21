#!/usr/bin/env python3
"""Secondary description of ALL three predeclared CA spread replicates, no selection."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wildfire_rl.ca_controlled import clustered_contrast


def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('analysis',type=Path);a.add_argument('--out',type=Path,required=True);args=a.parse_args()
    if args.out.exists():raise FileExistsError(args.out)
    p=json.loads(args.analysis.read_text());ids=p['plan']['cases'];methods=p['plan']['heuristics']+['matched_rbf']
    byrep={str(rep):{r['scenario_id']:r for r in p['robustness_rows'] if r['replicate']==rep} for rep in (1,2)}
    summary={}
    for m in methods:
        sf=p['results']['sf'][m]
        reps=[p['results']['ca'][m]]+[[byrep[str(rep)][sid]['results'][m] for sid in ids] for rep in (1,2)]
        if any([r['scenario_id'] for r in rows]!=ids for rows in [sf]+reps):raise ValueError('case order mismatch')
        joint=np.array([r['noop']>0 for r in sf])
        for rows in reps:joint&=np.array([r['noop']>0 for r in rows])
        x=np.array([(r['noop']-r['damage'])/r['noop'] for r,ok in zip(sf,joint) if ok])
        ys=np.array([[(r['noop']-r['damage'])/r['noop'] for r,ok in zip(rows,joint) if ok] for rows in reps])
        ca_noops=np.array([[r['noop'] for r in rows] for rows in reps],float)
        ca_damages=np.array([[r['damage'] for r in rows] for rows in reps],float)
        summary[m]={'joint_cases':int(joint.sum()),'joint_ids':[sid for sid,ok in zip(ids,joint) if ok],
            'sf_mean_fraction':float(x.mean()) if len(x) else None,
            'ca_mean_fraction':float(ys.mean()) if len(x) else None,
            'ca_fraction_each_replicate':ys.mean(1).tolist() if len(x) else None,
            'ca_minus_sf':clustered_contrast(ys.mean(0)[:,None],x[:,None]) if len(x) else None,
            'sf_mean_noop_ha':float(np.mean([r['noop'] for r in sf])*3.24),
            'ca_mean_noop_ha':float(ca_noops.mean()*3.24),
            'sf_mean_saved_ha':float(np.mean([r['noop']-r['damage'] for r in sf])*3.24),
            'ca_mean_saved_ha':float((ca_noops-ca_damages).mean()*3.24),
            'sf_pooled_fraction_all':float(sum(r['noop']-r['damage'] for r in sf)/sum(r['noop'] for r in sf)),
            'ca_pooled_fraction_all':float((ca_noops-ca_damages).sum()/ca_noops.sum())}
    result={'schema_version':'paired-replicate-description/1.0',
        'description':'Secondary descriptive mean of all three predeclared CA spread seeds. Mean fractions within fire, then paired case bootstrap; not a new primary or best-seed selection.',
        'source_analysis_sha256':hashlib.sha256(args.analysis.read_bytes()).hexdigest(),
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'summary':summary}
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    for m,r in summary.items():print(m,r)


if __name__=='__main__':main()
