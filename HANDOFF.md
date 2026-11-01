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
- `.local/simfire-venv` je odvojen Python 3.9.25 environment. U njemu radi kratki demo i
  novi 30-min smoke nad stvarnim gorivom i visinskim rasterom.
- BurnMD ZIP je lokalno provjeren prema službenom LFS SHA-256. Mineralovi podaci su
  pregledani, ali njegova linijska vremenska polja su prazna, a dataset reuse licenca
  nije razjašnjena. Sirovi ZIP i izvedene BurnMD mape ne redistribuirati.
- Dixie Fire 2021 (`FOD_ID 401019270`) je sačuvan kao mali FPA-FOD zapis i candidate
  kartica. Tačka je incident-referentna, ne potvrđeno GPS paljenje. Grid kartice je sada
  projektovan i tačan: 128×128 ćelija po 30 m u EPSG:32610.
- `scripts/fetch_simfire_real_inputs.py` pribavlja LF2016 FBFM13, LF2020 visinu i 24-satni
  ERA5 zapis za datum požara. Rasteri su provjereni po CRS-u, granicama, ćelijama i
  kategorijama goriva. Sirovi fajlovi su ignorisani u Gitu pod `.local/real-input-dixie/`;
  hashes su u kartici i receiptu.
- `scripts/run_simfire_real_input_smoke.py --steps 30` je pokrenut nad pravim LANDFIRE
  gorivom i terenom. [Karta, završno stanje, GIF i receipt](reports/real-fire-data/simfire-dixie-real-input-smoke/)
  su mali, pregledljivi primjeri. Atmosfera u tom smokeu je jasno označena kao demo.

## Šta još nije spremno

- Fuel je LF2016, pet godina prije Dixie požara. Jeste pre-event, ali nije dokazano da
  tačno opisuje gorivo 2021.
- ERA5 je oko 25 km rezolucije, a FPA-FOD HHMM nema razjašnjenu vremensku zonu. ERA5
  10-m vjetar nije isto što i midflame vjetar u SimFire; relativna vlažnost nije vlaga
  goriva. ERA5 zato još nije ubačen u simulaciju.
- Imamo jedan razvojni događaj, ne pravu train/validation/test kohortu.
- SimHarness/RLlib nije instaliran ni pokrenut; standalone SimFire smoke nije RL trening.
- Nema fizičke validacije niti zaključka o stvarnim hektarima spašenim u požaru.

## Sljedeći redoslijed

1. Provjeriti dostupnost i godinu boljeg fuel sloja za događaje koje ćemo stvarno uzeti.
2. Odlučiti i zapisati opravdan pristup datumu, 10-m vjetru i vlazi goriva; ne izjednačiti
   ERA5 RH sa fuel moisture.
3. Napraviti FPA-FOD kandidatsku kohortu i zamrznuti split po cijelim incidentima.
4. Postaviti/pinovati RL runtime u izolovanom okruženju i pokrenuti kratak CPU smoke.
5. Definisati no-op i jednostavne baseline politike, jednak budžet i horizont.
6. Tek nakon toga trenirati/fine-tunati i napraviti uparenu held-out evaluaciju i vizualizacije.

## Gdje je šta

- [STATUS](docs/STATUS.md) — urađeno i otvoreno, jasno razdvojeno.
- [BACKLOG](docs/BACKLOG.md) — aktivni taskovi; stari CFSDS plan je ispod označen kao arhiva.
- [DESIGN](docs/DESIGN.md) — istraživačko pitanje i metod.
- [Scenario pipeline](docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md) — šta je Y, šta je X i kako ih spajamo.
- [Mineral audit](docs/research/MINERAL_CASE_AUDIT.md) — dokaz šta je BurnMD slučaj dao i nije dao.
- [SimFire runtime](docs/research/SIMFIRE_ENVIRONMENT.md) — instalacija i smoke izlaz.
- [ADR-040](docs/specs/DECISION_RECORDS.md#adr-040--train-on-real-ignition-conditions-with-simulated-actions-2026-11-01) — odluka koja mijenja obavezni gate.
- [Arhivirani CFSDS handoff](HANDOFF_CFSDS_ARCHIVE.md) — prethodna putanja, nije aktivni plan.
