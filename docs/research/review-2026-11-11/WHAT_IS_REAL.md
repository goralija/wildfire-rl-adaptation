---
type: Research Analysis
title: "Šta je stvarno, a šta simulirano u SimFire putu"
description: "Šta se uzima iz stvarnih požara, odakle logika širenja i koliko simulacija prati stvarni rast."
status: stable
generated: {by: "process:claude-code", at: "2026-11-11T16:00:00Z"}
sources:
  - resource: /src/wildfire_rl/feds_simfire_setup.py
  - resource: /scripts/select_feds_growth_gate.py
  - resource: /reports/real-fire-data/feds-simfire-train-growth-gate-v1.json
---
# Is the owner's reading of the module diagram correct?

The owner's reading: "From real fires we derive how fire spreads in the real world and use that logic in simulated fires, so the agent learns to fight a real fire."

Code checked at worktree `task-026-stage-2` (HEAD 61f0ebf). SimFire 2.0.1 checked in `overnight-steps-5-8/.local/simfire-venv`. Paths are relative to the worktree unless stated otherwise. `fire.py` means `.../site-packages/simfire/game/managers/fire.py`. The project marks ADR-022 to ADR-028 as invalid, so no numbers are taken from them.

## 1. What comes from real data, and where it enters

| Input | Source and treatment | Where it enters |
|---|---|---|
| Fire selection | FPA-FOD record matched to one FEDS fire with five 12-hour states covering 0–48 h (`scripts/build_feds_episode_manifest.py:100-128`, `:160-167`). One record kept per FEDS fire (`:22-50`). Result: 98 TRAIN fires (2018: 70, 2019: 28) and 20 VALIDATION fires (2023) (`data/manifests/feds-episode-cohort-v1.json` `case_counts_by_split`). | Episode list |
| Starting burned area and active front | FEDS `lf_perimeter` and `lf_fireline` at the exact start time, drawn onto a 256×256 grid of 180 m cells (`scripts/build_feds_simfire_inputs.py:278-306`). Later perimeters are not used to build the start (`:335`). | `compose_initial_fire_map` makes the scar "burned" and the front "burning" (`src/wildfire_rl/simfire_initial_state.py:27-30`). It is loaded into SimFire with one burning cell per front cell (`feds_simfire_setup.py:409-415`). |
| Fuel | LANDFIRE FBFM13, the 13 standard Anderson fuel types: LF2016 for 2018–19 and LF2022 for 2023, majority resampling (`build_feds_simfire_inputs.py:272-275`, `:285`, `:312-318`). Described as a pre-event product, not a survey of the fire day (`:318`). | `OperationalFuelLayer` (`feds_simfire_setup.py:436-437`). Each code becomes SimFire's built-in fuel parameters (`:381-384`). |
| Terrain | LANDFIRE LF2020 elevation with bilinear resampling (`build_feds_simfire_inputs.py:286`, `:319-325`). | `OperationalTopographyLayer` (`feds_simfire_setup.py:438`). SimFire computes slope from it (`fire.py:446`). |
| Weather for each 12-hour segment | Daily gridMET wind speed `vs`, direction `th` and `fm100`, sampled at one cell (≤5 km) nearest the starting perimeter centroid (`scripts/sample_gridmet_episode_weather.py:110-145`; `gridmet_weather.py:110-134`). Each of the four segments uses the daily record that contains its midpoint (`gridmet_weather.py:137-152`). Two segments can therefore share one daily value (`feds_simfire_setup.py:43-48`). | The record is converted to SimFire values (`gridmet_weather.py:52-78`). Wind reaches the flames at WAF × speed. Direction is rotated 180°. fm100 is divided by 100 and used as fuel moisture. **One value is applied to the whole 46 km map** (`np.full`: `feds_simfire_setup.py:439-445`; `U[:] =`: `:451-455`; one moisture value: `fire.py:490`). fm100 is a stand-in for the moisture SimFire expects (`docs/research/SIMFIRE_ENVIRONMENT.md:147-148`). |
| Later perimeters (+12/24/36/48 h) | FEDS perimeters at the four later manifest timestamps (`scripts/run_feds_noop_episode.py:39-60`). | **Scoring only.** They are opened after the simulation has finished (`run_feds_noop_episode.py:185`) and compared with `binary_burn_metrics` (`:193-211`). The manifest lists them as evaluation-only (`build_feds_episode_manifest.py:179-188`). The RL environment never uses them: its reward is simulated burned area (`src/wildfire_rl/feds_simfire_env.py:3-4`, `:452`, `:471`; `scripts/train_feds_simfire.py:106`). |

