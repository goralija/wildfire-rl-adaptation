---
type: Specification
title: Environment i runbook
status: draft
---
# Environment i runbook

Core: Python >=3.11; bez pip biblioteka, `PYTHONPATH=src` za sve komande.
Optional modern RL: `python -m pip install -e '.[rl]'`; verified snapshots su u
`requirements/rl-macos-py312.freeze.txt` (Python 3.12/macOS ARM64) i
`requirements/rl-macos-py313.freeze.txt` (Python 3.13/macOS ARM64). Oba su lokalni
snapshoti platforme, ne obećanje kompatibilnosti na Colab/Linux GPU-u. Za Colab ponovo
razriješiti podržane verzije i sačuvati zaseban freeze i manifest.

Za najnoviji čisti lokalni dokaz vidi [environment setup receipt](../../reports/environment-setup/README.md):
Python 3.12.4, 26 app testova, 15 knowledge testova, strict bundle provjera i oba smokea
su prošla. Taj worktree `.venv`, external izvori, weights i Docker tag ostaju lokalni.

Run: `python -m wildfire_rl.cli --config configs/pilot.json --out runs/NEW_ID`.
Output postoji -> izaberi novi ID, nemoj brisati ili koristiti overwrite flag.
Bez optional paketa unittest preskače RL testove; core testovi moraju proći.
Ako subprocess C2F stane: timeout, returncode, stderr i input hash su obavezni u budućem
adapteru; ne tretirati puknut proces kao uspješno završenu epizodu.

Oporavak: Git branch + lokalni bundle; environment se ponovo kreira iz izvora/requirements.
Provjeri source hash za tačan replay; runtime i created_utc se prirodno razlikuju.
Privatni originali i lokalni modeli nisu u bundleu. Privatni originali nisu preduslov
za tehnički nastavak; javni sažetak i manifesti čuvaju potreban kontekst. Za modele
i raw podatke koristiti pinovane javne izvore iz HANDOFF-a, ne tuđu lokalnu putanju.
Open Questions: udaljena pohrana velikih artefakata i timski compute.

Legacy runtime je sada ostvaren preko `docker/firehose/Dockerfile`: pinned Python base,
SB3/contrib 1.5.0, Gym 0.21, C++ build flag overrides. Stvarni build i 12-case replay
su ponovljeni na Linux ARM64; tačan ID je u [environment receipt](../../reports/environment-setup/manifest.json),
raniji pinovani runtime manifest je u reports/firehose-verification/. Runtime bez mreže
i sa output-only host mountom. Rebuild drugih platformi još nije potvrđen.
