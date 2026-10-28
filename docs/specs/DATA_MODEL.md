---
type: Specification
title: Podaci i artefakti
status: draft
---
# Podaci i artefakti

Scenario JSON: rows, cols, ignition[], nonfuel[], priority[], spread_probability,
burn_duration, warmup_steps, horizon. Cell ID je nulti row-major indeks.
Config v1: schema_version, label, backend, scenario, budgets[], seeds[], policies[].
Epizoda: backend, scenario_sha256, budget, seed, policy, burned_cells/fraction,
priority_burned_cells/fraction, interventions, steps, terminated, truncated, runtime_seconds.
Summary: policy/B, n, srednja šteta i 95% interval, priority srednja šteta,
uparena spašena frakcija i interval, intervencije, truncation rate i runtime.
Manifest: config, config SHA256, source SHA256, Git commit/dirty, Python, platforma i UTC.
Model manifest: training seedovi, scenario, B, steps, package versions i SHA256 težina.

Nema baze ili migracija. schema_version promijeniti kada se mijenja kontrakt,
ne tiho reinterpretirati stare CSV-ove. Run je append-only direktorij.
Source hash pokriva `src/wildfire_rl/*.py`; config hash pokriva cijeli JSON.
Open Questions: glavni scenario manifest za weather i georeferencirane rastere.
