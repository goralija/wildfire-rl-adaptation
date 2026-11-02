---
okf_version: "0.2"
---
# Wildfire RL adaptation — baza znanja

## Počni ovdje

- [Projekt i pokretanje](README.md) - Cilj istraživanja i minimalni setup.
- [Trenutni dizajn i status](docs/STATUS.md) - Šta je napravljeno i šta stvarno još nedostaje.
- [Pravila poređenja agenata](docs/research/SIMFIRE_EVALUATION_PROTOCOL.md) - unaprijed zaključani baselinei, seedovi, mjere i test gate; bez pokretanja treninga.
- [80 stvarnih požara](data/manifests/simfire-fpa-fod-cohort-v2.json) - 40 train / 20 validation / 20 test; gorivo/teren, raw gridMET i eksplicitni SimFire daily proxy postoje za svih 80.
- [Naredni koraci](docs/BACKLOG.md) - Redoslijed do validnog ulaza, prve karte i poređenja agenata.
- [Kontekst za nastavnika ili kolegu](HANDOFF.md) - prenosiv pregled projekta bez historije razgovora.

## Pronađi detalje i dokaze

- [Dokumenti i istraživanje](docs/index.md) - protokol, odluke, status, izvori i arhivirani rezultati.
- [Podaci i porijeklo](data/index.md) - format scenarija, izvori i pravila za raw fajlove.
- [SimFire RL adapter](docs/research/SIMFIRE_RL_ADAPTER.md) - šta agent vidi, kojim potezom djeluje, kako dobije nagradu i šta je još pojednostavljeno.
- [FPA-FOD kohorta](docs/research/SIMFIRE_FPA_COHORT.md) - izvor, split, gorivo/teren, provenance i data limitations.
- [Pregled stvarnih vremenskih podataka](reports/real-fire-data/simfire-cohort-v2-gridmet-overview.png) - lokacije požara te dnevne raspodjele vjetra i 100-satnog indikatora goriva.
- [SimFire okruženje i probe](docs/research/SIMFIRE_ENVIRONMENT.md) - izolovani runtime, verzije i reproducibilne komande.
- [Smoke na sva tri split-a](reports/real-fire-data/simfire-cohort-v2-gym-smoke/) - legalna MaskablePPO predikcija; demo atmosfera.
- [GridMET proxy smoke i WAF poređenje](reports/real-fire-data/simfire-cohort-v2-gridmet-waf-sensitivity.json) - 0.1/0.3/0.5; tehničko testiranje, bez `learn()`.
- [No-op epizode bez intervencije](reports/real-fire-data/simfire-cohort-v2-gridmet-noop-horizon/) - stvarni train/validation slučajevi; Larch Creek test smoke je odvojen i izbačen iz završnog testa; 19 test incidenata ostaje zatvoreno.
- [Izvještaji i slike](reports/index.md) - mape, animacije i reproducibilni receipts.
- [Arhivirani Firehose/Cell2Fire alati](docker/index.md) - prethodni runtime i eksperimenti.
- [Mapa koda i održavanje](knowledge/index.md) - gdje se nalaze skripte i kako nastaviti.
- [Promjene baze znanja](log.md) - najnovije bilješke i ranije historija.

## Ulazi za agente

- [Zajednička pravila](AGENTS.md) - Obavezni kontekst i pravila rada u repozitoriju.
- [Claude ulaz](CLAUDE.md), [Gemini ulaz](GEMINI.md) i [GitHub Copilot](.github/index.md) - koriste ista pravila projekta.
