# synthetic

## Dokumenti

- [Sintetičko CA okruženje — trening i jednokratni test](README.md) - Historijski policy-v1 izvještaj, poništen ADR-029.

## Aktivni CA pilot v2 (2026-11-21)

- [Ljudski izvještaj](../../docs/research/CA_CONTROLLED_PILOT.md) — TASK-035/ADR-040.
- [Svih240 development ishoda](ca-controlled-development-v2.json), [grafikon](ca-controlled-development-v2.png).
- [Identičan tehnički replay15 epizoda](ca-controlled-replay-v2.json).
- [Testovi, hashovi i lokalni logovi](ca-controlled-verification-v2.json).

## CA v2 učenje (2026-11-21)

- [Ljudski izvještaj](../../docs/research/CA_LEARNING_PILOT.md) - TASK-038/ADR-042, bez RL prednosti.
- [Svih288 razvojnih putanja i svi modeli](ca-learning-development-v1.json) - [grafikon](ca-learning-development-v1.png).
- [Tehničke provjere](ca-learning-verification-v1.json) - hashovi, testovi i rekalkulacija; [restore18/18](ca-learning-restore-v1.json).
- [Lokalni paket modela/demonstracija](ca-learning-artifacts-v1.json) - source/weights manifest, nije uploadovan.

## Upareni SimFire/CA pilot (2026-11-21)

- [Ljudski izvještaj](../../docs/research/CA_SIMFIRE_PAIRED.md) - TASK-040 faza A / ADR-044, nije native PPO rangiranje.
- [Svi primarni i robustness ishodi](ca-simfire-paired-v1.json) - [sve3 replike, sekundarni sažetak](ca-simfire-paired-replicates-v1.json), [grafikon](ca-simfire-paired-v1.png).
- [Tehničke provjere i hashovi](ca-simfire-paired-verification-v1.json) - 369 testova, native replay i mask-score audit.
- [Lokalni paket](ca-simfire-paired-artifacts-v1.json) - nije uploadovan; [raspakovani replay33/33](ca-simfire-paired-restore-v1.json).
