# Nastavak rada bez chat historije

1. Iz ovog repozitorija pročitaj STATUS, DECISION_RECORDS, SIMULATOR_AUDIT i PROTOCOL.
2. `git status --short --branch`; provjeri da si u ispravnom task worktreeu.
3. `PYTHONPATH=src python3 -m unittest discover -s tests -v`.
4. `PYTHONPATH=src python3 -m wildfire_rl.cli --config configs/smoke.json --out runs/NEW_ID`.
5. Pročitaj `docs/research/FIREHOSE_VERIFICATION.md` i `docs/research/DATASET.md`.
   Runtime je već ostvaren: ne počinjati ponovo od instalacije ili traženja modela.
6. Počni TASK-004c: formalni Firehose adapter za stvarni warmup observation,
   kumulativnu štetu, maske/budžet i C++ termination reason / active-vs-burnt export.
   Sačuvaj RGB 3×20×20 i Discrete(400) checkpoint kontrakt; forced no-op ostaje izvan glave.
7. Dodaj integracijske regresijske testove za 206/207 brojač, identične kontrole,
   timeout/cleanup i razliku weather-horizon/containment. Tek potom dataset split i fine-tuning.
8. Za ponavljanje postojećeg testa koristi `docker/firehose/README.md`; lokalni image
   je `wildfire-firehose-probe:20261028`, rezultati u `runs/firehose-verification-final/`.

## Lokalne lokacije ove sesije
- Workspace: `/Users/harungoralija/Desktop/mpvi` (ulazni START_HERE.md).
- Primary clone: `/Users/harungoralija/Desktop/mpvi/repository` (lokalni main base).
- Ovaj worktree: `/Users/harungoralija/Desktop/mpvi/worktrees/project-bootstrap`.
- Branch: `feature/project-bootstrap`.
- `.venv`: optional moderni RL environment. `external/firehose`: pinovani izvor i ZIP-ovi.
- `private/`: originalni korisnički materijali, ignorisani u Gitu; ne objavljivati.
- Bundle backup je u workspace `backups/`, kreira se po završetku.

## Spreman prompt za nastavak

"Nastavi wildfire-rl-adaptation od TASK-004c. Prvo pročitaj STATUS, NEXT_SESSION,
FIREHOSE_VERIFICATION i DATASET. Cell2Fire build i oba postojeća modela već rade u
izolovanom Docker imageu; ne ponavljaj setup bez razloga. Implementiraj i testiraj
observation/damage/termination adapter uz očuvanje checkpoint kontrakta. Ne pokreći
veliko treniranje ili remote objavu bez naloga."
