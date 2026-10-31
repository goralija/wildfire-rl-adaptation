---
type: Audit
title: Train-only CFSDS simulator input alignment and provenance
description: Measured alignment of the three available train FireCases and source review for fuel, terrain, weather, and suppression.
status: active
sources:
  - resource: /reports/real-fire-data/cfsds-train-input-qc.json
  - resource: /data/manifests/cfsds-v1_1-pilot-cohort.json
  - resource: /docs/research/SOURCES.md
  - resource: /docs/research/CFSDS_FUEL_VINTAGE_REVIEW.md
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
separate question. The CWFIS download-site notice states that downloaded data are
under the Open Government Licence - Canada and specifies CFS attribution [S-039].
No product-specific exception was found in the reviewed v2014b or v20191114 listing
and metadata. Separately sourced component layers may have their own terms; the 2018
base-layer notes identify an Agriculture Canada data-sharing agreement and kNN layers
available on request [S-041]. CNFDB separately requires its End-User Agreement; no
agreement was accepted [S-031 through S-036].

Suppression/action evidence remains unknown for all 20 candidates. No event-level
agency action/resource timeline was joined. CNFDB provides agency-contributed
locations and perimeters, but its public documentation warns that records are
incomplete and variable in quality; an End-User Agreement is required [S-036].
The recent W.I.S.E. paper reports using CNFDB to exclude suppressed fires, but that
does not establish that this project has equivalent action data or can reproduce
that filter [S-037]. Unknown does not mean “unsuppressed.”

## Fuel-vintage research and leakage control

The focused public-source follow-up is recorded in the
[TRAIN fuel-vintage review](CFSDS_FUEL_VINTAGE_REVIEW.md). It adds the official CWFIS
site-wide reuse notice and the public 2018 baseline fuel-class rules/base-layer notes.
Those rules describe classification into baseline FBP classes; they are not the
post-fire burn-scar succession crosswalk. The v2014b metadata lists NFDB/NBAC use to
identify burn scars but does not date that layer's input cutoff.

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
The official 2018 FBP classification-rules and base-layers PDFs describe baseline fuel
assignment, not post-fire succession [S-041]. The publisher states that W.I.S.E. study
data are available on reasonable request, and the article text does not enumerate the
succession tree's branches [S-037].

The paper's initial boundary also selects day n-1 cells adjacent to target day n,
and explicitly acknowledges this uses future perimeter information [S-037]. The
first version of our `build_cfsds_case.py` implemented that target-aware selection,
so its initial observation exposed part of target geometry. That historical behavior
has since been replaced by the target-blind prototype recorded below. The day n-1
perimeter remains satellite-derived and does not provide an hourly front.

That published approach is a method candidate, not a result from this project and
must not be copied without adaptation. Before implementing it, resolve the v2014b
base map's historic burn coverage, transcribe/verify the succession tree and fuel
crosswalk, keep day n and later information out of all fuel inputs, and test how
non-fuel historical scar cells interact with this project's imported scar, active
front, and cumulative-damage state.

**Current decision:** keep v2014b only to reproduce the already-saved pilot cases.
Its 2011 land-cover vintage and version label do not prove the cutoff of the separate
NFDB/NBAC burn-scar input; the current 2026 pre-season map-update convention cannot be
assumed for v2014b. The general CWFIS reuse terms are documented as Open Government
Licence - Canada with attribution, but the post-fire succession tree and per-cell
lineage remain unresolved. No annual map has been selected as a leakage-safe
replacement for new training cases. No CFSDS target day was used to tune a map or
simulator setting. See the [full review](CFSDS_FUEL_VINTAGE_REVIEW.md).

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
front count reproduces the then-current target-aware builder rule only to explain the
existing case; it is not an acceptable front input for an unbiased benchmark. A
deliberately small C++ fixture originally placed one ordinary `burnt` initial-state cell
on an upstream `NF` fuel cell; the pinned importer rejected it before writing a grid.
That expected-rejection characterization and its image/fixture hashes remain in
[`nonfuel-initial-scar-compatibility.json`](../../reports/firehose-verification/nonfuel-initial-scar-compatibility.json).

