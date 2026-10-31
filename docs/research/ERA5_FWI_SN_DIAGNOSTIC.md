---
type: Research Note
title: ERA5-FWI-SN dnevni indeksi i kontrolisani replay tri TRAIN požara
---
# ERA5-FWI-SN dnevni indeksi i kontrolisani replay tri TRAIN požara

## Ukratko

Simulatoru nedostaju pouzdano opisani ulazni kodovi za opasnost od požara. Našli smo
kanadsku, javno objavljenu seriju šest dnevnih indeksa iz ERA5 reanalize: FFMC, DMC, DC,
ISI, BUI i FWI. Preuzeti su samo fajlovi za 2018. godinu; svi su provjereni prema
kontrolnim sumama kataloga. Originalni podaci ostaju lokalno u ignorisanom
`data/raw/era5-fwi-sn/v2/`.

Za tri već postojeća TRAIN slučaja napravili smo kopije simulator ulaza i promijenili
samo ovih šest dnevnih kodova. Satna temperatura, vlaga, vjetar, padavine, gorivo,
teren, početno stanje, seed i simulator ostali su isti. Novi FWI kod za taj dan je
ponovljen u svakom od 24 satna reda zato što izvor daje **dnevnu**, a ne satnu vrijednost.
To je tehnički ispravan način da se dnevna vrijednost unese u satnu tabelu; ne tvrdimo
da je ona mjerenje za svaki pojedinačni sat.

Tri uparene simulacije su uspjele. U dvije završna mapa požara nije se promijenila; u
trećoj se smanjila za tri model-ćelije, odnosno 3 ha. Sve tri i dalje dodiruju rub
modelskog izreza. Dakle, novi izvor je upotrebljiv i bolje dokumentovan, ali **nije
riješio veliko neslaganje simulacije s opaženim požarom**. To je korisno otkriće: stari
FWI kodovi nisu sami objašnjenje zašto simulator širi vatru previše.

## Izvor i način uzorkovanja

Korišten je [ERA5-FWI-SN](https://doi.org/10.5683/SP3/4B18XZ), Borealis izdanje v2,
uz metodološki opis u [Benoit et al. 2026](https://doi.org/10.5194/essd-18-5995-2026).
Indeksi su dnevni, izračunati iz satne ERA5 meteorologije oko lokalnog solarnog podneva,
na mreži od 0.25° odnosno približno 31 km. Rad izvještava medijansku korelaciju 0.81 s
kanadskim CWFIS mjerenjima za period 2015–2024; autori takođe navode da je prostorno
usrednjavanje zagladilo neke ekstremne vrijednosti.

Za svaki slučaj uzeta je najbliža ERA5-FWI-SN ćelija do unaprijed rekonstruisane,
target-blind lokacije day n−1 početnog fronta. Udaljenost je 7.986 km, 13.501 km i
11.130 km. To je bliže i jasnije definisano od preuzimanja prosjeka iz CFSDS dnevnog
sažetka, ali ćelija od oko 31 km je i dalje mnogo veća od simulatorovog izreza od 2 km.

| TRAIN slučaj / ciljni dan | Predikcija sa starim kodovima | Sa ERA5-FWI-SN | Promjena | IoU stari → novi | Rubne ćelije stari → novi |
| --- | ---: | ---: | ---: | ---: | ---: |
| `2018_1770` / 12.08.2018. | 73 ha | 70 ha | −3 ha | 0.1361 → 0.1418 | 26 → 25 |
| `2018_241` / 15.08.2018. | 237 ha | 237 ha | 0 ha | 0.0376 → 0.0376 | 62 → 62 |
| `2018_747` / 16.08.2018. | 66 ha | 66 ha | 0 ha | 0.2187 → 0.2187 | 19 → 19 |

Opaženi CFSDS rast je približno 12–15 ha po slučaju. U sva tri uparena replaya simulator
i dalje zahvata znatno više područja i nastavlja do ruba 20×20 mreže. Rezultati su jedan
seed po slučaju i služe samo poređenju ulaznog izvora; to nije podešavanje modela,
validacija fizike ili test uspješnosti agenta.

## Šta je sada riješeno, a šta nije

**Riješeno za ove tri dijagnostičke kopije:** poznat je javni izvor šest dnevnih FWI
kodova, tačan najbliži raster piksel, njegove vrijednosti i kontrolne sume. Sačuvani su
reproducibilni skripti za provjeru preuzetih fajlova, pripremu kopija i provjeru uparene
simulacije. Raniji FireCase-i nisu mijenjani.

**Nije riješeno:** za ta tri požara ostaju nepoznati ili nepotpuni podaci o gašenju,
istorijsko gorivo na datum požara nije dokazano, a ciljna CFSDS mapa ne pokazuje tačan
sat kada je svaka ćelija izgorjela. Sve tri simulacije dodiruju rub malog izreza, pa
lokalna mapa ne predstavlja otvoren prostor oko požara. Ovo su različiti problemi i novi
vremenski kod ih ne može sam popraviti.

Sada postoji i potencijalno bolji put za izbor nekih budućih TRAIN primjera: službeni
[Alberta istorijski dataset](https://open.canada.ca/data/en/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e)
opisuje vatrogasne resurse i podatke o prvom fizičkom suzbijanju, a njegov
[rječnik podataka](https://open.alberta.ca/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e/resource/1b635b8b-a937-4be4-857e-8aeef77365d2/download/fp-historical-wildfire-data-dictionary-2006-2025.pdf)
navodi vrijeme početka borbe protiv vatre. To bi moglo omogućiti provjeru da li je
konkretan ciljni dan bio prije prve fizičke intervencije. Taj CSV u ovom radnom
okruženju trenutno vraća HTTP 403, pa još nismo mogli spojiti nijedan Alberta događaj s
CFSDS-om. To **ne** mijenja stanje tri postojeća BC događaja.

## Reprodukcija i ograničenja

- [Mašinski čitljiv replay receipt](../../reports/real-fire-data/era5-fwi-sn-2018-weather-replay-comparison.json)
  sadrži uparene hashove, parametre i metrike.
- [Audit NetCDF vrijednosti](../../reports/real-fire-data/era5-fwi-sn-2018-pilot-comparison.json)
  čuva vrijednosti, raster koordinate, kontrolne sume i licencu.
- `scripts/audit_era5_fwi_sn_pilots.py` provjerava lokalne NetCDF fajlove i izvlači dnevne indekse.
- `scripts/prepare_era5_fwi_sn_replay_inputs.py` pravi samo ignorisane kopije ulaza.
- `scripts/compare_era5_fwi_sn_replays.py` provjerava da su satni meteorološki podaci i
  svi ostali ulazi ostali isti te sastavlja replay receipt.
- Sirovi NetCDF i detaljni simulator izlazi ostaju ignorisani u Gitu; tim može ponoviti
  postupak preuzimanjem samo 2018 fajlova iz Borealis kataloga.

Replay koristi izolovani, mrežno isključen `wildfire-firehose-probe:20261030-real-case`
container. Nije bilo treninga, kalibracije, promjene policy-ja, izmjene starih slučajeva
niti pristupa validation/test ciljevima. **Ukupni no-action gate ostaje FAIL, a
`research_ready=false`.**
