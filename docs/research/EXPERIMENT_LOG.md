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

## EXP-006 — FPA-FOD ↔ FEDS-CONUS ↔ FLE crosswalk, 2026-11-03

Read-only indexed HTTP Range audit of the 60-case, test-excluded FPA-FOD manifest
(40 train in 2018/2019; 20 validation in 2023). Match rule fixed before reading endpoint
results: FEDS `t_st` date within -1/+2 days of FPA discovery date, within 3 km of the
FPA reported point, with exactly one candidate; no final area/perimeter or test data
selects a fire ID. FEDS perimeters are expected at 12h cadence.

The exploratory any-time proximity rule returned 17/40 train and 12/20 validation;
that result was superseded because a perimeter could be near the FPA-FOD point long
after `t_st`, which is not a sound initial-state match. The fixed strict rule requires
an in-radius perimeter during the first 24 hours after `t_st`, inclusive. It returns
13/40 train and 7/20 validation, each with ≥2 consecutive 12h states and ≥5 states
within 48h. Both predeclared thresholds (20/8) fail. The train split was rerun with
the strict spatial-time query. Validation was deterministically post-filtered from
the saved candidate summary because Zenodo DNS was unavailable during continuation;
the original candidate report and this limitation are retained. FLE grouped incident
summary exists for 0/40 train and 13/20 validation cases; validation WFIGS IRWIN
matches are 20/20. The FLE service query is incident-level aggregate, not individual
line geometry.

The first combined run hit Zenodo HTTP 429 on opening the validation-year file after
both train years; split-only reports were then combined locally. A later attempt to
freshly re-read the validation file failed at DNS resolution, so the stricter criterion
was applied offline to the saved earliest-in-radius timestamps. The final combined
report labels that derivation and still records the gate as FAIL.
Exact per-case results, archive metadata and limitations: [combined crosswalk report](../../reports/real-fire-data/fpa-feds-fle-crosswalk-v1.json),
[method/data gate](FPA_FEDS_CROSSWALK.md). This is dataset coverage only: no SimFire
port, no-op simulation, physical-validation claim, PPO training or test-split access.


## EXP-007 — locally verified FEDS crosswalk and expanded candidate frame, 2026-11-03

The initial FPA-FOD frame (40 train/20 validation) was re-audited against locally
cached and checksum-verified FEDS-CONUS `lf_perimeter` archives for 2018/2019/2023. With
the unchanged join rule (FEDS start date -1/+2 days from FPA discovery, at least one
perimeter within 3 km during the first 24 hours from `t_st`, unique fire event), it
returns 19/40 train and 7/20 validation. The exact original frame fails both 20/8
minimums. Six additional train matches versus the prior 13/40 remote report were found
in the complete 2019 archive; the old result remains preserved as historical provenance.

To avoid adding only one post-result match, the same annual FPA-FOD screen snapshots
were treated as the candidate frame: all saved qualifying records for 2018/2019 train
(208) and 2023 validation (56), with the same original year split. The screen was
constructed without the FEDS crosswalk; it requires known date/location, MTBS ID, ten
western states, and reported final size >=5,000 acres. Under the same FEDS rule, 99/208
train and 20/56 validation incidents have unique matches and >=2 consecutive 12h states.
A full event timeline scan confirms all 119 have five exact 12h states from the selected
initial observation through +48h. This revised candidate-frame data-coverage gate passes
20/8. Selection on reported size means the resulting sample is conditioned on large
incidents; this is not a representative US fire sample. Neither area nor MTBS enters the
FEDS ID match, simulator observation, reward, or checkpoint choice. No 2024 test ID/data
was fetched or loaded.

Receipts: `reports/real-fire-data/fpa-feds-original-cohort-crosswalk-local-v1.json`,
`reports/real-fire-data/fpa-feds-candidate-frame-crosswalk-v1.json`,
`data/manifests/fpa-feds-candidate-frame-v1.json`, and
`data/manifests/feds-episode-cohort-v1.json`. Implementation: local-checksum-aware
`scripts/audit_feds_fpa_fle_crosswalk.py`, `scripts/fetch_feds_archive.py`, and
`scripts/build_feds_episode_manifest.py`. SimFire 2.0.1 at upstream commit
`04905b19fe8c10dc08d64faddd00303e0561bb66` was kept in the required separate Python
3.9.25 environment; exact macOS ARM64 lock is
`requirements/simfire-macos-arm64-py39.freeze.txt`.

Gate: data coverage passes for the revised frame, but active-front completeness, regional
fuel/terrain coverage, the SimFire train-only no-op comparison, and map-edge QC remain
open. This is not physical validation or an RL result. No training or test access.

## EXP-008 — SimFire environment and FEDS input integration, 2026-11-03

The active-front archive audit now finds an exact-timestamp `lf_fireline` feature for
all 99 train and 20 validation starts. Each line lies within one 375m FEDS pixel of
its perimeter; boundary overlap varies and is not assumed to be exact everywhere.
The complete initial scar/front fits a fixed 256×256 grid at 180m for 119/119 cases.

Created an isolated Python 3.9.25/macOS ARM64 SimFire 2.0.1 environment pinned to
upstream commit `04905b19fe8c10dc08d64faddd00303e0561bb66`; `uv pip check` passes for
85 packages. Official gridMET `th`, `vs`, and `fm100` annual archives for 2018/2019/2023
were checksum-verified; raw values were sampled at all 119 episode locations for four
12h segments each (396 train, 80 validation). Conversion code maps daily temperature,
wind, and 100h moisture fields to SimFire input units; WAF remains deliberately unset.

