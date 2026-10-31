---
type: Audit
title: TRAIN-only CFSDS fuel-map vintage and provenance review
description: Public-source review of historical Canadian FBP map timing, fuel-class rules, burn-scar succession documentation, and reuse terms.
status: recorded
sources:
  - resource: /docs/research/SOURCES.md
  - resource: /docs/research/CFSDS_TRAIN_INPUT_QC.md
  - resource: /reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json
---
# TRAIN-only CFSDS fuel-map vintage and provenance review

## Scope

This review follows the all-TRAIN target-independent day-pair/domain screen in
[EXP-013](EXPERIMENT_LOG.md#exp-013--full-train-target-independent-cfsds-day-pair-and-domain-screen-2026-10-31).
It asks whether an existing national Canadian FBP fuel raster can be treated as an
as-of-event input for CFSDS targets in 2014–2018 and whether the public rules are enough
to recreate the post-fire fuel succession used in the published W.I.S.E. assessment.
The review includes public metadata, a complete member-name inventory of the local
v2014b ZIP, and byte-range inspection of selected small files inside the official
v20191114 archive. The v20191114 fuel raster itself was not downloaded or inspected;
validation/test data were not opened.

The existing v2014b raster was used only for a train-only spatial fuel-class overlay;
no fuel map was generated or reclassified. No new FireCase, Cell2Fire replay,
calibration, benchmark, or training was run. Saved pilot files remain unchanged.

## Evidence by source vintage

| Source | Documented evidence | TRAIN use decision |
| --- | --- | --- |
| National FBP v2014b, 250 m | The complete 13-member local ZIP contains the raster, metadata, legend and GIS sidecars, but no separate burn-scar rule file. The PDFs name 2011 land cover, CanFI2000, ecological layers and NFDB/NBAC, without dated per-pixel lineage or an explicit burn-record cutoff. | Keep for exact reproduction of saved pilot files and class-only screening. Do not label it as an as-of-event map for new cases until its cutoff is verified. |
| Canadian Forest FBP v20191114, 250 m | The metadata lists a 2017 kNN forest inventory and NBAC; the 170-member ZIP index contains `docs/Burn Scar Rules.txt`. That file gives fire-age classes and says the rules used an NFDB update dated 2018-07-26 for fires over 50 ha. It also flags a region-dependent 6–21-year interval. | Do not use this later base map directly for 2014–2018 targets. Its rule text helps describe succession, but does not supply the missing v2014b cutoff or fully define age/calendar and regional-boundary arithmetic. |
| FBP Fuel Types 2024, 30 m | Official portal metadata gives 2020-08-01 through 2024-04-01 coverage and lists SCANFI, ecozones, and NBAC. | Postdates all current TRAIN targets; not a historical baseline for this cohort. |
| FBP Fuel Types 2026, 250 m current-year product | The current product description says annual maps are updated before fire season with burned-area and other information from the previous year, with publication scheduled by 30 April. | Useful evidence for the current publication convention. It does not prove when the v2014b raster or its NBAC/NFDB layer was frozen. |

The `2014b` version name and the 2011 land-cover input are not enough to establish the
cutoff of the separate burn-scar layer. The official metadata does not state when the
NFDB/NBAC snapshots were taken or whether that layer was revised after the 2014 fire
season. Therefore this review cannot certify an as-of-event cutoff for any new 2014–2018
case. A pre-season annual update convention observed on the current 2026 product cannot
be projected backward to v2014b without historical release documentation.

## What the published rules do and do not establish

The official v20191114 ZIP can be indexed without downloading its 2.68 GB raster: a
65,536-byte end-of-file range and the 13,417-byte central directory identify all 170
members. The index lists a small `docs/Burn Scar Rules.txt` file as well as baseline
classification documents and five R scripts. We range-extracted that text file (1,737
bytes after decompression) and one baseline classifier script. The classifier script
builds fuel classes from kNN/species/ecozone/land-cover inputs; it does not use fire
dates to apply succession. No separately named age-succession program appears in the
complete ZIP member list. This does not rule out an external manual GIS procedure.

The rules text states that scars from fires over 50 ha are treated as follows: 1–2 years
as Non-Fuel, 3–5 years as D-2, 6–21? years as M-2 C25, and older than 21 years as C-2.
It keeps O-1 as O-1 and preserves Water and Non-Fuel. It explicitly notes that the
6–21-year M-2 window may vary by region. For an NFDB update dated 2018-07-26, it lists
2016–2017 as Non-Fuel, 2013–2015 as D-2, and 2010–2012 as M-2 C25; 2010–2011 are
separated in the raster stack because the 2011 imagery initially classifies them as
Non-Fuel. The ZIP also gives layer precedence. These details substantially corroborate
the [W.I.S.E. Figure 2 transcription](#figure-2-transcription), but the question mark
and regional caveat mean the exact age cut and geographic lookup are still unresolved.

The official 2018 *FBP Fuel Layer Decision Rules* and *FBP Fuel Layer Base Layers*
documents describe how inventory, species, vegetation, land-cover and ecological data
are classified into baseline FBP fuel classes. They are useful provenance for how a fuel
code is assigned, but they are not the age-succession implementation. The base-layer
document also says kNN NFI v1 layers are available on request and some Agriculture Canada
land-cover input was under a data-sharing agreement; rebuilding the national base map
from public PDFs alone is not established.

The W.I.S.E. paper describes generating yearly fuel maps from the 2014, 2019, and 2024
FBP map releases by applying prior fire perimeters and a succession ruleset associated
with v20191114. It separately says that, for a day-n simulation, the same fire's pixels
with arrival day before n are set to non-fuel. These are two different transformations:

1. Annual/background fuel history: assign the post-fire class for older burn scars.
2. Current-event simulation mask: prevent the current fire's pre-target scar from
   burning again.

The paper's Figure 2 publicly shows the decision tree for the first transformation, and
the archive text now independently confirms its broad age classes and special cases.
The article data statement offers study data from the corresponding author upon
reasonable request. The internal text still does not define the exact calendar/date
arithmetic or the regional boundary for the 6–21-year M-2 interval. The burn-scar PDF
is a class legend, not an executable succession algorithm. The 2.68 GB archive raster
was not downloaded; only its central directory and selected small text members were
inspected. See the [member-review receipt](../../reports/real-fire-data/canfg-fuel-archive-member-review.json)
and source [S-032](SOURCES.md).
The second transformation has a local TRAIN-only temporal-mask proof for `2018_747`,
but the proof does not create an annual fuel layer. The paper also selects its active
boundary using day-n adjacency and acknowledges that this uses future information;
that input rule is not adopted here.

### Figure 2 transcription

The published decision tree reads as follows:

1. If the pre-fire fuel type is Grass (O-1), keep it as Grass (O-1), regardless of
   time since fire.
2. Otherwise, if more than 21 years have elapsed, assign Spruce (C-2).
3. Otherwise, if more than 5 years have elapsed, assign Mixedwood (M-2, C25%).
4. Otherwise, if more than 2 years have elapsed, assign Aspen (D-2).
5. Otherwise, assign Non-Fuel.

This is a transcription of the publisher's figure, not a claim that the project has
reproduced the full NRCan v20191114 release or independently validated its age-counting
convention. The figure does not state how fractional years, calendar-year boundaries,
fire dates, pre-existing scar classes, or nodata/water/urban classes are handled. The
paper's Figure 2 is the only public description located for these age thresholds; the
underlying executable implementation remains unverified. A separate CWFIS description
of its 2015 operational fuel grid says last-year burns were mapped as non-fuel and burns
from the prior two years as grass; that is a different, simpler historical product rule
and cannot be substituted for the v20191114 tree [S-042].

## Reuse terms

The CWFIS download-site licence notice states that downloaded data are under the Open
Government Licence - Canada and requests attribution to the Canadian Forest Service /
CWFIS. This corrects the earlier finding based only on the individual archive listings,
where no licence statement appeared. No product-specific exception was found in the
reviewed v2014b and v20191114 listing/metadata. Separately sourced component layers may
carry their own terms, and the 2018 base-layer notes identify at least one source-data
sharing agreement. The project should preserve CWFIS attribution and check component
terms if it later reconstructs or redistributes derived layers.

## Decision and requirements before map generation

**Decision:** preserve the existing v2014b-based pilot inputs for exact reproduction,
but do not describe v2014b as a verified as-of-event base for new cases. Do not directly
use v20191114, 2024, or 2026 layers as TRAIN-era baseline maps. The internal v20191114
burn-scar text now corroborates the broad W.I.S.E. Figure 2 succession classes and gives
an NFDB snapshot date for that later release, but it does not resolve the v2014b
NFDB/NBAC cutoff, the regional 6–21-year threshold, exact date arithmetic, or the
independently executable succession procedure. A full TRAIN overlay also shows that
class compatibility on v2014b alone is insufficient: 530/1,295 starting windows fail
the class-overlap check, 64 need sub-cell review, and 701 pass only this narrow check.
General CWFIS download reuse terms are documented as Open Government Licence - Canada
with attribution, but that does not resolve temporal leakage or every source-layer
condition. No annual fuel map is selected or emitted.

Before an annual map can be used, the project needs:

1. An authoritative date/cutoff for the base map's burn-history inputs, suitable for
   the target year. If none can be obtained, mark the vintage unresolved and do not
   claim leakage-safe fuel inputs.
2. Resolve the v20191114 rule text's exact age/calendar arithmetic and region-specific
   6–21-year M-2 threshold, and confirm how its stated layer order applies at overlaps.
   Preserve its explicit O-1, Water, Non-Fuel and >50 ha rules. The internal R classifier
   is for baseline fuel classes, not this age succession; no standalone succession
   program was found in the complete ZIP index. Do not invent a regional threshold or
   infer classes from the legend.
3. A frozen, target-independent history mask: only fires/burn days dated before target
   day n may alter the input; day n and later arrivals must be excluded. Retain the
   tested invariant `arrival_day < target_doy` for the current event.
4. Per-cell lineage for the generated layer: source class and map version, any burn
   event/date used, succession rule applied, and resampling/aggregation method into the
   simulator grid.
5. An importer contract for historically burned cells whose starting fuel class is
   non-fuel. This is now specified with an explicit `scar_nf` initial-state value: only
   the exact `NF` fuel code may use it, the cell remains in cumulative historical damage,
   and it is excluded from active fire spread. Generic `burnt` on `NF`, active `burning`
   on non-fuel, and `scar_nf` on fuel remain invalid. See
   [ADR-025](../specs/DECISION_RECORDS.md#adr-025) and the versioned contract receipt.

The rules file narrows the succession question, but does not resolve the map gate. The
CFSDS case builder still rejects initial nonfuel/water overlaps, and no annual map or
new FireCase is generated until the dated base-map source, age convention, regional
threshold, special-class handling, and per-cell provenance in items 1–4 are verified.
The `scar_nf` token must not be used merely because an event-arrival layer overlaps a
generic `NF` class; that overlap could reflect water, urban, no-data, or another mapping
error rather than a post-fire succession class.

Evidence and source detail: [source register S-031–S-049](SOURCES.md), [input QC](CFSDS_TRAIN_INPUT_QC.md),
[CFSDS full TRAIN fuel overlay](CFSDS_FULL_TRAIN_FUEL_OVERLAY.md),
[archive member receipt](../../reports/real-fire-data/canfg-fuel-archive-member-review.json),
[full TRAIN fuel overlay receipt](../../reports/real-fire-data/cfsds-full-train-fuel-overlay.json),
[pre-target mask proof](../../reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json),
[fuel source gate receipt](../../reports/real-fire-data/cfsds-train-fuel-source-gate.json),
[historical importer characterization](../../reports/firehose-verification/nonfuel-initial-scar-compatibility.json),
[contract receipt](../../reports/firehose-verification/nonfuel-initial-scar-contract.json),
[ADR-024](../specs/DECISION_RECORDS.md#adr-024), and
[ADR-025](../specs/DECISION_RECORDS.md#adr-025).
