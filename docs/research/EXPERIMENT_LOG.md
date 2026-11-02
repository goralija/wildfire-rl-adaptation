---
type: Experiment Log
title: Experiment log
---
# Experiment log

## EXP-021 — Adapt prior art and create georeferenced Dogrib QA plate, 2026-10-31

**Question.** Can we reuse a published CFSDS/FBP/weather preparation method and an
existing Cell2Fire/RL workflow, while avoiding target leakage and preserving data needed
for later maps/animations?

**Method.** Re-read the W.I.S.E. methods and limitations, the 2025 Dogrib/Cell2Fire paper,
the Firehose paper, the pinned public Dogrib inputs and our existing FireCase workflow.
Adaptation decision: W.I.S.E.-style case assembly/QC + CFSDS v1.1 + target-blind initial
state + existing Cell2Fire/Firehose runtime. Dogrib is now a geospatial schema/visual QA
fixture only. Added `scripts/plot_dogrib_reference.py` and ran it against the local,
hash-pinned, ignored Dogrib raw files. It draws fuels, terrain, KML boundaries, both
published ignition representations, observed scar and the package-supplied Prometheus
comparison layer. The JSON receipt preserves CRS, grid dimensions, source commit and
observed mismatches.

**Findings.** The full raster is 223×357 at 100 m, whereas the current policy grid is
20×20. The KML point maps to one-based row/column 189/92, while `Ignitions.csv` gives
188/91. Of 10,210 observed-scar cells, 663 overlap fuel code 101. The weather file has
eight hourly samples spanning seven hours; the initial and final KML perimeter timestamps
are 22 h 52 min apart. The supplied Prometheus comparison map has no independently
verified timestep match. The existing Sub20 crop shares fuel/elevation values with a
full-map block but slope/aspect and geographic origin are not verified.

**Decision and limits.** Do not run or advertise this as a full-event physical replay.
Keep it as a geospatial/input/visualization fixture unless the ignition, fuel/scar, time
and domain issues are resolved. Adopt W.I.S.E.'s case assembly/QC pattern, but do not copy
its future-informed initial-front construction or target-optimized sensitivity scenarios
into primary training or held-out evaluation. The Dogrib paper's same-scar optimization is
not an independent generalization test. No new simulator replay, no-action gate, RL
training, or benchmark was run. `research_ready=false` remains. The output files are
`reports/real-fire-data/dogrib-reference-alignment.png` and `.json`; see
`docs/research/ADAPTED_PRIOR_ART_WORKFLOW.md` and ADR-031.

## EXP-001 — synthetic pilot
Config `configs/pilot.json`; 5 politika × 5 B × 12 seedova = 300 epizoda.
Namjena: provjera pipelinea i budžetskog računovodstva. Nema RL modela i nema tvrdnje
o adaptaciji. Konačni replay, hashes i rezultati se prilažu u reports/pilot/.

## EXP-002 — optional modern RL smoke
Mala 6×6 mreža; CPU, novi MaskablePPO, 1,024 koraka, training seed 7.
Namjena: dokaz da maskirano učenje, save/load i rollout tehnički rade.
To nije Firehose model niti transfer learning; rollout koristi trening distribuciju.
Težine ostaju lokalno u runs/; mali manifest se čuva u reports/rl-smoke/.

EXP-001 preliminary horizon check: horizon=80 left active fires in some policy/B groups
(e.g. B=16 max-L2 2/12 and priority 3/12). Revised horizon=240 for complete-damage
measurement; this is a technical termination correction, not RL hyperparameter tuning.
All earlier local exploratory outputs remain under ignored runs/.

EXP-001 final: horizon=240, 300 epizoda, 0 truncated; dvostruki replay odgovara svim
metrikama osim runtime_seconds. Config SHA256 je u reports/pilot/replay-check.json.
Pri B=16 max-L2 je u ovom pilotu imao 75.09% opožarenog, no-action 98.37%; to je
samo ponašanje heuristika u sintetičkom svijetu, ne rezultat RL istraživanja.
EXP-002 final: 1,024 koraka, save/reload i validni masked rollout završeni na CPU-u;
manifest u reports/rl-smoke/training_manifest.json. Nema held-out tvrdnje.

## EXP-003 — stvarni Firehose/Cell2Fire inference, bez treniranja
12-case batch u Linux ARM64/Python 3.8/SB3 1.5.0. Oba pretrained modela izvršena,
svih 12 C++ returncodeova 0, reproducibilni seedovi, B=8/no-op, isti input hash i
nepromijenjeni policy tensor hashovi. Sažetak: reports/firehose-verification/.
Svi runovi imaju 58 odluka pod osmosatnim weather capom; ne tumačiti done kao containment.
Originalni reset nije učitao warmup; fixed PPO brojač 206 naspram 207 iz historije.
Odvojeni sync-reset slučaj daje 207/207. Runtime PASS, istraživački adapter još pending.
Ovo nije glavni benchmark: jedan ignition/weather/layout, premalo realizacija za ranking.

## TASK-012 — desk review podataka i protokol, 2026-10-30

Pregledane su primarne CFSDS v1 dokumentacija i peer-reviewed 2026 W.I.S.E. procjena
v1.1, zvanični CWFIS fuel-map katalog i Alberta wildfire data portal. Prijedlog je
razdvojiti glavni online Firehose/Cell2Fire RL benchmark od opcionalne historijske
simulator-verifikacije; Dogrib je povezan slučaj, CFSDS dnevni i input-intenzivan.
Dodane su uloge, ulazne kontrole, scenario ID/split ugovor, moderni-vs-legacy
environment plan i uslovni TASK-011 koraci u REAL_FIRE_DATASETS/DATASET/BACKLOG.

Ovo je desk review, ne eksperimentalni run: nema novog downloada, Firehose builda,
simulacije, treninga ili historijskog replaya u ovom koraku. Odluka o datasetu/obimu,
licencama ulaznih fajlova i scenarijima ostaje otvorena za timsko usaglašavanje.

## TASK-012 follow-up — BiH coverage screen, 2026-10-30

Na korisnikov zahtjev da istraživanje uključi lokalno relevantne stvarne požare,
preuzet je FireSpread_MedEU v2 ZIP (2,751,019 bajtova; SHA256 i download URL u
`reports/real-fire-data/medeu-spatial-screen.json`) u ignorisani `data/raw/`. Geopandas
overlay (dataset EPSG:3035 → WGS84) sa Natural Earth Admin 0 1:110m državnom granicom
našao je sedam kandidata koji dodiruju BiH: EFFIS IDs 12321, 13228, 22108, 25244, 25274,
43482, 205938. Ovo je grubi kandidat-screen, ne konačna lokacijska verifikacija.

Najbolji historijski referent po quality/daily coverage je EFFIS 205938: četiri
uzastopna koraka 2022-07-15..18, svi `very high`, završna površina 637.63 ha i prostor
oko 4.14×4.18 km. Najmanji po površini je 43482 (216.87 ha, 3 koraka), ali extent
2.56×1.71 km i jedan korak medium kvaliteta. Oba pokazuju da hektari sami ne kažu da li
fire extent stane u agentovih 2×2 km.

MedEU shapefile sadrži dnevne poligone i LCCS pokrovne udjele, ne DEM, hourly weather ili
Canadian FBP fuel codes; Zenodo v2 ne prikazuje licencu data arhive. Nije napravljeno
simulator case, data conversion, RL trening ili historijski replay. Environment sada ima
GIS stack; ERA5 CDS auth, kompatibilan BiH fuel/spread model, EFFIS location/MedEU license
checks, grid extent i simulator initial-front importer su i dalje potrebni.

### TASK-012 follow-up — EFFIS fuel layer screen, 2026-10-30

Preuzet je EFFIS European Fuel Map 2017 (250 m, EPSG:3035, NFFL/Anderson); SHA256,
source, licenca napomena i GIS overlay na dva lokalna MedEU događaja nalaze se u
`reports/real-fire-data/medeu-spatial-screen.json`. Ovo je data-screen, ne simulator
eksperiment: EFFIS vrijednosti nisu ubačene u Canadian FBP Cell2Fire, nije napravljena
case konverzija, replay niti trening. MedEU licenca/lokacije, fuel model validacija,
weather/DEM i multi-cell front import ostaju otvoreni.

## ENV-001 — moderni i legacy environment, 2026-10-30

Prvo su u izolovanom task worktreeu napravljeni Python 3.12.4/macOS ARM64 `.venv` i
odvojeni Linux ARM64/Python 3.8 Docker image iz tačno pinovanih Firehose/contrib commitova.
Potom je moderni venv reproduciran u korisnikovom `feature/project-bootstrap` checkoutu
iz istog kombinovanog freezea; tamošnji import, testovi, strict validator, CLI i PPO smoke
su ponovo prošli.
Prošlo je 26 app testa, 15 knowledge testa, strict validator, synthetic CLI smoke,
1,024-koračni optional modern PPO smoke i 12 kratkih Firehose inference slučajeva.
Legacy runtime je offline i training steps=0. Environment/image/package hashovi i
tačne ograničene tvrdnje su u `reports/environment-setup/`.

Poređenje input inventara s ranijim sačuvanim JSON-om pokazalo je potpuno isti rezultat:
141 fajl / 159,595 bajtova, 130 weather traceova po osam redova, 400 ćelijskih redova;
399 Data.csv redova ima 20 polja, jedan ima 19. Ignition 381 i 372 su oba goriva,
ali različite ćelije; to nije off-by-one. Adapter problemi ostaju.


## EXP-004 — CFSDS `2018_747` no-action replay diagnostic, 2026-10-30

Selected route: Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire. One pilot day-pair
(15–16 Aug 2018), in the preliminary train partition. 20×20 cells at 100m; 175 scar
cells plus 31 active-front cells imported through `InitialState.csv`. Inputs: CFSDS
90m burn-arrival raster, official Canadian FBP 2014b fuel map (250m), MRDEM 30m
terrain, ERA5-Seamless 24-row weather series. Target day remains separate from agent input.

Six compiled C++ no-action replays, seeds 123–128; interventions=0, training steps=0,
all runs finished successfully with the same input hash. Every run produced the identical
final grid, 66ha predicted area; observed CFSDS target=15.39ha; area-weighted
precision=.2213, recall=.9491, IoU=.2187, predicted/observed area ratio=4.2893. Nineteen
predicted cells touch the crop edge. Model duration varied from 206 to 363 saved minute
intervals, while the final grid stayed unchanged. Suppression status is unknown; daily
target is satellite-interpolated; daily FWI was held constant in hourly rows. This is an
input/model mismatch diagnostic and not physical validation or a counterfactual agent result.
Receipts: `reports/real-fire-data/2018_747-day228-replay.json` and
`reports/real-fire-data/2018_747-seed-sweep.json`; map:
`reports/real-fire-data/2018_747-day228.png`.

Gate: review fuel/terrain/weather alignment and crop-edge truncation; replay multiple
train fires/seeds; only then decide whether to calibrate and lock heldout cases. No RL
training performed.

## EXP-005 — More CFSDS train cases and zero-warmup check, 2026-10-30

