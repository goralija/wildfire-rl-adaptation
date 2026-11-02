---
type: Data Quality Audit
title: FPA-FOD, FEDS-CONUS i FLE — crosswalk i pre-agent gate
status: current
generated: {by: "process:codex", at: "2026-11-02T23:20:54Z"}
sources:
  - resource: /data/manifests/fireline-benchmark-cohort-v1.json
  - resource: /reports/real-fire-data/fpa-feds-fle-crosswalk-v1.json
  - resource: https://zenodo.org/records/22921773
  - resource: https://www.ess.uci.edu/~uci-nasa-firetracking/
  - resource: https://www.fs.usda.gov/rds/archive/catalog/RDS-2025-0011
---
# FPA-FOD, FEDS-CONUS i FLE — crosswalk i pre-agent gate

## Odluka

**Dogovoreni pre-agent data gate nije prošao u oba splita. Ne prelaziti na SimFire
adapter, no-op kalibraciju ili PPO trening dok se pokrivenost ne razriješi pod
unaprijed određenim pravilom ili se protokol izričito ne promijeni.** Test kohorta nije
učitana. Godišnje FEDS arhive nisu preuzete; audit je koristio prostorno indeksirane
FlatGeobuf upite preko HTTP Range-a, a validation je završno filtriran iz sačuvanog
kandidatskog izvještaja jer Zenodo nije bio dostupan pri nastavku.

## Činjenice i rezultati audita

Ulaz je verzionisana kohorta od 60 požara iz FPA-FOD-a: 40 train (2018/2019) i 20
validation (2023). Test slučajevi iz prvobitnog 80-požarnog uzorka namjerno nisu u
manifestu. Manifest čuva FPA-FOD ID, incidentni naziv/državu, datum otkrića i izvornu
tačku. Prijavljena završna površina i MTBS ID nose oznaku `reference_only`.

FEDS-CONUS ne sadrži FPA-FOD ID, zato se događaji spajaju samo po početnim
informacijama: FEDS `t_st` datum je od 1 dan prije do 2 dana poslije FPA-FOD datuma
otkrića, a barem jedan FEDS obod od `t_st` do `t_st + 24 h` mora biti najviše 3 km od
FPA-FOD tačke. Slučaj se prihvata samo ako je takav kandidat jedinstven i ima barem
dva uzastopna 12h stanja. Konačna površina, završni obod, FLE ishod i test split ne
biraju FEDS ID. Koordinata i datum FPA-FOD-a imaju nepoznatu event-specifičnu
nesigurnost, pa je veza označena kao provisional.

| Split | FPA slučajevi | Jedinstven FEDS kandidat | ≥2 uzastopna 12h stanja | ≥5 stanja / 48h | FLE incidentni sažetak |
| --- | ---: | ---: | ---: | ---: | ---: |
| Train | 40 | 13 | **13** | 13 | 0 |
| Validation | 20 | 7 | **7** | 7 | 13 |
| Prag | — | — | train ≥20; validation ≥8 | — | informativno |

Nijedan split ne doseže svoj prag: train nedostaje najmanje 7, validation najmanje 1
slučaj. Svih 13 train i 7 validation kandidata imaju najmanje pet tačno razmaknutih
FEDS opservacija unutar lokalnog spatial query-a. To je pokrivenost postojećeg
manifest-a, ne procjena ukupne dostupnosti FEDS-a. Pre-agent gate je **FAIL**.

Prva eksplorativna provjera dala je 17/40 i 12/20 jer je spajala događaje koji su bili
blizu FPA-FOD tačke bilo kad u cijelom FEDS toku. To je previše permisivno za inicijalno
stanje. Strogi rezultat iznad traži blizinu u prvih 24 sata od `t_st`. Za validation
je taj kriterij deterministički primijenjen na ranije sačuvane kandidate: njihov
izvještaj čuva najraniji timestamp unutar 3 km, pa se može tačno odbaciti kasno prvo
pojavljivanje bez ponovnog preuzimanja geometrije. [Kandidatski izvještaj](../../reports/real-fire-data/fpa-feds-fle-crosswalk-validation-candidate-search-v1.json)
je sačuvan radi porijekla; skripta podržava isti postupak preko
`--filter-existing-report`. Zenodo DNS nije bio dostupan pri nastavku, zato validation
filter nije nezavisno ponovljen preko mreže.

