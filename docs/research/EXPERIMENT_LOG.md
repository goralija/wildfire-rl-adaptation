---
type: Experiment Log
title: Experiment log
---
# Experiment log

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
The figure does not specify exact elapsed-year arithmetic or special-class behavior,
and the actual v20191114 rules artifact has not been checked. The official v2014b
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
