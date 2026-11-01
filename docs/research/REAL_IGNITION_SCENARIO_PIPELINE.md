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
`MTBS_ID CA3987612137920210714`). Its 455-byte source point record is saved with its hash.
The coordinate is an incident reference point with unknown event-specific accuracy, not
confirmed GPS ignition. It gives us an approximate anchor and date for assembling a demo
landscape; it does not make this a Dixie fire replay. The case is not a representative
sample, train/test split, or scientific benchmark.

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

## First real inputs: what has been fetched and what has not

The team can reproduce the first small input bundle with the two scripts below. The source
GeoTIFFs and ERA5 response stay in ignored `.local/real-input-dixie/`; only code, scenario
metadata, hashes and small visual outputs are committed.

```sh
.local/simfire-venv/bin/python scripts/fetch_simfire_real_inputs.py
.local/simfire-venv/bin/python scripts/run_simfire_real_input_smoke.py --steps 30
```

The current example has:

- **Fuel:** official LANDFIRE LF2016 FBFM13. It predates the 2021 event by five years, so
  it is a real, pre-event fuel map, but may miss vegetation changes from 2016–2021.
- **Terrain:** official LANDFIRE LF2020 elevation, source unit meters. The project bridge
  checks the GeoTIFF and SimFire applies its own documented meter-to-foot conversion.
- **Grid:** a true 128×128, 30 m grid in local UTM (EPSG:32610), centered on the reported
  point and snapped to 30 m boundaries. LANDFIRE returns nearest-neighbor samples in that
  projected grid. The incident point remains uncertain; the pixel size does not make it
  more precise.
- **Weather context:** 24 hourly ERA5 values from 2021-07-13 requested in UTC. ERA5 is a
  reanalysis on an approximately 25 km grid, so it cannot describe 30 m wind variation.
  The saved source time `1615` has no confirmed time zone in this project, so the ERA5
  series is not aligned to that exact clock time.
- **SimFire smoke:** the real fuel and terrain arrays are used. The 30-minute animation
  still uses clearly labelled example wind/moisture. We keep ERA5 out of the run because
  SimFire expects wind near the flame, while ERA5 reports 10-m wind, and air relative
  humidity is not dead-fuel moisture. Converting one into the other needs an explicit,
  defensible model.

These outputs close **raster acquisition, alignment, source-to-array mapping and one
executable real-layer smoke**. They do not close historical-weather mapping, fuel-vintage
selection, precise ignition localization, RL runtime, or physical validation. See the
[receipt and pictures](../../reports/real-fire-data/simfire-dixie-real-input-smoke/) and
[source catalog entries S-065–S-066](SOURCES.md).

Next: compare the chosen fuel vintage against better event-year alternatives, resolve how
wind/fuel moisture enter SimFire without pretending ERA5 RH is fuel moisture, and only then
build the multi-fire event cohort and the train/validation/test split. No historical final
perimeter or line is used as agent state or as a no-action reward.

Evidence: [ADR-040](../specs/DECISION_RECORDS.md#adr-040--train-on-real-ignition-conditions-with-simulated-actions-2026-11-01),
[ADR-043](../specs/DECISION_RECORDS.md#adr-043--use-a-projected-grid-and-do-not-force-weather-variable-equivalence-2026-11-01),
[EXP-033](EXPERIMENT_LOG.md#exp-033--real-layers-fetched-and-loaded-by-simfire-2026-11-01),
[Mineral audit](MINERAL_CASE_AUDIT.md), and [SimFire environment](SIMFIRE_ENVIRONMENT.md).
