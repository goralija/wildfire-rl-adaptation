"""Fixed inference-only feasibility matrix; writes a new /outputs/final directory."""
import contextlib,json,sys
from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('probe','/opt/firehose_probe.py');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
cases=[('none-123-a','none',123,0,False),('none-123-b','none',123,0,False),('none-124','none',124,0,False),('none-125','none',125,0,False),('min-123','min_l2',123,8,False),('max-123','max_l2',123,8,False),('fixed-123-a','ppo-fixed',123,8,False),('fixed-123-b','ppo-fixed',123,8,False),('fixed-124','ppo-fixed',124,8,False),('random-123','ppo-random',123,8,False),('fixed-123-sync','ppo-fixed',123,8,True),('none-123-sync','none',123,0,True)]
root=Path('/outputs/final');root.mkdir(exist_ok=False)
summary=[]
for label,policy,seed,budget,sync in cases:
 sys.argv=['probe','--policy',policy,'--seed',str(seed),'--budget',str(budget),'--out',str(root/label)]+(['--sync-reset'] if sync else [])
 with (root/(label+'.log')).open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
  code=probe.main()
 result=json.loads((root/label/'result.json').read_text());summary.append({'label':label,**{k:result.get(k) for k in ('success','policy','simulator_seed','budget','sync_reset','decisions','interventions_requested','nonfuel_requests','observed_ever_affected_cells','active_front_cell_ids_one_based','termination_reason','terminal_state_matches_grid_history','python_cumulative_affected_cells','python_cumulative_matches_simulator','weights_unchanged','subprocess_returncode','runtime_seconds')}})
 print(label,code,summary[-1],flush=True)
(root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
raise SystemExit(0 if all(r['success'] for r in summary) else 1)
