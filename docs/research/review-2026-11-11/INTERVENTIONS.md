---
type: Reference
title: "Šta politika smije raditi u svakom simulatoru"
description: "Intervencije, opservacija, heuristike, nasumična politika i budžet u SimFire-u, sintetičkom CA i pilotu."
status: stable
generated: {by: "process:claude-code", at: "2026-11-11T16:00:00Z"}
sources:
  - resource: /src/wildfire_rl/feds_simfire_env.py
  - resource: /src/wildfire_rl/feds_heuristics.py
  - resource: /src/wildfire_rl/synthetic_ca.py
  - resource: /src/wildfire_rl/synthetic_env.py
---
# What can a policy do to fight the fire? Interventions in the three simulators

Code checked at worktree `task-026-stage-2` (HEAD 61f0ebf). Paths are relative to that
worktree unless stated otherwise. SimFire 2.0.1 (pinned commit `04905b19…`) was read in
`overnight-steps-5-8/.local/simfire-venv/lib/python3.9/site-packages/simfire/`, written
below as `simfire/…`. Nothing in the repository was edited. Labels used:

- **[code]**: read directly in code.
- **[doc]**: read in an ADR or research document.
- **[measured]**: from a read-only probe I ran, which took several minutes (§1.9).
- **[inferred]**: my own reasoning from the code, not stated anywhere.

## Short answer

**There are no aircraft, air tankers, helicopters, water or retardant drops, engines,
backfires or burnouts in any of the three simulators.**

- **SimFire on real fire starts (the main simulator, ADR-031/032).** The policy has one
  tool. Every 12 hours it may order one straight hand-crew fireline of about 1.26 km in one of
  eight compass directions, or do nothing.
  - The line appears instantly. It is placed by the environment, not by the policy, two cells
    beyond the fire's leading edge in that direction.
  - In practice it is never breached. A probe found 0 of 2,179 line cells ignited on 98 TRAIN
    fires with one heuristic; extending this to PPO and VALIDATION is [inferred]. Fire gets
    past only by going around the line's ends.
  - At B=4 the `advancing_front` heuristic placed a line in only 175 of the 294 later
    decisions: the fire had died, or its preferred sector was illegal.
  - No unit moves, travels, builds over time or can be endangered.
- **Synthetic CA (ADR-028, stage 3, not rerun).** This is the only simulator with physical
  units: 2–4 units, either 20-person hand crews or dozers.
  - They arrive over the first 3 hours, 2–4 km away, walk at 2.5–3 km/h and build line
    cell by cell at fuel-dependent NWCG rates.
  - They retreat automatically when fire comes within 360 m, and they can be overrun or lost.
  - Lines never burn, but spotting can jump them. Units cannot touch burning cells.
- **Old pilot CA (pipeline test only).** The policy "treats" one abstract cell per tick.
  - A treated cell can no longer burn. Treating a burning cell puts it out at once.
  - This is the only simulator with direct suppression of burning cells, and it has no
    physical meaning or units.

---

## 1. SimFire on real fire starts (`FedsSimFireEnv`)

The stage-2 setup is the ADR-031 freeze record
`configs/frozen/feds-simfire-growth-gate-freeze-v1.json`:

- WAF 0.10, ROS multiplier 1.0, 5-minute internal step, 90-minute active-cell lifetime;
- `fireline_attenuation="per_minute"`, `spread_aggregation="last_write"`;
- line placement `front_edge` (run record and lock
  `reports/real-fire-data/feds-simfire-budget-{run-record,validation-lock}-adr030-v1.json`) [code/doc].

### 1.1 What SimFire supports natively, and what the project uses

- **Three control-line types, nothing else that acts on fire.**
  - `BurnStatus` has FIRELINE=3, SCRATCHLINE=4 and WETLINE=5 (`simfire/enums.py:52-69`).
  - Their rate-of-spread attenuation is 980, 490 and 245 ft/min (`simfire/enums.py:73-85`).
  - Each has a manager (`simfire/game/managers/mitigation.py:83,122,158`).
  - `update_mitigation` accepts only these three and skips anything else
    (`simfire/sim/simulation.py:449-478`) [code].
- **Wet line is a rate class, not a water resource.** It is a weaker line class (245 ft/min).
  SimFire has no water volume, drop or aircraft behind it [code].
- **Resource tables exist but are dead data.**
  - `enums.py` has these lookup tables: `HandLineRate` (chains/person/h by fuel,
    `enums.py:256-271`), `DozerType`/`DozerLineRates` (`:274-341`), `AirTankerType`/`AirTankerRates`
    (`:343-361`) and `HelicopterTypes`/`HelicopterRates` (`:363-373`).
  - Unit converters exist too (`simfire/utils/units.py:103-127`).
  - A grep of the whole package finds **no use of any of them** outside `enums.py`.
  - In pinned SimFire 2.0.1, aircraft, helicopters and dozers are therefore table entries only, with no simulated behaviour [code].
- **The `Agent` sprite is display only.** `update_agent_positions` exists
  (`simfire/sim/simulation.py:480-497`), but it only records positions for rendering and has no
  effect on spread. The project never calls it [code].
- **The project uses only FIRELINE.** The single call is `update_mitigation([(x, y, 3) …])`
  (`src/wildfire_rl/feds_simfire_env.py:438-440`). No other code in `src/` or `scripts/` uses
  scratch line or wet line [code].
  - The wrapper's attenuation function handles all three types
    (`feds_simfire_setup.py:482-486`), and the observation's line channel counts values
    3, 4 and 5 (`feds_simfire_env.py:370`). Only 3 ever occurs.

