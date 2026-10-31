---
type: Project Context
title: Projektni kontekst i stanje istraživanja
description: Kratki ulaz u cilj, ostvareno, otvorene odluke i prvi naredni posao.
status: stable
generated: {by: "process:codex", at: "2026-10-31T11:40:20Z"}
sources:
  - resource: /docs/STATUS.md
  - resource: /docs/specs/DECISION_RECORDS.md
  - resource: /docs/research/REQUIREMENTS_AND_RUBRIC.md
  - resource: /reports/firehose-verification/verification.json
---
# Projektni kontekst

MPVI projekat istražuje prilagodbu prethodno treniranog RL agenta različitim
budžetima intervencija pri šumskim požarima, uz poređenje sa zamrznutim modelom
i heuristikama te razmatranje prioritetnih područja. Polazna tema i profesorovi
zahtjevi su sažeti u [rubrici/zahtjevima](../docs/research/REQUIREMENTS_AND_RUBRIC.md).

## Šta je potvrđeno

- Naš sintetički engine, baseline politike i paired evaluacija rade; provjeren je
  [pilot od 300 baseline epizoda](../reports/pilot/README.md). To nisu Cell2Fire rezultati.
- Dva postojeća 20×20 Firehose checkpointa izvršena su bez treniranja u izolovanom
  Linux ARM64 legacy Docker runtimeu. [12 inference provjera](../docs/research/FIREHOSE_VERIFICATION.md)
  potvrđuje izvodivost, seed/budžet i nepromijenjene težine.
- Moderni Gymnasium/PPO smoke je zaseban mali model u sintetičkom engineu,
  [bez tvrdnje o transferu ili istraživačkom poboljšanju](../reports/rl-smoke/README.md).
- Simulator inputi su inventarisani; mali Dogrib/CFSDS uzorci su pregledani i imaju
  [izvore/hashove/provjerljive profile](../docs/research/REAL_FIRE_DATASETS.md).
- Glavni real-fire pravac je odabran: Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire.
  44 početna geometrijska kandidata podijeljena su 20/9/15 po godini požara; to nije
  finalan benchmark. Sirovi CFSDS ZIP-ovi ostaju u ignorisanom `data/raw/`.
- Tri train slučaja (`2018_747`, `2018_241`, `2018_1770`) pretvorena su i replayana bez
  intervencija/treninga; no-action prognoze 66/237/73 ha prema 15.39/12.15/12.15 ha
  pokazuju veliko neslaganje i rubni efekat. `2014_538` pada na fuel/water provjeri.
  Treba riješiti input/extent/model gate prije treniranja agenta.
- Per-cell train fuel audit sada je provjerio svih 20 kandidata: 10 prolazi samo fuel
  gate, a 10 pada na ne-gorivo/ambiguous overlay. Sva tri postojeća replay slučaja su
  među prolazima; zato fuel overlap sam ne objašnjava njihov veliki no-action rast.
  Ovo je legacy kohorta i target-aware crop; ti PASS/FAIL brojevi ne kvalifikuju novi
  target-blind shortlist, koji još nema svoj fuel audit.
  Novi input audit mjerio je samo tri materijalizovana slučaja: sve tri 20×20/100 m
  terrain mape su poravnate i kompletne; 17 slučajeva još nemaju paket. 2014b nema
  pixel-level cutoff dokaz, 2019 CanFG je razvojni i NBAC-zasnovan. Saved case manifests
  retain suppression `unknown` because the incident/action join is incomplete.
  [Fuel QC](../docs/research/CFSDS_TRAIN_QC.md) i
  [input/provenance QC](../docs/research/CFSDS_TRAIN_INPUT_QC.md).
