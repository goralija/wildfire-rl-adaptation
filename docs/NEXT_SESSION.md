# Nastavak rada bez chat historije

1. Iz ovog repozitorija pročitaj STATUS, DECISION_RECORDS, SIMULATOR_AUDIT i PROTOCOL.
2. `git status --short --branch`; provjeri da si u ispravnom task worktreeu.
3. `PYTHONPATH=src python3 -m unittest discover -s tests -v`.
4. `PYTHONPATH=src python3 -m wildfire_rl.cli --config configs/smoke.json --out runs/NEW_ID`.
5. Počni TASK-004 prema `docs/research/SIMULATOR_AUDIT.md`: odvojeni Linux legacy
   environment, pinned Firehose commit, C++ build, simulator seed, no-op i prvo opažanje,
   pa checkpoint inference. Timebox 4 aktivna sata; sačuvaj komande i logove.
6. Ako gate padne, dokumentuj prepreku i napravi SimFire spike; ne prepravljaj zaključak
   o pretrained agentu ako si ustvari trenirao novi model.
7. Nakon gatea freeze test manifest, runtime procjena, frozen baseline, pa tek fine-tuning.

## Lokalne lokacije ove sesije
- Workspace: `/Users/harungoralija/Desktop/mpvi` (ulazni START_HERE.md).
- Primary clone: `/Users/harungoralija/Desktop/mpvi/repository` (lokalni main base).
- Ovaj worktree: `/Users/harungoralija/Desktop/mpvi/worktrees/project-bootstrap`.
- Branch: `feature/project-bootstrap`.
- `.venv`: optional moderni RL environment. `external/firehose`: pinovani izvor i ZIP-ovi.
- `private/`: originalni korisnički materijali, ignorisani u Gitu; ne objavljivati.
- Bundle backup je u workspace `backups/`, kreira se po završetku.

## Spreman prompt za nastavak

"Nastavi wildfire-rl-adaptation od TASK-004. Pročitaj AGENTS.md, STATUS.md,
NEXT_SESSION.md, PROTOCOL.md i SIMULATOR_AUDIT.md. Provjeri postojeće testove.
Izvedi ograničeni Firehose feasibility gate; nemoj pokretati veliku training matricu,
objavljivati privatni materijal ili tretirati synthetic pilot kao glavni rezultat."
