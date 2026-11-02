---
type: Research Gate
title: SimFire physical validation — NIROPS progression data audit
status: eight validation incident codes crosswalked; source polygons and spatial comparison remain open
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

NIROPS grafikon prikazuje samo zbirnu površinu kroz vrijeme. U javnom USFS sloju otvoren je
jedan završni Hayden poligon, ali nije spremljen niti poravnat s 30 m SimFire ćelijama; nema
ranijeg oblika za uporediti, prostorne metrike nisu izračunate, a neslaganje vremena nije
riješeno. Dakle, još nema prostornog poređenja ni **fizičke validacije simulatora**.

NIROPS posmatra stvarni požar pod stvarnim gašenjem. Bez pouzdanih zapisa o linijama,
posadama i drugim intervencijama, razlika između historijskog oboda i SimFire-a može biti
posljedica nepoznatog gašenja, greške simulacije ili oboje. Ovaj izvor zato može provjeriti
koliko se simulator slaže s historijskim razvojem, ali sam ne može dokazati šta bi se desilo
bez gašenja niti koliko bi agent spasio hektara.

## Sljedeći konkretni koraci

1. Provjeriti da li javni USFS final-perimeter sloj ima tačne ID-jeve za ostalih sedam 2023
   validation matcha. Zadržati ga kao izvor završnih oblika, ne kao dnevni rast. Raw NIROPS
   progresija traži odobren pristup novom `/protected` mjestu ili kontrolisan veći scratch.
   Ne čitati 2024 TEST geometrije.
2. Prvo riješiti prostorni obim: za cijeli požar pribaviti šire LANDFIRE/elevation isječke
   prema stvarnim obodima i povećati mrežu; ili, ako se ostaje na 128×128, unaprijed definisati
   ograničeni lokalni zadatak i lokalne metrike. Ne nazivati lokalni grid cijelim požarom.
3. Provjeriti atribute i izvorne vremenske oznake (`DateFlown`, UTC, incident ID), projekciju,
   topologiju i šta tačno obod predstavlja; zabilježiti gdje su vremena procijenjena.
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
- Javni USFS završni poligon: **1 Hayden validation feature pregledan**, nije sačuvan ili uvezen; dnevna progresija nije dostupna iz tog zapisa.
- Cijeli validation požari mogu stati u trenutni 128×128 grid: **0/20**.
- Prostorna ili fizička validacija SimFire-a: **nije urađena**.
- Trening agenta, policy evaluacija i test geometrije: **nisu pokrenuti/otvoreni**.

Ništa iz 2024 `TEST` skupa nije otvoreno. Ne trenirati niti zaključivati o uštedi stvarnih
hektara iz ovih podataka.
