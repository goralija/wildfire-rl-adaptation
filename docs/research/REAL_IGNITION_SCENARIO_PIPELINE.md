---
type: Data Pipeline Design
title: Real fire locations into SimFire scenarios
status: current-provisional
sources:
  - resource: /data/manifests/simfire-scenario.schema.json
  - resource: /docs/research/SOURCES.md
  - resource: /docs/specs/DECISION_RECORDS.md
---
# Real fire locations into SimFire

## The simpler question we can actually test

The project asks whether fine-tuning a wildfire-control agent on real-fire-derived
conditions can improve its **simulated** performance over the same frozen base agent and
simple rules. We no longer require the central experiment to replay every historical
firefighting action. That requirement made the project depend on line-construction times
that the Mineral BurnMD files do not provide.

Instead, use an incident record for its reported **place and discovery date**, then build a
fixed, pre-declared local scenario from fuel, terrain and weather available for that place
and date. The simulator generates the spread and agent experience. Historic lines and final
perimeters stay separate from the agent and its reward. This tests policy adaptation to
realistic event locations and environmental conditions; it does not claim that the agent
would have changed the real event.

## What real records and simulator each contribute

| Real-world source provides | SimFire must receive |
| --- | --- |
| Fire occurrence ID and source/release | One frozen scenario ID and provenance record |
| Reported discovery date/time and precision | Start time/window in an explicit timezone |
| Reported incident location and known location uncertainty | A row/column plus a fixed-size landscape crop; the source may not give a verified ignition |
| Fuel map and elevation for the incident region | Aligned fuel-class and elevation arrays in documented units |
| Historical weather around discovery | Weather inputs with source, time-zone and unit conversion recorded |
| Final perimeter/size, when available | A separate reference layer for a clearly labelled map, not an agent input or reward |

The common JSON contract is
[`simfire-scenario.schema.json`](../../data/manifests/simfire-scenario.schema.json), with a
blank [template](../../data/manifests/simfire-scenario.template.json). The JSON keeps
small facts and file references; GeoTIFF rasters and weather series stay as separate files
with checksums. This avoids stuffing large pixel arrays into a hard-to-review JSON file.

## Dataset choice

The practical first source is the official US Forest Service FPA-FOD occurrence service.
Its current seventh-edition sixth update covers 1992–2024 and has 2.66 million incident
points; its published core fields include discovery date, final size and location. The
source says locations are at least as precise as a one-square-mile Public Land Survey
System section, so every coordinate must carry a precision warning rather than being
treated as an exact 30-m ignition. Its identifiers can link to separate large-fire and
incident-reporting datasets. The versioned archive permits use without added permissions
or fees when cited. See [official metadata and terms](SOURCES.md#s-064).

One real record is now mapped as a plumbing example: Dixie Fire 2021 (`FOD_ID 401019270`,
`MTBS_ID CA3987612137920210714`). The 455-byte source point record is saved with its hash,
and a conversion script made a 128×128, 30-m candidate card. This lets teammates inspect
the exact `Y → JSON → fixed grid` conversion instead of only reading a blank template. It
is not a representative event sample, train/test split or runnable simulator case.

BurnMD remains an optional source for line geometry and visual context. The Mineral case
shows why those lines are not required to train the first simulator-policy experiment:
the line categories are useful, but their construction-time fields are empty. Dataset-use
terms for BurnMD also remain unresolved. No raw or geometry-derived BurnMD data are
redistributed in this pipeline.

WildfireSpreadTS is a strong independent dataset for historical daily-spread research,
with 607 events and CC BY 4.0 terms, but its complete download is 48.4 GB and requires a
separate conversion into SimFire fuel/weather inputs. It is not the first environment
setup target on a machine with very little free storage. Its role and size are documented
at [Zenodo](https://zenodo.org/records/8006177) and [S-016/S-063](SOURCES.md).

## The conversion in ordinary language

1. **Pick an event without peeking at policy results.** Save its official record ID, date,
   point, stated point precision, release and license terms.
2. **Draw the same-size square around the reported location.** Do not size the map from
   the eventual fire perimeter or later fireline. That prevents future information from
   silently changing the agent's map.
3. **Fill that square with fuel and elevation.** Download the chosen source layers, align
   them to one grid and save their hashes. Unknown fuel classes stay explicitly unknown
   until mapped or excluded.
4. **Add the weather for the actual date.** Keep local/UTC time, source grid location,
   units and every conversion. SimFire's current simple wind/moisture settings are not
   automatically historical weather; until an explicit mapping is validated, a run is
   only an integration smoke.
5. **Write one scenario JSON.** It points to the raster and weather files and records the
   simulator version, map size, chosen starting cell, seed, duration and limitations.
6. **Let each policy play the same scenario.** Base agent, fine-tuned agent and simple
   controls use identical maps, weather, duration, random seeds and action budgets. The
   fine-tuning split is by entire fire incident, never by days or tiles from the same fire.
7. **Show both the simulation and the historical context.** Animate the simulated fire
   and agent lines. If a final perimeter is available, draw it as a separate reference
   outline and say that it includes real-world firefighting and reporting effects.

## What the comparison can and cannot say

Valid claim: “On these fixed SimFire scenarios built from historical incident locations,
maps and weather, policy A produced less simulated burned area than policy B under the
same simulated line budget.”

Not supported: “The agent would have saved the same hectares in the real incident.” A
reported final size includes real response, uncertain weather, reporting choices and fuel
conditions that the simulator may not reproduce.

## What is already executable, and the remaining handoff

- SimFire 2.0.1 runs locally in an isolated Python 3.9.25 environment; the saved GIF/map
  is a functional synthetic smoke, not this real-event path.
- A project-owned current-LFPS adapter can read either Mineral or a scenario JSON. Its dry
  run produces the fixed AOI/cache path for both Mineral and Dixie; the smoke runner can
  read the same manifest once a GeoTIFF exists.
- The Dixie raster fetch is not complete because this shell has no `LANDFIRE_EMAIL`. Disk
  space is 3.0 GiB at the 2026-11-01 check; the earlier 29-MiB warning is stale.
  SimHarness/RLlib is also not installed or selected for this host.
- The adapter's public-catalog fuel fallback is LF2016_FBFM13, four years before Mineral;
  it is a technical input candidate, not a vetted scientific vintage. The archived
  2019-Limited layer is not in the current public catalog.

Next implementation step: prepare and validate real fuel/elevation layers and dated weather
for the saved Dixie candidate, then produce the first real-input map/animation. This closes
the data-to-simulator path before we build a larger, reproducible FPA-FOD development/train/
held-out event sample. Historical line replay can continue separately if a version with
usable line times is found, but it no longer blocks the core RL question.

Evidence: [ADR-040](../specs/DECISION_RECORDS.md#adr-040--train-on-real-ignition-conditions-with-simulated-actions-2026-11-01),
[EXP-030](EXPERIMENT_LOG.md#exp-030--scenario-based-design-and-fpa-fod-source-review-2026-11-01),
[Mineral audit](MINERAL_CASE_AUDIT.md), and [SimFire environment](SIMFIRE_ENVIRONMENT.md).
