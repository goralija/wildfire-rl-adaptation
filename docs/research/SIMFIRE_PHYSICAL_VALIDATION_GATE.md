---
type: Research Gate
title: SimFire physical validation — NIROPS progression data audit
status: eight validation incident codes crosswalked; public perimeter shapes and current-map footprint screened; progression and physical simulator comparison remain open
sources:
  - resource: /docs/STATUS.md
  - resource: /docs/research/SIMFIRE_EVALUATION_PROTOCOL.md
  - resource: /reports/real-fire-data/nirops-validation-id-crosswalk-20261102.json
---
# Prije treninga: uporediti SimFire sa opaženim širenjem požara

## Zašto je ovo potrebno

Naš SimFire program može učitati stvarne požarne lokacije, karte goriva/terena i vremenski
proxy, ali uspješno pokretanje programa ne dokazuje da vatra u njemu napreduje kao stvarni
požar. NIROPS je nezavisni izvor avionskih infracrvenih snimanja požara s vremenskim
oznakama i geometrijama oboda. Zato je dobar kandidat za provjeru oblika i rasta simulacije.
Američka Šumarska služba objašnjava da NIROPS letove naručuju i daju prioritet požarišnim
timovima; dakle, snimci nisu ravnomjerni i ne pokrivaju svaki požar.
[USDA zapis i opis skupa](https://research.fs.usda.gov/treesearch/81275),
[Mendeley v2](https://data.mendeley.com/datasets/95rj5d379g/2).

## Šta smo sada provjerili

Preuzet je samo mali pomoćni dio verzije 2: ZIP sa 709 slikovnih grafikona površine kroz
vrijeme (78,086,022 bajta nakon izdvajanja iz glavnog arhiva) i ZIP s kodom autora (19.1
KB). Mendeley stranica navodi da je glavni arhiv 1.62 GB, a arhiv sirovih oboda
`NIROPS_2020_2024_R1_R6.zip` 1.29 GB; veličina cijelog v2 ZIP-a provjerena je HTTP
byte-range zaglavljem kao 1,735,431,121 bajt. Nije preuzet arhiv sirovih oboda ni dodatne
karte. Lokalni odabrani materijal je u ignorisanom `.local/nirops-progression-v2/` i nije u
Gitu.

Prema opisu skupa, izvorni IR poligoni su ručno iscrtani iz termalnih snimaka, objedinjeni u
jedan shapefile, standardizirani na EPSG:4326 i vremenski označeni UTC vremenom. Svaki
uključeni požar ima najmanje tri dana snimanja i barem jedan uzastopni dnevni par. Važno:
autori navode da su nedostajuća ili neusklađena vremena ponekad procijenjena iz imena fajla,
metapodataka i pomoćnih karata. Zato prije vremenskog poređenja treba provjeriti izvorno
vrijeme za svaki naš slučaj, umjesto da se oslanjamo samo na normalizovano polje.

Pregled samo ZIP indeksa (bez čitanja geometrija) pokazao je da je raw fajl jedan komprimovani
shapefile: `.shp` je 1,387,126,470 bajta u ZIP-u i 2,067,807,444 bajta nakon raspakivanja.
Nema zasebnih ZIP fajlova po požaru, pa običan HTTP range ne može izvući samo Hayden ili
drugih sedam požara. U tom trenutku je na ovoj mašini bilo 699 MiB slobodnog prostora, manje
od samog raw ZIP-a. [Archive-screen receipt](../../reports/real-fire-data/nirops-geometry-archive-screen-20261102.json)
bilježi byte-range, hash i strukturu. Dokumentovani stari NIFC FTP root vratio je 404;
pojedinačne incidentne podmape još nisu pronađene. To ne znači da su podaci uklonjeni:
zvanična NIFC stranica kaže da je 4. maja 2026. `/public/incident_specific_data` premješten
u `/protected/incident_specific_data`, a zaštićeni dio sada traži FAMAuth i odobrenje pristupa.
Javni „Incident Specific Maps” folder ostaje bez prijave, ali nije potvrđen kao arhiva
mašinski čitljivih NIROPS poligona.

Napravljen je crosswalk za tačno 20 FPA-FOD požara u `VALIDATION` splitu iz 2023. FPA-FOD
incidentni kodovi su poređeni sa kodovima u imenima NIROPS grafikona, nakon uklanjanja
razlika u crticama; država i ime su korišteni kao dodatne provjere:

- **8/20** ima isti incidentni kod, državu i ime.
- **3 dodatna pogotka samo po imenu/državi su odbačena.** Turkey, Beehive i Pearch imaju
  drugo NIROPS incidentno numerisanje, iako imena zvuče isto.
- **1 grafikon je vizuelno pregledan:** Hayden, s kodom `ID-SCF-023084`. Graf prikazuje
  površinu u acres kroz UTC datume; početna tačka je približno 21. jula 2023, a zadnja oko
  31. augusta. Završna vrijednost na slici je približno 24.800 acres, blizu FPA-FOD zapisa
  od 24.706 acres. Požar je u FPA-FOD-u evidentiran kao otkriven 19. jula. Očitavanja datuma
  i površine su približna, uzeta s osi grafikona. [Kopija grafikona](../../reports/real-fire-data/nirops-validation-charts/hayden-area-progression.png)
  je sačuvana u repou uz atribuciju; Mendeley v2 navodi CC BY 4.0.

Ponovljivi izračun i svi rezultati po slučaju nalaze se u
[JSON izvještaju](../../reports/real-fire-data/nirops-validation-id-crosswalk-20261102.json)
uz [skriptu](../../scripts/crosswalk_nirops_validation_ids.py). Raniji
[name-only screen](../../reports/real-fire-data/nirops-validation-name-screen-20261102.json)
sačuvan je kao poseban korak i pokazuje zašto samo ime nije dovoljno.

### Javni završni obod za Hayden

Nađena je alternativa za završni oblik: javni Forest Service sloj „2023 Fire Perimeter”
vratio je jedan zapis za Hayden pod službenim ID-jem `2023-IDSCF-023084`. Zapis je označen
kao **Final Wildfire Perimeter**, prijavljuje 24.706 acres (GIS izračun 24.730,34) i sadrži
komentar o NIROPS letu 30. augusta. To poklapa FPA-FOD incident i pokazuje da se barem završni
obod može dohvatiti bez velikog NIROPS ZIP-a. Geometrija je pregledana samo za ovaj 2023
validation požar i nije spremljena kao lokalna raw datoteka.

Ovaj sloj nije zamjena za NIROPS dnevni niz: za Hayden je vraćen samo jedan završni zapis,
ne raniji obod i naredni rast. Postoji i vremenska nedoumica: brojčano `perimeterdatetime`,
ako se tumači kao UTC, kaže 30. augusta u 22:52 UTC, dok komentar kaže 22:52 MDT, odnosno
31. augusta u 04:52 UTC. Timestamp ne smijemo koristiti za replay dok se značenje polja ne
razriješi. Detalji su u [USFS Hayden screen receiptu](../../reports/real-fire-data/usfs-hayden-final-perimeter-screen-20261102.json).

### Šta su pokazali javni obodni servisi za osam slučajeva

Nakon Haydena, atributno smo pretražili zvanični USFS 2023 sloj po tačnom incidentnom
identifikatoru i širi javni NIFC/WFIGS sloj po imenima ograničenim na 2023. NIFC rezultat
smo zatim provjerili prema jedinstvenom kodu incidenta, državi, lokalnom broju i veličini.
Nijedna od ovih dodatnih pretraga nije tražila geometriju.

| Validation slučaj | Šta je javno pronađeno | Procjena |
| --- | --- | --- |
| Hayden | NIFC final 24,708.7; USFS final 24,706 total / 24,730.34 GIS acres | Obje površine blizu FPA-FOD 24,706; vrijeme USFS leta još nije usklađeno |
| Sourdough | NIFC final 7,336.918 acres | Blizu FPA-FOD 7,377; USFS sloj nema taj tačan ID |
| River Road East | NIFC final 17,312.92; USFS final 17,313 total acres | Blizu FPA-FOD 17,313 |
| Bedrock | USFS jedan daily obod: 31,590 total / 31,589.2 GIS acres | Površina odgovara FPA-FOD 31,590, ali postoji samo jedan obod |
| Prior | NIFC final 0.1; USFS final 12,833 total / 12,833.22 GIS acres | USFS veličina odgovara FPA-FOD 12,833; NIFC geometrijski acres su očito nedosljedni |
| Rabbit | NIFC daily zapis s incidentom 8,354.8 acres, ali GIS acres i vrijeme poligona su prazni | Identitet se poklapa; server vraća okvir, ali puna geometrija i vrijeme treba posebno provjeriti |
| Pass | NIFC final 59,883.41; USFS final 59,883 total / 59,883.43 GIS acres | Blizu FPA-FOD 59,883; vrijeme USFS leta ima isti šest-satni problem kao Hayden |
| Gray | NIFC final 200 acres uz incident size 10,064 acres | Veliko odstupanje; ne koristiti bez pregleda izvornog poligona i provjere izvora |

Pet slučajeva ima finalni obod čija objavljena površina je bliska FPA-FOD zapisu:
Hayden, Sourdough, River Road East, Prior preko USFS sloja i Pass. Zatim smo uzeli pune oblike
samo za ovih osam 2023 VALIDATION slučajeva i provjerili ih u projekciji postojećih rastera;
sirove koordinate su korištene samo u memoriji i nisu sačuvane u repozitoriju. Svih osam
primarnih poligona je topološki ispravno, a izračunate površine su unutar 0.58% FPA-FOD
vrijednosti. Četiri slučaja s USFS i NIFC oblicima imaju gotovo iste koordinate (razlika ispod
milimetra), što je dosljednost između dva objavljivanja, ne nužno dvije nezavisne izmjere.

Neki atributi površine ipak su pogrešni: NIFC Prior navodi 0.1 acres, a Gray 200 acres, dok
njihovi oblici imaju oko 12,842 odnosno 10,057 acres, približno FPA-FOD veličinama. Za ta dva
slučaja treba vjerovati provjerenom obliku više nego tom jednom atributu, ali ne pretpostaviti
da će takvi atributi uvijek biti tačni. Javni servisi i dalje ne daju vremenski niz uzastopnih
oblika za ove požare. NIROPS ostaje mogući izvor takvog niza, ali njegove progresijske
geometrije nisu preuzete.

USFS sloj navodi da su datumska polja u UTC-u kada je dateFieldsTimeReference prazan.
Ipak, za Hayden je brojčano vrijeme 22:52 UTC, a komentar kaže 22:52 MDT; za Pass je brojčano
vrijeme 00:06 UTC, a komentar kaže 00:06 MDT. Esri dokumentacija objašnjava UTC pretpostavku,
ali ne može kazati kako su te letne bilješke unijete u USFS bazu. Zato nećemo samovoljno
pomjerati vrijeme za šest sati; treba izvorno objašnjenje od vlasnika podataka prije replaya.
Detalji po slučaju, ID-jevi i sirovi atributi su u
[public-perimeter screen receiptu](../../reports/real-fire-data/usfs-nifc-validation-perimeter-screen-20261102.json).

Zatim smo tražili samo pravougaoni okvir geometrije za svaki od osam 2023 validation požara,
bez preuzimanja koordinata poligona. Okviri su široki 6.35–21.55 km i visoki 7.05–21.32 km,
dok postojeći raster pokriva 3.84×3.84 km. Postojeći rasterni okvir siječe samo 3.2–22.5%
pripadajućeg pravougaonog okvira oboda. To je mjera pravougaonika, ne udio izgorjele površine,
ne stvarni dodir s poligonom i ne IoU. Za pokrivanje cijelog pravougaonog okvira na 30 m,
potrebno je 212×309 do 719×711 ćelija (4.0–31.2 puta više od sadašnjih 128×128); najveći
okvir je Pass. To nije procjena brzine ili memorije, a stvarni nepravilni oblik može zauzimati
manje ćelija od pravougaonika. Hayden, River Road East, Prior i Pass imaju skoro identične
okvire u USFS i NIFC servisima, što je dobar izvorni cross-check, ali ne zamjenjuje provjeru
koordinata/topologije. Rabbitov zapis ima server-side okvir uprkos praznim area/time poljima;
njegova puna geometrija je naknadno pregledana u sljedećoj sekciji. Vidi [extent-only receipt](../../reports/real-fire-data/simfire-validation-perimeter-extent-screen-20261102.json).

### Puni poligoni u odnosu na trenutne karte

Za prostorni QA smo zatim dohvatili tačne geometrije za osam odabranih 2023 VALIDATION
požara i četiri dodatna oblika radi poređenja USFS/NIFC zapisa. Granice su sklopljene prema
Esri pravilima za vanjske i unutrašnje prstenove, prebačene u isti UTM sistem kao fuel raster,
pa presječene s pravougaonikom postojeće 128×128 karte. Sirovi poligoni nisu spremljeni;
receipt čuva izvorne object ID-jeve, provjere, površine, preklop i potrebne dimenzije mreže.

| Slučaj | Izvor/vrsta oboda | Izračunata površina | Dio požara unutar trenutne karte | Pravougaona mreža 30 m za obuhvat oblika |
| --- | --- | ---: | ---: | ---: |
| Hayden | USFS final | 24,717 acres | 10.5% | 571×455 |
| Sourdough | NIFC final | 7,334 acres | 24.7% | 203×305 |
| River Road East | USFS final | 17,311 acres | 14.7% | 535×349 |
| Bedrock | USFS daily | 31,565 acres | 10.5% | 701×447 |
| Prior | USFS final | 12,842 acres | 26.1% | 390×244 |
| Rabbit | NIFC daily | 8,349 acres | 10.1% | 286×235 |
| Pass | USFS final | 59,934 acres | 4.8% | 699×691 |
| Gray | NIFC final | 10,057 acres | 5.5% | 355×329 |

Ovo je preciznije od ranijeg poređenja pravougaonih okvira: sada znamo da svaka karta
zaista presijeca svaki poligon, ali hvata samo 4.8–26.1% njegove ukupne površine. Za cijeli
poligon na 30 m treba 203–701 kolona i 235–691 redova; najveći pravougaoni okvir, Pass, treba
699×691 (483,009 ćelija, 29.5 puta više od sadašnje mreže). To je geometrijski prostor za
obuhvat obrisa, bez sigurnosne margine za simulirano širenje, i nije prognoza brzine ili
memorije.

USFS i NIFC oblici za Hayden, River Road East, Prior i Pass međusobno su gotovo identični.
Ipak, Grayov NIFC `gis_acres=200` i Priorov `gis_acres=0.1` ne slažu se s njihovim vlastitim
oblicima ni s FPA-FOD veličinama; projicirane površine oblika su oko 10,057 i 12,842 acres.
To je razlog da prije vizualizacije ili metrike računamo površinu iz provjerene geometrije,
umjesto da slijepo vjerujemo svakom gotovom polju acres. Detalji i metode su u [polygon QC
receiptu](../../reports/real-fire-data/usfs-nifc-validation-perimeter-polygon-qc-20261102.json);
osam poređenja se može vidjeti na [mapi javnih oboda i postojećih input karata](../../reports/real-fire-data/validation-perimeter-map-footprints-20261102.png).
Isti QA i slika se mogu ponoviti komandom
`.local/simfire-venv/bin/python scripts/qc_simfire_validation_perimeters.py --overwrite`;
skripta dohvaća samo unaprijed odobrene tačne ID-jeve za ove validation slučajeve.

### Trenutne SimFire mape nisu dovoljno velike za cijele požare

Mapa od 128×128 ćelija po 30 m ima maksimalno oko **3.644 acres** čak i kad bi svaka ćelija
izgorjela. Svih 20 validation požara ima prijavljenu završnu površinu veću od te granice:
raspon je **5.169–81.148 acres**, medijan **9.209 acres**. Za samo površinu — pod
nerealnom pretpostavkom kvadratnog požara — trebalo bi između 153 i 605 ćelija po stranici;
stvarni oblik može tražiti još širi isječak. Po-case rezultati su u
[grid-capacity auditu](../../reports/real-fire-data/simfire-validation-grid-capacity-20261102.json)
uz [skriptu](../../scripts/audit_simfire_validation_grid_capacity.py).

To ne sprečava mali, lokalni eksperiment o postavljanju linije. Znači da trenutna mapa ne
može opravdati tvrdnju da simulira cijeli historijski požar ili njegove ukupne hektare. Za
takvu tvrdnju treba proširiti Fuel/DEM mape na stvarni obod s marginom i povećati SimFire
mrežu. Ako se zadrži 128×128, istraživačko pitanje mora se ograničiti na jasno definisan
lokalni dio požara.

## Šta ovo još ne dokazuje

U odvojenom javnom polygon QA-u izmjerili smo površine oboda i njihov presjek s trenutnom
SimFire kartom. To potvrđuje da je karta premala za cijeli obod, ali nije poređenje simuliranog
rasta sa opaženim rastom. Za iste požare nemamo vremenski niz uzastopnih oboda. Raniji
geometrijski oblik ne dokazuje kako je požar rastao do kasnijeg oblika; vremensko neslaganje
za Hayden/Pass ostaje neriješeno. Dakle, još nema **fizičke validacije simulatora**.

NIROPS posmatra stvarni požar pod stvarnim gašenjem. Bez pouzdanih zapisa o linijama,
posadama i drugim intervencijama, razlika između historijskog oboda i SimFire-a može biti
posljedica nepoznatog gašenja, greške simulacije ili oboje. Ovaj izvor zato može provjeriti
koliko se simulator slaže s historijskim razvojem, ali sam ne može dokazati šta bi se desilo
bez gašenja niti koliko bi agent spasio hektara.

## Sljedeći konkretni koraci

1. Javni USFS/NIFC attribute-only screen za osam slučajeva je završen. Za stvarni replay i
   dalje trebaju višednevne NIROPS geometrije iz zaštićenog /protected foldera ili arhive uz
   veći scratch prostor. Ne čitati 2024 TEST geometrije.
2. Prvo riješiti prostorni obim: za cijeli požar pribaviti šire LANDFIRE/elevation isječke
   prema stvarnim obodima i povećati mrežu; ili, ako se ostaje na 128×128, unaprijed definisati
   ograničeni lokalni zadatak i lokalne metrike. Ne nazivati lokalni grid cijelim požarom.
3. Za svaki pribavljeni NIROPS niz provjeriti atribute i vrijeme snimanja (`DateFlown`, UTC,
   incident ID), projekciju i topologiju; zabilježiti gdje su vremena procijenjena.
4. Potvrditi veze s originalnim vremenima snimanja i završnim vremenom požara. Ne porediti
   direktno događaj od 19. jula s prvim NIROPS opažanjem od približno 21. jula kao da je
   simulacija imala poznat početni obod.
5. Utvrditi može li SimFire započeti od stvarnog NIROPS poligona. Sadašnji adapter počinje
   od jedne ćelije na prijavljenoj lokaciji; ne uvozi opaženi poligon. Ako se importer napravi,
   koristiti raniji poligon za početak i kasniji kao cilj, bez davanja budućeg poligona agentu.
6. Uspostaviti prostorne metrike i vremenski korak prije poređenja: npr. IoU/precision/recall
   oboda i greška površine, uz vidljivu kartu opaženo–simulirano. Označiti nedostajuća
   snimanja, nepravilne intervale i poznate intervencije.
7. Ako se koriste ovi 2023 slučajevi za kalibraciju, ne koristiti ih opet kao nezavisnu
   završnu provjeru politika; napraviti unaprijed zadanu podjelu ili pribaviti nezavisne
   kalibracijske slučajeve. Zamrznuti postojeći TEST split.
8. Tek nakon toga odlučiti jesu li postavke dovoljno mjerodavne za trening. PPO trening ostaje
   izvan ovog zadatka i nije pokrenut.

## Trenutno stanje

- Validation-only ID crosswalk: **8 jakih kod/država/ime podudaranja od 20 slučajeva**.
- NIROPS grafikoni: **1 vizuelno pregledan**; nije numerički digitalizovan.
- Originalne NIROPS geometrije preuzete/pregledane: **0**.
- Javni USFS/NIFC screen: **8 validation slučajeva**; svih osam primarnih poligona je validno, njihova projektovana površina unutar 0.58% odgovara FPA-FOD veličinama, a trenutna karta obuhvata 4.8–26.1% površine svakog. NIFC `gis_acres` atributi Priora i Graya nisu saglasni s geometrijom; sirove koordinate nisu sačuvane.
- Javne višednevne progresijske geometrije za ova 8 slučaja: **0 pronađeno u pretraženim servisima**; sirovi NIROPS niz i dalje nedostaje.
- Cijeli validation požari mogu stati u trenutni 128×128 grid: **0/20**.
- Prostorna ili fizička validacija SimFire-a: **nije urađena**.
- Trening agenta, policy evaluacija i test geometrije: **nisu pokrenuti/otvoreni**.

Ništa iz 2024 `TEST` skupa nije otvoreno. Ne trenirati niti zaključivati o uštedi stvarnih
hektara iz ovih podataka.
