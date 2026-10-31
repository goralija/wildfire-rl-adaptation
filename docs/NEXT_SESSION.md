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
  burn-scar layer. W.I.S.E. Figure 2 je sada pronađena i transkribovana, ali starosna
  računica, specijalne klase i stvarni v20191114 rules artifact nisu provjereni.
  Alberta 2006–2025 fire-level suppression dataset je pronađen; direktni CSV download
  endpoint vratio je HTTP 403 pa nijedan događaj nije spojen. DEM/weather lineage je
  nepotpuna, a suppression status za slučajeve ostaje unknown.
- Naknadna provjera službenih BC historical perimeter poligona našla je po jedan
  2018 kandidat za svaki od tri spremljena cilja: `2018_1770` → N12395,
  `2018_241` → C11937, `2018_747` → N12413. To su geometrijski crosswalk kandidati,
  bez dnevnih resursa ili akcija gašenja; suppression ostaje unknown. Receipt je
  `reports/real-fire-data/cfsds-train-bc-perimeter-crosswalk.json`.
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
- [BC perimeter crosswalk receipt](../reports/real-fire-data/cfsds-train-bc-perimeter-crosswalk.json) for the three saved 2018 TRAIN cases; no suppression fields
- [TASK-004c adapter/runtime receipt](../reports/firehose-verification/task004c-adapter-smoke.json)
- [No-action dijagnostika](research/CFSDS_NO_ACTION_DIAGNOSIS.md)

## Sljedeći taskovi po redu

1. Nastavi fuel source gate: pribavi autoritativni v2014b NFDB/NBAC cutoff ili zadrži
   vintage unresolved; provjeri javno prepisanu W.I.S.E. Figure 2 prema izvornom
   v20191114 artifactu i utvrdi računanje starosti/specijalne klase. Ne generiši godišnju
   mapu dok ovo nije riješeno.
2. Za tri spremljena TRAIN slučaja pokušaj pronaći BC operativne/suppression zapise preko
   kandidatskih ID-jeva N12395, C11937 i N12413; provjeri identitet preko fire year, date,
   target chronology i perimeter prije ikakvog statusa. BC perimeter je samo identifikator,
   ne evidencija gašenja. Za ostale TRAIN kandidate odredi provinciju pa traži nadležni
   izvor; Alberta CSV/dictionary još treba dohvatiti službenim putem nakon HTTP 403.
   Fire-level resursi nisu dnevni plan, a bez dokaza ostavi status `unknown`.
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
