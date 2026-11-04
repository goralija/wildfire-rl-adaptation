---
type: Handoff
title: Nastavak nakon koraka 5–8 (SimFire/FEDS, 2026-11-04)
---
# Naredni korak

## Trenutno stanje — 2026-11-04

Grana `codex/overnight-steps-5-8` je izvedena iz `codex/fireline-simfire-benchmark`
(PR #3) i sadrži korake 5–8. Ništa nije spojeno u `main`. Lokalni ulazi, venv, modeli i
puni izvještaji su u ignorisanom `.local/` na Harunovom računaru; obnova je opisana u
[environment recordu](research/SIMFIRE_ENVIRONMENT.md).

1. **Gate (korak 5) je FAIL.** Dijagnoza i preregistrovana mreža su u ADR-023/024.
   Zamrznuti gate zapis gotovo ne širi vatru. Strogo pravilo je strukturno naklonjeno
   persistence referenci jer su mnogi FEDS požari stvarno zaustavljeni.
2. **Validation (korak 6)** je skoriran jednom po zapisu. Stress zapis (WAF .01 / ROS 1.0)
   prolazi strogo pravilo na 20 VALIDATION slučajeva, iako je pao na TRAIN-u.
3. **Intervencije i benchmark (korak 7, ADR-025)** postoje i testirani su.
4. **Prilagodba budžetu (korak 8, ADR-026/027)**: osnovni PPO pobjeđuje no-op, fine-tuning
   po budžetu ne daje mjerljivu korist, a downwind heuristika je jednako dobra ili bolja.
   Sve je simulatorski i eksploratorno.

## Odluke za tim (ne donositi ih bez korisnika)

- Prihvatiti li stress scenarij kao radni simulator za predaju ili tražiti growth-aware
  gate, npr. ocjenu samo na požarima koji u FEDS-u rastu ili jednostavan model
  zaustavljanja/gašenja, prije bilo kakve tvrdnje o kalibraciji.
- Spojiti li ovu granu u PR #3 ili je držati kao zaseban draft PR.
- Šta od TASK-007 (prioritetna područja) i TASK-020 (gradnja linije kroz vrijeme, više
  linija po odluci) ulazi u obim prije postera.

## Najkorisniji tehnički nastavak

1. **Jači signal budžeta:** dozvoliti više jedinica po 12h odluci ili duži aktivni vijek
   ćelije, da veći budžet ima gdje djelovati. To je nova preregistracija (novi ADR), a ne
   izmjena ADR-026.
2. **Više seedova i koraka** ako tim želi uže intervale. Trenutni trošak je oko 8 odluka/s
   na 7 procesa.
3. **TASK-007:** težina prioritetnih ćelija u nagradi i ablacija ukupne naspram
   prioritetne štete.
4. **TASK-009:** grafikon `reports/real-fire-data/feds-simfire-policy-benchmark-v1.png` i
   ADR-027 tabela su polazište za poster. TEST 2024 otvoriti tek za završni obračun s
   unaprijed zaključanim politikama.

## Komande

Sve iz roota worktreea, uz `PYTHONPATH=src`, `SDL_VIDEODRIVER=dummy`, `OMP_NUM_THREADS=1`
i `MPLCONFIGDIR=.local/mpl-cache`:

```sh
scripts/run_budget_adaptation_experiment.sh            # trening po ADR-026 (SEEDS, BASE_STEPS, FT_STEPS)
OUT=.local/bench/NEW.json scripts/run_budget_adaptation_benchmark.sh
.local/simfire-venv/bin/python scripts/analyze_budget_adaptation.py .local/bench/NEW.json
.local/simfire-venv/bin/python scripts/plot_budget_benchmark.py .local/bench/NEW.json --out .local/bench/NEW.png
```

## Provjere prije predaje

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src .local/simfire-venv/bin/python -m unittest discover -s tests
PYTHONPATH=src python3 -m wildfire_rl.cli --config configs/smoke.json --out runs/NEW-ID
python3 scripts/validate_knowledge.py --strict
UV_CACHE_DIR=.local/uv-cache uv pip check --python .local/simfire-venv/bin/python
git diff --check
```

Ne otvarati TEST 2024. Ne pokretati plaćeni compute, push u tuđu granu ili merge bez
korisnikovog naloga. CFSDS/Cell2Fire rezultati ostaju historijski i odvojeni.
