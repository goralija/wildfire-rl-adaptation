---
type: History
title: Work log
---
# Work log

2026-11-03 — Korisnik je odobrio novu aktivnu putanju SimFire + FPA-FOD/FEDS-CONUS,
uz FLE/ICS-209 kao ograničen post-hoc kontekst, i implementaciju prvo kroz pre-agent
data gate. Sačuvan je novi worktree `codex/fireline-simfire-benchmark` od `main`;
tri lokalne izmjene glavnog checkouta i stari research worktree ostali su netaknuti.

Nastavak, 2026-11-03: checksum-verifikovani `lf_fireline` zapisi postoje na tačnom
početnom vremenu za 119/119 train/validation epizoda. Linije su blizu početnog oboda
(unutar 375m FEDS piksela), ali preklapanje s obodom varira; ovo je opaženi aktivni
front, ne evidencija izgrađene vatrogasne linije. Fiksna 256×256/180m mapa prima
cijele početne obode/frontove za svih 119 slučajeva.

Postavljen je izolovani SimFire 2.0.1/Python 3.9.25 macOS ARM64 environment; svih
85 zaključanih paketa prolazi `uv pip check`. Službeni gridMET `th`, `vs`, `fm100`
arhivi za 2018/2019/2023 su checksum-verifikovani; četiri 12h forcing uzorka postoje
za svaki od 119 slučajeva. Raw forcing je pretvoren u SimFire jedinice, ali
wind-adjustment faktor nije izabran. Jedan Plateau train slučaj ima LANDFIRE
LF2016 fuel i LF2020 elevation rastere; input smoke od 60 minuta sa demo vjetrom
spalio je 27 kumulativnih ćelija/87.48ha. To potvrđuje povezivanje kodnih putanja,
ne historijski no-op gate, spread validaciju ili fizičku tačnost. Još nema bulk
train mapa, poređenja sa persistence/elipsom, suppression akcija ili PPO treninga.

Napravljen je test-excluded manifest od 40 train / 20 validation događaja. U prvoj,
eksplorativnoj provjeri FEDS-CONUS FlatGeobuf godišnje datoteke čitane su samo
prostornim HTTP Range upitima, bez punog downloada; širi vremenski join dao je 17/40
train i 12/20 validation. Taj preliminarni rezultat je supersedovan strogim 24h
startnim kriterijem u zapisu ispod. FLE incidentni sažetak se spaja za 0/40 train i
13/20 validation; servis nije line-level geometrija.

Sačuvani su split izvještaji, kombinovani JSON, crosswalk skripta/testovi i novi
protokol/source/status/ADR-016 zapisi; korekcija i ADR-017 slijede niže. Prvi puni cross-split poziv dobio je Zenodo
429 na 2023 fajlu; split-only pozivi su kompletirani i kombinovani lokalno. Nema
preuzetih godišnjih arhiva. Provjere: 33 application testa prolaze (5 opcionalnih
geo/RL testova preskočeno u Python 3.12 core environmentu); svih 7 crosswalk testova
prošlo je u GIS-enabled environmentu; 15 knowledge testa i strict OKF/link provjera
za 68 Markdown fajlova prolaze; synthetic CLI smoke i `git diff --check` su čisti.
Prvi atomarni commit je sljedeći.

2026-11-03 — Korekcija crosswalk gatea prije predaje. Eksplorativni join od 17/40
train i 12/20 validation dopuštao je blizinu FPA tački bilo kada u toku požara. Zbog
početnog stanja simulatora kriterij je pooštren: obod unutar 3 km mora biti opažen u
prvih 24h od `t_st`; pragovi ostaju nepromijenjeni. Train je ponovo auditiran i daje
13/40; validation je deterministički postfiltriran iz sačuvanog najranijeg
in-radius vremena i daje 7/20. Stari kandidatski izvještaj je sačuvan; novi audit
alat i test pokrivaju ponovljivi offline filter. Gate pada u oba splita, pa SimFire
implementacija i no-op replay nisu započeti. Validation mrežna provjera nije ponovljena
jer Zenodo DNS nije bio dostupan; ovo je zabilježeno u izvještajima.
Provjere nakon korekcije: 34 aplikacijska testa prošla (5 opcionalnih preskočeno), svih
8 crosswalk testova u GIS environmentu, 15 knowledge testova, strict OKF/link check za
68 Markdown fajlova, CLI smoke i `git diff --check` su prošli.

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


