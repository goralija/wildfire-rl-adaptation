---
type: Dataset Review
title: 'Stvarni požari: izbor podataka i granica zaključaka'
sources:
- resource: /data/manifests/real-fire-candidates.json
- resource: /reports/real-fire-data/dogrib-profile.json
- resource: /reports/real-fire-data/cfsds-sample-profile.json
---
# Stvarni požari: izbor podataka i granica zaključaka

Provjereno 2026-10-30. CFSDS v1.1 + Canadian FBP/Cell2Fire je odabrana glavna
putanja jer se najbolje uklapa u već postojeći simulator i kontroler. Tri train slučaja
su pretvorena i izvršena bez intervencija; za jedan slučaj urađeno je šest seedova.
Fizika simulatora nije time validirana i politika nije trenirana na historijskim podacima.

## Status: Canada + CFSDS odabrani; pilot konverzija/replay izvršeni

Korisnik je odobrio da se izabere najbolja kompatibilna putanja bez geografskih
ograničenja. Odabrali smo kanadski CFSDS jer njegov FBP model odgovara postojećem
Cell2Fire-u. Historijski inputi daju realističnije karte goriva, teren, vrijeme i
početna stanja; agentov trening i dalje dobija nagradu iz novih simulator rollouta,
ne iz historijskih labela intervencija. Event split i screening su napravljeni, ali
potrebno je još fuel-vintage i vremensko poravnanje prije zamrzavanja punog benchmarka.
Tri train slučaja (`2018_747`, `2018_241`, `2018_1770`) su pretvorena i replayana; vidi
[pipeline i X/Y objašnjenje](REAL_CASE_PIPELINE.md).

| Dio | Šta imamo | Šta ostaje otvoreno |
| --- | --- | --- |
| Simulator inputi | pinovan Sub20 teren/gorivo/weather inventar i izvršeni rollouti | ispraviti geografsku registraciju, ignition i podatkovne nedosljednosti |
| Historijski podaci | CFSDS v1.1, 44 preliminarna kandidata; tri train slučaja su konvertovana, a `2014_538` je pao na water/nonfuel checku | napraviti per-cell fuel/weather QC; osigurati 2019/2024 FBP vintages i suppression status |
| RL iskustvo | postojeći simulator i stari checkpointi rade; tri no-action train replaya izvršena su na real-derived mapama | prvo proći no-action/calibration gate; zatim generisati agent rollout-e kroz više slučajeva/seedova |
| Evaluacija | `2018_747`: šest seedova, 66 ha/15.39 ha; `2018_241`: 237 ha/12.15 ha; `2018_1770`: 73 ha/12.15 ha; svi dotiču rub | razumjeti input/model neslaganje i extent prije zamrzavanja holdouta i poređenja politika |

**Odabrana putanja:** Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire. Time se zadržava
postojeći simulator i postojeći 20×20 agent, a historijska serija pokriva više stvarnih
požara. BiH/MedEU ostaje moguća kasnija odvojena studija, ali traži drugi fuel/spread
model i drugačiju veličinu karte.

- **Ako zadržimo postojeći Canadian FBP/Cell2Fire**, CFSDS v1.1 je najkompatibilniji
  kandidat za više nezavisnih događaja. Daje dnevne kanadske granice, a njegove fuel
  mape i W.I.S.E. rad koriste Canadian FBP. I dalje moramo pripremiti fuel/DEM/weather,
  ispraviti početno stanje i ograničenje 20×20.
- **Ako je važnije da priča bude o BiH**, FireSpread_MedEU v2 je bolja historijska
  progresijska osnova: iz lokalno preuzetog 2.8 MB poligonskog fajla, prvi overlay sa
  Natural Earth granicom našao je 7 kandidata koji dodiruju BiH granicu:
  EFFIS IDs `12321`, `13228`, `22108`, `25244`, `25274`, `43482`, `205938`. Ovo je
  kandidat-pretraga, ne potvrđena nacionalna selekcija; prije izbora provjeriti event
  lokacije s preciznom granicom i EFFIS zapisom. Detaljni metapodaci i hashovi su u
  [spatial-screen izvještaju](../../reports/real-fire-data/medeu-spatial-screen.json).
  Događaj `205938` ima četiri uzastopna dnevna koraka (15–18. juli 2022), sve označene
  „very high“, pa je dobar početni *historijski referentni slučaj*. Ali puni obuhvat je
  oko 4.14×4.18 km, veći od postojećeg 2×2 km agenta. Manji događaj `43482` ima završnu
  površinu 216.87 ha, ali mu je bounding extent 2.56×1.71 km; površina manja od 400 ha
  zato ne garantuje da stane u agentov kvadrat. EFFIS-ova 2017 karta daje gorivni sloj
  od 250 m: uz konačni poligon 205938 vidi se mješavina NFFL kodova 4/5/9 i no-data;
  43482 uglavnom kod 3. To su regionalne kategorije, ne terenska mjerenja.

