---
type: Research Analysis
title: "Da li kratke epizode koče učenje?"
description: "Odakle granica od 48 h, koji uzroci slabog učenja su vjerovatniji i šta testirati prvo."
status: stable
generated: {by: "process:claude-code", at: "2026-11-11T16:00:00Z"}
sources:
  - resource: /src/wildfire_rl/feds_simfire_env.py
  - resource: /reports/real-fire-data/fpa-feds-candidate-frame-train-v1.json
  - resource: /docs/specs/DECISION_RECORDS.md
---
# B: Are short (48 h) episodes why the agent does not learn?

Analysis of the hypothesis: "Our training fires were tracked for only 48 h, so episodes are
short and the agent has no time to learn. Synthetic fires fitted to real spread regularities,
running as long as needed, are the key to a smart agent that beats the heuristics."

Date: 2026-11-11. Repository state: worktree `.worktrees/task-026-stage-2` (commit 61f0ebf).
Read-only; nothing in the repository was edited. No training or simulation was run.
`obs_vs_forcing.py` imports repository modules. It wrote no new bytecode: `__pycache__` holds
only the existing cpython-39 files from 2026-11-10.

## Evidence labels

- **[valid]**: quoted from the valid ADR-031/ADR-032 records or their committed reports.
- **[new, TRAIN]**: my own analysis of existing TRAIN-only files, without new simulation.
  Scripts and outputs are in [analysis/](analysis/README.md):
  - `train_bench_analysis.py` and `.out`: the TRAIN benchmark `.local/bench/adr030-train.json`;
  - `extra.py` and `.out`: front size and per-fire sector range;
  - `obs_vs_forcing.py` and `.out`: observed wind against the forcing wind.

  The weather file was filtered to `split == "train"`. VALIDATION files were not opened, and
  TEST was not touched.
- **[historical]**: ADR-022 to ADR-028. ADR-029 voids their numbers, so they are used only
  qualitatively here.
- **[interpretation]**: my reading. A confidence level is given where it matters.

## Short answer

**The premise is wrong.**
- The 48 h limit does not come from FEDS. Every TRAIN fire is tracked by FEDS for at least
  108 h with no gaps (median about 11 days).
- FEDS is not in the learning loop anyway. The agent learns from SimFire's simulated burn;
  FEDS only scores the no-op gate.

**The conclusion is unlikely (confidence about 75–80%).** Episode length is not the binding
constraint. The evidence points instead to:
1. a very weak learning signal: the action effect is about 1/50 of the between-fire return
   spread, and the reward is raw;
2. very little optimisation: 72 PPO updates, and the policies did not even fit the TRAIN
   fires;
3. low leverage of a single 1.26 km line against fronts that are mostly much larger;
4. an open question about whether the existing hindsight headroom can be predicted from what
   the policy observes.

Longer episodes would not add training data per CPU hour. They would make credit assignment
harder. The project's own long-horizon synthetic CA (historical) did not produce a policy
that beats a heuristic either.

The hypothesis does have one valid core. A 48 h cut-off with no tail undervalues lines, above
all late ones, because their effect after +48 h is never counted. A fixed post-horizon tail on
the same real starts fixes that more cheaply and more safely than synthetic fires.

---

## 1. Where the 48 h / 4-decision limit comes from

### Facts

**ADR origin.** It is a data-coverage criterion that was turned into an episode design.
- ADR-016 (`docs/specs/DECISION_RECORDS.md:265-297`) requires at least two consecutive 12 h
  FEDS states.
- ADR-018 (`:328-358`) accepts the cohort because "all 119 have five 12 h states from start
  to +48 h". 48 h was the window over which the no-op simulator could be scored against FEDS
  perimeters.
