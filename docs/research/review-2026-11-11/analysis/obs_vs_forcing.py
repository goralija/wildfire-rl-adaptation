"""TRAIN only: does the observed (previous-day) wind give the same downwind sector as the forcing?"""
import json, math, sys
import numpy as np
sys.path.insert(0, sys.argv[1] + "/src")
from wildfire_rl.feds_simfire_setup import observed_weather_records
w = json.load(open(sys.argv[2]))
SECT = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
def sector(th_from):
    to = math.radians((th_from + 180) % 360)
    dx, dy = math.sin(to), -math.cos(to)
    return max(range(8), key=lambda i: (SECT[i][0]*dx + SECT[i][1]*dy)/math.hypot(*SECT[i]))
def angdiff(a, b):
    return abs((a - b + 180) % 360 - 180)
same = []; diffs = []; spd = []
for c in w["cases"]:
    if c.get("split") != "train":
        continue
    obs = observed_weather_records(c, "previous")
    for k, seg in enumerate(c["segments"]):
        a = seg["gridmet_values"]["th"]["value"]; b = obs[k]["gridmet_values"]["th"]["value"]
        same.append(sector(a) == sector(b)); diffs.append(angdiff(a, b))
        spd.append(seg["gridmet_values"]["vs"]["value"])
same = np.array(same); diffs = np.array(diffs)
print("TRAIN decisions:", len(same))
print("observed downwind sector == forcing downwind sector: %.2f" % same.mean())
print("wind direction difference observed vs forcing: median %.0f deg, share > 45 deg %.2f, > 90 deg %.2f" % (np.median(diffs), (diffs > 45).mean(), (diffs > 90).mean()))
print("forcing 10 m wind speed m/s: median %.1f, p90 %.1f; midflame proxy at WAF 0.10: median %.2f m/s" % (np.median(spd), np.percentile(spd, 90), 0.1*np.median(spd)))
