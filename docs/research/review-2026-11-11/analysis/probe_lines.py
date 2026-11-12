import json, sys, time, numpy as np, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "src")
from wildfire_rl.feds_simfire_env import FedsSimFireEnv, SIMFIRE_FIRELINE
from wildfire_rl.feds_simfire_setup import SimFireParams, load_split_cases
from wildfire_rl.feds_heuristics import make_heuristic
p = SimFireParams(**json.load(open("configs/frozen/feds-simfire-growth-gate-freeze-v1.json"))["frozen_params"])
env = FedsSimFireEnv(sim_params=p, budgets=(4,), line_placement="front_edge", max_budget=4)
ids = sorted(env.scenario_ids)[:int(sys.argv[1])]
pol = make_heuristic("advancing_front")
out=[]
for sid in ids:
    t=time.time()
    obs, info = env.reset(seed=0, options={"scenario_id": sid, "budget": 4})
    fm = env.simulation.fire_manager
    stats = {"max_ros_at_line_ft_per_min": 0.0, "max_ros_any_ft_per_min": 0.0}
    orig = fm._update_rate_of_spread
    def wrapped(ros, fire_map, orig=orig):
        per_min = ros / fm.update_rate
        line = fire_map == SIMFIRE_FIRELINE
        if line.any(): stats["max_ros_at_line_ft_per_min"] = max(stats["max_ros_at_line_ft_per_min"], float(per_min[line].max()))
        stats["max_ros_any_ft_per_min"] = max(stats["max_ros_any_ft_per_min"], float(per_min.max()))
        return orig(ros, fire_map)
    fm._update_rate_of_spread = wrapped
    applied=0; done=False; acts=[]
    while not done:
        a = pol(obs, env.action_masks()); acts.append(a)
        before = env.simulation.fire_map.copy()
        obs, r, done, _, si = env.step(a); applied += si["line_cells_applied"]
        # line cells placed this step = cells that were 0 before and line was applied
    fmap = env.simulation.fire_map
    out.append((sid, acts, applied, int((env.simulation.fire_map==SIMFIRE_FIRELINE).sum()), stats["max_ros_at_line_ft_per_min"], stats["max_ros_any_ft_per_min"]))
burnt = [o for o in out if o[3] < o[2]]
print("episodes", len(out), "with line", sum(o[2]>0 for o in out), "line cells applied", sum(o[2] for o in out), "line cells surviving", sum(o[3] for o in out))
print("episodes where a line cell burned", len(burnt), burnt[:5])
print("max ROS at any line cell ft/min", max(o[4] for o in out), "max ROS anywhere ft/min", max(o[5] for o in out))
print("decisions with action applied after 0:", sum(sum(1 for a in o[1][1:] if a) for o in out))
