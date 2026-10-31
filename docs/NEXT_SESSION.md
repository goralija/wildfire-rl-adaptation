---
type: Handoff
title: Nastavak nakon TRAIN-only CFSDS prostornog audita
---
# Naredna sesija

## Kratko stanje

Nastaviti na grani `research/cfsds-train-qc` u njenom postojećem task worktreeu.
Moderni Python/GIS environment i odvojeni legacy Cell2Fire runtime tehnički rade,
ali istraživački environment za stvarne požare još nije spreman za glavno treniranje.
No-action poređenje sa historijskim požarima nije prošlo; nema dokaza da RL agent
smanjuje stvarnu štetu.

Glavni put je Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire. Validation i test godine
ne otvarati radi izbora modela ili kalibracije; ne pokretati policy benchmark ni
fine-tuning prije prihvatljivih train ulaza, replay gatea i zamrznutog heldout splita.

## Završeno u ovoj fazi

- TASK-018 analiza tri sačuvana TRAIN no-action replaya potvrdila je rani kontakt s
  rubom 20×20 mreže (34–52 minute); uzrok prevelikog rasta nije izolovan jer nema
  intradnevnog ground trutha ni event-level suppression timeline-a.
- TASK-004c C++/Python epizodni adapter izvozi cumulative damage, front i terminalni
  razlog; fixture i 12 kratkih inference rollouta prolaze. To je adapter/runtime dokaz,
  ne fire-behavior validacija.
- TASK-015 pre-target maska i target-blind crop/state pravilo su implementirani.
  Perturbation proof za `2018_747` pokazuje da promjena target maske ne utiče na crop
  ni na početni input. Ovo važi za jedan fiksni TRAIN event/day par.
- Raniji TRAIN shortlist sadrži 25 parova, pet po godini, ali day-pair eligibilnost je
  zahtijevala target-day zapis i pozitivnu `firearea`; zato nije outcome-independent i
  ostaje samo historijski bounded audit. Novi full screen je target-independent pre-screen,
  ne konačni benchmark cohort.
- Prostorni audit uporedio je iste parove na oko 2, 3, 4 i 6 km. U 2 km target uđe u
  4/25 prozora (median capture 0%); u oko 4 km uđe u 19/25, ali median je samo 1.95%;
  u oko 6 km median raste na 15.31%, a dvije slike su premale za takav prozor. Nije
  usvojen veći model grid i nisu napravljeni FireCase-ovi/replayi.
- EXP-013 je potom obradio puni TRAIN raster cohort target-independent pravilom: za svaki
  raster prvi DOY sa najmanje tri validna 90 m arrival piksela je input dan, a naredni
  kalendarski dan target. Pregledano je svih 1.301 rastera (234/351/116/322/278 za
  2014–2018); 1.010 ima mapirane target piksele, a 291 ostaje označen kao „nema mapiranih
  piksela“. Pravilo je ostalo invariantno nakon uklanjanja target i kasnijih arrival
  oznaka. Na fiksnoj 20×20/100 m skali prozor postoji za 1.295 slučajeva; capture medijana
  je 36.71% na 1.008 opaženih targeta s validnim cropom. Širi prozori imaju veći capture
  među slučajevima gdje stanu, ali 254–566 rastera su premala za 4–6 km varijante. Ovo
  nije FireCase kohorta, nema usvojene domene i nije pokrenut replay/trening. Vidi
  [full screen report](research/CFSDS_FULL_DAY_PAIR_SCREEN.md),
  [JSON receipt](../reports/real-fire-data/cfsds-train-full-day-pair-screen.json) i
  [1301-row case/domain CSV](../reports/real-fire-data/cfsds-train-full-day-pair-screen.csv).
- Godišnja fuel mapa nije izrađena: v2014b nema potvrđen vremenski cutoff za NFDB/NBAC
  burn-scar layer. W.I.S.E. Figure 2 je javno transkribovana. Pregledani v20191114
  Decision Rules PDF opisuje bazno dodjeljivanje fuel klasa, ne succession prema starosti;
  2 GB raster ZIP nije pregledan. Tačan succession artifact, age arithmetic, specijalne
  klase i v2014b cutoff ostaju otvoreni; vidi fuel source-gate receipt.
  Alberta 2006–2025 fire-level suppression dataset je pronađen; direktni CSV download
  endpoint vratio je HTTP 403 pa nijedan događaj nije spojen. DEM/weather lineage je
  nepotpuna, a suppression status za slučajeve ostaje unknown.
- Naknadna provjera službenih BC historical perimeter poligona našla je po jedan
  2018 kandidat za svaki od tri spremljena cilja: `2018_1770` → N12395,
  `2018_241` → C11937, `2018_747` → N12413. To su geometrijski crosswalk kandidati,
  ne zajednički ID join. Operativni follow-up našao je javni izvještaj o containment-line
  radu na Coal Creek na target datum `2018_1770` i o planiranom paljenju/resursima Lost
  Dog Complexa dan prije targeta `2018_747`. Za C11937 postoji službeni next-day status,
  ali ne i pronađen dnevnik akcija. Sačuvani case manifesti i dalje imaju suppression
  `unknown`; detalji su u `reports/real-fire-data/cfsds-train-bc-operational-evidence.json`.
- TASK-015 NF-scar importer/cumulative-damage contract je implementiran i provjeren na
  izolovanom sintetičkom Sub20 C++ rolloutu; tri neispravna slučaja se odbijaju.
  Ovo ne otključava annual mapu ili CFSDS builder. Vidi ADR-025 i versioned receipt.

