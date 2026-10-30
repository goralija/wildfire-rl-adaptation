---
type: Handoff
title: Naredna sesija — nakon TASK-018 dijagnostike
---
# Naredna sesija

## Trenutno stanje

TASK-018 dijagnostička faza je završena na tri već postojeća **train-only** CFSDS no-action
replaya (`2018_747`, `2018_241`, `2018_1770`). Nisu napravljeni novi C++ replayi,
fine-tuning ni heldout kalibracija. Nema dokaza da agent smanjuje stvarnu štetu i
simulator još ne prolazi no-action reality-check.

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
- Suppression/gašenje je nepoznato, a prethodni output adapter ne razlikuje pouzdano
  iscrpljenost mreže, nestanak aktivnog fronta i vremenski horizon. Tačan fizički uzrok
  prevelikog rasta nije izolovan.

Detalji, opažanja naspram hipoteza i ograničenja su u
[TASK-018 dijagnozi](research/CFSDS_NO_ACTION_DIAGNOSIS.md), a svi fiksni vremenski
presjeci i hashovi u
[timeline reportu](../reports/real-fire-data/cfsds-no-action-timeline.json).

## Sljedeći zadatak: TASK-004c adapter

Prije nastavka dodatnog train replaya napraviti pouzdanu evidenciju epizode:

1. Sačuvati kumulativno pogođene/opožarene ćelije i početni historical scar i nakon
   tretiranja ćelije; postojeći Sub20 primjer ima poznato 206 naspram 207 neslaganje.
2. Exportovati aktivni front odvojeno od starijih opožarenih ćelija; C++ kod 1 trenutno
   spaja oba stanja.
3. Vratiti imenovani terminalni razlog: završetak zbog horizonta, nestanka fronta,
   potrošenog prostora/ćelija, subprocess greške ili timeout-a.
4. Zadržati checkpoint kontrakt RGB 3×20×20 / `Discrete(400)` i legacy no-op `-1`.
   Ne mijenjati reward ili model head usput.
5. Dodati regresijske testove i ponovljiv no-action/paired smoke nakon implementacije.

Poslije TASK-004c: završiti train-only terrain/weather/suppression i fuel-vintage QC
(TASK-015), zatim provesti ograničene train-only kontrolne replaye koji mijenjaju jedan
weather/FBP ulaz odjednom. Definisati zajednički vremenski horizont prije ikakve politike;
ne izabrati poseban prekid požara tako što se pogleda njegov target. No-action gate i
heldout ID freeze ostaju preduslovi benchmarka i fine-tuninga.

## Bitni artefakti

- [TASK-018 dijagnoza](research/CFSDS_NO_ACTION_DIAGNOSIS.md)
- [TASK-018 timeline/hash receipt](../reports/real-fire-data/cfsds-no-action-timeline.json)
- [TASK-015 fuel audit](research/CFSDS_TRAIN_QC.md) i
  [mašinski report](../reports/real-fire-data/cfsds-train-fuel-qc.json)
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
