#!/usr/bin/env python3
"""Matched percentages alongside the no-op growth scale; never mix native PPOs."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path)
    p.add_argument('--replicates',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    r=json.loads(a.report.read_text());s=json.loads(a.replicates.read_text())['summary']
    names=['random_legal','downwind','advancing_front64','matched_rbf']
    labels=['Random line','Downwind','Advancing front','Matched RBF agent']
    y=np.arange(len(names));fig,ax=plt.subplots(1,3,figsize=(17,5.3),layout='constrained')
    for key,offset,color,label in [('sf',-.18,'#4774a0','SimFire'),('ca',.18,'#178273','CA mean of 3 spread seeds')]:
        values=[100*s[n][key+'_mean_fraction'] if s[n][key+'_mean_fraction'] is not None else 0 for n in names]
        bars=ax[0].barh(y+offset,values,height=.34,color=color,label=label)
        ax[0].bar_label(bars,fmt='%.2f',padding=3,fontsize=8)
    ax[0].set_yticks(y,labels);ax[0].invert_yaxis();ax[0].legend(frameon=False)
    for index,name in enumerate(names):
        ax[0].scatter(100*np.array(s[name]['ca_fraction_each_replicate']),[index+.18]*3,
                      color='#063d35',s=15,zorder=5)
    count=s['noop']['joint_cases']
    ax[0].set_xlabel('Mean saved new area (%), same '+str(count)+'/16 cases')
    ax[0].set_title('Equal weight per fire')
    for key,offset,color in [('sf',-.18,'#4774a0'),('ca',.18,'#178273')]:
        bars=ax[1].barh(y+offset,[100*s[n][key+'_pooled_fraction_all'] for n in names],height=.34,color=color)
        ax[1].bar_label(bars,fmt='%.2f',padding=3,fontsize=8)
    ax[1].set_yticks(y,[]);ax[1].invert_yaxis()
    ax[1].set_xlabel('Pooled saved new area (%), all 16 fires')
    ax[1].set_title('Weight proportional to no-op area')
    rows=r['growth_masks'];x=np.array([p['sf_new_cells']*3.24 for p in rows])
    z=np.array([np.mean([p['ca_new_cells']]+[c['results']['noop']['noop'] for c in r['robustness_rows']
                if c['scenario_id']==p['scenario_id']])*3.24 for p in rows])
    ax[2].scatter(x,z,color='#76558b',s=35)
    limit=max(float(x.max()),float(z.max()),3.24)*1.3
    ax[2].plot([0,limit],[0,limit],linestyle='--',color='#92979b',linewidth=1,label='Equal growth')
    ax[2].set_xscale('symlog',linthresh=3.24);ax[2].set_yscale('symlog',linthresh=3.24)
    ax[2].set_xlim(0,limit);ax[2].set_ylim(0,limit)
    ax[2].set_xlabel('SimFire new no-op area (ha)');ax[2].set_ylabel('CA mean new no-op area (ha)')
    ax[2].set_title('No-op growth scale');ax[2].legend(frameon=False)
    for axis in ax:
        axis.spines[['top','right']].set_visible(False);axis.grid(alpha=.15);axis.set_axisbelow(True)
    fig.suptitle('Matched simulator pilot — 16 real TRAIN starts, full 256×256 maps, 48 hours',fontsize=13)
    fig.supxlabel('Secondary descriptive average of all 3 preregistered CA spread seeds; dots are individual seeds.\n'
                  'Common line-control / vegetation semantics. Native PPO policies are not ranked; no physical validation.',fontsize=9)
    a.out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(a.out,dpi=180);plt.close(fig)


if __name__=='__main__':main()
