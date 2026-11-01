---
type: Handoff
title: Naredni korak — zatvoriti vremenske i fuel pretpostavke
sources:
  - resource: /docs/STATUS.md
  - resource: /docs/BACKLOG.md
  - resource: /docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md
---
# Nastavak rada

## Šta je sada pokretljivo

U worktree-u su `external/simfire` (MITRE SimFire 2.0.1) i lokalni Python 3.9.25 venv.
Dixie Fire 2021 je samo razvojni primjer iz USFS FPA-FOD-a: njegova tačka je prijavljena
incidentna lokacija s nepoznatom preciznošću, ne GPS potvrda gdje je požar počeo.
Scenario je na tačnoj 128×128, 30 m mreži u EPSG:32610.

## Ako treba napraviti okruženje ispočetka

Ove naredbe su za macOS ARM64 i Python 3.9.25; freeze fajl nije Linux/Windows recept.
Izvršiti jednom u svježem worktree-u:

```sh
git clone https://github.com/mitrefireline/simfire.git external/simfire
git -C external/simfire checkout 04905b19fe8c10dc08d64faddd00303e0561bb66
python3.9 -m venv .local/simfire-venv
.local/simfire-venv/bin/python -m pip install -r requirements/simfire-macos-arm64-py39.freeze.txt
.local/simfire-venv/bin/python -m pip install ./external/simfire
```

To instalira samostalni SimFire i biblioteke za GeoTIFF. Ne instalira SimHarness/RLlib,
ne trenira agenta i ne mijenja sistemski Python.

Skripta za preuzimanje snima iz ignorisanog lokalnog foldera:

```sh
.local/simfire-venv/bin/python scripts/fetch_simfire_real_inputs.py
.local/simfire-venv/bin/python scripts/run_simfire_real_input_smoke.py --steps 30
```

Prva komanda pribavlja LANDFIRE 2016 FBFM13 goriva, LANDFIRE 2020 visinu terena i jedan
24-satni ERA5 niz za datum događaja. Provjerava GeoTIFF CRS, veličinu, granice i vrijednosti
goriva. Druga komanda koristi stvarne fuel/terrain nizove u SimFire i pravi mapu, završno
stanje i GIF u `reports/real-fire-data/simfire-dixie-real-input-smoke/`.

Sirovi TIFF i ERA5 JSON ostaju u `.local/real-input-dixie/`; mali manifest, hashovi, skripte,
receipt i slike su u Git-u. Izlaz je integracijski smoke, ne historijska simulacija: vjetar i
vlaga su demo vrijednosti, jer nije opravdano pretvoriti ERA5 10-m vjetar direktno u
SimFire midflame vjetar, niti vazdušnu RH nazvati vlagom goriva. HHMM `1615` u FPA zapisu
nema potvrđenu vremensku zonu. LF2016 gorivo prethodi Dixie događaju pet godina i ostaje
samo kandidat.

## Sljedeće konkretne odluke

1. Tražiti noviji pre-event fuel raster ili odabrati historijske požare sa dostupnom
   odgovarajućom LANDFIRE godinom.
2. Provjeriti FPA-FOD discovery-time definiciju; odabrati da li se koristi samo datum ili
   potvrđena lokalna zona.
3. Odabrati model za wind-at-flame i mrtvu vlagu goriva (ili zadržati podatke kao
   kontekst, a ne simulator input). Sačuvati pretpostavke kao polja/parametre, ne skrivati
   ih u skripti.
4. Sastaviti kohortu više požara i podijeliti po cijelom incidentu u train/validation/test.
5. Postaviti RL runtime, odvojeno provjeriti no-op/budget semantiku, zatim pokrenuti
   jednako uparene base-vs-finetune-vs-baseline epizode.

Ne trenirati na ovom jednom Dixie fixture-u i ne koristiti konačnu površinu ili perimeter
kao cilj smanjenja štete. Kanonski redoslijed je u [backlogu](BACKLOG.md), trenutni dokazi u
[statusu](STATUS.md) i [experiment logu](research/EXPERIMENT_LOG.md#exp-033--real-layers-fetched-and-loaded-by-simfire-2026-11-01).
