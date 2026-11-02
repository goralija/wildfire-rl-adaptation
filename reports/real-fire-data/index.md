# real-fire-data

## Aktivna SimFire kohorta — 80 stvarnih požara

- [FPA-FOD/SimFire cohort manifest](../../data/manifests/simfire-fpa-fod-cohort-v2.json) — 40 train / 20 validation / 20 test, cijeli incident po split-u.
- [Input acquisition](simfire-cohort-v2-input-acquisition.json) — gorivo i teren su provjereni za 80/80.
- [gridMET weather acquisition](simfire-cohort-v2-gridmet-weather.json) — originalna osam-poljska dnevna vrijednost za 80/80 slučajeva; ovaj receipt bilježi samo preuzimanje.
- [gridMET data QC summary](simfire-cohort-v2-gridmet-summary.json) i [vizualni pregled](simfire-cohort-v2-gridmet-overview.png) — provjera hashova/jedinica i raw raspodjele po split-u.
- [gridMET → SimFire proxy mapping](simfire-cohort-v2-gridmet-simfire-mapping.json) — zasebni, pretpostavkama označeni SimFire proxyji za 80/80; tačan satni replay 0/80.
- [WAF sensitivity smoke](simfire-cohort-v2-gridmet-waf-sensitivity.json) — isti train/validation/test primjerci pri 0.1/0.3/0.5, bez treniranja ili fizičke validacije.
- [Seed ćelije](simfire-cohort-v2-seed-selection.json) — fuel-only lokacijsko pravilo, bez finalnih perimetara.
- [Gymnasium demo smoke](simfire-cohort-v2-gym-smoke/) — stvarni fuel/terrain i demo weather, bez RL treninga.
- [Gymnasium gridMET proxy smoke](simfire-cohort-v2-gridmet-weather-smoke/) — po jedan slučaj po splitu; mapirani meteo podaci, jedna linijska tačka i no-op; bez `learn()`.
- [Duži proxy smoke](simfire-cohort-v2-gridmet-full-horizon-smoke-v2/) — po jedan train/validation/test incident, do 12 sati; PPO samo legalna inference proba, bez `learn()`.
- [Benchmark validation preflight](simfire-benchmark-validation-preflight-20261102.json) — svih 20 validation paketa hash-provjereno; observation i no-op provjereni, 0 simulacijskih koraka, testni ulazi nisu otvoreni.
- [No-op horizont probe](simfire-cohort-v2-gridmet-noop-horizon/) — samo čekanje, bez linije i agenta; train Owyhee i validation Hayden, sa slikama i receiptom.
- [Test smoke incident koji je otvoren](simfire-cohort-v2-gridmet-noop-test-exposed/) — Larch Creek je isključen iz budućeg završnog benchmarka; ostaje 19 test incidenata.
- [WAF osjetljivost](simfire-cohort-v2-gridmet-waf-sensitivity.json) — isti uzorci pri 0.1/0.3/0.5; tehnička, ne fizička provjera.
- [Dataset objašnjenje](../../docs/research/SIMFIRE_FPA_COHORT.md) i [adapter detalji](../../docs/research/SIMFIRE_RL_ADAPTER.md).

## Trenutni razvojni primjer

- [Dixie Fire FPA-FOD izvorni zapis](fpa-fod-dixie-2021-source.geojson) i [scenario kartica](../../data/manifests/simfire-fpa-fod-401019270-dixie-candidate.json) — incident-referentna tačka, ne potvrđeno paljenje; 128×128 UTM grid od 30 m.
- [Real-input SimFire smoke](simfire-dixie-real-input-smoke/) — stvarni LANDFIRE FBFM13 i elevation ulaze u SimFire; sačuvani su input-layer prikaz, završno stanje, 30-min GIF i receipt. Atmosfera je demonstracijska, nije historijski weather.
- [Raw input pravilo i provenance](../../docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md) — GeoTIFF/ERA5 JSON ostaju ignorisani u `.local/real-input-dixie/`; kartica i receipt čuvaju hashove.
- [Mineral Fire audit](mineral-case-audit.json) i [objašnjenje](../../docs/research/MINERAL_CASE_AUDIT.md) — vremena linija su prazna; taj slučaj nije replay ulaz.

## Arhivirani CFSDS train-only ulazni gate

