#!/usr/bin/env python3
"""Audit all saved TRAIN observations against verified inputs, without new simulations."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from analyze_feds_b1 import load_table
from wildfire_rl.feds_simfire_setup import (sha256_file,load_case_inputs,load_weather_records,
    observed_weather_records,record_forcing,SimFireParams)


def audit(table_path,input_root,weather_path):
    import numpy as np
    import rasterio
    from simfire.enums import FuelModelToFuel
    from wildfire_rl.feds_simfire_env import FedsSimFireEnv
    plan=json.loads((ROOT/'configs/frozen/feds-observation-audit-v1.json').read_text())
    if sha256_file(table_path)!=plan['table_sha256'] or sha256_file(weather_path)!=plan['weather_sha256']:
        raise ValueError('changed registered artifacts')
    table,cases=load_table(table_path)
    if len(cases)!=98:raise ValueError('full TRAIN cohort required')
    params=SimFireParams(**table['settings']['params'])
    weather=load_weather_records('train',weather_path=weather_path)
    helper=FedsSimFireEnv.__new__(FedsSimFireEnv);helper.block_count=16
    records=[]
    for case in cases:
        key=case['scenario_id']
        inputs=load_case_inputs(key,weather_path=weather_path,input_root=input_root,weather_records=weather)
        if inputs['receipt_sha256']!=case['input_receipt_sha256']:raise ValueError('changed input receipt')
        fuel=inputs['fuel'];front=inputs['front'];initial=inputs['scar']|front
        receipt=inputs['receipt'];grid=receipt['grid'];folder=input_root/key
        with rasterio.open(folder/receipt['fuel']['file']) as f, rasterio.open(folder/receipt['terrain']['file']) as dem:
            if f.crs!=dem.crs or f.transform!=dem.transform or f.shape!=dem.shape:
                raise ValueError('misaligned fuel/terrain rasters')
            if f.crs.to_string()!=grid['crs'] or not np.allclose(tuple(f.transform)[:6],grid['raster_transform'],rtol=0,atol=1e-5):
                raise ValueError('raster/receipt grid mismatch')
        if not np.isfinite(fuel).all() or not np.isfinite(inputs['elevation']).all():
            raise ValueError('nonfinite raster values')
        burnable=np.array([FuelModelToFuel[int(code)].w_0>0 for code in fuel.ravel()]).reshape(fuel.shape)
        expected=np.stack([helper._pool(initial.astype(np.float32)),helper._pool(front.astype(np.float32)),
            np.zeros((16,16),dtype=np.float32),helper._pool(np.clip(fuel.astype(np.float32)/13.,0.,1.))])
        if not np.array_equal(expected,np.asarray(case['observations'][0]['grid'],dtype=np.float32)):
            raise ValueError('initial grid mismatch: '+key)
        observed=observed_weather_records(weather[key],'previous')
        for k,(obs,record) in enumerate(zip(case['observations'],observed)):
            forcing=record_forcing(record,params);d=np.deg2rad(forcing['wind_direction_degrees_clockwise_north_to'])
            expected_weather=[np.clip(forcing['wind_speed_midflame_ft_per_min_proxy']/3000.,0.,1.),
                np.sin(d),np.cos(d),np.clip(forcing['fuel_moisture_fraction_proxy']/.3,0.,1.)]
            if not np.allclose(np.asarray(obs['weather']),np.asarray(expected_weather,dtype=np.float32),rtol=0,atol=1e-7):
                raise ValueError('weather observation mismatch')
            if record['gridmet_daily_label_mst']>=weather[key]['segments'][k]['gridmet_daily_label_mst']:
                raise ValueError('weather look-ahead')
            if obs['time']!=[k/4] or obs['budget']!=[.25,.25] or not case['action_masks'][k][0]:
                raise ValueError('time/budget/no-op invariant')
        with np.load(table_path.parent/(key+'.npz'),allow_pickle=False) as masks:
            if not np.array_equal(masks['initial'],initial):raise ValueError('initial cumulative damage mismatch')
            lines=masks['line_cells'][1:]
            total_lines=lines.sum(axis=(1,2));nonfuel=(lines & ~burnable).sum(axis=(1,2))
        records.append({'scenario_id':key,'nonfuel_map_fraction':float((~burnable).mean()),
            'initial_front_cells':int(front.sum()),'initial_front_nonfuel_cells':int((front & ~burnable).sum()),
            'planned_line_cells_counted_per_sequence':int(total_lines.sum()),
            'planned_line_nonfuel_cells_counted_per_sequence':int(nonfuel.sum()),
            'nonempty_sequences_entirely_on_nonfuel':int(((total_lines>0)&(total_lines==nonfuel)).sum()),
            'initial_front_occupied_pooled_pixels':int((np.asarray(case['observations'][0]['grid'])[1]>0).sum())})
    return {'schema_version':'feds-observation-input-audit/1.0','created_utc':datetime.now(timezone.utc).isoformat(),
        'label':'TRAIN INPUT/OBSERVATION CONTRACT AUDIT; NOT PHYSICAL VALIDATION','split':'train','case_count':98,
        'validation_used':False,'test_cases_loaded':False,'checks':{'input_hashes_and_initial_grid':'PASS',
        'actual_raster_crs_transform_alignment_and_finite_values':'PASS',
        'all392_observed_weather_records_and_day_lag':'PASS','time_budget_noop':'PASS','initial_cumulative_mask':'PASS'},
        'table_sha256':sha256_file(table_path),'weather_sha256':sha256_file(weather_path),
        'source_sha256':sha256_file(Path(__file__)),'plan_sha256':sha256_file(ROOT/'configs/frozen/feds-observation-audit-v1.json'),
        'summary':{'initial_front_nonfuel_cases':sum(r['initial_front_nonfuel_cells']>0 for r in records),
        'initial_front_nonfuel_cells':sum(r['initial_front_nonfuel_cells'] for r in records),
        'initial_front_cells':sum(r['initial_front_cells'] for r in records),
        'planned_line_cells_counted_per_sequence':sum(r['planned_line_cells_counted_per_sequence'] for r in records),
        'planned_line_nonfuel_cells_counted_per_sequence':sum(r['planned_line_nonfuel_cells_counted_per_sequence'] for r in records),
        'nonempty_sequences_entirely_on_nonfuel':sum(r['nonempty_sequences_entirely_on_nonfuel'] for r in records)},
        'known_contract_limits':['Mean pooling maps a 16x16 native block (2.88km) to one observed pixel; different front positions can give identical observations but different native line anchors.',
            'Fuel coding clip(code/13,0,1) aliases fuel13 and nonfuel91..99 before pooling. The policy cannot recover their distinction from this channel.',
            'Elevation affects Rothermel spread but is absent from the locked observation. Historical FEDS fronts overlapping nonfuel are satellite/raster compatibility uncertainty, not proof of a program defect.',
            'Nonfuel line cells are currently legal and spend budget; this is a known placement convention. No semantics are changed in this audit.'],
        'cases':records}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('table',type=Path)
    p.add_argument('--input-root',type=Path,required=True);p.add_argument('--weather',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('output exists')
    r=audit(a.table,a.input_root,a.weather);a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps(r['summary'],indent=2))

if __name__=='__main__':main()
