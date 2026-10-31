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
- TRAIN screen sadrži 25 parova, pet po godini, ali day-pair eligibilnost je zahtijevala
  target-day zapis i pozitivnu `firearea`; puna nezavisnost članstva od outcome-a nije
  dokazana. Ne koristiti taj screen kao konačni benchmark cohort.
- Prostorni audit uporedio je iste parove na oko 2, 3, 4 i 6 km. U 2 km target uđe u
  4/25 prozora (median capture 0%); u oko 4 km uđe u 19/25, ali median je samo 1.95%;
  u oko 6 km median raste na 15.31%, a dvije slike su premale za takav prozor. Nije
  usvojen veći model grid i nisu napravljeni FireCase-ovi/replayi.
- Godišnja fuel mapa nije izrađena: v2014b nema potvrđen pixel-level vremenski cutoff,
  succession crosswalk nije transkribovan/validiran, a C++ importer odbija historijski
  scar na `NF` ćeliji. DEM/weather lineage je nepotpuna, suppression unknown.

Metode i dokazi:

- [Spatial feasibility izvještaj](research/CFSDS_SPATIAL_FEASIBILITY.md) i
  [mašinski receipt](../reports/real-fire-data/cfsds-train-spatial-feasibility.json)
- [Target-blind pravilo i invariance proof](../reports/real-fire-data/cfsds-target-blind-input-invariance.json)
- [TRAIN shortlist](../reports/real-fire-data/cfsds-train-target-blind-window-screen.json)
- [Input/provenance QC](research/CFSDS_TRAIN_INPUT_QC.md), [fuel QC](research/CFSDS_TRAIN_QC.md)
- [Fuel mask proof](../reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json),
  [NF-scar importer receipt](../reports/firehose-verification/nonfuel-initial-scar-compatibility.json)
- [TASK-004c adapter/runtime receipt](../reports/firehose-verification/task004c-adapter-smoke.json)
- [No-action dijagnostika](research/CFSDS_NO_ACTION_DIAGNOSIS.md)

## Sljedeći taskovi po redu

1. Definiši i zapiši unaprijed target-independent pravilo za izbor TRAIN day-pair
   epizoda. Razdvoji tri stvari: dostupnost opaženog targeta za naknadni score, pravilo
   koje izabere dan n, i geometriju prozora koja mora koristiti samo podatke prije n.
   Raniji screen je koristio target-day red i pozitivnu `firearea`, zato taj dio prvo
   treba pregledati.
2. Provedi train-only prostorni pre-screen svih prihvatljivih 2014–2018 epizoda prema
   unaprijed navedenim fizičkim domenama. Sačuvaj target metrike samo kao naknadni
   feasibility check. Audit preko 25 starih kandidata nije iscrpan.
3. Prije pravljenja novih slučajeva potvrdi as-of-event fuel-map izvor, cutoff,
   succession crosswalk i uslove korištenja. Ne proglašavati v2014b vremenski sigurnim
   bez dokaza; ne koristiti razvojni v2019 ili post-event 2024 sloj kao gotov odgovor.
4. Fixtureom definiši kako se historijska kumulativna šteta čuva kad je ćelija non-fuel,
   a da takva ćelija ne širi vatru; aktivni front mora imati zaseban jasan ugovor.
5. Za TRAIN slučajeve koji prođu ove gateove pribavi DEM tile/version/hash i potpunu
   weather request/location/field/unit lineage. Suppression status tražiti iz službenih
   izvora; ako ga ne možemo povezati, ostaje `unknown`.
6. Tek tad preregistruj iste no-action ulaze, seedove i horizont; uradi mali train-only
   replay gate i unaprijed definiši prihvatljive metrike. Ne birati trajanje epizode po
   targetu. No-action gate i heldout freeze su preduslovi za benchmark/trening.

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