WFIGS/IRWIN tačan ID spoj radi za 20/20 slučajeva validation 2023; agregirani FLE
incidentni sažetak postoji za 13/20. Za svih 40 train slučajeva iz 2018–2019 nije
nađen WFIGS IRWIN ID iz FPA-FOD `FPA_ID` vrijednosti, pa nema ni FLE sažetka u ovom
spoju. To je zasebna prepreka za historijski suppression/resource opis. Dostupni FLE
servis je grupisani incidentni sažetak i nije linijska geometrija. FLE kategorije
„Held / Burned Over / Not Engaged“ i završni perimetar su post-hoc evidencija, ne
uzročna procjena rezultata linije u counterfactual epizodi.

Slučaj `Hayden` (`FOD_ID 401316132`) je ručno provjeren kao kontrola: FPA-FOD
`2023-IDSCF-023084` → WFIGS `poly_IRWINID` `{3B96070F-23BB-4B83-A2CB-5FA4C2E741E2}`
→ FLE sažetak. FEDS `fireID=59310`, `t_st=2023-07-19T12:00:00`; postoje 68 poludnevnih
opservacija koje sijeku početnu okolinu, do 2023-08-22. Ovo potvrđuje da pipeline radi
za taj događaj, ne da je cijeli izvor fizički validiran.

Pojedinačni redovi su sačuvani u [kombinovanom JSON izvještaju](../../reports/real-fire-data/fpa-feds-fle-crosswalk-v1.json),
[train izvještaju](../../reports/real-fire-data/fpa-feds-fle-crosswalk-train-v1.json)
i [validation izvještaju](../../reports/real-fire-data/fpa-feds-fle-crosswalk-validation-v1.json).
Reproducibilna skripta je
[`audit_feds_fpa_fle_crosswalk.py`](../../scripts/audit_feds_fpa_fle_crosswalk.py).
Da se smanji opterećenje Zenodo arhive, svaki split se pokreće odvojeno:

```sh
python scripts/audit_feds_fpa_fle_crosswalk.py --split train --out reports/real-fire-data/fpa-feds-fle-crosswalk-train-v1.json
python scripts/audit_feds_fpa_fle_crosswalk.py --split validation --out reports/real-fire-data/fpa-feds-fle-crosswalk-validation-v1.json
python scripts/audit_feds_fpa_fle_crosswalk.py --combine-split-reports reports/real-fire-data/fpa-feds-fle-crosswalk-train-v1.json reports/real-fire-data/fpa-feds-fle-crosswalk-validation-v1.json --out reports/real-fire-data/fpa-feds-fle-crosswalk-v1.json
```

Kada FEDS arhiva nije dostupna, sačuvani kandidatski izvještaj može se strogo
postfiltrirati bez ponovnog mrežnog upita:

```sh
python scripts/audit_feds_fpa_fle_crosswalk.py --filter-existing-report reports/real-fire-data/fpa-feds-fle-crosswalk-validation-candidate-search-v1.json --out reports/real-fire-data/fpa-feds-fle-crosswalk-validation-v1.json
```

## Izvori i šta oni podržavaju

