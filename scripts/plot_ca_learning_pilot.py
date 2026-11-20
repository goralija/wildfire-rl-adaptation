#!/usr/bin/env python3
"""Plot every registered seed and the descriptive paired learning contrasts."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    p=json.loads(args.report.read_text());s=p['summary']
    fig,axes=plt.subplots(1,2,figsize=(11,5.2),layout='constrained')
    values=[s['reference_saved']]+[s['phases'][x]['mean_saved_fraction'] for x in ('bc','ppo')]
    bars=axes[0].bar(range(3),100*np.array(values),color=['#8b969f','#487aab','#188276'])
    axes[0].bar_label(bars,fmt='%.2f%%',padding=5)
    for index,phase in enumerate(('bc','ppo'),start=1):
        points=[100*r['mean_saved_fraction'] for r in s['phases'][phase]['per_seed'].values()]
        axes[0].scatter(index+np.linspace(-.08,.08,len(points)),points,c='black',s=22,zorder=5)
    axes[0].set_xticks(range(3),['Teacher','BC final','BC + PPO final'])
    axes[0].set_ylabel('Mean saved weighted damage (%)')
    axes[0].set_title('All three training seeds shown as points')
    axes[0].margins(y=.2)
    for index,phase in enumerate(('bc','ppo')):
        r=s['phases'][phase]['vs_reference']
        mean=100*r['mean'];lo,hi=100*np.array(r['ci95'])
        axes[1].errorbar(mean,index,xerr=[[mean-lo],[hi-mean]],fmt='o',capsize=5,
                         color=['#487aab','#188276'][index])
    axes[1].axvline(0,color='#6e7378',linestyle='--',linewidth=1)
    axes[1].set_yticks([0,1],['BC final','BC + PPO final'])
    axes[1].set_ylim(-.5,1.5)
    axes[1].invert_yaxis()
    axes[1].set_xlabel('Saved damage difference vs teacher (percentage points)')
    axes[1].set_title('Descriptive case-cluster 95% intervals')
    for ax in axes:
        ax.spines[['top','right']].set_visible(False)
        ax.grid(axis='y' if ax is axes[0] else 'x',alpha=.15)
        ax.set_axisbelow(True)
    safety=[]
    for seed in p['plan']['model_seeds']:
        bc=s['phases']['bc']['per_seed'][str(seed)]
        ppo=s['phases']['ppo']['per_seed'][str(seed)]
        safety.append('%d: BC %d/%d; PPO %d/%d'%(seed,bc['close_calls'],bc['units_lost'],
                                               ppo['close_calls'],ppo['units_lost']))
    fig.suptitle('CA v2 short learning pilot — 16 development fires, 3 resource rosters',fontsize=13)
    fig.supxlabel('Safety: close calls / unit losses per 48 episodes. Teacher %d/%d\n%s\n'
                  'Reused development, simulator-only; no test or physical-validation claim.'%
                  (s['reference_close_calls'],s['reference_units_lost'],'  |  '.join(safety)),fontsize=9)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(args.out,dpi=180);plt.close(fig)


if __name__=='__main__':
    main()
