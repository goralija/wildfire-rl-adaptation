---
type: History
title: Work log
---
# Work log

2026-10-28 — empty upstream repository cloned; local empty base commit created to permit
worktree isolation. Work occurs on `feature/project-bootstrap`. No original project files
existed. User opted out of questions; all unconfirmed project choices remain assumptions.

Pre-flight: simulator -> policies -> evaluation share GridFire contract; optional Gym adapter
wraps that same engine. Pilot metrics never stand in for Cell2Fire validation.

Task 2 complete: simulator tests first failed for absent implementation; 11 behavior tests
passed after implementation. Two invalid test fixtures were corrected because they put
priority cells on NONFUEL; production validation was retained.
Task 3 complete: evaluation tests first failed for absent module, then six tests passed.
Task 4: checkpoint audit and optional Gym tests failed first; train/save/load smoke ran
1,024 CPU steps. Added RED→GREEN warmup-terminal regression after finding a valid fire
could end before the agent's first action.
Ruling: initial horizon 80 truncated some pilot fires; raise config horizon to 240 and
rerun the baseline matrix before reporting. Otherwise delayed spread could bias comparisons.
Ruling: native worktree creation had no repository context (task cwd was an empty folder);
used a local Git worktree under the authorized workspace after creating an empty base commit.

Task 5 complete: independent read-only source review found no Critical/Important issues;
22 tests passed independently. Final: minor (deferred): JSON null config prints traceback
instead of a friendly validation error (TASK-010); valid configs unaffected.
Ruling: realism, legacy inference, adaptation gains and generalization remain outside
bootstrap verdict because they have not been run; risk of misreporting is addressed by
explicit labels throughout README, reports and protocol.
Verification: 300-episode pilot replay identical excluding runtime; 0 truncated at horizon
240. Clean no-dependency environment passes 18 core tests and smoke, 4 RL tests skip;
modern optional environment passes all 22 tests. Pilot figure rendered locally and checked.
Local branch/worktree retained. No push, merge, paid compute or messaging performed.

Final artifact check: Python CSV writer uses standard CRLF line endings; Git whitespace
check flagged them. Added a CSV text/eol=lf Git attribute so committed reports normalize
without changing data or source hashes. This affects only repository serialization.

2026-10-28 — TASK-004 continuation authorized: build Firehose/Cell2Fire, attempt existing
checkpoint inference without training, and document dataset. Existing task worktree reused;
clean at start (e1de936). Docker daemon is available; choose isolated Linux container
instead of altering the modern .venv or installing system compiler libraries. A cached
managed Python 3.10 was made available by uv but is not needed for the selected Docker path.
No remote Git writes or long training authorized/required.
Plan: pinned dependency build -> binary no-action test -> legacy model load/predict ->
bounded rollouts and seed/replay checks -> dataset inventory/data card -> knowledge/handoff.
Verify: build exit 0, model action shape/mask, subprocess exits/timeout, paired seed replay,
existing tests, manifests with exact source/image/package versions. Treat any runtime patch
as an explicit compatibility decision, never a silent upstream change.

Runtime decision: checkpoint system_info.txt reports Python 3.8.12, SB3 1.5.0,
PyTorch 1.11.0+cu113 (GPU disabled), numpy 1.22.2, Gym 0.21.0. Use Python 3.8.20
container to match the Python minor version; PyTorch 1.13.1 has a verified Linux ARM64
wheel. This is compatible inference reproduction, not an exact original machine image.
SB3 contrib fork is pinned to 43b7fe6fcdda71c2c10de7af0d20f39e48ae5df3 (version 1.5.0).
Build only overrides compiler/include/link flags (remove x86-only -m64, enable OpenMP,
Eigen path), preserving original source and model files. Runtime network will be disabled.