One Plateau train case has valid LANDFIRE LF2016 FBFM13 fuel and LF2020 elevation
rasters on the fixed 180m grid. A one-hour no-op integration smoke with placeholder
demo weather ended at 27 cumulative cells (87.48ha), with fire still active. It exposed
and fixed SimFire adapter issues (shape type, parsed runtime units, coarse-cell fire
lifetime). The 90-update lifetime is a shared 180m/30m resolution scaling from the
upstream demo setting; it was not fit to this case's future perimeter.

This is runtime/input integration only, not the historical no-op gate, physical
validation, or a scientific result. Bulk train fuel/terrain coverage, hidden historical
weather rollouts against persistence/ellipse, and map-edge checks remain next. No
suppression action, PPO training, or test-split access occurred.

## EXP-009 — bulk TRAIN inputs and one-case no-op response diagnostic, 2026-11-03

Fetched and validated LANDFIRE FBFM13 plus LF2020 elevation GeoTIFFs for all 99/99
TRAIN episodes (198 rasters, plus FEDS start masks) at the fixed 256×256, 180m grids.
Validation rasters remain unrequested until parameters are selected on TRAIN. The
per-case receipt records source product, resampling, grid metadata and raster SHA-256:
`reports/real-fire-data/feds-simfire-input-train-coverage-v1.json`.

Added a one-case 48h no-op runner that updates SimFire wind/moisture every 12h from the
four historical gridMET segments, then loads the five FEDS perimeters only after the
full run and compares each saved checkpoint. It records IoU, precision/recall, burned hectares,
edge contact, elapsed fire status and the candidate wind-adjustment factor. The future
perimeters are not imported into the simulation or policy.

On the TRAIN Plateau case, WAF values 0.20–0.60 yield the same 61.56ha prediction (three
new cells) and IoU 0.64 against 71.28ha observed. At WAF 0.65, predicted area jumps to
1,244ha by +12h; at 0.75 it is 2,262ha, and at 1.0 it is 9,487ha. Factors 0.75 and 1.0
touch the map edge by +36h and +24h. A 5-minute internal timestep with a 90-minute
active-cell lifetime (18 updates) ran the high-spread 48h case in about 40 seconds.
This timestep is a tested runtime candidate, not a locked simulator choice. Full per-candidate inputs/output hashes and
trajectory summaries are in `reports/real-fire-data/feds-simfire-noop-pilot-v1.json`;
raw full trajectories remain ignored under `.local/`.

This exploratory response check is a single event and does not pass or fail the whole
no-op gate. It shows that neither a WAF nor an internal step can be selected from one
incident: calibrate shared settings on the TRAIN cohort, compare against persistence and
a prespecified ellipse, then fetch validation maps and assess the frozen setup. No PPO,
suppression action, validation map, or test split was run/opened.

## EXP-010 — TRAIN-only SimFire MaskablePPO execution smoke, 2026-11-03

At the user's direct request, added a technical from-scratch PPO path rather than leaving
the work at environment setup. `src/wildfire_rl/feds_simfire_env.py` samples only the 99
manifest TRAIN cases and uses four shared 12h decisions through 48h. Its current
prototype has a no-op and eight directional actions that place up to seven `FIRELINE`
cells for one budget unit. No-op is always legal; the episode continues after budget
exhaustion or fire extinction; cumulative burn is retained if SimFire overwrites a cell
with a line. The observation includes current pooled map/fuel state, budget/time, and
only the current forcing segment. The reward is incremental cumulative SimFire burn;
future FEDS outlines are not loaded by the environment and do not enter observation or
reward. This action design and reward are technical prototypes, not field-validated
fireline operations or selected benchmark definitions.

`scripts/train_feds_simfire.py` completed 64 CPU MaskablePPO decisions, saved and loaded
the checkpoint, then completed a four-decision TRAIN rollout on
`fpa-fod-400500346-south`. WAF `.605` and 5-minute updates were explicit provisional
smoke inputs, not selected parameters. The checkpoint and full receipt remain ignored
in `.local/feds-ppo-smoke-waf-0.605-64steps/`; the manifest labels the run as neither a
benchmark nor research result and hashes the inputs/checkpoint. No validation map or
2024 test record was opened. A separate Plateau no-op rerun at `.605` reproduced 19
cumulative cells/61.56ha, IoU .64 vs 71.28ha, no edge touch at four checkpoints; it
still does not calibrate a cohort or pass the persistence/ellipse gate.

A separate real TRAIN action-branch smoke reset Plateau with budget 1, selected a legal
direction, placed a fireline, spent exactly one unit, then completed the remaining
three no-op decisions through the fixed horizon. This verifies placement and budget
plumbing only; it is not evidence the line is operationally realistic or beneficial.

QA: the complete Python 3.9.25 SimFire suite passes 63 tests; the default Python 3.12
suite passes 60 tests with 9 optional-dependency skips. Strict OKF validation passes
69 Markdown files, the main CLI smoke succeeds, `uv pip check` confirms all 85 packages,
and `git diff --check` passes. The original target UV Python binary is stalled, so its
venv entrypoint uses the verified Python 3.9 base from the preserved neighboring
`cfsds-train-qc` worktree while retaining this worktree's installed packages. This
launcher dependency is local and documented; replace it before moving/removing that
worktree.