2026-11-03 — FEDS archive crosswalk and reproducible SimFire setup. Downloaded FEDS-CONUS
`lf_perimeter` FlatGeobufs for 2018, 2019, 2023 into ignored `.local/feds-conus/`; each
matches its published Zenodo MD5. The 2024 archive and test records were not fetched or
read. Re-ran the original 60-case FPA-FOD train/validation cohort locally: 19/40 and 7/20,
so the old cohort still misses the 20/8 gate. To avoid selecting a single extra fire after
seeing outcomes, screened the full saved FPA-FOD frames for the same years (208 train,
56 validation) and applied the unchanged early FEDS date/point/3km/unique-match rule.
The broad predeclared frame yields 99 train + 20 validation episodes, each with five
12-hour FEDS states from the initial state through +48h. This explicitly revises the
candidate universe under ADR-018; it does not alter the thresholds or test boundary.

Hardened the audit to handle date-only discovery times, verify local FEDS archives, and
scan the full selected event timeline after the initial 3km match so a moving perimeter
is not mistaken for missing time coverage. Added a checksum-aware fetcher restricted to
2018/2019/2023 and an episode-manifest builder that excludes FPA final area and MTBS IDs
from the policy scenario. Added a Python 3.9.25/macOS ARM64 lock pinned to SimFire 2.0.1
upstream commit `04905b19fe8c10dc08d64faddd00303e0561bb66`; SimFire remains a separate
runtime from the project's Python >=3.11 environment. Targeted crosswalk/fetcher/manifest
tests: 14 passed. No SimFire historical no-op, PPO training, test split, or physical
validation was run. Next: schema-check exact-time active fronts, prepare LANDFIRE inputs,
then begin the train-only no-op gate.

2026-11-03 — završena priprema TRAIN input okruženja i pokrenuta no-op dijagnostika.
Batch LANDFIRE builder preuzeo je 99/99 train FBFM13 + LF2020 elevation parova (198
GeoTIFF-ova), njihove početne FEDS maske i receipts. Sva rastera su na 256×256/180m,
provjerenih granica/CRS/dimenzija/NoData i fuel code skupa. Validation mape nisu
preuzete prije train kalibracije. Coverage je u
`reports/real-fire-data/feds-simfire-input-train-coverage-v1.json`; raw ostaje u
`.local/feds-simfire-cases`.

Dodani su bulk fetch CLI/testovi, kumulativna burn-mask metrika, 90-min ćelijskog
trajanja/timebase test i historijski no-op runner. Runner koristi svaki od četiri
12h gridMET segmenata u SimFire, pa nakon cijelog roll-outa otvara pet budućih oboda
isključivo za post-hoc poređenje spremljenih stanja. Pilot na TRAIN Plateau pokazuje
da WAF 0.20–0.60 ostaje praktično na
persistence (61.56 ha; tri nova ćelije; IoU .64 prema 71.28 ha), a 0.65 skoči na
1,244 ha za 12h; 0.75 i 1.0 su znatno veći i do +24/+36h dodiruju rub. Na 5-minutnom
SimFire internom koraku WAF-1 rollout trajao je oko 40 sekundi;
5m × 18 update-a zadržava nominalnih 90 minuta aktivne ćelije. Ovo je jedan događaj,
ne kohortni gate; nijedan faktor ili time-step još nije zaključan. Pilot je zabilježen u
`reports/real-fire-data/feds-simfire-noop-pilot-v1.json`. Nema suppression akcija, RL,
validation rastera ili TEST pristupa.

