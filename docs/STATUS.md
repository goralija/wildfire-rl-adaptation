# Trenutno stanje — 2026-10-28

## Radi
- Trajna baza znanja, profesorovi zahtjevi i bodovanje, spec suite, protokol i odluke.
- Synthetic-v1, pet baseline politika, budžeti/no-op, kumulativna i prioritetna šteta.
- Uparene epizode, 95% seed bootstrap intervali, config/source/Git/environment manifest.
- Optional Gymnasium i kratko MaskablePPO train/save/load na CPU-u.
- Statički Firehose audit i metadata dva postojeća 20×20 checkpointa bez deserializacije.

## Ne tvrditi
Cell2Fire nije kompajliran. Firehose checkpointi nisu izvršeni. Nema pretrained
fine-tuninga, glavnih RL poređenja ili potvrde fizikalnog realizma/operativne upotrebe.
Synthetic baseline rezultati ne potvrđuju hipotezu o RL adaptaciji.

## Dokazi i nastavak
- `.venv/bin/python -m unittest discover -s tests -v`: 22 testa, svi prolaze,
  uključujući 4 optional Gym/RL testa; provjereno i nezavisnim reviewerom.
- Čisti Python environment: 18 core testova prolazi, 4 RL testa očekivano preskočena;
  smoke CLI se izvršava bez instalacije biblioteka.
- Dvije izvedbe 300-epizodnog pilota: identične epizodne metrike osim vremena;
  nijedna epizoda nije truncated na horizontu 240.
- Novi MaskablePPO: 1,024 CPU koraka, save/load i masked rollout izvršeni.
- `pip check`: nema neusklađenih zavisnosti. Lokalni Markdown linkovi postoje.
- Pilot SVG renderovan i vizuelno pregledan; CI je pripremljen, nije izvršen na GitHubu.
- Primjeri i provenance: `reports/pilot/`, `reports/rl-smoke/`.

Sljedeće: TASK-004, simulator feasibility gate.
Deadline, compute i licence ostaju otvoreni. Sve izmjene su lokalne, remote nije mijenjan.

## Pregled i preostala sitnica
Nezavisan review: bez kritičnih ili važnih nalaza. Jedan minor odgođen: JSON `null`
config daje traceback umjesto uredne poruke; TASK-010, detalji u `docs/REVIEW.md`.
