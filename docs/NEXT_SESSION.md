---
type: Handoff
title: SimFire/FEDS no-op gate — setup završен
---
# Naredni korak

## Trenutno stanje — 2026-11-03

Rad je na grani `codex/fireline-simfire-benchmark` u izdvojenom
`.worktrees/fireline-simfire-benchmark` worktreeu izvedenom iz `main`. Main checkout i
stari research worktree ostaju sačuvani.

Početni data/environment gate sada prolazi za prošireni, predeklarisani okvir velikih
požara: 99 train (2018/2019) + 20 validation (2023), sa pet FEDS stanja po 12h kroz
48h. Originalni 60-fire uzorak i dalje pada prag 20/8 (19 train, 7 validation); taj
neuspjeh nije prepisan. Test 2024 nije preuzet niti otvoren.

Završeno na ovom worktreeu:

- checksum-verified FEDS perimeter i aktivni-front arhivi; tačan aktivni front postoji
  za 119/119 početnih stanja i svaka linija je unutar 375m izvornog piksela od oboda;
- geometrijski preflight: cijeli početni obod/front stane u 256×256 ćelija po 180m za
  99/99 train i 20/20 validation;
- python 3.9.25 SimFire venv je lokalno postavljen, 85 paketa prolazi `uv pip check`;
- svih 99/99 train slučajeva ima validirane LANDFIRE fuel/elevation mape i početne
  FEDS maske; coverage receipt sadrži SHA-256 za 198 rastera. Validation mape se još
  ne povlače prije nego se parametri izaberu na trainu;
- checksum-verified gridMET `th`, `vs`, `fm100` godišnji arhivi za 2018/2019/2023;
  za 119 slučajeva uzorkovana su 4 dnevna vremenska forcing segmenta (396 train,
  80 validation). WAF faktor nije izabran;
- jedan 60-min SimFire integracijski smoke prolazi sa demonstracijskim vremenom:
  16 početnih ćelija, 27 kumulativnih ćelija nakon sata. To nije historijski no-op gate
  niti fizička validacija;
- istorijski 48h no-op runner radi na train slučaju uz gridMET po 12h segmentima. Plateau
  pilot daje 61.56 ha/IoU .64 pri WAF .20–.60, a pri .65 skače na 1,244 ha u 12h; .75–1.0
  preplavljuje model i dotiče rub. Nijedan WAF nije izabran. 5-min interni korak je samo
  kandidat za efikasnost i nije zaključan;
- puni suite od 58 testova prolazi bez preskakanja u SimFire venv-u; strict validator
  provjerava 69 Markdown fajlova, a CLI smoke i svih 85 paketnih zavisnosti prolaze.

Raw arhive, venv, case rasteri, weather uzorci i rollout izlazi nalaze se u ignorisanom
`.local/`. Glavni kod, sažeti izvještaji i checksumi su verzionisani.

## Glavni artefakti

- [Dataset crosswalk i ograničenja](research/FPA_FEDS_CROSSWALK.md)
- [Environment setup, mapa i weather provenance](research/SIMFIRE_ENVIRONMENT.md)
- [ADR-019: mreža, agentova informacija i no-op gate](specs/DECISION_RECORDS.md)
- [119-case episode manifest](../data/manifests/feds-episode-cohort-v1.json)
- [Active-front coverage](../reports/real-fire-data/feds-active-front-coverage-v1.json)
- [180m map preflight](../reports/real-fire-data/feds-simfire-grid-preflight-v1.json)
- [gridMET archive/sample coverage](../reports/real-fire-data/feds-gridmet-weather-coverage-v1.json)
- [one-case LANDFIRE/SimFire smoke receipt](../reports/real-fire-data/feds-simfire-input-smoke-v1.json)
- [99-case train LANDFIRE coverage](../reports/real-fire-data/feds-simfire-input-train-coverage-v1.json)
- [single-case no-op WAF sensitivity diagnostic](../reports/real-fire-data/feds-simfire-noop-pilot-v1.json)
- [Pythoni lock](../requirements/simfire-macos-arm64-py39.freeze.txt)

## Sljedeća implementacija

1. Kalibrisati mali broj zajedničkih simulator parametara na train kohorti uz train-only
   48h no-op i persistence/elipsu. Pilot pokazuje pragovno ponašanje, zato ne podešavati
   WAF po požaru ili samo prema Plateau cilju; izmjeriti cijenu rollouts prije batcha.
2. Kad je shared setup izabran i zaključan, preuzeti validation mape i provjeriti no-op
   prema istim metrikama. Ako ne nadmaši persistence i elipsu ili udara u rub, zaustaviti
   RL dio i dijagnosticirati model/inpute.
3. Tek nakon no-op gatea implementirati sporo građenje linije, wait/16 sektora,
   20-članu ekipu × 8h i budžete 0/1/2/4 smjene. Nakon tih testova dodati frozen PPO i
   fine-tuning na istim epizodama, budžetima, vremenu, informacijama i seedovima.
4. Otvoriti 2024 test samo za završni obračun, nakon što su izbori zaključani.

Pri radu ostaviti 2024 zatvoren. Ne učitavati buduće FEDS obode u početno stanje ili
policy observation; mogu se koristiti samo za post-hoc poređenje. GridMET budućih 12h
segmenata je ex-post forcing za simulator, ne prognoza dostupna agentu.

## Provjere pred predaju

Pokrenuti `PYTHONPATH=src python3 -m unittest discover -s tests -v`, repo smoke CLI,
`python3 scripts/validate_knowledge.py --strict` sa `requirements/knowledge.txt`,
`uv pip check --python .local/simfire-venv/bin/python` i `git diff --check`.
Ne preuzimati/commitovati raw arhive ili venv. Ne pokretati dug trening, cloud compute,
push ili merge.

## Starija putanja

CFSDS/Cell2Fire izvještaji su historijski i odvojeni. Njihovi nalazi nisu SimFire
rezultati niti zamjena za ovaj 48h no-op gate.
