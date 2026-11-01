---
type: Data Review
title: "BurnMD Mineral Fire 2020: first local data audit"
status: current-provisional
sources:
  - resource: /docs/research/SOURCES.md
  - resource: /docs/research/EXPERIMENT_LOG.md
---
# BurnMD Mineral Fire 2020: first local data audit

## Result in everyday language

We have a real map of the Mineral Fire and its reported fire lines, and the BurnMD
archive checksum exactly matches MITRE's download pointer. The shapes can be read and
put on a map. That is a useful first bridge from a real incident into our tools.

We **cannot yet replay this event through time**. The archive contains line locations and
labels such as “Completed Dozer Line”, but the fields that would say when each line was
built are empty for this incident. The archive's `CreateDate` means when a map feature was
created in the source system; it is not proof that a crew built the line at that moment.
Giving the simulator guessed action times would make a plausible-looking animation, not
a faithful replay.

The plotted local QA image is stored in ignored `.local/burnmd-mineral-case/`. It draws the
11 perimeter observations in the order of their recorded collection dates and overlays
the reported line types. It is a picture of the source records, **not** a simulator result.
The reproducible command is:

```sh
.local/simfire-venv/bin/python scripts/audit_burnmd_case.py \
  --out reports/real-fire-data/mineral-case-audit.json \
  --map-out .local/burnmd-mineral-case/mineral-case-qa.png
```

The JSON report contains summary counts and identifiers but no copied geometries. The
map is derived from the data and stays local while reuse rights are unresolved.

## What is present in this event

| Source layer | Rows | What it gives us |
| --- | ---: | --- |
| Perimeters | 11 | Fire outline observations; `PolygonDat` has 11 recorded dates from July 15–22, 2020 |
| Lines | 249 | Reported fire edges, proposed lines, roads and completed line features |
| Points | 58 | Reported operational points, including dozer pushes and drop points |

The files use WGS84 coordinates (EPSG:4326); the 318 geometries checked were non-empty
and passed the basic geometry-validity check. BurnMD gives the fire start as July 13,
2020 and containment as July 26, 2020. Of the line rows, 121 are labelled completed dozer
line and 25 completed hand line. Forty are proposed dozer lines, and 27 are uncontrolled
fire edges. The separate status field has 24 proposed and 225 approved rows.

These labels let us distinguish some kinds of map features. They do not tell us the crew
size, whether the listed line stopped the fire, or the exact time that construction began
and ended.

## Why the time fields are a real issue

The BurnMD paper says it **estimates** timestamps for line coordinates from a line's final
timestamp and assumed production rates, adjusted using fuel and terrain. It assumes a
20-person hand crew and a D6C dozer. These times are modeled estimates, not GPS-tracked
crew times. [The paper describes the calculation](https://s3.us-east-1.amazonaws.com/climate-change-ai/papers/iclr2023/19/paper.pdf).

In the exact Mineral files in the downloaded archive:

- `LineDateTi` is empty on all 249 rows.
- The per-vertex `Mitigation` field contains an empty list on all 249 rows.
- `CreateDate` and `DateCurren` contain values, but they are source-feature/database
  timestamps, not verified action start or completion times.
- The official SimFire loader ignores the per-vertex `Mitigation` field and instead starts
  from `CreateDate` and assigns a constant movement speed of 20 feet/minute for dozer
  lines and 2 feet/minute for hand lines. That is a different method from the paper's
  fuel- and terrain-dependent estimate.

So an “historical replay” based on those lines would currently invent their timing. We
should not call that a successful match to history. We can either recover the calculated
line timestamps/inputs from a version or source that provides them, or pick an incident
whose archive rows contain enough timing information.

## A second mismatch to resolve

The paper reports **308 medium-sized fires**, while this exact ZIP contains **243 distinct
state/year/fire folders**. Those counts may differ because the paper counts fires while
the ZIP organizes incident folders, or because the downloadable archive is incomplete;
we have not proven which explanation is correct. Keep this as a dataset-coverage question,
not a claim that 65 specific fires are missing. The official BurnMD repository also has an
Apache-2.0 code license but no separate data-use notice was found in the ZIP or repository
README. We therefore keep the archive and derivative map local.

## LANDFIRE connection discovered

SimFire 2.0.1's included LANDFIRE client is from 2023. The current LANDFIRE service was
reworked in 2025: official requests now use `/api/job/submit`, require the requester's
email, and return a job status/output file. SimFire still calls an older ArcGIS URL; in
our live check that path returned the LANDFIRE web page instead of JSON, so SimFire could
not parse it. The official [LFPS user guide](https://lfps.usgs.gov/LFProductsServiceUserGuide.pdf)
documents the current API.

There is also a fuel-vintage constraint. LANDFIRE's current public product catalog lists
2016, 2022 and later fuel products, but the 2019 Limited fuel update used in the published
Mineral-area SimFire example is now archived and available by contacting LANDFIRE. The
new `scripts/prepare_mineral_landfire.py` bridge requests the publicly listed
`LF2016_FBFM13` fuel layer and `LF2020_Elev` elevation layer in the band order SimFire
expects. The 2016 fuel layer is four years older than Mineral Fire, so this is only a
pre-event fallback, not a resolved scientific choice. The script's `--dry-run` works
without an email or network request. A real request needs a real `LANDFIRE_EMAIL` value
from the user; the code does not invent or store one.

```sh
.local/simfire-venv/bin/python scripts/prepare_mineral_landfire.py --dry-run
LANDFIRE_EMAIL='your address' .local/simfire-venv/bin/python \
  scripts/prepare_mineral_landfire.py
```

The second command is intentionally not part of this audit: no real address was supplied.
Once run, it will place a checksum-receipted AOI raster in SimFire's expected ignored
`.local/simfire-mineral-2020/landfire/` cache. We must then inspect the raster bounds,
band order, no-data/fuel codes and ignition position before running the historical config.

## Decision and next work

Mineral is **usable for testing geometry conversion and map display**, but it is **not
approved for a timed historical-action replay**. That replay is now optional rather than a
gate for the main policy study. BurnMD is not the chosen broad training distribution unless
data reuse rights are clarified. Finish the core scenario steps in this order:

1. Resolve BurnMD's data terms and the 243-folder/308-paper-count discrepancy.
2. Choose an as-of-event fuel layer; do not silently substitute the 2016 fallback for
   unavailable 2019 data.
3. When storage and request identity are available, request the small AOI and confirm
   raster/data alignment and ignition position.
4. Prepare weather for the actual date/location and verify its mapping into SimFire before
   calling a real-input run a valid scenario.
5. If a timestamp-enriched Mineral source is found, continue the line replay as additional
   evidence. Do not guess times from `CreateDate`.

Evidence and file hashes: [Mineral audit receipt](../../reports/real-fire-data/mineral-case-audit.json),
[archive inventory](../../reports/real-fire-data/burnmd-archive-inventory.json),
[EXP-029](EXPERIMENT_LOG.md#exp-029--burnmd-mineral-case-and-landfire-api-compatibility-audit-2026-11-01),
and [ADR-039](../specs/DECISION_RECORDS.md#adr-039--mineral-is-a-spatial-fixture-only-pending-line-time-and-landfire-gates-2026-11-01).
