---
okf_version: "0.2"
---
# Wildfire RL adaptation — baza znanja

## Počni ovdje

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
