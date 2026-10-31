---
type: Experiment Report
title: TRAIN-only target-independent CFSDS day-pair and domain screen
status: stable
sources:
  - resource: /scripts/audit_cfsds_train_full_day_pairs.py
  - resource: /reports/real-fire-data/cfsds-train-full-day-pair-screen.json
  - resource: /reports/real-fire-data/cfsds-train-full-day-pair-screen.csv
---
# TRAIN-only target-independent CFSDS day-pair and domain screen

## Pitanje

Koliko se fire arrival rastera u TRAIN godinama može pretvoriti u dan-par bez
uslova koji zavise od narednog dana, i kako pet unaprijed zadatih fizičkih prozora
stoji kada se izabere početno stanje samo iz ranijeg dijela požara?

Ovo je geometrijski pre-screen 2014–2018 rastera. Nije konačna benchmark kohorta,
FireCase, simulator replay, dokaz da Cell2Fire prati stvarni požar, niti mjera koristi
RL agenta.

## Pravilo izbora para

Za svaki CFSDS fire arrival raster, `input day` je najraniji DOY na kojem su najmanje
tri validna 90 m raster piksela označena kao pristigla vatra. `target day` je sljedeći
kalendarski dan. Pravilo koristi samo godišnji arrival raster. Ne traži target piksele,
red u `Firegrowth_groups`, pozitivnu `firearea`, weather vrijednost, target centroid ili
bilo kakvu ciljnu geometriju. Ne bira se pet najboljih događaja: svaki raster se obradi.

Izabranih 1.301 parova zadržano je kroz poređenje svih pet domena. Ako nema označenih
piksela na naredni dan, par ostaje u cohort screen-u i dobija status
`no_mapped_pixels_on_next_day`; to ne znači dokazano nulti fizički rast. Ako bi target
prešao godišnju granicu arhive, par bi ostao zabilježen kao neopažljiv bez otvaranja
sljedeće godine.

Za svaki unaprijed zadan prozor, crop se bira iz input-day i starijih arrival piksela.
Prozor mora imati barem tri input-day piksela u sigurnoj unutrašnjosti; rubni pojas je
širok približno jednu modelsku ćeliju. Tek nakon izbora prozora računaju se target
metrike. Skripta za svaki od 1.301 para dodatno uklanja sve arrival oznake poslije input
dana, ponovo primjenjuje izbor i potvrđuje da input dan ostaje isti.

## Opseg i podaci

- Otvoreni su samo godišnji raster ZIP-ovi 2014–2018: ukupno 1.301 TIFF (234, 351, 116,
  322 i 278 po godini). Heldout/validation/test arhive nisu čitane.
- Svaki TIFF ima 90×90 m kvadratne ćelije; source ZIP hashovi su u JSON receipt-u.
- Svih 1.301 rasterskih požara ima bar jedan dan sa najmanje tri validna piksela; svih
  1.301 dobilo je početni/target dan.
- Na 1.010 parova naredni dan ima mapirane piksele. Na 291 paru naredni dan u rasteru
  nema nijednog mapiranog piksela. Broj po godinama: 2014 183/51, 2015 293/58,
  2016 82/34, 2017 239/83 i 2018 213/65 (mapirano/nema mapiranih piksela).
- Odabir i audit ne koriste dnevne group CSV tabele, gorivo, DEM, weather API, C++ ili RL.

## Rezultati po domeni

Capture omjer se računa samo za slučajeve gdje je naredni dan imao mapirane target
piksele i gdje je pre-target prozor mogao biti napravljen. Target-piksel „u prozoru“ broj
je nad svih 1.010 target-opaženih parova; prozor koji nije moguće napraviti broji se kao
bez capture-a u toj koloni. Brojevi su native 90 m piksela, bez resamplinga u Cell2Fire
ćelije.

