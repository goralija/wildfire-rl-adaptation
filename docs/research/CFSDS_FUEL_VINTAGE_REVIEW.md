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
The audit is limited to public metadata and documentation; it does not inspect
validation/test data.

No fuel raster was downloaded, generated, or reclassified in this review. No FireCase,
Cell2Fire replay, calibration, benchmark, or training was run. The 2014b raster remains
only as the recorded source for reproducing the existing pilot files.

## Evidence by source vintage

| Source | Documented evidence | TRAIN use decision |
| --- | --- | --- |
| National FBP v2014b, 250 m | Land Cover Map of Canada 2011, CanFI2000, ecological layers, and NFDB/NBAC are listed; NFDB/NBAC helped identify burn scars. No dated per-pixel lineage or explicit burn-record cutoff is stated. | Keep for exact reproduction of saved pilot cases. Do not label it as an as-of-event map for new cases until its cutoff is verified. |
| Canadian Forest FBP v20191114, 250 m | Metadata lists 2017 kNN forest inventory and says NBAC was used to reassign fuel types in burned areas. It is listed in a development directory at about 2 GB. No per-pixel NBAC cutoff is stated. | Do not use directly as the baseline for 2014–2018 targets: the underlying inventory/map vintage is later than those events and the burn-record cutoff is unspecified. The archive was not downloaded. |
| FBP Fuel Types 2024, 30 m | Official portal metadata gives 2020-08-01 through 2024-04-01 coverage and lists SCANFI, ecozones, and NBAC. | Postdates all current TRAIN targets; not a historical baseline for this cohort. |
| FBP Fuel Types 2026, 250 m current-year product | The current product description says annual maps are updated before fire season with burned-area and other information from the previous year, with publication scheduled by 30 April. | Useful evidence for the current publication convention. It does not prove when the v2014b raster or its NBAC/NFDB layer was frozen. |

The `2014b` version name and the 2011 land-cover input are not enough to establish the
cutoff of the separate burn-scar layer. The official metadata does not state when the
NFDB/NBAC snapshots were taken or whether that layer was revised after the 2014 fire
season. Therefore this review cannot certify an as-of-event cutoff for any new 2014–2018
case. A pre-season annual update convention observed on the current 2026 product cannot
be projected backward to v2014b without historical release documentation.

## What the published rules do and do not establish

The CWFIS directory includes official 2018 documents called *FBP Fuel Layer Decision
Rules* and *FBP Fuel Layer Base Layers*. These describe how inventory, species,
vegetation, land-cover and ecological data are classified into baseline FBP fuel
classes. They are useful provenance for how a fuel code is assigned. They are not the
post-fire burn-scar succession crosswalk cited by the W.I.S.E. paper. The base-layer
document also says the kNN NFI v1 layers are available on request and that some
Agriculture Canada land-cover input was under a data-sharing agreement; consequently,
rebuilding the national base map from its component layers is not established by the
public PDFs alone.

The W.I.S.E. paper describes generating yearly fuel maps from the 2014, 2019, and 2024
FBP map releases by applying prior fire perimeters and a succession ruleset associated
with v20191114. It separately says that, for a day-n simulation, the same fire's pixels
with arrival day before n are set to non-fuel. These are two different transformations:

1. Annual/background fuel history: assign the post-fire class for older burn scars.
2. Current-event simulation mask: prevent the current fire's pre-target scar from
   burning again.

The paper identifies a decision-tree figure for the first transformation, but its text
does not enumerate the rule branches and it does not provide a public code/data archive;
its data statement offers data from the corresponding author upon reasonable request.
The public CWFIS FBP classification-rules PDF is not a substitute for that burn-scar
tree. The second transformation has a local TRAIN-only temporal-mask proof for
`2018_747`, but the proof does not create an annual fuel layer. The paper also selects
its active boundary using day-n adjacency and acknowledges that this uses future
perimeter information; that input rule is not adopted here.

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
use v20191114, 2024, or 2026 layers as TRAIN-era baseline maps. General CWFIS download
reuse terms are documented as Open Government Licence - Canada with attribution, but
that does not resolve temporal leakage or every source-layer condition. No annual fuel
map is selected or emitted.

Before an annual map can be used, the project needs:

1. An authoritative date/cutoff for the base map's burn-history inputs, suitable for
   the target year. If none can be obtained, mark the vintage unresolved and do not
   claim leakage-safe fuel inputs.
2. A complete, source-verifiable post-fire succession mapping from input fuel class and
   burn-age band to output class, including treatment of no-data, water, non-fuel,
   urban, and ambiguous classes. Record the source figure/rules version and a reviewed
   transcription; do not infer the tree from the legend or base-classification rules.
3. A frozen, target-independent history mask: only fires/burn days dated before target
   day n may alter the input; day n and later arrivals must be excluded. Retain the
   tested invariant `arrival_day < target_doy` for the current event.
4. Per-cell lineage for the generated layer: source class and map version, any burn
   event/date used, succession rule applied, and resampling/aggregation method into the
   simulator grid.
5. An importer contract for historically burned cells whose starting fuel class is
   non-fuel. The current C++ importer rejects a `burnt` initial state on `NF`, so
   annual classification must not silently rewrite either the fuel or damage state.

The immediate next implementation task can progress independently: define and test the
historical-scar/importer contract using a small TRAIN-only fixture while keeping annual
fuel generation blocked on items 1–4. Then return to the missing dated-source and
succession evidence before materializing any new simulator case.

Evidence and source detail: [source register S-031–S-041](SOURCES.md), [input QC](CFSDS_TRAIN_INPUT_QC.md),
[pre-target mask proof](../../reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json),
[NF-scar importer receipt](../../reports/firehose-verification/nonfuel-initial-scar-compatibility.json),
and [ADR-024](../specs/DECISION_RECORDS.md#adr-024).
