# real-fire-data

## Najnoviji train-only ulazni gate

- [CFSDS train fuel QC metoda](../../docs/research/CFSDS_TRAIN_QC.md) i [mašinski čitljiv rezultat](cfsds-train-fuel-qc.json) — 20 train kandidata; 10 prolazi samo gorivnu provjeru, 10 pada; nijedan nije potvrđen kao kompletan simulator slučaj.
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
- [CFSDS replay 2018_1770](2018_1770-day224-replay.json) - zero-warmup no-action replay; 73 ha forecast versus 12.151 ha observed.
- [CFSDS map 2018_1770](2018_1770-day224.png) - input state, observed target and no-action result.
- [Fuel compatibility rejection 2014_538](2014_538-fuel-rejection.json) - geometry-screened candidate rejected at FBP nonfuel/water check.
- [CFSDS cohort screen](cfsds-cohort-screen.json) - preliminary annual candidates and event-level split counts.
- [Preuzimanje CFSDS arhive](cfsds-download-manifest.json) - sizes and checksums for ignored raw files.
- [Stvarni požari: pregled kandidata i mali uzorci](README.md) - Experiment Report
- [FireSpread_MedEU BiH spatial screen](medeu-spatial-screen.json) - provenance, checksum, candidate EFFIS IDs and crop limits