Metode i dokazi:

- [Spatial feasibility izvještaj](research/CFSDS_SPATIAL_FEASIBILITY.md) i
  [mašinski receipt](../reports/real-fire-data/cfsds-train-spatial-feasibility.json)
- [Target-blind pravilo i invariance proof](../reports/real-fire-data/cfsds-target-blind-input-invariance.json)
- [TRAIN shortlist](../reports/real-fire-data/cfsds-train-target-blind-window-screen.json)
- [Input/provenance QC](research/CFSDS_TRAIN_INPUT_QC.md), [fuel QC](research/CFSDS_TRAIN_QC.md)
- [Fuel-vintage review](research/CFSDS_FUEL_VINTAGE_REVIEW.md), [ADR-024](../docs/specs/DECISION_RECORDS.md#adr-024), [ADR-026](../docs/specs/DECISION_RECORDS.md#adr-026)
- [EXP-016 input-lineage audit](research/EXPERIMENT_LOG.md#exp-016--train-fuel-tree-correction-and-external-input-lineage-audit-2026-10-31)
- [Fuel mask proof](../reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json),
  [NF-scar importer contract receipt](../reports/firehose-verification/nonfuel-initial-scar-contract.json)
- [Fuel source-gate receipt](../reports/real-fire-data/cfsds-train-fuel-source-gate.json) for the v2014b cutoff and v20191114 rules-artifact inventory
- [BC perimeter crosswalk receipt](../reports/real-fire-data/cfsds-train-bc-perimeter-crosswalk.json) for the three saved 2018 TRAIN cases; no suppression fields
- [BC operational evidence receipt](../reports/real-fire-data/cfsds-train-bc-operational-evidence.json) for dated activity/status reports on the three BC candidate incidents; partial public evidence, not a full daily resource log
- [TASK-004c adapter/runtime receipt](../reports/firehose-verification/task004c-adapter-smoke.json)
- [No-action dijagnostika](research/CFSDS_NO_ACTION_DIAGNOSIS.md)

## Sljedeći taskovi po redu

1. Fuel source-gate pretraga javno dostupnih metadata/PDF-ova je završena bez cutoffa:
   v2014b NFDB/NBAC snapshot nije datiran, a javno navedeni v20191114 Decision Rules PDF
   pokriva baznu klasifikaciju, ne post-fire age-tree. Sljedeći dokaz mora doći od
   NRCan/CWFIS ili autora rada: eksplicitan v2014b cutoff i succession artifact/code ili
   potvrda da je Figure 2 kompletan algoritam. ZIP od 2 GB nije pregledan. Do tada drži
   gate zatvoren i ne generiši godišnju mapu.
2. Nastavi TRAIN-only BC suppression search: pribavi event-keyed dnevne zapise za N12395,
   C11937 i N12413 ako su javno dostupni; sadašnji izvještaji za Coal Creek/Lost Dog su
   snapshots i kandidatski join, a C11937 nema pronađene dnevne akcije. Za ostale TRAIN
   slučajeve odredi provinciju pa traži nadležni izvor; Alberta CSV/dictionary još treba
   dohvatiti službenim putem nakon HTTP 403. Fire-level resursi nisu dnevni plan, a bez
   dokaza ostavi status `unknown`.
3. Za prihvatljive TRAIN slučajeve kompletiraj DEM tile/version/hash i zabilježi tačan
   weather query, traženu i vraćenu lokaciju, model/polja/jedinice/timezone/raw hash.
   Tri sačuvana FireCase paketa su target-aware i njihove weather request lokacije nisu
   rekonstruisane; ne predstavljaj ih kao čiste benchmark ulaze.
4. Preregistruj iste no-action ulaze, seedove i horizont; uradi mali train-only replay
   gate na slučajevima koji prođu prethodne gateove i unaprijed definiši prihvatljive
   metrike. Ne birati trajanje epizode po targetu.
5. Tek nakon prolaza no-action gatea i heldout freeze-a razmatrati benchmark i fine-tuning.
   Target-independent day-pair i puni TRAIN prostorni pre-screen su završeni.

Opcije 20×20 na 200/300 m čuvaju oblik tenzora/akcija, ali mijenjaju prostorno značenje
svake akcije i modelskog širenja. 40×40 na 100 m čuva rezoluciju ali ne može koristiti
postojeći 20×20 checkpoint. Prostorni audit sam ne bira između njih; potreban je zaseban
FBP/policy ugovor prije izrade simulator paketa.

## Lokalni environment

Moderni Python 3.12.4 `.venv` s GIS alatima je u glavnom klonu, dok legacy Firehose
koristi izolovan Linux ARM64 Docker image. Raw CFSDS i ostali rasteri su ignorisani u
Git-u; u ovom audit worktreeu se čitaju preko putanje glavnog klona i ne kopiraju u Git.
Pravila i download izvori su u [manifestima](../reports/real-fire-data/cfsds-download-manifest.json)
i [runbooku](../HANDOFF.md). Ne miješati legacy SB3/Gym environment s modernim GIS venvom.

Pred predaju: `PYTHONPATH=src python3 -m unittest discover -s tests -v`, knowledge
validator `python3 scripts/validate_knowledge.py --strict`, synthetic CLI smoke i
`git diff --check`. Ne prepisivati postojeće `runs/`; svaki smoke treba svježe ignorisano
odredište.
