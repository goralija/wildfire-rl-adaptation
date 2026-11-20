#!/usr/bin/env python3
"""Scientific figure for the four fixed nested TRAIN comparisons."""
import argparse
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    r=json.loads(a.analysis.read_text())
    names=['nested_summary_ridge','nested_summary_rbf','nested_directional_rbf','nested_full_grid_rbf']
    labels=['28 features / ridge','28 features / RBF','76 directional features / RBF','Full 16x16 grid / RBF']
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),sharey=True,layout='constrained')
    for ax,mode,title,gap in zip(axes,['raw','charged'],['Original accounting','Line-footprint charge'],[434.1930612244898,428.8040816326531]):
        entries=[r['results'][mode][n] for n in names]
        values=np.array([e['mean_gain_ha_vs_advancing_front'] for e in entries]);y=np.arange(len(names))
        band=np.array([e['descriptive_paired_bootstrap_95'] for e in entries])
        ax.barh(y,values,color=['#2563eb' if v>0 else '#94a3b8' for v in values],height=.5)
        ax.hlines(y,band[:,0],band[:,1],color='#172554',lw=1.5);ax.scatter(values,y,color='#172554',s=22,zorder=3)
        ax.axvline(0,color='#475569',lw=1)
        threshold=max(r['continuation_threshold']['mean_gain_ha_vs_advancing_front'],r['continuation_threshold']['fraction_of_oracle_gap']*gap)
        ax.axvline(threshold,color='#d97706',ls='--',label='Registered continuation threshold')
        ax.set_yticks(y,labels);ax.set_title(title);ax.set_xlabel('Mean gain vs advancing_front (ha); positive = better')
        ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    axes[0].invert_yaxis();axes[1].legend(loc='lower right',fontsize=8)
    fig.suptitle('98 TRAIN fires | outer LOO + 4 inner folds | fixed menu\nBands describe fixed OOF effects; reused TRAIN, no independent final or physical validation',fontsize=11)
    a.out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(a.out,dpi=160);plt.close(fig)

if __name__=='__main__':main()