### 1.2 The intervention: one fireline per 12h decision

**Physical meaning (ADR-025) [doc].**
- One budget unit is one 20-person hand-crew shift building one straight fireline segment.
  This is stated in `feds_simfire_env.py:53` (`LINE_LENGTH_M = 1260.0`) and ADR-025.
- ADR-025 cites NWCG production of about 2–15 chains/h, or 0.3–2.4 km per 8h shift, and places
  1.26 km inside that range.
- It is a modelling convention, "not a field-validated line-construction model"
  (`feds_simfire_env.py:228-231`).

**Geometry [code, checked with `python -c`].**
- **Cell size.** The grid is 256×256 cells of 180 m (46 km square) (`feds_simfire_setup.py:53,277`).
- **Axis sectors (E, S, W, N).** The line is 7 cells, 1,260 m (`feds_simfire_env.py:63-79,97-117`).
- **Diagonal sectors.** The line is 5 diagonal cells plus 4 corner-filler cells, 9 cells in all,
  spanning 1,273 m. The fillers make the line 4-connected, so SimFire's 8-connected spread
  cannot slip between diagonal cells (`feds_simfire_env.py:97-117`; SimFire spreads diagonally,
  `configs/simfire_feds_base.yml:71`, `simfire/game/managers/fire.py:211-221`).
- **Orientation.** The line always runs perpendicular to the chosen sector direction.
- **Sector to compass.** The raster is north-up (`feds_simfire_inputs.py:72`, negative y
  resolution). Columns increase east and rows increase south. Sectors 0–7 are therefore
  **E, SE, S, SW, W, NW, N, NE**, and action = sector + 1 (`feds_simfire_env.py:40-49`) [code].
  - ADR-032's "action 7" (seeds 12, 14, 20 always open with it) is a line on the **north**
    side of the fire. Action 6 is NW, action 4 is SW and action 3 is S.
- **Wind convention checked.** SimFire treats `U_dir` as the downwind bearing clockwise from
  north, with image y pointing down (`simfire/world/rothermel.py:99-105`). This matches the
  heuristics' `heading_vector = (sin, −cos)` in (column, row) (`feds_heuristics.py:36-38`) and
  the from→to conversion (`gridmet_weather.py:47-49`). The downwind heuristic does aim
  downwind [code].

**Where the line goes (`front_edge`, used for all stage-2 training and benchmarks) [code].**
- The environment, not the policy, picks the exact cells (`feds_simfire_env.py:157-182`):
  1. "Front" means SimFire's currently burning cells (`fire_map == 1`, `:326,:433`). At
     reset these are the FEDS active-front cells.
  2. The anchor is the burning cell furthest along the sector direction. Ties go to the first
     cell in row-major order, i.e. the northernmost, then westernmost (`np.argmax`, `:179`).
  3. The line centre is 2 cell steps beyond the anchor in the sector direction (`:180-181`):
     360 m on axis sectors, 2 × 254.6 m = 509 m on diagonals [inferred from the arithmetic].
  4. Only cells that are currently UNBURNED (state 0) receive line (`_placeable`, `:120-123`).
     Cells off the grid, burning, burned or already line are dropped, so the line can come out
     clipped or gapped.
- **Distance from the fire.** Only the line's centre is guaranteed to stand off. Its ends can
  lie next to burning cells elsewhere on the front [inferred].
- **Non-burnable cells.** Placement does not check fuel. A line can be laid on water, rock or
  urban cells (FBFM 91–99), where it changes nothing [code: `_placeable` checks only state 0].
- **Old centroid placement (not used in stage 2).** The line centre sits 6 cells (1.08 km) from
  the front centroid in the sector direction (`feds_simfire_env.py:134-154`).

**Timing [code].**
- The line is written into the fire map instantly, before the next 12h of spread is
  simulated (`feds_simfire_env.py:432-447`).
- There is no build time, no travel and no crew. A line is permanent and is never maintained,
  widened or removed.

### 1.3 When the line holds and when fire crosses it

**Mechanism [code].**
- SimFire lets fire enter line cells: UNBURNED and the three line types are all valid spread
  targets (`simfire/game/managers/fire.py:179-201`).
- Every cell accumulates a "burn amount" from the Rothermel rate of spread (ROS) reaching it.
  It ignites when that amount exceeds the cell width, 590.55 ft = 180 m
  (`fire.py:568`, `feds_simfire_setup.py:406-408`).
- On line cells the project's wrapper subtracts 980 ft/min × 5 min each update and floors the
  burn amount at zero (`_per_minute_line_attenuation`, `feds_simfire_setup.py:458-488`,
  installed at `:536-538`). ADR-030 §2 and its addendum record this choice.
- **Result.** A fireline cell ignites only if the effective spread rate reaching it exceeds
  **980 ft/min ≈ 299 m/min ≈ 18 km/h** long enough to bank one cell width. The time since
  placement does not matter.
- **Pinned SimFire behaves differently.** It subtracts a fixed 980 per update and has no floor
  (`fire.py:236-284`). At a 5-minute step that would hold only below 196 ft/min, but idle lines
  bank negative burn and become near-absolute barriers. The project does not use this mode.

**In practice the line never burns [measured on TRAIN with one heuristic; inferred for PPO and VALIDATION].**
- I ran the stage-2 setup on all 98 TRAIN fires: `advancing_front` heuristic, B=4, `front_edge`.
  - It laid 2,179 line cells in 98 episodes, and **0 of them ever ignited**.
  - The highest spread rate reaching any line cell was 58.5 ft/min (about 6% of the threshold).
  - The highest rate anywhere on the map was 207 ft/min.
