---
type: Experiment Report
title: Izvršena Firehose provjera
---
# Izvršena Firehose provjera

`verification.json`: 12/12 uspješnih rollouta, replay/seed/budget/weights checks.
`summary.csv` i `summary.json`: mali rezultati. `probes/*.json`: akcije, state hashovi,
input/checkpoint/weight hashovi i detalji svakog izvršavanja.
`dataset-inventory.json`: 141 input fajl i provenance hashovi.
`environment.json`, `environment-freeze.txt`: tačan runtime identitet/verzije.

Nakon dodavanja CFSDS ulaza i početnog multi-cell stanja ponovljeno je 12 kratkih
Sub20 inference slučajeva na novom Docker imageu; svih 12 je prošlo, C++ return code je
0, a postojeće PPO težine ostale su nepromijenjene. Sažeti receipt je
[`real-case-image-regression.json`](real-case-image-regression.json); sirovi run logovi
ostaju lokalno pod `runs/firehose-final-check/`.

Ovo dokazuje izvršavanje, bez treniranja. Ne predstavlja glavnu evaluaciju RL kvaliteta.
Runtime gate je prošao; research_ready je false zbog dokumentovanih wrapper/termination
ograničenja. Nalazi i interpretacija su u docs/research/FIREHOSE_VERIFICATION.md.
