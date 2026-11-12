"""TRAIN-only analysis for TUNED_HEURISTICS.md (no simulation, no VALIDATION, no TEST).

Inputs (argv): repo worktree, TRAIN benchmark JSON, gridMET weather JSON, TRAIN no-op gate report.
"""
import json
import math
import sys
from collections import Counter, defaultdict

import numpy as np

REPO, BENCH, WEATHER, GATE = sys.argv[1:5]
sys.path.insert(0, REPO + "/src")
from wildfire_rl.feds_simfire_setup import observed_weather_records  # noqa: E402

HA = 3.24
rng = np.random.default_rng(20261111)

d = json.load(open(BENCH))
assert d["split"] == "train" and not d["test_cases_loaded"]
eps = d["episodes"]
by = {(e["scenario_id"], e["policy"], e["budget"]): e for e in eps}
fires = sorted({e["scenario_id"] for e in eps})
policies = sorted({e["policy"] for e in eps})
noop = {f: by[(f, "noop", 0)]["added_burned_cells"] for f in fires}
BUDGETS = (1, 2, 4)


def delta(f, p, B):
    return (by[(f, p, B)]["added_burned_cells"] - noop[f]) * HA


# ---------------------------------------------------------------- 0. determinism / pooled table
print("== 0. pooled outcome table (sequence -> outcome), all budgets")
table = defaultdict(dict)
conflicts = 0
for e in eps:
    seq = tuple(e["actions"])
    val = e["added_burned_cells"]
    t = table[e["scenario_id"]]
    if seq in t and t[seq] != val:
        conflicts += 1
    t[seq] = val
print("sequence/outcome conflicts across policies and budgets:", conflicts)
nseq = [len(t) for t in table.values()]
print("distinct sequences per fire: median %d, min %d, max %d" % (np.median(nseq), min(nseq), max(nseq)))


def nlines(seq):
    return sum(1 for a in seq if a)


# coverage of the B=1 tree (33 sequences) per fire
cov1 = [sum(1 for s in t if nlines(s) <= 1) for t in table.values()]
print("B=1 tree coverage (of 33 legal-or-not sequences): median %d, min %d, max %d" % (np.median(cov1), min(cov1), max(cov1)))
single_at = Counter()
for t in table.values():
    for s in t:
        if nlines(s) == 1:
            single_at[next(i for i, a in enumerate(s) if a)] += 1
print("single-line sequences observed by decision of the line:", dict(sorted(single_at.items())))

# ---------------------------------------------------------------- 1. selector oracle by subset
print("\n== 1. per-fire hindsight selection among menus (mean delta vs no-op, ha) and share of the best-of-44 gap")
menus = {
    "adv": ["advancing_front"],
    "downwind": ["downwind"],
    "{adv,dw}": ["advancing_front", "downwind"],
    "{adv,dw,random}": ["advancing_front", "downwind", "random_legal"],
    "{adv,dw,noop}": ["advancing_front", "downwind", "noop"],
    "{adv,dw,random,noop}": ["advancing_front", "downwind", "random_legal", "noop"],
    "10 base PPO": [p for p in policies if p.startswith("base-")],
    "all 44": policies,
}
for B in BUDGETS:
    best44 = np.mean([min(delta(f, p, B) for p in policies) for f in fires])
    adv = np.mean([delta(f, "advancing_front", B) for f in fires])
    # best single policy on TRAIN in-sample
    singles = {p: np.mean([delta(f, p, B) for f in fires]) for p in policies}
    bestp = min(singles, key=singles.get)
    print("B=%d  best-of-44 %.1f | best single policy in-sample %s %.1f | adv %.1f" % (B, best44, bestp, singles[bestp], adv))
    for name, m in menus.items():
        v = np.mean([min(delta(f, p, B) for p in m) for f in fires])
        share = (v - adv) / (best44 - adv) if best44 != adv else float("nan")
        print("     %-22s %7.1f ha  share of (best-of-44 - adv) gap: %.2f" % (name, v, share))