- Fire therefore gets past a line only around its ends, through clipped gaps, or by burning
  in from a direction the line does not cover [inferred from the probe and the geometry].
- The 1.26 km line is short compared with the fires. ADR-031 reports a mean of 2,193 added
  cells (about 7,100 ha) by +48h on growing TRAIN fires.
- **The "line burns more than no-op" episodes.** ADR-032 found 48 of 2,379 such episodes on
  VALIDATION. They are not line failures. They come from `last_write` sprite ordering in
  pinned SimFire: a line changes the order of the burning sprites, so a different neighbour's
  spread rate is written for other cells. This is documented in ADR-032 and
  `scripts/analyze_budget_adaptation.py:302-348` [doc].

**Line cells count as saved, with no charge [code + inferred].**
- Damage is `cumulative_burned`, which counts states 1 and 2 only
  (`feds_simfire_env.py:215-221,444-452`; benchmark `scripts/benchmark_feds_policies.py:143`).
- A line cell (state 3) that never burns is therefore not damage, even when the no-op fire
  would have burned it.
- The synthetic CA charges such cells as agent damage (TASK-024, ADR-030 addendum). SimFire
  has **no equivalent charge**: a grep of `analyze_budget_adaptation.py` finds no line charge.
- **Size of the credit.** A line on cells the no-op fire would burn is credited with up to
  7 × 3.24 = 22.7 ha (axis) or 9 × 3.24 = 29.2 ha (diagonal) per line, for its own footprint
  alone. That is up to about 117 ha at B=4.
- **Comparison with ADR-032.** Base PPO minus random line is −5.5 ha at B=1, and the random
  line's own delta against no-op is −19.3, −115.7 and −234.3 ha at B=1, 2 and 4. ADR-032 does
  not separate how much of these deltas is footprint credit [inferred]. An upper bound is
  computed in [TUNED_HEURISTICS §1.7](TUNED_HEURISTICS.md) (about 26 ha per line, 21–26% of heuristic gains).

### 1.4 What the action mask forbids [code]

- The action space is `Discrete(9)`: action 0 is no-op and actions 1–8 are sectors 0–7
  (`feds_simfire_env.py:312`).
- `build_action_mask` (`feds_simfire_env.py:197-212`) works as follows.
  - No-op is always legal.
  - With no remaining budget, every line action is illegal.
  - Otherwise a sector is legal if its placement rule yields **at least one** placeable
    (UNBURNED, on-grid) cell.
- **Consequences.**
  - A line clipped to a single cell is legal and still costs a full unit (`:437-442`).
  - A sector whose cells are all already line or already burned is illegal, which happens
    when the front has not moved since the last line there [inferred].
  - Once nothing is burning, every line action is illegal (`:147-149,176-178`).
- **Illegal actions sent anyway.** They become no-op with a −0.01 reward penalty
  (`:427-429,453-454`). MaskablePPO and all the heuristics respect the mask, so in the
  benchmark `invalid_actions` stays 0 [inferred from the code paths].

### 1.5 What is NOT modelled in SimFire [code unless marked]

- **Absent resources.** Aircraft, air tankers, helicopters, water, retardant, foam, engines and
  dozers do not exist; at most they appear as dead tables (§1.1). Scratch line and wet line
  exist in SimFire but are unused.
- **Absent tactics.**
  - There are no backfires, burnouts, firing operations or mop-up.
  - Burning cells cannot be suppressed: line goes on UNBURNED cells only.
- **Absent crew modelling.**
  - There is no travel, staging, arrival time or build-over-time; the line is instant (ADR-025).
  - There is no crew position, safety, entrapment, fatigue or shift limit.
- **Absent fire processes.**
  - There is no spotting: SimFire has no ember code; a grep finds "spot" only in a CFD wind
    comment.
  - There is no diurnal or night effect. Wind speed, direction and fuel moisture are one
    uniform value per 12h segment over the whole grid (`feds_simfire_setup.py:451-455`).
- **Absent controls.**
  - A line cannot be longer or shorter than 1.26 km, curved, anchored to a road or placed at a
    chosen distance.
  - Only 8 directions exist (ADR-025 lists 16 sectors and crew-hours as future work, TASK-020).
- **Absent decision options.** There is no line-holding or failure model beyond the 980 ft/min
  threshold, which does not bind in practice (§1.3). There is no cost beyond the budget count
  and no protection of assets: the reward weights every cell equally.

### 1.6 What every policy sees [code]

**The observation** (`feds_simfire_env.py:313-318,365-387`) has four parts.
- **`grid`, 4 × 16 × 16.** Each block averages 16 × 16 cells (2.88 km × 2.88 km) of the
  46 km map. The channels are:
  1. cumulative burned share, including the initial FEDS scar and front;
  2. currently burning share;
  3. line share;
  4. fuel code / 13, clipped to [0, 1]. Non-burnable codes 91–99 therefore all read 1.0, the
     same as FBFM 13 [inferred from the clip].
- **`budget`.** Initial and remaining budget, each divided by 4 (`max_budget=4` in training
  and benchmark).
- **`weather`, 4 values.** Wind-speed proxy / 3000 ft/min, sin and cos of the downwind
  bearing, and fm100 / 0.3.
  - The values come from the **latest daily gridMET record strictly before the upcoming
    segment's day**. At decision 0 that is the pre-start day (ADR-030 §1 and addenda;
    `feds_simfire_setup.py:331-354`).
  - The forcing that actually drives the next 12h is never shown. The perfect-forecast mode
    is an ablation only.
  - At WAF 0.10 the speed value is small: 5 m/s reads about 0.03 [inferred from
    `gridmet_weather.py:68-71`].
