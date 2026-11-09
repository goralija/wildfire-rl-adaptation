---
type: Playbook
title: Gdje pronaći kod, podatke i način rada
description: Rutiranje istraživačkih i tehničkih zadataka na kanonske fajlove i komande.
status: stable
generated: {by: "process:claude-code", at: "2026-11-04T03:40:00Z"}
sources:
  - resource: /src/wildfire_rl/simulator.py
  - resource: /src/wildfire_rl/evaluation.py
  - resource: /src/wildfire_rl/firehose_probe.py
  - resource: /HANDOFF.md
---
# Mapa projekta i radnih zadataka

| Ako radiš na… | Prvo pročitaj | Kod/dokazi i provjera |
| --- | --- | --- |
| CFSDS cohort/replay TASK-015/016 | [pipeline](../docs/research/REAL_CASE_PIPELINE.md), [dataset pregled](../docs/research/REAL_FIRE_DATASETS.md) | [cohort manifest](../data/manifests/cfsds-v1_1-pilot-cohort.json), [case builder](../scripts/build_cfsds_case.py), [replay metrics](../scripts/evaluate_cfsds_replay.py), [reports](../reports/real-fire-data/index.md) |
| SimFire/FEDS growth gate i zamrzavanje (ADR-030 §3, ADR-031) | [ADR-030/031](../docs/specs/DECISION_RECORDS.md), [handoff faza 1–2](../docs/HANDOFF_STAGE_1_2.md) | [cohort evaluator](../scripts/evaluate_feds_train_noop.py), [izbor kandidata](../scripts/select_feds_growth_gate.py), [VALIDATION sažetak](../scripts/summarize_feds_validation_gate.py), [testovi izbora](../tests/test_select_feds_growth_gate.py), [freeze zapis](../configs/frozen/feds-simfire-growth-gate-freeze-v1.json), [allowlist](../configs/frozen/validation-freeze-allowlist.json), [TRAIN gate](../reports/real-fire-data/feds-simfire-train-growth-gate-v1.json), [VALIDATION](../reports/real-fire-data/feds-simfire-validation-growth-gate-v1.json); gate PASS, nije fizička validacija |
| SimFire/FEDS no-op gate (ADR-022–024) | [environment record](../docs/research/SIMFIRE_ENVIRONMENT.md), [odluke](../docs/specs/DECISION_RECORDS.md), [next steps](../docs/NEXT_SESSION.md) | [shared setup](../src/wildfire_rl/feds_simfire_setup.py), [cohort evaluator](../scripts/evaluate_feds_train_noop.py), [diagnosis](../scripts/diagnose_feds_noop_gate.py), [freeze records](../configs/frozen/feds-simfire-gate-freeze-v1.json), [validation no-op](../reports/real-fire-data/feds-simfire-validation-noop-v1.json); gate FAIL |
| Intervencije, heuristike, budget adaptation (ADR-025–027) | [ADR-025–027](../docs/specs/DECISION_RECORDS.md), [benchmark summary](../reports/real-fire-data/feds-simfire-policy-benchmark-v1.json) | [env](../src/wildfire_rl/feds_simfire_env.py), [heuristics](../src/wildfire_rl/feds_heuristics.py), [training](../scripts/train_feds_budget_adaptation.py), [experiment runner](../scripts/run_budget_adaptation_experiment.sh), [benchmark](../scripts/benchmark_feds_policies.py), [benchmark runner](../scripts/run_budget_adaptation_benchmark.sh), [analysis](../scripts/analyze_budget_adaptation.py), [plot](../scripts/plot_budget_benchmark.py); simulator-only, stress scenario |
| Sintetički CA trening i test na stvarnim startovima (ADR-028) | [spec](../docs/research/SYNTHETIC_CA_ENV.md), [izvještaji](../reports/synthetic/index.md) | [CA](../src/wildfire_rl/synthetic_ca.py), [env](../src/wildfire_rl/synthetic_env.py), [heuristike](../src/wildfire_rl/synthetic_heuristics.py), [real cases](../src/wildfire_rl/synthetic_real_cases.py), [PPO](../scripts/train_synthetic_ppo.py), [BC](../scripts/bc_warm_start.py), [eval](../scripts/evaluate_synthetic_policies.py), [real test](../scripts/evaluate_real_cases.py), [gap](../scripts/diagnose_synthetic_calibration_gap.py), [testovi](../tests/test_synthetic_ca.py); simulator-only |
| FEDS/SimFire technical PPO smoke | [runtime and limitations](../docs/research/SIMFIRE_ENVIRONMENT.md), [ADR-021](../docs/specs/DECISION_RECORDS.md) | [MaskablePPO smoke CLI](../scripts/train_feds_simfire.py), [budget/damage tests](../tests/test_feds_simfire_env.py) |
| Sintetičkoj dinamici, budžetu i šteti | [pravila](../docs/specs/BUSINESS_RULES.md), [domain](../docs/specs/DOMAIN.md) | [simulator.py](../src/wildfire_rl/simulator.py): Scenario/GridFire; [testovi](../tests/test_simulator.py) |
| Politikama i paired evaluaciji | [protokol](../docs/research/PROTOCOL.md), [pilot](../reports/pilot/README.md) | [policies.py](../src/wildfire_rl/policies.py), [evaluation.py](../src/wildfire_rl/evaluation.py), [CLI](../src/wildfire_rl/cli.py), [testovi](../tests/test_evaluation.py) |
| Modernom Gym/PPO smokeu | [HANDOFF](../HANDOFF.md), [RL manifest](../reports/rl-smoke/README.md) | [gym_env.py](../src/wildfire_rl/gym_env.py), [train.py](../src/wildfire_rl/train.py), [testovi](../tests/test_gym_env.py) |
| Firehose adapteru TASK-004c/017 | [runtime nalaz](../docs/research/FIREHOSE_VERIFICATION.md), [Docker runbook](../docker/firehose/README.md) | [firehose_probe.py](../src/wildfire_rl/firehose_probe.py), [initial-state patch](../docker/firehose/cfsds_initial_state.patch), [fixture check](../docker/firehose/verify_initial_state.py), [Dockerfile](../docker/firehose/Dockerfile); state importer je implementiran, cumulative-damage/terminal-reason dio još nije dovršen |
| Porijeklu težina i inputa | [data pravila](../data/README.md), [audit modela](../docs/research/checkpoint-audit.json) | [upstream manifest](../data/manifests/upstream.json), [ZIP audit bez deserializacije](../src/wildfire_rl/checkpoint_audit.py), [input inventar](../scripts/inventory_firehose_dataset.py) |
| Bazi znanja/novom handoffu | [pravila održavanja](maintenance.md), [OKF profil](okf-format.md) | [AGENTS](../AGENTS.md), [glavni indeks](../index.md), [validator](../scripts/validate_knowledge.py), [CI](../.github/workflows/tests.yml) |
| Posteru i predaji | [rubrika](../docs/research/REQUIREMENTS_AND_RUBRIC.md), [isporuke](../reports/DELIVERABLES.md) | [istraživački rezultati](../reports/index.md), [kriteriji prihvata](../docs/specs/ACCEPTANCE_CRITERIA.md); glavni rezultati još nisu ostvareni |

## Pokretanje i environment

[HANDOFF](../HANDOFF.md) je kanonski prenosivi setup. Osnovni paket traži Python >=3.11,
bez dodatnih biblioteka. Iz repo roota:

```sh
python3 -m venv .venv
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m wildfire_rl.cli --config configs/smoke.json --out runs/NEW_ID
```

Optional moderni RL koristi `pip install -e '.[rl]'`, s vlastitim snapshotom verzija.
Legacy Firehose koristi Docker/Python 3.8 i pinovane izvore, odvojeno od modernog .venv.
Nije potvrđen build na svakoj arhitekturi/Colabu. Lokalni Docker tag i prethodni .venv
ne prenose se Git klonom; javne komande, verzije i dokazi se prenose.

## Granica samostalnosti repozitorija

Sav javni kontekst, kod, konfiguracije i mali dokazi su u repou. Veliki/raw artefakti,
treći checkouti, težine i privatni originali su izvan bundlea. [HANDOFF](../HANDOFF.md)
i manifesti daju javne izvore i očekivane hashove; privatna prepiska nije preduslov
za setup. Postojeći run folder se ne prepisuje: biraj nov ID.