- ADR-019 (`:362-394`) samples gridMET "on four 12 h segments over 48 h".
- ADR-021 (`:423-446`) and ADR-025 (`:561-563`, "Budgets per 48h episode … the episode
  always runs four decisions") inherit it.
- ADR-030 §3 and ADR-031 define the gate and the freeze on the four timepoints +12/+24/+36/+48 h.

**Code.**
- `src/wildfire_rl/feds_simfire_env.py:225`: the docstring says "A 48h episode with four
  shared 12h decisions".
- `feds_simfire_env.py:283`: `self.horizon_steps = 4`.
- `feds_simfire_env.py:447`: `self.simulation.run("12h")`.
- `feds_simfire_env.py:456`: `terminated = self.decision_index >= self.horizon_steps`.
- `src/wildfire_rl/feds_simfire_setup.py:250-251`: a gridMET record must have exactly four
  segments.
- `src/wildfire_rl/gridmet_weather.py:138-143`: `for index in range(4)` over 12 h segments.
- `scripts/sample_gridmet_episode_weather.py:218`: `"horizon_hours": 48`.
- `configs/simfire_feds_base.yml:15`: `runtime: 48h`.

**FEDS tracking is not the limit.** [new, TRAIN]
- Source: `reports/real-fire-data/fpa-feds-candidate-frame-train-v1.json`, keys
  `cases[].feds.selected.event_longest_12h_run`, `event_observed_states` and
  `last_observed_state`, restricted to the 98 manifest TRAIN cases.
- All 98 are tracked continuously from the episode start, with no gaps.
- Run length: minimum 10 states (108 h), median 23 states (about 11 days), p90 78, maximum
  206.
- Tracked for ≥144 h: 77/98. Tracked for ≥168 h: 69/98. Tracked for ≥240 h: 57/98.
- Example: Plateau is tracked for 63 states (31 days), but its episode stops at 48 h.

**FEDS is not in the learning loop.**
- The reward is `-new_burned_cells/100` from SimFire (`feds_simfire_env.py:451-452`).
- The manifest `information_boundary` marks future FEDS geometries as `evaluation_only`.
- FEDS length therefore limits only how far the simulator's realism can be checked, not what
  the agent can experience.

**Weather is available.** The full annual gridMET NetCDFs for 2018, 2019 and 2023 (`th`,
`vs`, `fm100`) are local in `.local/gridmet/`. A longer horizon only needs the sampler to
emit more segments, plus the matching loader change.

**Simulator behaviour at 48 h on the frozen record.** [new, TRAIN] Source:
`.worktrees/task-026-stage-1/.local/gate/adr030/waf-0.1-ros-1.json`, field
`trajectory[].fire_active_after_segment` and the cell counts.
- Without a line, SimFire is still burning after each segment in 67, 60, 56 and 56 of 98
  fires. So 31 fires go out within 12 h, and 42 are out by 36 h.
- Mean new cells per 12 h segment are 450, 562, 612 and 665, so growth is accelerating. For
  the 56 fires still burning, the last segment adds about 1,164 cells (about 3,770 ha).
- At +48 h the largest fire covers 21,912 cells, which is 33% of the 65,536-cell map. No
  edge contact occurs at WAF 0.10.
- At WAF 0.20, 14 cases already touch the edge within 48 h [valid, ADR-031 table].
- The frozen setting overgrows real fires: 1.8× on growing fires and about 8,976 ha per fire
  on the 16 non-growing fires by +48 h [valid, ADR-031].

### Interpretation

**48 h is a design choice.** It came from the gate (comparing the no-op run with FEDS out to
+48 h) and spread into the environment, the weather sampler and the freeze.

**SimFire episodes from the same starts could run longer:**
- Weather: no obstacle.
- FEDS: it still provides at least 108 h of reference for every TRAIN fire.
- Map edge: a real risk. Growth is accelerating, and the biggest fire already covers a third
  of the 46 km map. My expectation is that edge contacts would appear at 72–96 h (medium
  confidence, untested). A 96 h no-op screen of the 98 TRAIN fires would settle this in a
  few minutes; see §5.
- Overgrowth: the main obstacle. The record free-burns fires that in reality were contained.
  Every extra hour makes the simulated fire less like the real one, so "longer real-start
  episodes" turn into synthetic fires in all but name.

**Procedure.** ADR-030 ties the gate to four timepoints, and nothing may change after a result
has been seen. A longer horizon therefore needs a new ADR, a new or extended gate and a new
freeze. It is not a parameter tweak.

**A second real-data alternative.** Because FEDS keeps tracking, each TRAIN fire offers many
later start states. Counting the 48 h windows inside each fire's continuous run gives about
3,264 possible start states instead of 98.
- This is a hypothesis, not a checked fact. Each start needs a FEDS active front at that `t`,
  a re-centred map (possibly a new LANDFIRE fetch) and new weather.
- The effective number of independent fires stays 98.
- It still adds real diversity of states much more cheaply than a synthetic generator.

## 2. Is episode length the binding constraint? Candidate causes

The table ranks the causes by how strongly the evidence supports each one.

| Candidate cause | Evidence | Reading |
|---|---|---|
| **Weak learning signal (reward scale and variance)** | See (a) | **Likely binding** (medium-high) |
| **Too little optimisation** | See (b) | **Likely binding** (high) |
| **Low leverage of the action** | See (c) | **Binding on the ceiling** (high) |
| **Information: can the best line be predicted?** | See (d) | **Open; the key unknown** |
| Fixed compass sectors | See (e) | Minor |
| 16×16 pooled observation | See (f) | Probably minor |
| 4 decisions per episode / 48 h | See (g) | **Not binding for learning**; matters for valuation |
| Heuristics near the optimum? | See (h) | **No** in hindsight; unknown for a realisable policy |

### (a) Reward scale and variance

**Facts.** [new, TRAIN]
- No-op adds a mean of 2,289 cells per fire (median 1,117, SD 3,374, maximum 17,709).
- As a return (reward = −cells/100) that is −22.9 ± 33.7 per episode.
- The mean |effect| of `advancing_front` against no-op at B=2 is 0.70 reward units.
- The between-fire spread is therefore about 50 times the action effect.
- The reward is raw: no counterfactual no-op baseline, and no `VecNormalize`. Only
  `VecMonitor` is used (`scripts/train_feds_budget_adaptation.py:91`). SB3 normalises
  advantages per minibatch, but the critic still has to predict a heavy-tailed fire size from
  a pooled observation.

**Reading.** The policy gradient is dominated by which fire was drawn, not by which line was
chosen. SimFire is deterministic per fire, so all within-fire variation comes from the action.
Subtracting a cached per-fire no-op return (98 numbers) would remove almost all of the noise.
The synthetic CA already uses that counterfactual form; this environment does not.

### (b) Too little optimisation

**Facts.**
- Settings (`train_feds_budget_adaptation.py:61-62, 101-110`): 8,064 decisions = 7 envs ×
  16 steps × 72 rollouts. That is 72 policy updates of 4 epochs with batch 56, an MLP 64×64,
  and entropy 0.01.
- On average about 20 episodes per fire.
- ADR-032: 7/10 base policies open with the same action in every VALIDATION episode [valid].
- On TRAIN the same collapse is visible [new, TRAIN]. At B=2, seven bases open with one
  action on all 98 fires (s12, s13, s14, s16, s18, s19, s20). s11 splits 49/49 between
  no-op and action 6. s15 (71/27) and s17 (88/10) use two actions.
- **On the TRAIN fires themselves**, base PPO (−175.1 ha at B=2) is behind the random legal
  line (−205.6), `downwind` (−187.7) and `advancing_front` (−194.4) [valid, ADR-032].

**Reading.** The policies have not even fitted the 98 deterministic TRAIN fires. Whatever the
first observation looks like, they collapse to one sector. That is underfitting or a
low-signal optimisation failure, not a lack of "time inside the episode".

**Episode length does not change the data budget.** Cost scales with simulated 12 h segments,
not with episodes. A 96 h episode costs twice as much and gives half as many episodes per CPU
hour. More training on the same 48 h episodes is directly possible: 10× costs about 7 h per
seed at the measured 3 decisions/s.

### (c) Low leverage of the action

**Facts.**
- One budget unit is one 7-cell line (about 1.26 km), placed 2 cells (360 m) beyond the
  leading front cell of the chosen sector (`feds_simfire_env.py:157-182`, ADR-025).
- The initial active front has median 68 cells (p10 16, p90 206); 69% of fires have more
  than 28 front cells [new, TRAIN, gate report `initial_feds_state`].
- Effect on burned area:
  - every policy family burns 0.3–8% less than no-op [valid, ADR-032];
  - line episodes identical to no-op: 29–47% depending on policy and budget, about 45% at
    B=1 [new, TRAIN];
  - line episodes worse than no-op: 2–8% (the `last_write` artefact) [new, TRAIN];
  - fires where none of the 44 policies changes anything: 17–19/98, 11 of which have zero
    no-op growth [new, TRAIN].

**Reading.** A single line usually covers a tenth of the front or less, and the fire goes
round it. The ceiling on any policy is low relative to fire size. A longer horizon would make
the fire bigger relative to a fixed line, which makes this worse, not better.

### (d) Information: can the best line be predicted?

**Facts.** [new, TRAIN]
- At B=1, the benchmark has a line at decision 0 in 6 of the 8 sectors for the median fire
  (≥3 sectors for all 98).
- Per fire, the best observed sector beats the average observed sector by 288 ha on average.
- The spread between the best and worst sector has median 118 ha and mean 440 ha.
- The sector choice therefore matters per fire, and a lot.
- The policy, however, observes the previous day's wind (ADR-030 §1). Its downwind sector
  matches the sector of the wind actually driving the segment in only 40% of the 392 TRAIN
  decisions. The median direction error is 28°, and 15% of decisions are off by more than 90°.
- The wind is also weak in the frozen record: median 10 m wind 3.5 m/s gives about 0.35 m/s
  midflame at WAF 0.10.

**Reading.** The headroom depends on things the policy cannot see well: the future weather,
and the fuel just ahead of the front at line scale. Whether it can be predicted is the
central unknown. A supervised probe can test it cheaply (§5, step 2).

### (e) Compass sectors fixed to the map

**Facts.** [new, TRAIN; observational]
- B=1 single-line episodes, by the angle between the line sector and the actual segment
  wind-to:

  | Angle to wind-to | Mean effect |
  |---|---:|
  | 0–45° | −153 ha |
  | 45–90° | −96 ha |
  | 90–135° | −87 ha |
  | 135–180° | −88 ha |

- This is confounded: different policies chose different sectors on different fires.
- `downwind`, which maps the wind to a sector, does no better than the random line
  [valid, ADR-032].

**Reading.** A wind-relative action frame would make the "downwind" rule one action and could
speed up learning. With weak wind and stale wind information, though, it does not unlock much.

### (f) 16×16 pooled observation

**Fact.** Each block is 16×16 cells (2.9 km). The line itself is placed at full resolution by
the environment; the policy only chooses the sector.

**Reading.** Probably not binding by itself. Pooling does hide which sector has fuel or a
fuel break right in front of the line, so it may contribute to (d). The supervised probe will
show it: if full-resolution features predict the best sector and pooled ones do not, pooling
is binding.

### (g) Four decisions per episode and the 48 h horizon

**Facts.** [new, TRAIN]
- Line actions by decision index: 11,613 at decision 0, then 5,214, 2,269 and 2,147.
- For 31/98 fires the no-op burns out within 12 h, so later decisions do nothing there.

**Reading.**
- With γ=1 and 4 steps, credit assignment is easy; short episodes favour learning.
- The 48 h cut does bias valuation: a line at decision 3 is credited with only 12 h of
  effect, and blocked growth after +48 h counts for nothing. That undervalues late and
  indirect lines. It is a reward-design issue that a fixed tail fixes (continue the
  simulation with no decisions, as the CA does with its 12 h tail).
- [historical] The CA (ADR-028) ran 12–48 decisions per episode and hit exactly the opposite
  problem: a credit-assignment failure, with line built too far from the fire to matter.

### (h) Are the heuristics already near the best achievable?

**Facts.** [new, TRAIN] For each fire and budget, take the best outcome among the 44
evaluated policies. This is oracle selection with hindsight, among only 7–10 distinct action
sequences per fire.

| Budget | Best of 44 | Per-fire best of `advancing_front` and `downwind` | Best single heuristic | Random line |
|---|---:|---:|---:|---:|
| B=1 | −378 ha | −159 | −113 | −107 |
| B=2 | −577 ha | −278 | −194 | −206 |
| B=4 | −686 ha | −392 | −308 | −248 |

- At B=2 the best of 44 is about 7.8% of the no-op mean (7,416 ha).
- The top 10 fires carry 36–46% of that gain.

**Reading.**
- In hindsight there is real headroom: at least about 3× the heuristics' gain. It is a lower
  bound on the true clairvoyant optimum.
- In absolute terms it stays small next to fire size, and it is concentrated in a few fires.
- What a policy can realise from its observation is unknown; see (d).

## 3. Headroom: what could ANY policy do in this MDP?

### Why an exhaustive search gives an exact upper bound

- The environment is deterministic for a given fire (seed 0; the benchmark checks B=0
  determinism).
- For each fire, the best open-loop action sequence therefore equals the best closed-loop
  outcome for that fire.
- The mean over fires of these per-fire optima is a **clairvoyant upper bound for every
  policy**, PPO included.
- Two further numbers come from the same table:
  - the best **fixed** sequence over all fires (the non-adaptive optimum);
  - the "fixed direction" policies, already known.
- The gap between the clairvoyant bound and the non-adaptive optimum is the most that being
  "smart" can buy in this MDP. Report clairvoyant headroom and headroom reachable from the
  observation separately.

### Size of the search

Legal sequences per fire (unused budget allowed; masks only shrink these):

| Budget | Legal sequences |
|---|---:|
| B=1 | 1 + 4·8 = 33 |
| B=2 | 1 + 32 + 6·64 = 417 |
| B=4 | 9⁴ = 6,561 |

### Cost on this machine (8 cores, 7 workers)

One 48 h episode costs about 4–6 worker-seconds at WAF 0.10:
- the TRAIN gate ran 98 no-op episodes in 79 s (documented command with 7 workers), about
  5.6 worker-s each;
- the TRAIN benchmark ran 17,248 episodes in 247 min, about 87 min on 7 workers plus 160 min
  on 3, about 3.8 worker-s each.

| Run | Episodes | Worker-hours | Wall time on 7 workers |
|---|---:|---:|---:|
| B=1 exhaustive, 98 fires | 3,234 | ≈4.5 | **≈40 min** |
| B=1 exhaustive, 20-fire pilot | 660 | ≈0.9 | **≈8 min** |
| B=2 exhaustive, 20 fires | 8,340 | ≈12 | ≈1.7 h |
| B=2 exhaustive, 98 fires | 40,866 | ≈57 | ≈8 h |
| B=4 exhaustive, 98 fires | 642,978 | ≈900 | ≈5 days (not sensible) |
| B=4 greedy (9 options × 4 decisions), 98 fires | ≈3,500 | ≈5 | ≈45 min |
| B=4 beam search, width 4, 98 fires | ≈14,000 | ≈20 | ≈3 h |

Only the exhaustive rows give the exact clairvoyant bound. The greedy and beam rows, like the
best of 44, give feasible sequences, so they are **lower bounds on the ceiling**: the headroom
is at least that large.

Savings:
- Prefix sharing would save about 3.6× (7,380 segments per fire instead of 26,244), but only
  if a SimFire state can be deep-copied. That is unverified.
- Pruning helps: once the fire is dead every continuation equals no-op, and 31/98 fires die
  within 12 h.

### Proposed pilot (not run)

1. Write a small TRAIN-only script that enumerates the 33 B=1 sequences per fire through
   `FedsSimFireEnv`. It records the outcome **and the observation at each decision along the
   no-op prefix**.
2. Run it on 20 TRAIN fires (about 8 min), check against the benchmark's B=1 episodes (the
   same sequences must match exactly), then run all 98 (about 40 min).