MedEU i dalje nije gotov simulator set: geometrije su granice, LCCS su udjeli pokrova,
a ne Firehose fuel codeovi; u paketu nema DEM-a ni satnog historijskog vremena. Za BiH
smo našli zaseban EFFIS European Fuel Map iz 2017. (250 m, NFFL/Anderson modeli 1–10),
ali postojeći Firehose C++ build je kanadski FBP. Ne preimenovati evropske kodove u
kanadske. Potrebno je odabrati/validirati simulator koji podržava odgovarajuće NFFL
gorivo ili napraviti opravdan crosswalk i kalibrisati ga na odvojenim događajima. EFFIS
navodi CC BY 4.0 za EU-owned web sadržaj osim posebnih izuzetaka; provjeriti slojsku
napomenu i obavezno navesti izvor/promjene. MedEU Zenodo v2 nema jasan dataset-license
field, pa prava na taj ZIP posebno potvrditi. FIRE-RES server/paper je još jedan mogući
izvor usklađenih 100 m evropskih gorivnih/terrain slojeva i Scott–Burgan modela; tačnu
BiH pokrivenost, izvoz i uslove upotrebe treba prvo provjeriti. FHMZ BiH koristi kanadski
FWI za opasnost, ali to ne znači da je Canadian FBP gorivo/širenje lokalno validno.

Za globalnu pokrivenost postoji GlobFire, ali je grublji i ne daje simulator inpute.
Dogrib je dobar formatni primjer, ali samo jedan događaj i dijeli teren s postojećim
Sub20. Lokalni Cell2Fire adapter sada prima višepikselno početno stanje i provjeren je
na fixtureu i pilotu `2018_747`. Trening rollout-i se dešavaju u
simulatoru; opažene granice su zaseban reality-check, ne akcijske oznake.
[Pipeline detalji i predloženi JSON](REAL_CASE_PIPELINE.md).

## Preporuka nakon istraživanja — 2026-10-30

### Šta da zovemo „datasetom“

U ovom projektu postoje tri različite vrste podataka:

1. **Ulazi simulacije:** mapa šume, gorivo, teren, vrijeme i mjesto početnog paljenja.
   Oni definišu uslove u kojima se požar simulira.
2. **RL iskustvo:** nizovi opažanje–akcija–ishod koje agent sakupi dok radi u simulatoru.
   Ovo je glavni izvor treninga za pitanje o budžetskoj adaptaciji.
3. **Historijske reference:** opažene ili satelitom procijenjene površine i napredak
   stvarnih požara. One mogu pomoći procijeniti ponašanje simulatora, ali ne govore
   šta bi se desilo da je RL agent odabrao neku drugu intervenciju.

Historijski landscape, vrijeme i početno stanje mogu biti osnova za stvarne Firehose
trening-scenarije. Ali opažene granice požara nisu oznake dobrih ili loših akcija. Učenje
se i dalje odvija online u simulatoru, na više početaka/seedova izvedenih iz slučajeva;
historijski nastavak požara služi za provjeru rasta bez intervencije, odvojeno od
kontrafaktualnog poređenja politika.

### Preporučeni obim projekta

