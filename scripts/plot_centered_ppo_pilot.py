#!/usr/bin/env python3
"""Export the frozen TRAIN pilot; effect intervals are paired by fire."""
import argparse
import json
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path('.local/matplotlib').resolve()))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def plot(report,out):
    data=json.loads(report.read_text());summary=data['summary'];fig,axes=plt.subplots(1,2,figsize=(13,5.7))
    colors=['#426b96','#c66b35','#78956c','#72638c','#767676']
    methods=['original512','centered512','exact_uniform','advancing_front64','fitting_selected_fixed']
    labels=['Original PPO (512)','Centered PPO (512)','Exact uniform line','Fixed front','Fit-selected sector']
    x=np.arange(2);width=.15
    for k,(method,label,color) in enumerate(zip(methods,labels,colors)):
        y=[summary['backends'][be]['metrics'][method]['mean_saved_percent_joint'] for be in ('simfire','ca')]
        bars=axes[0].bar(x+(k-2)*width,y,width,color=color,label=label)
        axes[0].bar_label(bars,fmt='%.2f',fontsize=8,padding=3)
    axes[0].set_xticks(x,['SimFire','CA']);axes[0].set_ylim(0,16)
    axes[0].set_ylabel('Mean charged damage saved (%)');axes[0].set_title('Same 14 fires, same 512 step training budget')
    axes[0].legend(frameon=False,fontsize=9,loc='upper center',ncol=2)
    axes[0].grid(axis='y',alpha=.15);axes[0].set_axisbelow(True)
    for k,(be,label) in enumerate([('simfire','SimFire'),('ca','CA')]):
        for offset,reference,color in [(.15,'original512',colors[0]),(-.15,'exact_uniform',colors[2])]:
            v=summary['backends'][be]['centered_minus_reference_pp'][reference];lo,hi=v['ci95'];m=v['mean']
            axes[1].errorbar(m,1-k+offset,xerr=[[m-lo],[hi-m]],fmt='o',capsize=4,color=color,
                label=('Centered − original512' if reference=='original512' else 'Centered − exact uniform') if k==0 else None)
            axes[1].text(hi+.3,1-k+offset,'%.2f [%+.2f, %+.2f]'%(m,lo,hi),va='center',fontsize=8)
    axes[1].axvline(0,color='#999999',linewidth=1,linestyle='--');axes[1].set_yticks([1,0],['SimFire','CA'])
    axes[1].set_xlim(-10,16);axes[1].set_ylim(-.6,1.6);axes[1].set_xlabel('Change in saved damage (percentage points)')
    axes[1].set_title('Descriptive 95% paired fire bootstrap');axes[1].legend(frameon=False,fontsize=9,loc='upper left')
    for ax in axes:
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Reward centering: CA mean improves, SimFire mean falls; neither passes continuation rule',fontsize=12,y=.98)
    fig.text(.03,.045,'TRAIN development only • 3 model seeds averaged within each fire • 14 joint-positive fires • 10,000 bootstrap draws\nNo checkpoint/seed selection; zero-no-op cases retained separately; no physical validation.',fontsize=9,color='#444444')
    fig.tight_layout(rect=[0,.12,1,.92]);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=170);plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();plot(a.report,a.out)
