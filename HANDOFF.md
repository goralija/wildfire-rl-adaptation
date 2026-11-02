---
type: Playbook
title: Handoff — stvarna kohorta u SimFire-u
sources:
  - resource: /docs/STATUS.md
  - resource: /docs/NEXT_SESSION.md
  - resource: /docs/research/SIMFIRE_FPA_COHORT.md
  - resource: /docs/research/SIMFIRE_RL_ADAPTER.md
---
# Handoff

## Šta želimo pokazati

U istoj simulaciji uporediti početnog PPO agenta i kopiju koja je dodatno učila na
različitim uslovima stvarnih požara. Agent dobija prijavljenu lokaciju/datum i stvarne
karte goriva i terena. SimFire generiše nove situacije, poteze i nagrade. Historijski
završni obod ne postaje agentov “tačan odgovor”. Ne tvrdimo da je rezultat dokaz stvarno
spašenih hektara.

## Šta je sada pripremljeno

- 80 stvarnih USFS FPA-FOD požara: 40 train / 20 validation / 20 test, bez dijeljenja
  jednog požara između splitova.
- LANDFIRE gorivo i teren su preuzeti, poravnati i hash-provjereni za svih 80.
- Osam dnevnih gridMET polja postoji za svih 80. Po-slučaju dnevni proxy je priključen u
  Gymnasium adapter i mapping fajlovi su vezani hashovima za scenario manifeste.
- Pinned SimFire 2.0.1 + lokalni Python 3.9.25 RL runtime; tačne dodatne verzije su u
  `requirements/simfire-rl-macos-arm64-py39.freeze.txt`.
- Proxy smoke je prošao kroz po jedan train/validation/test požar; WAF 0.1/0.3/0.5 su
  tehnički provjereni. FPA-FOD/SimFire agent nije treniran i nema njegovih težina.
- Postojeći puni test paket sadrži jedan test koji trenira 16 koraka na malom sintetičkom
  `GridFire` fixtureu i odmah briše privremene težine. Taj test je izvršen tokom ove sesije;
  nije koristio FPA-FOD slučajeve ili SimFire. Ako je trening zabranjen, ne pokretati puni
  suite; vidi upozorenje u `AGENTS.md`.
- Maksimalno trajanje jedne SimFire ćelije postavljeno je na 15 jednominutnih koraka;
  postoje i no-op smoke rezultati/slike za po jedan slučaj iz svakog splita. Ovo nije
  fizička kalibracija.
- Manifesti i mali source/weather JSON-i su u Gitu; velike GeoTIFF karte ostaju u
  ignorisanom `.local/simfire-cohort-v2/`.

## Šta proxy znači

Izvorni gridMET je stvarni dnevni regionalni kontekst (~4 km), ne satno mjerenje na mjestu
paljenja. Prva SimFire varijanta pretpostavlja 10 m vjetar kao približan 20 ft vjetar, koristi
WAF 0.3, okrene vjetar iz “odakle” u “prema” i procijeni sitnu vlagu preko temperature/RH.
Ovo pravi izvršive simulacijske uslove, ali nije tačna historijska rekonstrukcija. Ograničenja
i izvori su u [dataset kartici](docs/research/SIMFIRE_FPA_COHORT.md) i [mapping logu](docs/research/EXPERIMENT_LOG.md#exp-038--map-daily-gridmet-context-into-explicit-simfire-proxy-inputs-2026-11-01).

## Šta još prije vjerodostojnog poređenja

1. Benchmark ugovor i inference-only runner su pripremljeni:
   [`SIMFIRE_EVALUATION_PROTOCOL.md`](docs/research/SIMFIRE_EVALUATION_PROTOCOL.md) i
   [`evaluation-v1.json`](configs/simfire/evaluation-v1.json). Ugovor koristi no-op,
   front-edge pravilo, base PPO i fine-tuned PPO na istim scenarijima i seedovima.
2. Lokalni validation preflight je prošao: svih 20 validation input paketa provjereno,
   jedna početna observation učitana, nula simulacijskih koraka i bez otvaranja test inputa.
3. Na svakom novom checkoutu ponoviti instalaciju i podatke iz
   [`docs/NEXT_SESSION.md`](docs/NEXT_SESSION.md), zatim pokrenuti validation preflight.
   Veliki rasteri i venv nisu u Gitu.
4. Još treba definisati base PPO trening recept, fine-tuning budžet i pregledati fizičke
   pretpostavke. SimFire model nije fizički validiran.
5. Larch Creek je isključen; preostalih 19 test požara ostaje zatvoreno do finalne uparene
   procjene. Runner blokira test bez eksplicitnih zastavica i oba checkpointa.
6. Trening nije pokrenut i ostaje odgođen; ova pripremna promjena ga ne pokreće.

## Ponoviti kratki smoke

```sh
.local/simfire-venv/bin/python scripts/smoke_simfire_gym_env.py
```

No-op kroz duži horizont, bez agenta i bez linije:

```sh
.local/simfire-venv/bin/python scripts/smoke_simfire_noop_horizon.py --splits train validation
```

Ispis i slike: `reports/real-fire-data/simfire-cohort-v2-gym-smoke/`. Za čistu instalaciju,
preuzimanje podataka i sljedeće zadatke vidi [`docs/NEXT_SESSION.md`](docs/NEXT_SESSION.md).
**Trening, fine-tuning i fizička validacija nisu još pokrenuti.**
