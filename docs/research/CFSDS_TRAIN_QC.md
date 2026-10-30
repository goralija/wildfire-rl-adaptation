---
type: Audit
title: Train-only CFSDS fuel compatibility audit
description: Methods and results for mapping the 20 preliminary CFSDS train day-pairs to the 2014b Canadian FBP and 20x20 Cell2Fire grids.
status: stable
sources:
  - resource: /reports/real-fire-data/cfsds-train-fuel-qc.json
  - resource: /data/manifests/cfsds-v1_1-pilot-cohort.json
  - resource: /docs/specs/DECISION_RECORDS.md
---
# Train-only CFSDS fuel compatibility audit

## Why this check exists

The preliminary cohort contains 20 train day-pairs selected by crop geometry. That
screen alone does not tell us whether the observed fire lies on fuel categories that
the pinned Cell2Fire build can represent. This check is the first part of TASK-015's
input-quality gate. It is deliberately limited to train events so that validation and
test outcomes do not guide training-case acceptance or model calibration.

The source event map is a 90 m CFSDS day-of-burning raster. The current policy model
uses a centered 20 by 20 grid of 100 m cells, and the available official Canadian FBP
fuel layer is 250 m, release 2014b. The audit therefore reports both the original
90 m overlay and the actual 100 m model-grid overlay. Those spatial scales are not
interchangeable. CFSDS day-of-burning values are satellite-hotspot interpolations,
not hourly ground-truth fire perimeters [Barber et al., 2024](SOURCES.md#s-015).

## Method

For each of the 20 train records in the cohort manifest, the tool reconstructs three
masks from the selected annual arrival raster: earlier burned scar, day n-1 active
front, and day n target. Disconnected day n pixels are reported and excluded from the
connected target in the same way as the existing case builder. A cross-check compares
the target-area summary against the annual CFSDS group table.

The official 2014b categorical fuel raster is overlaid on the native crop with
nearest-neighbour resampling. Separately, the three masks are area-averaged onto the
centered 20 by 20 / 100 m policy grid, while the fuel categories use nearest-neighbour
resampling exactly as the case builder does. The report records categorical majority
cells and fractional observed area so small sub-cell overlaps remain visible.

For this project's strict gate, Water, Non-fuel, Wetland, Urban, Vegetated Non-fuel,
Unknown, no-data and unmapped coverage count as excluded or ambiguous. A case fails
the fuel-only gate if any native scar/front/target pixel, or any majority model-grid
scar/front/target cell, lands on one of those categories. A sub-majority excluded
overlap is reported for review; it is never silently rounded away. This project rule
is **inspired by** the fuel filters in the 2026 W.I.S.E. assessment, but it is stricter
in checking the full earlier scar and is not a reproduction of that paper's protocol
or results [Bennett et al., 2026](SOURCES.md#s-019).

The cohort manifest and combined crop-screen JSON contain all three splits and are
loaded to select the train rows. The audit opens no validation/test fuel or CFSDS
source rasters and does not compute any validation/test overlay. It performs no
simulator replay, training, or parameter calibration. Input and code SHA-256 hashes,
map geometry, environment
versions and each case-level measurement are in the [machine-readable report](../../reports/real-fire-data/cfsds-train-fuel-qc.json).

Re-run from the repository root when the documented local raw data and Firehose
checkout are present:

```sh
PYTHONPATH=src python3 scripts/audit_cfsds_train_fuel.py
```

Optional `--raw-root`, `--fuel-zip`, `--lookup`, and `--out` flags let a teammate
provide local paths without adding raw archives or the third-party checkout to Git.

## Findings on 2026-10-30

- All 20 train candidates were processed; there were no processing or source-table
  cross-check errors. All 20 retained a valid adjacent previous-day front and next-day
  target on the model grid, with neither majority front nor target touching the 20x20
  grid edge.
- Ten cases pass **fuel only**: `2014_221`, `2015_252`, `2015_2924`, `2015_896`,
  `2017_1431`, `2017_1871`, `2018_1770`, `2018_1860`, `2018_241`, and `2018_747`.
- Ten fail the strict fuel gate: `2014_2221`, `2014_285`, `2014_432`, `2014_538`,
  `2015_2929`, `2015_438`, `2017_1146`, `2017_1296`, `2017_51`, and `2018_1932`.
  Most failures involve earlier scar area; some also overlap the active front or target.
  The detailed native-pixel and 100 m majority/fractional counts are in the report.
- The existing three no-action replay cases (`2018_747`, `2018_241`, `2018_1770`)
  all pass this fuel-only check. This means fuel overlap alone does not explain their
  large predicted growth; weather/FWI, FBP settings, suppression, and crop/domain
  effects remain open.
- Suppression status remains unknown for all 20. No candidate is certified as a
  complete simulator case by this audit. The report's zero full-replay/policy-evaluation
  eligibility means the remaining gates were not assessed here; it is not a claim that
  the ten fuel-pass events are unusable.

## Limits and next work

The 2014b fuel vintage is a useful training-period layer but does not prove annual
fuel succession for every event. The 250 m layer resampled to 100 m does not provide
new 100 m fuel detail. The project's strict rule can reject a case due to even one
native fire pixel on an excluded class; inspect area/counts before interpreting a
failure as a broad landscape mismatch. More complete quality control still needs
fuel-vintage review, terrain/weather alignment, suppression evidence, crop/domain
adequacy and the no-action simulator gate. The W.I.S.E. paper uses annual fuel-map
vintages and additional event filters; its reported skill scores are not Cell2Fire
results and must not be attributed to this project.

Next: finish train-only fuel-vintage, terrain/weather alignment and suppression evidence;
then use the three existing fuel-pass replay cases for preregistered weather/FWI,
FBP-parameter and crop-edge controls. Keep all validation/test event outcomes out of
tuning. TASK-004c adapter is complete, but no-action benchmark/fine-tuning remains blocked
by the independent replay quality gate and heldout event freeze in ADR-015/018.
