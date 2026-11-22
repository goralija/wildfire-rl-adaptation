#!/usr/bin/env python3
"""Publication-style static view of all frozen stages, references and action bias."""
import argparse
import json
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'.local/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def plot(report,audit,out):
    fig,axs=plt.subplots(2,2,figsize=(13.5,8.5),constrained_layout=True)
    colors={'simfire':'#b34d22','ca':'#247787'};labels={'simfire':'SimFire','ca':'CA (spread 0)'}
    fig.suptitle('Paired PPO development pilot: no established learning advantage',fontsize=16,weight='bold')
    ax=axs[0,0];steps=[0,512,2048]
    for be in colors:
        b=report['summary']['backends'][be]
        for seed in report['plan']['model_seeds']:
            ax.plot(steps,[b['checkpoints'][str(s)]['model_seeds'][str(seed)]['mean_saved_percent_joint'] for s in steps],
                    color=colors[be],alpha=.3,lw=1)
        ax.plot(steps,[b['checkpoints'][str(s)]['mean_saved_percent_joint'] for s in steps],
                color=colors[be],marker='o',lw=2.5,label=labels[be])
    ax.set(title='A  All checkpoints; thick line = mean of 3 model seeds',xlabel='Training steps',ylabel='Charged area saved (%)')
    ax.set_xticks(steps);ax.legend(frameon=False);ax.grid(alpha=.2)
    ax=axs[0,1];methods=['random_legal','downwind','advancing_front64','PPO']
    for i,be in enumerate(colors):
        b=report['summary']['backends'][be]
        values=[b['heuristics'][m]['mean_saved_percent_joint'] if m!='PPO' else b['checkpoints']['2048']['mean_saved_percent_joint'] for m in methods]
        bars=ax.bar(np.arange(4)+(i-.5)*.36,values,width=.34,color=colors[be],label=labels[be])
        ax.bar_label(bars,fmt='%.2f',padding=3,fontsize=9)
    ax.set_xticks(range(4),['Random (seed 0)','Downwind','Fixed front','Final PPO'])
    ax.set(title='B  Same 14 positive-no-op fires, same denominators',ylabel='Mean charged area saved (%)',ylim=(0,13))
    ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    ax=axs[1,0]
    for i,be in enumerate(colors):
        b=report['summary']['backends'][be]
        for j,(key,label) in enumerate([('final_minus_initial_pp','Final − untrained'),('final_minus_front_pp','Final − fixed front')]):
            d=b[key];y=j+(i-.5)*.2
            ax.errorbar(d['mean'],y,xerr=[[d['mean']-d['ci95'][0]],[d['ci95'][1]-d['mean']]],
                        fmt='o',capsize=4,color=colors[be],label=labels[be] if j==0 else None)
    ax.axvline(0,color='#555',lw=1);ax.set_yticks([0,1],['Final − untrained','Final − fixed front'])
    ax.set(title='C  Paired fire means and descriptive 95% intervals',xlabel='Difference (percentage points)')
    ax.grid(axis='x',alpha=.2)
    ax=axs[1,1];rows=[r for r in audit['action_diagnostics'] if r['checkpoint']==2048]
    rows=sorted(rows,key=lambda r:(r['backend']=='ca',r['seed']))
    palette=plt.get_cmap('tab10');bottom=np.zeros(6)
    names=['No-op','E','SE','S','SW','W','NW','N','NE']
    for action in range(9):
        counts=np.array([r['action_counts'].get(str(action),0) for r in rows])
        if counts.any():
            ax.barh(np.arange(6),counts,left=bottom,color=palette(action),label=names[action]);bottom+=counts
    ax.set_yticks(range(6),[('SF' if r['backend']=='simfire' else 'CA')+' / '+str(r['seed']) for r in rows])
    ax.set_ylim(6.4,-.7);ax.set_xticks([0,4,8,12,16]);ax.set_xlim(0,16)
    ax.set(title='D  Greedy first action often constant; probabilities nearly uniform',xlabel='Number of development fires (16 per model)')
    ax.legend(ncol=4,frameon=False,loc='lower right',fontsize=9)
    fig.supxlabel('TRAIN development only: 45 fitting / 16 previously explored evaluation fires; common B=1, 48h.\n'
                  'Panels A–C use the same 14 joint-positive fires. Thin lines are model seeds, not extra fires.\n'
                  'Greedy sector repeats do not imply a low-entropy distribution or the same physical line coordinates.',fontsize=10)
    out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=180);plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    plot(json.loads(a.analysis.read_text()),json.loads(a.audit.read_text()),a.out)