# agreement of first sectors
print("\n   adv vs downwind first action at B=1 (equal / differ):", end=" ")
agree = {f: by[(f, "advancing_front", 1)]["actions"][0] == by[(f, "downwind", 1)]["actions"][0] for f in fires}
print(sum(agree.values()), "/", len(fires) - sum(agree.values()))
for B in BUDGETS:
    same_out = sum(by[(f, "advancing_front", B)]["added_burned_cells"] == by[(f, "downwind", B)]["added_burned_cells"] for f in fires)
    dd = np.array([delta(f, "downwind", B) - delta(f, "advancing_front", B) for f in fires])
    print("   B=%d: identical outcome adv vs dw on %d fires; dw-adv mean %.1f ha, sd %.1f, fires dw better %d, adv better %d"
          % (B, same_out, dd.mean(), dd.std(ddof=1), (dd < 0).sum(), (dd > 0).sum()))

# ---------------------------------------------------------------- 2. buildable selector, leave-one-fire-out
print("\n== 2. LOFO selector between adv and downwind from decision-0 observables")
w = json.load(open(WEATHER))
wx = {c["scenario_id"]: c for c in w["cases"] if c.get("split") == "train"}
gate = {r["scenario_id"]: r for r in json.load(open(GATE))["results"]}
assert set(fires) <= set(wx) and set(fires) <= set(gate)
feat = {}
for f in fires:
    obs0 = observed_weather_records(wx[f], "previous")[0]["gridmet_values"]
    a_adv = by[(f, "advancing_front", 1)]["actions"][0]
    a_dw = by[(f, "downwind", 1)]["actions"][0]
    if a_adv and a_dw:
        ang = abs(((a_adv - a_dw) * 45 + 180) % 360 - 180)
    else:
        ang = 180.0
    feat[f] = {
        "wind_obs": obs0["vs"]["value"],
        "fm100_obs": obs0["fm100"]["value"],
        "front_cells": gate[f]["initial_feds_state"]["active_front_cells"],
        "scar_cells": gate[f]["initial_feds_state"]["burn_scar_cells"],
        "sector_angle": ang,
        "budget": None,
    }
FEATS = ["wind_obs", "fm100_obs", "front_cells", "scar_cells", "sector_angle"]


def fit_stump(train, B):
    """Pick (feature, threshold, side) that maximises in-sample gain of choosing dw over adv."""
    base = {f: delta(f, "advancing_front", B) for f in train}
    alt = {f: delta(f, "downwind", B) for f in train}
    best = (0.0, None)  # (total improvement over always-adv, rule)
    total_dw = sum(alt[f] - base[f] for f in train)
    if total_dw < 0:
        best = (total_dw, ("always_dw",))
    for k in FEATS:
        vals = sorted({feat[f][k] for f in train})
        for thr in vals:
            for side in ("le", "gt"):
                sel = [f for f in train if (feat[f][k] <= thr) == (side == "le")]
                imp = sum(alt[f] - base[f] for f in sel)
                if imp < best[0]:
                    best = (imp, (k, thr, side))
    return best[1]


def apply_rule(rule, f):
    if rule is None:
        return "advancing_front"
    if rule == ("always_dw",):
        return "downwind"
    k, thr, side = rule
    return "downwind" if (feat[f][k] <= thr) == (side == "le") else "advancing_front"


def boot_ci(x, n=4000):
    x = np.asarray(x, float)
    s = rng.choice(x, size=(n, x.size), replace=True).mean(axis=1)
    return np.percentile(s, [2.5, 97.5])


for B in BUDGETS:
    realised, adv_v, dw_v, orc = [], [], [], []
    rules = Counter()
    for f in fires:
        train = [g for g in fires if g != f]
        rule = fit_stump(train, B)
        rules[rule[0] if rule else "none"] += 1
        p = apply_rule(rule, f)
        realised.append(delta(f, p, B))
        adv_v.append(delta(f, "advancing_front", B))
        dw_v.append(delta(f, "downwind", B))
        orc.append(min(adv_v[-1], dw_v[-1]))
    gain = np.array(realised) - np.array(adv_v)
    insample_rule = fit_stump(fires, B)
    ins = np.mean([delta(f, apply_rule(insample_rule, f), B) for f in fires])
    print("B=%d LOFO stump selector %.1f ha | always adv %.1f | always dw %.1f | oracle{adv,dw} %.1f | in-sample stump %.1f (rule %s)"
          % (B, np.mean(realised), np.mean(adv_v), np.mean(dw_v), np.mean(orc), ins, insample_rule))
    print("     LOFO selector - adv: %.1f ha, 95%% bootstrap CI [%.1f, %.1f]; rule features chosen across folds %s"
          % (gain.mean(), *boot_ci(gain), dict(rules)))