- [CFSDS train fuel QC metoda](../../docs/research/CFSDS_TRAIN_QC.md) i [mašinski čitljiv rezultat](cfsds-train-fuel-qc.json) — 20 train kandidata; 10 prolazi samo gorivnu provjeru, 10 pada; nijedan nije potvrđen kao kompletan simulator slučaj.
- [CFSDS train input QC](../../docs/research/CFSDS_TRAIN_INPUT_QC.md) i [mašinski čitljiv rezultat](cfsds-train-input-qc.json) — poravnanje izmjereno za 3/20 dostupnih train FireCase paketa; fuel vintage nije potvrđen kao vremenski siguran, suppression ostaje unknown.
- [CFSDS TRAIN fuel-vintage mask proof](cfsds-train-fuel-vintage-mask-proof.json) — `2018_747` pre-target maska isključuje target dan i kasnije; godišnja fuel mapa nije izrađena dok se ne potvrde bazni cutoff i succession crosswalk.
- [CFSDS TRAIN fuel source gate](cfsds-train-fuel-source-gate.json) — v2014b ne navodi NFDB/NBAC cutoff; javno navedeni v20191114 decision-rules PDF pokriva bazne fuel klase, a ne post-fire age succession.
- [CFSDS TRAIN terrain/weather provenance](cfsds-train-terrain-weather-provenance.json) — postojeća tri slučaja: MRDEM source class je adjusted GLO-30; novi target-blind API weather odgovori i query URL-ovi su pinovani, ali naspram starih inputa temperature/humidity se razlikuju.
- [Pinned response 2018_1770](weather-snapshots/2018_1770_2018-08-12.json), [2018_241](weather-snapshots/2018_241_2018-08-15.json), [2018_747](weather-snapshots/2018_747_2018-08-16.json) — tri mala, 24-satna odgovora sa SHA-256 u provenance receipt-u; ne mijenjaju stare Weather.csv/FireCase ulaze.
- [CFSDS target-blind input invariance proof](cfsds-target-blind-input-invariance.json) — TRAIN `2018_747`; promjena day-n maske ne mijenja crop, 20×20 početni scar/front ni `InitialState.csv`.
- [CFSDS TRAIN target-blind window screen](cfsds-train-target-blind-window-screen.json) — samo 2014–2018 TRAIN; target coverage je post-selection dijagnostika, 4/25 prozora imaju ikakav target pixel.
- [CFSDS TRAIN prostorni feasibility audit](cfsds-train-spatial-feasibility.json) — poređenje 2–6 km domena na istih 25 TRAIN parova; target dijagnostika je post-selection, bez FireCase-a ili replaya.
- [CFSDS puni TRAIN target-independent day-pair screen](../../docs/research/CFSDS_FULL_DAY_PAIR_SCREEN.md), [JSON receipt](cfsds-train-full-day-pair-screen.json) i [1301-case/domain CSV](cfsds-train-full-day-pair-screen.csv) — svih 1.301 TRAIN rastera, pet unaprijed definisanih domena, 1.010 target-opaženih i 291 bez mapiranih target piksela; bez simulator replaya.
- [CFSDS full TRAIN fuel-class overlay](../../docs/research/CFSDS_FULL_TRAIN_FUEL_OVERLAY.md), [zbirni JSON](cfsds-full-train-fuel-overlay.json) i [1301-redni CSV](cfsds-full-train-fuel-overlay.csv) — 1.295/1.301 prozora overlayano na 2014b; 701 pass-only, 64 review, 530 fail; nijedan nije full-case approved.
- [CanFG v20191114 archive member review](canfg-fuel-archive-member-review.json) — službeni 2.68 GB ZIP indeksiran bez preuzimanja karte; pronađena pravila za scar-succession, ali v2014b cutoff ostaje otvoren.
- [CFSDS no-action dijagnostika](../../docs/research/CFSDS_NO_ACTION_DIAGNOSIS.md) i [mašinski čitljiva vremenska analiza](cfsds-no-action-timeline.json) — tri sačuvana train replaya, bez novog C++ runa, kalibracije ili treninga.
- [ERA5-FWI-SN 2018 source audit](era5-fwi-sn-2018-pilot-comparison.json) i [paired weather replay receipt](era5-fwi-sn-2018-weather-replay-comparison.json) — checksum-provjereni dnevni indeksi i tri uparene kopije; sirovi NetCDF fajlovi ostaju u ignorisanom `data/raw/era5-fwi-sn/v2/`.
- [Alberta 2006–2025 historical wildfire catalogue](https://open.canada.ca/data/en/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e) — katalog navodi action-time/resources kolone, ali 403 sprečava preuzimanje; vidi [EXP-026](../../docs/research/EXPERIMENT_LOG.md#exp-026--alberta-suppression-source-schema-and-access-audit-2026-10-31). Nema Alberta događaja spojenih.

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