TASK-004 runtime results: original C++ fork compiled without source edits in Linux ARM64;
both pretrained ZIPs loaded in SB3/contrib 1.5.0 and executed (0 training steps). Final
12-case batch passed with returncode 0, exact no-action/model seed replay, changed spread
for changed C++ seeds, identical input hash, B=8 enforcement/no-op continuation, and
unchanged model tensors. Four new probe helper tests were RED→GREEN.
Ruling: keep Firehose for next phase; runtime feasibility passed, full research gate remains
partial pending reset/cumulative-damage and termination reason adapter. Do not switch to
SimFire merely because the legacy stack needs isolation.
Confirmed wrapper issue: warmup CSV has 7 affected cells, reset state is blank; fixed PPO
upstream counter 206 vs history union 207. Explicit sync-reset diagnostic gives 207/207.
Confirmed state semantics: C++ outputGrid=1 merges burning and burnt; done may be weather
horizon, so no containment claims. Datacard inventories 141 files, 400 cells (307 fuel),
base weather plus 129 variants; current rows mode reads only base Weather.csv.
No raw dataset/model/image published, no remote pushes, no training or paid compute.

Evidence packaging correction: the global runs/ ignore also matched the nested report
folder named runs. Moved the twelve small JSON evidence files to reports/.../probes/
so model actions/state hashes are actually versioned; raw grids/logs remain ignored.

Final runtime review: fresh read-only reviewer found no Critical/Important or new minor
issues in the diagnostic scope; independently passed 26 tests and checked evidence,
commits/source hashes and all dataset file hashes. Physical validity, policy quality,
redistribution rights, future adapter and new-platform Docker rebuild are explicitly
outside that verdict. Final host suite 26/26; clean core 22 pass + 4 optional RL skips;
core smoke still executes. All changes remain local on feature/project-bootstrap.

2026-10-28 — User correctly distinguished environment configuration from observed-fire
data and requested real dataset candidates. Reviewed primary sources for Dogrib/Cell2Fire,
CFSDS and WildfireSpreadTS; bounded public data downloads only, no training or simulation.
Plan: assess relevance to budget adaptation -> inspect small observed-outcome samples ->
record provenance/quality/limitations and a feasible historical validation path.

Downloaded 16 selected Dogrib files (3,390,138 bytes) plus two CFSDS 2020 ZIPs
(293,731 bytes); SHA256 and offline sample checks passed for all 18 files. Dogrib
observed scar is 223x357 with 10,210 positive cells; 663 overlap fuel code101.
Sub20 fuel/elevation exactly match full Dogrib array[0:20,20:40]; slope/aspect differ,
and retained Sub20 origin does not match that crop. Thus not independent map validation.
CFSDS sample: 38 matched rasters/IDs at 90 m, 372 daily rows, 60 columns, no duplicate
fire-days, two missing BUI rows, no wind-direction column. Daily summaries alone cannot
supply the complete FBP grid/weather needed for a Cell2Fire replay.

Decision ADR-007: historical data strengthen simulator credibility but are not mandatory
for a conditional simulator policy comparison and do not identify counterfactual RL
benefits. Dogrib first as a connected case after temporal/input alignment; CFSDS as
conditional small independent event subset. Preserve TASK-004c as next technical task.
Do not mix 2024 CFSDS paper v1 (180 m) with inspected v1_1 files (90 m, beta caveats).
Raw samples/PDF remain ignored; only manifests/profiles/checks/source notes are versioned.
No physical validation, training, full large-archive download or remote writes performed.

2026-10-28 — User explicitly authorized committing/publishing all work as a PR and
preparing a colleague handoff. Reused feature/project-bootstrap worktree. Remote
inspection confirmed the GitHub repository still has no branches; main must first
receive only the existing empty base commit, leaving the full implementation in PR.
ADR-008 records the new remote authorization; no automatic merge is authorized.

Added portable HANDOFF.md: clone/setup, current capabilities, first TASK-004c with
acceptance checks, separate modern/legacy environments, public URLs/hash recovery
for ignored inputs, and a ready continuation prompt. Linked from README/knowledge
entry points. Existing public code/reports total about 0.54 MB; raw data, models,
private originals and third-party checkouts remain ignored.

Fresh host verification before publication: all 26 tests passed; synthetic smoke
executed. Reviewed 139 reachable historical blobs for ignored raw/private directories,
private-key/token patterns and file email addresses: no matches. Handoff links pass.
This bounded publication check does not change the research-readiness limitations.

