---
type: Audit
title: Train-only CFSDS simulator input alignment and provenance
description: Measured alignment of the three available train FireCases and source review for fuel, terrain, weather, and suppression.
status: active
sources:
  - resource: /reports/real-fire-data/cfsds-train-input-qc.json
  - resource: /data/manifests/cfsds-v1_1-pilot-cohort.json
  - resource: /docs/research/SOURCES.md
---
# Train-only CFSDS simulator input QC

## Purpose and scope

This is the remaining input-alignment audit under TASK-015. It checks only the 20
event/day-pair IDs in the cohort's train list. The local run inventory contained
three generated FireCases (2018_1770, 2018_241, and 2018_747); no validation
or test case package, raster, or outcome was opened. The other 17 train cases were
not present in the supplied run directory, so their terrain and weather alignment
is **not measured**.

The audit checks generated input files and provenance. It does not establish that
Cell2Fire accurately predicts fire behavior. It did not launch the simulator, train
or calibrate an agent, or choose values by comparing new predictions with target
perimeters. Machine-readable measurements and hashes are in
[cfsds-train-input-qc.json](../../reports/real-fire-data/cfsds-train-input-qc.json).

## What was measured locally

All three available FireCases identify their event and split=train. Each has
matching Forest.asc, elevation.asc, slope.asc, and saz.asc headers for the expected
20 by 20 grid at 100 m, matching 401-row Data.csv, and 400 valid terrain cells
with no no-data cells.

| Train event | Target date | Mean elevation | Elevation range | Mean slope | Slope range | Weather point to CFSDS centroid |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2018_1770 | 2018-08-12 | 1834.58 m | 1622–2154 m | 26.19% | 5–56% | 2.436 km |
| 2018_241 | 2018-08-15 | 936.46 m | 899–983 m | 5.45% | 0–15% | 5.156 km |
| 2018_747 | 2018-08-16 | 1404.83 m | 1301–1533 m | 15.43% | 1–44% | 5.195 km |

The terrain grids came from NRCan MRDEM-30 DTM and were reduced from 30 m to the
simulator's 100 m cells. Their generated-file hashes are preserved, but these case
manifests do not include the source tile checksum or tile acquisition date. MRDEM is
a blended terrain product, and some incorporated lidar was collected in 2006–2023;
the original pixel source and date for these particular cells are not known [S-034].
The grids are internally aligned; source-tile provenance and terrain vintage are
still open.

Each saved Weather.csv contains 24 ordered hourly rows from 00:00 through 23:00
on that event's target local date. The API location is 2.436–5.195 km from the
CFSDS summary centroid, but it is still one reanalysis location shared across the
2 by 2 km simulator window. ERA5 and ERA5-Land are hourly products with grid
spacing much coarser than that window [S-035]. The six daily CFSDS FWI codes are
constant in all 24 rows: the current files do not contain an independently
derived hourly FWI trajectory. Open-Meteo documents that ERA5-Seamless merges
temperature and humidity from ERA5-Land with wind and solar radiation from ERA5;
the case manifests do not preserve an exact source/version mapping for every
column, including precipitation. Record the full request and field mapping before
regenerating weather inputs.

The case fuel grids use National FBP fuel-type map v2014b at 250 m. The existing
train-only fuel audit found 10 PASS_FUEL_ONLY and 10 FAIL_FUEL_OVERLAP; this
status means only that the observed scar/front/target avoids disallowed fuel classes
under that audit's rule. It is not a physical-validation or vintage-safety result
[S-031; see also the method in CFSDS_TRAIN_QC.md].

## License and reuse notes

The official 2024 FBP map and MRDEM portal records list the Open Government Licence
– Canada. MRDEM also carries a Copernicus-derived component and product-specific
attribution/limitation notes. Open-Meteo states that API data are CC BY 4.0, while
free-service conditions (including non-commercial use and rate limits) are a
separate question. The reviewed CWFIS v2014b and v20191114 directory/metadata files
did not state a license; do not infer one from the fact that a URL is public. Ask
NRCan to confirm reuse/redistribution terms before publishing those raster files.
CNFDB separately requires its End-User Agreement; no agreement was accepted [S-031
through S-036].

Suppression/action evidence remains unknown for all 20 candidates. No event-level
agency action/resource timeline was joined. CNFDB provides agency-contributed
locations and perimeters, but its public documentation warns that records are
incomplete and variable in quality; an End-User Agreement is required [S-036].
The recent W.I.S.E. paper reports using CNFDB to exclude suppressed fires, but that
does not establish that this project has equivalent action data or can reproduce
that filter [S-037]. Unknown does not mean “unsuppressed.”

## Fuel-vintage research and leakage control

The previous fuel QC described v2014b as predating every train event. That is too
strong: the official metadata says its source includes 2011 land cover, CanFI2000,
ecological inputs, and NFDB/NBAC use for identifying burn scars, but gives no
per-pixel provenance or explicit cutoff for the burn records [S-031]. Its version
label alone cannot certify that all 2014 targets are free of event or future
information. The current saved pilot cases remain reproducible with their recorded
v2014b hash, but the layer is not yet certified as an as-of-event input.

NRCan's CWFIS development directory contains a 250 m CanFG layer labelled
v20191114. Its metadata lists 2017 kNN forest inventory and NBAC, and the archive
is about 2 GB. The product is in the development directory; it is evidence that
a later vintage exists, not evidence that its raw raster is appropriate for 2014–18
training. Since it was released after these targets and uses NBAC, direct use may
reveal post-target fire history; its precise per-pixel cutoff is unverified. The
archive was not downloaded
[S-032].