- **`time`.** Decision index / 4.
- **Not in the observation.** Elevation or slope (SimFire's spread uses slope), the
  full-resolution map, future FEDS perimeters and the forcing in use.

**Who sees what.**
- **Heuristics.** They receive exactly the PPO observation dict and the same mask
  (`feds_heuristics.py:3-9`; benchmark `:137`). They see nothing the agent does not.
- **PPO.** It additionally uses `budget` and `time`, which no heuristic reads. Its
  observation is therefore a superset of what the heuristics use.
- **Both.** Both choose only a direction. The environment then uses the full-resolution
  burning map to place the cells (§1.2), which neither of them sees.

### 1.7 How each policy decides [code]

Common to all: one integer action per 12h decision, taken from `(observation, mask)`.

- **`noop`** (`feds_heuristics.py:46-47`). It always returns 0. It never spends budget.
- **`downwind`** (`:50-56`).
  1. Take sin and cos of the observed (lagged) downwind bearing, `weather[1:3]`. Wind speed
     is ignored.
  2. Convert to a (column, row) vector `(sin, −cos)`.
  3. Choose the sector whose unit direction has the highest cosine with it
     (`sector_for_vector`, `:24-33`). Ties go to the lower sector index because of the strict `>`.
  4. If that sector is legal, play it. **Otherwise play no-op.** `_first_legal` (`:41-43`)
     does not fall back to the next-best sector.
  - A zero vector would mean no-op, but sin and cos cannot both be 0 [inferred].
- **`advancing_front`** (`:59-75`).
  1. On the 16×16 pooled grids, compute the burning-share centroid minus the burned-share
     centroid, in block units.
  2. If either channel is empty, or the vector is shorter than 1e-6, use `downwind` instead.
  3. Otherwise take the closest sector and apply the same `_first_legal` rule.
  - The fallback does not matter once the fire is out, because every line is then masked.
- **`random_legal`** (`:78-86`).
  - It chooses uniformly among the legal line actions 1–8, and plays no-op only when no line
    is legal. It therefore spends budget at every chance.
  - **Seeding.** It uses `np.random.default_rng(seed)`. The benchmark passes `--seed`
    (default 0; stage 2 used 0, per the lock file), and a new policy object is built for each
    scenario (`benchmark_feds_policies.py:117,130`).
  - So the stream restarts in every scenario and continues across that scenario's budgets
    in the order 0, 1, 2, 4. B=0 draws nothing, because the legal set is empty.
  - **The same directions repeat across fires.** Whenever all 8 sectors are legal, every
    scenario gets the same draws. ADR-032 reports this: action 7 in all 20 VALIDATION fires
    at B=1. The "random" baseline is one fixed set of directions, not an average over random
    placements.
- **PPO (MaskablePPO)** (`scripts/train_feds_budget_adaptation.py:91-125`).
  - **Training.** It is trained from scratch with a 64×64 MLP and γ=1 on TRAIN fires. Base
    models use budget {2}; fine-tunes use {1}, {4} and {2} (ADR-026/032). Scenario and budget
    are drawn uniformly at each reset (`feds_simfire_env.py:400-409`). Actions are sampled
    stochastically under the mask.
  - **Benchmark.** It acts deterministically under the mask (`benchmark_feds_policies.py:48-50`).
  - **What it learned.** ADR-032 reports that 7 of 10 base policies open with the same fixed
    direction on every VALIDATION fire, and that three fine-tunes never place a line [doc].
- **Heuristic budget use.** All three line heuristics place a line at every decision where
  their chosen sector is legal and budget remains (ADR-025: "spends a unit at the first legal
  opportunity"). None of them saves budget for later.

### 1.8 Budget and episode rules [code]

- **Episode.** It is 48h: 4 decisions of 12h (`horizon_steps = 4`, `:283`). Each decision
  runs `simulation.run("12h")`, i.e. 144 SimFire updates of 5 minutes (`:446-447`).
- **At most one line per decision.** So B=4 *allows* a line at every decision.
  - In the probe (§1.9), `advancing_front` at B=4 placed a line in only 175 of the 294 later
    decisions. Extra budget buys less than it seems.
- **Budgets.** The benchmark uses B ∈ {0, 1, 2, 4} per episode (ADR-025/026).
- **Spending.**
  - One unit is spent only if at least one cell was actually placed (`:437-441`). A clipped
    line costs a full unit.
  - When the budget reaches 0, only no-op is legal. The episode still runs all 4 decisions
    (`:456`), and unspent budget is worth nothing.
- **Reward.** −(newly burned cells)/100 per decision, minus 0.01 for an invalid action (`:451-454`).
- **Fire going out.** If the fire dies early, SimFire stops and the remaining decisions are
  forced no-ops (`:445-447`).

### 1.9 The probe I ran (read-only)

- **Script.** `analysis/probe_lines.py` (run from the repository root with `PYTHONPATH=src`),
  run with the `overnight-steps-5-8/.local/simfire-venv` Python.
- **Run time.** Several minutes in the background, so longer than a short check. Nothing was
  written to the repository, and `.local/simfire-runs` stayed empty.
- **Setup.** The ADR-031 freeze record, TRAIN split, 98 fires, `advancing_front`, B=4,
  `front_edge`, seed 0.
- **Instrumentation.** I wrapped the fire manager's `_update_rate_of_spread` to record the
  peak per-minute spread rate reaching line cells and reaching any cell.
- **Results.**
  - All 98 episodes placed at least one line.
  - There were 175 nonzero actions in the 294 later decisions (decisions 1–3). The other 119
    later decisions were no-ops although budget remained.
    - The cause is either a dead fire, where every line is masked, or a preferred sector that
      was illegal, since `_first_legal` has no fallback.
    - I did not separate the two causes; [TUNED_HEURISTICS §1.6](TUNED_HEURISTICS.md) later
      estimates the missing fallback at no more than about 10 of about 1,000 decisions.
  - 2,179 line cells were placed and 2,179 were still unburned at the end.
  - The peak rate at a line cell was 58.5 ft/min, about 17× below the threshold. The peak rate
    anywhere was 207 ft/min.
- **Scope.** This covers one heuristic on TRAIN only. Extending "the line never burns" to PPO
  or VALIDATION is [inferred].

---

## 2. Synthetic cellular automaton (`SyntheticSuppressionEnv`, ADR-028)

ADR-029 marks its results invalid until the stage-3 rerun. This section describes the code,
not any results.

### 2.1 Units and what they physically are [code]

**Two unit types** (`src/wildfire_rl/synthetic_env.py:52,58-99`). No aerial, engine or water
resource exists.

| Unit | Travel | Line production (examples; full table in code) | Slope rule | Source (code comment `:76-83`, doc) |
|---|---|---|---|---|
| `hand_crew_20`, a 20-person Type II crew | 50 m/min (3.0 km/h off-trail, an assumption). One cell takes 3.6 min, a diagonal 5.1 min. Slowed by `exp(−2·Δz/d)` (`:529-532`) | FM1 18 ch/h (362 m/h, 30 min per cell); FM2/FM9 16; FM8 5; FM10 4 (134 min per cell); FM7 2 (268 min per cell); urban 91: 6 (assumption) | No limit | NWCG PMS 410-1 App. A p. A-30; travel from Sullivan et al. 2020 (5 km/h on trail; 3 km/h is an assumption) |
| `dozer`, Type II | 42 m/min (2.5 km/h, an assumption below a D6R's first gear). One cell takes 4.3 min | FM1/FM2 105 ch/h (2.1 km/h, 5 min per cell); FM4 47.5; FM8 87.5; FM10/FM13 15 (36 min per cell) | ×0.6 at 26–40% slope, ×0.3 at 41–45%; cells above 45% are impassable (`:66-73,368-369`) | PMS 410-1 p. A-34; the 45% limit is from the Baboon Fire 2020 report |

- **Rates are quantized** to the 2-minute substep [inferred].
- **Units per episode.**
  - **Training curriculum.** 2–4 units (`Curriculum.unit_counts`, `:144`). Each is a dozer
    with probability 0.4 (`:145,217-221`).
    - Phase A uses horizons of 12/24h with 2–3 units; phase B uses 12/24/48h with 2–4 units
      (`scripts/train_synthetic_ppo.py:33-34`).
  - **Maximum 4 slots** (`MAX_UNITS = 4`, `:41`), ordered dozers first, then hand crews, each
    by arrival time (`:224-226`).
  - **Real-case test.** A fixed protocol: dozer at 30 min, crew at 60, crew at 90, dozer at
    120 (`synthetic_real_cases.py:44-45`), over a 48h horizon (`:37`).
- **Arrival.**
  - In training, arrival times are uniform over 0–180 min (`:220`).
  - On arrival a unit appears at a staging cell (`:341-357`). The cell lies
    sqrt(burned cells/π) + U(11, 22) cells (2.0–4.0 km) from the burned centroid.
  - The staging cell must be passable, not burned and have no burning cell within 2 cells;
    otherwise the radius shrinks ×0.97, up to 200 tries.
- **Not in the CA.** There are no aircraft, helicopters, engines, water tenders, retardant or
  aerial resources of any kind [code: `UNIT_TYPES` has only these two entries].

### 2.2 Per-unit actions and how a line is built [code]

**Action space.** `MultiDiscrete([17] × 4)`: one action per unit slot per **60-minute**
decision (`:38,42,253`).
- **0, stay.** The unit stays put.
- **1–8, move.** The unit moves one cell in compass direction N, NE, E, SE, S, SW, W or NW
  (`OFFSETS`, `synthetic_ca.py:63`).
- **9–16, build line and advance in direction k.**
  - If the current cell is buildable (burnable, UNBURNED and not yet line, `:372-374`), the
    unit adds production metres. At 180 m the cell becomes line (`:514-523`).
  - On the next substep the cell is no longer buildable, so the unit moves one cell in
    direction k (`:524-535`).
  - Over an hour the unit lays a trail of line behind it [inferred from repeated substeps].

**Timing.** The chosen action is applied on every 2-minute substep for 30 substeps
(`:542-549`), unless retreat overrides it (§2.4).
- Progress is keyed to the cell being built or the move target. Changing the build direction
  in the same cell keeps the progress (`:491-495`).

**The mask** (`:384-394`).
- Stay is always legal, and inactive or lost units can only stay.
- Move k is legal if the target is on the grid and passable: not water, not burning, and for
  dozers at most 45% slope (`:360-370,376-382`). Burned ("black") cells are passable.
- Build k is legal if the current cell is buildable **or** move k is legal.
- There is no requirement to be near the fire.

**Placement limits.** Line can go only on burnable, unburned cells. It cannot go on burning or
burned cells, water, rock or agricultural land (`:372-374`).

### 2.3 When a CA line holds [code]

- **Line cells can never ignite.** `ignite` and the contact-spread candidate set both exclude
  `fire.line` (`synthetic_ca.py:214-216,299`).
- **No diagonal leaks.** A diagonal step between two orthogonally adjacent line cells is
  blocked (`synthetic_ca.py:293-297`).
- **Spotting can jump lines.**
  - Each burning shrub, timber or slash cell can throw an ember with per-substep probability
    `spot_rate·(U/U_ref)²` (`:309-324`).
  - The landing distance is 1 + Exponential(mean 3 cells), downwind, with angle noise of about
    0.35 rad.
  - The ember lands on any unburned, burnable, non-line cell, including cells beyond a line.
  - `spot_rate` is drawn from 0–4·10⁻⁴ in training (`synthetic_env.py:148`); real cases use
    the default 2·10⁻⁴ (`synthetic_ca.py:189`).
- **Line credit.** A line cell inside the paired no-op fire's footprint is charged as agent
  damage, in both training and evaluation (`synthetic_env.py:333-336,558-566`; TASK-024 and
  the ADR-030 addendum).

### 2.4 Retreat, overrun and safety penalties [code]

- **Automatic retreat.** `auto_retreat=True` by default (`:240,500-507`).
  - **Trigger.** A burning cell within 2 cells (Chebyshev, 360 m) and the unit not on a refuge
    cell. A refuge is burned, non-burnable or line (`:402-410,438-439`).
  - **Escape route.** A breadth-first search over passable cells finds the nearest safe cell:
    a refuge, or at least 5 cells (900 m) from fire (`:430-465`).
  - **Speed.** The unit escapes up to 2 cells per 2-minute substep, an assumption: "partly by
    vehicle".
  - **Effect on the order.** The ordered action is skipped on that substep, and progress resets.
- **Overrun.** This is checked after each fire substep (`:552-555,467-489`).
  - If the unit's cell catches fire and a passable neighbour exists, the unit is displaced
    there. Refuge cells are preferred, then the cell farthest from fire. This is a **close
    call**.
  - If no neighbour is passable, the unit is **lost** and deactivated.
- **Penalties.** −1.0 per lost unit and −0.1 per close call (`:44-45,604`). They are part of
  the training reward. For acceptance, safety is a non-inferiority condition against the
  comparator heuristic (ADR-030 §5).
- **Not modelled.**
  - Escape-route time and safety-zone size: the 4× flame-height rule is below the 180 m
    resolution (`docs/research/SYNTHETIC_CA_ENV.md:96-97`).
  - Fatigue, shift limits and night work rules: units work continuously for up to 48h
    [inferred: no such code].

### 2.5 What is and is not modelled in the CA

- **Modelled.**
  - Diurnal fire activity: ×0.3 at night up to ×1.0 in early afternoon
    (`synthetic_ca.py:118-121`), plus diurnal wind in synthetic weather (`:494-508`).
  - Spotting, slope and moisture effects.
  - Urban cells as priority assets with weight 50 (`synthetic_env.py:43`).
- **Not modelled.**
  - Aircraft, water, retardant, engines, backfires and burnouts.
  - Direct attack on burning cells: units cannot enter them or build on them.
  - Roads or faster travel on roads.
  - Line holding or mop-up crews, and line failure other than by spotting.
  - Crew rest.

### 2.6 What the CA policies see [code]

**Agent observation** (`synthetic_env.py:651-722`).
- **Map.** 13 channels at 64×64, i.e. 2×2-pooled 360 m blocks. The channels are burning
  (max), ever burned, line (max), urban (max), base ROS, non-burnable, water (max), slope,
  elevation, and one position plane per unit slot.
- **Per-unit vector.**
  - Active, lost, dozer flag and arrival-time offset.
  - Row and column, build progress and the current action.
  - The offset to the nearest burning cell and to the nearest unburned urban cell (L1-nearest,
    /64).
  - A **15×15 full-resolution crop** of burning, burned and blocked cells around the unit.
- **Globals.**
  - Wind speed / 8 m/s, sin and cos of the downwind bearing, and moisture / 0.3.
  - Hour of day as sin and cos.
  - Decision / horizon, active-unit share and burning-cell count / 500.

**Weather timing.** The agent sees the weather of the hour about to be simulated: both
`_observation` and the next `_advance` read `weather.at(self.decision)` (`:710`, `:540`,
`:583-587`).
- In effect this is a one-hour perfect forecast. It is the opposite of SimFire's lag rule.
- On real cases the shown values are the ex-post gridMET of the current segment
  (`synthetic_real_cases.py:117-149`) [code].

**The heuristics see more than the agent.**
- They take the whole `env` and read full-resolution state directly:
  - `env.fire.burning`, `env.fire.ever_burned` and `env.land.urban`;
  - exact unit positions;
  - `env.spec_now.weather.at(env.decision)` (`synthetic_heuristics.py:47-57,142`).
- The agent sees the same weather. Spatially, however, it sees the map only 2×2-pooled,
  plus 15×15 crops around each unit.
- The module docstring (`synthetic_heuristics.py:1-5`) and (before 2026-11-12) `SYNTHETIC_CA_ENV.md:164-166` say
  the heuristics "read only what the agent's observation also encodes". That holds for the
  *kind* of information but **not for its resolution**.
- Neither side sees the no-op rollout or later weather.

### 2.7 How each CA policy decides (every hour, per active unit) [code]

**Shared helpers** (`synthetic_heuristics.py:20-44`).
- `_direction_toward` picks the legal move or build whose one-cell step lands closest to a
  target. It returns 0 (stay) unless some step is strictly closer. Ties go to the first
  direction in N→NW order.
- `_heading_action` ranks the 8 directions by cosine with a heading and takes the best legal
  one with a positive cosine, else stay.
- "Nearest" means Euclidean distance with ties to the first cell in row-major order (`:60-64`).
- Every heuristic returns all zeros when nothing is burning.

**`noop`** (`:67-68`). All units stay. Automatic retreat still applies.

**`random`** (`:71-78`).
- For each of the 4 slots it picks uniformly among that slot's legal actions: stay, moves
  and builds. Inactive slots have only "stay" legal, but still consume a draw.
- Seeded with `np.random.default_rng(seed)`, where `seed` is the synthetic episode seed
  (`scripts/evaluate_synthetic_policies.py:67`) or `spec.seed` on real cases
  (`scripts/evaluate_real_cases.py:61`).
- **This is not SimFire's `random_legal`.** It is mostly a random walk that seldom builds
  coherent line. (ADR-028 gate v4 reports 1.5% mean saved [doc]; that is an invalid-era figure.)

**`direct_flank`** (`:81-111`).
1. Find the nearest burning cell. If it is more than 4.5 cells away, move toward the point
   3 cells (540 m) from it, on the unit's side.
2. Otherwise build. The heading is the tangent to the radius from the **burned-area
   centroid**, oriented so that it points downwind (dot product with wind ≥ 0).
3. Odd slots reverse the tangent when the unit is on the upwind side (radial·wind < −0.3).
4. If the unit is closer than 3 cells, add 0.7 × the radial vector so the line drifts outward.
5. Play the best-matching legal build action, else stay.

**`downwind_indirect`** (`:114-136`).
1. The anchor is the burned centroid plus (the furthest downwind extent of burned cells
   + 8 cells) along the wind direction.
2. Slot i's start point is the anchor ± (1 + i//2) × 2 cells across the wind, alternating
   sides.
3. If the unit is more than 1.5 cells off the anchor line along the wind, or more than 25
   cells from its start point, move toward the start point.
4. Otherwise build across the wind, toward its own side.

**`protect_urban`** (`:139-167`).
1. With no unburned urban cell, or no fire, act as `direct_flank`.
2. Otherwise find the burning cell nearest the urban centroid, then the urban cell nearest
   to that burning cell.
3. If they are more than 30 cells (5.4 km) apart, act as `direct_flank`.
4. Otherwise take the urban cells within 8 cells of that target and form a ring around their
   centre, with radius = their maximum distance + 2 cells.
5. Units more than 1.5 cells off the ring move onto it. Units on the ring build tangentially;
   odd slots go the other way.

**PPO (MaskablePPO).** A CNN over the map and an MLP over the vectors (doc). It chooses all 4
unit actions jointly each hour under the mask. In evaluation it is deterministic
(`evaluate_synthetic_policies.py:50-55`).

### 2.8 Budget and episode rules in the CA [code]

- **Budget.** There is no budget counter. The resource is the number of units, their arrival
  times and their production rates.
- **Episode.**
  - Decisions are 60 minutes, made of 30 substeps of 2 minutes (`:38-39`).
  - The horizon is 12, 24 or 48 h (curriculum) or 48 h on real cases.
  - After the horizon, units withdraw while lines stay. Both rollouts then run 12 more hours
    on shared random numbers (`:593-601`).
  - The episode ends early if the agent's fire goes out; the remaining no-op damage is then
    credited at once (`:589-592`).
- **Reward.** (no-op damage − agent damage) / max(no-op total, 20), minus the safety penalties
  (`:585,604`).

---

## 3. Old pilot CA (`simulator.py`, `gym_env.py`, `policies.py`)

**Purpose.** Labelled "Small synchronous cellular automaton for pipeline tests, not fire
prediction" (`src/wildfire_rl/simulator.py:1`). It has no physical units, cell size or time
scale.

**Fire model.**
- The grid is 20×20 in `configs/pilot.json`, with 6×6 in the training smoke
  (`train.py:30-31`).
- Spread uses 4 neighbours with probability 0.35 per edge per tick, using common random
  numbers keyed by seed, tick and edge (`simulator.py:70-97`).
- A cell burns for 3 ticks. The fire runs 2–4 warm-up ticks before any action. The horizon is
  80 steps by default and 240 in `pilot.json`.

**The intervention.** "Treat" one cell per tick: `Discrete(rows·cols + 1)`, where the last
index is no-op (`gym_env.py:22`, `simulator.py:107-118`).
- **Mask.** Budget must be left, and the cell must be FUEL or **FIRE** (`simulator.py:99-101`).
- **Effect.** Treatment happens before that tick's spread and sets the cell to TREATED.
  - A treated fuel cell can never burn.
  - A treated burning cell stops burning and spreading at once: an instant extinguishment.
    It stays counted in `ever_burned`.
- This is the **only** simulator in which a burning cell can be suppressed. The "unit" is
  abstract: cost 1 per cell, no travel, no rate and no safety (ADR-003).

**Budget.** Configured budgets are {0, 2, 4, 8, 16} in `pilot.json`, or {0, 2, 4} in training.
- At most one treatment per tick.
- Running out of budget does not end the episode. The episode ends when no cell is burning,
  or is truncated at the horizon (`simulator.py:103-105`).

**Observation.** The full grid at full resolution (`gym_env.py:29-39`): state / 4, burning age,
ever-burned flag and priority-cell flag, plus budget and time.
- The scripted baselines read the same engine state directly (`policies.py:8-33`), so they
  and the agent see the same information.

**Policies** (`policies.py:5-33`).
- **The fallback.** Every policy returns no-op when no cell is valid.
- **`none`.** Always no-op.
- **`random`.** A uniform choice over all valid cells, burning or unburned, anywhere on the
  grid. It is seeded per episode as `random.Random(f'policy:{seed}')` (`evaluation.py:59`).
- **`min_l2`.** Of the valid burning cells, it treats the one closest (squared Euclidean) to
  the ignition. Ties go to the lowest cell index.
- **`max_l2`.** The same, but it treats the farthest burning cell.
- **`priority`.** It treats the burning cell closest to any priority cell (or to the ignition
  if there are no priority cells). Ties go to the lowest index.
- **For all three distance policies:** with no valid burning cell, they play no-op.
- **PPO.** A smoke-test MaskablePPO only (`train.py:30-45`).

---

## 4. Comparison table

| | SimFire on FEDS starts (main) | Synthetic CA | Old pilot CA |
|---|---|---|---|
| Grid / cell | 256×256, 180 m (46 km) | 128×128, 180 m (23 km) | 20×20, abstract |
| Decision interval / episode | 12h / 4 decisions (48h) | 60 min / 12–48h + 12h tail | 1 tick / up to horizon |
| Intervention types | FIRELINE only (SimFire also has scratch and wet line, unused) | Line built by units | "Treat" one cell |
| Physical unit | 1 budget unit = one 20-person crew shift ≈ 1.26 km line (convention) | 20-person Type II crew; Type II dozer | None |
| Aircraft / water / retardant / engines / backfire | No / no / no / no / no | No / no / no / no / no | No (abstract) |
| How a line appears | Instantly, whole segment | Cell by cell at NWCG rates (crew FM1 about 30 min per 180 m cell; dozer about 5 min) | Instantly, one cell |
| Who picks the exact cells | Environment (front_edge rule); policy picks 1 of 8 directions | Policy steers each unit cell by cell | Policy picks the cell |
| Where | Perpendicular to sector, centre 2 cells beyond the leading burning cell (360 m axis, 509 m diagonal) | Wherever a unit stands on an unburned burnable cell | Any FUEL or FIRE cell |
| Line length per action | 7 cells (1,260 m) or 9 cells (1,273 m diagonal), clipped | 1 cell (180 m) per completed build | 1 cell |
| On burning or burned cells? | No (UNBURNED only; non-burnable allowed) | No (unburned burnable only) | Yes on burning (extinguishes); no on burned |
| When fire crosses | Only if the spread rate reaching the line exceeds 980 ft/min (about 18 km/h); measured peak about 58 ft/min, 0 of 2,179 cells ignited (TRAIN, one heuristic; inferred for the rest); fire goes around | Never by contact; spotting can jump | Never (treated is permanent) |
| Line cells in damage | Counted as saved even if no-op would burn them (no charge) | Charged as damage if in no-op footprint | Treated fire cells stay counted as burned |
| Spotting / diurnal | No / no | Yes / yes | No / no |
| Travel, arrival, safety | None | Travel 2.5–3 km/h, arrival 0–3h at 2–4 km, auto-retreat, close call −0.1, loss −1.0 | None |
| Budget | B ∈ {0,1,2,4} lines per 48h, at most 1 per decision; unspent budget is worthless | No counter: 2–4 units (4 fixed on real cases) | B treatments, at most 1 per tick |
| Policy observation | 4×16×16 pooled (2.88 km blocks), budget, lagged daily weather, time; no slope | 13×64×64 pooled (360 m) + 15×15 full-resolution crops per unit + upcoming-hour weather | Full grid |
| Heuristics vs agent | Identical inputs; agent also gets budget and time | Heuristics read full-resolution env state (more than the agent) | Same |
| Random policy | Uniform over legal lines; seed 0 restarted per fire, so the same directions repeat | Uniform over all legal per-unit actions (mostly wandering); episode seed | Uniform over valid cells; `policy:{seed}` |

## 5. Documents that no longer match the code

1. **ADR-025, diagonal line length.** It says a segment is "up to about 1.8 km diagonally".
   The code now uses 5 diagonal cells plus 4 fillers, 1,273 m (`feds_simfire_env.py:70-79`).
2. **`SIMFIRE_ENVIRONMENT.md:384-387`, placement and cell count.** It says "at most seven
   FIRELINE cells ahead of the front centroid". That is the old `centroid` placement; stage 2
   uses `front_edge`, and diagonal lines have 9 cells.
3. **ADR-025, wind used by the downwind heuristic.** It says the heuristic uses the "current
   12h wind-to heading". ADR-030 replaced this with the lagged daily record, and the
   `feds_heuristics.py` docstring is current.
4. **ADR-025, line failure.** It says "line failure [is] not modelled". Failure is modelled
   through the 980 ft/min threshold but does not occur in practice (§1.3). It also does not
   mention that line cells count as saved (§1.3).
5. **Synthetic heuristics' information claim.** `synthetic_heuristics.py:1-5` and
   `SYNTHETIC_CA_ENV.md:164-166` say the heuristics see only what the agent sees. They read
   full-resolution state (§2.6). *Status 2026-11-12: the doc is corrected; the docstring is not.*
6. **`SYNTHETIC_CA_ENV.md:27`, real-case count.** It says 119 FEDS cases; the count is now 118
   (ADR-030 TASK-027 addendum). *Status 2026-11-12: corrected in the doc.*
7. **Head-rate calibration error.** `SYNTHETIC_CA_ENV.md:61` says "at most 12%";
   `synthetic_ca.py:42` says "within about 20%".
