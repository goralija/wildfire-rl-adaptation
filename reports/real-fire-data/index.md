# real-fire-data

- [Paired PPO preflight](paired-ppo-preflight-v1.json) - TASK-043:61ulaz/122reference/16parity/132native putanje PASS, reuse stare fizike.
- [Paired PPO verifikacija](paired-ppo-verification-v1.json) -408pinned testova i start u pozadini; finalni learning još u toku.
- [Paired PPO launch](paired-ppo-launch-v1.json) - historijski PID/komanda; živo stanje čitati lokalno prije nastavka.

- [Zajednički PPO tehnički smoke](common-ppo-smoke-v1.json) - TASK-040 B.1/ADR-050, sve4kratke probe i36kontrolnih/replay putanja; bez rankinga.
- [Nezavisna provjera ugovora](common-ppo-independent-v1.json) - whole maske, union/reward i raspored.
- [Common PPO verifikacija](common-ppo-verification-v1.json) - testovi, source/plan hashovi i pokušaji.
- [Common PPO lokalni paket](common-ppo-artifacts-v1.json) - hash217fajlova, nije uploadovan.
- [Common PPO restore](common-ppo-restore-v1.json) -4numeric modela,12putanja iz obnovljenog sourcea/ulaza.

- [V2 objava i CI](feds-observation-repair-publication-v2.json) - push grane, sva četiri CI posla PASS na1cabe778, bez novog PR-a/mergea.

- [V2 repair coverage](feds-observation-repair-coverage-v2.json) -98 replayeva,392 opažanja,3136 candidate geometrija; legacy i whole-noop PASS.
- [V2 svi nested rezultati](feds-observation-repair-analysis-v2.json) -4 reprezentacije×2 maske×2 obračuna; niko ne prelazi prag; [grafikon](feds-observation-repair-v2.png).
- [V2 fiksne heuristike](feds-observation-repair-heuristics-v2.json) -fine+gate 123,72 charged ha; +22,68 prema starom pravilu, širok opisni interval.
- [V2 native replay provjera](feds-observation-repair-native-v2.json) -7/7 tehničkih putanja po cijeloj maski, nije novi performance uzorak.
- [V2 verification](feds-observation-repair-verification-v2.json) -344/344 pinovani suite, source/log hashovi; [izvještaj](../../docs/research/SIMFIRE_OBSERVATION_REPAIR.md).
- [V2 lokalni paket](feds-observation-repair-artifact-manifest-v2.json) -stari ulazi/ishodi i novi v2 podaci/kod, bez velikih podataka u Gitu.

- [TASK-034 input/observation audit](feds-observation-input-audit-v1.json) - 98 inputa, raster CRS/transform, 392 opažena weather zapisa; sva provjera PASS, aliasing i nonfuel opisani.
- [TASK-034 nested politike](feds-observation-offline-v1.json) - četiri porodice, svi OOF izbori; nijedna ne prelazi prag; [grafikon](feds-observation-offline-v1.png).
- [Native numerička osjetljivost](feds-native-sensitivity-v1.json) - dva dijagnostička TRAIN slučaja, 20 uspješnih rollouta; locked maske PASS, alternative nisu novi gate.
- [TASK-034 tehnička provjera](feds-observation-verification-v1.json) - 327/327 pinovani suite, startup race i regresija, source/engine hashovi; nije fizička validacija.
- [TASK-034 lokalni paket](feds-observation-artifact-manifest-v1.json) - puni ulazi/stara tabela plus novi rezultati, native maske i izvorni kod; [tumačenje](../../docs/research/SIMFIRE_OBSERVATION_AUDIT.md).

- [SimFire B=1 provjerena tabela](feds-b1-table-check-v1.json) - 98×33 ishoda, svi input/mask/reference checkovi PASS, ADR-032 agregati se poklapaju, bez ruba.
- [SimFire B=1 sve offline metode](feds-b1-offline-v1.json) - osam metoda, LOO po požaru, raw/charged; nijedna ne prelazi prag; [grafikon](feds-b1-offline-v1.png), [tumačenje](../../docs/research/SIMFIRE_B1_EXPLORATION.md).
- [SimFire B=1 lokalni paket artefakata](feds-b1-artifact-manifest-v1.json) - hash prenosive lokalne arhive: 98 TRAIN ulaza, tačan weather, puna tabela i izvorni kod; nije uploadovana.