Portable handoff verification: cloned feature/project-bootstrap into a fresh temporary
directory using Git transport (no hardlinks), created a new venv without installing
dependencies, passed 22 core tests with four optional skips, and executed the documented
synthetic smoke successfully. Clone contains no external/raw/private/local-venv assets.
Only documentation changed during PR preparation; research/runtime code was preserved.

2026-10-28 — User corrected the handoff priority: dataset refinement is not complete
or agreed. Verified that handoff/README/status/backlog/PR all prematurely selected
TASK-004c as the immediate project step, although source recommendations remained
provisional. Added TASK-012 and ADR-009: clarify data roles, choice/scope, model/domain
mapping and scenario/evaluation contract first. Keep the known adapter fixes as the
technical follow-up before experiments. Updated handoff prompts and data selection
status; no dataset was newly adopted, no code/data/experiments changed.
Verification after the correction: 26 tests pass, synthetic smoke succeeds, changed
document links/candidate JSON validate and Git whitespace check passes.

2026-10-28 — User requested all project knowledge as a self-contained OKF 0.2
repository bundle in the same PR. Existing docs already lived in Git; migration
adds types/titles and selected known source pointers, root index/log, lowercase
directory indexes and concise context/code-map/maintenance/format guides. The only
existing document rename is docs/INDEX.md → docs/index.md, performed via an
intermediate filename for macOS compatibility; all live references were updated.

ADR-010: root bundle keeps canonical documents in place instead of duplicating them
under a second knowledge tree. Agent routing files share AGENTS rather than copying
full rules. Workstation-specific prerequisites were removed from NEXT_SESSION;
public source/hash recovery remains in repo manifests. Dataset TASK-012 stays open/first.
No private originals, raw samples, checkpoints, third-party code or environment files
were added. No invented human verification or source modified timestamps.

Checker tests were written first: all initially failed because the CLI was absent;
12 tests passed after implementation. PyYAML 6.0.3 lives in a separate temporary
knowledge-tool venv and requirements/knowledge.txt; application dependencies unchanged.
Strict navigation validation currently passes 63 public Markdown files. The checker
is a scoped project tool, not a full implementation of optional OKF attestation fields.

Clean-clone verification: new Git clone and new Python 3.12.12 venv passed 22 core
tests/four optional skips and synthetic smoke before any package install. Installing
only the pinned PyYAML then passed knowledge tests/strict navigation. Public tracked
file scan found no private/raw/env paths or key/token/email patterns (130 files).

Fresh read-only OKF review found two P2 checker false positives (valid fence shapes
and optional Markdown link titles). Both were reproduced with failing tests and
fixed in one pass; 14 knowledge tests, 26 application tests and 63-file strict check
pass. No additional onboarding/provenance/dependency/TASK-012 findings; details in REVIEW.

Final clone rerun caught a newly added inline-code link example being interpreted as
a path. Added failing code-span fixtures, fixed extraction, and verified 15 knowledge
tests/63-file strict check in the clean clone again. Application suite remains 26/26.
Receipt with checker/test/requirements/workflow SHA256 is reports/knowledge-validation.json.
TASK-013 knowledge migration is complete; TASK-012 dataset refinement remains open/first.

2026-10-28 — User explicitly requested primary clone at mpvi root, linked worktrees
under .worktrees/, and ignored local scratch storage. Preflight: primary main and PR
worktree clean; one linked worktree, same published head; no managed app worktree attachment.
Plan: record ignore/layout policy -> snapshot Git/assets -> Git move linked checkout ->
promote existing .git and repair links -> preserve backups in .local and fix local venv
paths -> verify identities, ignores, tests/smoke and OKF -> update same PR. No PR/main merge.

Layout complete: existing .git is now at mpvi root; linked checkout moved with Git
to .worktrees/project-bootstrap and repaired after main Git metadata promotion.
main stayed 9e24b48; feature stayed 3615632 during relocation. Both statuses clean;
Git fsck exit 0. Previous backups and START_HERE preserved under ignored .local.
A temporary ignored main-checkout AGENTS pointer routes to canonical PR knowledge.

