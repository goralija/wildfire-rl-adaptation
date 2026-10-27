# Environment i runbook

Core: Python >=3.11; bez pip biblioteka, `PYTHONPATH=src` za sve komande.
Referentni lokalni environment: Python 3.13 `.venv` u task worktreeu.
Optional RL: `python -m pip install -e '.[rl]'`; snapshot tačnih verzija je u requirements/.
Snapshot sa macOS ARM64 nije obećanje kompatibilnosti na Colab Linux GPU-u.
Za Colab ponovo razriješiti podržane verzije i sačuvati zaseban freeze i manifest.

Run: `python -m wildfire_rl.cli --config configs/pilot.json --out runs/NEW_ID`.
Output postoji -> izaberi novi ID, nemoj brisati ili koristiti overwrite flag.
Bez optional paketa unittest preskače RL testove; core testovi moraju proći.
Ako subprocess C2F stane: timeout, returncode, stderr i input hash su obavezni u budućem
adapteru; ne tretirati puknut proces kao uspješno završenu epizodu.

Oporavak: Git branch + lokalni bundle; environment se ponovo kreira iz izvora/requirements.
Provjeri source hash za tačan replay; runtime i created_utc se prirodno razlikuju.
Originalni privatni attachmenti i lokalni modeli nisu u bundleu; zasebna lokalna kopija
je dostupna dok ovaj worktree ostaje sačuvan.
Open Questions: udaljena pohrana velikih artefakata i timski compute.