- [SimFire B=1 TRAIN-only weather](feds-b1-train-weather-v1.json) - 98 slučajeva, 392 segmenta + 98 pre-start zapisa, šest izvornih arhiva s hashovima; bez validation/test vrijednosti.
- [SimFire B=1 tehnička provjera](feds-b1-verification-v1.json) - 314/314 u pinovanom runtimeu, verzije i hashovi; [postupak TASK-028–030](../../docs/research/SIMFIRE_B1_EXPLORATION.md).

- [FPA-FOD ↔ FEDS-CONUS ↔ FLE crosswalk](fpa-feds-fle-crosswalk-v1.json) - combined 40/20 train/validation gate; FAIL u oba splita, test nije učitan.
- [FPA-FOD/FEDS metoda i odluka](../../docs/research/FPA_FEDS_CROSSWALK.md) - izvori, metod i nastavak.
- [Train split crosswalk](fpa-feds-fle-crosswalk-train-v1.json) - 13 od 40 slučajeva prolazi strogi vremenski uslov.
- [Validation kandidatska pretraga](fpa-feds-fle-crosswalk-validation-candidate-search-v1.json) - sačuvani kandidati prije strogog 24h filtera.
- [Validation split crosswalk](fpa-feds-fle-crosswalk-validation-v1.json) - 7 od 20 slučajeva prolazi strogi vremenski uslov; izvještaj je izveden determinističkim postfilterom sačuvanih kandidata.
- [Prvobitna kohorta, lokalno ponovljen crosswalk](fpa-feds-original-cohort-crosswalk-local-v1.json) - 19/40 train i 7/20 validation; gate i dalje FAIL.
- [Prošireni candidate-frame crosswalk](fpa-feds-candidate-frame-crosswalk-v1.json) - 99/208 train i 20/56 validation; checksum-verifikovane lokalne FEDS arhive; gate PASS.
- [Episode cohort derivation](../../data/manifests/feds-episode-cohort-v1.json) - 118 epizoda (98 train, 20 validation) s pet poludnevnih stanja kroz 48 h; duplikat FEDS požara 58826 isključen po ADR-030 §6 (TASK-027). Coverage i preflight izvještaji ispod su izrađeni na ranijih 119 i sadrže i isključeni zapis.
- [FEDS active-front coverage](feds-active-front-coverage-v1.json) - isti timestamp front/perimeter pronađen za 119/119 epizoda.
- [180m map preflight](feds-simfire-grid-preflight-v1.json) - početni obod i front stanu u 256×256 mrežu za 99 train i 20 validation požara.
- [gridMET archive/weather coverage](feds-gridmet-weather-coverage-v1.json) - devet arhiva s SHA-256; 392 train i 80 validation segmenta plus `pre_start` za 118 slučajeva, FEDS `t` kao lokalni prolaz (TASK-027); hash fajla s vremenom (`7a51aadd…`), hash manifesta i poređenje sa starim neispravnim fajlom; raw-only forcing.
- [One-case SimFire input smoke](feds-simfire-input-smoke-v1.json) - Plateau real-input runtime smoke s demonstracijskim vremenom; nije no-op gate.
- [SimFire TRAIN inputs](feds-simfire-input-train-coverage-v1.json) - 99/99 početnih scar/front + LANDFIRE fuel/terrain pairs; hashes i validation status.
- [SimFire no-op pilot](feds-simfire-noop-pilot-v1.json) - jedan TRAIN Plateau slučaj; ne zaključava WAF ili timestep i nije fizička validacija.
- [TRAIN-only SimFire no-op screen](feds-simfire-train-noop-screen-v1.json) - osam WAF kandidata × 99 TRAIN slučajeva; 0/8 je prošlo persistence/elipsa gate. Nevažeće (ADR-029); zamijenjeno growth gateom ispod.
- [TRAIN growth gate, ADR-030 §3](feds-simfire-train-growth-gate-v1.json) - 17 fiksnih kandidata × 98 TRAIN požara na ispravljenim ulazima; 8 prolazi, izabran WAF 0.10 / ROS 1.0 (IoU rasta 0.0958 prema 0.0258 za elipsu); prerastanje nerastućih požara prijavljeno po kandidatu (ADR-031).
- [VALIDATION growth gate, jednom](feds-simfire-validation-growth-gate-v1.json) - zamrznuti zapis na 20 VALIDATION požara: IoU rasta 0.0983 prema 0.0278; nije korišten za izbor (ADR-031).
- [Benchmark i studija budžeta, ADR-030 §4](feds-simfire-budget-benchmark-adr030-v1.json) - 10 seedova, 20 VALIDATION požara, jednom: nijedan od šest primarnih testova ne odbacuje; PPO se ne razlikuje od nasumične linije ni od `advancing_front`; uključuje broj epizoda gdje linija spali više od no-opa (ADR-032). [Grafikon](feds-simfire-budget-benchmark-adr030-v1.png).
- [Zapis o pokretanju faze 2](feds-simfire-budget-run-record-adr030-v1.json) - potvrde treninga za 40 politika, hashovi i sažeci TRAIN i VALIDATION benchmarka, opis ponašanja politika (ADR-032).
- [Lock prije VALIDATION-a](feds-simfire-budget-validation-lock-adr030-v1.json) - najbolja TRAIN heuristika, hash TRAIN izvještaja i hashovi 40 modela, commitovano prije VALIDATION benchmarka (ADR-032).
- [TRAIN no-op diagnosis](feds-simfire-train-noop-diagnosis-v1.json) - reproducirani WAF .01 run; deficit IoU dolazi iz požara koji u FEDS-u gotovo ne rastu (ADR-023).
- [SimFire VALIDATION inputs](feds-simfire-input-validation-coverage-v1.json) - 20/20 validation scar/front + LANDFIRE pairs; preuzimanje je krenulo minutu prije freeze commita, bez skoriranja prije njega (ADR-024).
- [VALIDATION no-op, jednom po zapisu](feds-simfire-validation-noop-v1.json) - gate freeze pada blizu persistence; free-burn stress scenarij prolazi strogo pravilo na 20 slučajeva (ADR-024).
- [Policy benchmark i budget adaptation](feds-simfire-policy-benchmark-v1.json) - upareni heuristike/PPO na VALIDATION stress scenariju; simulatorski, ne fizički rezultat (ADR-025/026). Nevažeće (ADR-029); zamijenjeno benchmarkom iz ADR-032.
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

