---
type: Handoff
title: Naredna sesija — nakon TASK-015 fuel-vintage mask proofa
---
# Naredna sesija

## Trenutno stanje

TASK-018 dijagnostička faza je završena na tri **train-only** CFSDS no-action replaya
(`2018_747`, `2018_241`, `2018_1770`). Nisu napravljeni novi CFSDS replays,
fine-tuning ni heldout kalibracija. Kasniji Sub20 C++ runovi služe samo adapter smokeu.
Nema dokaza da agent smanjuje stvarnu štetu i simulator još ne prolazi no-action
reality-check.

Glavni nalazi:

- Fuel/FBP ulaz koristi isti kanadski FBP 2014b sloj (250 m prebačen na 100 m) i istu
  lookup tabelu. Te tri modelirane mape imaju klase C2/C3/D1; ne nedostaju im posebni
  mixedwood/grass parametri. Fuel-only PASS nije fizička validacija.
- Sačuvani simulator grids na fiksnim 30–1.440 minuta pokazuju različite brzine rasta.
  Sva tri slučaja dotaknu rub 20×20 prozora za 34–52 minute; `2018_241` napuni svih
  400 ćelija. CFSDS je dnevni satelitski interpolisani cilj bez tačnog sata izgaranja.
- `Weather.csv` ima 24 satna reda, a pinovani C++ kod ima do 60 minuta po redu, pa je
  stvarni maksimalni horizont 1.440 simulator minuta. Polje u ranijoj probe datoteci
  pogrešno je pokazivalo 480 jer je množilo interval odluka (`steps_per_action=8`) sa
  60. Kod je popravljen da broji redove; raniji replayi nisu mijenjani.
- Suppression/gašenje je nepoznato. TASK-004c adapter sada emitira named terminal reason
  i zasebne affected/front/treatment skupove; batch potvrđuje integraciju, ali ne
  razrješava tačan fizički uzrok prevelikog rasta.

Detalji, opažanja naspram hipoteza i ograničenja su u
[TASK-018 dijagnozi](research/CFSDS_NO_ACTION_DIAGNOSIS.md), a svi fiksni vremenski
presjeci i hashovi u
[timeline reportu](../reports/real-fire-data/cfsds-no-action-timeline.json).

## Završeni adapter i trenutno stanje TASK-015 input QC-a

TASK-004c adapter je lokalno završen. C++ sada odvaja stariji scar od aktivnog fronta,
čuva kumulativno pogođene ćelije i uz završetak ispisuje imenovani razlog. Python `info`
dobija isti terminalni spisak i reason. Ćelija koju C++ u istom koraku označi i kao
pogođenu i kao tretiranu ostaje u kumulativnom C++/Python izvještaju iako se na
kategorijalnom gridu vidi kao `-1`. RGB 3×20×20, `Discrete(400)`, no-op `-1`, reward i
checkpoint težine ostaju isti. Fixture i 12/12 inference rollouta prolaze; detalji i
ograničenja su u [TASK-004c receiptu](../reports/firehose-verification/task004c-adapter-smoke.json).

**Ovo je adapter/runtime prolaz, ne fire-behavior prolaz.** Svih 12 batch slučajeva završilo
je na `weather_horizon`; u toj matrici nismo direktno izvršili C++ grane `front_extinguished`,
`grid_exhausted` ili `no_ignition`. CFSDS no-action razlika i rubni efekat ostaju otvoreni,
pa nema fizičke validacije, dokaza da agent smanjuje štetu, policy benchmarka ni treniranja.

Train-only input QC je sada izmjeren za tri dostupna FireCase paketa i fuel-vintage
izvori su pregledani. Još nije bezbjedno proglasiti train slučajeve potpuno spremnim:
17 paketa nedostaje, 2014b nema dokumentovan per-pixel vremenski cutoff, 2019 CanFG
je u razvojnom direktoriju i koristi NBAC, izvorni DEM tile/weather field lineage nisu
sačuvani, a suppression je unknown za svih 20. Detalji i redoslijed su u
[input QC izvještaju](research/CFSDS_TRAIN_INPUT_QC.md) i
[mašinskom receipt-u](../reports/real-fire-data/cfsds-train-input-qc.json).

Sljedeći tehnički koraci:

