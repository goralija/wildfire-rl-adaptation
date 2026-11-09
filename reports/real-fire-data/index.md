# real-fire-data

- [FPA-FOD ↔ FEDS-CONUS ↔ FLE crosswalk](fpa-feds-fle-crosswalk-v1.json) - combined 40/20 train/validation gate; FAIL u oba splita, test nije učitan.
- [FPA-FOD/FEDS metoda i odluka](../../docs/research/FPA_FEDS_CROSSWALK.md) - izvori, metod i nastavak.
- [Train split crosswalk](fpa-feds-fle-crosswalk-train-v1.json) - 13 od 40 slučajeva prolazi strogi vremenski uslov.
- [Validation kandidatska pretraga](fpa-feds-fle-crosswalk-validation-candidate-search-v1.json) - sačuvani kandidati prije strogog 24h filtera.
- [Validation split crosswalk](fpa-feds-fle-crosswalk-validation-v1.json) - 7 od 20 slučajeva prolazi strogi vremenski uslov; izvještaj je izveden determinističkim postfilterom sačuvanih kandidata.
- [Prvobitna kohorta, lokalno ponovljen crosswalk](fpa-feds-original-cohort-crosswalk-local-v1.json) - 19/40 train i 7/20 validation; gate i dalje FAIL.
- [Prošireni candidate-frame crosswalk](fpa-feds-candidate-frame-crosswalk-v1.json) - 99/208 train i 20/56 validation; checksum-verifikovane lokalne FEDS arhive; gate PASS.
- [Episode cohort derivation](../../data/manifests/feds-episode-cohort-v1.json) - 119 epizoda s pet poludnevnih stanja kroz 48 h.
- [FEDS active-front coverage](feds-active-front-coverage-v1.json) - isti timestamp front/perimeter pronađen za 119/119 epizoda.
- [180m map preflight](feds-simfire-grid-preflight-v1.json) - početni obod i front stanu u 256×256 mrežu za 99 train i 20 validation požara.
- [gridMET archive/weather coverage](feds-gridmet-weather-coverage-v1.json) - devet arhiva s SHA-256; 396 train i 80 validation segmenta, raw-only forcing.
- [One-case SimFire input smoke](feds-simfire-input-smoke-v1.json) - Plateau real-input runtime smoke s demonstracijskim vremenom; nije no-op gate.
- [SimFire TRAIN inputs](feds-simfire-input-train-coverage-v1.json) - 99/99 početnih scar/front + LANDFIRE fuel/terrain pairs; hashes i validation status.
- [SimFire no-op pilot](feds-simfire-noop-pilot-v1.json) - jedan TRAIN Plateau slučaj; ne zaključava WAF ili timestep i nije fizička validacija.
- [TRAIN-only SimFire no-op screen](feds-simfire-train-noop-screen-v1.json) - osam WAF kandidata × 99 TRAIN slučajeva; 0/8 je prošlo persistence/elipsa gate.
- [TRAIN no-op diagnosis](feds-simfire-train-noop-diagnosis-v1.json) - reproducirani WAF .01 run; deficit IoU dolazi iz požara koji u FEDS-u gotovo ne rastu (ADR-023).
- [SimFire VALIDATION inputs](feds-simfire-input-validation-coverage-v1.json) - 20/20 validation scar/front + LANDFIRE pairs; preuzimanje je krenulo minutu prije freeze commita, bez skoriranja prije njega (ADR-024).
- [VALIDATION no-op, jednom po zapisu](feds-simfire-validation-noop-v1.json) - gate freeze pada blizu persistence; free-burn stress scenarij prolazi strogo pravilo na 20 slučajeva (ADR-024).
- [Policy benchmark i budget adaptation](feds-simfire-policy-benchmark-v1.json) - upareni heuristike/PPO na VALIDATION stress scenariju; simulatorski, ne fizički rezultat (ADR-025/026).
- [SimFire/FEDS environment](../../docs/research/SIMFIRE_ENVIRONMENT.md) - reproducibilan Python 3.9 runtime, LANDFIRE/weather setup i naredni gate.
- [Crosswalk method and data gate](../../docs/research/FPA_FEDS_CROSSWALK.md) - metod, odluke i ograničenja.

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
