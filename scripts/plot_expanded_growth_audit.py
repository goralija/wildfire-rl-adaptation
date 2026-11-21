#!/usr/bin/env python3
"""Frozen61-case diagnostic, predeclared growth groups and all case maps."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('analysis',type=Path);p.add_argument('--groups',type=Path,required=True)
    p.add_argument('--data-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();r=json.loads(args.analysis.read_text());g=json.loads(args.groups.read_text())
    s=r['summary']['raw']['48'];methods=['simfire','ca0','ca1','ca2','ca_mean3','ellipse','persistence']
    labels=['SimFire','CA seed0 (primary)','CA seed1','CA seed2','CA mean3 (secondary)','Ellipse','Persistence']
    colors=['#366eac','#bf731e','#dab886','#e9cfac','#c05d29','#719353','#91969a']
    fig,ax=plt.subplots(2,2,figsize=(15,10),layout='constrained')
    for axis,key,title in [(ax[0,0],'mean_growth_iou','48h new-area spatial overlap'),
                           (ax[0,1],'mean_absolute_new_area_error_ha','48h absolute new-area error')]:
        values=[s['methods'][m][key] for m in methods]
        bars=axis.barh(np.arange(len(methods)),[v if v is not None else 0 for v in values],color=colors)
        axis.bar_label(bars,labels=['undefined' if v is None else format(v,'.3f' if key=='mean_growth_iou' else ',.0f') for v in values],padding=3,fontsize=8)
        axis.set_yticks(np.arange(len(methods)),labels);axis.invert_yaxis();axis.set_title(title)
        axis.set_xlabel(('IoU, higher is better; n='+str(len(s['observed_positive_ids']))) if key=='mean_growth_iou'
                        else 'ha, lower is better; n='+str(len(s['complete_ids'])))
        axis.margins(x=.2)
    group_names=['zero_growth','near_stalled','growing'];y=np.arange(3)
    glabels=['Zero growth','Growth <10% of initial','Growth >=10% of initial']
    glabels=[label+' (n='+str(len(g['growth_groups'][name]['complete_ids']))+')' for label,name in zip(glabels,group_names)]
    for axis,key,title in [(ax[1,0],'mean_absolute_new_area_error_ha','Predeclared groups: area error'),
                           (ax[1,1],'mean_growth_iou','Predeclared groups: spatial overlap')]:
        for method,offset,color,label in [('simfire',-.24,colors[0],'SimFire'),('ca0',0,colors[1],'CA seed0'),
                                          ('ca_mean3',.24,colors[4],'CA mean3 (secondary)')]:
            values=[g['growth_groups'][name]['methods'][method][key] for name in group_names]
            bars=axis.barh(y+offset,[v if v is not None else 0 for v in values],height=.22,color=color,label=label)
            axis.bar_label(bars,labels=['undefined' if v is None else format(v,'.3f' if key=='mean_growth_iou' else ',.0f') for v in values],padding=3,fontsize=8)
        axis.set_yticks(y,glabels);axis.invert_yaxis();axis.set_title(title)
        axis.set_xlabel('IoU on observed-positive cases' if key=='mean_growth_iou' else 'Mean absolute new-area error (ha)')
        axis.margins(x=.22)
    ax[1,0].legend(frameon=False,loc='lower right')
    for axis in ax.flat:
        axis.spines[['top','right']].set_visible(False);axis.grid(alpha=.15);axis.set_axisbelow(True)
    fig.suptitle('Frozen SimFire / CA bridge against FEDS — all61 compatible TRAIN starts',fontsize=14)
    fig.supxlabel('Equal fire weights; raw48h in-map targets; CA mean3 averages scalar metrics within fire.\n'
                  'No tuning, independent holdout, native PPO ranking or physical validation.',fontsize=9)
    args.out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(args.out.with_suffix('.png'),dpi=170);plt.close(fig)

    for page,start in enumerate(range(0,len(r['rows']),16),1):
        rows=r['rows'][start:start+16];fig,axes=plt.subplots(4,4,figsize=(15,16.2),layout='constrained')
        for axis in list(axes.flat)[len(rows):]:axis.set_visible(False)
        for axis,row in zip(axes.flat,rows):
            sid=row['scenario_id'];name=sid.split('-',3)[-1].replace('-',' ').title()
            if not row['complete']:
                axis.text(.5,.5,'Missing/invalid observations',ha='center',va='center');axis.set_title(name);continue
            with np.load(args.data_root/'simfire'/(sid+'.npz'),allow_pickle=False) as z:
                initial=z['initial'];sf=z['simfire'][-1]&~initial
            with np.load(args.data_root/'ca'/(sid+'.npz'),allow_pickle=False) as z:ca=z['ca0'][-1]&~initial
            with np.load(args.data_root/'observations'/(sid+'.npz'),allow_pickle=False) as z:target=z['4']&~initial
            rgba=np.ones((*initial.shape,4));rgba[initial]=[.77,.77,.77,1];rgba[target]=[.32,.56,.37,1]
            axis.imshow(rgba,extent=(-23.04,23.04,-23.04,23.04))
            for mask,color in [(sf,colors[0]),(ca,colors[1])]:
                if mask.any():axis.contour(mask.astype(float),levels=[.5],colors=[color],linewidths=.65,
                                           origin='upper',extent=(-23.04,23.04,-23.04,23.04))
            if not row['fully_covered']:name+=' (FEDS clipped)'
            axis.set_title(name+'\nNew area (ha): FEDS / SF / CA0\n'+
                           ' / '.join(format(int(v.sum())*3.24,',.0f') for v in (target,sf,ca)),fontsize=9)
            axis.set_xticks([-20,0,20]);axis.set_yticks([-20,0,20]);axis.tick_params(labelsize=7);axis.set_aspect('equal')
        handles=[Line2D([0],[0],color=c,lw=3,label=label) for c,label in
                 [('#c4c4c4','Initial damage (excluded)'),('#528f5e','Observed new growth'),
                  (colors[0],'SimFire new growth outline'),(colors[1],'CA seed0 new growth outline')]]
        fig.legend(handles=handles,loc='outside lower center',ncol=2,frameon=False)
        fig.suptitle(('All61 preregistered TRAIN starts, page%d/4, cases%d–%d — same46.08km square\n'%(page,start+1,start+len(rows)))+
                     'Axes: km from map centre. Raw FEDS; unknown suppression. CA common-control bridge.',fontsize=12)
        fig.savefig(args.out.with_name(args.out.stem+'-maps-'+str(page)).with_suffix('.png'),dpi=140);plt.close(fig)


if __name__=='__main__':main()
