# Stvarni požari: izbor podataka i granica zaključaka

Provjereno 2026-10-28. Ovo je izbor izvora i pregled malih uzoraka. Nismo još
validirali fiziku simulatora, izvršili historijski replay niti trenirali politiku na njima.

## Treba li nam takav dataset?

Za osnovno pitanje — da li prilagodba postojeće RL politike različitim budžetima
pomaže u odnosu na zamrznutu politiku i heuristike u istom simulatoru — nije strogi
preduslov. U dostavljenoj rubrici kvalitet podataka nosi 10%, ali nema izričitog
zahtjeva da podaci moraju biti opaženi stvarni požari. Priprema, porijeklo, provjere
i pošteni splitovi simulacijskih ulaza također zahtijevaju dokumentovanje.

Ipak preporučujemo mali historijski slučaj za provjeru veze simulatora sa stvarnošću.
Odvajamo tri stvari:

- **Ulazi okruženja:** gorivo, teren, vrijeme, početno paljenje. To smo ranije
  preširoko nazvali datasetom; sama postavka okruženja ne sadrži opaženi ishod požara.
- **Historijske reference:** zabilježena opožarena površina ili dnevni napredak,
  uz odgovarajuće ulaze. Koriste se za provjeru simulatora i granica njegove primjene.
- **RL iskustvo i evaluacija:** nastaju interakcijom sa simulatorom. Historijski
  požar nam ne daje oznaku najbolje intervencije ni ishod neke druge RL odluke.

Opaženi požari uključuju stvarne intervencije, nepoznate uslove i greške mjerenja.
Podudaranje sa njima samo po sebi ne dokazuje korist naše politike u stvarnom svijetu.

## Preporuka: Dogrib prvo, mali CFSDS podskup zatim