2026-11-03 — na korisnikov direktni zahtjev dovršena je tehnička TRAIN-only FEDS/SimFire
PPO putanja. Ciljni `.local/uv-python` launcher bio je zaglavljen u I/O; sačuvan je kao
backup, a `bin/python` sada poziva provjereni Python 3.9.25 iz susjednog očuvanog
`cfsds-train-qc` worktreea uz lokalnih 85 paketa. `uv pip check` prolazi. Novi
`FedsSimFireEnv` uzorkuje isključivo 99 train slučajeva, koristi četiri 12h odluke kroz
48h, budžete, stalno legalan no-op, kumulativnu štetu i kratku osmosmjernu fireline
akciju. Budžet ili gašenje vatre ne prekida epizodu. Budući FEDS obodi ne ulaze u
policy observation/reward.

Pokrenut je 64-decision CPU MaskablePPO smoke sa WAF .605 kao eksplicitnim provisional
parametrom. Checkpoint je sačuvan/ponovo učitan, završni TRAIN rollout odrađen, a zaseban
budget-1 TRAIN potez potrošio je jednu jedinicu i postavio fireline. Svi izlazi/težine
su ostali u `.local/feds-ppo-smoke-waf-0.605-64steps`; ovo nije benchmark ili RL rezultat.
Ponavljanje Plateau .605 no-op-a dalo je 19 ćelija/61.56 ha, IoU .64 i bez ruba u četiri
tačke; WAF nije izabran i cohort persistence/elipsa gate je još otvoren. Validation
mape i 2024 TEST nisu preuzeti/učitani.

Provjera: Python 3.9.25 suite 63/63 PASS; project Python 3.12 suite 60 PASS i 9 optional
dependency skips; strict knowledge validation 69 Markdown PASS; glavni CLI smoke,
85-package `uv pip check` i `git diff --check` prolaze. Detalji i tačna trening komanda
su u [environment record](research/SIMFIRE_ENVIRONMENT.md), [EXP-010](research/EXPERIMENT_LOG.md)
i [handoff](NEXT_SESSION.md).

2026-11-03 — dovršen je TRAIN-only no-op screen uz persistence i unaprijed definisanu
elipsu. Osam WAF-ova (0, .0025, .01, .025, .05, .10, .20, .605) obrađeno je na istih
99 slučajeva, 5-min internom koraku, seed=0 i 48h horizontu; svaki run dao je 99/99
uspješnih epizoda i 396 vremenskih poređenja. Nijedan kandidat nije prošao strogi uslov
(bez ruba i bolji mean IoU i površinska greška od obje reference). Persistence je .5343
IoU / 2351.7ha greške; elipsa .5308 / 2346.6ha. Najbolji kandidat IoU-om je WAF .0025
(.4769), najniži area error je WAF .01 (2262.1ha); WAF .605 dodiruje rub u 61 slučaju.
Zato nema izabranog WAF ili timebase; benchmark PPO ostaje blokiran, a tehnički smoke
ostaje moguć. Validation mape i TEST 2024 nisu učitani. Sažetak/hashovi su u
`reports/real-fire-data/feds-simfire-train-noop-screen-v1.json`, raw reporti ostaju u
`.local/`. Suite Python 3.9: 65 PASS; glavni suite: 62 PASS, 9 optional skips; CLI smoke
and 85-package check prolaze. Ovo je model screen, ne fizička validacija.

Dodatna WAF .01 / 1-min timebase osjetljivost takođe je završila 99/99: mean IoU .4771,
bez rubnih kontakata, naspram .4769 na 5-min koraku. Rezultat ne mijenja gate; 3/10/15-
min koraci nisu pokretani i interni korak ostaje neizabran. Strict knowledge validator
prošao je 69 Markdown fajlova, a `git diff --check` je čist.