Integrity: all 13,246 non-venv/non-Git/cache file hashes matched, all 11 backup hashes
and original START_HERE hash matched; 18 raw sample hashes independently passed.
Both upstream clones remain clean at their pins. Local venv relocated by repairing
15 text path files and 5 wheel RECORDs, backing up originals; all 19 installed
distribution versions unchanged. Editable import, pip and wildfire executable point
at the new worktree. No package downloads/retraining/merge required.

Verification after relocation: 26 app tests, 15 knowledge tests, smoke and strict
64-Markdown validation pass. Replayed new HANDOFF main-clone/nested-worktree recipe
in a fresh temporary clone: core 22 pass/four optional skips, clean main/worktree,
strict knowledge passes. Public summary: reports/workspace-relocation.json; complete
local snapshots/repair details stay ignored in .local/migration. TASK-012 stays first.

2026-10-30 — User clarified the data target: build agent-training scenarios from real-fire
landscapes/weather/initial conditions, use observed progression as a separate no-action
reality-check, and compare policy counterfactuals only inside the simulator. Reviewed
Cell2Fire's exact CSV/raster parser contract and found a blocking shape mismatch:
`Ignitions.csv` maps one start cell per simulation year; multiple Python rows do not
initialize a simultaneous historical fire front. Added TASK-017 multi-cell initial-state
support after TASK-004c and before TASK-016 case conversion/replay. A 20x20/100m policy
covers 400 ha, so full-size events need an explicit crop/front boundary plan.

Expanded source review: CFSDS v1.1 remains best fit to current Canadian FBP simulator;
FireSpread_MedEU v2 offers 103 Europe/Mediterranean cases and 320 ~3m progression steps
but no Canadian FBP fuel mapping and no clearly displayed data-package license; GlobFire
is a global, coarser 500m fallback with several-day timing uncertainty. Added source
comparison, exact JSON/Cell2Fire mapping, weather/FWI/raster issues and claim limits to
REAL_CASE_PIPELINE / REAL_FIRE_DATASETS / DATASET; updated decision addendum, manifests,
handoff, statuses and task sequence. Sources include the Cell2Fire paper, CFSDS/W.I.S.E.,
FireSpread_MedEU descriptor, Copernicus ERA5-Land and JRC/GWIS data notes.

Installed the optional `geo` extra into the isolated modern Python 3.12.4/macOS ARM64
`.venv`: rasterio, geopandas, pyproj, xarray/rioxarray, netCDF4, scipy, shapely, pandas,
pyogrio and CDS API. Pinned rasterio 1.4.x and netCDF4 1.7.2 to compatible macOS 14 ARM64
wheels after latest releases attempted an unavailable local source build. All imports and
in-memory nearest-neighbour reprojection passed; Sub20 ASC parses but has no CRS. Created
combined GIS+RL freeze. CDS credentials and actual event download/conversion remain open;
no event split or large raster set was selected.

2026-10-30 follow-up — User asked for a broad, local-data-aware investigation before
choosing a path. Downloaded the 2.75 MB FireSpread_MedEU v2 shapefile to Git-ignored
`data/raw/` for a spatial-only scan. Reprojected its 649 EPSG:3035 rows to WGS84 and
intersected them with Natural Earth Admin 0 1:110m Bosnia and Herzegovina. Seven
candidate EFFIS IDs overlap: 12321, 13228, 22108, 25244, 25274, 43482, 205938. The
coarse country border means these still need authoritative-location verification.

EFFIS 205938 has four consecutive daily growth boundaries (2022-07-15..18), all rated
very high, final mapped area 637.63 ha, and ~4.14×4.18 km extent. EFFIS 43482 is the
smallest by area (216.87 ha) but has a 2.56×1.71 km extent and one medium-quality step.
Both exceed the verified PPO's 2×2 km footprint in at least one direction. Full event
fits need a verified larger grid/model or a clearly documented crop. Hashes, source
links, event metadata and limitations are in `reports/real-fire-data/medeu-spatial-screen.json`.