The importer contract now adds a separate `scar_nf` state. It accepts this token only
when the simulator map's exact class is `NF`, keeps the cell in C++ `burntCells` and the
terminal/Python cumulative `ever_affected` set, exports it as a historical scar, and never
adds it to the active front or available fuel. Ordinary `burnt` on `NF`, `burning` on
non-fuel, and `scar_nf` on a fuel cell remain invalid. The serializer helper can emit this
token only from an explicitly provided nonfuel-scar mask that is a subset of historical
burnt cells. It does not infer that mask from a CFSDS event layer or FBP fuel class.
The runnable C++ contract receipt is tracked separately in
[`nonfuel-initial-scar-contract.json`](../../reports/firehose-verification/nonfuel-initial-scar-contract.json).

**Decision:** preserve the source fuel class and require explicit provenance before
using `scar_nf`. This resolves how a qualified historical scar is represented, but does
not prove that any real `NF` overlay is a post-fire succession class. The case builder
continues to reject all non-fuel/water scar or front cells; annual map generation still
requires dated base-map vintage, a verified succession tree, and per-cell lineage. No
validation/test raster, CFSDS replay, training, or target-based parameter selection was
used.

## Target-blind crop and initial-state proof — 2026-10-31

The prototype rule in [`scripts/cfsds_initial_state.py`](../../scripts/cfsds_initial_state.py)
uses only arrival values strictly before day n. It chooses the eligible 23×23 crop whose
center is nearest the centroid of all day n−1 pixels; a crop must contain at least three
safe-interior day n−1 pixels. Those interior pixels become the active front. Day n−1
pixels on the one-pixel native crop border and older pre-target pixels become historical
scar. Ties are deterministic: more interior front, more pre-target history, then
row/column order. This is a declared daily-front proxy, not hourly flame truth.

The train-only [`2018_747` invariance receipt](../../reports/real-fire-data/cfsds-target-blind-input-invariance.json)
perturbs all 19 target-day pixels while preserving prior history. The crop offset, native
prior mask, 20×20 burnt/front masks and serialized `InitialState.csv` remain identical;
the separate target truth changes. The chosen target-blind crop happens to include 17/19
target pixels, but this coverage was measured only after the crop rule was fixed.
This proof fixes one TRAIN event/day explicitly; it proves conditional input invariance,
not that the cohort's event-day selection is itself independent of target availability.

A separate predeclared train-only screen processed years 2014–2018 and selected five
candidates per year by pre-target state metrics. Only 4 of 25 shortlisted windows contain
any target-day pixel; median target capture is zero and maximum capture is 1.0402%.
Target geometry is diagnostic only and does not influence crop, candidate ranking, or
eligibility. The result indicates that a fixed 2×2 km grid often misses the next day's
observed growth for this shortlist. Do not tune the rule against target coverage; define
any future spatial-feasibility rule from inputs available before day n, or reconsider the
model-domain contract before a reality-check replay.

The new window screen defaults to 2014–2018 and refuses validation/test years before
opening their archives. `build_cfsds_case.py` now defaults to this train-only report and
requires explicit false flags for target use both at report and candidate-row level; the
legacy combined screen is rejected for new case generation. The builder calculates an
intended weather lookup point from the pre-target front but still reads the supplied
`--weather-json`; this invariance proof does not inspect that response or any `Weather.csv`.
No weather file was regenerated, so weather location/field provenance remains open.

No FireCase was rebuilt and no C++ replay or training was run. The proof demonstrates
input invariance for one TRAIN event only, not physical validity or policy benefit.

## Status and next work

- Generated terrain/weather package available: 3 of 20 train candidates.
- Legacy fuel-only screen: 10 pass and 10 fail on the previous cohort/windows; the new
  target-blind shortlist has not been fuel-audited and vintage suitability is unresolved.
- Suppression status: unknown for 20 of 20.
- No-action gate: not passed. No benchmark or fine-tuning.

Before new train replay work:

1. Resolve target-blind spatial feasibility using only pre-target information: quantify
   how much prior scar/front the fixed crop omits and verify that a usable day n−1 front
   survives regridding. The current target screen is post-selection diagnosis only, never
   an eligibility/tuning criterion. If the fixed 2×2 km domain is unsuitable, record the
   blocker and justify a separate model-domain decision before replay.
2. Continue the source gate: obtain/verify the dated base-map burn-history cutoff and
   source/validate the v20191114 post-fire succession tree and fuel crosswalk, including
   per-cell provenance. CWFIS general reuse terms are now documented as Open Government
   Licence - Canada with attribution; separately sourced layer terms still need review.
3. Use the tested `scar_nf` importer token only when cell-level evidence confirms that
   an NF class is a post-fire succession outcome, not Water, Urban, no-data or an
   overlay error. The generic case builder still rejects every initial non-fuel/water
   overlap until that provenance and fuel map are supplied.
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
