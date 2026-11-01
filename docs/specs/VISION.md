---
type: Specification
title: Vizija i granice projekta
status: current-provisional
sources:
  - resource: /docs/DESIGN.md
  - resource: /docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md
  - resource: /docs/specs/DECISION_RECORDS.md
---
# Vizija i granice

## Cilj

Odgovoriti može li dodatno učenje PPO agenta poboljšati postavljanje vatrogasnih linija
unutar SimFire-a, kada scenariji dolaze iz stvarnih požarnih lokacija/datuma, goriva,
terena i historijskog vremena.

## Šta tačno znači “bolje”

Na istim ulazima, seedovima, trajanju i linijskom budžetu, fine-tuned agent treba imati
manju **simuliranu** opožarenu površinu od svog zamrznutog base agenta i jednostavnih
kontrola kroz heldout incidente. Pozitivni, nulti i negativni nalazi su svi prihvatljivi.

## Šta historijski podaci rade

- Incident record daje prijavljenu lokaciju i datum paljenja, uz poznatu vremensku/prostornu
  nesigurnost.
- Gorivo, teren i weather postaju simulatorovi inputi nakon izvora, vintagea, jedinica,
  geometrije i hashova provjere.
- Konačni historijski obod/veličina ostaju odvojena referenca za vizualni kontekst; nisu
  agentova nagrada niti tačan odgovor za novi counterfactual potez.
- Human line layers iz BurnMD-a mogu kasnije služiti za dodatni prikaz/replay ako se nađu
  pouzdana vremena i potvrde prava. Taj replay nije gate za osnovni policy experiment.

## Granice

Ne dajemo preporuke stvarnim dispečerima; ne simuliramo evakuacije/sve tipove ekipa; ne
zaključujemo uzročni učinak alternativne strategije na historijski stvarni požar; ne
tvrdimo univerzalnu fizičku ili operativnu validaciju SimFire-a.

## Trenutni kandidati i otvoreni rad

USFS FPA-FOD je kandidat za incident distribuciju; službeni archive page dopušta
korištenje bez dodatne dozvole ili naknade uz citat. Jedan Dixie Fire zapis pretvoren je u
development scenario-karticu, ali real fuel/terrain/weather scenario i RLlib runtime nisu
napravljeni. Zadnja provjera pokazala je 3.0 GiB slobodno, a `LANDFIRE_EMAIL` nije
postavljen.

Glavni opis: [DESIGN](../DESIGN.md),
[pipeline](../research/REAL_IGNITION_SCENARIO_PIPELINE.md),
[status](../STATUS.md), [ADR-040](DECISION_RECORDS.md#adr-040--train-on-real-ignition-conditions-with-simulated-actions-2026-11-01).
