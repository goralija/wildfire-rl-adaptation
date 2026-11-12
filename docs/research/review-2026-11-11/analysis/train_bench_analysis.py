"""TRAIN-only analysis of the existing ADR-032 TRAIN benchmark (no simulation)."""
import json
import math
import sys
from collections import Counter, defaultdict

import numpy as np

BENCH = sys.argv[1]
WEATHER = sys.argv[2]
d = json.load(open(BENCH))
assert d["split"] == "train"
eps = d["episodes"]
CELL_HA = 3.24

def family(p):
    if p.startswith("base-"):
        return "base"
    if p.startswith("ft-b1"):
        return "ft-b1"
    if p.startswith("ft-b2"):
        return "ft-b2"
    if p.startswith("ft-b4"):
        return "ft-b4"
    return p

by = {}
for e in eps:
    by[(e["scenario_id"], e["policy"], e["budget"])] = e
fires = sorted({e["scenario_id"] for e in eps})
policies = sorted({e["policy"] for e in eps})
noop = {f: by[(f, "noop", 0)]["added_burned_cells"] for f in fires}
na = np.array([noop[f] for f in fires], dtype=float)
print("fires", len(fires), "policies", len(policies))
print("no-op added cells: mean %.0f median %.0f std %.0f min %d max %d" % (na.mean(), np.median(na), na.std(), na.min(), na.max()))
print("no-op return (-cells/100): mean %.2f std %.2f" % (-na.mean() / 100, na.std() / 100))
print("fires with zero no-op growth:", int((na == 0).sum()))

# A/B: delta vs no-op per family/budget, share of line episodes that change nothing
print("\n== per family x budget: mean delta ha, share of line-episodes identical to no-op, worse than no-op")
fam_rows = defaultdict(list)
for e in eps:
    if e["budget"] == 0:
        continue
    delta = e["added_burned_cells"] - noop[e["scenario_id"]]
    fam_rows[(family(e["policy"]), e["budget"])].append((delta, e["lines_applied"]))
for key in sorted(fam_rows):
    rows = fam_rows[key]
    deltas = np.array([r[0] for r in rows], float)
    lines = np.array([r[1] for r in rows])
    with_line = lines > 0
    same = (deltas[with_line] == 0).mean() if with_line.any() else float("nan")
    worse = (deltas[with_line] > 0).mean() if with_line.any() else float("nan")
    print("%-16s B=%d n=%4d mean %.1f ha | line eps %4d, unchanged %.2f, worse %.3f, mean lines %.2f" % (
        key[0], key[1], len(rows), deltas.mean() * CELL_HA, with_line.sum(), same, worse, lines.mean()))

# C: oracle selection among the 44 observed policies per fire and budget
print("\n== headroom from existing episodes (best of 44 observed policies per fire, oracle selection)")
heur = ["advancing_front", "downwind", "random_legal"]
for B in (1, 2, 4):
    best = []
    h = {n: [] for n in heur}
    base_mean = []
    seqs = []
    for f in fires:
        vals = [by[(f, p, B)]["added_burned_cells"] for p in policies]
        best.append(min(vals) - noop[f])
        for n in heur:
            h[n].append(by[(f, n, B)]["added_burned_cells"] - noop[f])
        base_mean.append(np.mean([by[(f, p, B)]["added_burned_cells"] - noop[f] for p in policies if p.startswith("base-")]))
        seqs.append(len({tuple(by[(f, p, B)]["actions"]) for p in policies}))
    best = np.array(best, float)
    besth = np.minimum.reduce([np.array(h[n], float) for n in ("advancing_front", "downwind")])
    print("B=%d best-of-44 %.1f ha | best-of(adv,downwind) per fire %.1f | adv %.1f | downwind %.1f | random %.1f | base PPO mean %.1f | distinct seqs/fire median %d" % (
        B, best.mean() * CELL_HA, besth.mean() * CELL_HA, np.mean(h["advancing_front"]) * CELL_HA,
        np.mean(h["downwind"]) * CELL_HA, np.mean(h["random_legal"]) * CELL_HA, np.mean(base_mean) * CELL_HA, int(np.median(seqs))))
    print("     fires where no observed policy changes outcome: %d / %d; fires where best-of-44 < -100 cells: %d" % (
        int((best == 0).sum()), len(fires), int((best < -100).sum())))
    # concentration of the oracle gain
    s = np.sort(best)
    print("     oracle gain share from top 5 fires: %.2f, top 10: %.2f" % (s[:5].sum() / s.sum(), s[:10].sum() / s.sum()))
    rel = best / np.maximum(na, 1)
    print("     oracle gain as fraction of fire's no-op growth: median %.3f, mean %.3f (fires with no-op>0)" % (
        np.median(rel[na > 0]), rel[na > 0].mean()))

# E: SNR. Std across fires of no-op cells vs size of policy deltas
print("\n== scale: per-fire no-op return std %.1f vs mean |delta| of advancing_front at B=2 %.2f (reward units)" % (
    na.std() / 100, np.mean([abs(by[(f, "advancing_front", 2)]["added_burned_cells"] - noop[f]) for f in fires]) / 100))

# Episodes: which sectors do base policies open with
print("\n== first action of base policies on TRAIN B=2")
for p in policies:
    if p.startswith("base-"):
        c = Counter(by[(f, p, 2)]["actions"][0] for f in fires)
        print(p, dict(c.most_common(4)))

# G: delta vs angle between first-line sector and downwind heading (B=1 episodes, all policies)
w = json.load(open(WEATHER))
wx = {c["scenario_id"]: c for c in w["cases"] if c.get("split") == "train"}
SECT = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))

def sector_bearing(s):
    dx, dy = SECT[s]
    return (math.degrees(math.atan2(dx, -dy)) + 360) % 360

def wind_to(rec):
    v = rec["gridmet_values"]
    th = v["th"]["value"] if isinstance(v, dict) and "th" in v else None
    return (th + 180.0) % 360 if th is not None else None

first = next(iter(wx.values()))
print("\nweather record keys:", list(first.keys()), list(first["segments"][0].keys()), first["segments"][0]["gridmet_values"])
bins = defaultdict(list)
for e in eps:
    if e["budget"] != 1 or e["lines_applied"] != 1:
        continue
    f = e["scenario_id"]
    k = next(i for i, a in enumerate(e["actions"]) if a)
    seg = wx[f]["segments"][k]
    wt = wind_to(seg)
    if wt is None:
        continue
    diff = abs((sector_bearing(e["actions"][k] - 1) - wt + 180) % 360 - 180)
    bins[int(diff // 45)].append(e["added_burned_cells"] - noop[f])
print("== B=1 single-line episodes: delta (ha) by angle between line sector and actual segment wind-to (45 deg bins)")
for b in sorted(bins):
    a = np.array(bins[b], float)
    print("  %3d-%3d deg n=%4d mean %.1f ha, unchanged %.2f" % (b * 45, b * 45 + 45, len(a), a.mean() * CELL_HA, (a == 0).mean()))

# Which decision step the line is placed (all line episodes)
st = Counter()
for e in eps:
    for i, a in enumerate(e["actions"]):
        if a:
            st[i] += 1
print("\nline actions by decision index (all policies, all budgets):", dict(sorted(st.items())))