3. Report:
   - the clairvoyant bound;
   - the best fixed sequence;
   - the gap to `advancing_front` and `downwind`;
   - how concentrated the gap is.

The best of 44 already gives −378 ha at B=1, so the bound is at least that.

**Useful side effect.** At B=1 every sequence is "no-op until decision k, then one line, then
nothing legal". The whole B=1 MDP therefore fits in a table: 98 × 4 observations plus 98 × 33
outcomes. PPO, or a contextual bandit, can be trained on that table for millions of steps in
minutes with no further simulation. That directly tests whether more training would help;
see §5.

## 4. Synthetic fires fitted to real-fire statistics, with longer horizons

### What "spread regularities" could concretely mean, and where to fit them

**From FEDS (12 h, 375 m), per fire and step:**
- the distribution of area growth ratios;
- head advance and flank advance;
- length-to-breadth ratio;
- the direction of growth against gridMET wind and LANDFIRE slope and fuel;
- the probability that growth stalls in a step (16/98 TRAIN fires do not grow 10% in 48 h,
  ADR-031);
- tracked duration (median about 11 days here).

**From FPA-FOD:**
- final size and discovery date;
- in the full database, containment dates, which would give a duration and containment
  hazard. The local candidate-frame manifest
  (`data/manifests/fpa-feds-candidate-frame-v1.json`) has only discovery date and time and
  the reported final area. A containment field would need a new extract.

