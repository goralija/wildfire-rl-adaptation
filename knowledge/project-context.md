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

## Šta je otvoreno i šta prvo raditi

**Prvi projektni korak je TASK-012 — dataset refinement.** Uloga stvarnih podataka,
konačni izvor/podskup, obim, veza s modelom i evaluacijski skup još nisu usaglašeni.
Dogrib/CFSDS su kandidati; Dogrib dijeli teren sa Sub20 pa nije nezavisan holdout.
Preuzeti uzorak nije zamrznut trening/test dataset. Počni od
[otvorenih odluka o podacima](../docs/research/REAL_FIRE_DATASETS.md) i
[backloga](../docs/BACKLOG.md).

TASK-004c je poznati tehnički nastavak: stvarni warmup observation, kumulativna šteta,
active/burnt export i termination reason. Runtime PASS nije research-ready. Trenutni
checkpoint kontrakt je RGB 3×20×20 i Discrete(400), uz forced legacy no-op -1 nakon B.

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
