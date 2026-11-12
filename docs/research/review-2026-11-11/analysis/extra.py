import json, sys, numpy as np
from collections import defaultdict
gate = json.load(open(sys.argv[1]))["results"]
fc = np.array([c["initial_feds_state"]["active_front_cells"] for c in gate])
sc = np.array([c["initial_feds_state"]["burn_scar_cells"] for c in gate])
print("initial active-front cells: median %d p10 %d p90 %d; scar cells median %d" % (np.median(fc), np.percentile(fc,10), np.percentile(fc,90), np.median(sc)))
print("share of fires whose initial front has > 7 cells: %.2f, > 28 cells: %.2f" % ((fc>7).mean(), (fc>28).mean()))
d = json.load(open(sys.argv[2])); eps = d["episodes"]
noop = {e["scenario_id"]: e["added_burned_cells"] for e in eps if e["policy"]=="noop" and e["budget"]==0}
tab = defaultdict(dict)
for e in eps:
    if e["budget"]==1 and e["lines_applied"]==1 and e["actions"][0]!=0:
        tab[e["scenario_id"]][e["actions"][0]] = e["added_burned_cells"]-noop[e["scenario_id"]]
rng=[]; gain=[]
for f,t in tab.items():
    if len(t)>=3:
        v=np.array(list(t.values()),float); rng.append(v.max()-v.min()); gain.append(v.mean()-v.min())
rng=np.array(rng); gain=np.array(gain)
print("fires with >=3 distinct decision-0 sectors observed at B=1: %d; best-worst range median %.0f ha mean %.0f ha; best-vs-average-sector mean %.0f ha" % (len(rng), np.median(rng)*3.24, rng.mean()*3.24, gain.mean()*3.24))
print("sectors observed per fire (B=1, decision 0): median", np.median([len(t) for t in tab.values()]))