**Fitting method.** Simulation-based calibration (approximate Bayesian computation or
summary-statistic matching) of a stochastic CA's rate of spread, wind and slope response and
a stop hazard to these summaries. Fit on TRAIN only, by fire-level cross-validation.

### What the existing synthetic CA already does (ADR-028, `docs/research/SYNTHETIC_CA_ENV.md`)

| Aspect | What it does | Fitted to real-fire statistics? |
|---|---|---|
| Spread | Fuel-dependent ignition probability; Rothermel-shaped wind term; Alexandridis slope term; moisture damping; diurnal cycle (lines 48–63) | No: the contact constant k is calibrated to the Anderson (1982) head-rate table; φ_ref, moisture of extinction and the diurnal factor are assumptions (lines 58–59) |
| Landscapes | Procedural (lines 138–149); 0.3–1.2 domain randomisation | No: "own priors, not a histogram of real cases" (lines 29–30) |
| Horizon and decisions | 12/24/48 h horizon plus a 12 h tail, hourly decisions | — |
| Units | Finite units with travel and line-building rates | — |
| Reward | Counterfactual against no-op on common random numbers | — |
| Map | 128×128 cells (23 km), **smaller** than SimFire's 46 km | — |

So it already is "longer, controllable synthetic fires with many decisions", but it is not
fitted to FEDS statistics.

