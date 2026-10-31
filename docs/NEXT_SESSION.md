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
  burn-scar layer, a succession crosswalk nije transkribovan/validiran. Public-source
  pregled je pronašao CWFIS Open Government Licence - Canada i službene baseline FBP
  class rules; ta pravila nisu post-fire succession stablo. Importer sada prihvata
  samo eksplicitni `scar_nf` marker na tačnoj `NF` ćeliji, a DEM/weather lineage je
  nepotpuna i suppression unknown.
- TASK-015 NF-scar importer/cumulative-damage contract je implementiran i provjeren na
  izolovanom sintetičkom Sub20 C++ rolloutu; tri neispravna slučaja se odbijaju.
  Ovo ne otključava annual mapu ili CFSDS builder. Vidi ADR-025 i versioned receipt.

Metode i dokazi:

- [Spatial feasibility izvještaj](research/CFSDS_SPATIAL_FEASIBILITY.md) i
  [mašinski receipt](../reports/real-fire-data/cfsds-train-spatial-feasibility.json)
- [Target-blind pravilo i invariance proof](../reports/real-fire-data/cfsds-target-blind-input-invariance.json)
- [TRAIN shortlist](../reports/real-fire-data/cfsds-train-target-blind-window-screen.json)
- [Input/provenance QC](research/CFSDS_TRAIN_INPUT_QC.md), [fuel QC](research/CFSDS_TRAIN_QC.md)
- [Fuel-vintage review](research/CFSDS_FUEL_VINTAGE_REVIEW.md), [ADR-024](../docs/specs/DECISION_RECORDS.md#adr-024)
- [Fuel mask proof](../reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json),
  [NF-scar importer contract receipt](../reports/firehose-verification/nonfuel-initial-scar-contract.json)
- [TASK-004c adapter/runtime receipt](../reports/firehose-verification/task004c-adapter-smoke.json)
- [No-action dijagnostika](research/CFSDS_NO_ACTION_DIAGNOSIS.md)

## Sljedeći taskovi po redu

1. Iz javnih izvora je potvrđeno da nema dovoljno dokumentovanog cutoffa za v2014b
   NFDB/NBAC scar layer ni javno transkribovanog v20191114 post-fire succession stabla.
   Pribavi autoritativne datume/ruleset ili zadrži fuel vintage kao unresolved; ne koristi
   target-capture metrike i ne generiši godišnju mapu dok ovaj gate ne prođe.
2. Za TRAIN parove koji prođu izvorni fuel/input gate pribavi DEM tile/version/hash, kompletnu
  weather request/location/field/unit lineage i suppression evidence; bez event-level
  dokaza suppression ostaje `unknown`.
3. Preregistruj iste no-action ulaze, seedove i horizont; uradi mali train-only replay
  gate na slučajevima koji prođu prethodne gateove i unaprijed definiši prihvatljive
  metrike. Ne birati trajanje epizode po targetu.
4. Tek nakon prolaza no-action gatea i heldout freeze-a razmatrati benchmark i fine-tuning.
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
