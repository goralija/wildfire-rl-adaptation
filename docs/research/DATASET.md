---
type: Dataset Review
title: 'Dataset: šta imamo i šta ćemo koristiti'
sources:
- resource: /reports/firehose-verification/dataset-inventory.json
- resource: /data/manifests/upstream.json
---
# Dataset: šta imamo i šta ćemo koristiti

**Postavka okruženja i dataset opaženih požara su različite stvari.** Početni Firehose
fajlovi su ulazi za simulaciju; agent interakcijom stvara RL iskustvo. Oni sami nisu
skup stvarnih ishoda niti oznaka ispravnih intervencija. Korisnikov cilj je da ti ulazi
dolaze iz stvarnih požara i njihovih distribucija, a historijski događaji ostanu
odvojeni za replay/holdout. Odabrali smo Canada + CFSDS v1.1 jer odgovara postojećem
Canadian FBP simulatoru i nudi mnogo različitih požara. Jedan slučaj je već pretvoren
u simulator ulaze i no-action replayan, uz veliko neslaganje prema opaženom rastu. Ako
želimo stvarne BiH slučajeve, FireSpread_MedEU v2 je
našao 7 prvih prostorno lokaliziranih kandidata, a EFFIS-ova karta iz 2017. daje
evropske NFFL kodove goriva od 250 m; potrebni su kompatibilan simulator, provjera licence
i veći grid jer postojeći 20×20 prozor ne pokriva cijele dobre primjere. Dnevni perimetri traže
simulator state-import; ovaj projekat sada ima višepikselni početni state adapter.
Preporuka i format su u
[REAL_FIRE_DATASETS](REAL_FIRE_DATASETS.md) i [REAL_CASE_PIPELINE](REAL_CASE_PIPELINE.md);
punu listu fire ID-jeva i benchmark još treba zamrznuti.

## Postojeći Firehose Sub20x20 — data card

