---
type: Playbook
title: Nastavak projekta — scenariji stvarnih požara u SimFire-u
sources:
  - resource: /docs/STATUS.md
  - resource: /docs/BACKLOG.md
  - resource: /docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md
---
# Handoff — trenutni cilj i konkretno stanje

## Šta želimo pokazati

Želimo uporediti osnovnog i dodatno naučenog agenta koji postavljaju vatrogasne linije.
Oba se igraju u istoj simulaciji i dobijaju iste početne uslove i budžet. Pitanje je da li
agent koji je dodatno učio na **raspodjeli uslova iz stvarnih požara** pravi manju štetu
unutar simulacije. Ne predstavljamo to kao dokaz da bi u stvarnosti spasio isti broj
hektara.

## Dizajn koji izbjegava prethodno kruženje

Historijski BurnMD line replay nije više ulazni uslov za glavni ogled. Mineral Fire 2020
ima lokaciju, perimetre i linije, ali tačna vremena izgradnje linija nedostaju; korištenje
`CreateDate` kao vremena akcije bilo bi nagađanje. Umjesto toga scenario počinje od stvarne
prijavljene lokacije/datuma incidenta, a simulator dobija dokumentovan fuel, terrain i weather.
FPA-FOD koordinata nije nužno potvrđena tačka paljenja. Budući
obod/linije ne određuju mapu, stanje agenta ni RL nagradu.

Kandidat za širu, javno dostupnu raspodjelu incidenata je USFS FPA-FOD. Ono nudi prijavljeno
vrijeme/lokaciju i konačnu veličinu, uz prostornu nesigurnost lokacije; te vrijednosti nisu
30-m GPS istina. Zašto i kako: [pipeline i laički opis](docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md).

## Šta je stvarno spremno

- `external/simfire` je MITRE SimFire 2.0.1 na commitu
  `04905b19fe8c10dc08d64faddd00303e0561bb66`.
- `.local/simfire-venv` je odvojen Python 3.9.25 environment; 30-min funkcionalni demo
  ima GIF, završnu mapu i receipt u
  [demo folderu](reports/environment-setup/simfire-functional-demo/). To je funkcionalni
  smoke, ne historijski slučaj ili naučni rezultat.
- BurnMD ZIP je lokalno provjeren prema službenom LFS SHA-256. Mineralovi 11 perimetara,
  249 linija i 58 tačaka su pročitani i metadata audit je u
  [receiptu](reports/real-fire-data/mineral-case-audit.json). Sirovi ZIP, GIS geometrije
  i mapa ostaju van Git-a dok se data prava ne razjasne.
- `data/manifests/simfire-scenario.schema.json` definiše mali zajednički JSON. Veliki
  rasterski/weather ulazi ostaju fajlovi s vlastitim hashom.
- Dixie Fire 2021 (`FOD_ID 401019270`) je sačuvan kao mali FPA-FOD GeoJSON izvorni zapis i
  pretvoren u [candidate scenario karticu](data/manifests/simfire-fpa-fod-401019270-dixie-candidate.json).
  Kartica ima event ID, vrijeme bez izmišljene vremenske zone, WGS84 incident-referentnu
  tačku (ne potvrđeno paljenje), PLSS napomenu i grid od 128×128 nominalnih 30 m ćelija.
- `scripts/build_fpa_fod_scenario.py` može dohvatiti jedan FOD_ID i napraviti karticu.
  `scripts/prepare_mineral_landfire.py --scenario-manifest ... --dry-run` računa Dixie AOI
  i SimFire cache putanju. `scripts/run_simfire_operational_smoke.py` prima isti manifest
  kada odgovarajući TIFF bude u cache-u.

## Šta još nije spremno

- Pravi LANDFIRE raster nije preuzet. Trenutni shell nema `LANDFIRE_EMAIL`; zadnja provjera
  pokazala je 3.0 GiB slobodno (2026-11-01; raniji 29-MiB podatak je zastario).
- SimHarness/RLlib nije instaliran; treba izabrati podržan trening runtime nakon što se
  oslobodi prostor. Sam standalone SimFire nije RL trening.
- Nije potvrđena konverzija historijskog vremena/vremenskih uslova u SimFire ulaze.
- Nije napravljena FPA-FOD kohorta, incident split niti stvarni real-landscape scenario.
- BurnMD dataset reuse licenca je neriješena. Ne redistribuirati podatke niti izvedene mape.

## Sljedeći redoslijed

1. Za Dixie candidate pribaviti stvarni pre-event fuel/elevation i historijski weather.
   LANDFIRE job traži stvarni `LANDFIRE_EMAIL`; ne koristiti adresu iz Git postavki.
2. Pokrenuti `scripts/prepare_mineral_landfire.py --scenario-manifest data/manifests/simfire-fpa-fod-401019270-dixie-candidate.json`
   kad je email dostupan, pa provjeriti TIFF CRS/bounds/bands/no-data/lokaciju početne ćelije.
   LF2016 FBFM13 je samo pre-event tehnički fallback, ne konačna fuel-vintage odluka.
3. Napraviti scenario JSON sa verified raster/weather checksumima. Sve nedostajuće
   vrijednosti ostaju `missing`, ne popunjavaju se izmišljeno.
4. Pokrenuti scenario-manifest runner na jednom real-fuel/terrain tileu i napraviti
   prvu kartu/animaciju.
5. Sastaviti veći FPA-FOD uzorak i zamrznuti event-level train/validation/test split.
6. Instalirati/pinovati kompatibilan SimHarness/RLlib runtime ili mali dokumentovani Gym
   adapter; prvo kratki CPU smoke, pa tek onda budgeted RL.
7. Base-vs-fine-tuned vs-heuristic/no-op poređenje na jednakim heldout scenarijima,
   seedovima i budžetu.

## Gdje je šta

- [STATUS](docs/STATUS.md) — urađeno i otvoreno, jasno razdvojeno.
- [BACKLOG](docs/BACKLOG.md) — aktivni taskovi; stari CFSDS plan je ispod označen kao arhiva.
- [DESIGN](docs/DESIGN.md) — istraživačko pitanje i metod.
- [Scenario pipeline](docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md) — šta je Y, šta je X i kako ih spajamo.
- [Mineral audit](docs/research/MINERAL_CASE_AUDIT.md) — dokaz šta je BurnMD slučaj dao i nije dao.
- [SimFire runtime](docs/research/SIMFIRE_ENVIRONMENT.md) — instalacija i smoke izlaz.
- [ADR-040](docs/specs/DECISION_RECORDS.md#adr-040--train-on-real-ignition-conditions-with-simulated-actions-2026-11-01) — odluka koja mijenja obavezni gate.
- [Arhivirani CFSDS handoff](HANDOFF_CFSDS_ARCHIVE.md) — prethodna putanja, nije aktivni plan.