Added source-conditioned recommendations: CFSDS is the compatible route for keeping
the current Canadian FBP simulator; MedEU is the local BiH progression route, but first
requires regional fuel/spread model selection, dataset ZIP license confirmation, event
location verification, weather/DEM assembly and grid-scale decision. MedEU file was not
converted and is not in Git. No case build, simulator replay, training or policy claim
was made. Updated dataset pipeline, project handoff/status/backlog, source list, manifest,
environment receipt and decision/experiment logs accordingly.

2026-10-30 handoff to requested branch — Confirmed the user's `feature/project-bootstrap`
checkout was clean and at the same base commit, then applied the documented research
changes there. Copied only Git-ignored local materials needed for continuity: three raw
research ZIPs, upstream Firehose checkouts, prior small smoke/inference outputs. Created
the `.venv` in that project checkout using the pinned macOS ARM64/Python 3.12 freeze.
Repeated 26 application tests, 15 knowledge tests, 67-file strict validation, synthetic
CLI smoke, 1,024-step modern PPO smoke, and GIS imports/raster metadata checks; all passed.
The first unsandboxed package install was blocked by network isolation, then the user-
authorized network-enabled install completed. No Git commit or remote update was made.

2026-10-30 follow-up — Broadened the BiH path to actual fuel coverage. Downloaded the
EFFIS European Fuel Map 2017 archive (18,226,545 bytes, SHA256
`ed06080d81048de18dc34caf0f4fcc2f26d626f020bf132277d4e470a71a83d8`) to ignored
`data/raw/`. Read the 250 m EPSG:3035 NFFL/Anderson raster through `/vsizip/` without
extracting its 621,969,457-byte TIFF. Spatial overlay found codes 4/5/9 plus 9 no-data
pixels on final event `205938`, and codes 3/5 on `43482`. Results and method are in
`reports/real-fire-data/medeu-spatial-screen.json`.

This closes one data-source gap but exposes the model boundary: the checked-in Firehose
Cell2Fire C++ build is Canadian FBP; EFFIS categories must not be substituted into it.
The BiH path therefore needs a compatible NFFL/European spread engine or a defensible,
validated crosswalk. FIRE-RES publishes a potentially relevant 100 m Scott–Burgan server,
but exact BiH coverage, export rights and terms remain unverified; the product catalogue
also shows differing continental/pilot resolutions. EFFIS generic EU reuse terms default
to CC BY 4.0 unless layer-specific conditions apply. No FireCase conversion, no-action
replay or RL training was run. Updated route recommendations, source records, manifests,
environment receipt and backlog to show these gates.


2026-10-30 follow-up — User directed us to select the best simulator-compatible data
route without a national constraint and continue the next phase. Accepted Canada +
CFSDS v1.1 + Canadian FBP/Cell2Fire. Downloaded and checksum-verified all 23 annual
CFSDS archive pairs (2002–2024; 102,405,239 bytes) into ignored `data/raw/cfsds-v1_1/`.
Profiled 2014–2024: 3,141 fires / 82,015 daily rows / raster matches; selected at most
five compact crop candidates per year (44 retained: 20 train, 9 validation, 15 test
by event year). The split is preliminary and not exhaustive, and suppression/fuel-
vintage QC is not complete. Detailed ID list is in `data/manifests/cfsds-v1_1-pilot-cohort.json`.

Implemented `InitialState.csv` multi-cell importer for prior scar + active front, plus
`--fire-map` option for the real case in the isolated legacy image. Built a real CFSDS
case `2018_747`, 15–16 Aug 2018: CFSDS arrival mask resampled from 90m, official Canadian
FBP 2014b fuel map from 250m, MRDEM 30m terrain, 24 hourly ERA5-Seamless records, and a
100m 20×20 simulator grid. C++ import shows 175 scar / 31 active-front cells. Target
mask is held in separate `truth/`. Actual compiled C++ no-action replay succeeded with
seed 123; no RL training or interventions. Result: 66 ha predicted versus 15.39 ha
observed, IoU .2187, with 19 predicted cells touching the crop boundary. Fire-suppression
status is unknown, so this is not a physical validation or a policy result. A visual
map, case provenance, and JSON replay receipt are committed-size artifacts under
`reports/real-fire-data/`; the raw files and run outputs remain ignored.

