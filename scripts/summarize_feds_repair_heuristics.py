#!/usr/bin/env python3
"""Secondary paired audit of the registered fixed v2 rules; no new policy tuning."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from analyze_feds_b1 import load_table
from wildfire_rl.feds_simfire_setup import sha256_file


def main():
    import numpy as np
    from wildfire_rl.feds_observation_dataset import load_observation_case
    from wildfire_rl.feds_repaired_policies import make_repaired_heuristic
    from wildfire_rl.feds_b1 import policy_sequence
    from wildfire_rl.feds_b1_learning import paired_interval
    p=argparse.ArgumentParser();p.add_argument('dataset',type=Path);p.add_argument('--table',type=Path,required=True);p.add_argument('--analysis',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('new output required')
    d=json.loads(a.dataset.read_text());analysis=json.loads(a.analysis.read_text());_,cases=load_table(a.table)
    if len(cases)!=98 or d['split']!='train' or d['validation_used'] is not False or d['test_cases_loaded'] is not False or sha256_file(a.dataset)!=analysis['dataset_sha256']:
        p.error('changed/invalid artifacts')
    by_id={r['scenario_id']:r for r in d['cases']};names=['noop','downwind','advancing_front','advancing_front64'];rows={mode:{mask:{name:[] for name in names} for mask in ('legacy','burnable_lines')} for mode in ('raw','charged')}
    for c in cases:
        _,obs,masks=load_observation_case(a.dataset.parent,by_id[c['scenario_id']],d['settings'])
        for mask in masks:
            for name in names:
                actions=policy_sequence(make_repaired_heuristic(name),obs,masks[mask])
                match=[r for r in c['outcomes'] if tuple(r['effective_actions'])==actions]
                for mode in rows:
                    values={r[mode+'_saved_cells'] for r in match}
                    if len(values)!=1:raise ValueError('inconsistent sequence score')
                    rows[mode][mask][name].append({'scenario_id':c['scenario_id'],'actions':list(actions),'saved_ha':float(next(iter(values)))*3.24})
    summary={};comparisons={}
    for mode,blocks in rows.items():
        summary[mode]={};comparisons[mode]={}
        original=np.array([r['saved_ha'] for r in blocks['legacy']['advancing_front']])
        for mask,policies in blocks.items():
            summary[mode][mask]={}
            matched=np.array([r['saved_ha'] for r in policies['advancing_front']])
            for name,values in policies.items():
                saved=np.array([r['saved_ha'] for r in values]);mean=float(saved.mean())
                if abs(mean-analysis['heuristic_mean_saved_ha'][mode][mask][name])>1e-7:raise ValueError('policy implementation differs from registered analysis')
                delta=saved-original;changed=sum(r['actions']!=old['actions'] for r,old in zip(values,blocks['legacy'][name]))
                summary[mode][mask][name]={'mean_saved_ha':mean,'gain_vs_original_advancing_front_ha':float(delta.mean()),
                    'gain_vs_matched_advancing_front_ha':float((saved-matched).mean()),'descriptive_paired_bootstrap_95':paired_interval(delta),
                    'without_largest_absolute_delta_ha':float(np.delete(delta,int(np.argmax(np.abs(delta)))).mean()),
                    'better_fires':int((delta>1e-8).sum()),'worse_fires':int((delta< -1e-8).sum()),'mask_changed_action_cases':changed,'per_fire':values}
        fine_legacy=np.array([r['saved_ha'] for r in blocks['legacy']['advancing_front64']]);fine_new=np.array([r['saved_ha'] for r in blocks['burnable_lines']['advancing_front64']])
        comparisons[mode]={'fine_geometry_only_gain_ha':float((fine_legacy-original).mean()),'nonfuel_gate_on_fine_gain_ha':float((fine_new-fine_legacy).mean()),
            'nonfuel_gate_better_cases':int((fine_new>fine_legacy+1e-8).sum()),'nonfuel_gate_worse_cases':int((fine_new<fine_legacy-1e-8).sum())}
    report={'schema_version':'feds-repair-heuristic-audit/2.0','label':'SECONDARY REUSED TRAIN DESCRIPTION; NO NEW POLICY SELECTION OR PHYSICAL VALIDATION',
        'split':'train','case_count':98,'validation_used':False,'test_cases_loaded':False,'dataset_sha256':sha256_file(a.dataset),
        'analysis_sha256':sha256_file(a.analysis),'source_sha256':sha256_file(Path(__file__)),'all_registered_means_match':'PASS',
        'results':summary,'paired_components':comparisons,'uncertainty':'Descriptive paired bootstrap of fixed fire effects,10000 seed0, no refit or independent confirmation.'}
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')

if __name__=='__main__':main()
