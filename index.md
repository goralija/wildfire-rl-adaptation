---
okf_version: "0.2"
---
# Wildfire RL adaptation — baza znanja

## Počni ovdje

- [Projekt i pokretanje](README.md) - Cilj istraživanja i minimalni setup.
- [Sažeti projektni kontekst](knowledge/project-context.md) - Odabrani CFSDS pravac, pilot rezultat i otvoreni replay gate.
- [Handoff za kolegu](HANDOFF.md) - Prenosiv nastavak bez chat historije.
- [Trenutno stanje](docs/STATUS.md) - Šta radi, dokazi i ograničenja.
- [Naredna sesija](docs/NEXT_SESSION.md) - Redoslijed nastavka.
- [Prioriteti i prihvat](docs/BACKLOG.md) - TASK-004c adapter je završen; preostaje train-only input QC i no-action gate.

## Pronađi detalje i dokaze

- [Kontekst i pravila održavanja](knowledge/index.md) - Mapa koda/zadataka, OKF profil i održavanje.
- [Dokumenti projekta](docs/index.md) - Protokol, zahtjevi, specifikacije, odluke i historija.
- [Podaci](data/index.md) - Porijeklo, javni izvori i CFSDS pilot cohort manifest.
- [Real-case pipeline](docs/research/REAL_CASE_PIPELINE.md) - Jednostavan opis šta stvarni podaci daju (Y), šta simulator prima (X), te jaz početnog fronta.
- [Train-only CFSDS input QC](docs/research/CFSDS_TRAIN_INPUT_QC.md) - Izmjereni ulazi, target-blind početno stanje i otvoreni fuel/weather/spatial/suppression rizici.
- [TRAIN fuel-vintage mask proof](reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json) - Provjera da su u jednom TRAIN slučaju target dan i kasniji dani van maske; godišnja mapa još nije kreirana.
- [TRAIN target-blind input proof](reports/real-fire-data/cfsds-target-blind-input-invariance.json) - Target maska mijenja truth, ali ne početni input za `2018_747`.
- [TRAIN target-blind window screen](reports/real-fire-data/cfsds-train-target-blind-window-screen.json) - Pre-target screen; pokazuje ograničenje 2×2 km izreza bez korištenja targeta za izbor.
- [Izvještaji](reports/index.md) - Sintetički pilot, runtime dokazi i stvarni CFSDS C++ replay.
- [Runtime okruženja](docker/index.md) - Pinovani legacy setup i inference bez treniranja.
- [Promjene baze znanja](log.md) - Najnovije promjene prve i veze na detaljnu historiju.

## Ulazi za agente

- [Zajednička pravila](AGENTS.md) - Obavezni kontekst i pravila rada u repozitoriju.
- [Claude ulaz](CLAUDE.md) - Usmjerenje na isti AGENTS i projektni kontekst.
- [Gemini ulaz](GEMINI.md) - Usmjerenje na isti AGENTS i projektni kontekst.
- [GitHub Copilot ulaz](.github/index.md) - Repo instrukcije koje upućuju na zajedničke izvore.
