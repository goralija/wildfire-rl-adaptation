# Dataset: šta imamo i šta ćemo koristiti

**Postavka okruženja i dataset opaženih požara su različite stvari.** Početni Firehose
fajlovi su ulazi za simulaciju; agent interakcijom stvara RL iskustvo. Oni sami nisu
skup stvarnih ishoda niti oznaka ispravnih intervencija. Sada su zasebno preuzeti i
pregledani mali Dogrib/CFSDS historijski uzorci. Preporuka i ograničenja su u
[REAL_FIRE_DATASETS](REAL_FIRE_DATASETS.md). Konačna uloga, izbor i obim još nisu
usaglašeni; TASK-012 dataset refinement je neposredni sljedeći korak.

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
| `Ignitions.csv` | izvorni input navodi 381; provjera modela koristi 372 | mjesto paljenja, indeks od jedan |
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

## Planirani istraživački dataset

1. **Scenario inputs:** mapa + weather trace + ignition + simulator seed + priority maska.
   Svaka kombinacija dobija scenario ID, porijeklo, transformacije i hash.
2. **Train/validation/test manifesti:** odvojene kombinacije ignition/weather i po
   mogućnosti odvojene mape. Samo promjena seeda na istoj mapi/weather nije dokaz
   prostorne ili meteorološke generalizacije. Test manifest se zamrzava prije tuninga.
3. **RL iskustvo:** (opažanje, akcija, nagrada, sljedeće opažanje, done/reason), nastaje
   u simulatoru. PPO koristi rollout buffer; ne mora čuvati sav trening kao offline dataset.
4. **Evaluacijski dataset:** po scenariju i politici čuvamo damage, priority damage,
   intervencije, horizon/reason, seedove, runtime i identitet checkpointa. Iz toga nastaju
   krive šteta/budžet i intervali.

Početak je ova mala postojeća mapa; zatim proširujemo scenarije nakon provjere
adaptera. Preporučen dodatak je ograničena historijska provjera simulatora: Dogrib kao
početni povezani slučaj, zatim mali nezavisni CFSDS podskup ako kompletni inputi budu
izvedivi. To nije uslov da uopšte počnemo RL poređenje niti dokaz koristi intervencija
u stvarnom svijetu. Regionalni BiH GIS i velika kampanja označavanja nisu u sadašnjem obimu.

## Ponovi inventar

```sh
python3 scripts/inventory_firehose_dataset.py --root external/firehose/data/Sub20x20 --out runs/new-dataset-inventory.json
```

Skripta čuva hash svakog fajla, dimenzije, spatial alignment, weather brojnosti,
fuel lookup pokrivenost i missingness. Rezultati su ograničeni na pinovani Sub20x20,
ne predstavljaju inventar svih mapa autorskog repozitorija.