Built and replayed two additional 2018 train day-pairs with the same 20×20/100m
converter, Canadian FBP 2014b map, MRDEM terrain, hourly ERA5-Seamless weather,
historical `InitialState.csv`, and no interventions. The C++ run used `steps-before=0` so
the simulator began at the observed prior-day state. `2018_241` predicted 237 ha versus
12.153 ha observed (IoU=.0376; 62 predicted cells touch the crop edge, final affected
grid=400/400). `2018_1770` predicted 73 ha versus 12.151 ha (IoU=.1361; 26 edge cells).
Each currently has one seed. `2018_241` was also run with `steps-before=20`; final metrics
were identical, so that warmup does not explain its overgrowth. The existing `2018_747`
seed-123 no-action run with zero warmup also reproduced 66 ha / IoU=.2187.

An additional geometrically screened train case, `2014_538`, failed the converter's
fuel compatibility gate because a historical state/target cell maps to Water or
Non-fuel on the 2014b map; it was not sent to C++.

Receipts: `reports/real-fire-data/2018_241-case.json`, `2018_241-day227-replay.json`,
`2018_241-day227-replay-warmup20.json`, `2018_241-day227.png`, and equivalent
`2018_1770-*` files; rejection receipt `2014_538-fuel-rejection.json`. These runs
confirm that geometric crop screening is insufficient and that simulator no-action
behavior needs input/model diagnosis before policy training. No RL training performed.

## EXP-006 — Train-only per-cell CFSDS fuel QC, 2026-10-30

Audited all 20 preliminary train day-pairs against the official Canadian FBP 2014b
250 m fuel layer. The tool independently reports 90 m CFSDS native-pixel overlap and
the actual centered 20×20/100 m Cell2Fire grid, matching the existing converter's
nearest-neighbour fuel resampling and area-averaged state masks. It cross-checks event
area against the annual group table and records source/code hashes.

Results: 10 `PASS_FUEL_ONLY`, 10 `FAIL_FUEL_OVERLAP`, zero processing errors. All 20
retain a valid adjacent front/target pair on the model grid, and majority front/target
cells do not touch the grid edge. All three existing no-action replay cases pass the
fuel-only gate, so fuel overlap by itself does not account for their spread mismatch.
Suppression is unknown for all candidates. The all-split cohort manifest and crop-screen
JSON were loaded for train selection, but no validation/test source or fuel raster was opened or
overlaid. No C++ replay, policy benchmark, calibration or RL training was run.

The exclusion rule checks earlier scar as well as active front and target, and is a
project-specific conservative gate inspired by (not reproducing) the W.I.S.E. method.
10 fuel-pass events are not full-case passes; terrain/weather/suppression, fuel vintage,
crop adequacy and no-action behavior remain separate. See [method](CFSDS_TRAIN_QC.md)
and [receipt](../../reports/real-fire-data/cfsds-train-fuel-qc.json). Next is TASK-018
train-only diagnosis of the three current replay mismatches. No heldout outcomes used.

## EXP-007 — CFSDS no-action timeline diagnosis, 2026-10-30

Compared the saved minute-grid histories for the three existing train-only no-action
replays at fixed 30, 60, 120, 240, 480, 720 and 1,440 simulated-minute checkpoints.
The original input manifests and simulator-input hashes were preserved. No C++ replay,
training, parameter tuning or validation/test raster inspection was performed.

Predicted areas at the fixed checkpoints show different spread timing by event: at 30
minutes the three cases are 18/8/0 ha; at 120 minutes 42/46/13 ha; at the final state
66/237/73 ha versus CFSDS targets 15.387/12.153/12.151 ha. All three first reach the
20×20 grid edge after 34/37/52 minutes. `2018_241` fills all 400 cells; `2018_1770`
reaches its 24-row weather limit; `2018_747` stops earlier with no active cells and
remaining unburned grid cells. The saved Python probe horizon field had incorrectly
multiplied `steps_per_action` by 60 (480 min); source inspection confirms the C++ cap is
24 weather rows × 60 min = 1,440 min. The field now uses actual `Weather.csv` row count.

Confirmed and hypothesized explanations are separated in
[`CFSDS_NO_ACTION_DIAGNOSIS.md`](CFSDS_NO_ACTION_DIAGNOSIS.md); checkpoint measurements
and all three input/container hashes are in
[`cfsds-no-action-timeline.json`](../../reports/real-fire-data/cfsds-no-action-timeline.json).
The diagnostic stage is complete, but the physical cause remains unresolved because the
daily CFSDS target has no exact within-day timing, suppression is unknown, all runs touch
the crop edge, and weather/FWI inputs are approximate. TASK-004c is next; the no-action
gate remains failed and fine-tuning stays on hold.

## EXP-008 — Firehose cumulative damage and terminal-state adapter, 2026-10-30

Implemented TASK-004c against pinned Firehose `e49a52a9` and contrib `43b7fe6f` in the
isolated Linux ARM64 image. The C++ terminal receipt now exposes sorted one-based IDs for
the active front, cumulative affected cells and treated cells, plus a named simulator
termination reason. The Python adapter reconciles its final counters with that receipt.
For historical initial-state imports, the exported grid distinguishes scar/front; standard
maps retain the legacy one-code fire grid. The checkpoint observation/action/reward contract
was not changed.

A first 12-case run exposed a real discrepancy for PPO-selected cells that became treated
and affected in one simulator interval: the grid displayed only `-1` while the C++ cumulative
set retained the cell. The adapter now treats the C++ terminal list as canonical and checks
that every grid-visible fire cell appears in it, while each hidden affected ID is explained
by the treated set. The corrected matrix passed 12/12 cases; all Python/C++ final cumulative
counts matched, all subprocesses returned 0, all five pretrained inference runs kept identical
weights, and repeated fixed-seed no-action/PPO pairs reproduced actions and state hashes.
The initial-state fixture also passed with 1 scar + 2 active cells and matching terminal
counts. Strict validation, synthetic CLI smoke and the 38-test project suite passed.

This was adapter/inference verification only: no training or physical validation. Every
matrix case ended at `weather_horizon`; `front_extinguished`, `grid_exhausted`, and
`no_ignition` C++ terminal branches were not directly exercised in the matrix. Existing
CFSDS no-action overgrowth and crop-edge contact remain, so no-action gate is still failed
and policy benchmark/fine-tuning remain on hold. Machine receipt:
[`task004c-adapter-smoke.json`](../../reports/firehose-verification/task004c-adapter-smoke.json).

## EXP-009 — Train-only CFSDS input alignment and source-vintage review, 2026-10-31

Inspected only the 20 TRAIN IDs and their matching local generated-case directories.
Three train packages were available (2018_1770, 2018_241, 2018_747); validation
and test case packages were not opened. Their four ASCII maps share the expected
20×20/100 m header, the terrain layers contain 400 non-NoData cells, and each
Weather.csv has 24 ordered rows on the target's local date. Their weather request
locations are 2.436–5.195 km from the CFSDS summary centroid; the six daily FWI
fields are repeated across all hourly weather rows. Seventeen train case packages
were not present and remain unmeasured.

Reviewed official 2014b, 2019 development and 2024 fuel-map metadata, the W.I.S.E.
annualization recipe, MRDEM, ERA5/Open-Meteo, and CNFDB source documentation.
Reviewed the published license/terms statements too: the official 2024 map and
MRDEM portal list OGL Canada, Open-Meteo API data are CC BY 4.0 with separate
service limits, and no license statement was located in the 2014b/v20191114
directory metadata; confirm those terms with NRCan before raster redistribution.
The 2014b metadata has no explicit temporal cutoff for NFDB/NBAC burn information;
the 2019 CanFG raster is in a development directory and lists NBAC; the 2024 map
postdates the 2014–2018 train events. The W.I.S.E. recipe is recorded as a candidate
method only. No annual map was selected as a leakage-safe replacement. All train
suppression remains unknown. The report preserves this uncertainty rather than
marking cases fully qualified.

