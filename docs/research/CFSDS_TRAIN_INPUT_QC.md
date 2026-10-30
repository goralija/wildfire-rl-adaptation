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

The W.I.S.E. paper describes a useful candidate recipe: start from one of the
versioned FBP maps, overlay only perimeters burned before target day n, and apply
the v20191114 burn-scar succession rules to form an event-specific annual map. It
uses day n-1 for initialization and day n as the assessment target [S-037].
That published approach is not a result from this project and must not be copied
without adaptation. Before implementing it, resolve the v2014b base map's historic
burn coverage, verify the exact class crosswalk/ruleset, keep day n and later
information out of the fuel input, and test how a day n-1 scar classified as
non-fuel interacts with this project's imported scar and active-front state.

**Current decision:** keep v2014b only to reproduce the already-saved pilot cases.
No annual map has been selected as a leakage-safe replacement for new training
cases. No CFSDS target day was used to tune a map or simulator setting.

## Status and next work

- Generated terrain/weather package available: 3 of 20 train candidates.
- Fuel-only screen: 10 pass and 10 fail; vintage suitability is unresolved.
- Suppression status: unknown for 20 of 20.
- No-action gate: not passed. No benchmark or fine-tuning.

Before new train replay work:

1. Build a small, train-only fuel-vintage proof of concept from documented sources.
   Record exact base-map hashes, time cutoffs, succession rules and per-cell
   provenance; assert that the fuel layer excludes target day n and future scars.
2. Check the proposed scar/non-fuel treatment against the current initial-state
   importer and simulator behavior with a fixture before using it in any FireCase.
3. Materialize inputs for the remaining train-only candidates selected for replay.
   Save source tile hashes/acquisition metadata for terrain and full weather API
   request, timezone, resolved location, units and variable-to-source mapping.
4. Seek event-level suppression evidence from the appropriate agency if available;
   otherwise retain unknown and define how that uncertainty affects cohort
   eligibility before running the replay gate.
5. Preregister the input variants, seeds, metrics and a common simulation horizon.
   Use target perimeters only for the declared aggregate train gate; do not select
   per-event stopping times or tune from any validation/test outcome.

TASK-015 remains partial until these input provenance and no-action criteria are
resolved. No benchmark, fine-tuning, or agent-superiority claim is supported.