QA and boundary work identified the next gate: review fuel/DEM/weather alignment,
perimeter handling and available crop extent; run several train-only event/seed replays;
prepare 2019/2024 FBP vintages and suppression/QC evidence before final event split; finish
the remaining TASK-004c cumulative-damage and terminal-reason export before training or
held-out policy comparisons. Updated ADR-013/014, STATUS/NEXT_SESSION/BACKLOG, data and
research manifests, knowledge context, and root log/index. No model fine-tuning or remote
Git action was performed.


2026-10-30 follow-up — Ran five additional offline CPU-only C++ no-action replays for
train pilot `2018_747` with seeds 124–128 (original seed 123 retained). All five extra
runs completed successfully, used the exact same input SHA-256, imported scar=175/front=31,
and produced the same final grid as seed 123. Thus all six runs yield 66 ha, IoU .2187,
19 predicted edge cells; simulator elapsed model periods range from 206 to 363. This shows
seed-stable final extent on this one case but does not show independent-event accuracy;
the unknown suppression, map boundary, weather/FWI assumptions and model calibration
still prevent a physical-validation claim. Receipt: `reports/real-fire-data/2018_747-seed-sweep.json`.


2026-10-30 verification — Rebuilt real-case Docker image was regression-checked against
the existing 12-case Sub20 inference matrix: 12/12 succeeded, all C++ exit codes were 0,
and all existing PPO checkpoint weights remained unchanged. The run was offline/CPU-only,
without training. Compact receipt: `reports/firehose-verification/real-case-image-regression.json`;
raw logs stay in ignored `runs/firehose-final-check/`.

2026-10-30 — Started isolated branch `research/cfsds-train-qc` from merged main
`ea5b8a7a`. Implemented `scripts/audit_cfsds_train_fuel.py` and focused optional GIS
unit tests. The train-only audit reads the 20 train rows, compares CFSDS 90 m masks and
the actual 20×20/100 m simulator grid to the Canadian FBP 2014b map, cross-checks annual
group-table area, and stores SHA-256 provenance in
`reports/real-fire-data/cfsds-train-fuel-qc.json`. Result: 10 `PASS_FUEL_ONLY`, 10
`FAIL_FUEL_OVERLAP`, zero processing errors. The existing three replay cases pass the
fuel gate, so their mismatch needs separate weather/FWI, FBP, suppression and domain
diagnosis. All suppression remains unknown. A precision review corrected the report to
state that the all-splits crop-screen file is loaded for selection, while no
validation/test fuel/source rasters are opened or overlaid. The published W.I.S.E.
filter is cited as inspiration only; this project gate is not its reproduction.

Added the fuel-only statuses and report pointer to the train rows in the cohort manifest.
Regenerated the report so its SHA-256 provenance matches the updated manifest.
Documented method, finding, limits and next TASK-018 in the research note, ADR-016,
experiment/work logs, status, backlog, handoff and navigation. No raw archive, third-party
checkout, venv, simulator replay, parameter calibration or agent training was added.
Verification: full application suite 29/29 passed, knowledge checker tests 15/15 passed,
strict OKF validator passed with 68 Markdown files, and the synthetic CLI smoke wrote
its output successfully. Report/manifest/script SHA-256 consistency was checked; no
absolute workstation paths were found in the new report. These checks cover the exact
implementation, report and documentation recorded above.

2026-10-30 — TASK-018 completed as a train-only diagnostics stage on
`research/cfsds-train-qc`. Compared existing FireCase/replay manifests and hashes,
Canadian FBP fuel classes, weather/FWI inputs, initial fronts, model extents and saved
simulator grids. Added `scripts/analyze_cfsds_replay_timeline.py` and a compact report
with fixed 30/60/120/240/480/720/1,440-minute measurements. All three saved forecasts
first contact the 20×20 crop edge within 34–52 model minutes; `2018_241` eventually
fills the 400-cell grid. Since CFSDS gives a daily satellite-interpolated target without
within-day timing and suppression records are unknown, the diagnosis does not identify
one physical cause or select per-event stop times.

