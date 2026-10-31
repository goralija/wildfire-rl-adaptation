# real-fire-data

## Najnoviji train-only ulazni gate

- [CFSDS train fuel QC metoda](../../docs/research/CFSDS_TRAIN_QC.md) i [mašinski čitljiv rezultat](cfsds-train-fuel-qc.json) — 20 train kandidata; 10 prolazi samo gorivnu provjeru, 10 pada; nijedan nije potvrđen kao kompletan simulator slučaj.
- [CFSDS train input QC](../../docs/research/CFSDS_TRAIN_INPUT_QC.md) i [mašinski čitljiv rezultat](cfsds-train-input-qc.json) — poravnanje izmjereno za 3/20 dostupnih train FireCase paketa; fuel vintage nije potvrđen kao vremenski siguran, suppression ostaje unknown.
- [CFSDS TRAIN fuel-vintage mask proof](cfsds-train-fuel-vintage-mask-proof.json) — `2018_747` pre-target maska isključuje target dan i kasnije; godišnja fuel mapa nije izrađena dok se ne potvrde bazni cutoff i succession crosswalk.
- [CFSDS TRAIN fuel source gate](cfsds-train-fuel-source-gate.json) — v2014b ne navodi NFDB/NBAC cutoff; javno navedeni v20191114 decision-rules PDF pokriva bazne fuel klase, a ne post-fire age succession.
- [CFSDS target-blind input invariance proof](cfsds-target-blind-input-invariance.json) — TRAIN `2018_747`; promjena day-n maske ne mijenja crop, 20×20 početni scar/front ni `InitialState.csv`.
- [CFSDS TRAIN target-blind window screen](cfsds-train-target-blind-window-screen.json) — samo 2014–2018 TRAIN; target coverage je post-selection dijagnostika, 4/25 prozora imaju ikakav target pixel.
- [CFSDS TRAIN prostorni feasibility audit](cfsds-train-spatial-feasibility.json) — poređenje 2–6 km domena na istih 25 TRAIN parova; target dijagnostika je post-selection, bez FireCase-a ili replaya.
- [CFSDS puni TRAIN target-independent day-pair screen](../../docs/research/CFSDS_FULL_DAY_PAIR_SCREEN.md), [JSON receipt](cfsds-train-full-day-pair-screen.json) i [1301-case/domain CSV](cfsds-train-full-day-pair-screen.csv) — svih 1.301 TRAIN rastera, pet unaprijed definisanih domena, 1.010 target-opaženih i 291 bez mapiranih target piksela; bez simulator replaya.
- [CFSDS no-action dijagnostika](../../docs/research/CFSDS_NO_ACTION_DIAGNOSIS.md) i [mašinski čitljiva vremenska analiza](cfsds-no-action-timeline.json) — tri sačuvana train replaya, bez novog C++ runa, kalibracije ili treninga.

## Dokumenti

- [CFSDS pilot `2018_747` case manifest](2018_747-case.json) - public source versions, conversion decisions and input checksums.
- [CFSDS pilot replay](2018_747-day228-replay.json) - one compiled C++ no-action run, observed-growth comparison and limitations.
- [CFSDS pilot seed repeats](2018_747-seed-sweep.json) - six no-action seeds on the same inputs, final-map repeatability and boundary contact.
- [CFSDS pilot map](2018_747-day228.png) - fuel, starting scar/front, observed next-day growth and simulator result.
- [CFSDS train case 2018_241](2018_241-case.json) - converted case provenance and input details.
- [CFSDS replay 2018_241](2018_241-day227-replay.json) - zero-warmup no-action replay; 237 ha forecast versus 12.153 ha observed.
- [CFSDS replay 2018_241 with warmup](2018_241-day227-replay-warmup20.json) - comparison showing the 20-minute pre-simulation did not change final metrics.
- [CFSDS map 2018_241](2018_241-day227.png) - input state, observed target and no-action result.
- [CFSDS train case 2018_1770](2018_1770-case.json) - converted case provenance and input details.
- [TRAIN-only BC historical perimeter crosswalk](cfsds-train-bc-perimeter-crosswalk.json) - candidate official BC incident IDs for the three saved 2018 TRAIN cases; no suppression/action observations.
- [TRAIN-only BC operational evidence](cfsds-train-bc-operational-evidence.json) - dated public suppression reports/status for candidate incidents N12395, C11937, N12413; partial snapshots, not a complete daily resource/action table.
- [CFSDS replay 2018_1770](2018_1770-day224-replay.json) - zero-warmup no-action replay; 73 ha forecast versus 12.151 ha observed.
- [CFSDS map 2018_1770](2018_1770-day224.png) - input state, observed target and no-action result.
- [Fuel compatibility rejection 2014_538](2014_538-fuel-rejection.json) - geometry-screened candidate rejected at FBP nonfuel/water check.
- [CFSDS cohort screen](cfsds-cohort-screen.json) - preliminary annual candidates and event-level split counts.
- [Preuzimanje CFSDS arhive](cfsds-download-manifest.json) - sizes and checksums for ignored raw files.
- [Stvarni požari: pregled kandidata i mali uzorci](README.md) - Experiment Report
- [FireSpread_MedEU BiH spatial screen](medeu-spatial-screen.json) - provenance, checksum, candidate EFFIS IDs and crop limits