| Uloga | Preporuka | Zašto | Granica zaključka |
| --- | --- | --- | --- |
| Formatni primjer | Dogrib 2001 u Cell2Fire FBP formatu | Ima stvarne gorivne/terrain slojeve i literature primjere; dobar za provjeru raster→Cell2Fire formata. | Nije nezavisan holdout; Sub20 dijeli isti teren, a origin/slope/aspect/ignition trebaju provjeru. |
| Glavna real-derived distribucija za postojeći simulator | CFSDS v1.1 + odgovarajući FBP/DEM/weather i 20×20 isječci | Najbolji fit postojećem kanadskom FBP sistemu i donosi mnogo različitih kanadskih slučajeva; jedan slučaj je već pretvoren i replayan. | Dnevne granice su interpolirane; pilot je znatno prerastao opaženi cilj i dotakao ivicu karte. Potrebni su kalibracija/bolji extent i još slučajeva. |
| Lokalni BiH historijski referent | MedEU opažene granice + EFFIS NFFL 250 m gorivna karta + regionalni fire-spread model | Sedam prvih događaja dodiruje BiH; 205938 ima četiri uzastopna dnevna koraka very high kvalitete; završni poligon ima EFFIS gorivne kodove. | NFFL karta nije kompatibilna s postojećim kanadskim FBP buildom; MedEU ZIP licenca/lokacije treba potvrditi; 205938 je 4.14×4.18 km, veći od 20×20/100m agenta. |
| Globalni/coarser fallback | GlobFire v2 daily perimeters + regionalni vegetation/DEM/weather | Globalna pokrivenost 2001–2021; događaji se mogu uzorkovati po regionu gdje lokalne baze nisu dovoljno dostupne. | 500 m MODIS MCD64A1; nekoliko dana vremenske nesigurnosti; nema input paketa gorivo/teren/weather i 5× je grublji od simulatorove 100 m grid-e. |
| RL rollout-i | Online simulacije na konvertovanim slučajevima; frozen/fine-tuned/baseline dobijaju iste početke, vremenske nizove, seedove i budžete | Simulator sam računa ishode za kontrafaktualne akcije. | Zaključak ostaje vezan za model, njegove apstraktne ćelijske akcije i izabrane scenarije. |
| Historijski replay/evaluacija | Opaženi perimetar `day n-1` je početno stanje, `day n` je skriveni target | No-action simulacija provjerava da li model prati realni rast bez intervencije. | Za dnevni front treba simulator state importer; vremenske oznake, suppression i rezolucija nose neizvjesnost. |