## Zamrznuti SimFire/CA rast prema FEDS-u (2026-11-21)

- [Ljudski izvještaj](../../docs/research/PAIRED_OBSERVED_GROWTH.md) - TASK-041/ADR-046, nije fizička validacija ili native PPO rangiranje.
- [Svi slučajevi/vremena/seedi](paired-observed-growth-v1.json) - [metrike](paired-observed-growth-v1.png), [svih16mapa](paired-observed-growth-maps-v1.png).
- [Testovi, provenance i nezavisna rekalkulacija](paired-observed-growth-verification-v1.json).
- [Lokalni paket](paired-observed-growth-artifacts-v1.json) - [raspakovani SF/CA replay i80rastera](paired-observed-growth-restore-v1.json), bez uploada godišnjih arhiva ili raw mapa.

## Prošireni zamrznuti TRAIN audit (2026-11-21)

- [Ljudski izvještaj](../../docs/research/EXPANDED_OBSERVED_GROWTH.md) - TASK-042/ADR-048, svih61compatible početaka.
- [Svi slučajevi/vremena/seedi](expanded-observed-growth-v1.json) - [unaprijed zadane podgrupe](expanded-observed-growth-groups-v1.json), [metrike](expanded-observed-growth-v1.png).
- [Mape1–16](expanded-observed-growth-maps-v1-1.png), [17–32](expanded-observed-growth-maps-v1-2.png), [33–48](expanded-observed-growth-maps-v1-3.png), [49–61](expanded-observed-growth-maps-v1-4.png).
- [Testovi/provenance/rekalkulacija](expanded-observed-growth-verification-v1.json), [lokalni paket](expanded-observed-growth-artifacts-v1.json), [restore](expanded-observed-growth-restore-v1.json).
