---
type: Playbook
title: Gdje pronaći kod, podatke i način rada
description: Rutiranje istraživačkih i tehničkih zadataka na kanonske fajlove i komande.
status: stable
generated: {by: "process:codex", at: "2026-10-28T12:55:34Z"}
sources:
  - resource: /src/wildfire_rl/simulator.py
  - resource: /src/wildfire_rl/evaluation.py
  - resource: /src/wildfire_rl/firehose_probe.py
  - resource: /HANDOFF.md
---
# Mapa projekta i radnih zadataka

| Ako radiš na… | Prvo pročitaj | Kod/dokazi i provjera |
| --- | --- | --- |
| Dataset refinementu TASK-012 | [DATASET](../docs/research/DATASET.md), [stvarni požari i otvorene odluke](../docs/research/REAL_FIRE_DATASETS.md), [protokol](../docs/research/PROTOCOL.md) | [manifest kandidata](../data/manifests/real-fire-candidates.json), [profili/hashovi](../reports/real-fire-data/index.md), [offline kontrola uzoraka](../scripts/profile_real_fire_samples.py) |
| Sintetičkoj dinamici, budžetu i šteti | [pravila](../docs/specs/BUSINESS_RULES.md), [domain](../docs/specs/DOMAIN.md) | [simulator.py](../src/wildfire_rl/simulator.py): Scenario/GridFire; [testovi](../tests/test_simulator.py) |
| Politikama i paired evaluaciji | [protokol](../docs/research/PROTOCOL.md), [pilot](../reports/pilot/README.md) | [policies.py](../src/wildfire_rl/policies.py), [evaluation.py](../src/wildfire_rl/evaluation.py), [CLI](../src/wildfire_rl/cli.py), [testovi](../tests/test_evaluation.py) |
| Modernom Gym/PPO smokeu | [HANDOFF](../HANDOFF.md), [RL manifest](../reports/rl-smoke/README.md) | [gym_env.py](../src/wildfire_rl/gym_env.py), [train.py](../src/wildfire_rl/train.py), [testovi](../tests/test_gym_env.py) |
| Firehose adapteru TASK-004c | [runtime nalaz](../docs/research/FIREHOSE_VERIFICATION.md), [Docker runbook](../docker/firehose/README.md) | [firehose_probe.py](../src/wildfire_rl/firehose_probe.py), [helper testovi](../tests/test_firehose_probe.py), [Dockerfile](../docker/firehose/Dockerfile), [batch](../docker/firehose/verify_batch.py); konačni adapter još nije implementiran |
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