# also: LOFO choice of the best single policy out of 44, per budget, and budget-adaptation analogue
print("\n== 2b. LOFO 'tune one discrete parameter' = pick best of 44 policies on 97 fires, score held-out fire")
for B in BUDGETS:
    lofo_B, lofo_2, chosen = [], [], Counter()
    for f in fires:
        train = [g for g in fires if g != f]
        pB = min(policies, key=lambda p: np.mean([delta(g, p, B) for g in train]))
        p2 = min(policies, key=lambda p: np.mean([delta(g, p, 2) for g in train]))
        chosen[pB] += 1
        lofo_B.append(delta(f, pB, B))
        lofo_2.append(delta(f, p2, B))
    singles = {p: np.mean([delta(f, p, B) for f in fires]) for p in policies}
    bestp = min(singles, key=singles.get)
    diff = np.array(lofo_B) - np.array(lofo_2)
    print("B=%d in-sample best %s %.1f | LOFO tuned-at-B %.1f | LOFO tuned-at-B=2 then used at B %.1f | per-budget minus B=2-tuned %.1f [%.1f, %.1f] | choices %s"
          % (B, bestp, singles[bestp], np.mean(lofo_B), np.mean(lofo_2), diff.mean(), *boot_ci(diff), dict(chosen.most_common(3))))

# ---------------------------------------------------------------- 3. power at n = 20
print("\n== 3. minimum detectable effect at n = 20 from TRAIN paired-delta SDs (normal approx, 80% power)")
z = 1.96 + 0.84
zholm = 2.64 + 0.84  # two-sided alpha .05/6
for B in BUDGETS:
    pairs = {
        "downwind - adv": [delta(f, "downwind", B) - delta(f, "advancing_front", B) for f in fires],
        "random - adv": [delta(f, "random_legal", B) - delta(f, "advancing_front", B) for f in fires],
        "best-of-44 - adv": [min(delta(f, p, B) for p in policies) - delta(f, "advancing_front", B) for f in fires],
        "oracle{adv,dw} - adv": [min(delta(f, "downwind", B), delta(f, "advancing_front", B)) - delta(f, "advancing_front", B) for f in fires],
    }
    for name, x in pairs.items():
        x = np.asarray(x)
        sd = x.std(ddof=1)
        # subsample n=20 from TRAIN to see the spread of a 20-fire mean
        sub = np.array([rng.choice(x, 20, replace=False).mean() for _ in range(4000)])
        top2 = np.sort(np.abs(x))[-2:].sum() / max(np.abs(x).sum(), 1e-9)
        print("B=%d %-22s mean %7.1f sd %6.1f | MDE n=20: %.0f ha (Holm/6: %.0f) | 20-fire subsample mean 2.5-97.5%%: [%.0f, %.0f] | top-2 fires share of |delta| %.2f"
              % (B, name, x.mean(), sd, z * sd / math.sqrt(20), zholm * sd / math.sqrt(20), *np.percentile(sub, [2.5, 97.5]), top2))

# ---------------------------------------------------------------- 4. missing fallback: upper bound
print("\n== 4. heuristic decisions with action 0 while budget remained and the no-op fire was still active")
act_after = {f: [s["fire_active_after_segment"] for s in gate[f]["trajectory"]] for f in fires}
# check gate no-op == bench no-op
mism = sum(1 for f in fires if gate[f]["trajectory"][-1]["new_burned_cells_since_initial"] != noop[f])
print("gate no-op vs bench no-op final added cells mismatches:", mism)
for p in ("advancing_front", "downwind"):
    for B in BUDGETS:
        n_idle, n_idle_active = 0, 0
        for f in fires:
            acts = by[(f, p, B)]["actions"]
            used = 0
            for k, a in enumerate(acts):
                if a:
                    used += 1
                    continue
                if used < B:
                    n_idle += 1
                    # the fire is burning at decision k iff k == 0 or the no-op was active after segment k-1
                    active = True if k == 0 else bool(act_after[f][k - 1])
                    n_idle_active += active
        print("  %-16s B=%d idle decisions with budget left %3d, of which no-op fire still burning %3d" % (p, B, n_idle, n_idle_active))

