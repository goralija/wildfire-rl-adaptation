#!/usr/bin/env python3
"""Plot registered heuristic and model contrasts; TRAIN exploration only."""
import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);p.add_argument('--heuristics',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    r=json.loads(a.analysis.read_text());h=json.loads(a.heuristics.read_text())
    fig,axes=plt.subplots(1,2,figsize=(13,5),layout='constrained',gridspec_kw={'width_ratios':[1,1.5]})
    policies=[('legacy','advancing_front'),('legacy','advancing_front64'),('burnable_lines','advancing_front64')]
    labels=['Original coarse rule','Fine-front rule','Fine-front + nonfuel gate']
    ax=axes[0]
    for y,(mask,name) in enumerate(policies):
        row=h['results']['charged'][mask][name];gain=row['gain_vs_original_advancing_front_ha'];lo,hi=row['descriptive_paired_bootstrap_95']
        ax.barh(y,gain,color='#2563eb',height=.45);ax.hlines(y,lo,hi,color='#172554');ax.scatter(gain,y,color='#172554',s=22,zorder=3)
    ax.set_yticks(range(3),labels);ax.invert_yaxis();ax.axvline(0,color='#475569',lw=1)
    ax.set_title('Fixed rules: gain over original coarse rule');ax.set_xlabel('Mean gain (ha), line-footprint charge')
    names=['legacy28','categorical154','local458','terrain536'];y=np.arange(4);ax=axes[1]
    for mask,offset,color in [('legacy',-.15,'#94a3b8'),('burnable_lines',.15,'#2563eb')]:
        rows=[r['results']['charged'][mask][n] for n in names]
        gains=[row['mean_gain_ha_vs_reference'] for row in rows];bands=np.array([row['descriptive_paired_bootstrap_95'] for row in rows])
        ax.barh(y+offset,gains,height=.25,color=color,label=mask)
        ax.hlines(y+offset,bands[:,0],bands[:,1],color='#172554',lw=1);ax.scatter(gains,y+offset,s=16,color='#172554',zorder=3)
    ax.set_yticks(y,['Legacy 28','Categories 154','Local geometry 458','Terrain 536 (primary with gate)']);ax.invert_yaxis();ax.axvline(0,color='#475569',lw=1)
    ax.set_title('Nested models: gain over matched fit-selected rule');ax.set_xlabel('Mean gain (ha), line-footprint charge');ax.legend(fontsize=8,loc='lower right')
    for ax in axes:ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    fig.suptitle('Observation v2 | 98 reused TRAIN fires | fixed plan\nBands: descriptive paired bootstrap; no independent final or physical validation',fontsize=11)
    a.out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(a.out,dpi=160);plt.close(fig)

if __name__=='__main__':main()
