---
type: Playbook
title: Gdje pronaći kod, podatke i način rada
description: Rutiranje istraživačkih i tehničkih zadataka na kanonske fajlove i komande.
status: stable
generated: {by: "process:codex", at: "2026-10-31T09:28:36Z"}
sources:
  - resource: /src/wildfire_rl/simulator.py
  - resource: /src/wildfire_rl/evaluation.py
  - resource: /src/wildfire_rl/firehose_probe.py
  - resource: /HANDOFF.md
---
# Mapa projekta i radnih zadataka

| Ako radiš na… | Prvo pročitaj | Kod/dokazi i provjera |
| --- | --- | --- |
| CFSDS cohort/replay TASK-015/016/018 | [pipeline](../docs/research/REAL_CASE_PIPELINE.md), [dataset pregled](../docs/research/REAL_FIRE_DATASETS.md), [train fuel audit](../docs/research/CFSDS_TRAIN_QC.md), [train input audit](../docs/research/CFSDS_TRAIN_INPUT_QC.md), [no-action dijagnostika](../docs/research/CFSDS_NO_ACTION_DIAGNOSIS.md) | [cohort manifest](../data/manifests/cfsds-v1_1-pilot-cohort.json), [fuel QC code](../scripts/audit_cfsds_train_fuel.py), [input QC code](../scripts/audit_cfsds_train_case_inputs.py), [case builder](../scripts/build_cfsds_case.py), [replay metrics](../scripts/evaluate_cfsds_replay.py), [timeline analysis](../scripts/analyze_cfsds_replay_timeline.py), [reports](../reports/real-fire-data/index.md) |
| TASK-015 fuel-vintage proof | [input QC decision](../docs/research/CFSDS_TRAIN_INPUT_QC.md), [ADR-020](../docs/specs/DECISION_RECORDS.md#adr-020), [ADR-025](../docs/specs/DECISION_RECORDS.md#adr-025) | [temporal mask helper](../scripts/cfsds_fuel_vintage.py), [TRAIN proof CLI](../scripts/prove_cfsds_train_fuel_vintage.py), [mask receipt](../reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json), [NF-scar C++ fixture](../docker/firehose/verify_nonfuel_initial_scar.py), [contract receipt](../reports/firehose-verification/nonfuel-initial-scar-contract.json); annual map remains blocked |
| TASK-015 fuel-source/vintage review | [fuel-vintage decision review](../docs/research/CFSDS_FUEL_VINTAGE_REVIEW.md), [input QC](../docs/research/CFSDS_TRAIN_INPUT_QC.md), [ADR-027](../docs/specs/DECISION_RECORDS.md#adr-027) | [source register S-031–S-044](../docs/research/SOURCES.md); W.I.S.E. Figure 2 transcribed, v2014b cutoff unresolved; [BC perimeter crosswalk](../reports/real-fire-data/cfsds-train-bc-perimeter-crosswalk.json) provides three candidate incident IDs but no suppression action data |
| TASK-015 target-blind initial state | [input QC](../docs/research/CFSDS_TRAIN_INPUT_QC.md), [ADR-021](../docs/specs/DECISION_RECORDS.md#adr-021) | [crop/front helper](../scripts/cfsds_initial_state.py), [builder](../scripts/build_cfsds_case.py), [train screen](../scripts/profile_cfsds_cohort.py), [invariance proof](../scripts/prove_cfsds_target_blind_input.py), [tests](../tests/test_cfsds_initial_state.py), [receipts](../reports/real-fire-data/index.md); 25-pair shortlist is not a full day-pair cohort |
| TASK-015 target-blind spatial feasibility | [bounded 25-pair report](../docs/research/CFSDS_SPATIAL_FEASIBILITY.md), [full 1301-pair report](../docs/research/CFSDS_FULL_DAY_PAIR_SCREEN.md), [ADR-023](../docs/specs/DECISION_RECORDS.md#adr-023) | [full screen CLI](../scripts/audit_cfsds_train_full_day_pairs.py), [domain helper](../scripts/cfsds_spatial_feasibility.py), [JSON receipt](../reports/real-fire-data/cfsds-train-full-day-pair-screen.json), [per-case CSV](../reports/real-fire-data/cfsds-train-full-day-pair-screen.csv); no FireCase/replay |
| Sintetičkoj dinamici, budžetu i šteti | [pravila](../docs/specs/BUSINESS_RULES.md), [domain](../docs/specs/DOMAIN.md) | [simulator.py](../src/wildfire_rl/simulator.py): Scenario/GridFire; [testovi](../tests/test_simulator.py) |
| Politikama i paired evaluaciji | [protokol](../docs/research/PROTOCOL.md), [pilot](../reports/pilot/README.md) | [policies.py](../src/wildfire_rl/policies.py), [evaluation.py](../src/wildfire_rl/evaluation.py), [CLI](../src/wildfire_rl/cli.py), [testovi](../tests/test_evaluation.py) |
| Modernom Gym/PPO smokeu | [HANDOFF](../HANDOFF.md), [RL manifest](../reports/rl-smoke/README.md) | [gym_env.py](../src/wildfire_rl/gym_env.py), [train.py](../src/wildfire_rl/train.py), [testovi](../tests/test_gym_env.py) |
| Firehose adapter TASK-004c/017 | [runtime nalaz](../docs/research/FIREHOSE_VERIFICATION.md), [Docker runbook](../docker/firehose/README.md), [adapter receipt](../reports/firehose-verification/task004c-adapter-smoke.json) | [firehose_probe.py](../src/wildfire_rl/firehose_probe.py), [initial-state patch](../docker/firehose/cfsds_initial_state.patch), [state/terminal patch](../docker/firehose/task004c_state_export.patch), [fixture check](../docker/firehose/verify_initial_state.py), [Dockerfile](../docker/firehose/Dockerfile); adapter je završen, CFSDS no-action quality gate ostaje otvoren |
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
