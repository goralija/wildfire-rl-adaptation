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

Korisnik je izabrao **SimFire + FPA-FOD početne uslove + FEDS-CONUS opažene obode**,
uz FLE/ICS-209 kao ograničeni post-hoc kontekst. FPA-FOD godina drži isti incidentni
split: train 2018/2019, validation 2023, test 2024; test ostaje zatvoren.

Kompletni lokalni FEDS perimeter fajlovi za 2018, 2019. i 2023. checksum-verifikovani
su. Originalna 60-case kohorta po fiksnom ranom join pravilu ima 19/40 train i 7/20
validation te pada pragove 20/8. Širi, unaprijed spremljeni FPA-FOD candidate frame za
iste godine ima 208 train i 56 validation screen kandidata; isti join pravac nalazi
99/208 train i 20/56 validation jedinstvenih match-eva. Svih 119 ima pet uzastopnih
FEDS stanja kroz 48h. Taj prošireni pre-agent data-coverage gate je PASS, ali rezultat
je za selektovan okvir velikih požara, ne nacionalno reprezentativan uzorak.

FEDS active-front coverage potvrđen je za 119/119 početnih stanja; 119/119 početnih
geometrija stane u 256×256×180m mapu. SimFire Python 3.9.25 runtime i 99/99 TRAIN
LANDFIRE rastera su postavljeni; gridMET forcing je uzorkovan za 119 slučajeva. No-op
Plateau pilot pokazuje oštar WAF prag; parametar i interni korak nisu izabrani, a
cohort no-op gate s persistence/elipsnom referencom ostaje otvoren. Na direktan
korisnikov zahtjev sada postoji zaseban TRAIN-only MaskablePPO put za tehničko treniranje
iz početka; to ne prolazi niti zamjenjuje research gate. Validation mape nisu preuzete,
a test 2024 nije učitan.

## Šta je potvrđeno

- Naš sintetički engine, baseline politike i paired evaluacija rade; provjeren je
  [pilot od 300 baseline epizoda](../reports/pilot/README.md). To nisu Cell2Fire rezultati.
- Dva postojeća 20×20 Firehose checkpointa izvršena su bez treniranja u izolovanom
  Linux ARM64 legacy Docker runtimeu. [12 inference provjera](../docs/research/FIREHOSE_VERIFICATION.md)
  potvrđuje izvodivost, seed/budžet i nepromijenjene težine.
- Moderni Gymnasium/PPO smoke je zaseban mali model u sintetičkom engineu,
  [bez tvrdnje o transferu ili istraživačkom poboljšanju](../reports/rl-smoke/README.md).
- Zaseban FEDS/SimFire TRAIN env omogućio je 64-step MaskablePPO trening, spremanje/
  ponovno učitavanje checkpointa i završni TRAIN rollout; to je tehnička provjera
  [train putanje](../docs/research/SIMFIRE_ENVIRONMENT.md), ne kalibrisan benchmark.
- Simulator inputi su inventarisani; mali Dogrib/CFSDS uzorci su pregledani i imaju
  [izvore/hashove/provjerljive profile](../docs/research/REAL_FIRE_DATASETS.md).
- Historijska CFSDS putanja (44 kandidata, Canada + FBP/Cell2Fire) je raniji odvojeni
  rad. Njena tri train replaya i mismatch nalazi nisu SimFire rezultati i ne prenose
  se kao validacija novog benchmarka.
- Tri train slučaja (`2018_747`, `2018_241`, `2018_1770`) pretvorena su i replayana bez
  intervencija/treninga; no-action prognoze 66/237/73 ha prema 15.39/12.15/12.15 ha
  pokazuju veliko neslaganje i rubni efekat. `2014_538` pada na fuel/water provjeri.
  Zato no-op/reference gate za research tvrdnje ostaje otvoren.
- FireSpread_MedEU/EFFIS ostaje odvojeni mogući BiH pravac; evropski NFFL fuel kodovi
  nisu direktno kompatibilni s trenutnim Canadian FBP.

## Šta je otvoreno i šta prvo raditi

Korisnikov cilj je sada jasan: graditi RL scenarije od pravih požara i porediti agente
na istim historijskim uslovima. To ne znači učiti „tačnu akciju“ iz perimetra: simulacija
generiše counterfactual ishode. Pročitaj [X/Y mapiranje i ograničenja](../docs/research/REAL_CASE_PIPELINE.md)
i [izbor izvora](../docs/research/REAL_FIRE_DATASETS.md).

Sljedeći research gate je no-op SimFire replay na train kohorti: koristiti gridMET kao
skriveni ex-post simulator forcing, porediti dodatni burn sa persistence/elipsom i
provjeriti rub mape. Zaključati mali skup zajedničkih parametara prije validation
provjere. Tehnički PPO smoke/trening sada može raditi na TRAIN-u, ali se ne koristi kao
benchmark ili tvrdnja o koristi dok ovaj gate nije završen prema
[aktivnom crosswalk protokolu](../docs/research/FPA_FEDS_CROSSWALK.md).

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