Izvor: [pinovani autorski repo](https://github.com/aidan-curtis/firehose/tree/e49a52a9a987a1585d25ddca2f711222ca500ffb/data/Sub20x20).
Lokalno: `external/firehose/data/Sub20x20/`, ignorisano u Gitu.
Inventar: [dataset-inventory.json](../../reports/firehose-verification/dataset-inventory.json).

| Dio | Zabilježeni sadržaj | Uloga |
| --- | --- | --- |
| `Forest.asc` | 20×20 = 400 ćelija; 307 gorivih, 93 nonfuel | raspored goriva |
| Fuel kodovi | C-1 19, C-2 203, C-3 18, O-1a 67, nonfuel 93 | Canadian FBP gorivo |
| `elevation.asc`, `slope.asc`, `saz.asc` | iste dimenzije, origin, cellsize i NODATA | teren i orijentacija |
| `Data.csv` | 400 ćelijskih redova, 20 kolona | pripremljeni parametri simulatora |
| `fbp_lookup_table.csv` | svi opaženi kodovi imaju lookup | tip goriva i RGB prikaz |
| `Weather.csv` | 8 vremenskih redova | stvarno korišten u sadašnjem rows testu |
| `Weathers/Weather*.csv` | 129 dodatnih fajlova po 8 redova | alternativni scenariji, nisu automatski korišteni |
| `Ignitions.csv` | input navodi 381; inference provjera koristi 372 | različita mjesta: 381 je red 20/kolona 1 (O-1a), 372 red 19/kolona 12 (C-2) |
| Priority maska | `Reward.asc` nije prisutan za ovu mapu | napravit ćemo kontrolisani dodatni ulaz |

Ukupno 141 fajl / 159,595 bajtova (~156 KiB). Ima 130 različitih weather sadržaja
računajući bazni fajl; različit sadržaj ne potvrđuje nezavisno uzorkovanje iz stvarnosti.
ASC navodi cellsize=100 i projektovane koordinate, ali CRS/jedinice nisu dokumentovani
ovim inventarom. Ne pretvarati ćelije u hektare prije provjere CRS-a.
`Data.csv` ima lat/lon i kanadske fuel tipove; ovo nisu provjereni podaci za BiH.

## Kvalitet i ograničenja

- Četiri rastera imaju po 20 redova × 20 kolona i ista zaglavlja unutar Sub20 paketa.
  Naknadna Dogrib provjera otkrila je da origin ne odgovara stvarnom izrezu pune
  mape: gorivo/elevation su identični njenom bloku [0:20,20:40]. Zajednička zaglavlja
  zato ne dokazuju ispravnu geografsku lokaciju; vidjeti REAL_FIRE_DATASETS.
- Nema nepoznatih fuel kodova. Svih 130 weather fajlova ima 8 redova; nema negativnog
  WS ili RH izvan [0,100] u tim poljima. Ovo nije fizička validacija svih vrijednosti.
- Više `Data.csv` kolona je prazno po dizajnu jer se vrijeme/vjetar/indeksi popunjavaju
  iz weather inputa ili koriste defaulti; ne popunjavati proizvoljno nule bez izvornog koda.
- Zadnji red `Data.csv` ima 19 polja umjesto 20; nedostaje prazni završni `pattern`.
  Trenutni C++ parser koristi poziciju 18 za pattern (isto kao time), pa izvršeni runovi
  ne pucaju zbog nedostajuće zadnje kolone. To je schema/parser neusklađenost koju treba
  razjasniti prije drugačijeg preprocessinga, a ne tiho prepisati raw fajl.
- Bazni weather ima ISO datume iz 2001; alternative koriste drugačiji datum-format.
  Njihovo porijeklo/generisanje, vremenska zona i statistička nezavisnost nisu utvrđeni.
- Repo navodi GPL-3.0 za kod. Posebna licenca/provenance mapa i weather fajlova nije
  potvrđena; čuvati URL/commit/hash i izbjegavati redistribuciju sirovih podataka zasad.
- Same mape nisu dovoljne za tvrdnju o generalizaciji na drugi teren ili vremenske uslove.

## Preporučeni dataset/scenario plan

Korisnik je jasno odredio cilj: RL treba učiti u Firehose/Cell2Fire na scenarijima koji
predstavljaju stvarne pejzaže, gorivo, vrijeme i početna stanja požara. Zato ne koristimo
random toy mape kao glavni training distribution. Agentov reward i nove akcija–ishod
epizode ipak generiše simulator; historijski perimetri nisu etikete „dobre akcije“.

**Početna pilot konverzija:** CFSDS događaj `2018_747`, dani 15–16.08.2018. Odabrali smo ga
jer stane u postojeći 20×20 model i njegov mali prozor koristi samo FBP goriva C-3/D-1,
bez miješanog goriva kojem nedostaje simulator-parametar. Ulazi i rezultat su u
[case manifestu](../../reports/real-fire-data/2018_747-case.json),
[replay izvještaju](../../reports/real-fire-data/2018_747-day228-replay.json) i
[karti](../../reports/real-fire-data/2018_747-day228.png) i [šest-seed izvještaju](../../reports/real-fire-data/2018_747-seed-sweep.json).
Svih šest C++ no-action seedova dalo je istu završnu mapu od 66 ha novog opožarenog
područja prema opaženih 15.39 ha i dotaklo rub 2×2 km karte. Seedovi su mijenjali
trajanje, ne završnu mapu. Dvije dodatne 2018 train konverzije dale su 237 ha i 73 ha
prema opaženih oko 12 ha po danu; i one su dotakle rub. `2014_538` nije prošao FBP
fuel/water kompatibilnost. Ovo nije rezultat treniranja: sljedeće treba provjeriti
gorivo, vrijeme, model i prostor prije rada na politici.

Dogrib ostaje koristan formatni primjer, ali nije pilot ovog historijskog day-pair
pipelinea: njegovi podaci dijele dio terena s postojećim Firehose Sub20.

**Odabrani multi-event izvor za postojeći simulator:** CFSDS v1.1
day-of-burning rasteri. Svaki scenario se pravi od događaja/dana, historijskog FBP fuel
mapa, DEM-a, hourly ERA5-Land weathera i početne granice požara. Dnevni CFSDS raster
služi kao `day n` target za provjeru bez intervencije; RL rollout-i na tom pejzažu su
simulatorovi counterfactual-i. Raster je satelitski interpolisan i ne predstavlja tačan
satni front. Višepikselni initial-state importer sada postoji i provjeren je kroz jedan
stvarni pilot; glavna još nepoznata stvar je kvalitet no-action podudaranja. Kompletan
JSON-to-Cell2Fire field mapping je u
[REAL_CASE_PIPELINE](REAL_CASE_PIPELINE.md).

**Ako je glavni cilj Evropa/BiH:** FireSpread_MedEU sadrži 103 događaja i 320 ~3 m
koraka; prostorni pregled našao je sedam kandidata koji dodiruju BiH granicu. Najbolje
ocijenjeni lokalni primjer `EFFIS_id=205938` ima četiri dnevna koraka visoke kvalitete,
ali je oko 4.14×4.18 km. Manji primjer `43482` je 216.87 ha, ali mu je okvir 2.56×1.71 km.
Postojeći PPO pokriva 2×2 km; zato niži broj hektara sam po sebi ne garantuje da cijela
granica stane u prozor. Vidi [lokalni prostorni pregled](../../reports/real-fire-data/medeu-spatial-screen.json).
Prvo izabrati i provjeriti lokalno prikladan model goriva; ne preslikavati LCCS/CLC
landcover u C-1/C-2 bez fizičkog opravdanja. EFFIS-ov 250 m NFFL sloj je prostorno
uzorkovan preko dva završna događaja, ali nije isti gorivni sistem kao trenutni Canadian
FBP build. Sama v2 arhiva nema DEM ili satni weather;
pre-fire point zapis nije izmjerena stvarna tačka paljenja.

Za glavni eksperiment:

1. **Source/event manifest:** Canada + CFSDS/Canadian FBP je odabrani glavni pravac;
   44 kandidata iz trenutnog screening uzorka su podijeljena po cijelim događajima:
   20 train, 9 validation i 15 test. To su geometrijski kandidati, ne još završen
   fuel/weather kvalitetni benchmark. Izabrati godišnju FBP mapu, satelitski front,
   DEM, weather window i suppression flag po `event_id`. Za BiH:
   provjeriti EFFIS IDs iz prostornog pregleda, licencu za MedEU zip, high-resolution
   event bounds, regionalni fuel model i grid koji može obuhvatiti požar.
2. **Intermediate FireCase JSON:** event/date, CRS/transform, shape/cellsize, fuel/DEM/
   observed perimeter asset paths+hashes, weather series+units/timezone, initial-front
   construction, conversion log i event-level split group.
3. **Cell2Fire folder:** poravnati categorical fuel, DEM/slope/aspect, `Data.csv`, hourly
   `Weather.csv` i `InitialState.csv` za scar + multi-cell front; obični `Ignitions.csv`
   ostaje za slučaj jedne tačke. Kreirati no-action replay i porediti njegovu
   granicu sa skrivenim observed `day n`.
4. **Splits:** rasporediti cijele fire IDs u train/validation/test; nijedan crop ili
   drugi dan istog incidenta ne smije preći u drugu particiju. Kalibraciju raditi samo
   na train/calibration fire IDs.
5. **RL experience/evaluation:** simulator generiše transitions online; za svaku politiku
   zabilježiti istu mapu/front/weather/C++ seed/budžet, simulated damage, horizon,
   intervencije, checkpoint/hash i observed-boundary spread score.

Sljedeće je proširiti train-only CFSDS replaye, pregledati poravnanje fuel/DEM/weather
i prostor oko predviđenog rasta. Za BiH početi s MedEU `205938` (ili manjim `43482`)
samo poslije fuel-modela, licence i scale odluke. Tek kad više no-action train replaya
bude razumljivo, zamrznuti event-level heldout IDs i pokrenuti benchmark/fine-tuning.
Jedna Dogrib/CFSDS mapa ne pokazuje generalizaciju. Ne predstavljati kanadske FBP gorive
klase kao validaciju šumskih požara u BiH.

## Ponovi inventar

```sh
python3 scripts/inventory_firehose_dataset.py --root external/firehose/data/Sub20x20 --out runs/new-dataset-inventory.json
```

Skripta čuva hash svakog fajla, dimenzije, spatial alignment, weather brojnosti,
fuel lookup pokrivenost i missingness. Rezultati su ograničeni na pinovani Sub20x20,
ne predstavljaju inventar svih mapa autorskog repozitorija.
Ponovljeni inventar 2026-10-30 nakon ponovnog checkouta tačnog Firehose commita u
potpunosti odgovara sačuvanom `reports/firehose-verification/dataset-inventory.json`.
