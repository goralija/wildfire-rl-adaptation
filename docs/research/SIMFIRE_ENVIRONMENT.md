---
type: Environment Record
title: Pokrenut lokalni SimFire — 2026-11-01
sources:
  - resource: /docs/specs/DECISION_RECORDS.md
  - resource: /docs/research/EXPERIMENT_LOG.md
---
# SimFire okruženje: prvi stvarni simulator smoke

## Šta smo napravili

Zvanični [MITRE SimFire](https://github.com/mitrefireline/simfire) je kloniran na
`04905b19fe8c10dc08d64faddd00303e0561bb66` (package 2.0.1). Napravljen je odvojeni
Python 3.9.25 environment `.local/simfire-venv/`; stari projektni Python 3.12 nije
mijenjan. Instalirano je 68 SimFire paketa, prema pinovima u
[`simfire-macos-arm64-py39.freeze.txt`](../../requirements/simfire-macos-arm64-py39.freeze.txt).
Izvorni klon, venv, wheel cache i BurnMD fajlovi ostaju u Git-ignorisanom prostoru.

Na ovom Macu uv je skinuo Python u ugniježđeni `python/bin/` direktorij, a zatim pao
pri pravljenju svoje završne symlink registracije. Sačuvani interpreter se ipak uredno
pokrenuo i njime je napravljen venv. Ovo je lokalni workaround; za drugi računar koristite
Python 3.9 ili Conda/uv Python 3.9, pa provjerite njihov lokalni setup. Ovaj freeze je
specifičan za macOS ARM64 i ne predstavlja Linux/Windows lock.

SimFire trenutno traži `pkg_resources`, pa environment pin-uje `setuptools<81`.
Smoke prolazi, uz upstream upozorenja o zastarjelom `pkg_resources` API-ju i Pydantic
konfiguraciji. Nije instaliran SimHarness/RLlib; oni su zaseban i teži dio i trebaju
posebnu provjeru kompatibilnosti.

## Reprodukcija demo pokretanja

Potrebni su SimFire source u `external/simfire/` i venv u `.local/simfire-venv/`:

```sh
.local/simfire-venv/bin/python scripts/run_simfire_demo.py \
  --steps 30 \
  --out runs/simfire-demo/first
```

Odredište mora biti novo/prazno. Script koristi zvanični `functional_config.yml`,
uključuje Pygame dummy display radi rada bez otvorenog prozora i čuva GIF, završnu mapu
i JSON receipt. Ne učitava BurnMD, LANDFIRE ni historijsku vremensku prognozu.

## Rezultat — 30 minuta

| Mjera | Vrijednost |
| --- | ---: |
| Mreža | 225 × 225 ćelija |
| Simulirano vrijeme | 30 minuta / 30 koraka |
| Spaljeno stanje na kraju | 1.687 ćelija |
| Aktivna vatra na kraju | 436 ćelija |
| Neizgorjelo | 48.502 ćelije |
| Postavljene linije / agent | 0 / ne koristi se |
| SimHarness/RL trening | nije pokrenut |

Ovo dokazuje samo da se instalirani SimFire može učitati, napraviti funkcionalno stanje,
odraditi korake i prikazati rezultat. **To nije stvarni historijski slučaj, fizička
validacija, agentov rezultat ni dokaz smanjenja štete.**

Sačuvani, mali primjeri: [animacija](../../reports/environment-setup/simfire-functional-demo/functional-fire.gif),
[završna mapa](../../reports/environment-setup/simfire-functional-demo/final-state.png)
i [receipt](../../reports/environment-setup/simfire-functional-demo/receipt.json).
Receipt eksplicitno označava `scientific_result=false`,
`real_historical_data=false` i `training_performed=false`.

## Granica i sljedeći korak

SimFire je tehnički pokrenut, ali real inputs/RL nisu spremni. Glavni sljedeći gate je jedan
scenario zasnovan na stvarnom događaju sa provjerenim fuel, elevation i weather ulazima, a ne
historijski linijski replay. Detalji su u
[scenario pipeline-u](REAL_IGNITION_SCENARIO_PIPELINE.md).

LANDFIRE bridge dry-run je u `scripts/prepare_mineral_landfire.py`. On koristi prijavljenu
požarnu lokaciju ili scenario JSON i fiksni 128×128 nominalni 30 m tile; ne bira AOI prema budućim
linijama/perimetrima. Cache path je poravnat sa SimFire 2.0.1 `LandFireLatLongBox` kodom.
Upstream kod dodaje 100 arc-seconds (~3.1 km sjever-jug) na donji desni ugao, iako njegov
komentar kaže oko 90 m; bridge kopira stvarnu implementaciju da SimFire pronađe isti fajl.
Dixie i Mineral dry-run prolaze. FPA-FOD tačka za Dixie je referentna lokacija incidenta,
ne potvrđena tačka paljenja; za razvojni smoke koristila bi se kao približna početna
lokacija. SimFireov geografski grid koristi fiksni stepen-po-ćeliji proračun, zato je 30 m
nominalna veličina, a stvarna istok-zapad udaljenost zavisi od geografske širine.
Operativni runner prima scenario manifest, ali stvarni API job i raster smoke još nisu
pokrenuti.

Na provjeri 2026-11-01 nema `LANDFIRE_EMAIL`, a disk ima 3.0 GiB slobodno; ranija napomena
o 29 MiB je zastarjela. SimHarness/RLlib još nije instaliran ni izabran za ovaj host.

### Recept za istu macOS ARM64 platformu

Za identično lokalno ponovno postavljanje treba instaliran Python 3.9.25, `uv` i mrežni
pristup:

```sh
git clone https://github.com/mitrefireline/simfire.git external/simfire
git -C external/simfire checkout 04905b19fe8c10dc08d64faddd00303e0561bb66
python3.9 -m venv .local/simfire-venv
uv pip install --python .local/simfire-venv/bin/python \
  -r requirements/simfire-macos-arm64-py39.freeze.txt
uv pip install --python .local/simfire-venv/bin/python ./external/simfire
```

Upstream repo [`pyproject.toml`](https://raw.githubusercontent.com/mitrefireline/simfire/04905b19fe8c10dc08d64faddd00303e0561bb66/pyproject.toml)
navodi Python `~3.9`. Tim koji nema Python 3.9 neka koristi Conda environment po
[SimHarness README-u](https://github.com/mitrefireline/simharness#installation); tačan
Linux/RLlib setup još nije napravljen niti testiran za naš projekat.
