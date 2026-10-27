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
Testovi i primjeri rezultata su u `reports/` i experiment logu; konačna verifikacija
se bilježi u ovom dokumentu nakon pregleda. Sljedeće: TASK-004, simulator feasibility gate.
Deadline, compute i licence ostaju otvoreni. Sve izmjene su lokalne, remote nije mijenjan.
