# Stvarni požari: pregled kandidata i mali uzorci

Prikladnost izvora za naš projekat, ne rezultat fizičke validacije simulatora.
Primarni nalazi i preporuka: docs/research/REAL_FIRE_DATASETS.md.
Candidate manifest: data/manifests/real-fire-candidates.json.

Dogrib uzorak: 16 fajlova / 3,390,138 bajtova, lokalno u data/raw/dogrib-reference/.
CFSDS uzorak: dva ZIP-a za 2020 / 293,731 bajt, data/raw/cfsds-sample-2020/.
Raw podaci ostaju ignorisani. Ovdje su samo porijeklo/hashovi i mali profili.
Dogrib profile poredi stvarni mask, simulator reference i Firehose mapu; CFSDS
profile provjerava 38 rastera i 372 dnevna reda. Ovo nije provjera cijelog CFSDS-a.

sample-checks.txt je stvarni stdout offline ponavljanja: svih 18 preuzetih fajlova
ima zabilježenu veličinu/SHA256, Dogrib overlap i CFSDS ID/pixel-scale provjere prolaze.
Komanda iz repo roota: python3 scripts/profile_real_fire_samples.py.
Izvršeno Python 3.12.14 / NumPy 2.3.5 / Pillow 12.3.0 (postojeći bundled runtime).
Candidate manifest ne znači da je svaki kandidat preuzet: WildfireSpreadTS i BurnMD
su pregledani samo na nivou javnih metapodataka.
