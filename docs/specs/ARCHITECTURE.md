# Arhitektura

Sada: `Scenario -> GridFire -> policies/evaluation -> CSV + manifest + SVG`.
Optional: `GridFireEnv -> MaskablePPO -> lokalni ZIP + training_manifest.json`.
`checkpoint_audit` čita isključivo JSON metadata provjerenih upstream ZIP fajlova.

`simulator.py`: dinamika i računovodstvo. `policies.py`: kontrolne heuristike.
`evaluation.py`: config validacija, uparivanje, bootstrap, provenance i izvještaj.
`gym_env.py`: Gym API i budžetsko opažanje. `train.py`: ograničeni CPU smoke.
`cli.py`: thin CLI. Nema web servera, baze, dockera ili cloud infrastrukture za core.

Plan: adapter za izabrani realističniji simulator tek nakon gatea. Ne praviti generički
plugin framework dok nemamo dva stvarna backenda. Firehose zavisnosti ostaju izolovane.
20×20 CNN težine se ne mogu pretpostavljeno prenijeti na novi Dict/MLP prostor.
Open Questions: legacy reprodukcija vs migracija na moderni SB3; status u ADR-002.
