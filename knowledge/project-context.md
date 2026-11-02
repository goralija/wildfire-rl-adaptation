---
type: Project Context
title: Projektni kontekst i stanje istraživanja
description: Kratki ulaz u cilj, ostvareno, otvorene odluke i prvi naredni posao.
status: stable
generated: {by: "process:codex", at: "2026-10-28T12:55:34Z"}
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

## Trenutni pravac — 2026-11-03

Korisnik je za novi benchmark izabrao **SimFire + FPA-FOD početne uslove + FEDS-CONUS
tok opaženih oboda**, uz FLE/ICS-209 kao ograničeni post-hoc kontekst. Ova uputa
superseduje raniji CFSDS/Cell2Fire izbor kao aktivni pravac; CFSDS replayi ostaju
historijski dokaz odvojene grane.

Prvi obavezni korak je završeni [FPA↔FEDS↔FLE crosswalk](../docs/research/FPA_FEDS_CROSSWALK.md).
Od 40 train slučajeva 13 ima jedinstven FEDS match i dovoljno 12h stanja; od 20
validation slučajeva to postiže 7. Pragovi su 20/8, zato je data gate **FAIL u oba splita**.
FLE incidentni sažetak spojen je za 0/40 train i 13/20 validation slučajeva. Ne
portati SimFire adapter, ne pokretati no-op kalibraciju ni PPO dok pokrivenost oba
splita ne bude razriješena i novi gate ne prođe. Test split ostaje neotvoren.

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
- Historijska CFSDS putanja (44 kandidata, Canada + FBP/Cell2Fire) je raniji odvojeni
  rad. Njena tri train replaya i mismatch nalazi nisu SimFire rezultati i ne prenose
  se kao validacija novog benchmarka.
- Tri train slučaja (`2018_747`, `2018_241`, `2018_1770`) pretvorena su i replayana bez
  intervencija/treninga; no-action prognoze 66/237/73 ha prema 15.39/12.15/12.15 ha
  pokazuju veliko neslaganje i rubni efekat. `2014_538` pada na fuel/water provjeri.
  Treba riješiti input/extent/model gate prije treniranja agenta.
- FireSpread_MedEU/EFFIS ostaje odvojeni mogući BiH pravac; evropski NFFL fuel kodovi
  nisu direktno kompatibilni s trenutnim Canadian FBP.

## Šta je otvoreno i šta prvo raditi

Korisnikov cilj je sada jasan: graditi RL scenarije od pravih požara i porediti agente
na istim historijskim uslovima. To ne znači učiti „tačnu akciju“ iz perimetra: simulacija
generiše counterfactual ishode. Pročitaj [X/Y mapiranje i ograničenja](../docs/research/REAL_CASE_PIPELINE.md)
i [izbor izvora](../docs/research/REAL_FIRE_DATASETS.md).

Trenutni prvi zadatak je riješiti train/validation pokrivenost FPA-FOD kohorte pod istim
datum/tačka/3 km/prvih-24h FEDS join pravilom. Sačuvati test 2024 zatvoren. Ako nova
kohorta ne može ispuniti pragove bez promjene pravila/splita, zabilježiti novu odluku
prije nastavka. Potom tek slijede SimFire adapter, opaženi-state no-op poređenje,
kalibracija zajedničkih parametara i agent benchmark po
[aktivnom protokolu](../docs/research/FPA_FEDS_CROSSWALK.md).

Stari Firehose TASK-004c i CFSDS TASK-015/016 adapteri ne ispunjavaju automatski
SimFire kontrakt. Portovati samo mali, pregledan dio ako novi data gate prođe.

TASK-014 core/legacy environment je lokalno reproducovan na macOS ARM64 + Linux ARM64;
moderni venv ima geospatial ETL stack. Receipt bilježi pakete, image hash i inference.
TASK-004c treba dovršiti cumulative-damage i terminal-reason dio. Runtime PASS nije
research-ready. Checkpoint kontrakt je RGB 3×20×20 i
Discrete(400), uz forced legacy no-op -1 nakon budžeta.

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