## 2. Where the spread logic comes from

- **Spread model.** SimFire's built-in Rothermel model (`fire.py:287-291`, `simfire/world/rothermel.py:4-25`) drives spread, using the standard FBFM13 fuel parameters.
  - A cell catches fire when the accumulated spread exceeds one cell width (`fire.py:568`, `burn_amounts > pixel_scale`; cell = 180 m, `feds_simfire_setup.py:53`, `:435`).
  - Burning cells go out after a 90-minute lifetime (`:63-64`, `:389-391`).
  - None of these equations or fuel constants is estimated from the fires.
- **What was tuned, and how.**
  - Two scalars were tuned together: the wind adjustment factor (WAF, which scales wind speed) and a rate-of-spread multiplier (ROS).
  - There were **17 candidates**, fixed in advance: WAF {0, .0025, .01, .025, .05, .10, .20, .605} at ROS 1.0, plus WAF {.05, .2, .4} × ROS {.35, .5, .7} (`scripts/select_feds_growth_gate.py:34-38`; ADR-030 §3, `DECISION_RECORDS.md:962-979`).
  - **Data:** 98 TRAIN fires, one no-op (no firefighting) run each with seed 0.
  - **Rule:** a candidate passes if every case runs without error, no fire touches the map edge, and on growing fires (observed +48 h area at least 1.10 × the starting area) the mean growth-only IoU beats a fixed downwind 2:1 ellipse. Among passing candidates the highest growth IoU wins; ties go to the lower area error (`select_feds_growth_gate.py:47-57`, `:202-216`; `scripts/evaluate_feds_train_noop.py:63`, `:82-116`).
- **Result.**
  - 8 of 17 passed (`reports/real-fire-data/feds-simfire-train-growth-gate-v1.json` `passing_candidates`).
  - The selected candidate was **WAF 0.10, ROS 1.0** (`configs/frozen/feds-simfire-growth-gate-freeze-v1.json` `frozen_params`). Because ROS = 1.0, Rothermel runs unscaled, so **the only tuned value in use is the WAF**.
  - The other settings were fixed by hand, not fitted: 5-minute step (ADR-030 §2, `DECISION_RECORDS.md:956-959`), 90-minute lifetime (`configs/simfire_feds_base.yml:68-70`), and the project's per-minute fireline correction (`feds_simfire_setup.py:458-488`).
  - WAF 0.10 was not the best fit. Growth IoU keeps rising with WAF up to .20 at ROS 1.0. **.10 was chosen because it is the highest value that keeps every fire off the map edge** (`DECISION_RECORDS.md:1225-1226`).
  - Among the 8 passing candidates, WAF 0.10 has the **largest** area error: 4,119.5 ha, against 2,343–2,726 ha for the others (gate report `candidates[].mean_absolute_area_error_ha`).
  - The no-wind candidate (WAF 0) also passes (`DECISION_RECORDS.md:1224-1225`).

## 3. How closely the simulation matches real spread

All figures are for the frozen setting, from the gate report and ADR-031 (`DECISION_RECORDS.md:1159-1236`).

