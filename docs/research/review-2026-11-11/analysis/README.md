---
type: Analysis Record
title: "Skripte i izlazi pregleda 2026-11-11"
description: "TRAIN-only analize postojećih izlaza faze 1 i 2 i jedan probni SimFire run; kako ih ponoviti."
status: stable
generated: {by: "process:claude-code", at: "2026-11-12T10:00:00Z"}
sources:
  - resource: /docs/research/review-2026-11-11/SHORT_EPISODES.md
  - resource: /docs/research/review-2026-11-11/TUNED_HEURISTICS.md
  - resource: /docs/research/review-2026-11-11/INTERVENTIONS.md
---
# Skripte i izlazi pregleda 2026-11-11

Skripte čitaju samo TRAIN podatke. Ulazni fajlovi su lokalni i ignorisani (`.local/`); u
novom klonu ih treba napraviti ponovo po [HANDOFF](../../../../HANDOFF.md) i
[HANDOFF_STAGE_1_2](../../../HANDOFF_STAGE_1_2.md). Izlazi (`*.out`) su sačuvani kakvi su
dobijeni 2026-11-11 na commitu `61f0ebf`.

| Skripta | Izlaz | Šta računa | Koristi ga |
| --- | --- | --- | --- |
| `train_bench_analysis.py` | `train_bench_analysis.out` | varijansa no-opa, efekat linije, najbolja politika po požaru unazad | [SHORT_EPISODES](../SHORT_EPISODES.md) |
| `extra.py` | `extra.out` | veličina početnog fronta, raspon ishoda po sektoru | [SHORT_EPISODES](../SHORT_EPISODES.md) |
| `obs_vs_forcing.py` | `obs_vs_forcing.out` | poklapanje vjetra koji agent vidi i vjetra koji pokreće vatru | [SHORT_EPISODES](../SHORT_EPISODES.md) |
| `E_heuristics_analysis.py` | `E_heuristics_analysis.out` | determinizam, jaz do najboljeg, selektor s LOO, prag otkrivanja, zasluga linije | [TUNED_HEURISTICS](../TUNED_HEURISTICS.md) |
| `probe_lines.py` | (brojke u izvještaju) | da li vatra prelazi liniju: `advancing_front`, B=4, 98 TRAIN požara | [INTERVENTIONS §1.9](../INTERVENTIONS.md) |

## Kako pokrenuti

Iz korijena checkouta koji ima `.local/bench/` i `.local/gridmet/` (na Harunovom računaru
worktree faze 2), sa SimFire Python 3.9 okruženjem (`P`, vidi HANDOFF). `A` mora biti apsolutna
putanja do ovog foldera u checkoutu koji ga sadrži (poslije merge-a: `main`). Putanja do gate
izvještaja je worktree faze 1. Probni run nije sačuvao izlazni fajl; njegove brojke su samo u
[INTERVENTIONS §1.9](../INTERVENTIONS.md).

```sh
A=/apsolutna/putanja/do/docs/research/review-2026-11-11/analysis
GATE=../task-026-stage-1/.local/gate/adr030/waf-0.1-ros-1.json
nice -n 19 $P -B $A/train_bench_analysis.py .local/bench/adr030-train.json .local/gridmet/feds-episode-weather-v1.json
nice -n 19 $P -B $A/extra.py $GATE .local/bench/adr030-train.json
nice -n 19 $P -B $A/obs_vs_forcing.py . .local/gridmet/feds-episode-weather-v1.json
nice -n 19 $P -B $A/E_heuristics_analysis.py . .local/bench/adr030-train.json .local/gridmet/feds-episode-weather-v1.json $GATE
# probni SimFire run (nekoliko minuta; prvi argument je broj TRAIN požara)
PYTHONPATH=src nice -n 19 $P -B $A/probe_lines.py 98
```

Argumenti su preuzeti iz samih skripti (`sys.argv`). Skripte nisu dio testiranog paketa i
nisu prošle reviziju kao kod u `src/`; služe kao trag kako su brojke u izvještajima dobijene.