# ---------------------------------------------------------------- 5. budget structure in hindsight
print("\n== 5. hindsight structure across budgets (pooled observed sequences; lower bound on the tree)")
first_line_same, n_cmp, best1_late = 0, 0, 0
for f in fires:
    t = table[f]
    s1 = [s for s in t if nlines(s) <= 1]
    s2 = [s for s in t if nlines(s) <= 2]
    b1 = min(s1, key=lambda s: t[s])
    b2 = min(s2, key=lambda s: t[s])
    if t[b1] < noop[f]:
        k1 = next(i for i, a in enumerate(b1) if a)
        best1_late += k1 > 0
    if t[b1] < noop[f] and t[b2] < noop[f]:
        n_cmp += 1
        first_line_same += [(i, a) for i, a in enumerate(b1) if a][0] == [(i, a) for i, a in enumerate(b2) if a][0]
print("fires where best observed B=1 line is not at decision 0:", best1_late)
print("fires (with gains at both) where best observed B=2 sequence starts with the best B=1 line: %d / %d" % (first_line_same, n_cmp))
for B in BUDGETS:
    pooled = np.mean([(min(v for s, v in table[f].items() if nlines(s) <= B) - noop[f]) * HA for f in fires])
    print("B=%d pooled best observed sequence with <= B lines: %.1f ha" % (B, pooled))

# ---------------------------------------------------------------- 6. line-footprint credit, upper bound
print("\n== 6. upper bound on footprint credit (7 cells axis, 9 diagonal, x 3.24 ha) vs mean delta")
for p in ("advancing_front", "downwind", "random_legal"):
    for B in BUDGETS:
        ub = np.mean([sum((7 if a % 2 == 1 else 9) for a in by[(f, p, B)]["actions"] if a) * HA for f in fires])
        md = np.mean([delta(f, p, B) for f in fires])
        print("  %-16s B=%d footprint upper bound %.1f ha vs mean delta %.1f ha (%.0f%%)" % (p, B, ub, md, 100 * ub / -md))

# ---------------------------------------------------------------- 7. fixed sector at decision 0, B=1 (single line at d0)
print("\n== 7. B=1 single line at decision 0: mean delta by action over fires where observed; axis vs diagonal")
d0 = defaultdict(dict)
for f, t in table.items():
    for s, v in t.items():
        if nlines(s) == 1 and s[0]:
            d0[f][s[0]] = (v - noop[f]) * HA
ax = [v for t in d0.values() for a, v in t.items() if a % 2 == 1]
dg = [v for t in d0.values() for a, v in t.items() if a % 2 == 0]
print("axis mean %.1f (n=%d), diagonal mean %.1f (n=%d)" % (np.mean(ax), len(ax), np.mean(dg), len(dg)))
for a in range(1, 9):
    v = [t[a] for t in d0.values() if a in t]
    print("  action %d observed on %2d fires, mean %.1f ha" % (a, len(v), np.mean(v)))
for p, B in (("base-s15", 1), ("base-s17", 2)):
    print("  %s B=%d sequences:" % (p, B), Counter(tuple(by[(f, p, B)]["actions"]) for f in fires).most_common(4))

# ---------------------------------------------------------------- 8. fixed sector honestly (no per-fire fitting)
print("\n== 8. fixed decision-0 sector at B=1 (actions 3-7, observed on all fires): LOFO pick and bootstrap CI vs adv")
cand = [a for a in range(1, 9) if all(a in d0[f] for f in fires)]
adv1 = {f: delta(f, "advancing_front", 1) for f in fires}
lofo, picks = [], Counter()
for f in fires:
    tr = [g for g in fires if g != f]
    a = min(cand, key=lambda a: np.mean([d0[g][a] for g in tr]))
    picks[a] += 1
    lofo.append(d0[f][a] - adv1[f])
lofo = np.array(lofo)
nw = np.array([d0[f][6] - adv1[f] for f in fires])
print("candidates", cand, "LOFO picks", dict(picks))
print("LOFO fixed sector - adv: %.1f ha, 95%% CI [%.1f, %.1f]" % (lofo.mean(), *boot_ci(lofo)))
print("fixed NW (action 6) - adv, in-sample choice: %.1f ha, 95%% CI [%.1f, %.1f]; fires better %d worse %d" % (
    nw.mean(), *boot_ci(nw), (nw < 0).sum(), (nw > 0).sum()))