1. Završeni su samo dva pripremna dokaza: pre-target maska na jednom TRAIN eventu
   (`2018_747`) i C++ fixture koji karakteriše `NF` scar odbijanje. Pogledati
   [mask receipt](../reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json),
   [import receipt](../reports/firehose-verification/nonfuel-initial-scar-compatibility.json),
   ADR-020 i EXP-010. Nije izrađena godišnja fuel mapa i nije mijenjan case builder.
2. **Prvi naredni zadatak:** prije benchmarka ukloniti buduću informaciju iz početnog fronta: trenutni case builder
   bira day n-1 ćelije prema njihovoj susjednosti targetu day n. W.I.S.E. paper to koristi
   i priznaje kao favorizujuću buduću informaciju. Definisati front samo iz n-1 i ranijih
   podataka, preregistrovati ga, pa testirati da se početni input ne mijenja kad se target
   maska promijeni.
3. Pribaviti/dokumentovati bazni FBP as-of-event cutoff i prepisati/provjeriti v20191114
   burn-scar succession tree, uključujući licencu i per-pixel porijeklo. Ne koristiti
   v2019 development ili 2024 raster kao gotovu historijsku mapu.
4. Odlučiti i fixtureom testirati importer contract za slučaj da validno succession
   pravilo staru ćeliju označi kao non-fuel: scar mora ostati u kumulativnoj historijskoj
   šteti, dok takva ćelija ne smije postati gorivo za širenje; testirati kako se aktivni
   front pravilno predstavlja.
5. Tek nakon tih dokaza napraviti mali annual-map rezultat za jedan TRAIN event; assertioni
   moraju isključiti target dan n i sve kasnije datume, a target-blind day n-1 front mora
   biti kompatibilan.
6. Za train slučajeve odabrane za replay prikupiti izvornu terrain tile provenancu i
   kompletan vremenski API request, resolved location, units i variable-source mapping;
   zadržati unknown ako ih se ne može dokazati.
7. Potražiti event-level suppression dokaz od nadležne agencije. CNFDB dokumentuje
   agency-provided lokacije/perimetre i ograničenu potpunost, a ne već spojenu timeline
   akcija ovog projekta; nema prihvaćanja EULA bez ovlaštenja.
8. Unaprijed zapisati ulazne varijante, seedove, metrike i zajednički horizont, pa tek
   onda uraditi train-only kontrolisane no-action replays. Ne birati per-event trajanje
   prema targetu i ne koristiti validation/test ishode.
9. Heldout event IDs zamrznuti tek nakon prihvatljivog train no-action gatea. Benchmark
   i fine-tuning ostaju blokirani do tada.

Benchmark i fine-tuning ostaju blokirani dok se ne prođu i no-action quality gate i
heldout freeze. Ne otvarati validation/test rastere ili ishode radi QC/tuninga.

## Bitni artefakti

- [TASK-018 dijagnoza](research/CFSDS_NO_ACTION_DIAGNOSIS.md)
- [TASK-018 timeline/hash receipt](../reports/real-fire-data/cfsds-no-action-timeline.json)
- [TASK-015 fuel audit](research/CFSDS_TRAIN_QC.md) i
  [mašinski report](../reports/real-fire-data/cfsds-train-fuel-qc.json)
- [TASK-015 input audit](research/CFSDS_TRAIN_INPUT_QC.md) i
  [mašinski report](../reports/real-fire-data/cfsds-train-input-qc.json)
- [X/Y data pipeline](research/REAL_CASE_PIPELINE.md)
- [cijeli real-fire report index](../reports/real-fire-data/index.md)
- [backlog](BACKLOG.md), [odluke](specs/DECISION_RECORDS.md) i [status](STATUS.md)

## Lokalni environment

Moderni Python 3.12.4 `.venv` ima GIS/knowledge pakete. Legacy Firehose je odvojeni
Linux ARM64 Docker image. Sirovi CFSDS, DEM, fuel karte, generated FireCase fajlovi i
simulator grids ostaju ignorisani; mali kod, manifests/hashovi, sažeci i rezultati idu u
Git. U čistom checkoutu koristiti [download manifest](../reports/real-fire-data/cfsds-download-manifest.json)
i pipeline runbook. Ne instalirati legacy SB3/Gym pakete u moderni venv.

Prije handoffa pratiti `AGENTS.md`: fokusirani/puni testovi, strict knowledge validator,
i synthetic CLI smoke. Nikad ne prepisivati postojeće `runs/` rezultate; odabrati nov
output folder.
