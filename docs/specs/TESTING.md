---
type: Specification
title: Verifikacija
status: draft
---
# Verifikacija

Core: `PYTHONPATH=src python3 -m unittest discover -s tests -v`.
Optional testovi se stvarno izvršavaju tek sa `.[rl]`; skips nisu dokaz RL kompatibilnosti.
Testovi pokrivaju sinhrono širenje, trajni damage, budžet/no-op, maske, nonfuel,
horizont, priority reward, replay, RNG izolaciju, baseline validnost, ručne male
rezultate, duplikate/pairing, config validaciju i zabranu prepisivanja.
RL: Gym checker, seed reset, invalid action no-op i kratko MaskablePPO learn/save/load.
Checkpoint audit: JSON može sadržati nevažeći serialized pickle i ipak se ne izvršava.

Smoke: config smoke; pilot: 300 epizoda. Replay poredi sve epizodne vrijednosti osim
runtime_seconds; manifest timestamp/platform nisu bit-po-bit deterministični.
Prije glavne evaluacije: C2F integracijski test, first observation, simulator seed,
timeout/cleanup, frozen inference i višeseed fine-tuning kontrole.

Sadašnji testovi ne potvrđuju fiziku požara, poboljšanje RL-a, stabilnost C++ integracije
ili generalizaciju. Nema coverage cilja koji zamjenjuje testove važnih pravila.
Open Questions: vremenski cap i tolerancije determinističnosti izabranog backenda.