### What went wrong there [historical; numbers voided by ADR-029]

- PPO from scratch got about 186× more training than the SimFire base (1.5M steps against
  8,064) and still lost to the scripted `direct_flank`. The diagnosis was a credit-assignment
  failure: the policy built line far from the fire.
- Behaviour cloning plus PPO only tied with its teacher.
- The CA had bugs: build progress reset when the action changed, and line cells inside the
  no-op footprint were counted as saved.
- Its "calibration gap" (median IoU 0.27–0.30 at 48 h) used the faulty weather and an IoU
  that included the initial area.
- At 48 h plus the tail, the no-op fire reached the 23 km crop edge in 34/119 real cases.

**Reading.** The CA is the closest existing test of "synthetic fires with more decisions per
episode and much more training". It did not produce a policy that beats a heuristic. It is
not a clean test of "longer episodes": its horizon was at most 48 h plus a 12 h tail.

### Sim-to-real risk (the main problem)

1. **Suppression is baked into the data.**
   - FEDS fires are historically suppressed fires. Their stall rate, growth distribution and
     duration already include firefighting.
   - A generator fitted to them has a no-op that is already partly suppressed. The agent's
     lines then act on top of an unknown amount of suppression already present.
   - Without suppression data the free-burn counterfactual cannot be identified: FLE joins
     0/40 TRAIN cases (ADR-016).
   - Fitting a free-burn simulator to suppressed fires gives what ADR-031 found: about 9,000 ha
     of overgrowth per contained fire at 48 h. Running it longer makes this worse.
