---
type: Decision Log
title: Odluke (append-only)
---
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

## ADR-008 — objava grane i PR za timski handoff, accepted 2026-10-28
Korisnik je sada izričito zatražio commit, PR cijelog dosadašnjeg rada i handoff
za kolegu. Time je odobrena remote objava koja je u ADR-005 bila odgođena.
GitHub repo je i dalje prazan: objaviti postojeći prazni bazni commit kao `main`,
zatim `feature/project-bootstrap` sa cjelokupnim radom i otvoriti PR prema mainu.
Ne mergeati PR automatski. Sačuvati historiju, postojeći worktree i lokalne artefakte.

HANDOFF.md daje prenosive upute bez Harunovih lokalnih putanja/okruženja. Objavljuju
se naš kod, dokumentacija, mali rezultati i manifesti. Raw podaci, težine, treći repo,
image, .venv i privatni originali ostaju izvan Gita. Ovo nije izbor licence za tim
niti dozvola za redistribuciju tuđih modela/podataka. Sljedeći tehnički posao ostaje TASK-004c.

## ADR-009 — dataset refinement je prvi projektni korak, accepted 2026-10-28
Korisnik je nakon handoffa ukazao da uloga, izbor i obim podataka nisu do kraja
usaglašeni. Raniji handoff je pomiješao poznati sljedeći tehnički posao sa sljedećim
projektnim korakom. Ovo zamjenjuje redoslijed iz ADR-007/008 gdje se može čitati
da TASK-004c treba odmah početi, prije refinementa.

Prvi fokus je TASK-012: dokumentovati i usaglasiti uloge simulator inputa, RL iskustva
i stvarnih referenci, izbor/obim, mapiranje na model, scenarije/splitove i metrike.
Dogrib/CFSDS preporuke ostaju provisional; preuzimanje/profilisanje nije konačan izbor
ili spreman evaluacijski dataset. Ovaj zapis usvaja redoslijed, ne zatvara te odluke.
TASK-004c ostaje poznati tehnički nastavak prema usaglašenom obimu i preduslov glavne
evaluacije postojećeg pristupa. Runtime nalazi i svi raniji dokazi ostaju važeći.

## ADR-010 — repo kao OKF 0.2 knowledge bundle, accepted 2026-10-28
Korisnik je zatražio samostalnu bazu znanja u repozitoriju, OKF 0.2 i agent onboarding,
u istom PR-u. Biramo repo root kao bundle root: postojeći docs/reports ostaju kanonski
koncepti, dodaju se typed frontmatter, lowercase indeksi, root log i knowledge playbookovi.
Ne pravimo paralelne kopije cijelog docs stabla niti vanjski servis/MCP kao preduslov.

Root index/AGENTS usmjeravaju čitanje; mali CLAUDE/GEMINI/Copilot ulazi dijele ista
pravila. Spec pin je GoogleCloudPlatform/open-knowledge-format commit ad30107c….
Validator i odvojeni CI knowledge job provjeravaju strukturu i projektne lokalne
linkove/dostupnost; PyYAML je samo alatna zavisnost, osnovni engine ostaje bez nje.
Migracija ne dodaje izmišljenu provenance, ljudsku potvrdu ili naučnu verifikaciju.

TASK-012 ostaje prvi istraživački korak; dataset odluke su otvorene. Raw/težine,
treći repo, environmenti i privatni originali ostaju van bundlea uz recovery manifeste.
Lokalni START_HERE/backup i chat nisu izvor istine ili preduslov za novog saradnika.
