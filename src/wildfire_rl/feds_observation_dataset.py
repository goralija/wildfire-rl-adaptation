"""Guarded non-pickle observation artifacts for the fixed TRAIN repair study."""
import json
from pathlib import Path
import numpy as np
from .feds_simfire_setup import sha256_file

SHAPES={'grid':(4,4,16,16),'weather':(4,4),'time':(4,1),'budget':(4,2),
 'global_grid':(4,20,64,64),'action_patches':(4,8,20,17,17),
 'candidate_line_masks':(4,8,17,17),'candidate_centres':(4,8,2)}


def load_observation_case(root,item,settings):
    root=Path(root);path=root/item['file']
    if path.resolve().parent!=root.resolve() or path.name!=item['scenario_id']+'.json' or sha256_file(path)!=item['sha256']:
        raise ValueError('changed or invalid observation record')
    record=json.loads(path.read_text())
    if record['scenario_id']!=item['scenario_id'] or record['split']!='train' or record['settings']!=settings or record['legacy_and_candidate_and_whole_mask_check']!='PASS':
        raise ValueError('observation identity/split/settings/reference mismatch')
    npz=path.with_suffix('.npz')
    if sha256_file(npz)!=record['npz_sha256']:raise ValueError('changed observation arrays')
    with np.load(npz,allow_pickle=False) as data:
        arrays={name:data[name] for name in SHAPES}
        for name,value in arrays.items():
            if value.shape!=SHAPES[name] or not np.isfinite(value).all():raise ValueError('invalid observation shape/values')
        masks={name:data['mask_'+name] for name in ('legacy','burnable_lines')}
        for name,value in masks.items():
            if value.shape!=(4,9) or not np.isin(value,[0,1]).all() or not value[:,0].all():raise ValueError('invalid action masks')
            masks[name]=value.astype(bool)
        if np.any(masks['burnable_lines'] & ~masks['legacy']):raise ValueError('new mask is not a legal subset')
    return record,[{key:value[k] for key,value in arrays.items()} for k in range(4)],masks