The official 2024 map is 30 m, covers 2020-08-01 to 2024-04-01, and uses SCANFI,
ecozones, and NBAC. It postdates all current train targets, so it is not a safe
replacement baseline for them [S-033].

The W.I.S.E. paper describes two distinct candidate fuel steps: make yearly maps
from one of the 2014/2019/2024 FBP releases using the v20191114 burn-scar succession
rules, then, for a day-n job, reclassify the same fire's perimeters before day n as
non-fuel [S-037]. The rule set's existence is verified, but its exact tree has not
yet been transcribed and validated for this project's crosswalk. The official
one-page CanFG-with-burn-scars PDF is a class legend, not that decision tree [S-038].

The paper's initial boundary also selects day n-1 cells adjacent to target day n,
and explicitly acknowledges this uses future perimeter information [S-037]. Our
current `build_cfsds_case.py` implements that target-aware selection. It means the
existing initial observation exposes part of target geometry even when the target
raster is not copied into the observation. This is a separate leakage path from the
fuel mask and must be replaced with a target-blind front definition before an
unbiased agent benchmark. The day n-1 perimeter is satellite-derived and does not
provide an hourly front, so the target-blind definition itself must be preregistered
and checked on train data.

That published approach is a method candidate, not a result from this project and
must not be copied without adaptation. Before implementing it, resolve the v2014b
base map's historic burn coverage, transcribe/verify the succession tree and fuel
crosswalk, keep day n and later information out of all fuel inputs, and test how
non-fuel historical scar cells interact with this project's imported scar, active
front, and cumulative-damage state.

**Current decision:** keep v2014b only to reproduce the already-saved pilot cases.
No annual map has been selected as a leakage-safe replacement for new training
cases. No CFSDS target day was used to tune a map or simulator setting.

## Train-only perimeter-mask and importer proof — 2026-10-31

Added `scripts/cfsds_fuel_vintage.py` and
[`scripts/prove_cfsds_train_fuel_vintage.py`](../../scripts/prove_cfsds_train_fuel_vintage.py).
The latter refuses any screen row outside `split=train` and reads only the `2018_747`
arrival raster (target DOY 228) for this proof. Its rule is:

```text
pre_target = valid AND arrival_day > 0 AND arrival_day < target_doy
```

The source raster is 48×50. This rule selects 881 pre-target event pixels overall and
272 in the existing 23×23 model crop; it includes day n-1 (136 pixels in the crop,
36 classified as the active front after target adjacency), and excludes all 19 day-n
target pixels. There are no later-than-target arrivals in this particular event raster.
Unit tests use an explicit n+1 value and confirm it is excluded; therefore the actual
event counts and the general boundary-rule check are recorded separately in
[`cfsds-train-fuel-vintage-mask-proof.json`](../../reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json).

This proves only the temporal perimeter predicate. It does **not** build/reclassify a
fuel raster: the existing v2014b map still lacks a verified per-pixel cutoff, and the
v20191114 succession tree has not yet been transcribed/validated. The diagnostic
front count reproduces the current target-aware builder rule only to explain the
existing case; it is not an acceptable front input for an unbiased benchmark. A
deliberately small C++
fixture places one `burnt` initial-state cell on an upstream `NF` fuel cell. The pinned
importer terminates with
`InitialState.csv marks a non-fuel/harvested cell as burned`, before writing an initial
grid; the probe then reports a secondary `IndexError` because that grid is absent.
The expected-rejection characterization and image/fixture hashes are in
[`nonfuel-initial-scar-compatibility.json`](../../reports/firehose-verification/nonfuel-initial-scar-compatibility.json).

**Decision:** do not silently map prior CFSDS scars to generic non-fuel or change the
case builder yet. First establish the base-map vintage/succession rules, define a
target-blind day n-1 front, and decide how C++/Python damage accounting represents a
historically burnt cell that is non-fuel at simulation start. The active front must be
valid under the simulator's fuel/import contract. No validation/test raster, replay,
training, or target-based parameter selection was used.

## Status and next work

- Generated terrain/weather package available: 3 of 20 train candidates.
- Fuel-only screen: 10 pass and 10 fail; vintage suitability is unresolved.
- Suppression status: unknown for 20 of 20.
- No-action gate: not passed. No benchmark or fine-tuning.

Before new train replay work:

1. Obtain/verify a safe base-map temporal cutoff and transcribe/validate the v20191114
   succession tree and fuel crosswalk, including licensing and per-cell provenance.
2. Replace the current target-aware `day n-1 adjacent to target day n` front selection
   with a preregistered definition based only on day n-1-and-earlier information; add
   a regression proving the initial input is invariant to the target-day mask.
3. Decide/test importer semantics when historical cumulative damage occupies a cell
   whose as-of-event fuel class is non-fuel; the current importer explicitly rejects it.
4. Only then build a fuel raster for one TRAIN case using the tested pre-target mask.
   Preserve assertions excluding target day n and later arrivals; keep the day n-1
   front compatible with spread.
5. Materialize inputs for the remaining train-only candidates selected for replay.
   Save source tile hashes/acquisition metadata for terrain and full weather API
   request, timezone, resolved location, units and variable-to-source mapping.
6. Seek event-level suppression evidence from the appropriate agency if available;
   otherwise retain unknown and define how that uncertainty affects cohort
   eligibility before running the replay gate.
7. Preregister the input variants, seeds, metrics and a common simulation horizon.
   Use target perimeters only for the declared aggregate train gate; do not select
   per-event stopping times or tune from any validation/test outcome.

TASK-015 remains partial until these input provenance and no-action criteria are
resolved. No benchmark, fine-tuning, or agent-superiority claim is supported.
