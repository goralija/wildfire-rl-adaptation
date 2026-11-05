---
type: Project Context
title: Projektni kontekst i stanje istraživanja
description: Sažetak aktivnog SimFire/FEDS benchmarka, koraka 5–8 i otvorenih odluka.
status: stable
generated: {by: "process:claude-code", at: "2026-11-04T03:45:00Z"}
sources:
  - resource: /docs/STATUS.md
  - resource: /docs/NEXT_SESSION.md
  - resource: /docs/specs/DECISION_RECORDS.md
  - resource: /reports/real-fire-data/feds-simfire-train-noop-screen-v1.json
  - resource: /reports/real-fire-data/feds-simfire-policy-benchmark-v1.json
---
# Projektni kontekst

MPVI projekat istražuje prilagodbu RL agenta različitim budžetima intervencija pri
šumskim požarima, uz poređenje sa zamrznutim modelom i heuristikama. Zahtjevi predmeta
su sažeti u [rubrici](../docs/research/REQUIREMENTS_AND_RUBRIC.md). Aktivni benchmark
koristi SimFire, FPA-FOD početne uslove i FEDS-CONUS vremenske obode; stariji
CFSDS/Cell2Fire rad ostaje odvojen i historijski.

## Aktivni pravac

Korisnik je odabrao **SimFire + FPA-FOD + FEDS-CONUS**, uz FLE/ICS-209 samo kao
ograničeni post-hoc kontekst. Split je po godini: train 2018/2019 (99 požara), validation
2023 (20), test 2024 (zatvoren). Okvir obuhvata veće požare u deset zapadnih država i nije
reprezentativan za sve požare. FEDS/FPA veza ostaje provisionalna.

## Aktuelno — sintetički CA trening (ADR-028), 2026-11-05

- **Trening.** Agent se trenira samo na proceduralno generisanim sintetičkim požarima,
  u vlastitom CA simulatoru ([spec](../docs/research/SYNTHETIC_CA_ENV.md)):
  - vjerovatnoća paljenja zavisi od tipa goriva;
  - jedinice imaju fizičke brzine kretanja i gradnje linije;
  - nagrada je kontrafaktualna, protiv no-op rollouta;
  - jedinice se povlače po LCES pravilu i kažnjavaju se bliski susreti i gubici.
- **Uloga stvarnih slučajeva.** 119 FEDS startova služi samo kao jednokratni test
  zaključanih politika. Ishod je simuliran.
- **Rezultat.**
  - PPO od nule nije dostigao heuristiku.
  - `policy-v1` (imitacija direct_flank, pa PPO) je na sintetičkoj validaciji izjednačena
    s direct_flank (preregistrovani kriterij: FAIL) i jasno bolja od no-op.
  - Na stvarnim startovima čuva u prosjeku 12% no-op štete po slučaju više od no-op, uz
    upola manje bliskih susreta od direct_flank.
- **Granica.** Jaz kalibracije prema FEDS-u je velik (medijan IoU 0.27–0.30 na 48h).
  Detalji su u ADR-028 i [izvještajima](../reports/synthetic/index.md).
- **Odnos prema ranijem radu.** Koraci 5–8 ispod su historijski i ostaju na snazi kao
  dokaz da SimFire gate pada.

## Stanje koraka 5–8 — 2026-11-04

- **Kalibracija (korak 5) je FAIL.** Nakon dijagnoze i preregistrovane 3×3 mreže
  (ADR-023/024) nijedan zajednički SimFire parametar ne pobjeđuje persistence i elipsu
  istovremeno na TRAIN-u. Deficit dolazi iz požara koji u FEDS-u ne rastu, vjerovatno
  zaustavljenih ili ugašenih; slobodno-goreći no-op to ne može predstaviti. Zamrznuti
  gate zapis je `FAIL_exploratory` i gotovo ne širi vatru.
- **Validation (korak 6)** je skoriran jednom po zapisu
  ([izvještaj](../reports/real-fire-data/feds-simfire-validation-noop-v1.json)).
- **Koraci 7–8** rade na zasebnom, jasno označenom free-burn stress zapisu (ADR-024–027):
  jedinica budžeta je smjena ekipe od 20 ljudi = linija od ~1.26 km. Osnovni PPO pobjeđuje
  no-op, fine-tuning po budžetu nema mjerljive koristi, a downwind heuristika je jednako
  dobra ili bolja ([sažetak](../reports/real-fire-data/feds-simfire-policy-benchmark-v1.json)).

## Šta je potvrđeno, a šta nije

- Ulazi i no-op rezultati su reproducibilni na drugom računaru (isti hashovi, isti IoU).
- Benchmark je determinističan; politike dobijaju iste scenarije, budžete, opservacije i seed.
- Nije potvrđena fizička kalibracija SimFire-a, korist RL-a u stvarnom gašenju, niti
  korist prilagodbe budžetu. FEDS su satelitske procjene, gridMET je grubi proxy.
- Prioritetna područja (TASK-007), gradnja linije kroz vrijeme i TEST evaluacija nisu rađeni.

## Šta prvo raditi

1. Timski odlučiti o growth-aware gateu ili modelu zaustavljanja prije tvrdnje o
   kalibraciji, i o tome da li stress scenarij ostaje radni simulator.
2. Ako se nastavlja korak 8: nova preregistracija s jačim signalom budžeta (više linija po
   odluci ili duži vijek aktivne ćelije) i više seedova.
3. TASK-007 i TASK-009 (poster); TEST 2024 tek na kraju, sa zaključanim politikama.

TASK-012 CFSDS izbor i Firehose TASK-004c su historijski, odvojeni pravci. Kasnija
odluka/ADR ima prednost nad starijim task opisima.

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
