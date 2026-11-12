---
type: Research Analysis
title: "Heuristike optimizovane treningom"
description: "Šest porodica pristupa (podešena heuristika, selektor, BC+PPO, rezidualni RL, planiranje, čisti RL) i plan."
status: stable
generated: {by: "process:claude-code", at: "2026-11-11T16:00:00Z"}
sources:
  - resource: /src/wildfire_rl/feds_heuristics.py
  - resource: /scripts/benchmark_feds_policies.py
  - resource: /docs/specs/DECISION_RECORDS.md
---
# E: Heuristics optimised through training — does the direction make sense here?

The owner's question: "Is the best approach perhaps to use heuristics that we optimise through
training, so that they cover the cases where the heuristics alone cannot reach high-quality
performance?" Judged together with A (literature), B (short episodes), C (interventions) and
D (what is real), which are in this folder ([index](index.md)) and are not redone here.

Date: 2026-11-11. Repository state: worktree `.worktrees/task-026-stage-2` (HEAD 61f0ebf).
Read-only: nothing in the repository was edited, no training, no SimFire run. The new numbers
come from `E_heuristics_analysis.py` (output `E_heuristics_analysis.out`, both in
[analysis/](analysis/README.md)), run with `nice -n 19` and `python -B` in under a minute, on TRAIN files only:
- `.local/bench/adr030-train.json` (ADR-032 TRAIN benchmark, 98 fires, 17,248 episodes);
- `.local/gridmet/feds-episode-weather-v1.json`, filtered to `split == "train"`, read only
  through `observed_weather_records(c, "previous")` (what the policy sees, never the forcing);
