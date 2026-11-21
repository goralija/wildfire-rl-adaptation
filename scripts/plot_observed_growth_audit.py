#!/usr/bin/env python3
"""Scientific overview and all16 matched maps of the frozen TRAIN growth audit."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('analysis',type=Path)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    r = json.loads(args.analysis.read_text()); s = r['summary']['raw']['48']
    rows = [x for x in r['rows'] if x['complete']]
    fig,ax = plt.subplots(2,2,figsize=(14,10),layout='constrained')
    names = ['simfire','ca0','ca1','ca2','ca_mean3','ellipse','persistence']
    labels = ['SimFire','CA seed0 (primary)','CA seed1','CA seed2','CA mean3 (secondary)','Ellipse','Persistence']
    colors = ['#366eac','#bf731e','#dab886','#e9cfac','#c05d29','#719353','#91969a']
    y = np.arange(len(names))
    for axis,key,title in [(ax[0,0],'mean_growth_iou','48h new-area spatial overlap'),
                           (ax[0,1],'mean_absolute_new_area_error_ha','48h absolute new-area error')]:
        vals = [s['methods'][m][key] for m in names]
        bars = axis.barh(y,[v if v is not None else 0 for v in vals],color=colors)
        axis.bar_label(bars,labels=['undefined' if v is None else format(v,'.3f' if key=='mean_growth_iou' else ',.0f') for v in vals],padding=3,fontsize=8)
        axis.set_yticks(y,labels);axis.invert_yaxis();axis.set_title(title)
        axis.set_xlabel(('IoU, higher is better; '+str(len(s['observed_positive_ids']))+' observed-growing fires')
                        if key=='mean_growth_iou' else 'ha, lower is better; all complete fires')
        axis.margins(x=.2)
    observed = [x['metrics']['raw']['48']['simfire']['observed_new_area_ha'] for x in rows]
    for method,color,label in [('simfire',colors[0],'SimFire'),('ca0',colors[1],'CA primary seed0')]:
        pred = [x['metrics']['raw']['48'][method]['predicted_new_area_ha'] for x in rows]
        ax[1,0].scatter(observed,pred,color=color,s=30,label=label,alpha=.8)
    limit = max([3.24]+observed+[x['metrics']['raw']['48']['simfire']['predicted_new_area_ha'] for x in rows])*1.5
    ax[1,0].plot([0,limit],[0,limit],color='#aaa',ls='--',lw=1)
    ax[1,0].set_xscale('symlog',linthresh=3.24);ax[1,0].set_yscale('symlog',linthresh=3.24)
    ax[1,0].set_xlim(0,limit);ax[1,0].set_ylim(0,limit)
    ax[1,0].set_xlabel('Observed new FEDS area (ha)');ax[1,0].set_ylabel('Predicted new area (ha)')
    ax[1,0].set_title('48h growth scale, one point per fire');ax[1,0].legend(frameon=False)
    hours = [12,24,36,48]
    for method,color,label,style in [('simfire',colors[0],'SimFire','-'),('ca0',colors[1],'CA seed0','--'),
                                    ('ca_mean3',colors[4],'CA mean3 (secondary)','-'),('ellipse',colors[5],'Ellipse',':')]:
        vals = [r['summary']['raw'][str(h)]['methods'][method]['mean_growth_iou'] for h in hours]
        ax[1,1].plot(hours,vals,style,color=color,marker='o',label=label)
    ax[1,1].set_xticks(hours,['%dh\nn=%d'%(h,len(r['summary']['raw'][str(h)]['observed_positive_ids'])) for h in hours])
    ax[1,1].set_xlabel('Hours since shared initial state; observed-growing fire count')
    ax[1,1].set_ylabel('Mean new-area IoU');ax[1,1].set_title('Same observed-growing subset within each horizon')
    ax[1,1].set_ylim(0,.26);ax[1,1].legend(frameon=False,loc='upper right')
    for axis in ax.flat:
        axis.spines[['top','right']].set_visible(False);axis.grid(alpha=.15);axis.set_axisbelow(True)
    fig.suptitle('Frozen SimFire / CA bridge against exact-time FEDS — TRAIN diagnostic',fontsize=14)
    fig.supxlabel('Each fire has equal weight; CA mean3 averages scalar metrics inside fire. '
                  'No tuning, native PPO ranking or physical validation.',fontsize=9)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(args.out.with_suffix('.png'),dpi=170);plt.close(fig)

    fig,axes = plt.subplots(4,4,figsize=(15,15),layout='constrained')
    for axis,row in zip(axes.flat,r['rows']):
        sid = row['scenario_id']
        if not row['complete']:
            axis.text(.5,.5,'Missing/invalid observations',ha='center',va='center');continue
        with np.load(args.data_root/'simfire'/(sid+'.npz'),allow_pickle=False) as z:
            initial = z['initial']; sf = z['simfire'][-1]&~initial
        with np.load(args.data_root/'ca'/(sid+'.npz'),allow_pickle=False) as z: ca = z['ca0'][-1]&~initial
        with np.load(args.data_root/'observations'/(sid+'.npz'),allow_pickle=False) as z: target = z['4']&~initial
        rgba = np.ones((*initial.shape,4));rgba[initial] = [.77,.77,.77,1]
        rgba[target] = [.32,.56,.37,1]
        axis.imshow(rgba,extent=(-23.04,23.04,-23.04,23.04))
        for mask,color in [(sf,colors[0]),(ca,colors[1])]:
            if mask.any(): axis.contour(mask.astype(float),levels=[.5],colors=[color],linewidths=.65,
                                        origin='upper',extent=(-23.04,23.04,-23.04,23.04))
        name = sid.split('-',3)[-1].replace('-',' ').title()
        if not row['fully_covered']: name += ' (FEDS clipped)'
        axis.set_title(name+'\nObserved/SF/CA0 new ha: '+
                       '/'.join(format(int(v.sum())*3.24,',.0f') for v in (target,sf,ca)),fontsize=9)
        axis.set_xticks([-20,0,20]);axis.set_yticks([-20,0,20]);axis.tick_params(labelsize=7)
        axis.set_aspect('equal')
    handles = [Line2D([0],[0],color=c,lw=3,label=label) for c,label in
               [('#c4c4c4','Initial damage (excluded)'),('#528f5e','Observed new growth'),
                (colors[0],'SimFire new growth outline'),(colors[1],'CA seed0 new growth outline')]]
    fig.legend(handles=handles,loc='outside lower center',ncol=2,frameon=False)
    fig.suptitle('All16 preregistered TRAIN starts, 48h — same46.08km square in every panel\n'
                 'Axes: km from map centre. Raw FEDS; unknown suppression. CA common-control bridge.',fontsize=12)
    fig.savefig(args.out.with_name(args.out.stem+'-maps').with_suffix('.png'),dpi=150);plt.close(fig)


if __name__=='__main__':main()
