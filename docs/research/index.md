# Istraživanje i podaci

## Dokumenti

- [Dataset: šta imamo i šta ćemo koristiti](DATASET.md) - Dataset Review
- [Experiment log](EXPERIMENT_LOG.md) - Experiment Log
- [Firehose/Cell2Fire izvršavanje — 2026-10-28](FIREHOSE_VERIFICATION.md) - Verification Record
- [Istraživački protokol — draft v1, 2026-10-28](PROTOCOL.md) - Research Protocol
- [Stvarni požari: izbor podataka i granica zaključaka](REAL_FIRE_DATASETS.md) - Dataset Review
- [Train-only CFSDS fuel QC](CFSDS_TRAIN_QC.md) - Metoda, nalaz i ograničenja prvog train input gatea
- [Train-only CFSDS input QC](CFSDS_TRAIN_INPUT_QC.md) - Poravnanje dostupnih train FireCase mapa, weather inputa, fuel vintagea i suppression evidencije
- [TRAIN BC perimeter crosswalk](../../reports/real-fire-data/cfsds-train-bc-perimeter-crosswalk.json) - Tri target-centroid matcha na službene BC požare; ID-ji za provjeru, bez akcija gašenja
- [TRAIN BC operational evidence](../../reports/real-fire-data/cfsds-train-bc-operational-evidence.json) - Dnevni javni izvještaji za dva od tri kandidata, s razlikom između cilj-dana i okolnih dana; nije dnevnik dispečiranja
- [EXP-021: BC status snapshot follow-up](EXPERIMENT_LOG.md#exp-021--train-only-bc-incident-status-snapshot-follow-up-2026-10-31) - Službeni PECC statusi za dva kandidata; dvije verzije navode različite procjene za isto vrijeme i ne daju akcije gašenja
- [TRAIN-only CFSDS fuel-vintage review](CFSDS_FUEL_VINTAGE_REVIEW.md) - Službeni izvori za istorijski cutoff, javno transkribovanu W.I.S.E. Figure 2, neriješenu age/class semantiku i reuse uslove
- [TRAIN-only fuel source-gate receipt](../../reports/real-fire-data/cfsds-train-fuel-source-gate.json) - Šta zvanični metadata i javno navedeni v20191114 dokumenti dokazuju, a šta ne
- [TRAIN terrain/weather provenance receipt](../../reports/real-fire-data/cfsds-train-terrain-weather-provenance.json) - MRDEM source-class check i pinovani target-blind ERA5-Seamless odgovori za tri stare dijagnostičke slučajeve; source vintage i legacy weather mismatch ostaju otvoreni
- [TRAIN-only CFSDS prostorna podobnost](CFSDS_SPATIAL_FEASIBILITY.md) - Poređenje unaprijed zadanih target-blind domena na istim TRAIN parovima
- [Puni TRAIN target-independent day-pair screen](CFSDS_FULL_DAY_PAIR_SCREEN.md) - 1.301 CFSDS rastera i pet fiksnih domena; target metrics samo post-selection dijagnostika
- [Puni TRAIN fuel-class overlay](CFSDS_FULL_TRAIN_FUEL_OVERLAY.md) - 1.301 target-independent parova overlayanih na v2014b; class-only nalazi, bez annual fuel mape ili replaya
- [EXP-022: full TRAIN fuel-class overlay](EXPERIMENT_LOG.md#exp-022--full-train-fuel-class-overlay-on-target-blind-pairs-2026-10-31) - 701 pass-only, 64 review, 530 fail, 6 bez prozora
- [EXP-023: embedded v20191114 burn-scar rules](EXPERIMENT_LOG.md#exp-023--v20191114-archive-burn-scar-rules-and-v2014b-member-review-2026-10-31) - mali rule fajl pregledan iz 2.68 GB ZIP-a bez preuzimanja karte
- [EXP-024: W.I.S.E. suppression exclusion and burn-history dates](EXPERIMENT_LOG.md#exp-024--wise-suppression-exclusion-and-national-burn-history-dating-2026-10-31) - dokumentovan uslov da `unknown` gašenje nije isto što i `none`; provjereni su i službeni NBAC vremenski metapodaci
- [CanFG archive member review](../../reports/real-fire-data/canfg-fuel-archive-member-review.json) - ZIP unosi, byte ranges i hashovi; v2014b cutoff ostaje nepoznat
- [Kako su raniji radovi pripremali i provjeravali stvarne požare](CFSDS_PRIOR_WORK_AND_PLAIN_EXPLANATION.md) - CFSDS, W.I.S.E., Dogrib/Cell2Fire i Firehose, te laičko objašnjenje šta još blokira validan eksperiment
- [Provjereni tok prilagođen našem projektu](ADAPTED_PRIOR_ART_WORKFLOW.md) - šta preuzimamo iz W.I.S.E., Dogrib/Cell2Fire i Firehose, kako izbjegavamo poznate zamke i kako čuvamo podatke za buduće mape/animacije
- [Dogrib geografska QA karta](../../reports/real-fire-data/dogrib-reference-alignment.png) - georeferencirana kontrola goriva, terena, perimetara, paljenja i opaženog scara; nije simulator replay
- [Dogrib QA receipt](../../reports/real-fire-data/dogrib-reference-alignment.json) - mašinski čitljive koordinate, vremenski raspon i otvorena neslaganja
- [EXP-010: fuel-vintage mask proof](EXPERIMENT_LOG.md#exp-010--train-only-pre-target-fuel-mask-and-nf-scar-importer-characterization-2026-10-31) - TRAIN-only vremenska maska i raniji expected-rejection nalaz
- [EXP-011: target-blind CFSDS početno stanje](EXPERIMENT_LOG.md#exp-011--train-only-target-blind-crop-and-initial-state-proof-2026-10-31) - target-mask invariance na TRAIN `2018_747` i 2014–2018 crop coverage dijagnostika
- [EXP-015: NF historical-scar importer contract](EXPERIMENT_LOG.md#exp-015--explicit-nonfuel-historical-scar-importer-contract-2026-10-31) - C++ import i cumulative-damage provjera za eksplicitno označene scar ćelije
- [CFSDS no-action dijagnostika](CFSDS_NO_ACTION_DIAGNOSIS.md) - Vremenski presjeci, FWI/weather, rub mreže i završni uslovi na tri train slučaja
- [Od stvarnog požara do Cell2Fire scenarija](REAL_CASE_PIPELINE.md) - Data Pipeline Design, X/Y format i ograničenja
- [Zahtjevi i kriteriji profesora](REQUIREMENTS_AND_RUBRIC.md) - Requirements
- [Simulator i pretrained feasibility audit](SIMULATOR_AUDIT.md) - Audit
- [Izvori i literatura](SOURCES.md) - Reference
