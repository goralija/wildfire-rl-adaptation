---
type: Project Context
title: Projektni kontekst i stanje istraživanja
description: Sažetak aktivnog SimFire/FEDS benchmarka, dokaza i sljedećeg research gatea.
status: stable
generated: {by: "process:codex", at: "2026-11-03T20:58:26Z"}
sources:
  - resource: /docs/STATUS.md
  - resource: /docs/NEXT_SESSION.md
  - resource: /docs/specs/DECISION_RECORDS.md
  - resource: /reports/real-fire-data/feds-simfire-train-noop-screen-v1.json
---
# Projektni kontekst

MPVI projekat istražuje prilagodbu RL agenta različitim budžetima intervencija pri
šumskim požarima, uz poređenje sa zamrznutim modelom i heuristikama. Zahtjevi predmeta
su sažeti u [rubrici](../docs/research/REQUIREMENTS_AND_RUBRIC.md). Aktivni benchmark
koristi SimFire, FPA-FOD početne uslove i FEDS-CONUS vremenske obode; stariji
CFSDS/Cell2Fire rad ostaje odvojen i historijski.

## Aktivni pravac — 2026-11-03

Korisnik je odabrao **SimFire + FPA-FOD + FEDS-CONUS**, uz FLE/ICS-209 samo kao
ograničeni post-hoc kontekst. Podjela po godini je train 2018/2019, validation 2023,
test 2024. Test je zatvoren.

Originalna 60-case kohorta lokalno daje 19/40 train i 7/20 validation poklapanja pa
ne prolazi pragove 20/8. Unaprijed sačuvani širi FPA-FOD frame daje 99 train i 20
validation slučajeva od 208/56 kandidata; svih 119 ima pet FEDS stanja kroz 48h. Ovaj
**data coverage gate je PASS**, ali frame je ograničen na veće požare u deset zapadnih
država i nije reprezentativan za sve požare. FEDS/FPA veza ostaje provisionalna.

SimFire Python 3.9.25 runtime, 99/99 train LANDFIRE gorivo/teren i početne FEDS maske
su pripremljeni. GridMET forcing je uzorkovan za 99 train i 20 validation slučajeva.
Validation rasteri nisu preuzeti.

## Mjerodavan rezultat no-op provjere

Na svih 99 TRAIN slučajeva izvršeno je osam 48h no-op kandidata s različitim WAF
vrijednostima. Svaki slučaj poređen je na četiri vremena; svi runovi su završili bez
greške. Persistence baseline ima mean IoU .5343, elipsna referenca .5308. Najbolji
SimFire kandidat po IoU imao je .4769. Nijedan od osam kandidata nije istovremeno
nadmašio obje reference po IoU i grešci opožarene površine uz nula rubnih kontakata.
Zato je **TRAIN no-op research gate FAIL**; nijedan WAF ni interni korak nije
izabran. Jednominutna osjetljivost nije promijenila nalaz. Detalji su u
[no-op izvještaju](../reports/real-fire-data/feds-simfire-train-noop-screen-v1.json)
i [ADR-022](../docs/specs/DECISION_RECORDS.md).

Na zahtjev korisnika postoji odvojena TRAIN-only Gymnasium/MaskablePPO putanja i
završen je 64-step tehnički smoke. To dokazuje da se kod može pokrenuti, ne da je
simulator validiran ili da je politika korisna. Benchmark/PPO policy-benefit trening
ostaje blokiran dok se neslaganje ne dijagnosticira i novi zajednički TRAIN no-op gate
ne prođe. 2024 TEST nije učitan.

## Šta je potvrđeno, a šta nije

- Sintetički engine i heuristički pilot rade, ali nisu rezultati stvarnih požara.
- Firehose/Cell2Fire checkpoint inference je raniji, odvojeni runtime nalaz.
- FEDS-CONUS obodi su satelitske procjene, ne ground truth; gridMET je grubi historical
  forcing proxy, ne operativna vremenska prognoza.
- Runner, testovi i PPO smoke potvrđuju tehničko izvršavanje. Ne potvrđuju fizičku
  tačnost, fizičku validaciju niti RL prednost.
- SimFire akcije i nagrada su prototip; fireline ponašanje nije operativno validirano.

## Šta prvo raditi

1. Pregledati po-požar greške i provjeriti forcing, vjetra/moisture mapiranje,
   rasterizaciju i prostornu mrežu. Ne podešavati po požaru.
2. Dokumentovati mali zajednički kandidat skup samo na TRAIN kohorti i ponoviti isti
   no-op gate prema nepromijenjenim persistence/elipsa referencama.
3. Validation rastere koristiti tek nakon prolaza TRAIN gatea i zamrzavanja parametara;
   2024 TEST ostaviti zatvoren do završnog obračuna.
4. Prije policy poređenja precizirati intervenciju i dati svim agentima iste požare,
   budžete, horizont, informacije i seedove.

TASK-012 CFSDS izbor je historijski i više nije aktivni benchmark. Firehose TASK-004c
je zaseban legacy adapter koji nije SimFire gate. Kasnija odluka/ADR ima prednost nad
starijim task opisima.

## Kako nastaviti

1. Pročitati [STATUS](../docs/STATUS.md), [NEXT_SESSION](../docs/NEXT_SESSION.md) i
   najnoviji unos u [odlukama](../docs/specs/DECISION_RECORDS.md).
2. Koristiti [HANDOFF](../HANDOFF.md) za novi klon i
   [mapu koda](code-map.md) za relevantne fajlove.
3. Nakon bitnog pomaka osvježiti izvore i navigaciju prema
   [pravilima održavanja](maintenance.md).

Ovaj sažetak je ulaz za ljude i agente; detaljni izvještaji/odluke su kanonski.
Ako su u sukobu, najnovija korisnička odluka i najnoviji ADR imaju prednost; ažurirati
sažetak i zabilježiti neslaganje.