2. **The thing the policy exploits is not in the data.** What drives a policy is how a
   1.26 km line changes spread at 180 m scale. FEDS at 375 m and 12 h cannot see that.
   Fitted marginal statistics would make no-op fires look realistic while the
   line-interaction model, the part that decides the policy, stays uncalibrated.
3. **Map edges and horizon.** Longer free-burning fires need bigger maps (SimFire 46 km; CA
   23 km already clipped in about 29% of cases), or the edge truncates the damage the reward
   counts.
4. **Evaluation.** The real-start benchmark would remain the only check. A policy trained on
   fitted synthetic fires could still be judged only inside a simulator.

**What is worth fitting.** A stall or containment hazard per 12 h step, from FEDS growth and
FPA-FOD durations, used as an *evaluation stratum or no-op realism check*. It should not
silently reduce the no-op fire that the reward credits the agent against.

## 5. Verdict and test order

### Verdict

**Not the key** (confidence about 75–80%).
- The premise (FEDS tracked for only 48 h) is false: every TRAIN fire is tracked for at least
  108 h.
- FEDS is not what the agent learns from.
- Episode length does not limit how much the agent can train.
- The evidence points to:
  - a signal-to-noise problem in a raw reward;
  - far too little optimisation (the policies do not fit their own TRAIN fires);
  - a low action ceiling (about 8% of no-op even in hindsight at B=2);
  - an untested question of whether the hindsight headroom can be predicted.

Synthetic fires would help only in one case: if, after these are fixed, a learner fits TRAIN
well but fails to generalise across fires. Even then, the need is more *diverse* starts,
which rolling real starts may give more cheaply, not *longer* fires.

The 20% where I could be wrong:
- Late and indirect line value may be large once a post-horizon tail is counted.
- With a tail plus a counterfactual reward, longer horizons might change which strategy is
  optimal.

The tail experiment in step 5 below tests this.

### Order of tests (cheapest first; TRAIN only; each tells candidate causes apart)

