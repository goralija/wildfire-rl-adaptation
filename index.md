---
okf_version: "0.2"
---
# Wildfire RL adaptation — baza znanja

## Počni ovdje

- [Najnovije: centrirana PPO nagrada](docs/research/CENTERED_PPO_PILOT.md) - TASK-045/ADR-056 završen, oba continuation kriterija false; svi seedovi i nezavisni audit.


- [Najnovije: PPO signal i reference](docs/research/PPO_SIGNAL_DIAGNOSIS.md) - TASK-044/ADR-054 završen: uniformni referenti, početni gradient coupling i smjer za kontrolisani pilot.


- [Najnovije: upareni PPO learning](docs/research/PAIRED_PPO_LEARNING.md) - TASK-043/ADR-052 završen, oba learning kriterija false; svi seedovi i puni audit/restore.


- [Najnovije: zajednički PPO ugovor](docs/research/COMMON_PPO_INTERFACE.md) - TASK-040 B.1/ADR-050 završen, isti input/charged reward,4×64koraka i replay/restore PASS.


- [Najnovije: prošireni audit opaženog rasta](docs/research/EXPANDED_OBSERVED_GROWTH.md) - TASK-042/ADR-048 završen na61TRAIN, grupe nerasta i jasne granice; sljedeći prijedlog TASK-040 B.1.

- [Najnovije: rast prema opaženom FEDS-u](docs/research/PAIRED_OBSERVED_GROWTH.md) - TASK-041/ADR-046 završen: CA bliži opaženom razmjeru, spatial neizvjesnost; TASK-042 je sljedeći prijedlog.

- [Najnovije: upareno SimFire/CA poređenje](docs/research/CA_SIMFIRE_PAIRED.md) - TASK-040 faza A/ADR-044 završena, mješoviti procentni rezultati; TASK-041 growth audit je sljedeći prijedlog.

- [Završeno: CA v2 BC/PPO](docs/research/CA_LEARNING_PILOT.md) — TASK-038/ADR-042 završen, šest modela bez prolaza; sljedeći prijedlog TASK-039.

- [Prethodni kontrolisani CA pilot](docs/research/CA_CONTROLLED_PILOT.md) — TASK-035/ADR-040 završen:240 epizoda, sljedeći TASK-038.

- [Najnovije: popravljeno SimFire opažanje](docs/research/SIMFIRE_OBSERVATION_REPAIR.md) - TASK-036 fazaA/ADR-038, stvarni popravak, jača heuristika i nesiguran TRAIN dobitak.

- [Prethodni TASK-034: SimFire pregled](docs/research/SIMFIRE_OBSERVATION_AUDIT.md) - Završen audit i preporuka kontrolisanog CA pilota, ADR-036; preostali SimFire v2 put je eksplicitan.

- [Prethodni nastavak: SimFire B=1](docs/research/SIMFIRE_B1_EXPLORATION.md) - TASK-028–030 završeni: 98×33 ishoda, osam LOO metoda bez prolaza praga, ADR-034; predložen TASK-034.

- [Projekt i pokretanje](README.md) - Cilj istraživanja i minimalni setup.
- [Sažeti projektni kontekst](knowledge/project-context.md) - Aktivni SimFire/FEDS pravac i crosswalk gate.
- [Handoff za kolegu](HANDOFF.md) - Prenosiv nastavak bez chat historije.
- [Trenutno stanje](docs/STATUS.md) - Šta radi, dokazi i ograničenja.
- [Naredna sesija](docs/NEXT_SESSION.md) - Ispravke nakon revizije (ADR-029) i redoslijed nastavka.
- [Prioriteti i prihvat](docs/BACKLOG.md) - Dataset refinement prvi; adapter je tehnički nastavak.

## Pronađi detalje i dokaze

- [Kontekst i pravila održavanja](knowledge/index.md) - Mapa koda/zadataka, OKF profil i održavanje.
- [Dokumenti projekta](docs/index.md) - Protokol, zahtjevi, specifikacije, odluke i historija.
- [Podaci](data/index.md) - Porijeklo, FPA-FOD/FEDS kohorta i historijski CFSDS nalazi.
- [Real-case pipeline](docs/research/REAL_CASE_PIPELINE.md) - Jednostavan opis šta stvarni podaci daju (Y), šta simulator prima (X), te jaz početnog fronta.
- [FPA-FOD/FEDS crosswalk i data gate](docs/research/FPA_FEDS_CROSSWALK.md) - Aktivni SimFire benchmark pravac, pokrivenost i stop-uslov.
- [SimFire/FEDS runtime i trening](docs/research/SIMFIRE_ENVIRONMENT.md) - pinovani Python 3.9 runtime, TRAIN-only PPO putanja i no-op gate status.
- [SimFire TRAIN growth gate](reports/real-fire-data/feds-simfire-train-growth-gate-v1.json) - 98 TRAIN požara na ispravljenim ulazima; gate PASS, zamrznut WAF 0.10 / ROS 1.0 (ADR-031); nije fizička validacija.
- [SimFire benchmark i studija budžeta](reports/real-fire-data/feds-simfire-budget-benchmark-adr030-v1.json) - 10 seedova na zamrznutom zapisu; nijedan od šest primarnih testova ne odbacuje, PPO se ne razlikuje od jednostavnih pravila (ADR-032); simulatorski rezultat.
- [SimFire TRAIN no-op screen](reports/real-fire-data/feds-simfire-train-noop-screen-v1.json) - 99 TRAIN požara; rezultat nevažeći zbog gridMET greške (ADR-029), zamijenjen growth gateom.
- [Izvještaji](reports/index.md) - Sintetički pilot, runtime dokazi, FEDS crosswalk i historijski CFSDS replay.
- [Runtime okruženja](docker/index.md) - Pinovani legacy setup i inference bez treniranja.
- [Promjene baze znanja](log.md) - Najnovije promjene prve i veze na detaljnu historiju.

## Ulazi za agente

- [Zajednička pravila](AGENTS.md) - Obavezni kontekst i pravila rada u repozitoriju.
- [Claude ulaz](CLAUDE.md) - Usmjerenje na isti AGENTS i projektni kontekst.
- [Gemini ulaz](GEMINI.md) - Usmjerenje na isti AGENTS i projektni kontekst.
- [GitHub Copilot ulaz](.github/index.md) - Repo instrukcije koje upućuju na zajedničke izvore.