| Kandidat | Šta nudi | Uloga za nas | Provjera i pristup |
| --- | --- | --- | --- |
| [Dogrib 2001](https://github.com/humnetlab/Cell2Fire/tree/84e3c817ad866358d8db28e87c9445b42aaf7908/data/real/dogrib) | FBP gorivo, teren, weather, ignition i zaseban raster stvarne opožarene površine; 223×357 ćelija, 100 m | najbliži postojeće pripremljen historijski slučaj za Cell2Fire | preuzeto 16 odabranih fajlova, 3.39 MB; nisu preuzeti svi pripremljeni simulator inputi |
| [Canadian Fire Spread Dataset — CFSDS](https://osf.io/f48ry/) | satelitski izveden dnevni napredak kanadskih požara i okolišne varijable | širi izbor drugih požara za vanjsku provjeru nakon pripreme inputa | mali 2020 uzorak: 38 požara, 372 dnevna reda, dva ZIP-a ukupno 0.294 MB |
| [WildfireSpreadTS](https://zenodo.org/records/8006177) | dnevne višekanalne serije za 607 požara u SAD-u, 2018–2021; predikcija širenja za 24 h | dobra alternativa ako pitanje postane predikcija širenja; slabiji prvi izbor za sadašnji kontroler | samo pregled metapodataka; arhiva 48.4 GB nije preuzeta |

Za Dogrib su provjereni deklaracija MIT licence repozitorija i porijeklo originalnog
Prometheus/Alberta primjera; zasebni uslovi izvornih podataka nisu potvrđeni. Raw uzorak
ostaje lokalni. CFSDS OSF projekt i WildfireSpreadTS metapodaci navode CC-BY 4.0;
pri korištenju navesti autore, izvor, verziju i transformacije. Licenca naučnog članka
ne zamjenjuje provjeru licence podataka.

### Dogrib: korisna referenca, ali dijeli teren s našim inputom

[Kim, Pais i Gonzalez (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12254405/)
koriste Dogrib za poređenje Cell2Fire sa stvarnom opožarenom površinom. Njihova
kalibracija i objavljene metrike nisu naši rezultati niti potvrda našeg Firehose forka.

Naš pregled preuzetih fajlova je utvrdio:

- `real_scar_dogrib.csv` je opažena referenca: 10,210 označenih ćelija u rasteru
  223×357. Razdvojen je whitespaceom uprkos ekstenziji CSV.
- `prometheus_dogrib.csv` je izlaz drugog simulatora, odvojen zarezima. Njegov
  tačan vremenski prozor nije utvrđen; ne koristiti ga kao opaženu istinu.
- **663 označene opožarene ćelije poklapaju se s nonfuel kodom 101.** Potrebno je
  razjasniti rasterizaciju/klasifikaciju. Ne brisati ih radi boljeg rezultata; ako je
  opravdana maska, prikazati i cijeli domen i analizu osjetljivosti na maskiranje.
- Firehose `Sub20x20/Forest.asc` i `elevation.asc` identični su bloku pune mape
  `[0:20,20:40]`; slope/aspect nisu identični. Ovo je dokaz zajedničkog terena,
  pa Dogrib **nije nezavisan test prostorne generalizacije** postojeće politike.
- Sub20 ASC zadržava origin pune mape. Iz njegovog zaglavlja slijedio bi drugi
  blok (red 203, kolona 0), koji ne odgovara stvarnim vrijednostima. Zasad se ne
  oslanjati na taj origin za geografski smještaj ili automatsko izrezivanje labela.

Originalni [Dogrib_v624 README](https://github.com/humnetlab/Cell2Fire/blob/84e3c817ad866358d8db28e87c9445b42aaf7908/data/real/Dogrib_v624/Dogrib_v624_README.pdf)
(Neal McLoughlin, Government of Alberta, revizija 2019-02-03) opisuje ranije gašenje
i veliki nalet 16. oktobra 2001. Postoje perimetri za 16. oktobar 13:00 i 17. oktobar
11:52. Prije poređenja treba uskladiti početni perimetar, paljenje, weather varijantu,
vremensku zonu i završni trenutak; postoje i lokalne korekcije vjetra. Konačna
opožarena površina cijelog događaja ne smije automatski postati label za osmosatni run.

Puna mapa ima 79,611 ćelija. Naš checkpoint očekuje RGB 3×20×20 i 400 akcija;
ne može direktno upravljati ovom punom mapom. Prva historijska provjera je provjera
simulatora bez RL-a. Eventualni 20×20 izrez i njegove granične uslove treba posebno
definisati; to nije isto što i cjelovit replay događaja.

### CFSDS: pinovati izdanje, ne miješati članak i današnje fajlove

[Rad iz 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11239873/) opisuje izdanje sa
3,269 požara iz 2002–2021, većih od 1,000 ha, na 180 m. Datum gorenja procjenjuje se
interpolacijom MODIS/VIIRS detekcija; nije precizan zapis fronta iz minute u minutu.

Pregledani [OSF version record](https://osf.io/download/8fe4u/) navodi v1_1 od
2025-06-12: 90 m, požari >500 ha i dodane godine 2022–2024. Sadrži beta upozorenje
i bilješku o ispravkama topologije/interpolacija te ažuriranju point fajlova. Zato
pinujemo konkretne preuzete fajlove i provjeravamo događaje pojedinačno.

U odabranom uzorku za 2020 provjereno je:

- 38 rastera ima iste fire ID-jeve kao 372 reda dnevne tabele sa 60 kolona.
  Nema duplikata `(ID, DOB)`; dva reda nemaju BUI.
- GeoTIFF pixel scale je 90 m; NODATA je `4294967295`, nije dan gorenja.
- Pregledana dnevna tabela nema smjer vjetra. Sažeci goriva/biomase nisu potpuna
  prostorna FBP mapa prije požara. Trebaju dodatni gorivo/teren inputi na cijelom
  simulacijskom domenu i odgovarajuće vrijeme sa smjerom vjetra.
- Dnevna referenca može provjeravati dnevni/ukupni napredak, ne potvrđuje tačnost
  stanja na svakom osamminutnom koraku politike.

Godina 2020 izabrana je za mali pristup/schema check. Nije unaprijed zamrznut
test split niti dokaz kvaliteta svih CFSDS godina. Kasnije izabrati događaje koji
nemaju zajednički teren s Dogrib/Firehose mapama; nezavisnost potvrditi prostorno.

## Ograničeni naredni koraci

1. Završiti postojeći TASK-004c adapter; dataset istraživanje ga ne zamjenjuje.
2. TASK-011a: uskladiti Dogrib ulaze, perimetre i vremenski prozor, razjasniti nonfuel
   neslaganja i uslove podataka. Tek zatim kratak no-action replay i poređenje na
   istom domenu/vremenu: IoU/F1 opožarenog područja i greška površine, uz više seedova.
   Ako se bilo šta kalibriše na Dogribu, on je kalibracijski slučaj, ne holdout test.
3. TASK-011b: provjeriti izvedivost 3–5 drugih CFSDS požara s kompletnim inputima.
   Prije tuninga odvojiti kalibraciju i holdout po cijelim događajima; ne dijeliti
   susjedne piksele/dane istog požara u train i test. Ako inputi nisu dostupni u
   ograničenom naporu, ostaviti CFSDS kao dokumentovan budući rad.
4. Glavno poređenje politika ostaje upareno unutar kontrolisanih simulator scenarija.
   Odvojeno izvještavati vjerodostojnost simulatora i dobitak RL adaptacije.

## Lokalni dokazi i ponavljanje

- [Candidate manifest](../../data/manifests/real-fire-candidates.json): izvori,
  verzije, licence i granice pregleda.
- [Mali profili i download manifesti](../../reports/real-fire-data/README.md):
  URL, veličina i SHA256 svakog preuzetog fajla. Raw uzorci su ignorisani u
  `data/raw/dogrib-reference/` i `data/raw/cfsds-sample-2020/`.
- [Offline provjera](../../scripts/profile_real_fire_samples.py), izvršena s Python
  3.12.14, NumPy 2.3.5 i Pillow 12.3.0; traži oba raw uzorka i pinovani
  `external/firehose/data/Sub20x20/`. Nisu potrebni network, trening ili novi paketi
  ako se koristi postojeći bundled runtime. Iz repo roota:

```sh
python3 scripts/profile_real_fire_samples.py
```

Ne preuzimati cijeli WildfireSpreadTS ili dodatne gigabajte radi ove početne provjere.