- Novi FBP fuel source review našao je CWFIS site-wide Open Government Licence - Canada
  uz atribuciju, ali v2014b i dalje nema cutoff za NFDB/NBAC burn scars. Službeni 2018
  fuel-class decision rules opisuju bazno klasifikovanje, ne post-fire age succession.
  W.I.S.E. Figure 2 succession tree je javno transkribovana, ali starosna semantika/
  specijalne klase i underlying v20191114 implementation nisu potvrđeni; javni ZIP od
  2 GB nije pregledan. Nema novog godišnjeg map vintagea; 2014b ostaje samo za
  reprodukciju spremljenih slučajeva. Alberta 2006–2025 suppression dataset je pronađen,
  ali CSV endpoint vratio je HTTP 403 i nema event join-a. [Audit](../docs/research/CFSDS_FUEL_VINTAGE_REVIEW.md),
  [ADR-024](../docs/specs/DECISION_RECORDS.md#adr-024), [ADR-026](../docs/specs/DECISION_RECORDS.md#adr-026).
- Terrain/weather provenance je dodatno provjeren za tri postojeća TRAIN pilota: svi
  uzorkovani MRDEM source-class pikseli su adjusted GLO-30 (2011–2015 input collection),
  a rekonstruisani target-blind ERA5-Seamless odgovori su sačuvani sa query URL-ovima.
  Ipak, stare temperature se razlikuju svih 24 sata u sva tri slučaja, humidity u 1–6
  sati, stari DEM revision ostaje nepoznat, a FireCase-i su target-aware. Ovo nije PASS
  za environment/no-action gate. [Receipt](../reports/real-fire-data/cfsds-train-terrain-weather-provenance.json),
  [snapshots](../reports/real-fire-data/weather-snapshots/), [EXP-020](../docs/research/EXPERIMENT_LOG.md#exp-020--train-terrain-source-class-and-weather-snapshot-provenance-2026-10-31),
  [ADR-030](../docs/specs/DECISION_RECORDS.md#adr-030).
- Službeni BC historical perimeter servis geometrijski povezuje target-centroid tri
  spremljena 2018 TRAIN slučaja s kandidatima N12395, C11937 i N12413. Follow-up javni
  izvještaji dokumentuju containment-line rad na cilj-dan Coal Creeka i paljenje/resurse
  Lost Dog Complexa dan prije drugog cilja; za C11937 je pronađen next-day status, ne
  dnevnik akcija. Zbog kandidatskog incident-spoja i nepotpunih snapshot izvještaja case
  manifests zadržavaju `suppression_status=unknown`; nema ćelijskog action-inputa.
  [Crosswalk](../reports/real-fire-data/cfsds-train-bc-perimeter-crosswalk.json),
  [operational evidence](../reports/real-fire-data/cfsds-train-bc-operational-evidence.json),
  [ADR-027](../docs/specs/DECISION_RECORDS.md#adr-027) and
  [ADR-028](../docs/specs/DECISION_RECORDS.md#adr-028).
- TRAIN-only fuel-vintage mask proof obrađuje samo `2018_747`: `arrival_day < target_doy`
  bira 881 prethodno spaljenu ćeliju u rasteru i isključuje 19 target ćelija; unit test
  provjerava i budući dan n+1. Godišnja mapa nije generisana jer 2014b cutoff i succession
  crosswalk nisu potvrđeni. Importer contract sada prihvata `scar_nf` samo uz eksplicitnu
  oznaku caller-a i tačnu C++ `NF` klasu; sačuva scar u cumulative damage, bez aktivnog
  fronta. Ovo je sintetički ugovorni test, ne CFSDS konverzija. [Mask receipt](../reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json),
  [contract receipt](../reports/firehose-verification/nonfuel-initial-scar-contract.json),
  [ADR-020](../docs/specs/DECISION_RECORDS.md#adr-020) i
  [ADR-025](../docs/specs/DECISION_RECORDS.md#adr-025).
  Raniji builder je birao day n-1 front prema targetu day n; to je zamijenjeno
  target-blind centroid prozorom i unutrašnjim day n-1 frontom. Za `2018_747` promjena
  target maske ne mijenja simulator input. Međutim, post-selection train screen shortlist
  sadrži makar jedan target pixel u samo 4/25 cropa, pa prostorna podobnost 2×2 km domena
  ostaje otvorena. Vidi [invariance receipt](../reports/real-fire-data/cfsds-target-blind-input-invariance.json),
  [screen receipt](../reports/real-fire-data/cfsds-train-target-blind-window-screen.json)
  i [ADR-021](../docs/specs/DECISION_RECORDS.md#adr-021).
- Bounded audit poredi starih 25 parova na oko 2–6 km; ti parovi i dalje imaju target-day
  summary/pozitivnu firearea uslov i nisu potpuno outcome-independent. Naknadni puni
  screen je obradio svih 1.301 TRAIN rastera po pravilu: najraniji DOY sa ≥3 arrival
  piksela kao input, dan poslije kao target. 1.010 targeta ima mapirane piksele, 291 nema;
  uklanjanje target/budućih arrival oznaka nije promijenilo nijedan izabrani input dan.
  Za 20×20/100 m prozor je nađen u 1.295 slučajeva; target capture medijana je 36.71%
  (N=1.008 targeti s cropom). Širi prozori uhvate više piksela, ali mnoga izvorna rasterska
  područja su premala. Nijedna domena nije usvojena, a geometry screen ne potvrđuje
  simulator fitness. [Full report](../docs/research/CFSDS_FULL_DAY_PAIR_SCREEN.md),
  [JSON](../reports/real-fire-data/cfsds-train-full-day-pair-screen.json),
  [per-case CSV](../reports/real-fire-data/cfsds-train-full-day-pair-screen.csv),
  [ADR-023](../docs/specs/DECISION_RECORDS.md#adr-023).
- TASK-018 je završio dijagnostičko poređenje tri sačuvana no-action replaya na fiksnim
  vremenskim presjecima: svi dodiruju rub 20×20 domene za 34–52 minute, a jedan popuni
  svih 400 ćelija. Rezultati su osjetljivi na vrijeme, ali nema unutar-dnevnog ground trutha
  ili suppression podataka da se tačan uzrok izdvoji. Probe horizon metapodatak ispravljen
  je sa 480 na 1.440 minuta za 24 hourly reda. [Izvještaj](../docs/research/CFSDS_NO_ACTION_DIAGNOSIS.md).
- FireSpread_MedEU/EFFIS ostaje odvojeni mogući BiH pravac; evropski NFFL fuel kodovi
  nisu direktno kompatibilni s trenutnim Canadian FBP.

## Šta je otvoreno i šta prvo raditi

Korisnikov cilj je sada jasan: graditi RL scenarije od pravih požara i porediti agente
na istim historijskim uslovima. To ne znači učiti „tačnu akciju“ iz perimetra: simulacija
generiše counterfactual ishode. Pročitaj [X/Y mapiranje i ograničenja](../docs/research/REAL_CASE_PIPELINE.md)
i [izbor izvora](../docs/research/REAL_FIRE_DATASETS.md).

Glavni izbor geografije i simulatora je zatvoren po korisnikovoj uputi. Dijagnostička
faza TASK-018 je završena, ali no-action gate i uzrok neslaganja ostaju otvoreni.
TASK-004c episode adapter je sada završen lokalno: C++/Python dijele terminalni cumulative
damage, scar i aktivni front su odvojeni, a završetak dobija named reason. Fixture + 12/12
inference rollouta potvrđuju adapter contract; svi matrix slučajevi završili su na weather
horizonu. [Receipt i tehnički limiti](../reports/firehose-verification/task004c-adapter-smoke.json).
Target-day curenje iz početnog fronta je uklonjeno za crop/initial-state pravilo i
provjereno na jednom TRAIN paru. Stari 25-pair bounded screen imao je slab target coverage;
puni target-independent screen sada obuhvata 1.301 paru i nijedan grid nije usvojen.
Target-independent day-pair i full TRAIN domain screen su završeni. Source review je
otkrio nedostatak javnog datiranog cutoffa; W.I.S.E. succession tree je transkribovan,
ali datumsku semantiku i izvorni artifact tek treba provjeriti. `scar_nf` importer contract
je završen. Sljedeće pribaviti autoritativni base-map cutoff, spojiti Alberta source ako se
može preuzeti, i zatvoriti DEM/weather/suppression provenance samo na train/calibration
događajima. Izmjereni
input audit trenutno pokriva 3/20 train paketa. Vidi [task handoff](../docs/NEXT_SESSION.md).
Preliminarni 44 ID-ja i pilot su u
[CFSDS kohort manifestu](../data/manifests/cfsds-v1_1-pilot-cohort.json).

TASK-014 core/legacy environment je lokalno reproducovan na macOS ARM64 + Linux ARM64;
moderni venv ima geospatial ETL stack. Receipt bilježi pakete, image hash i inference.
No-action gate i heldout freeze i dalje su preduslovi benchmarka ili fine-tuninga. Runtime
PASS nije research-ready. Checkpoint kontrakt je RGB 3×20×20 i Discrete(400), uz forced
legacy no-op -1 nakon budžeta.

Glavni fine-tuning, dokazana RL prednost, fizička validacija stvarnim požarima,
BiH primjenjivost, konačni test split, rok/compute i timska licenca ostaju otvoreni.
Pretpostavke/protokol nisu već ostvareni nalazi niti profesorov zahtjev.

## Kako nastaviti

1. Provjeri [STATUS](../docs/STATUS.md) i najnovije odluke u
   [append-only ADR logu](../docs/specs/DECISION_RECORDS.md); kasnije odluke mogu zamijeniti ranije.
2. Koristi [HANDOFF](../HANDOFF.md) za klon/setup i
   [mapu koda i zadataka](code-map.md) za konkretne fajlove/komande.
3. Nakon rada osvježi [izvorne dokumente i navigaciju](maintenance.md), uz tačne dokaze.

Ovaj sažetak služi ulazu, a detaljni dokumenti ostaju kanonski. Ako su u sukobu,
pročitaj najnoviju korisničku uputu/ADR, ispravi sažetak i zabilježi neslaganje.