- `.worktrees/task-026-stage-1/.local/gate/adr030/waf-0.1-ros-1.json` (TRAIN no-op gate run;
  its final no-op areas match the benchmark's no-op on all 98 fires).

VALIDATION numbers are quoted from ADR-032 only. TEST 2024 was not touched.

## Labels

- **[fact]** read in code, an ADR or a report, with a location.
- **[new, TRAIN]** my analysis of existing TRAIN files (section of `E_heuristics_analysis.out`
  given as §0–§8).
- **[A]/[B]/[C]/[D]** taken from the earlier analyses in this folder.
- **[interpretation]** my reading, with a confidence level.

---

## Short answer

**The idea is sound in direction but small in payoff, and it cannot be judged on 20
VALIDATION fires. Do not start it as a training project. Start it as an offline analysis on an
exhaustive TRAIN table. That one run decides it.** (Confidence: medium-high on the
direction, medium on the numbers.)

1. **"Heuristic + optimisation" is the right family for this MDP.** That is what the
   literature supports [A §4–5] and what the MDP's structure invites. The problem has 4
   decisions, 9 actions and a deterministic simulator, so it is close to a contextual bandit
   [B §2g]. A low-dimensional rule tuned on TRAIN needs few episodes, which is exactly what
   SimFire's speed allows. PPO from scratch needs many, which it does not [A §3.6].
2. **But the headroom the owner is pointing at ("cases where heuristics fail") is almost
   entirely "pick the right compass sector for this particular fire".** On TRAIN at B=2, the
   per-fire hindsight best of the 10 base PPO policies, which are mostly fixed-direction
   policies, captures 83% of the gap between `advancing_front` and the best of all 44
   policies. Choosing per fire between `advancing_front` and `downwind` captures only 22%
   [new, TRAIN §1]. The headroom is real in hindsight (−577 ha against −194 ha at B=2). It is
   useful only if the right sector can be **predicted from what the policy observes**.
3. **The first cheap test of predictability is negative.** A leave-one-fire-out selector
   chooses between `advancing_front` and `downwind` from decision-0 observables (lagged wind,
   fm100, front and scar size, sector disagreement). It does no better than always playing
   `advancing_front`: +29, −15 and +55 ha at B=1, 2 and 4 (positive = worse), every interval
   including zero. Its in-sample versions look 25–50 ha better, which is overfitting
   [new, TRAIN §2]. Choosing "the best of 44 policies" on 97 fires and scoring the held-out
   fire loses 90–125 ha against the in-sample figure at B=2 and B=4 [new, TRAIN §2b]. With 98
   heavy-tailed fires, tuning even one discrete choice is noisy.
4. **Twenty VALIDATION fires can detect only large gains.** The minimum detectable effect at
   80% power is about 30 ha at B=1, but about 120–150 ha at B=2 and 150–180 ha at B=4 (from
   the ADR-032 interval widths), or 170–270 ha (from TRAIN heuristic-vs-heuristic spreads).
   No tuned rule has yet shown an out-of-sample gain on TRAIN. The only choice that needs no
   per-fire fitting, a fixed NW line at decision 0 picked leave-one-fire-out, gives −16 ha
   against `advancing_front`, 95% CI [−95, +58], better on 27 fires and worse on 31
   [new, TRAIN §8]. Apparent gains of 35 ha (`base-s15` at B=1) are in-sample: every PPO
   policy was trained on all 98 TRAIN fires. **Only B=1 is even in principle within reach**,
   and that is also the only budget where ADR-032 had a near-signal. Whether anything
   reaches it is exactly what the exhaustive table must show.
5. **For the original budget question, "tune per budget" is a fair and cleaner stand-in
   for fine-tuning, but only if the rule has a budget-dependent parameter** (when to spend,
   or a sector rule that depends on the remaining budget). In this MDP the budget changes
   only timing and the number of lines. B=1 is the only budget with a real timing choice,
   and the existing data contain almost no late single lines, so the timing headroom is
   **unmeasured** [new, TRAIN §0].

**Ranked recommendation:**
1. Exhaustive TRAIN table at B=1, which also scores families 1–4 offline.
2. Planning under persistence weather (model-predictive control), labelled as such.
3. A tuned scoring heuristic at B=2/B=4.
4. Behaviour cloning plus PPO.
5. Pure RL with a no-op-relative reward and more training.

Residual RL collapses into the selector. Details are in §5 and §6.

---

## 0. What "heuristics optimised through training" means in this MDP

**Facts.**
- The policy chooses one of 9 actions per 12 h decision: no-op or a 1.26 km line in one of
  8 compass sectors. There are 4 decisions per episode, at most one line each and B ≤ 4. The
  environment places the cells (`feds_simfire_env.py:157-182, 418-442`) [C §1.2].
- The simulator is deterministic per fire. The benchmark confirms this, and so does the
  pooled table here: across all policies and budgets, **0 conflicts** between an action
  sequence and its outcome on any fire [new, TRAIN §0].
- The legal action sequences per fire number 33 at B=1, 417 at B=2 and 6,561 at B=4 [B §3].
- The heuristics see the same observation as PPO: 16×16 pooled grid, lagged weather, no
  budget and no time (`feds_heuristics.py:1-10`) [C §1.6].
- The heuristics spend at the first legal opportunity and have no fallback sector
  (`feds_heuristics.py:41-43`).

**Consequences [interpretation, high confidence].**
- **At B=1, every policy is a mapping from the no-op path's observations to one decision,
  "at which decision k, in which sector".** Before the first line, every trajectory equals
  no-op. A table of 98 fires × 33 outcomes, plus the observation at each of the 4 decisions
  along the no-op path, therefore lets us score **any** B=1 policy exactly, without
  simulation. That covers a tuned heuristic, a selector, a behaviour-cloned network, a
  residual policy and a tabular RL policy. This is B's step 1. Here it becomes the gate for
  the whole direction.
- At B=2 the observations diverge after the first line. The B=2 tree (417 leaves, 52 decision
  nodes per fire with budget left: 1 + 9 + 17 + 25) must then record the observation at each internal node. With
  that, any B=2 policy can again be scored offline.
- At B=4 the tree is too large (6,561 leaves). Every candidate rule there costs real
  simulation.
- So, unlike in most RL problems, "tuning a heuristic" here can be done mostly **offline on a
  cached table**. That is the main practical argument for the direction.

## 1. New TRAIN facts used in this analysis

### 1.1 Where the hindsight headroom sits (selector oracle by menu) [new, TRAIN §1]

Mean added-area delta against no-op, in ha. Each menu's value takes the best member per fire
in hindsight. "Share" is the fraction of the gap between `advancing_front` and the best of
all 44 policies.

| Menu, per-fire hindsight choice | B=1 | share | B=2 | share | B=4 | share |
|---|---:|---:|---:|---:|---:|---:|
| `advancing_front` only | −112 | 0 | −194 | 0 | −290 | 0 |
| `downwind` only | −113 | 0 | −188 | −0.02 | −308 | 0.05 |
| {adv, downwind} | −159 | 0.18 | −278 | 0.22 | −392 | 0.26 |
| {adv, downwind, noop} | −159 | 0.18 | −278 | 0.22 | −392 | 0.26 |
| {adv, downwind, random line} | −223 | 0.42 | −372 | 0.46 | −471 | 0.46 |
| 10 base PPO policies | −322 | 0.79 | −510 | 0.83 | −608 | 0.80 |
| all 44 policies | −378 | 1 | −577 | 1 | −686 | 1 |

- Adding no-op to the menu adds nothing. A line almost never hurts in a way a selector could
  avoid, since only 2–8% of line episodes burn more than no-op [B §2c].
- Adding the random line roughly doubles the share. Its value is that it plays different
  sectors, not that it is random: it repeats one fixed draw per fire [C §1.7].
- Seven of the ten base policies open with one fixed action on all 98 fires [B §2b]. The
  base-PPO menu is therefore essentially "choose among about 7 fixed compass sectors per
  fire", and that already gives about 80% of the headroom.
- **Reading [interpretation, high]:** the headroom is "which sector for which fire". It is
  not "when to spend", nor "whether to use heuristic A or B".

### 1.2 How often there is anything to select between the two heuristics [new, TRAIN §1]

- `advancing_front` and `downwind` choose the same first action on 31 of 98 fires.
- Their outcomes are identical on 48, 37 and 28 fires at B=1, 2 and 4.
- Paired difference `downwind` − `advancing_front`: mean −1.0, +6.7 and −18.2 ha, with SD 268,
  431 and 422 ha per fire.
- Each wins on roughly as many fires as the other (24/26, 25/36, 32/38).

### 1.3 A selector you could actually build, scored leave-one-fire-out [new, TRAIN §2]

**Method.**
- A decision stump chooses `downwind` over `advancing_front` per fire.
- Features are what is known at decision 0: the previous-day wind speed and fm100 the policy
  sees, the initial FEDS front and scar size, and the angle between the two heuristics'
  sectors.
- The stump is refit on 97 fires and applied to the held-out one.

| B | Always adv | Always downwind | LOFO selector | Selector − adv (95% bootstrap CI) | In-sample stump | Hindsight {adv, dw} |
|---|---:|---:|---:|---|---:|---:|
| 1 | −112.2 | −113.2 | −83.5 | +28.7 [−0.7, +70.3] (worse) | −137.4 | −159.0 |
| 2 | −194.4 | −187.7 | −209.8 | −15.4 [−57.6, +17.6] | −233.4 | −277.5 |
| 4 | −289.9 | −308.1 | −234.5 | +55.4 [−6.0, +124.7] (worse) | −338.0 | −392.1 |

**Reading [interpretation, medium-high].**
- The in-sample stump finds a rule worth 25–50 ha at every budget, and each rule disappears
  out of sample. At B=1 and B=4 the selected rule is actively harmful.
- The features chosen across folds are scar size at B=1, fm100 at B=2 and sector
  disagreement at B=4. That instability is a fingerprint of noise.
- This does **not** prove that no observable predicts the right sector. The features are
  coarse, and the choice is limited to 2 of 8 sectors. It does show that **naive tuning on 98
  fires overfits**, and that any tuned rule needs nested cross-validation before anyone
  believes it.

### 1.4 "Tune one discrete parameter" honestly: best of 44 chosen on 97 fires [new, TRAIN §2b]

Two policies are scored on the held-out fire:
- **tuned at B:** the policy with the best mean on the 97 other fires at the same budget;
- **tuned at B=2:** the policy with the best mean on the 97 other fires at B=2, applied
  at B.

The second is the analogue of "no budget adaptation".

| B | In-sample best | LOFO, tuned at B | LOFO, tuned at B=2 | Per-budget − B=2-tuned (95% CI) | Choices across folds |
|---|---|---:|---:|---|---|
| 1 | `base-s15` −147.0 | −147.0 | −50.1 | −96.9 [−177.9, −28.5] | `base-s15` in all 98 |
| 2 | `base-s17` −222.3 | **−132.0** | −132.0 | 0 | `base-s17` 90, `base-s15` 7, `ft-b1-s12` 1 |
| 4 | `downwind` −308.1 | **−183.6** | −222.2 | +38.6 [−4.4, +92.7] | `downwind` 83, `base-s17` 15 |

**Reading [interpretation, medium-high].**
- **Winner's curse.** At B=2 and B=4, the LOFO score of the "tuned" choice is 90–125 ha worse
  than its in-sample score, and worse than simply playing `advancing_front` (−194 and −290).
  A handful of large fires decide which policy looks best. Leave one of them out and the
  choice flips.
- **B=1 is different, but not cross-validated.** The choice is stable across all 98 folds,
  and the chosen policy beats `advancing_front` by 35 ha on TRAIN. **This is in-sample with
  respect to PPO training.** LOFO removes the optimism of *choosing* among the 44 policies,
  not of *fitting*: `base-s15` was trained on the held-out fire too. The same applies to the
  per-budget −97 ha below.
  - That policy is `base-s15`, which opens NW on 70 fires and SW on 28.
  - The best *fixed* sector at B=1 is NW (action 6) at −128.7 ha among the sectors seen on
    all 98 fires [new, TRAIN §7]. Actions 3–7 are observed on all fires.
  - The fixed NW line, picked leave-one-fire-out among actions 3–7 (NW is picked in all 98
    folds), scores −16.4 ha against `advancing_front`, 95% bootstrap CI [−94.7, +57.8], with
    27 fires better and 31 worse [new, TRAIN §8]. **There is no honest out-of-sample gain
    from a fixed compass bias on TRAIN.** The extra 18 ha of `base-s15` (NW on 70 fires, SW
    on 28) is in-sample fit.
  - Whether a map-fixed direction learned on 2018–19 fires transfers to the 2023 VALIDATION
    fires is doubtful [interpretation, medium]. It reflects regional wind and terrain, not a
    tactic.
- **Budget adaptation, LOFO.** At B=1, re-tuning per budget is 97 ha better than reusing the
  B=2 choice. That is only because the B=2 choice (`base-s17`, which opens W on 88 of 98 fires) is a poor
  B=1 policy. At B=4 re-tuning is 39 ha worse. The budget effect and the selection noise are
  the same size.

### 1.5 Detectability on 20 fires [new, TRAIN §3; ADR-032]

Minimum detectable effect (MDE), two-sided α = .05 and 80% power, normal approximation:
MDE ≈ 2.8·SD/√20. With Holm over 6 tests, about ×1.24.

| Basis | B=1 | B=2 | B=4 |
|---|---:|---:|---:|
| VALIDATION SD implied by the ADR-032 base − adv interval half-widths (≈19, 83, 102 ha → SD ≈ 44, 189, 233) | **≈28 ha** (Holm ≈34) | ≈118 (≈147) | ≈146 (≈181) |
| TRAIN SD of `downwind` − adv per fire (268, 431, 422) | 168 (209) | 270 (336) | 264 (328) |
| TRAIN SD of hindsight {adv, dw} − adv (186, 259, 285) | 117 (145) | 162 (202) | 178 (222) |

- The ADR-032 intervals come from seed-averaged PPO deltas on VALIDATION fires, which are
  smaller (median no-op 685 ha) than TRAIN fires.
- A single deterministic tuned rule against `advancing_front` will sit between the two rows.
- Sign-flip tests with heavy tails lose further power. Three of six ADR-032 estimates
  changed sign without one scenario.

**Reading [interpretation, medium-high].**

| B | Realisable gains seen so far (cross-validated on TRAIN) | VALIDATION MDE at n=20 | Verdict |
|---|---|---|---|
| 1 | ≈ 0: fixed NW −16 ha [−95, +58]; the LOFO selector is +29 (worse); 35 ha only in-sample | about 30 ha | **Below the MDE**, unless the probe on the exhaustive table finds predictable signal |
| 2, 4 | about 0 | 120–270 ha | **Undetectable.** Even the *hindsight* oracle between the two heuristics (83 and 102 ha) is below the MDE |

So whether tuning "works" must be decided mainly by **nested cross-validation on the 98 TRAIN
fires**, which has about 2.2× the precision of 20 fires (√(98/20)). Even that precision is not
enough to resolve a 16 ha effect: the TRAIN CI for fixed NW is ±75 ha. VALIDATION becomes a
one-shot confirmation at B=1, not a discovery tool. The case for the exhaustive table as the
gate gets stronger, not weaker: nothing seen so far survives honest evaluation.

### 1.6 The missing fallback is small [new, TRAIN §4]

Decisions where a heuristic played no-op although budget remained and the **no-op** fire was
still burning:

| Heuristic | B=1 | B=2 | B=4 |
|---|---:|---:|---:|
| `advancing_front` | 0 | 2 of 96 idle decisions | 8 of 119 |
| `downwind` | 0 | 0 of 93 | 3 of 113 |

- The rest are fires that went out. 31 of 98 no-op fires die within 12 h [B §1].
- This is an approximation: after a line the state differs from the no-op path.
- **Reading [interpretation, medium-high].** The fallback fix changes at most about 10
  decisions in about 1,000. Make it, since it is one line of code, but do not expect it to
  move results. C's "175 of 294 later decisions" is overwhelmingly dead fires.

### 1.7 The line-footprint credit is about a quarter of every heuristic's gain (upper bound) [new, TRAIN §6]

- Line cells are counted as saved even when the no-op fire would have burned them
  [C §1.3; `feds_simfire_env.py:215-221, 444-452`].
- Upper bound on this credit: 7 cells for an axis line and 9 for a diagonal, × 3.24 ha, per
  applied line.
  - `advancing_front`: 26, 44 and 72 ha at B=1, 2 and 4, which is 22–25% of its mean delta.
  - `downwind` and the random line: 21–26%.
- Axis and diagonal single lines at decision 0 do equally well (−90.8 against −89.1 ha) [new, TRAIN §7], so
  the credit does not obviously bias the direction choice.
- The real credit is below this bound. It can only be measured with the line cells and the
  no-op footprint, and the benchmark JSON does not store them.
- **Reading [interpretation, high].**
  - At B=1 the bound (≈26 ha) is the same size as the MDE (≈30 ha) and larger than any
    gain seen out of sample (≈ 0–16 ha).
  - An optimiser rewarded with it will learn to lay line where the fire would burn anyway,
    and a planner too.
  - The project already decided this question for the CA: ADR-030 addendum, "line charge
    stays in the training reward", `DECISION_RECORDS.md:1018-1032`. SimFire does not apply
    it. **This must be fixed before any tuning.**

### 1.8 Budget structure in hindsight [new, TRAIN §0, §5]

- Single-line sequences in the existing data put the line at decision 0 in 619 of 621 cases.
  Only one line each at decisions 1 and 2. **The value of waiting is unmeasured.**
- The pooled table covers only 6–9 of the 33 B=1 sequences per fire (median 7).
- Among the 79 fires where both the best observed B=1 and B=2 sequences beat no-op, the best
  B=2 sequence starts with the best B=1 line on 48 (61%) and starts differently on 31.
  - So in hindsight, the right first move depends on the budget in a sizeable minority of
    fires.
  - Whether that is predictable, or just the sector problem again, is unknown.

## 2. Measurement note: the CPU figure in the brief

- The brief says "~3 decisions/s per worker". ADR-032 measured about 3 decisions/s **in
  total** with 7 PPO environments: 17,136 decisions for the first seed in 95 min. That is
  about 0.4 decisions/s per worker in training.
- The benchmark is cheaper per decision: 3.8–5.6 worker-s per 4-decision episode [B §3],
  about 1–1.4 worker-s per decision.
- Costs below use **4.7 worker-s per benchmark-style episode** (range 3.8–5.6), **4 workers
  at low priority** on the owner's laptop, and about **1.7–2 decisions/s in total for PPO
  training on 4 workers**.
- Low priority under other load can stretch any wall time by 1.5–2×.

| Unit | Worker-h | Wall on 4 workers |
|---|---:|---:|
| 1,000 benchmark episodes | ≈1.3 | ≈20 min |
| B=1 exhaustive, 98 fires (3,234 episodes) | 3.4–5.0 | **≈50–75 min** |
| B=2 exhaustive, 98 fires (40,866 episodes, no prefix sharing) | 43–64 | **≈11–16 h** |
| B=2 exhaustive, 30-fire subset | 13–19 | ≈3.5–5 h |
| PPO, one stage-2-sized run (171,360 decisions) | — | ≈24–28 h |

---

## 3. The six families

### 3.1 Parameterised heuristic tuned on TRAIN (grid, Bayesian optimisation, CMA-ES), per budget

**What it looks like here.** One scoring rule replaces the two heuristics. At decision k,
play the legal sector s with the highest score:

`score(s) = w_wind·cos(s, observed downwind) + w_front·cos(s, front − scar centroid vector) + w_mass·(burning share in the pooled blocks in sector s) + w_fuel·(mean fuel code ahead in s) + w_bias·b_s`

plus two budget parameters:
- **spend threshold τ_B:** play no-op if the best score is below τ_B and decisions remain,
  which is how a rule can learn to wait;
- **fallback:** take the next legal sector instead of no-op.

Notes on the parameters:
- `b_s` is an optional fixed compass bias. It is what makes `base-s15` look good at B=1;
  include it only to measure it, since it will not transfer across regions.
- "Wind source" can only be the lagged observed record. The forcing is the
  perfect-forecast ablation, ADR-030 §1.
- In all, 4–6 continuous weights plus τ_B per budget.

**What it needs.**
- Cell-accounting fix (§4).
- An evaluator. Offline on the B=1 table and the B=2 tree. With simulation at B=4: about 98
  episodes per configuration, about 8 worker-min each.
- **Nested LOFO or grouped 5-fold CV** for every tuning run. §1.3–1.4 show that unnested
  numbers are optimistic by 25–125 ha.

**Headroom.**
- Ceiling: the observation-predictable part of the exhaustive gap. Hindsight lower bounds
  on that gap are 266, 382 and 396 ha above `advancing_front` [B §2h].
- Realistic [interpretation, medium-low]: 0–50 ha at B=1, and probably under 50 at B=2/4.
  - The coarse-feature selector found nothing.
  - The only fit-free candidate, a fixed NW bias, gives −16 ha with a CI of ±75 ha
    [new, TRAIN §8]. Its in-sample 35 ha version comes from PPO trained on those fires.
  - Prediction is capped by weather: the lagged wind matches the driving sector in 40% of
    decisions [B §2d].

**Can 20 VALIDATION fires detect it?** Only at B=1, and only if the cross-validated gain is
≥ 30–35 ha. Not at B=2 or B=4 (§1.5).

**CPU.**
- B=1 and B=2: CPU minutes on the tables, once they exist.
- B=4: grid of 24 configurations ≈ 2,350 episodes ≈ 3 worker-h ≈ 45–60 min. CMA-ES with
  about 200 evaluations ≈ 19,600 episodes ≈ 26 worker-h ≈ 6.5 h, × folds if nested. Use the
  grid.

**Risks.**
- Overfitting to a few large fires (shown in §1.4).
- Exploiting the line-cell credit.
- Exploiting simulator artefacts: the `last_write` episodes [C §1.3].
- A compass bias that does not transfer.
- A tuned rule that is, in effect, a linear policy. That is fine, but it should be called
  that.

**Budget question.** Compare θ_B (tuned per budget) against θ_2 (tuned at B=2 and reused),
both scored by nested CV on TRAIN and once on VALIDATION. This mirrors ADR-026's
"fine-tuned − frozen base". The matched control is θ_2 re-tuned with the same number of
evaluations; for a grid it is identical.
- **Fair stand-in?** Yes, and arguably a cleaner one: it asks whether the best rule depends
  on B, without confounding that with network optimisation noise.
- **Conditions:**
  - The family must contain budget-dependent parameters (τ_B, or weights that depend on the
    remaining budget). Otherwise the answer is trivially "no".
  - It answers "does the optimal *rule* change with B", which is a property of the MDP. It
    does not answer "does gradient fine-tuning of a *network* recover that change". Report
    it as the former.

### 3.2 Selector: a learned or fitted rule picks the heuristic or sector per fire or per decision

**What it looks like here.** A classifier maps the decision-k observation to one of
{adv, downwind, no-op, fixed sector 0–7} and is trained on the table by cross-entropy on the
hindsight-best label, or by direct cost-sensitive loss on realised hectares. Per decision
rather than per fire is free at B=1, since there is one line.

**Facts (§1.1–1.3).**
- A per-fire selector over {adv, downwind} can capture at most 18–26% of the hindsight gap.
- A selector over sectors can capture up to about 80% or more.
- The buildable two-way selector does no better than `advancing_front` out of sample.

**What it needs.**
- The B=1 table with observations. Then B's step 2, the supervised probe, which is the same
  test: pooled observations against a full-resolution variant, grouped CV.

**Headroom.** Unknown and decisive. If the probe recovers ≥ 25% of the B=1 hindsight gap
(≈ 65 ha of 266) out of fold, the direction is alive. If it recovers ≈ 0, as the stump did,
the honest result is that **in this simulator, with this observation, the right line is not
predictable, so no heuristic, tuned heuristic or RL policy can beat simple rules by a
detectable margin.** That is a publishable finding in its own right.

**Detectability, CPU and risks.**
- Detectability as in §3.1.
- CPU: minutes once the table exists.
- Risk: label noise. Many fires have several near-equal sectors. Use cost-sensitive loss,
  not argmax labels.

**Budget question.** At B=1 only. A budget-conditioned selector at B=2 needs the B=2 tree.

### 3.3 Behaviour cloning of the best heuristic, then PPO fine-tuning

**What it looks like here.**
- Clone the teacher into the existing 64×64 MaskablePPO network with masked cross-entropy.
  `scripts/bc_warm_start.py` does this for the CA and would need a SimFire port.
- Then run the ADR-026 design unchanged: a base fine-tune at B=2 and three per-budget
  fine-tunes, 10 seeds.

**Teacher choice.** It must be chosen on TRAIN.
- `advancing_front` is the locked TRAIN comparator (ADR-032; lock file
  `feds-simfire-budget-validation-lock-adr030-v1.json`).
- ADR-032 reports `downwind` as descriptively best on VALIDATION. Choosing it **because of
  that** would leak VALIDATION into the design.
- If `downwind` is preferred, justify it on TRAIN: it is ahead at B=4 (−308 against −290),
  behind at B=2.

**What it needs.**
- BC data: the heuristic is a deterministic function of the observation, so data come from
  the table or from about 300 rollouts (≈ 25 min).
- A SimFire port of the BC script.
- The cell-accounting fix.
- Ideally a no-op-relative reward. With the raw reward, the critic noise that collapsed
  stage 2 [B §2a] will pull the fine-tuned policy off the teacher.

**Headroom and evidence.**
- Literature: Murray beat its demonstrator by at most 1.6–1.7 pp of burned area; Hammond
  needed demonstrations at all [A §4.1].
- Project history: BC+PPO **tied** `direct_flank` in the CA (ADR-028 addendum,
  `DECISION_RECORDS.md:805-836`). Historical; ADR-029 voids the numbers, but the pattern is
  what the literature shows.
- Expected [interpretation, medium]: a tie with the teacher, ± a few tens of ha.

**Detectability.** Not at B=2/4. At B=1 only if it gains ≥ 30 ha over the teacher, which
nothing so far suggests.

**CPU.**
- About one stage-2 run: ≈ 24–28 h on 4 low-priority workers.
- Plus a TRAIN benchmark of the 40 new policies (≈ 15,700 episodes ≈ 20 worker-h ≈ 5 h) and
  a VALIDATION benchmark (≈ 45 min).
- **The same question can be answered first in the tabular B=1 MDP in minutes.**

**Risks.**
- PPO drifting off a good teacher.
- Seed-to-seed collapse again.
- The most expensive option per bit of information.

**Budget question.** This is the **most faithful continuation of the original question**.
- The stage-2 null is hard to interpret because 7 of 10 bases collapsed to one direction
  [B §2b]. A "fine-tuned − base" contrast between degenerate policies says little.
- A BC-initialised base is a non-degenerate starting point. "Does fine-tuning for B
  help?" becomes meaningful.
- It still has the power problem at B=2/4.

### 3.4 Residual RL / override the heuristic only when confident

**What it looks like here.** The action space is discrete with 4 decisions. "Residual" can
only mean "default to the heuristic's action, override with another sector when a learned
score clears a margin". That is a selector (§3.2) with a default and a confidence
threshold, or §3.3 with a KL penalty to the teacher.

**Reading [interpretation, high].** It is not a separate family here. Score it as the
selector with an abstain option on the B=1 table. The abstain threshold is one more
parameter tuned by nested CV. It is attractive for reporting ("overrides `advancing_front`
on 12% of decisions and wins X ha there"). It adds no new headroom. Same cost as §3.2
offline, or §3.3 if trained by PPO.

### 3.5 Search and planning with the simulator (lookahead, model-predictive control, MCTS with a heuristic rollout)

**What it looks like here.** At each decision, for each legal action, simulate the rest of
the episode with a heuristic rollout (`advancing_front` with fallback). Play the best first
action, then re-plan at the next decision. The tree is tiny, so full-width depth-4
enumeration at B=1 (33 leaves) is cheaper and better than MCTS. MCTS only matters at B=4.

**Legitimacy. Two very different things share this name.**
1. **Rollouts with the true forcing ("clairvoyant").** They see the upcoming weather, which
   ADR-030 §1 forbids policies to see.
   - The result equals the exhaustive per-fire optimum: B's upper bound.
   - **It is a bound, not a policy.** It must never be compared with heuristics as if it
     were one.
2. **Rollouts with persistence weather.** Every future segment uses the last *observed*
   record, which is information the policy already has. This is legitimate model-predictive
   control (MPC) under the ADR-030 information rule.
   - Two privileges remain, and both must be labelled:
     - it uses the full-resolution fire state, which the policy observation pools to 2.9 km
       blocks;
     - its dynamics model is exactly the evaluation simulator.
   - In real operations an incident team would plan with an imperfect model. Here **model
     error is only weather error.**
   - At WAF 0.10 the midflame wind is weak (median ≈ 0.35 m/s [B §2d]), so spread is driven
     mostly by fuel and slope, which the model knows exactly. Persistence MPC may therefore
     come close to the clairvoyant bound [interpretation, medium-low, untested].
   - That would be a correct statement about this simulator and a weak statement about real
     suppression (D's verdict).

**What it needs.**
- A way to run SimFire with substituted forcing. A small wrapper change is needed, because
  the env reads forcing from the weather file (`feds_simfire_env.py:446`, `apply_forcing`).
- Prefix replay from reset, since state copy is unverified [B §3].
- The cell-accounting fix.
- A planning ADR stating the information set.

**Headroom.**
- Persistence MPC lies somewhere between the heuristics and the bound (266/382/396 ha
  above `advancing_front`, lower bounds).
- It is the only family whose expected gain might exceed the n=20 MDE at B=2 and B=4.
- Bertsimas, Diao and Petersen all report planning beating heuristics [A §2, rows 10–12].

**CPU.**
- Per episode, with replay: Σ over decisions of ≤ 9 actions × (k replayed + 4 − k rolled
  out) segments ≈ 144 segments ≈ 36 episode-equivalents ≈ 140–200 worker-s, less for fires
  that die.
- TRAIN, 98 fires × 3 budgets ≈ 12–16 worker-h ≈ 3–4 h.
- VALIDATION, 20 × 3 ≈ 2.5 worker-h ≈ 40 min.
- At B=1, open-loop enumeration of 33 sequences under persistence costs the same as the B=1
  exhaustive run.

**Risks.**
- It answers "can a model-based decision aid beat rules *in this simulator*", which is
  close to circular.
- It is not RL. It must not be presented as a learned policy.
- It inherits the line-cell credit if the fix is not made first.

**Budget question.** Budget awareness is built in: it plans with the remaining budget. The
budget contrast is "MPC told B" against "MPC assuming B=2". That is a clean and cheap test of
whether budget-specific decisions matter. It is arguably the best available answer to the
original question's *substance*. It is not an answer to its *method* (fine-tuning a learned
policy).

### 3.6 For contrast: improved pure RL (no-op-relative reward, more training)

**What it looks like here.**
- Reward = no-op new cells − agent new cells per segment. The no-op per segment is cached:
  98 × 4 numbers, already in the gate trajectory.
- Plus the line charge, plus 5–10× more updates.

**Evidence.**
- SimHarness, on SimFire, used this reward [A §3.3].
- The between-fire spread is about 50× the action effect under the raw reward [B §2a].
- The policies do not even fit TRAIN [B §2b].

**Test first, for free.** Tabular RL or a contextual bandit on the B=1 table, raw against
counterfactual reward, in-sample and leave-fires-out (B's step 3). It shows whether the
stage-2 failure was optimisation and noise or unpredictability.

**Headroom.** The same ceiling as §3.2: the observation-predictable gap. Pure RL can at best
learn what the selector learns, with more variance. The literature says it rarely beats a
good heuristic without a heuristic start [A §4.1].

**CPU.** 10× base training is about 80,640 decisions per seed, ≈ 11–13 h per seed on 4
workers. Ten seeds take about 5 days, before fine-tunes. **Not justified until the tabular
test shows learnable headroom.**

**Risks.** The same collapse, at greater cost.

**Budget question.** Unchanged from ADR-026, with a better-trained base.

## 4. Prerequisites, in order

1. **Line-cell charge in SimFire** (§1.7). A line cell inside the paired no-op footprint counts
   as damage, as the CA already does under the user's decision
   (`DECISION_RECORDS.md:1018-1032`).
   - It needs the no-op cumulative burn mask per fire: 98 masks, from one no-op run each, or
     from the exhaustive run's no-op leaf.
   - It needs the line cells per episode, which the env reports in its info, though the
     benchmark does not store them.
   - It changes the ADR-032 numbers, so it needs an ADR, and stage-2 numbers must be
     re-scored under both rules.
2. **Exhaustive B=1 TRAIN table** (B's step 1). For every fire it stores:
   - the 33 outcomes;
   - the observation at each no-op-path decision;
   - the line cells per leaf and the no-op mask, so both accountings can be scored;
   - whether each sector was legal.

   It is the evaluator for families 1–4 and the bound for 5–6. TRAIN only, read-only use of
   the env. It needs a new script but no change to locked code.
3. **Heuristic fallback to the next-best legal sector.** It affects at most about 10 of
   about 1,000 decisions (§1.6). Add it as **new** heuristic variants
   (`advancing_front_fb`, …). Do not edit the locked `advancing_front`, which is the ADR-032
   comparator.
4. **Random baseline over K seeds** instead of one repeated draw [C §1.7]. This matters
   only if the random line stays a reference.
5. **Evaluation protocol before tuning.**
   - Nested grouped CV on TRAIN is primary for development.
   - VALIDATION is used once per pre-registered contrast. It has already been used twice:
     the no-op gate score (ADR-031) and the policy benchmark (ADR-032). Any new VALIDATION
     comparison is a **further use** and must be pre-registered in an ADR naming the
     policies, the contrasts and the tests.
6. **Horizon and tail decision** (see §5). Tuning optimises the reward as defined. If a
   post-horizon tail is to be added, decide it first, or the tuning has to be repeated.

## 5. Interaction with longer episodes and synthetic fires

- **Tuned heuristics do not need more episodes.**
  - A rule with 5–7 parameters tuned on 98 fires is limited by the number of distinct fires
    and their heavy tail, not by episode count.
  - Synthetic fires would help only if they add *independent diversity that transfers*,
    which B argues is unlikely [B §4].
  - More fires would help most at evaluation: power (§1.5). Rolling real start states from
    the same TRAIN fires [B §1] add states, not independent fires.
- **Longer episodes change what is optimal.**
  - Late lines are undervalued by the 48 h cut [B §2g], so a tail would favour waiting and
    indirect lines. That is exactly the budget-relevant timing parameter τ_B.
  - So **if a tail is going to be adopted, adopt it before tuning**, or the tuned timing is
    tuned to an artefact.
  - B's step 5 (B=1 exhaustive with a 48 h tail, ≈ 80 min on 7 workers, ≈ 2–2.5 h on 4)
    tests this. It belongs in the same run family as prerequisite 2.
- **Longer horizons make the tables more expensive**, roughly × segments. At 96 h, B=1 stays
  cheap. B=2 exhaustive at 96 h becomes about 25–30 h on 4 workers. At that point beam search
  or MPC replaces enumeration.
- **The synthetic CA is the opposite case.** Its heuristics are rich (units, travel,
  standoff), it has many decisions, and it is fast at about 40 decisions/s. There, tuning
  heuristic parameters, such as standoff or flank choice, by CMA-ES is cheap and well
  matched. If stage 3 runs, "tuned `direct_flank`" is a natural comparator.
  - Caveat: its heuristics read full-resolution state [C §2.6], so "matched information"
    needs restating first.

## 6. Verdict, ranked recommendation and plan

### Verdict

- **Does the direction make sense?** Yes, as a reframing. "Optimise structure, don't learn
  from scratch" is what the evidence supports [A §5c], and this MDP is small enough to
  optimise offline.
- **Is it likely to produce a policy that beats `advancing_front` detectably on 20
  VALIDATION fires?** Probably not at B=2/4 (confidence about 75%). Possibly at B=1, if
  observations predict the sector much better than the coarse features tested here. I give
  that about 20% (revised down from a first estimate of 30%, because the only fit-free gain on
  TRAIN, fixed NW, is −16 ha with a ±75 ha interval).
- **What carries the project is the measurement:**
  1. the exact ceiling;
  2. how much of it is predictable;
  3. whether the best rule depends on B.

  Whichever way they come out, they answer the owner's question and the original budget
  question with a clear, defensible result.

What would change this verdict:
- the out-of-fold supervised probe recovers ≥ 25% of the B=1 hindsight gap (direction
  becomes promising);
- persistence MPC gets close to the clairvoyant bound (then the "smart" part is the model,
  not learning);
- the line charge removes most of the remaining gains (then the result is "lines barely
  matter in this simulator").

### Ranked recommendation

1. **Exhaustive B=1 table + offline scoring of families 1–4 + tabular RL, all with nested
   CV.** Cheapest, decisive, and it reuses one run for everything.
2. **Persistence-weather MPC** (family 5, legitimate version), with the clairvoyant bound
   reported separately. It is the only candidate with a plausible detectable gain at B=2/4,
   and its budget contrast is clean. Label it a planner in the same simulator.
3. **Tuned scoring heuristic** (family 1) at B=2 and B=4, on the B=2 tree or a 24-point grid.
   Only if step 1 shows predictable headroom. Run the per-budget contrast as the
   budget-adaptation stand-in.
4. **BC + PPO fine-tune** (family 3) with a TRAIN-chosen teacher and a no-op-relative
   reward. Only if steps 1 and 3 show headroom that a network could plausibly capture. It is
   the most faithful continuation of the original question and the most expensive.
5. **Pure RL with a better reward and more training** (family 6). Only if the tabular test
   shows that the stage-2 failure was optimisation, not unpredictability.
- **Residual RL** (family 4) is not a separate item. Score it as a selector with an abstain
  option inside step 1.

### Ordered plan with costs

Costs: 4 low-priority workers, 4.7 worker-s per episode; ×1.5–2 under other load.

| # | Step | Data | Cost | Go / no-go |
|---:|---|---|---|---|
| 0 | Done: this document and B. Selector oracle, LOFO selector, power, fallback, footprint bound | TRAIN JSON | done | — |
| 1 | **Line-charge accounting** in a scoring helper (no env change yet). Store line cells and the no-op mask in step 2's output | TRAIN | ≈ ½ day of code | — |
| 2 | **B=1 exhaustive TRAIN table**: 33 outcomes per fire, no-op-path observations, legality, line cells, no-op mask. 20-fire check against the benchmark first (exact match required) | TRAIN | ≈ 15 min pilot + 50–75 min full | Bound ≈ best fixed sector → stop tuning; report "no adaptive headroom" |
| 3 | **Offline on the table, nested grouped CV:** best fixed sector; tuned scoring rule (family 1, B=1); selector / probe with pooled and full-resolution features (2, 4); tabular RL raw vs counterfactual (6); BC fit to adv (3); each scored with and without the line charge | TRAIN table | CPU minutes to ≈1 h | Out-of-fold gain ≥ 30 ha and ≥ 25% of the gap → continue; ≈ 0 → write up "not predictable from the observation" |
| 4 | **B=1 + 48 h tail exhaustive** (B's step 5), same script, exploratory label. Optional but before any timing conclusion | TRAIN | ≈ 2–2.5 h | Tail changes the best k or sector on many fires → decide the horizon before step 5 |
| 5 | **Persistence MPC and clairvoyant bound** at B=1/2/4, plus "MPC assuming B=2" | TRAIN | wrapper code ≈ 1 day; ≈ 3–4 h compute | MPC − adv out of sample on TRAIN vs MDE |
| 6 | **B=2 tree** (52 decision nodes with observations per fire). Start with 30 fires; all 98 only if step 3 passed | TRAIN | ≈ 3.5–5 h (30 fires) / 11–16 h (98) | Tuned rule at B=2 cross-validated |
| 7 | B=4 grid (24 configurations) for the tuned rule, nested CV | TRAIN | ≈ 3 worker-h per pass ≈ 45–60 min; × folds | — |
| 8 | **Pre-registered further VALIDATION use** (after ADR-031 and ADR-032): at most a few locked policies (e.g. tuned rule θ_B, θ_2, MPC, adv, downwind) at B=1/2/4; primary test at B=1 | VALIDATION | ≈ 10–45 min | One shot |
| 9 | Only if justified: BC + PPO (≈ 1–1.5 days training + ≈ 5 h TRAIN benchmark) or pure RL with counterfactual reward (≈ 5 days for 10 seeds at 10×) | TRAIN, then another pre-registered VALIDATION use | days | — |

### Which steps need a new ADR before running

- **No ADR (TRAIN-only, exploratory, no locked code or metric changed):** steps 0, 2 and 3,
  plus 6 and 7 while TRAIN-only. They use the frozen record and the env read-only. Their
  results must be labelled exploratory and must not feed back into any locked comparator
  without an ADR.
  - Under ADR-030's "no gate rule may change after a result", a step-2 script that adds
    a new output does not change anything locked.
- **Needs an ADR (or ADR-030/032 addendum) before running:**
  - **Step 1 as the official metric.** It changes the SimFire damage rule and therefore the
    ADR-032 numbers. Its offline computation inside steps 2–3 is fine as an exploratory
    second score.
  - **Step 4.** A horizon or tail change. Exploratory is acceptable, but any adoption needs an
    ADR with a new gate/freeze [B §5].
  - **Step 5.** A new policy class with privileged inputs (full-resolution state, the
    simulator as model). The ADR must fix the information set (persistence weather, no
    forcing) and label the clairvoyant run as a bound.
  - **Step 8.** A further use of VALIDATION, after ADR-031 and ADR-032. It must pre-register the policies, contrasts,
    budgets, primary test (B=1), tests and corrections, and be committed before running.
  - **Step 9.** A new training protocol (BC teacher chosen on TRAIN, reward change). It
    supersedes ADR-026's design.
  - **Changing the locked heuristics** (fallback). Prefer new variants. Editing
    `advancing_front` itself needs an ADR, since it is the ADR-032 comparator.

## Confidence summary

| Claim | Confidence |
|---|---|
| Hindsight headroom is mostly per-fire sector choice | high (§1.1, direct computation) |
| Naive tuning on 98 fires overfits by 25–125 ha | high (§1.3–1.4, LOFO) |
| 20 VALIDATION fires cannot detect gains below about 120 ha at B=2/4 | medium-high (two independent SD estimates) |
| The line credit is a must-fix before optimising | high in principle; size only bounded (≤ 22–26% of gains) |
| The fallback fix is negligible | medium-high (no-op-path approximation) |
| No tuned rule has an out-of-sample gain on TRAIN yet (fixed NW −16 [−95, +58]; 35 ha only in-sample) | high (§1.4, §8) |
| A tuned heuristic beats adv detectably at B=1 | about 20% |
| Persistence MPC beats adv detectably at B=2/4 | about 35–45% (untested; hinges on weak wind) |
| "Tune per budget" is a fair stand-in for budget fine-tuning | medium-high, with the conditions in §3.1 |

## Key references

- Code:
  - `src/wildfire_rl/feds_heuristics.py:41-43` (no fallback), `:50-75` (rules);
  - `src/wildfire_rl/feds_simfire_env.py:157-182` (front-edge placement), `:197-212` (mask),
    `:418-470` (step, raw reward, info with line cells);
  - `scripts/benchmark_feds_policies.py:112-156` (episode record: no line cells, no
    observations);
  - `scripts/train_feds_budget_adaptation.py:55-130` (PPO settings);
  - `scripts/bc_warm_start.py:1-10` (CA-only BC);
  - `src/wildfire_rl/synthetic_heuristics.py:1-5`.
- Decisions, in `docs/specs/DECISION_RECORDS.md`:
  - ADR-030 §1 (information), §4 (statistics) `:944-1016`;
  - line-charge addendum `:1018-1032`;
  - autonomy addendum `:1138-1158`;
  - ADR-032 `:1267`;
  - CA BC+PPO tie (historical) `:790-836`.
- Data: the TRAIN benchmark, weather (TRAIN rows) and TRAIN gate files listed at the top.
- Outputs: `E_heuristics_analysis.py` and `E_heuristics_analysis.out` in [analysis/](analysis/README.md).
