#!/usr/bin/env python3
"""Static diagnostic figures; one-step probes are not new policy performance."""
import argparse
import json
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'.local/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def plot(r,parent,out):
    fig,axs=plt.subplots(2,2,figsize=(13.5,8.7),constrained_layout=True)
    colors={'simfire':'#b34d22','ca':'#247787'}
    fig.suptitle('PPO signal diagnosis: case scale and actor–critic clipping coupling',weight='bold',fontsize=16)
    ax=axs[0,0]
    for i,be in enumerate(colors):
        b=r['references']['backends'][be]['evaluation'];old=parent['summary']['backends'][be]
        values=[old['checkpoints']['2048']['mean_saved_percent_joint'],b['uniform_initial_line']['mean_saved_percent_joint'],
                b['selected_fixed_reference']['mean_saved_percent_joint'],old['heuristics']['advancing_front64']['mean_saved_percent_joint']]
        bars=ax.bar(np.arange(4)+(i-.5)*.36,values,width=.34,color=colors[be],label='SimFire' if be=='simfire' else 'CA spread 0')
        ax.bar_label(bars,fmt='%.2f',padding=3,fontsize=9)
    ax.set_xticks(range(4),['Old final PPO','Exact uniform','Fit-selected sector','Fixed front'])
    ax.set(title='A  Same 14 development fires, first-decision references',ylabel='Mean charged area saved (%)',ylim=(0,13));ax.legend(frameon=False)
    ax=axs[0,1]
    for i,be in enumerate(colors):
        b=r['references']['backends'][be]['fitting']
        values=[b[k]['between_fraction']*100 for k in ('cost_scale','centered_cost_scale')]
        bars=ax.bar(np.arange(2)+(i-.5)*.36,values,width=.34,color=colors[be])
        ax.bar_label(bars,fmt='%.2f',padding=3,fontsize=9)
    ax.set_xticks(range(2),['Original cost','Subtract own no-op cost'])
    ax.set(title='B  Between-fire share of initial-action cost variance (45 fit)',ylabel='Between-fire fraction (%)',ylim=(0,112))
    ax=axs[1,0];rows=sorted(r['probes'],key=lambda p:(p['backend']=='ca',p['seed']))
    for j,(reward,clipping,label,color) in enumerate([
        ('centered','global','Centered / global','#397c58'),
        ('original','separate','Original / separate','#9a6bc3'),
        ('centered','separate','Centered / separate','#d0a02d')]):
        ratios=[]
        for p in rows:
            d={(m['reward'],m['clipping']):m for m in p['modes']}
            ratios.append(d[reward,clipping]['actor']['parameter_step_l2']/d['original','global']['actor']['parameter_step_l2'])
        ax.barh(np.arange(6)+(j-1)*.22,ratios,height=.2,label=label,color=color)
    ax.axvline(1,color='#333',ls='--',lw=1)
    ax.set_yticks(range(6),[('SF' if p['backend']=='simfire' else 'CA')+' / '+str(p['seed']) for p in rows]);ax.invert_yaxis()
    ax.set(title='C  Disposable first Adam step: actor parameter change',xlabel='Step norm / original-reward global-clip step norm')
    ax.legend(frameon=False,fontsize=8,loc='lower right')
    ax=axs[1,1];rows=sorted([x for x in r['policy_diagnostics'] if x['checkpoint']==2048],key=lambda p:(p['backend']=='ca',p['seed']))
    for i,g in enumerate(('actor','critic')):
        ax.bar(np.arange(6)+(i-.5)*.34,[p['parameter_delta'][g]['relative_l2']*100 for p in rows],width=.32,label=g,color=('#555','#9ab0ba')[i])
    ax.set_xticks(range(6),[('SF' if p['backend']=='simfire' else 'CA')+'\n'+str(p['seed']) for p in rows])
    ax.set(title='D  Existing final checkpoints: relative parameter movement',ylabel='L2 change / initial L2 norm (%)');ax.legend(frameon=False)
    for ax in axs.flat:ax.grid(axis='y' if ax!=axs[1,0] else 'x',alpha=.15);ax.set_axisbelow(True)
    fig.supxlabel('TRAIN diagnosis only. Fixed sectors selected on fitting45; evaluation16 never selects them.\n'
                  'Centering preserves final action-cost order at the fixed four-step horizon.\n'
                  'First-step probes reproduce the same initial batches; no changed-policy fire performance was measured.',fontsize=10)
    out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=180);plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',type=Path,required=True)
    p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    plot(json.loads(a.analysis.read_text()),json.loads(a.parent.read_text()),a.out)