Source review found and corrected a probe metadata error: its `weather_horizon_minutes`
used `60 × steps_per_action` (480) instead of the 24 hourly weather rows × 60 min =
1,440-minute horizon. The field now counts rows in the actual copied `Weather.csv`; this
does not alter completed replays. Added focused tests, TASK-018 diagnosis/receipt,
ADR-017, backlog/status/handoff/index updates. No new C++ replay, PPO training, raw data,
or validation/test outcome was used. TASK-004c is next; the no-action gate remains failed.

Verification: full application suite 34/34 passed, strict OKF validation passed with
69 Markdown files, and the timeline CLI smoke against the saved `2018_747` replay
reproduced the committed checkpoints and terminal grid metrics. Its generated output
is under ignored `runs/`; no simulator was rerun. `git diff --check` passed.

## 2026-10-30 — TASK-004c episode adapter

TASK-004c episode adapter completed locally on `research/cfsds-train-qc`. Added the second
pin-compatible Firehose patch for cumulative affected/front/treatment IDs and terminal
reasons; synced FireEnv's initial reset grid and terminal counters; kept checkpoint RGB,
action count, no-op and reward contract. A first 12-case integration run exposed cells
that C++ kept in cumulative damage while the categorical output grid showed treatment
(`-1`). The C++ terminal receipt is now canonical, Python counters synchronize from it,
and the probe verifies visible grid coverage plus treated-cell explanation for hidden IDs.
The fixture and corrected inference matrix pass; no training or physical validation ran.
The no-action gate remains failed and other C++ termination branches were not exercised
by this matrix. See `reports/firehose-verification/task004c-adapter-smoke.json` and ADR-018.

Verification after the implementation: all 38 project unit tests passed, strict OKF
validation passed, the synthetic CLI smoke wrote successfully, and `git diff --check` was
clean. The next task is remaining train-only TASK-015 fuel-vintage/terrain/weather/
suppression QC followed by predeclared no-action replay checks; no heldout result or
training was used.

## 2026-10-31 — TASK-015 train-only input alignment and fuel-vintage research

Added a small standard-library audit that reads only train IDs from the cohort and
checks matching local FireCase inputs. It found three materialized packages out of
20. All three share 20×20/100 m fuel/terrain grid headers; elevation, slope and aspect
have 400 valid cells each; each Weather.csv has 24 ordered hours on its target local
date. The reanalysis request location is 2.436–5.195 km from the CFSDS summary
centroid; the daily FWI codes repeat across the hourly rows. The other 17 packages
remain unmeasured. Machine report: reports/real-fire-data/cfsds-train-input-qc.json.

Reviewed official v2014b, v20191114 development, and 2024 fuel-map sources, the W.I.S.E.
annual-map method, MRDEM, ERA5/Open-Meteo and CNFDB documentation. The v2014b metadata
does not disclose an explicit per-pixel/burn-record time cutoff; v20191114 is in the
development catalog, about 2 GB, and includes NBAC-based reassignment; 2024 postdates
the current train targets. License review found OGL Canada for the 2024 map/MRDEM,
CC BY 4.0 for Open-Meteo API data with separate service terms, and no license
statement in the reviewed 2014b/v20191114 listings or metadata; confirm terms with
NRCan before redistributing those rasters. The W.I.S.E. recipe remains a method
candidate, not a project implementation. We preserve v2014b only for reproducing saved pilot cases.
We do not claim its map is leakage-safe for new cases. Suppression remains unknown
for all 20; no agency action timeline was joined. Terrain source tile dates/hashes and
full weather field lineage are missing from the existing case manifests.

Added focused train-only report/script/tests and updated source list, research note,
ADR-019, backlog, status, next-session, work log, handoff, code map and root navigation.
No new simulator replay, training, calibration, benchmark or heldout inspection ran.
No raw/large map, external checkout, venv, or generated run output was added to Git.
The no-action gate remains failed.

Verification: 42/42 project tests pass; strict OKF validation passes for 70 Markdown
files; synthetic CLI smoke succeeds in a fresh ignored run directory; git diff --check
is clean.

