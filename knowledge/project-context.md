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
- FireSpread_MedEU/EFFIS ostaje odvojeni mogući BiH pravac; evropski NFFL fuel kodovi
  nisu direktno kompatibilni s trenutnim Canadian FBP.

## Šta je otvoreno i šta prvo raditi

Korisnikov cilj je sada jasan: graditi RL scenarije od pravih požara i porediti agente
na istim historijskim uslovima. To ne znači učiti „tačnu akciju“ iz perimetra: simulacija
generiše counterfactual ishode. Pročitaj [X/Y mapiranje i ograničenja](../docs/research/REAL_CASE_PIPELINE.md)
i [izbor izvora](../docs/research/REAL_FIRE_DATASETS.md).

Glavni izbor geografije i simulatora je zatvoren po korisnikovoj uputi. Sljedeće je
sistemski provjeriti fuel-vintage, FWI/weather i FBP parametre za train događaje,
razumjeti no-action prekomjerno širenje, pripremiti 2019/2024 FBP map vintages i spojiti
suppression/QC metadata.
Preliminarni 44 ID-ja i pilot su u
[CFSDS kohort manifestu](../data/manifests/cfsds-v1_1-pilot-cohort.json). Adapter za
`burnt` + višestruki `burning` početni state i jedan case converter su već ostvareni;
TASK-004c još treba terminalni razlog i cumulative-damage export.

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