No simulator replay, target-based parameter selection, benchmark, calibration,
fine-tuning, or validation/test outcome inspection was performed. The no-action gate
remains failed. See [input QC](CFSDS_TRAIN_INPUT_QC.md),
[receipt](../../reports/real-fire-data/cfsds-train-input-qc.json),
[source review](SOURCES.md), and [ADR-019](../specs/DECISION_RECORDS.md#adr-019).

Verification for EXP-009: all 42 project unit tests passed, strict OKF validation
passed for 70 Markdown files, the synthetic CLI smoke wrote successfully to a fresh
ignored run folder, and git diff --check was clean. The train-input report was
regenerated from the three supplied train case packages. No raw data or generated
simulator input was added to Git.

## EXP-010 — TRAIN-only pre-target fuel mask and NF-scar importer characterization, 2026-10-31

Added a pure pre-target mask helper and a TRAIN-guarded audit CLI. On only
`2018_747` (target DOY 228), the full 48×50 arrival raster yielded 881 valid event
pixels before the target and 19 target pixels; the 23×23 simulator crop contained
272 pre-target pixels, 136 pixels on day n-1 (36 selected as the active front after
adjacency separation), and 236 earlier scar pixels. This raster had no arrivals
after the target. A unit fixture includes day n+1 and verifies it is excluded, so
the temporal rule is checked even though no future-coded pixel occurs in this event
raster. Source/archive/member hashes are in the mask receipt.

Ran one short, network-disabled C++ constructor/import check against the already-built
pin-compatible local image. A synthetic upstream Sub20 fixture marks cell 4 (`NF`)
as burnt and cell 1 as burning. The C++ importer reproducibly rejects the scar with
`InitialState.csv marks a non-fuel/harvested cell as burned` before grid export; the
probe's subsequent `IndexError` is only because no initial grid exists. The verifier
records this expected rejection as a passing characterization test, not successful
NF-scar compatibility. No Firehose code or case-builder semantics were altered.

No fuel map was emitted: the 2014b per-pixel historical cutoff and authoritative
succession tree has not yet been transcribed/validated, and the current importer cannot
represent an NF initial scar. Review of the W.I.S.E. paper also confirmed that the current
case builder selects its n-1 front using target day n adjacency; this target-aware input
must be replaced before an unbiased benchmark. No CFSDS replay, training, calibration,
heldout inspection or target-based selection was performed. Decision and follow-up are in ADR-020 and
[`CFSDS_TRAIN_INPUT_QC.md`](CFSDS_TRAIN_INPUT_QC.md); receipts:
[`mask proof`](../../reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json),
[`importer check`](../../reports/firehose-verification/nonfuel-initial-scar-compatibility.json).

## EXP-011 — TRAIN-only target-blind crop and initial-state proof, 2026-10-31

Replaced day-n-adjacent front selection with a rule defined before the cohort screen:
use only valid arrival values before target day n; center the 23×23 native crop nearest
the centroid of all day n−1 pixels; require at least three day n−1 pixels in the safe
interior; classify every such interior pixel as active and leave the crop border plus
older pre-target pixels as historical scar. Ties prefer more safe-interior front pixels,
then more pre-target history, then row/column. The day-n target mask is computed after
this selection and written separately as evaluation truth. The chosen weather point is
intended to be the safe-interior n−1 front centroid; no weather response or `Weather.csv`
was checked by this proof.

On TRAIN event `2018_747` (target DOY 228), all 19 target pixels were moved to different
nodata locations. The target truth changed, but selected crop offset, prior mask, 20×20
burnt/front masks, and row-major `InitialState.csv` were identical. The new crop contains
17 of the 19 target pixels (89.47%); this is post-selection diagnostic evidence, not an
eligibility rule. Receipt: [`cfsds-target-blind-input-invariance.json`](../../reports/real-fire-data/cfsds-target-blind-input-invariance.json).

A train-only cohort screen read only 2014–2018 CFSDS rasters, one year at a time, and
retained five events per year based on pre-target front/history metrics. It did not open
validation/test rasters. Only 4/25 selected windows contain any target-day pixels;
median capture is 0 and maximum is 1.0402%. Target coverage was calculated after crop and
candidate selection; it did not influence them. This warns that the current fixed 2×2 km
domain is often too small for next-day perimeter reality checks. Do not tune crop or
shortlist with this target-based diagnostic; investigate target-blind spatial feasibility
or an independently justified domain change before replay. Receipt:
[`cfsds-train-target-blind-window-screen.json`](../../reports/real-fire-data/cfsds-train-target-blind-window-screen.json).

Twelve focused CFSDS helper/screen tests pass. No new FireCase, annual fuel map, C++ replay, calibration,
benchmark, or training was run. Fuel vintage, importer scar semantics, terrain/weather
provenance, suppression, spatial feasibility, and the no-action gate remain open.
The prior 10/20 fuel-only audit applies to the legacy cohort/windows, not this new
target-blind shortlist; rerun it only after spatial feasibility defines a valid train set.
The saved pilot FireCases are not retroactively relabeled as target-blind.

## EXP-012 — TRAIN-only target-blind spatial-domain feasibility, 2026-10-31

Compared five preregistered footprints on the same 25 existing 2014–2018 TRAIN event/day
pairs: 20×20 at 100/150/200/300 m and 40×40 at 100 m. For each option the crop was
selected first using only valid arrival pixels before target day n and the day n−1
centroid, with a safe border approximately one model cell wide. Day-n raster pixels were
then measured as a post-selection coverage diagnostic. The existing 25 event/day pairs
were not reranked by target coverage. Important scope limit: original pair eligibility
required a day-n summary record and positive `firearea`, so fully outcome-independent
pair membership remains an open protocol issue.

Results: at 2 km, 4/25 windows contain any target pixel (median capture 0%, maximum
1.04%); at 3 km, 16/25 contain any pixel (median 0.13%); at about 4 km, 19/25 contain a
pixel but median capture is only 1.95%; at about 6 km, only 23/25 source rasters fit the
requested 67×67 window, with 22/23 valid windows containing any target pixel, median
capture 15.31%, and P75 50.08%. The two too-small source rasters are `2014_932` (56×139)
and `2015_895` (57×136). Counts are native 90 m raster pixels; no resampling to simulator
cells occurred.

Interpretation: the fixed 2×2 km domain is inadequate for reality-checking this shortlist.
Wider domains improve geometric coverage but do not qualify a simulator case or prove the
coarse-grid FBP model. 20×20 at 200/300 m preserves tensor/action shape while changing
physical action semantics; 40×40 at 100 m requires a new policy input/action shape. No
domain was selected from target metrics. Follow ADR-022: preregister a target-independent
day-pair rule and screen all TRAIN opportunities at fixed domains before building cases.

No fuel/DEM/weather inputs were resampled, no FireCase was built, and no C++ replay,
calibration, benchmark, training, or validation/test raster inspection occurred. The
no-action gate remains failed. Receipt: [method/report](CFSDS_SPATIAL_FEASIBILITY.md),
[machine output](../../reports/real-fire-data/cfsds-train-spatial-feasibility.json).

Verification: all 61 project tests passed; strict OKF validation passed for 71 Markdown
files; the synthetic CLI smoke wrote to a fresh ignored `/private/tmp` directory; and
`git diff --check` passed. The train-only audit read only 2014–2018 raster archives and
recorded archive/member/code SHA-256 values.

## EXP-013 — full TRAIN target-independent CFSDS day-pair and domain screen, 2026-10-31

Implemented a TRAIN-guarded scanner that reads only the 2014–2018 CFSDS annual arrival
raster ZIPs. The preregistered rule uses, for each fire raster, the earliest DOY with at
least three valid native 90 m fire pixels as input day and the following calendar day as
target. The rule does not read group CSV rows, positive `firearea`, weather, or target
geometry. All 1.301 raster IDs became pairs (234/351/116/322/278 by year); 1.010 have
mapped pixels on the target day and 291 are retained as
`no_mapped_pixels_on_next_day`. This status describes the raster product, not verified
absence of physical growth.

The scanner then evaluated the same pairs on five fixed domains. Each window uses input-day
and older arrivals only and requires at least three input-day pixels in its safe interior.
For every raster, removing target and all later arrival labels leaves the selected input
day unchanged. Target coverage is calculated after selection and is not a criterion.

| Domain | Window found | Mapped-target pairs with any target pixel inside / 1,010 | Median target capture among observed targets with a window (N) |
| --- | ---: | ---: | ---: |
| 20×20 at 100 m | 1,295/1,301 | 945 | 36.71% (1,008) |
| 20×20 at 150 m | 1,226/1,301 | 921 | 66.45% (957) |
| 20×20 at 200 m | 1,042/1,301 | 804 | 85.78% (823) |
| 20×20 at 300 m | 729/1,301 | 580 | 98.98% (593) |
| 40×40 at 100 m | 1,044/1,301 | 805 | 85.86% (824) |

Capture denominators vary because large requested windows do not fit many source rasters;
254 cannot fit the roughly 4 km footprints and 566 cannot fit the roughly 6 km footprint.
Do not use these medians as an unconditional scale ranking. No domain was adopted and
target pixels were not resampled to simulator cells.

The script generated an aggregate JSON receipt and a 1,301-row per-case/domain CSV. Both
record SHA-256 provenance; the JSON records annual archive and code hashes. The actual
screen CLI completed successfully on the supplied raw TRAIN ZIPs. No application tests
were added or run in this task. No validation/test archive, group CSV, fuel/DEM/weather
layer, C++ simulator, or checkpoint was opened or executed. No FireCase, replay,
calibration, benchmark, or training was run. This is a pair/geometry gate, not a
simulator-validity gate.

Method: [full screen report](CFSDS_FULL_DAY_PAIR_SCREEN.md); decision:
[ADR-023](../specs/DECISION_RECORDS.md#adr-023); machine output:
[JSON](../../reports/real-fire-data/cfsds-train-full-day-pair-screen.json) and
[CSV](../../reports/real-fire-data/cfsds-train-full-day-pair-screen.csv).

## EXP-014 — TRAIN fuel-vintage public-source review, 2026-10-31

Reviewed official CWFIS archive/development metadata, the current-year 2026 FBP product
description, the CWFIS download-site licence notice, official 2018 fuel-class/base-layer
rules PDFs, and the publisher version of the W.I.S.E. paper. Scope was limited to public
documentation and the 2014–2018 TRAIN fuel-vintage question; validation/test materials
were not opened.

v2014b metadata documents 2011 land cover, CanFI2000, ecological inputs, and NFDB/NBAC
use to identify burn scars, but gives no burn-record snapshot date/cutoff. v20191114 uses
2017 kNN inventory and NBAC reassignment, with no per-pixel cutoff; it is not adopted as
a direct baseline for 2014–2018. The 2024 map postdates this TRAIN interval. The 2026
current product's described annual pre-season update convention is useful context but
does not retroactively establish the v2014b cutoff.

The 2018 official decision-rules/base-layer PDFs describe assignment of baseline FBP
classes from vegetation/inventory inputs, not the separate post-fire succession tree
cited by the W.I.S.E. paper. The publisher text points to a succession decision-tree
figure but does not enumerate its branches; article data are available on reasonable
request. The site-wide CWFIS licence notice states Open Government Licence - Canada and
requires Canadian Forest Service/CWFIS attribution; this corrects the prior file-level
review without resolving separate source-layer terms.

Decision: keep v2014b only for reproducing existing saved pilots. No annual fuel map is
selected or emitted; the as-of-event burn-history cutoff and exact succession crosswalk
remain unresolved. Next, the importer contract for a historical scar on a non-fuel cell
can be specified independently, while the map remains blocked. No raster was downloaded,
no simulator case/replay or training was run, and no heldout data was inspected.

Method and sources: [fuel-vintage review](CFSDS_FUEL_VINTAGE_REVIEW.md),
[source register S-031–S-041](SOURCES.md),
[ADR-024](../specs/DECISION_RECORDS.md#adr-024).

## EXP-015 — Explicit nonfuel historical-scar importer contract, 2026-10-31

Updated the pinned Firehose initial-state import patch to accept `scar_nf` as a
separate, explicit provenance assertion. It is accepted only when the upstream
`Data.csv` cell has the exact class `NF`; ordinary `burnt` on NF, `burning` on NF,
and `scar_nf` on a burnable fuel cell are rejected. An accepted scar remains in C++
`burntCells`, the terminal cumulative-damage receipt, and Python `ever_affected`, but
never becomes available fuel or part of the active front. No fuel code or map value is
rewritten.

The synthetic Sub20 fixture ran in the pinned Linux ARM64 image with networking disabled,
no policy, zero intervention budget, and no training. Its explicit scar was present in
the initial cumulative set `[1,4]`, remained in the terminal set `[1,2,3,4]`, and was
absent from the active front at all three transitions. The terminal grid, C++ cumulative
set, and Python cumulative set agreed; termination was `weather_horizon`. Three negative
fixtures were rejected with the expected C++ errors. The runtime details and source hashes
are in the [machine-readable receipt](../../reports/firehose-verification/nonfuel-initial-scar-contract.json).

The schema helper now accepts an explicit `nonfuel_scar` mask, verifies it has the same
shape as historical damage and is a subset of that mask, and emits `scar_nf`; it does
not infer provenance from a fuel class or arrival raster. The real CFSDS builder still
rejects nonfuel scars until the annual fuel vintage and succession mapping are supported
by evidence. Cumulative damage comparisons must use the same initial scar on both agents;
the already-burned scar is not new simulated damage.

This is a parser/state-contract test on a bundled synthetic landscape, not physical fire
validation, CFSDS replay, training, benchmark, or evidence that an agent improves real
outcomes. Validation/test data were not inspected. See [ADR-025](../specs/DECISION_RECORDS.md#adr-025),
[input QC](CFSDS_TRAIN_INPUT_QC.md), and the [verification index](../../reports/firehose-verification/index.md).

## EXP-016 — TRAIN fuel-tree correction and external input lineage audit, 2026-10-31

Revisited the publisher version of the W.I.S.E. assessment after locating its Figure 2.
The public figure depicts a succession decision tree and has been transcribed in the
[fuel-vintage review](CFSDS_FUEL_VINTAGE_REVIEW.md): O-1 remains grass; otherwise age
thresholds are >21 years C-2, >5 years M-2 C25%, >2 years D-2, and younger burns
Non-Fuel. This corrects the earlier claim that the tree was not publicly transcribable.
The figure does not specify exact elapsed-year arithmetic or special-class behavior;
at the time of EXP-016, the actual v20191114 rules artifact had not yet been checked.
It was later inspected by byte range in EXP-023. The official v2014b
metadata still does not state the NFDB/NBAC burn-history cutoff; no annual map is
authorized.

Reviewed local lineage for the three saved TRAIN FireCases. Their DEM inputs name the
MRDEM-30 DTM VRT and bilinear 30 m to 100 m conversion, and output hashes exist, but
tile/source-cell IDs and per-cell acquisition dates are absent. Their raw Open-Meteo
responses preserve resolved location, time zone, variables/units and response hashes,
but not the original query coordinate/URL; the historical choice of query point is
therefore not demonstrably target-blind. The cases were made by the former target-aware
builder and remain diagnostic outputs, not clean replay inputs.

Found the official Alberta 2006–2025 wildfire dataset and dictionary, whose metadata
describes fire-level location, duration, weather, staffing and physical suppression
resources. A direct CSV request returned HTTP 403; no data were retrieved or joined.
Even a successful event-level match would not provide a daily action timeline by itself.
Two saved case centroids are in BC, while a third is near the Alberta/BC boundary, so
province-specific matching is required rather than assigning jurisdiction by case ID.

No CFSDS case, raster, simulator replay, or training was generated or run. No heldout
data were opened. This was a public-source and saved-manifest audit only.

Evidence: [ADR-026](../specs/DECISION_RECORDS.md#adr-026),
[input QC](CFSDS_TRAIN_INPUT_QC.md),
[fuel-vintage review](CFSDS_FUEL_VINTAGE_REVIEW.md),
[sources S-034–S-043](SOURCES.md).

## EXP-017 — TRAIN-only BC historical-perimeter crosswalk, 2026-10-31

Queried the official BC Wildfire historical-perimeter ArcGIS layer for only the three
already-saved 2018 TRAIN cases. For each case, took `summary_centroid_wgs84` from its
saved case manifest and queried a point intersection with `FIRE_YEAR=2018`. Exactly one
historical polygon intersected each target centroid:

- `2018_1770` → N12395 (fire date 2018-08-10, cause Person, reported polygon area 955.7 ha)
- `2018_241` → C11937 (fire date 2018-08-01, cause Lightning, reported polygon area 13,433.1 ha)
- `2018_747` → N12413 (fire date 2018-08-10, cause Lightning, reported polygon area 713.7 ha)

The same response identifies each perimeter as a 2018 rollover and gives a post-target
GPS track date. This is useful to find provincial event records, but it is not a common
incident-ID join and is not valid pre-target fuel, state or simulator input. The layer
contains no staffing, equipment, suppression action, or daily resource schedule, so
suppression remains `unknown` for all three.

Saved each query's complete small JSON response, its SHA-256 and the case-manifest SHA-256
in the [crosswalk receipt](../../reports/real-fire-data/cfsds-train-bc-perimeter-crosswalk.json).
This audit opened no other TRAIN, validation or test event. No CFSDS input, FireCase,
replay, benchmark or training was produced.

Evidence: [ADR-027](../specs/DECISION_RECORDS.md#adr-027),
[source register S-044](SOURCES.md),
[BC Wildfire historical perimeter layer](https://delivery.maps.gov.bc.ca/arcgis/rest/services/whse/bcgw_pub_whse_land_and_natural_resource/MapServer/6).

## EXP-018 — TRAIN-only BC operational-record search, 2026-10-31

Followed only the three saved 2018 TRAIN perimeter candidates (N12395, C11937 and
N12413). Contemporaneous public reporting relaying BC Wildfire Service information
documents containment-line work with five heavy-equipment units and one helicopter at
Coal Creek (N12395) on the `2018_1770` target date, August 12. An August 14 update adds
11 firefighters, one helicopter and five equipment units as a later snapshot.

For Lost Dog Complex (candidate N12413), an August 16 local recap explicitly covers
August 15 and reports a successful planned ignition, 54 firefighters, two helicopters
and six heavy-equipment units associated with the complex. An August 18 update reports
45 firefighters, three helicopters and four equipment units on August 17. The reports
bracket the `2018_747` target date (August 16), but do not give a complete target-day
timeline or allocate all complex-level resources exclusively to N12413.

The official EMBC PECC Situation Report #10 (August 16 snapshot) lists North Baezaeko
(C11937) at 2,500 ha and 0% contained. It supplies no crew/action details for the
`2018_241` target date (August 15). Its 0% containment status cannot be read as no
suppression. The BC Wildfire season summary independently identifies C11937 as a
lightning-caused fire discovered August 1, with final season size 13,433.2 ha.

These are candidate-incident records without a shared CFSDS key. Two cases now have
dated public evidence of suppression activity on or adjacent to the target; one still
has only next-day status evidence. The saved case-manifest suppression labels remain
`unknown`, because none of these sources supplies a complete event-keyed daily action
table. No action was translated to simulator cells or used to train/calibrate a policy.
No replay, FireCase build, fuel-map generation, training, or validation/test inspection
was done. See the [operational evidence receipt](../../reports/real-fire-data/cfsds-train-bc-operational-evidence.json),
[input QC](CFSDS_TRAIN_INPUT_QC.md), [ADR-028](../specs/DECISION_RECORDS.md#adr-028),
and [sources S-045–S-047](SOURCES.md).

## EXP-019 — TRAIN fuel-vintage artifact inventory, 2026-10-31

Rechecked the official v2014b and v20191114 metadata and inventoried the official
v20191114 public directory. The v2014b metadata lists the 2011 land-cover map and
CanFI2000, and says NFDB/NBAC were used with ecozones to identify burn scars, but gives
no date for those burn records or a per-pixel cutoff. The v20191114 metadata lists a
2017 kNN forest inventory and NBAC reassignment of burned-area fuel types, again with no
NBAC snapshot date or per-pixel cutoff.

The official v20191114 directory lists a metadata PDF, an approximately 2 GB ZIP, a
burn-scar legend, base-layer notes, a *Decision Rules* PDF, and a sample colour workbook.
The November 14, 2018 *Decision Rules* PDF maps vegetation/forest/species/land-cover and
ecological attributes to baseline fuel classes; it does not specify years-since-fire
succession thresholds. The burn-scar PDF is a legend, not the post-fire age algorithm.
At the time of EXP-019, the ZIP had not been downloaded or inspected, so the directory
listing could not establish whether additional artifacts were embedded inside it. A
later byte-range inspection is recorded in EXP-023.

The W.I.S.E. article states that annual maps use a v20191114 succession ruleset and
that Figure 2 visualizes it. The project transcription remains a transcription of the
published figure; its exact date arithmetic, special-class semantics, and underlying
release implementation are not verified by the listed official decision-rules PDF.
**Decision:** keep annual fuel generation blocked. No historical raster was downloaded
or generated, no FireCase/replay/training occurred, and no validation/test data were
inspected. Evidence: [source-gate receipt](../../reports/real-fire-data/cfsds-train-fuel-source-gate.json),
[fuel-vintage review](CFSDS_FUEL_VINTAGE_REVIEW.md), [ADR-029](../specs/DECISION_RECORDS.md#adr-029),
and [S-048](SOURCES.md).

## EXP-020 — TRAIN terrain source-class and weather snapshot provenance, 2026-10-31

For the three already-materialized TRAIN pilot cases only, read NRCan's separate
MRDEM-30-SOURCE COG over each 2 km simulator extent. Each 67×67 source window contained
4,489/4,489 pixels with source code 1 (adjusted Copernicus GLO-30), so all 400 model
cells overlap that source class. NRCan's product specification dates the GLO-30 source
collection to 2011–2015. The current source-class COG is a 2026 snapshot; the saved
manifest does not identify an exact DTM revision, upstream tile checksum, or per-pixel
acquisition date. This is source-category evidence, not proof that the legacy elevation
values were built from byte-identical 2011–2015-only data.

Recomputed the target-blind day-n−1 safe-front centroid coordinates and requested each
case's existing target date from Open-Meteo ERA5-Seamless. All responses resolved to the
same coarse grid point/timezone as the legacy manifests. The target-day temperature
values changed in 24/24 hours in all cases; relative humidity changed in 6/24, 3/24,
and 1/24 hours. Wind speed, wind direction and precipitation matched all 24 values.
`2018_747`'s old 72-hour response was compared only over August 16, its target-date
slice. The reason for historical response changes is unverified. Exact query URLs and
new 24-hour responses are committed as small snapshots with hashes. Legacy manifests,
weather files and FireCases were not modified.

**Decision:** preserve the new replies as immutable input snapshots for a future
rebuild, but do not treat the old cases as target-blind or use this result to pass the
environment/no-action gate. Fuel-vintage validity, exact legacy DTM vintage, full-cohort
weather/provenance, domain fit, event-keyed suppression and no-action replay acceptance
remain open. No case rebuild, simulator replay, calibration, benchmark, training or
heldout inspection occurred. Evidence: [terrain/weather receipt](../../reports/real-fire-data/cfsds-train-terrain-weather-provenance.json),
[pinned response snapshots](../../reports/real-fire-data/weather-snapshots/),
[input QC](CFSDS_TRAIN_INPUT_QC.md), [ADR-030](../specs/DECISION_RECORDS.md#adr-030),
and [S-049](SOURCES.md).

## EXP-021 — TRAIN-only BC incident-status snapshot follow-up, 2026-10-31

Expanded the public-source search for only the three saved 2018 TRAIN perimeter
candidates. The official 405-page Emergency Management BC response package contains
PECC Situation Reports #10 and #11. SitRep #10, sent August 16, lists an August 16
15:00 snapshot with North Baezaeko (C11937) at 2,500 ha/0% contained and Lost Dog
Complex (N12413) at 452.5 ha/out of control. SitRep #11, sent August 17, prints that
same snapshot time but reports C11937 at 4,000 ha/10% and N12413 at 706 ha/out of
control. The two publications therefore provide versioned incident-status estimates,
not a consistent daily perimeter series. The Lost Dog snapshot falls on the CFSDS
`2018_747` target date; the North Baezaeko snapshot is one day after `2018_241`'s target.

A text search of this package returned no N12395 entry. Indexed searches for the three
incident identifiers did not surface a case-specific public BCWS daily action-plan or
dispatch package. This is a bounded public-search result, not proof that unpublished,
unindexed, or request-only records do not exist. Existing local reports remain the only
reviewed public source describing target-day action at candidate N12395. No action
schedule, crew assignment, treatment location, or common CFSDS-to-BC incident key was
found for any saved case.

**Decision:** do not infer `no suppression` from a 0% containment report or an absent
public record; leave all three manifest labels `suppression_status=unknown`. Do not
turn these incident-level area/status estimates into per-cell simulator actions or
ground-truth arrival masks. Preserve report number, publication date, printed snapshot
date/time, and estimate separately for any future visualization. No case, replay,
calibration, benchmark, training, or heldout inspection was performed.

Evidence: [updated operational evidence receipt](../../reports/real-fire-data/cfsds-train-bc-operational-evidence.json),
[source S-046](SOURCES.md), [input QC](CFSDS_TRAIN_INPUT_QC.md), [ADR-032](../specs/DECISION_RECORDS.md#adr-032),
and the [official PECC response package](https://docs.openinfo.gov.bc.ca/Response_Package_PSS-2018-86747.pdf).

## EXP-022 — full TRAIN fuel-class overlay on target-blind pairs, 2026-10-31

Applied the available Canadian FBP v2014b categorical raster to all 1,301 day-pair
records in the full TRAIN target-independent screen. The same fixed 20×20/100 m model
extent was used; it fits 1,295 source rasters. Initial scar and day-n−1 safe-front masks
were built with the project's target-blind `derive_pre_target_state_masks` helper.
Day-n target masks were formed separately and inspected only after the pair/window
selection as a diagnostic. No CFSDS `Firegrowth_groups` table, validation/test raster,
simulator, or agent was opened or run.

For the pre-target scar/front, 701/1,295 windows pass the narrow fuel-class overlay,
64 need review for sub-cell fractional overlap, and 530 fail because an observed cell
overlaps water/nonfuel/ambiguous/unmapped classes. Six source rasters cannot fit the
fixed window. 477 of all 1,301 pairs have a majority-resampled front and target that
are adjacent on the 20×20 grid without touching its edge. Among post-selection target
masks, 930 windows contain an adjacent target pixel; 583 class-pass, 68 need review,
279 fail and 365 have no adjacent target mask inside the crop. These target findings
are diagnostics, not selection criteria.

**Decision:** this expands the fuel overlay to the full target-independent TRAIN
screen, but its 701 passes are not eligible simulator cases. The 2014b vintage and
other inputs remain unverified; the no-action gate remains failed. No annual fuel map,
FireCase, replay, benchmark, calibration, or training was performed. The JSON receipt
records source/code hashes and aggregate outcomes; the compact CSV records one row per
screen pair. See [method/results](CFSDS_FULL_TRAIN_FUEL_OVERLAY.md), [JSON](../../reports/real-fire-data/cfsds-full-train-fuel-overlay.json),
[CSV](../../reports/real-fire-data/cfsds-full-train-fuel-overlay.csv),
[ADR-033](../specs/DECISION_RECORDS.md#adr-033), and [source S-031](SOURCES.md).

## EXP-023 — v20191114 archive burn-scar rules and v2014b member review, 2026-10-31

Inspected the official v20191114 ZIP without downloading its 2,680,409,561-byte map.
HTTP byte ranges retrieved its 65,536-byte tail and 13,417-byte central directory, which
enumerates all 170 members. Only two small members were extracted: the 1,737-byte
`docs/Burn Scar Rules.txt` and a 16,925-byte base FBP classifier script. The rules text
says the burn-scar transition was applied to fires over 50 ha in the most recent NFDB
update dated 2018-07-26; its broad classes are 1–2 years Non-Fuel, 3–5 D-2, 6–21? M-2
C25 and over 21 C-2. O-1 remains O-1; Water/Non-Fuel are retained. It explicitly warns
that the M-2 age interval can vary by region. It also lists historical classes and
raster layer order. The inspected R classifier builds baseline fuel classes and does
not implement year-since-fire transitions; no separately named age-succession program
appears in the exhaustive member-name list.

Inspected all 13 members of the local ignored v2014b ZIP. It contains its raster,
metadata, colour legend, and GIS sidecars, but no separate burn-scar rule file. The
v2014b metadata still does not identify the NFDB/NBAC snapshot cutoff. Therefore the
later release's 2018 NFDB timestamp cannot be transferred to v2014b, and neither ZIP
inspection closes the historical map gate. The region-specific boundary, exact
date/year arithmetic and v2014b lineage remain open. No annual map or case was built.

Evidence: [archive member receipt](../../reports/real-fire-data/canfg-fuel-archive-member-review.json),
[fuel-vintage review](CFSDS_FUEL_VINTAGE_REVIEW.md), [source register S-031/S-032/S-048](SOURCES.md),
[official CanFG directory](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/),
[W.I.S.E. paper](https://doi.org/10.1071/WF26072), and [ADR-033](../specs/DECISION_RECORDS.md#adr-033).

## EXP-024 — W.I.S.E. suppression exclusion and national burn-history dating, 2026-10-31

Rechecked the publisher text of the W.I.S.E. assessment, the official v2014b metadata,
the official current CWFIS FAQ, and NBAC 1972–2024 metadata v20250506. W.I.S.E. reports
removing any fire with recorded suppression in CNFDB because the model does not account
for intervention. This gives a concrete precedent for the eligibility gate: a case with
`suppression_status=unknown` cannot be described as an untreated natural-growth case.
For our three saved 2018 BC candidate crosswalks, two have partial public reporting of
activity at the candidate incident/complex level and the third has only status reports;
none has a complete shared-ID daily action record or proof of no action. Keep all three
labels unknown and exclude them from a clean no-action/agent claim.

The v2014b metadata lists NFDB/NBAC inputs and cites the 2016 NFDB Agency FireData
publication, while giving no burn-record snapshot cutoff. This citation does not prove
that 2016 records were included; it means the `2014b` product label is insufficient to
claim that its scar history predates the 2014–2018 TRAIN events. Current NBAC is an annual
retrospective composite with fire-year and agency date/source/acquisition fields; the
v20250506 metadata says the release added or improved historical polygons and removed
duplicates across years. NBAC can support future reconstruction of prior-fire geography,
but a latest revised composite is not automatically an as-of-target input. v20191114's
2018-07-26 scar-source update remains later than these TRAIN events. In the current
project split, 2019+ outcomes are validation/test; they were not opened and cannot be
used to choose a training source or rescue the TRAIN gate.

**Decision:** require positive evidence for a “no suppression” label before using a
historical case to pass the no-action gate; unknown does not count as none. Preserve
NBAC/NFDB as candidate sources for a documented retrospective prior-burn reconstruction,
not as a proven as-of-target snapshot. Keep current 2014b fuel gate closed; do not inspect
heldout fire outcomes, build annual maps, make cases, replay, or train from this review.

Evidence: [W.I.S.E. method, fuel maps, and cohort filters](https://doi.org/10.1071/WF26072),
[v2014b metadata](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/archive/nat_fbpfuels_2014b_metadata.pdf),
[CWFIS FAQ](https://cwfis.cfs.nrcan.gc.ca/en/faq?wbdisable=true),
[NBAC v20250506 metadata](https://cwfis.cfs.nrcan.gc.ca/downloads/nbac/NBAC_1972to2024_20250506_shp_metadata.pdf),
[sources S-031/S-036/S-037/S-050](SOURCES.md), and [ADR-034](../specs/DECISION_RECORDS.md#adr-034).

## EXP-025 — ERA5-FWI-SN daily-weather paired TRAIN replays, 2026-10-31

Replaced only FFMC, DMC, DC, ISI, BUI and FWI in copies of the three existing 2018
TRAIN simulator inputs with daily ERA5-FWI-SN v2 values at the nearest 0.25-degree
grid cell to the target-blind day-n-1 front location. Each daily code was repeated in
the 24 hourly `Weather.csv` rows for that date; hourly temperature, relative humidity,
wind and precipitation were preserved. Original cases, source weather files, terrain,
fuel, state masks, policy, seed, budget, reset setting and pinned offline simulator
image stayed fixed. The comparison script verified the input hashes and same-start-state
condition before interpreting the paired results.

All six 2018 source files match the Borealis metadata MD5 values. All three paired
replays completed. `2018_1770` changed from 73 to 70 newly burned 100 m cells (IoU
0.1361 to 0.1418); `2018_241` remained 237 cells (IoU 0.0376); `2018_747` remained
66 cells (IoU 0.2187). Every updated run still reached the edge of the 20×20 crop.
These are deterministic input-sensitivity results, not evidence that daily FWI is the
only correct weather source or that the simulator is physically calibrated.

**Decision:** ERA5-FWI-SN v2 is an auditable daily source for future Canadian cases if
the event date, target-blind point, nearest grid cell and daily-to-hourly repetition are
recorded. Keep hourly weather variables separately sourced. Do not overwrite the three
old cases or use this small sensitivity result to close the no-action, fuel-vintage,
spatial-domain or physical-validity gates. The weather correction did not explain the
large spread mismatch: two final masks were identical, one differed by three cells,
and all three still touched the crop edge. `research_ready=false` remains.

Evidence: [ERA5-FWI diagnostic note](ERA5_FWI_SN_DIAGNOSTIC.md), [audit receipt](../../reports/real-fire-data/era5-fwi-sn-2018-pilot-comparison.json),
[paired replay receipt](../../reports/real-fire-data/era5-fwi-sn-2018-weather-replay-comparison.json),
[Benoit et al. 2026](https://doi.org/10.5194/essd-18-5995-2026), and [Borealis dataset](https://doi.org/10.5683/SP3/4B18XZ).

## EXP-026 — Alberta suppression-source schema and access audit, 2026-10-31

Rechecked the official Alberta historical-wildfire catalogue, its 2006–2025 CSV/dictionary
links, and the public provincial Historical Wildfires ArcGIS REST service. The catalogue
describes fire-level staffing/resources and the dictionary identifies fields for initial
action and physical firefighting start; the direct CSV remains blocked by HTTP 403 / a
Cloudflare verification interstitial in this environment. The official spatial service
does load, but the inspected historical point schema has reported status/status-date and
area/cause fields, not the initial-action time or crew/resource columns needed to mark a
target day as pre-suppression. It is not a substitute for the CSV.

The three saved pilot events are BC crosswalk candidates, not Alberta events, so even a
successful Alberta download would not resolve their suppression evidence. The potential
Alberta route is still worth pursuing for future TRAIN fires: after obtaining the official
table, match by fire number/year and location, then conservatively require a target date
strictly before the recorded physical-firefighting start date. Same-day or missing dates
remain unknown because CFSDS does not provide within-day arrival times. No third-party
mirror was treated as official evidence; no record was joined, downloaded or promoted to
an eligibility label.

**Decision:** retain `suppression_status=unknown` for all existing cases; no status or
perimeter snapshot proves no physical action. For this environment, the suppression gate
remains blocked pending an authoritative event-keyed action table (or a different
pre-registered study design whose claim does not rely on untreated historical growth).
The service schema and source-access outcome are recorded in [S-043/S-052](SOURCES.md).

Evidence: Alberta [official catalogue](https://open.canada.ca/data/en/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e), [official wildfire data page](https://www.alberta.ca/wildfire-maps-and-data),
[historical wildfire REST service](https://geospatial.alberta.ca/mimas/rest/services/wildfire/historical_wildfires_data/FeatureServer), [S-043/S-052](SOURCES.md), and [ADR-036](../specs/DECISION_RECORDS.md#adr-036).

## EXP-027 — pivot to BurnMD + SimFire/SimHarness, 2026-11-01

The project instruction was to alter the research design so it fits the most useful real
data and the actual wildfire-control question. A primary-source review found that BurnMD
describes 308 western-US medium fires from 2018–2021 with perimeter histories and
operational mitigation-line records. SimFire/SimHarness provide a paired simulator/RL
workflow with real LANDFIRE fuel/terrain and line-placement actions. The published SimFire
example used LANDFIRE 2019 near the 2020 Mineral Fire; we select Mineral Fire only as the
first technical feasibility candidate, not as a final heldout case.

This better matches a resource-limited line-placement study than forcing CFSDS daily burn
maps into a small Canadian FBP/Cell2Fire input. The revised validation check replays
documented historical lines at their times before comparing alternative policies. It does
not ask for an untreated/no-action trajectory when suppression may have occurred. Agent
inputs remain limited to information available at the decision time, and historical
perimeters/actions remain separate reference data.

Important unresolved checks: the 345 MB BurnMD archive is in Git LFS but a separate data
license was not found; its paper reports approximate/missing timestamps, line-status
filtering needs, assumed work rates and no included weather field. SimFire 2.0.1 declares
Python ~3.9 while the project environment is 3.12, and the SimFire paper leaves detailed
validation as future work. No archive was downloaded, no package installed, no simulator
run, no conversion and no training occurred in this literature/design review.

**Decision:** adopt BurnMD as the preferred primary data candidate and SimFire/SimHarness as
the preferred backend candidate, conditional on bounded feasibility gates TASK-020–023.
Archive the previous CFSDS/Cell2Fire workflow without discarding its results. Next step is
inspect/download and license/schema audit, then an isolated Python 3.9 runtime and one
Mineral Fire replay. See [new design](BURNMD_SIMFIRE_PIVOT.md), [ADR-037](../specs/DECISION_RECORDS.md#adr-037--pivot-to-burnmd-simfire-and-historical-action-replay-2026-11-01), and [sources S-053–S-056](SOURCES.md).

## EXP-028 — SimFire standalone Python 3.9 functional smoke, 2026-11-01

Installed official SimFire 2.0.1 at upstream source commit
`04905b19fe8c10dc08d64faddd00303e0561bb66` into an isolated macOS ARM64/Python 3.9.25
venv. A dependency-only freeze is saved at
[`requirements/simfire-macos-arm64-py39.freeze.txt`](../../requirements/simfire-macos-arm64-py39.freeze.txt).
The upstream import of `pkg_resources` required `setuptools<81`; it is pinned in the
freeze. The existing project Python 3.12 environment was not modified. SimHarness/RLlib
was not installed.

Ran `scripts/run_simfire_demo.py --steps 30` with upstream `functional_config.yml`,
Pygame dummy display and the default seeded functional landscape. Run completed on a
225×225 grid (50,625 cells): 1,687 `BURNED`, 436 `BURNING`, 48,502 `UNBURNED`; no
mitigation actions/agents. It produced a 30-minute GIF, final-state map and JSON receipt.
The small artifacts are preserved in
[`simfire-functional-demo/`](../../reports/environment-setup/simfire-functional-demo/).

This is a **technical simulator smoke only**: no BurnMD file or LANDFIRE data was read,
no historical event was initialized, no policy/agent or SimHarness was run, no training
was performed, and the counts are not a scientific or real-world effect. It proves the
selected standalone simulator imports, advances a fire map and emits visual output on
this host. This closes only the local standalone portion of TASK-021; it does not clear
the BurnMD license, historical replay or RL training gates.

At the time of this log entry, the public 362,131,110-byte BurnMD Git LFS archive was
being downloaded locally into ignored `data/raw/burnmd/`; its pointer SHA-256 is
`4eefcbfdabce4966d68e0009e8a4b88dd34294a2cb5dee6aea84dd017eb334c7`. No archive contents
or data-use license have been confirmed yet. See [runtime record](SIMFIRE_ENVIRONMENT.md),
[receipt](../../reports/environment-setup/simfire-functional-demo/receipt.json),
[EXP-027](#exp-027--pivot-to-burnmd-simfiresimharness-2026-11-01), and [S-053–S-058](SOURCES.md).

## EXP-029 — BurnMD Mineral case and LANDFIRE API compatibility audit, 2026-11-01

Verified the local BurnMD ZIP against the official LFS pointer SHA-256 and inspected
Mineral's polygon, line and point shapefiles directly from the archive. They contain 11,
249 and 58 records respectively; the 318 geometries are non-empty and valid. The event
reports a 2020-07-13 start and 2020-07-26 containment; its 11 perimeter observation dates
span 2020-07-15 to 2020-07-22. The line layer has 121 completed-dozer, 25 completed-hand,
40 proposed-dozer and 27 uncontrolled-fire-edge records. However, `LineDateTi` is null on
all 249 rows and `Mitigation` is an empty list for all 249. SimFire's historic loader
calculates line timing from `CreateDate` at fixed 20 ft/min dozer and 2 ft/min hand-line
rates, which differs from the paper's fuel/topography-dependent estimates. Mineral cannot
currently support a reliable historical-action replay.

The archive has 243 unique state/year/fire folders, whereas the paper reports 308 medium
fires. The cause of the 65-count discrepancy is unknown. The repository has an Apache code
license, but no dataset-specific use notice was found in the inspected repository or ZIP;
do not redistribute the archive or derived map pending rights review.

The bundled SimFire `landfire==0.5.0` client calls the retired pre-2025 ArcGIS endpoint;
the official LFPS service now documents `/api/job/submit`, email, status polling and an
output URL. Added `scripts/prepare_mineral_landfire.py` to target the current API and write
its TIFF into the SimFire cache. Its dry-run succeeds. The adapter also was corrected to
derive a fixed 128×128×30 m tile from the recorded ignition rather than later line/perimeter
extent. SimFire's pinned code pads a lower-right corner by 100 arc-seconds (about 3.1 km
north-south), despite an upstream comment describing about 90 m; the adapter mirrors the
actual code so the cache path matches. A separate metadata-only report and a local-only QA
map were produced.

The adapter has not made an actual LANDFIRE request because no contact email is set and
the host had only 29 MiB free. The LF2016 FBFM13 fallback is four years before Mineral and
not a final scientific fuel-vintage decision. See [audit report](MINERAL_CASE_AUDIT.md),
[receipt](../../reports/real-fire-data/mineral-case-audit.json), [ADR-039](../specs/DECISION_RECORDS.md#adr-039--mineral-is-a-spatial-fixture-only-pending-line-time-and-landfire-gates-2026-11-01),
and [S-059–S-061](SOURCES.md).

## EXP-030 — scenario-based design and FPA-FOD source review, 2026-11-01

The missing Mineral line times made historical-action replay a poor prerequisite for the
question the project actually wants to answer: whether fine-tuning helps an agent control
fire spread in the simulator when its scenario distribution comes from real incidents.
Reframed the main experiment to use real ignition locations/dates and separately sourced
fuel, terrain and weather as scenario inputs. SimFire generates spread and reward; future
perimeters and completed fire sizes remain separate references, not input or reward. This
can test policy adaptation in the simulator without claiming a counterfactual real-world
hectare reduction.

Reviewed the current official USFS FPA-FOD ArcGIS service. Its seventh-edition sixth update
covers 1992–2024 with about 2.66 million incident points and fields for record ID, discovery
date/time, fire size, coordinate and possible perimeter/incident-report crosswalk IDs. Its
metadata warns that locations may only be precise to a one-square-mile PLSS section; the
scenario must preserve coordinate precision, not treat every point as exact GPS. The
current service can update; a versioned Research Data Archive record is preferred for a
frozen cohort. Dataset-specific reuse conditions still need review.

The NeurIPS 2023 WildfireSpreadTS dataset has 607 fires and CC BY 4.0 terms, but the full
archive is 48.4 GB. It is a good separate daily-spread benchmark, not a practical first
download on this host and not a ready-made SimFire action dataset. Recorded in [S-062/S-063](SOURCES.md).

Added a versioned
[scenario manifest schema](../../data/manifests/simfire-scenario.schema.json),
[blank template](../../data/manifests/simfire-scenario.template.json),
[plain-language conversion pipeline](REAL_IGNITION_SCENARIO_PIPELINE.md), and the current
design/backlog/handoff. Updated the Mineral LANDFIRE dry-run adapter to center a fixed map
on ignition, not future event geometry. `--dry-run`, Python compilation and JSON parsing
passed. No FPA sample was downloaded; no LANDFIRE job was submitted; there is no verified
real-input SimFire run, SimHarness/RLlib installation or training result. The host had 29
MiB free and `LANDFIRE_EMAIL` was unset.

**Decision:** adopt the scenario-derived simulator experiment in [ADR-040](../specs/DECISION_RECORDS.md#adr-040--train-on-real-ignition-conditions-with-simulated-actions-2026-11-01).
Historical line replay is optional evidence, not a prerequisite. The next task is a small,
versioned FPA-FOD event cohort and the first verified fuel/terrain/weather scenario.

## EXP-031 — first FPA-FOD to SimFire candidate card, 2026-11-01

Queried the official current USFS FPA-FOD service for a reproducible single record,
Dixie Fire 2021 (`FOD_ID=401019270`, `FPA_ID=INF-2021-CABTU-009205`,
`MTBS_ID=CA3987612137920210714`). The returned 455-byte GeoJSON contains a point requested
in EPSG:4326, discovery date 2021-07-13, reported HHMM `1615`, final size 963,309 acres,
and the incident/perimeter join identifiers. The published metadata says event locations
can be only as precise as a one-square-mile PLSS section; this record has no event-specific
accuracy field. The discovery-time timezone is not specified in our source review and is
left null in the manifest. The official versioned archive says the data may be used without
extra permission or fee when the Short (2026) citation is included ([S-064](SOURCES.md)).

Added `scripts/build_fpa_fod_scenario.py` to fetch one pinned FOD_ID or rebuild from a local
GeoJSON, retain a small hashed source snapshot, convert acres to hectares only in a
reference-only field, and create a `simfire-scenario/1.0` card. The record maps to a fixed
128×128 grid at 30 m with the ignition in the centre. Fuel, elevation and weather are
explicitly `missing`; readiness is `candidate`, split is `unassigned`, and final area/MTBS
remain outside agent input/reward. The card and the 455-byte source snapshot are committed;
the same raw download remains ignored under `data/raw/fpa-fod/`.

Generalized `scripts/prepare_mineral_landfire.py` to accept a scenario manifest and produce
the matching current-LFPS AOI/SimFire cache path. Dixie dry-run returned top-left
`(39.89378816280924, -121.39663741862155)`, bounds
`[-121.396637418622, 39.830454829417, -121.333304085229, 39.893788162809]`, and the
2021 cache year. Updated `scripts/run_simfire_operational_smoke.py` so it can consume the
same scenario, configure its grid/ignition, and use a timestamped result directory. Its
actual run was not started because the TIFF is absent.

Validation for this work: Python compilation for all new/changed scenario scripts passed;
the offline candidate rebuild passed; both the default Mineral dry-run and Dixie
scenario-manifest dry-run printed their expected fixed AOIs; the parsed source record and
manifest paths/hashes agree. The last disk check showed 3.0 GiB free (replacing the stale
29-MiB status snapshot), but `LANDFIRE_EMAIL` remains unset. No LANDFIRE job, historical
weather fetch, real-raster smoke, RL install, training, or physical validation occurred.

**Decision:** treat Dixie as a development fixture only, not a scientifically sampled fire
or a train/test example ([ADR-041](../specs/DECISION_RECORDS.md#adr-041--fpa-fod-dixie-is-only-the-first-scenario-adapter-fixture-2026-11-01)). The next concrete gate is real fuel/terrain and weather input sourcing for this card, followed by a real-input map/animation.

## EXP-032 — point-role and grid semantics made explicit, 2026-11-01

A second review of the FPA-FOD record-to-SimFire bridge found that the source provides an
incident reference coordinate, but does not establish that this is an exact fire-start GPS
point. The prior candidate card called it an ignition without carrying that distinction.
The grid also follows SimFire's fixed degrees-per-cell conversion, so its "30 m" is a
nominal simulator cell size rather than a latitude-independent ground distance.

Updated the shared scenario schema/template and rebuilt the Dixie card to store
`event.location_wgs84.role=incident_reference_point`, point-accuracy note, a nominal-grid
note and `fire_behavior.seed_cell`. The LANDFIRE adapter checks that the recorded grid
origin matches the fixed-size location rule. The operational smoke runner validates and
uses the seed cell from the manifest and records the location role/accuracy in its receipt.
Current navigation was shortened so the root page leads to the live design, candidate,
backlog and evidence; previous CFSDS documents remain reachable as an archive.

The offline rebuild produced the expected FOD_ID and candidate manifest with the point role, nominal grid note and seed cell. Both Dixie and Mineral LANDFIRE dry-runs passed; Python compilation passed for the changed scenario scripts; the strict knowledge-bundle check passed for 86 Markdown files; `git diff --check` passed. The real raster request is still waiting for the actual requester email; there is still no real-fuel/weather smoke or RL result.

## EXP-033 — real layers fetched and loaded by SimFire, 2026-11-01

Revisited the data-to-simulator bridge against the actual source field meanings. The FPA-FOD
Dixie point remains an incident reference with unknown event-specific accuracy, so it is
used only as a provisional scenario anchor. Replaced the old degree-based grid in the
scenario builder with a fixed 128×128 grid in the local UTM zone, aligned to exact 30 m
boundaries. Dixie uses EPSG:32610, bounds `[636690, 4413360, 640530, 4417200]` meters,
and stores the source point cell separately from the original coordinate.

Added `scripts/fetch_simfire_real_inputs.py`. It requests two small public LANDFIRE
ImageServer exports without the LFPS email workflow: LF2016 FBFM13 for fuel and LF2020
elevation for terrain. Both arrive as one-band signed-16 GeoTIFFs on the same EPSG:32610
grid with nearest-neighbor sampling. The fuel tile contains FBFM13 codes
`1,2,4,5,6,7,8,9,10,91,98,99`; no unmapped code, NoData cell or CRS/bounds mismatch was
found. Elevation values are 456–1385 m. The source fuel map predates Dixie by five years,
so it is a pre-event candidate rather than a verified event-year map.

Fetched a 24-hour ERA5 series for 2021-07-13 at the source location in UTC: temperature,
relative humidity, 10 m wind speed/direction and precipitation. Kept the response locally
with its SHA-256. It is not fed to SimFire: source discovery HHMM lacks a confirmed timezone,
10 m wind is not midflame wind, and air RH is not dead-fuel moisture. The 30-minute smoke
uses SimFire example wind/moisture values and labels them as demonstration conditions.

Added `scripts/run_simfire_real_input_smoke.py`. It uses SimFire's FBFM13-to-fuel mapping
and meters-to-feet elevation conversion, while bypassing the pinned simulator's retired
network loader. The 30-minute run completed with the actual fuel and elevation arrays and
generated an input-layer map, final-state map and GIF. Reproduction receipt and small
visual outputs are in
[`simfire-dixie-real-input-smoke`](../../reports/real-fire-data/simfire-dixie-real-input-smoke/).
Raw TIFF/ERA5 files stay ignored under `.local/real-input-dixie/`; their paths and hashes
are in the manifest/receipt. Added rasterio 1.4.3 to the local SimFire environment freeze.

**What this closes:** public data retrieval, exact projected grid creation, GeoTIFF checks,
class/unit mapping into SimFire, and one real-layer integration run. **What it does not
close:** year-specific fuel validation, historical-weather-to-SimFire mapping, ignition
point accuracy, RL runtime, training, held-out comparison or physical validation. Dixie
remains a development fixture, not training data. See
[ADR-043](../specs/DECISION_RECORDS.md#adr-043--use-a-projected-grid-and-do-not-force-weather-variable-equivalence-2026-11-01)
and sources [S-065–S-066](SOURCES.md).

## EXP-034 — 80 real FPA-FOD cases and LANDFIRE maps, 2026-11-01

Built cohort `fpa-fod-western-us-2018-2024-v2` from the official USFS occurrence service.
Screened the 2018, 2019, 2023 and 2024 pools, then selected 20 per year by stable hash rank
with a preference for state diversity. The screening pools were 146, 62, 56 and 109
records; the cohort contains 40 train / 20 validation / 20 test incidents, split by full
fire and by year. Selection requires a reported size of at least 5,000 acres, date,
coordinates and an MTBS ID for display-only context.

Created a 128×128 projected 30 m grid for every case, acquired LF2016 FBFM13 for
2018–2019, LF2022 FBFM13 for 2023–2024 and LF2020 elevation. All 80 fuel/terrain pairs
passed the implemented CRS, bounds, shape, source code/value and checksum verification.
The seed-selection pass found the reported point cell burnable in 71 cases and selected a
nearby burnable proxy in 9 cases; the proxies were within approximately 62 m. No observed
final area/perimeter was used to choose a start cell.

Small source snapshots, manifests, per-case metadata, hashes and reports are in Git. The
GeoTIFFs remain in ignored `.local/simfire-cohort-v2/`. This is a reproducible acquisition
and input-format result, not per-event fuel survey or physical spread validation. The
source FPA-FOD coordinate retains its incident-reference/uncertainty label.

**Weather result:** new-cohort historical weather is 0/80. The input rerun used
`--skip-weather` because the Open-Meteo host was not resolving in the runtime. The final
receipt says fuel/terrain ready and weather open, not training ready.

Evidence: [`simfire-fpa-fod-cohort-v2.json`](../../data/manifests/simfire-fpa-fod-cohort-v2.json),
[source snapshots](../../reports/real-fire-data/fpa-fod-simfire-cohort-v2/),
[input receipt](../../reports/real-fire-data/simfire-cohort-v2-input-acquisition.json),
[seed receipt](../../reports/real-fire-data/simfire-cohort-v2-seed-selection.json),
[ADR-044](../specs/DECISION_RECORDS.md#adr-044--versioned-80-incident-cohort-with-time-separated-splits-2026-11-01).

## EXP-035 — Gymnasium SimFire cohort smoke, 2026-11-01

Installed a separate Python 3.9-compatible RL dependency set into the ignored SimFire
venv, pinned as `requirements/simfire-rl-macos-arm64-py39.freeze.txt`. Added a Gymnasium
adapter and map CNN feature extractor. Ran one real-raster scenario from each split. The
adapter validated raster hash/CRS/bounds/dimensions, loaded fuel and terrain, initialized
SimFire on the projected 30 m grid using 98.43 ft per cell, placed one fireline point,
advanced the environment, and left only no-op legal after spending the budget. A
MaskablePPO policy initialized and selected a legal train action.

The run used explicitly marked demo atmosphere values (wind speed 7, direction 90°,
moisture 3%). It did not load historical weather and did not call `learn()`. It generated
small map/GIF images and JSON receipts for the three splits. The adapter's point action is
instant and can be placed anywhere; no travel/construction-time model exists yet.

**Result:** the real-input-to-RL software path is smoke-runnable, but no learned policy or
historical-weather policy comparison exists. This is not physical validation. Evidence:
[adapter](SIMFIRE_RL_ADAPTER.md), [receipt and visual outputs](../../reports/real-fire-data/simfire-cohort-v2-gym-smoke/),
[ADR-045](../specs/DECISION_RECORDS.md#adr-045--implement-a-simple-auditable-simfire-gymnasium-adapter-2026-11-01).

## EXP-036 — historical weather fetch retry from cohort runtime, 2026-11-01

Retried an exact hourly archive query for the first 2018 TRAIN case (`FOD_ID 400310930`,
Owyhee; 2018-07-21). The runtime returned `curl: (6) Could not resolve host:
archive-api.open-meteo.com`; the browser research tool also reported that the API URL was
not accessible. No response JSON was saved and no weather values were fabricated. The
existing 2021 Dixie ERA5 response is a different one-off example, not a substitute.

**Result at that point:** Open-Meteo retrieval failed from this runtime. That blocked source
route, not all public weather data. The later gridMET retrieval is documented separately in
EXP-037; gridMET supplies daily historical context but does not resolve the simulator
wind/moisture/time mapping. Evidence: [failed Open-Meteo attempt](../../reports/real-fire-data/simfire-cohort-v2-input-acquisition.json),
[ADR-046](../specs/DECISION_RECORDS.md#adr-046--keep-historical-weather-training-gated-until-weather-is-fetched-and-mapped-2026-11-01),
[Open-Meteo API docs S-069](SOURCES.md).

## EXP-037 — 80-case gridMET historical context acquisition and QC, 2026-11-01

Downloaded eight daily gridMET variables through NCAR GDEX for the reported date and
incident-reference point of every case: 10 m wind speed/direction, maximum air temperature,
minimum/maximum relative humidity, daily precipitation, NFDRS model-G 100-hour fuel
moisture and energy-release component. The first pass succeeded for 79 cases; one transient
HTTP 503 on the Turkey Fire `fm100` request was retried alone. Final result: **80/80 cases,
zero failures**. Each small JSON records the requested and sampled grid coordinates,
provider variable/unit, URL and response-day label; per-file SHA-256 is pinned in the case
manifest and acquisition receipt.

The QC summary re-opened every case file, verified all 8 variables and finite values,
matched all file hashes against both receipts and the cohort manifest, and confirmed that
each variable in a case came from the same sampled grid cell. Counts are 40 train / 20
validation / 20 test; [summary JSON](../../reports/real-fire-data/simfire-cohort-v2-gridmet-summary.json)
and [overview figure](../../reports/real-fire-data/simfire-cohort-v2-gridmet-overview.png)
show data spread. Example units are m/s for wind, degrees clockwise from north for
direction, K for temperature, % for RH/FM100, and mm for precipitation.

**What this closes:** there is real public daily weather context for all 80 incident/date
cases, saved in a compact reproducible format. **What it does not close:** this is a daily
~4 km estimate, not an hourly fire-start observation. FPA-FOD coordinates are incident
references, discovery HHMM is unzoned here, gridMET days use MST, and the 10 m wind / air RH
/ 100-hour model-G moisture do not directly equal SimFire midflame wind / fine-fuel moisture.
At the time EXP-037 closed, the Gymnasium adapter did not yet load these values and the
smoke still used marked demo atmosphere. EXP-038 below records the later explicit mapping;
no agent training was started.

Evidence: [acquisition receipt](../../reports/real-fire-data/simfire-cohort-v2-gridmet-weather.json),
[per-case files](../../data/processed/simfire-cohort-v2-gridmet-weather/),
[QC/summary generator](../../scripts/summarize_gridmet_cohort.py), [overview figure](../../reports/real-fire-data/simfire-cohort-v2-gridmet-overview.png),
[ADR-047](../specs/DECISION_RECORDS.md#adr-047--use-gridmet-as-daily-context-keep-simfire-mapping-explicit-2026-11-01),
[S-071–S-072](SOURCES.md).

## EXP-038 — map daily gridMET context into explicit SimFire proxy inputs, 2026-11-01

Generated one versioned proxy for each of the 80 cases and checked its source-weather hash
against the case manifest. The mapping records formulas and assumptions: gridMET 10 m wind
as an approximate 20 ft reference, nominal WAF 0.3, meteorological wind-from rotated to
SimFire wind-toward, and Simard EMC from daily maximum temperature/minimum RH as a fuel
moisture proxy. Original weather remains unchanged. WAF alternatives 0.1/0.3/0.5 were run
on one case from each split; all nine receipts preserve the same case/source hashes and show
wind changing proportionally while direction and moisture remain stable.

**Result:** 80/80 SimFire proxy inputs exist and pass checksum/config loading; exact hourly
historical replay remains 0/80. This is an executable data transformation, not proof that
the weather proxy equals ignition-time midflame wind or fine-fuel moisture. No agent learning
was run. Evidence: [mapping report](../../reports/real-fire-data/simfire-cohort-v2-gridmet-simfire-mapping.json),
[sensitivity report](../../reports/real-fire-data/simfire-cohort-v2-gridmet-waf-sensitivity.json),
[mapping script](../../scripts/map_gridmet_weather_to_simfire.py), and [ADR-048](../specs/DECISION_RECORDS.md#adr-048--set-a-30-m-cell-duration-and-protect-the-test-smoke-case-2026-11-01).

## EXP-039 — set a 30 m cell-duration parameter and probe no-action episodes, 2026-11-01

An initial full-horizon smoke using SimFire's stock four-frame fire-pixel duration ended
Owyhee after 8 simulated minutes with two burned cells. Direct one-minute inspection showed
that a new adjacent cell reached the 30 m/98.43 ft burn threshold only after three updates;
the next front accumulated at a slower rate and went out before crossing another cell.
SimFire defines the duration as the number of update frames for which one pixel can remain
on fire (S-073). We therefore made the adapter setting explicit at **15 one-minute updates**
to accommodate slower spread across this project's 30 m cells. This is an engineering
configuration, not a calibrated physical parameter.

With no fireline and WAF 0.3, deterministic no-op horizon probes produced:

- Owyhee, TRAIN: 675 simulated minutes, 8,792 burned 30 m cells, natural termination.
- Hayden, VALIDATION: 720 minutes, 1,059 cells, horizon truncation.
- Larch Creek, TEST: 84 minutes, 24 cells, natural termination.

These contrasting outcomes demonstrate that the interface can produce multi-hour and
shorter episodes; they do not validate historical burned area or action effectiveness.
Larch Creek has been opened during adapter/configuration troubleshooting and is excluded
from the future final benchmark, leaving 19 unopened test incidents. The reusable no-op
script, receipts, and map images are in [no-op horizon probes](../../reports/real-fire-data/).
No learning, checkpoint update, or policy training occurred. See [adapter](SIMFIRE_RL_ADAPTER.md),
[status](../STATUS.md), [ADR-048](../specs/DECISION_RECORDS.md#adr-048--set-a-30-m-cell-duration-and-protect-the-test-smoke-case-2026-11-01),
and [SimFire configuration source S-073](SOURCES.md).

## TASK-025 — freeze the SimFire benchmark and prepare a non-training evaluator, 2026-11-02

Recorded the policy comparison contract before any policy learning: no-op, deterministic
front-edge rule, generic base MaskablePPO and a copy fine-tuned on the 40 TRAIN incidents.
Fixed the per-incident settings, five paired environment seeds, primary simulated-area
measure, validation checkpoint selection, equal-incident weighting, incident-cluster
bootstrap and final TEST gate in a versioned JSON config and research protocol. Larch Creek
remains excluded from the final test membership.

Added `scripts/evaluate_simfire_benchmark.py` for an input/hash preflight and inference-only
policy runs. Its default preflight opens only VALIDATION, initializes one observation, and
does not advance the simulator. TEST runs require two explicit flags and both model
checkpoints. The runner has no `learn()` path and writes fresh receipts under ignored
`.local/` output. Pure tests cover membership integrity, heuristic masking/tie-breaking and
paired incident summaries.

This protocol/task update is not a simulation experiment or physical validation. No
FPA-FOD/SimFire policy training, project checkpoint creation, or evaluation on the 19
reserved TEST fires was performed. During verification, the legacy full test suite did run
its 16-step `.learn()` smoke on a tiny synthetic `GridFire` fixture; it saved a checkpoint
only in a temporary directory that the test removed. The validation preflight verified all
20 validation input packages and initialized Hayden with zero simulator steps; no TEST
input was opened. Future no-training sessions must skip
that test (as now documented in `AGENTS.md`). The first full-suite invocation also found an
incorrect expected value in the new paired-summary test; that arithmetic expectation was
fixed and the six focused evaluator tests pass. The full suite was not rerun to avoid
repeating the synthetic learning call. The generic PPO training recipe, fine-tuning budget,
and physical review of weather/spread assumptions remain open. The saved [validation
preflight receipt](../../reports/real-fire-data/simfire-benchmark-validation-preflight-20261102.json)
records 20/20 validation input checks, a legal no-op, zero advanced simulation steps, and no
test inputs opened. See [protocol](SIMFIRE_EVALUATION_PROTOCOL.md),
[runner](../../scripts/evaluate_simfire_benchmark.py), [ADR-049](../specs/DECISION_RECORDS.md#adr-049--freeze-the-simfire-policy-comparison-contract-2026-11-02),
and [status](../STATUS.md).

## TASK-026 — NIROPS progression source audit for the physical validation gate, 2026-11-02

Identified the latest USFS National Infrared Operations (NIROPS) perimeter progression
dataset as a candidate independent check for SimFire spread. The current Mendeley v2 record
describes 12,705 timestamped IR perimeters across 737 western-US incidents from June 2020 to
November 2024, with UTC timestamps and WGS84 geometry. Its 2020–2024 coverage overlaps the
cohort's 2023 VALIDATION and 2024 TEST years, but no exact incident match has been verified.
The version 1 page showed a 1.62 GB archive; the v2 size is unconfirmed. No data were
downloaded and no TEST perimeter geometry was opened.

Recorded the main limits before proposing use: NIROPS coverage is selective and can start
after ignition; observations are active-fire extents, not complete cumulative burn records
or untreated counterfactuals; irregular acquisition and unrecorded suppression can confound
spread comparisons. The current SimFire adapter also starts from a single FPA-FOD reference
cell rather than an observed perimeter. The SimFire paper's SimHarness demonstration used
DQN and included an unmitigated final map in the observation, so it is not copied as a
direct PPO recipe or validation proof. Kept the benchmark cohort/test membership unchanged.

TASK-026 remains open. Its next operation is a metadata-first, VALIDATION-only 2023
crosswalk, followed by a check of geometry meaning, timestamps, suppression evidence and
whether an initial-perimeter importer is necessary. Training remains prohibited in this
phase. See the [physical validation gate](SIMFIRE_PHYSICAL_VALIDATION_GATE.md),
[source records S-074/S-075](SOURCES.md), and [backlog](../BACKLOG.md).

### TASK-026 follow-up — exact incident-code crosswalk, 2026-11-02

Inspected the small v2 time-series-chart archive and author-code member; the full v2 archive
size is 1,735,431,121 bytes, while no raw perimeter archive was downloaded. Screened the
frozen 20-case 2023 VALIDATION cohort against NIROPS chart incident codes and FPA-FOD
`FPA_ID`s. Eight cases have an exact normalized incident-code match, with state and fire
name also agreeing. Three extra same-name/state candidates (Turkey, Beehive, Pearch) have
different incident codes and are rejected. The reproducible output is
[`nirops-validation-id-crosswalk-20261102.json`](../../reports/real-fire-data/nirops-validation-id-crosswalk-20261102.json).

Visually reviewed only the Hayden chart. Its charted area rises from about 3,000 acres on
2023-07-21 to about 24,800 acres on 2023-08-31, near the FPA-FOD reported 24,706 acres; the
chart is an area summary, not a map. An unchanged copy is saved at
[`hayden-area-progression.png`](../../reports/real-fire-data/nirops-validation-charts/hayden-area-progression.png)
under the dataset's CC BY 4.0 license, with attribution in the crosswalk receipt. The
date/area readings are approximate and cannot
establish polygon alignment. No perimeter geometry, TEST content, or simulator step was
opened or advanced. No training or policy evaluation ran. TASK-026 stays open for obtaining
the eight validation polygons, checking their timestamps/meaning and suppression context,
and establishing whether SimFire can import an observed perimeter without leaking later
observations to the policy. See [gate details](SIMFIRE_PHYSICAL_VALIDATION_GATE.md).

### TASK-026 follow-up — archive structure and map-size gate, 2026-11-02

Read only the last 4 MiB of the raw geometry ZIP using an HTTP range request, then parsed its
central directory. The archive contains one shapefile, not incident-specific ZIP members; its
compressed `.shp` stream is 1,387,126,470 bytes and expands to 2,067,807,444 bytes. The
geometry payload and `.dbf` attributes were not opened, so no incident shapes were identified
or inspected. At the time of the check the machine had 699 MiB free, less than the archive;
the author-documented NIFC FTP root returned 404, and no specific incident subfolder has yet
been checked. See the [archive screen receipt](../../reports/real-fire-data/nirops-geometry-archive-screen-20261102.json).

Separately audited only the 20 frozen 2023 VALIDATION scenario manifests. Their current
128×128 cells at 30 m cover at most 3,643.72 acres if every cell burns. All 20 FPA-FOD
reported final areas are larger: 5,169–81,148 acres, with a 9,209-acre median. The square
cell counts in the receipt are area-only lower bounds; real perimeter shapes and map margins
can require larger extents. Thus the current crop cannot support a whole-fire extent/area
claim, though a deliberately bounded local fireline task remains possible. Reproduction is
available in [`audit_simfire_validation_grid_capacity.py`](../../scripts/audit_simfire_validation_grid_capacity.py)
and its [receipt](../../reports/real-fire-data/simfire-validation-grid-capacity-20261102.json).

This changes TASK-026's next gate: first decide whether to enlarge the physical map and
reacquire aligned fuel/elevation layers, or explicitly narrow the research question to one
local segment; then obtain and inspect only the matched 2023 VALIDATION polygons. The raw
archive did not make that decision for us. No geometry payload, test data, simulation step,
policy evaluation or training was run.

### TASK-026 follow-up — public USFS final perimeter, 2026-11-02

Checked the official public USDA Forest Service 2023 perimeter layer as a smaller alternative
for final shapes. An exact Hayden record was found by its incident name and matched the
crosswalk code `ID-SCF-023084`; its feature is `2023-IDSCF-023084`, categorized as Final
Wildfire Perimeter. The source shows 24,706 `totalacres` and 24,730.34 `gisacres`, consistent
with the FPA-FOD final area. One validation geometry page was opened for provenance/availability
inspection but the polygon was not saved or aligned with SimFire. The layer returned one final
record for Hayden, not a sequence of daily progression shapes.

The numeric `perimeterdatetime` is 2023-08-30 22:52 UTC if interpreted as UTC, while the
feature's comment says an IR flight at 22:52 MDT, which converts to 2023-08-31 04:52 UTC. Do
not use this field for a timed replay until its timezone semantics are resolved. The NIFC
landing page now documents that the older `/public/incident_specific_data` path moved to
`/protected/incident_specific_data` on 2026-05-04 and that protected content requires FAMAuth.
Therefore the immediate next step is to screen the same public USFS layer for the other seven
validation matches and treat it only as final perimeter coverage; progression still needs
NIROPS access or another time-series source. See [USFS screen receipt](../../reports/real-fire-data/usfs-hayden-final-perimeter-screen-20261102.json),
[NIFC archive screen](../../reports/real-fire-data/nirops-geometry-archive-screen-20261102.json),
and [the gate](SIMFIRE_PHYSICAL_VALIDATION_GATE.md). No TEST geometry, simulation step,
policy evaluation or training was accessed/run.