| Mreža | Prozor nađen / 1.301 | Target opažen, neki piksel u prozoru / 1.010 | U sigurnoj unutrašnjosti / 1.010 | Medijan target capture (N) | Medijan input-front capture | Razlog nemogućeg prozora |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 20×20, 100 m (oko 2 km) | 1.295 (99.5%) | 945 | 933 | 36.71% (1.008) | 99.36% | 4 bez 3 sigurnih front ćelija; 2 rastera premala |
| 20×20, 150 m (oko 3 km) | 1.226 (94.2%) | 921 | 913 | 66.45% (957) | 100% | 7 bez sigurnog fronta; 68 rastera premala |
| 20×20, 200 m (oko 4 km) | 1.042 (80.1%) | 804 | 799 | 85.78% (823) | 100% | 5 bez sigurnog fronta; 254 rastera premala |
| 20×20, 300 m (oko 6 km) | 729 (56.0%) | 580 | 579 | 98.98% (593) | 100% | 6 bez sigurnog fronta; 566 rastera premala |
| 40×40, 100 m (oko 4 km) | 1.044 (80.2%) | 805 | 804 | 85.86% (824) | 100% | 3 bez sigurnog fronta; 254 rastera premala |

Capture medijane na većim prozorima koriste manji skup slučajeva jer mnogo izvornih
fire rastera nema potrebnu širinu/visinu. Zato medijane nisu direktno uporediva rang-lista
modela: 6 km uhvati veći dio targeta tamo gdje stane, ali može se napraviti za samo 729
od 1.301 događaja. Kod 2 km gotovo svaki slučaj dobije početni prozor, ali medijalni
capture je 36.71% među slučajevima s opaženim targetom i validnim cropom. Ni ovo ne
pokazuje kako bi FBP/Cell2Fire propagirao vatru.

Isti tensor 20×20 na 150–300 m mijenja fizičko značenje akcije i požarnog širenja.
40×40 na 100 m mijenja observation/action dimenzije i ne može koristiti postojeći
20×20 checkpoint bez novog modela. Nijedna nova domena nije izabrana iz ovih post-selection
target metrika.

## Zaključak i naredni korak

Day-pair membership je sada target-independent za puni skup godišnjih TRAIN rastera po
ovdje navedenom operativnom pravilu. Stari shortlist od 25 parova i dalje je koristan kao
istorijski bounded audit, ali njegovo ranije target-uslovljeno članstvo nije zamijenjeno
retroaktivno.

Screen daje osnovu za sljedeći **train-only ulazni gate**: odrediti kako će se realne
episode geometrije spojiti sa prihvatljivim, vremenski sigurnim FBP gorivom i ostalim
simulator ulazima. Trenutni 2014b fuel sloj nema potvrđen per-pixel cutoff, succession
crosswalk i non-fuel scar contract nisu riješeni, a DEM/weather provenance i suppression
nedostaju. Zato 1.301 par nije 1.301 trenabilnih/validiranih simulator scenarija. Ne
pokretati no-action benchmark ni fine-tuning dok postojeći no-action gate ne prođe.

## Ograničenja i reprodukcija

- CFSDS nudi dnevno interpolirane arrival oznake, ne tačan satni front ni dokaz o
  gašenju. „Nema mapiranih target piksela“ može biti rast koji nije zabilježen po
  proizvodu, a ne fizičko odsustvo rasta.
- Tri piksela su samo minimalan rasterski uslov za pre-screen. To nije fizički uzorak
  dovoljan za agentov benchmark.
- Target coverage je post-selection dijagnostika. Nije ulaz u izbor para, prozora,
  checkpointa ili hiperpodešavanja.
- Nije urađen fuel/DEM/weather alignment, raster resampling, FireCase export, C++ replay,
  training, calibration, benchmark ili tvrdnja o policy koristi.

Ponoviti iz repo roota kada su lokalni TRAIN ZIP-ovi dostupni:

```sh
python3 scripts/audit_cfsds_train_full_day_pairs.py \
  --raw-root data/raw/cfsds-v1_1 \
  --out reports/real-fire-data/cfsds-train-full-day-pair-screen.json
```

Skripta generiše JSON sa pravilom, source ZIP i code hashovima, aggregate summaryjem, te
CSV sa svih 1.301 odabranih parova i pet setova domain metrika. Raw CFSDS podaci ostaju
izvan Git-a.
