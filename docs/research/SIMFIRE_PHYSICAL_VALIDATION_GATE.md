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

## Šta ovo još ne dokazuje

Grafikon prikazuje samo zbirnu površinu kroz vrijeme. Ne pokazuje gdje se vatra prostorno
širila i nije zamjena za originalne NIROPS obode. Nismo preuzeli ili otvorili nijedan obod
kao geometriju, nismo ga poravnali s 30 m SimFire ćelijama i nismo mjerili presjek/razliku
simulirane i opažene površine. Jedan grafikon koji prati FPA-FOD završnu veličinu potvrđuje da
izvor vrijedi dalje pregledati; **nije fizička validacija simulatora**.

NIROPS posmatra stvarni požar pod stvarnim gašenjem. Bez pouzdanih zapisa o linijama,
posadama i drugim intervencijama, razlika između historijskog oboda i SimFire-a može biti
posljedica nepoznatog gašenja, greške simulacije ili oboje. Ovaj izvor zato može provjeriti
koliko se simulator slaže s historijskim razvojem, ali sam ne može dokazati šta bi se desilo
bez gašenja niti koliko bi agent spasio hektara.

## Sljedeći konkretni koraci

1. Za osam identifikovanih `VALIDATION` slučajeva nabaviti samo odgovarajuće originalne
   NIROPS obode ako izvor dozvoljava izdvajanje po incidentu; u suprotnom procijeniti je li
   preuzimanje 1.29 GB arhiva nužno i praktično. Autorov primjer koda pokušava crawlovati
   NIFC `incident_specific_data` FTP za sve `IR/` foldere; direktno otvaranje navedenog root
   URL-a u browseru vratilo je 404, a specifične podfoldere još nismo pregledali. Provjeriti
   atribute i vremenske oznake (`DateFlown`, UTC, incident ID), projekciju, topologiju i šta
   tačno obod predstavlja.
2. Potvrditi veze s originalnim vremenima snimanja i završnim vremenom požara. Ne porediti
   direktno događaj od 19. jula s prvim NIROPS opažanjem od približno 21. jula kao da je
   simulacija imala poznat početni obod.
3. Utvrditi može li SimFire započeti od stvarnog NIROPS poligona. Sadašnji adapter počinje
   od jedne ćelije na prijavljenoj lokaciji; ne uvozi opaženi poligon. Ako se importer napravi,
   koristiti raniji poligon za početak i kasniji kao cilj, bez davanja budućeg poligona agentu.
4. Uspostaviti prostorne metrike i vremenski korak prije poređenja: npr. IoU/precision/recall
   oboda i greška površine, uz vidljivu kartu opaženo–simulirano. Označiti nedostajuća
   snimanja, nepravilne intervale i poznate intervencije.
5. Ako se koriste ovi 2023 slučajevi za kalibraciju, ne koristiti ih opet kao nezavisnu
   završnu provjeru politika; napraviti unaprijed zadanu podjelu ili pribaviti nezavisne
   kalibracijske slučajeve. Zamrznuti postojeći TEST split.
6. Tek nakon toga odlučiti jesu li postavke dovoljno mjerodavne za trening. PPO trening ostaje
   izvan ovog zadatka i nije pokrenut.

## Trenutno stanje

- Validation-only ID crosswalk: **8 jakih kod/država/ime podudaranja od 20 slučajeva**.
- NIROPS grafikoni: **1 vizuelno pregledan**; nije numerički digitalizovan.
- Originalne NIROPS geometrije preuzete/pregledane: **0**.
- Prostorna ili fizička validacija SimFire-a: **nije urađena**.
- Trening agenta, policy evaluacija i test geometrije: **nisu pokrenuti/otvoreni**.

Ništa iz 2024 `TEST` skupa nije otvoreno. Ne trenirati niti zaključivati o uštedi stvarnih
hektara iz ovih podataka.
