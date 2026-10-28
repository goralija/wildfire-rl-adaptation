# Nastavak rada bez chat historije

Za drugi računar ili novog saradnika prvo pročitaj [HANDOFF](../HANDOFF.md):
clone grana, minimalni setup i pribavljanje lokalno ignorisanih izvora/podataka.
Lokalne putanje ispod su samo historija Harunovog računara, nisu prenosivi setup.

1. Iz ovog repozitorija pročitaj STATUS, DECISION_RECORDS, SIMULATOR_AUDIT i PROTOCOL.
2. `git status --short --branch`; provjeri da si u ispravnom task worktreeu.
3. `PYTHONPATH=src python3 -m unittest discover -s tests -v`.
4. `PYTHONPATH=src python3 -m wildfire_rl.cli --config configs/smoke.json --out runs/NEW_ID`.
5. Pročitaj `docs/research/FIREHOSE_VERIFICATION.md` i `docs/research/DATASET.md`.
   Runtime je već ostvaren: ne počinjati ponovo od instalacije ili traženja modela.
6. Počni TASK-012 — dataset refinement: pročitaj REAL_FIRE_DATASETS i DATASET.
   Razdvoji simulator inpute, RL iskustvo i historijske reference; pripremi prijedlog
   izbora/obima, model/scenario veze, splitova, metrika i nedostajućih inputa.
   Označi otvorene odluke: Dogrib/CFSDS nisu konačno usaglašen izbor ili test skup.
7. Nakon usaglašavanja obima slijedi TASK-004c: formalni Firehose adapter za stvarni warmup observation,
   kumulativnu štetu, maske/budžet i C++ termination reason / active-vs-burnt export.
   Sačuvaj RGB 3×20×20 i Discrete(400) checkpoint kontrakt; forced no-op ostaje izvan glave.
8. Dodaj integracijske regresijske testove za 206/207 brojač, identične kontrole,
   timeout/cleanup i razliku weather-horizon/containment. Tek potom dataset split i fine-tuning.
9. Za ponavljanje postojećeg testa koristi `docker/firehose/README.md`; lokalni image
   je `wildfire-firehose-probe:20261028`, rezultati u `runs/firehose-verification-final/`.
10. Za historijske reference pročitaj `docs/research/REAL_FIRE_DATASETS.md` i TASK-011.
   Dogrib/CFSDS mali uzorci su već lokalno preuzeti. Ne preuzimati gigabajte niti
   proglašavati Dogrib nezavisnim testom: dijeli teren s Firehose Sub20. Raw ulazi
   i opaženi ishodi su odvojeni; fizička validacija još nije izvršena.

## Lokalne lokacije ove sesije
- Workspace: `/Users/harungoralija/Desktop/mpvi` (ulazni START_HERE.md).
- Primary clone: `/Users/harungoralija/Desktop/mpvi/repository` (lokalni main base).
- Ovaj worktree: `/Users/harungoralija/Desktop/mpvi/worktrees/project-bootstrap`.
- Branch: `feature/project-bootstrap`.
- `.venv`: optional moderni RL environment. `external/firehose`: pinovani izvor i ZIP-ovi.
- `private/`: originalni korisnički materijali, ignorisani u Gitu; ne objavljivati.
- Bundle backup je u workspace `backups/`, kreira se po završetku.

## Spreman prompt za nastavak

"Nastavi wildfire-rl-adaptation od TASK-012 — dataset refinement. Pročitaj HANDOFF,
STATUS, DATASET, REAL_FIRE_DATASETS i PROTOCOL. Imamo pregled kandidata i male uzorke,
ali izbor, uloga i obim nisu usaglašeni. Pripremi prijedlog izvora/podskupa, veze s
20×20 modelom, scenarija/splitova, metrika i granica zaključaka. Odvoji preporuke
od odluka. Runtime već radi; TASK-004c slijedi nakon refinementa u usaglašenom obimu.
Ne pokreći dugo treniranje, velika preuzimanja ili remote objavu bez naloga."
