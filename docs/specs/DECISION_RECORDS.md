# Odluke (append-only)

## ADR-001 — trajna projektna memorija u repozitoriju, accepted 2026-10-28
Korisnik traži lak nastavak. Biramo Markdown, JSON konfiguracije/manifeste i mali Python
paket. Alternativa vanjska baza/servis uvodi održavanje bez koristi u početku.
Privatni originali ostaju ignorisani; javni sažetak čuva relevantne zahtjeve.

## ADR-002 — Firehose kao kandidat, synthetic samo za pilot, provisional 2026-10-28
Cell2Fire nije obavezan. Zadržavamo mogućnost postojećih težina, ali legacy setup,
fiksni seed i interaktivni fork moraju proći TASK-004. SimFire je fallback, ne automatski
bolji izbor. Trošak pogrešne odluke ograničen je feasibility timeboxom.

## ADR-003 — intervencija i pošteno računovodstvo, accepted for pilot 2026-10-28
Jedna ćelija, trajni tretman, cost=1, no-op=N; B potrošen ne završava epizodu.
Ever-burned je trajni damage; time-limit je truncation, ne containment.
Glavni backend mora eksplicitno dokazati istu semantiku ili dokumentovati razliku.

## ADR-004 — dva odvojena environmenta, accepted 2026-10-28
Moderni optional Gymnasium/SB3 smoke odvojen od legacy Firehose reprodukcije.
Ne pokušavati tiho učitavanje SB3 1.5.0 težina u novi Dict env i 401 akciju.
Glavni minimalni pristup zadržava arhitekturu i fine-tunira po B; budget-conditioned
model je dodatni pravac nakon definisane migracije i kontrola.

## ADR-005 — lokalni završetak bez remote promjena, accepted for bootstrap 2026-10-28
Repo je prazan. Pravimo lokalnu baznu historiju i izolovanu feature granu, commit i
bundle. Ne kreiramo remote main, PR ili cloud zadatke bez naloga za objavu.
Posljedica: GitHub ostaje prazan dok se grana ne objavi; lokalni rezultat je pregledljiv.

## Otvorene odluke
OD-001: licenca našeg koda i redistribucija mapa/modela.
OD-002: deadline, compute i glavni matriks nakon runtime mjerenja.
OD-003: legacy runtime ili migracija težina; no-op learned ili prisilni wrapper.
OD-004: prostorni/meteorološki test split i granica tvrdnji o generalizaciji.

## ADR-006 — Firehose runtime potvrđen, accepted 2026-10-28
Nastavak ADR-002/004: izvorni fork kompajliran je i oba postojeća 20×20 checkpointa
izvršena su bez treniranja. Zadržavamo Firehose za narednu fazu; promjena simulatora
sada nije opravdana. Legacy okruženje je odvojeni Docker image (Python 3.8 / SB3 1.5),
moderni .venv ostaje za sintetički pilot. Probe čuva 400-action glavu i RGB opažanje;
budžet nameće forced no-op, pa još ne uči vrijeme intervencije.

Runtime PASS nije research-ready: dokazani reset/cumulative-damage problem i spajanje
active/burnt stanja zahtijevaju TASK-004c. Ne koristiti upstream done za containment.
Dataset se za početak sastoji od pinovanih map/terrain/weather inputa i scenarija;
RL iskustvo generiše simulator. Nema obaveze skupljanja označenih intervencija ili
regionalnog GIS-a. Raw data/weights i Docker image ostaju lokalni dok licence nisu provjerene.

## ADR-007 — historijski podaci imaju zasebnu validacijsku ulogu, accepted 2026-10-28
Korisnik je ispravno razdvojio simulator inpute od dataseta opaženih požara i tražio
dobar stvarni dataset. Osnovno istraživačko pitanje ostaje adaptacija politike unutar
simulatora; ne uvodimo obavezu supervised labela intervencija ili novu forecasting temu.

Preporučen početak je Dogrib 2001 sa opaženim scarom i pripremljenim Cell2Fire inputima;
zatim mali CFSDS podskup za nezavisnije događaje, uslovno dostupnim kompletnim inputima.
Izbor konkretnog holdout skupa je provisional. Mali uzorci su preuzeti i pregledani,
ali fizička validacija nije izvršena. Dogrib dijeli fuel/elevation blok s Firehose
Sub20, pa služi kao povezana referenca/kalibracijski slučaj, ne nezavisan test.

Historijski ishodi ne identifikuju ishode novih RL intervencija. Mjerenje sličnosti
požara odvajamo od paired policy benchmarka. Event split i vremenski alignment
preduslovi su za vanjske tvrdnje, ne razlog da odgađamo popravku TASK-004c.
Pinovati CFSDS fajlove: rad opisuje 180 m v1, pregledani v1_1 uzorak ima 90 m.
Raw ostaje ignorisan, manifesti/hashovi/profili i odluke idu u Git. Detalji i
ograničenja: research/REAL_FIRE_DATASETS.md; implementacija provjere je TASK-011.