- FEDS-CONUS arhiva je verzija v1 objavljena 2026-10-02, 2012–2025; `lf_perimeter`
  fajlovi sadrže postprocesirane obode velikih požara preko 4 km² na 12-satnim
  koracima, izvedene iz VIIRS aktivnih detekcija rezolucije 375 m. Zenodo metapodaci
  daju CC BY 4.0 i checksume korištenih fajlova. [FEDS arhiva](https://zenodo.org/records/22921773),
  [zvanični FEDS pregled](https://www.ess.uci.edu/~uci-nasa-firetracking/).
- Zvanični NRT OGC servis nije zamjena za ovu arhivu kroz sve godine: njegova
  dokumentacija navodi 2018–2021 za Western US i 2025–danas za North America; 2023
  slučajevi zato dolaze iz objavljene arhive. [FEDS NRT FAQ](https://earth-information-system.github.io/fireatlas/docs/nrt.html).
- FLE RDS izdanje obuhvata linije i ishode iz NIFC operativnih podataka 2017–2024;
  Forest Service navodi da se podaci mogu koristiti bez naknade ili dodatne dozvole.
  Ovdje korišten ArcGIS sloj daje grupisane sažetke. Za prostorni obračun linija treba
  odvojeno pribaviti i provjeriti RDS geometrije. [RDS-2025-0011](https://doi.org/10.2737/RDS-2025-0011),
  [opis istraživačkog izdanja](https://www.fs.usda.gov/rds/archive/catalog/RDS-2025-0011).
- GOFER daje satne obode i aktivne linije, ali objavljeni pilot je 28 vrlo velikih
  požara u Kaliforniji 2019–2021, uz grublju GOES prostornu rezoluciju oko 2 km;
  odličan je dodatni vremenski izvor gdje postoji, ali ne pokriva validation 2023 i
  nije tiha zamjena za kohortu. [GOFER studija](https://essd.copernicus.org/articles/16/1395/2024/).
- FEDS-MTBS je alternativni način identifikacije preko MTBS ID-ja, ali FEDS tracking
  je ograničen konačnim Landsat/MTBS obodom; dokumentacija navodi da završni obod
  ograničava tracking. To je prikladno za ograničenu vizualnu rekonstrukciju, ne za
  nezavisni no-action gate niti kao isti benchmark. [FEDS-MTBS opis](https://www.ess.uci.edu/~uci-nasa-firetracking/),
  [arhiva](https://zenodo.org/records/20187963).
- ICS-209-PLUS daje dnevni kontekst o incidentu i resursima (1999–2020), ali nema
  dokaz da je određeni broj ljudi/opreme radio na određenoj liniji. Zato se u
  counterfactual benchmarku koriste jednaki standardizirani budžeti za sve politike;
  ICS podaci mogu biti samo incidentni kontekst za godine pokrivenosti. [USFS ICS-209-PLUS](https://research.fs.usda.gov/firelab/products/dataandtools/ics-209-plus).
- SimFire/SimHarness rad opisuje agentni simulator i akcije intervencije, ali ne
  pretvara runtime test u fizičku validaciju. Predloženi zaključak ostaje ograničen
  na politiku unutar kalibrisanog simulatora. [SimFire i SimHarness rad](https://arxiv.org/abs/2311.15925).
- W.I.S.E. evaluacija poredi mnogo 12-satnih oboda i eksplicitno prikazuje koliko se
  metrika može uljepšati ako se trajanje biranja oboda odabere po najboljem F1 za
  svaki posmatrani dan. Ovdje zato nema podešavanja svakog požara prema njegovom
  završnom obodu. [W.I.S.E. evaluacija](https://doi.org/10.1071/WF26072).

## Predloženi nastavak — nije pokrenut

1. Pripremiti prijedlog kako dostići pragove za train i validation pod istim ranim
   prozorom, bez mijenjanja pravila nakon gledanja rezultata. Postojeći validation set
   je viđen i ne smije se koristiti za tuning; svaki novi validation izbor mora imati
   unaprijed dokumentovan selekcijski okvir. Test ostaje zatvoren.
2. Ako dozvoljeni kohortni poolovi ne daju najmanje 20 train i 8 validation požara,
   donijeti novu izričitu odluku o drugom izvoru/kohorti ili revidiranom benchmarku.
   Ne širiti radius ili vremenski prozor samo da bi prag prošao.
3. Razriješiti FLE spoj starih FPA ID formata. U međuvremenu ne porediti historijski
   resurs po liniji; dati svim agentima identičan unaprijed definisan budžet. Ne
   koristiti završni obod kao nagradu ili terminalni uslov.
4. Tek nakon prolaza data gatea selektivno portati provjereni SimFire scenario
   adapter. Početno stanje nosi već opožareni scar i više aktivnih ćelija; decisions
   su svakih 12h do fiksnih 48h. Politika bira čekanje ili jedan od 16 sektora fronta.
   Standardni resurs je 20-člana ekipa tokom 8h smjene; linija se gradi postepeno dok
   se vatra širi. Budžeti su 0/1/2/4 smjene. NWCG tabele daju početni produktivni
   raspon, a ne obećanu stvarnu operativnu brzinu. [NWCG production tables](https://www.fs.usda.gov/t-d/nwcg/files/NWCG_production_tables_2021.pdf),
   [Holmes & Calkin (2013)](https://doi.org/10.1071/WF11098).
5. Agent ne vidi ni ne dobija nagradu iz istorijskog završnog oboda; simulator se
   nastavlja nakon nultog budžeta i poslije kraja historijskog toka. Porediti no-op,
   front-edge heuristiku, zamrznutog PPO-a i kopiju fine-tunanu samo na trainu, uz
   iste scenarije, budžete, vrijeme i uparena sjemena. Primarno mjeriti novo izgorjelu
   površinu u 48h; zatim trajanje/containment, radne sate ekipe, dužinu izgrađene linije
   i trade-off štete prema resursima. Otvoriti test tek za završni obračun.
6. Ovaj benchmark bi pokazao razliku politika **unutar SimFire parametara**, ne broj
   hektara koje bi stvarni agent sigurno spasio. Za simulator se prije agentnog testa
   traži no-op poređenje s persistence i jednostavnom elipsnom referencom te provjera
   rubnog efekta mape.

Ovaj audit je data-coverage rezultat, ne simulacija širenja, ne fizička validacija i
ne RL rezultat. SimFire kod, scenariji, PPO checkpointovi i produženo treniranje nisu
preuzeti niti pokrenuti u ovom koraku.