- **Growth IoU (how well new burned area overlaps with observed new burned area; 1 is perfect).**
  - TRAIN: 0.0958 against 0.0258 for the ellipse, on 82 growing fires (`selected.simfire_mean_case_growth_iou`, `ellipse_mean_case_growth_iou`).
  - VALIDATION: 0.0983 against 0.0278, on 18 growing fires (`feds-simfire-validation-growth-gate-v1.json` `growth_gate.*`).
  - Both are below 0.10. SimFire is ahead of the ellipse on 59 of the 82 growing fires. It adds no cells at all on 10 of them (`DECISION_RECORDS.md:1183-1185`; `selected.growing_cases_without_simfire_growth`).
  - Only 18% of the new cells it predicts fall inside the observed growth, and it covers 26% of the observed growth (`:1227-1229`).
- **Size of growth.**
  - On growing fires, mean simulated growth at +48 h is 2,193 cells against 1,219 observed, 1.8× (`:1227-1228`).
  - Fire by fire, computed here from the local full report (sha256 `ba7e91…`, equal to `selected.local_full_report_sha256`), simulated +48 h growth is within a factor of 2 of observed growth on only **12 of 82** fires. It is more than 2× too large on 33 and less than half on 37.
- **Overgrowth on fires that stopped growing.**
  - On the 16 non-growing fires, the simulation adds about 2,770 cells (8,976 ha) more than FEDS observed (`freeze selected_candidate.non_growing_mean_overgrowth_*`).
  - The likely reason: real fires were contained or suppressed, while the no-op run burns freely (`select_feds_growth_gate.py:282-283`).
- **Area error and whole-mask IoU.**
  - Mean absolute area error is 4,120 ha, against 2,371 ha for "persistence" (simply assuming the fire does not grow).
  - Whole-mask IoU is 0.355 against 0.532 on TRAIN and 0.406 against 0.543 on VALIDATION (`DECISION_RECORDS.md:1232-1234`; validation `full_mask_metrics_for_context`).
  - On these measures, the no-growth guess scores better than the simulator.
- **What the PASS shows.** Under the rule set in advance, SimFire puts new growth in better places than a fixed geometric ellipse on fires that grew, on TRAIN and again on VALIDATION (`DECISION_RECORDS.md:1221-1222`).
- **What the PASS does not show.**
  - The ellipse is a weak benchmark: it adds about 23 cells where FEDS observed 1,219 (`:1223-1224`).
  - The result is not a calibration or a physical validation. The report's `physical_validation` field is `false`.
  - The frozen setting is "a free-burning scenario that passes the pre-set gate, not a calibrated or physically validated spread model" (`:1235-1236`; freeze `warning`).

## 4. Corrected description for a non-expert, and verdict

**What the diagram shows.** The project takes about 118 large western US fires (2018, 2019 and 2023). For each fire it records where it had burned and where it was actively burning at one satellite snapshot. It adds the real fuel map, terrain and daily weather for that place. These are given to SimFire, an off-the-shelf fire simulator that uses the standard Rothermel spread equations. Nothing about how fire spreads is learned from the real fires. The project's only adjustment was one wind-strength setting, chosen from 17 preset options on 98 fires: the strongest setting that kept simulated fires inside the map. Satellite perimeters from the next 48 hours are used only to grade the uncontrolled simulation. The simulator beats a crude fixed-ellipse guess but still matches real growth poorly: about 10% overlap on new burned area, and often more than double or less than half the real growth. The agent is then trained, and the stage-2 policy benchmark run, entirely inside this simulator. The reward is simulated burned area, and policies are never scored against what the real fires did (`feds_simfire_env.py:3-4`; `scripts/benchmark_feds_policies.py:4-13`). Even in the simulator, the trained policy could not be told apart from a random legal fireline or the best simple rule (ADR-032, `DECISION_RECORDS.md:1267`).

**Verdict: partly correct.** The starting state, fuel, terrain and weather really do come from real fires. But the core claim is wrong: no spread logic is derived from real fires (generic Rothermel plus one wind setting chosen from 17), the resulting spread matches real fires poorly, and the agent learns to reduce burning in a SimFire run seeded with a real fire, not to fight the real fire.