## 2026-10-31 — TASK-015 pre-target mask proof and non-fuel importer characterization

Added a reusable pre-target arrival-day mask and a train-only proof for `2018_747`
(target DOY 228). It selected 881 valid pre-target pixels across the source raster and
272 in the 23×23 simulator crop; all 19 target-day pixels were excluded. The event has
no later-than-target pixels, so a unit fixture separately verifies that day n+1 is
excluded. This is a temporal-mask proof only: no annual fuel map or fuel-class
reclassification was emitted because the base-map cutoff and succession crosswalk
remain unverified.

An isolated fixture reproduced the pinned C++ importer's rejection of historical
`burnt` state on an `NF` cell. The simulator emitted
`InitialState.csv marks a non-fuel/harvested cell as burned` before exporting an initial
grid; the probe's subsequent missing-grid `IndexError` is a secondary wrapper symptom.
This is an expected-rejection characterization, not a compatibility pass. No importer
or case-builder behavior changed.

The audit also confirmed that the current case builder selects the day n−1 active
front using adjacency to the day n target. That exposes target geometry through the
initial input, even if the target raster itself is kept hidden. The next task is to
define and preregister a target-blind initial-front rule using only day n−1 and earlier
information, then test that changing the target mask cannot change the initial state.
The annual fuel-map provenance/succession and historical-scar contract remain separate
blockers. No CFSDS replay, training, calibration, benchmark, or validation/test outcome
was used.

Verification: 46/46 project tests passed; strict OKF validation passed for 70 Markdown
files; a fresh synthetic CLI smoke succeeded; the train-only proof CLI succeeded; the
network-isolated C++ expected-rejection verifier succeeded; and `git diff --check` was
clean. The first CLI smoke invocation intentionally avoided overwriting an existing
`runs/` directory by rerunning under a fresh output name. Raw archives, Docker image,
external checkout, and generated run outputs remain outside Git.

## 2026-10-31 — TASK-015 target-blind crop/state and train spatial screen

Replaced target-adjacent front selection with a registered pre-target rule. The 23×23
crop center is nearest the centroid of all day n−1 pixels; safe-interior day n−1 pixels
are active front, and the one-cell crop border plus older arrivals become historical
scar. `build_cfsds_case.py` now recomputes this crop from pre-target data, defaults to the
train-only screen, and rejects screens/candidate rows without explicit target-blind flags.
The cohort-screen CLI defaults to 2014–2018 and refuses validation/test years.

For TRAIN `2018_747` (DOY 228), moved all 19 day-n target pixels while preserving prior
arrivals. Crop offset, 20×20 scar/front masks and serialized `InitialState.csv` stayed
identical; the target truth changed. The crop contains 17/19 target pixels, measured only
after selection. The separate target-blind train screen selected 25 candidates (five/year)
by pre-target metrics; only 4/25 contain any target-day pixel, median capture 0, maximum
1.0402%. This is a spatial-feasibility blocker, not a reason to tune windows with outcomes.

Receipts: [invariance proof](../reports/real-fire-data/cfsds-target-blind-input-invariance.json),
[train screen](../reports/real-fire-data/cfsds-train-target-blind-window-screen.json).
The historical combined cohort report retains legacy target-aware offsets and is rejected
by the updated builder. No FireCase rebuild, C++ replay, fuel-map generation, training,
calibration, benchmark, or validation/test raster access occurred.

Verification: all 58 project tests passed; strict OKF validation passed for 70 Markdown
files; synthetic CLI smoke wrote to a fresh `/private/tmp` folder; the CFSDS screen
processed 1,301 TRAIN event rasters/28,347 daily rows and emitted 25 TRAIN candidates;
the target-mask proof passed; `build_cfsds_case.py --help`, Python compilation and
`git diff --check` passed. The screen CLI's heldout-year rejection is unit-tested.
No validation/test raster was opened. Generated smoke output and raw CFSDS archives stay
outside Git. The screen emitted a non-fatal NumPy 2.5/Rasterio deprecation warning while
reading rasters; the report completed successfully.