| Step | What | Cost | Tells apart |
|---:|---|---|---|
| 0 | Existing-report analyses (this document) | done | Premise false; SNR, collapse and ceiling numbers |
| 1 | **B=1 exhaustive** on 20, then 98 TRAIN fires: clairvoyant bound, best fixed sequence, observations at each node | about 8 + 40 min wall | Is there headroom for adaptivity at all? If bound ≈ best fixed sequence, stop tuning RL and redesign the actions |
| 2 | **Supervised probe** on the step-1 table: predict the best (decision, sector) from the decision-k observation (pooled, and a full-resolution variant) with leave-one-fire-out CV; score the realised hectares | minutes of CPU | Is the headroom **predictable** from what the policy sees? Is pooling binding? |
| 3 | **Tabular-MDP RL** on the step-1 table: (i) raw reward vs (ii) counterfactual reward (cached per-fire no-op subtracted); 10⁵–10⁶ steps. Report two numbers: **in-sample fit** on all 98 fires, and **leave-fires-out** (train on about 78 TRAIN fires, score the other 20; repeat over folds) | minutes to about 1 h of CPU, no simulation | In-sample: training amount and signal-to-noise (if (ii) approaches the bound and PPO-8k did not, the failure was optimisation and noise, not episode length). Leave-fires-out: whether the headroom is learnable across fires. There are only 98 distinct decision-0 observations, so in-sample fit alone shows memorisation |
| 4 | **96 h no-op screen** of 98 TRAIN fires on the frozen parameters (needs weather sampler and loader to emit 8 segments; exploratory label) | code change plus about 3–6 min of compute | Edge contacts, overgrowth growth, how many fires are still active beyond 48 h |
| 5 | **Tail test.** Repeat B=1 exhaustive with 4 decisions plus a 48 h no-decision tail | about 80 min wall | Does the horizon change line values or the ranking of the optimal sector or time? This is the honest test of the user's hypothesis |
| 6 | Only if 1–3 show predictable headroom and 3 shows good TRAIN fit but poor cross-fire generalisation: add start diversity. First rolling real starts (audit fireline availability per `t`), then a generator fitted to FEDS statistics with a separate stop hazard | days | Diversity as the binding constraint |
| 7 | Only after 1–5: a new ADR (horizon, reward baseline, action frame), a new gate and freeze, then PPO with 10 seeds | hours to days | Confirmatory |

Steps 4, 5 and 7 change the environment or the horizon. ADR-030 says no gate or rule may
change after a result, so these need a new ADR and an explicit "exploratory" label before
anything in them is used for selection. Steps 1–3 only read the current environment.
TEST 2024 stays closed throughout.

## Key file references

- `src/wildfire_rl/feds_simfire_env.py:157-182` (front-edge placement, 2-cell standoff),
  `:225` (48 h docstring), `:283-284` (`horizon_steps = 4`, `block_count = 16`), `:447`
  (12 h run), `:451-452` (raw reward), `:456` (termination).
- `src/wildfire_rl/feds_simfire_setup.py:250-251` (exactly four gridMET segments).
- `src/wildfire_rl/gridmet_weather.py:138-143` (four 12 h segments).
- `scripts/sample_gridmet_episode_weather.py:218` (`horizon_hours: 48`).
- `configs/simfire_feds_base.yml:15` (`runtime: 48h`).
- `scripts/train_feds_budget_adaptation.py:61-62, 91, 101-110` (PPO settings, no reward
  normalisation).
- `src/wildfire_rl/feds_heuristics.py:36-75` (heuristics use the same pooled observation and
  wind).
- `docs/specs/DECISION_RECORDS.md`:
  - ADR-016 `:265`, ADR-018 `:328`, ADR-019 `:362`, ADR-025 `:545`;
  - ADR-028 and addenda `:672-898` (historical);
  - ADR-030 `:944`, ADR-031 `:1159`, ADR-032 `:1267`.
- `docs/research/SYNTHETIC_CA_ENV.md:29-30, 48-63, 138-149, 153-160`.
- Data:
  - `reports/real-fire-data/fpa-feds-candidate-frame-train-v1.json` (tracking length);
  - `.worktrees/task-026-stage-1/.local/gate/adr030/waf-0.1-ros-1.json` (no-op activity,
    front size);
  - `.worktrees/task-026-stage-2/.local/bench/adr030-train.json` (TRAIN benchmark).