Firehose rad koristi 20×20/400 akcija; autori navode teže random-ignition taskove i
sample-efficiency izazove na 40×40/1600 akcija. Cell2Fire paper opisuje 20×20 i 40×40
Dogrib sub-instance. Prvo zadržati 20×20 za end-to-end converter, a potom izmjeriti da li
je pokrivenost preuska; 40×40 checkpointi postoje, ali nisu dio izvršene 12-case provjere.
Originalni okvir definiše akciju kao trajni tretman ćelije, a epizoda završava kad se
vatra ugasi **ili** kad ponestane weather inputa. Naš adapter zato mora razlikovati
ta dva kraja prije nego što tvrdimo da je došlo do containmenta. [Firehose rad i opis
akcije/simulacije](https://williamshen-nz.github.io/firehose/firehose-paper.pdf).

### Zašto CFSDS nije „gotov simulator dataset“

CFSDS v1 iz rada iz 2024. sadrži 3,269 požara iz 2002–2021. na 180 m; opisuju se
interpolirane dnevne procjene dana gorenja iz MODIS/VIIRS detekcija, uz okolišne
varijable. Izdanje v1.1, pregledano u OSF verzionom zapisu, navodi 90 m i godine
2022–2024. Novija nezavisna procjena W.I.S.E. navodi ukupno 5,435 požara u v1.1,
ali za svoj izvršiv test smanjila je obim na 2,210 požara iz 2014–2024. i 19,848
uzastopnih dnevnih parova: bili su potrebni kompatibilni FBP slojevi; za njihov no-action
benchmark izbačeni su požari sa zabilježenom intervencijom, ne-susjedni dnevni perimetri,
spot-fire slučajevi i problematična/nonfuel područja. I dalje su potrebni vremenski
odgovarajuće gorivo, teren, prethodno opožarena mapa, vrijeme i front/paljenje. Njihov
pripremljeni pair set se daje na razuman zahtjev, ali javne CFSDS/FBP/DEM/weather inpute
možemo sastaviti i pravila reprodukovati. To je najbolji pronađeni multi-fire izvor, ali
broj „hiljade požara“ ne znači da možemo odmah pokrenuti hiljade Firehose epizoda.
[Barber et al. CFSDS](https://doi.org/10.1038/s41597-024-03436-4),
[Bennett et al. (2026), CFSDS v1.1 benchmark](https://doi.org/10.1071/WF26072).

### FireSpread_MedEU: jači evropski perimetri, drugačiji fuel model

[FireSpread_MedEU v2](https://zenodo.org/records/18200075), objavljen 2026, nudi
103 evropska/mediteranska događaja iz 2017–2023 i 320 rekonstruisanih propagation
koraka iz Planet satelitskih slika, oko 3 m prostorne rezolucije. Autori su granice
ručno pregledali/dotjerali; 63% koraka je dnevno, a ostali mogu imati preskočene dane
zbog oblaka, dima ili satelitske pokrivenosti. Uključeni su predpožarni datumi,
obrazloženje nedostajućih datuma, kvalitetna procjena i povezani EFFIS ID.
To je kvalitetniji real-world progresijski signal nego široki CFSDS, ali nije gotov
Cell2Fire set: zip daje perimetre i LCCS landcover udjele, ne gotov kanadski FBP raster,
DEM ni satni vremenski niz. Zenodo v2 record pokazuje „Open“, ali ne prikazuje jasan
dataset license field; provjeriti uslove prije distribucije ili ozbiljnije upotrebe.
[Dataset i schema](https://zenodo.org/records/18200075),
[recenzirani Data Descriptor](https://doi.org/10.1038/s41597-026-06965-2).

**Praktičan izbor:** najbrži put uz postojeće pretrained agenta je Canada + CFSDS +
Canadian FBP. BiH putanja sad ima konkretne izvore za opažene granice i gorivo (MedEU +
EFFIS), ali zahtijeva drugi ili prošireni fire-spread model, licencnu/lokacijsku provjeru,
veći grid i novi adapter; težine se ne prenose automatski. Ne pretvarati NFFL/FAO/CLC
„šumu“ mehanički u kanadski `C-2`/`C-3`: fuel modeli predstavljaju strukturu goriva i
empirijsku fiziku, a ne samo opći tip zemljišta.

### GlobFire / Global Fire Atlas: globalni događaji, grublja satelitska mjera

[GlobFire v2 DailyPerimeters](https://developers.google.com/earth-engine/datasets/catalog/JRC_GWIS_GlobFire_v2_DailyPerimeters)
je globalni MODIS MCD64A1 fire-event skup za 2001–2021 s nominalnim dnevnim granicama,
500 m gridom i deklarisanom CC-BY-4.0 licencom. GWIS objašnjava da događaje sklapa iz
burn-date proizvoda i da početni/završni datumi imaju nekoliko dana neizvjesnosti.
To je korisno za regionalnu analizu požara kad treba globalna pokrivenost, ali 500 m
labelu ne treba lažno predstaviti kao 100 m opažanje ili satni front. Uz to i dalje
trebaju tačni fuel/terrain/weather ulazi i multi-cell initial-state podrška. Ako imamo
izbor, CFSDS je bolji Canadian FBP trening/test kandidat; MedEU je bolji za detaljne
evropske reference; GlobFire je broad-coverage fallback.
([GWIS opis](https://gwis.jrc.ec.europa.eu/about-gwis/technical-background/statistics),
[Global Fire Atlas paper](https://doi.org/10.5194/essd-11-529-2019)).

Ta procjena poredi dnevne simulirane perimetre s procijenjenim dnevnim perimetrima.
Podrazumijevani W.I.S.E. benchmark imao je prosječni F1 0.259; „najbolji“ dijagnostički
slučaj s optimizacijom trajanja gorenja i smjera vjetra imao je F1 0.539, ali koristi
informaciju podešenu prema ciljanom danu. Ovo **nije** Firehose rezultat, ni direktno
poređenje naših RL politika; nalaz služi kao upozorenje da historijska simulacija
zahtijeva kalibraciju i da preciznost inputa ograničava validaciju.

### Ulazni ugovor i scenario ID

Za glavni benchmark svaki scenario mora biti ponovljiv i prepoznatljiv. Predloženi ID
uključuje: `map_id + ignition_cell + weather_trace_id/hash + cpp_seed + priority_mask_id/hash`.
Uz svaki scenario čuvati izvor i verziju fajlova, licencu/provenance status, transformacije,
CRS/cellsize gdje su poznati, hashove i objašnjenje train/validation/test uloge. Sam seed
nije dovoljan ako su ignition/weather fiksni ili simulator ignoriše seed.

Prije zamrzavanja scenarija riješiti četiri konkretne provjere iz postojeće mape:

- `Ignitions.csv` navodi 381, dok je postojeća inference provjera koristila 372;
  to nisu isto mjesto niti off-by-one: uz one-based row-major indeks 381 je red 20,
  kolona 1 (O-1a), a 372 je red 19, kolona 12 (C-2). Oba su goriva; treba utvrditi
  koju početnu lokaciju predviđeni benchmark zaista želi.
- zadnji `Data.csv` red ima 19 polja naspram 20 u ranijim redovima;
- Sub20 raster zaglavlje ima cellsize 100, ali CRS/jedinice i geografski origin nisu
  pouzdano potvrđeni;
- 129 alternativnih weather fajlova imaju nepoznato porijeklo/generisanje i format datuma.

Do provjere koristimo samo weather fajl čiji se format i stvarna upotreba mogu potvrditi.
Ne uključujemo 129 varijanti u train/test samo zato što su prisutne. Njihov sadržaj
treba validirati, razvrstati po generativnom izvoru i provjeriti raspon/distribuciju.
Ne mijenjamo raw upstream fajlove da prikrijemo parser ili provenance problem.

Scenario split mora biti po **scenarijima**, ne samo po trening seedu. Zadržati postojeće
32/12/30 seedove kao prijedlog za training/validation/test kontrolu tek kad je potvrđeno
da su seedovi proslijeđeni u C++ i mijenjaju realizaciju. Glavni evaluacijski test treba
zamrznuti prije tuninga. Ako ostane jedna mapa, odvojiti kombinacije weather/ignition
i seed, ali rezultate nazvati upareno poređenje na jednoj mapi; ne tvrditi prostornu
generalizaciju. Predloženi minimum iz protokola — 3 trening seeda × 30 test scenarija
× budžeti {2,4,8,16} — ostaje plan koji se tek nakon mjerenja brzine može smanjiti
ili prihvatiti.

### Okruženja i priprema podataka

Ne pravimo jedno zajedničko Python okruženje. Repo podržava tri jasna sloja:

| Sloj | Namjena | Status i sljedeća provjera |
| --- | --- | --- |
| Moderni project `.venv`, Python ≥3.11 | Core, GIS pretprocesiranje, ERA5 NetCDF/weather i analize | Python 3.12.4/macOS ARM64 spreman s `.[rl,geo]`; rasterio/geopandas/pyproj/xarray/rioxarray/netCDF4/CDS API import i raster reprojection smoke su prošli. |
| Optional modern RL | Gymnasium/SB3 za sintetički/projektni pipeline smoke | PPO smoke je prošao, ali nije Firehose fine-tune. |
| Legacy Firehose Docker | Python 3.8, Gym 0.21, SB3/contrib 1.5 i PyTorch za težine | Build i 12 inference provjera su prošli na Linux ARM64; ovdje će se izvršavati Firehose rollout-i. |

Raw/georeferencirani slojevi ostaju ignorisani; verzije/URL/hashovi i transformacije
ostaju u Git manifestu. Za CFSDS koristiti odgovarajuće historical map vintage 2014,
2019 ili 2024 umjesto današnje karte bez provjere; W.I.S.E. metode koriste godišnje
burn-scar maske i succession pravila. 2026 30 m karta je aktuelna alternativa, ne
automatska historical input mapa. [CWFIS FBP fuel maps](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/).

## Opcije koje sada ne preporučujemo

- **Ne trenirati Firehose politiku direktno na CFSDS/Dogrib opaženim ishodima.** Ti
  ishodi ne sadrže kontrafaktualnu oznaku uspješnosti naših mogućih akcija.
- **Ne stavljati puni Dogrib grid u 20×20 checkpoint.** Puna mapa je 223×357, a
  postojeći checkpoint vraća jednu od 400 ćelija. Isječak/promjena rezolucije zahtijeva
  novu, eksplicitnu definiciju domena i ne smije se zvati nezavisnim holdoutom.
- **Ne mijenjati backend u SimFire ili 40×40 model samo radi većeg dataseta.** To
  odbacuje provjereni checkpoint/akcijski kontrakt i traži novi benchmark/compute plan.
- **Ne preuzimati cijeli WildfireSpreadTS (48.4 GB).** Njegov fokus je dnevna prognoza
  širenja u SAD-u, ne Cell2Fire budget-control; za sada ima slab fit i visok trošak.
- **Ne koristiti samo finalne Alberta perimetre kao vremenski niz širenja.** Službeni
  portal nudi historijske perimetre i zapise, ali je GIS pristup kroz AGSP ograničen
  na verificiran Alberta nalog, a finalni obris ne daje dnevni front sam po sebi.
  [Alberta wildfire maps and data](https://www.alberta.ca/wildfire-maps-and-data).

## Predloženi naredni taskovi

1. **TASK-012 izbor puta — završen:** Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire.
   Izbor odgovara postojećem simulatoru, agentu i dostupnom višegodišnjem izvoru.
2. **TASK-014 GIS setup:** moderni project `.venv`, GIS/network data libraries, synthetic
   PPO smoke i legacy Docker/inference su lokalno pripremljeni. Environment receipt
   navodi tačne GIS pakete nakon instalacije; drugi OS/arch nije provjeren.
3. **TASK-015 — djelimično završen:** ekranirati 44 kandidata iz po najviše pet slučajeva
   godišnje; podijeljeni su po događajima u 20 train, 9 validation i 15 test. Ovaj spisak
   nije iscrpan i nije finalni benchmark. Za širenje na 2019–2024 treba odgovarajuće
   nacionalne FBP fuel mape iz 2019. i 2024. i potpunu provjeru vremena/suppressiona.
4. **TASK-017 — prvi adapter završen:** `InitialState.csv` uvozi raniji scar i više
   aktivnih ćelija; provjeren je na fixtureu i na stvarnom CFSDS ulazu. TASK-004c je
   naknadno završio cumulative-damage/front export i terminalni razlog;
   [adapter receipt](../../reports/firehose-verification/task004c-adapter-smoke.json).
5. **TASK-016 — tri train konverzije izvršene:** FireCase JSON, GIS ulazi i C++ no-action
   replays rade; za `2018_747` šest seedova daje istu završnu mapu. Sva tri slučaja
   predviđaju previše širenja i dotiču rub. `2014_538` je odbijen na water/nonfuel checku.
   Naredno provjeriti gorivo, FWI/weather, FBP parametre, suppression i veličinu domene.
6. **TASK-005/006 — na čekanju gatea:** ne pokretati glavno treniranje dok više train
   replaya ne pokaže dovoljno stabilno ponašanje i dok se event-level test lista ne
   zaključa. Zatim porediti frozen/fine-tuned/heuristike pod istim događajima, seedovima
   i budžetima; test ID-jeve ne koristiti za kalibraciju.

Preostali rok, obim, raspodjela rada i računarski budžet nisu usaglašeni.

## Zašto su nam stvarni događaji potrebni u ovom projektu

Za samu tehniku budget adaptationa dovoljan bi bio kontrolisan benchmark simulatora.
Ali korisnik sada izričito želi pokazati rad na uslovima izvedenim iz stvarnih požara,
zato real-derived scenario set i historijski check ulaze u ovaj zadatak. To i dalje ne
znači da model učimo na požaru kao na odgovoru: razdvajamo tri stvari:

- **Ulazi okruženja:** gorivo, teren, vrijeme, početno paljenje. To smo ranije
  preširoko nazvali datasetom; sama postavka okruženja ne sadrži opaženi ishod požara.
- **Historijske reference:** zabilježena opožarena površina ili dnevni napredak,
  uz odgovarajuće ulaze. Koriste se za provjeru simulatora i granica njegove primjene.
- **RL iskustvo i evaluacija:** nastaju interakcijom sa simulatorom. Historijski
  požar nam ne daje oznaku najbolje intervencije ni ishod neke druge RL odluke.

Opaženi požari uključuju stvarne intervencije, nepoznate uslove i greške mjerenja.
Podudaranje sa njima samo po sebi ne dokazuje korist naše politike u stvarnom svijetu.

## Kandidati za real-derived scenario skup / historijski reality-check

| Kandidat | Šta nudi | Uloga za nas | Provjera i pristup |
| --- | --- | --- | --- |
| [Dogrib 2001](https://github.com/humnetlab/Cell2Fire/tree/84e3c817ad866358d8db28e87c9445b42aaf7908/data/real/dogrib) | FBP gorivo, teren, weather, ignition i zaseban raster stvarne opožarene površine; 223×357 ćelija, 100 m | opcion, vremenski poravnat simulator sanity-check; nije nezavisan prostorni holdout zbog zajedničkog terena s Sub20 | preuzeto 16 odabranih fajlova, 3.39 MB; nisu preuzeti svi pripremljeni simulator inputi |
| [Canadian Fire Spread Dataset — CFSDS](https://osf.io/f48ry/) | satelitski izveden dnevni napredak kanadskih požara i okolišne varijable | najbolji match za širi real-derived skup ako ostajemo na Canadian FBP simulatoru; prvo 3 događaja | mali 2020 uzorak: 38 požara, 372 dnevna reda, dva ZIP-a ukupno 0.294 MB; day-pair replay traži multi-cell state importer |
| [FireSpread_MedEU v2](https://zenodo.org/records/18200075) | 103 događaja iz Evrope/Mediterana, 320 ~3 m ručno pregledanih Planet-satellite progression koraka, 2017–2023; naš prvi BiH overlay daje 7 ID kandidata | detaljni progresijski izvor za BiH; može se prostorno spojiti s EFFIS European Fuel Map | ZIP 2.8 MB; 205938 extent 4.14×4.18 km i 20×20/100m agentu je premalen; 63% koraka daily; nema DEM/hourly weather; ZIP license field nije prikazan; EFFIS gorivo je NFFL, a naš build FBP-Canada |
| [EFFIS European Fuel Map](https://forest-fire.emergency.copernicus.eu/about-effis/technical-background/fuels) | evropska NFFL/Anderson fuel klasifikacija; naš preuzeti sloj iz 2017. je 250 m EPSG:3035 i pokriva MedEU kandidate | konkretan regionalni gorivni sloj; overlay pokazuje da se kategorije mogu uzorkovati preko stvarnih poligona | nije terenski inventar; ne daje DEM/vrijeme; model nije isti kao postojeći Canadian FBP; opća CC BY licenca može imati izuzetke po sloju |
| [GlobFire v2](https://developers.google.com/earth-engine/datasets/catalog/JRC_GWIS_GlobFire_v2_DailyPerimeters) | globalni MODIS fire-event perimetri, 2001–2021, 500 m, nominalno daily | fallback za globalnu/region-wide distribuciju gdje nema kvalitetnije lokalne fire progression baze | dnevna oznaka izvedena iz MCD64A1; nekoliko dana vremenske nesigurnosti; složenije cloud/GEE preuzimanje i nema fuels/weather/terrain bundle |
| [WildfireSpreadTS](https://zenodo.org/records/8006177) | dnevne višekanalne serije za 607 požara u SAD-u, 2018–2021; predikcija širenja za 24 h | niži prioritet; razmotriti ako se pitanje projekta promijeni u dnevnu prognozu širenja | samo pregled metapodataka; arhiva 48.4 GB nije preuzeta |

Za Dogrib je provjerena deklaracija MIT licence repozitorija, ali zasebni uslovi
originalnih Prometheus/Alberta podataka nisu potvrđeni. CFSDS OSF projekt i
WildfireSpreadTS metapodaci navode CC-BY 4.0. EFFIS navodi da je EU-owned web sadržaj
CC BY 4.0 osim ako pojedinačna napomena kaže drugačije; sačuvati citat European Fuel
Map 2017 i navesti prerade. FireSpread_MedEU v2 Zenodo metadata
pokazuje da je dataset otvoren, ali ne prikazuje dataset licence field; članak je
CC-BY-4.0, što samo po sebi ne rješava licencu odvojenog zip fajla. Prije dijeljenja
ili uključivanja u Git potvrditi uslove baš podataka; sačuvati autore, URL, verziju i
transformacije.

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

1. Canada/CFSDS/Canadian FBP/Cell2Fire put je izabran. Dovršiti train-only TASK-015:
   fuel vintages, terrain/weather alignment, suppression dokaze i crop adequacy.
2. TASK-004c/017 adapteri su završeni; tehnički runtime smoke nije fizička validacija.
3. TASK-016: nakon unaprijed definisane QC varijante, provjeriti no-action rast na
   kalibracijskim slučajevima. Test događaje ne koristiti za tuning.
4. Tek nakon zadovoljavajućeg no-action ponašanja trenirati/porediti politike na
   event-level holdout scenarijima. Odvojeno izvještavati simulator fit i policy gain.

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
