---
type: Experiment Report
title: TRAIN-only prostorna podobnost CFSDS target-blind domena
status: stable
sources:
  - resource: /reports/real-fire-data/cfsds-train-target-blind-window-screen.json
  - resource: /reports/real-fire-data/cfsds-train-spatial-feasibility.json
  - resource: /scripts/audit_cfsds_train_spatial_feasibility.py
---
# TRAIN-only prostorna podobnost CFSDS domena

## Pitanje i ograničenje

Može li ciljno slijep prozor oko prethodnog CFSDS dana obuhvatiti naredni dnevni
perimetar, i kako se rezultat mijenja kad se unaprijed zada veći fizički prostor?
Ovaj audit provjerava samo istih 25 TRAIN event/day parova iz ranijeg target-blind
shortlista (pet po godini, 2014–2018). Ne govori da li cijeli CFSDS skup ima pogodne
slučajeve i ne bira nove slučajeve. Raniji screen je za eligibilnost para tražio zapis za
dan n i pozitivnu `firearea`; target geometrija nije birala prozor/rang, ali potpuno
target-independent day-pair cohort pravilo još nije uspostavljeno.

## Metod

Za svaku varijantu prozor se prvo bira iz dolaznih vrijednosti strogo prije target DOY,
centriran što bliže centroidu svih day n−1 piksela. Najmanje tri n−1 piksela moraju biti
u sigurnom unutrašnjem dijelu. Rubni prsten je približno širine jedne model ćelije,
zaokružen na broj izvornih 90 m CFSDS piksela. Izjednačenja prati pre-target pravilo iz
ADR-021. Tek nakon što je izvor prozora fiksiran računa se koliko day-n rastera leži
unutar prozora.

Lista od 25 event/day parova ostaje ista za sve veličine. Kandidati nisu ponovo rangirani
prema target pokrivenosti. “Target capture” je udio svih day-n izvornih 90 m piksela
požara koji upada u izabrani prozor; “safe interior” isključuje rubni prsten. Navedeni
procenti broje CFSDS raster piksele, ne Cell2Fire ćelije niti hektare stvarno izgorjelog
terena.

Varijante su definisane prije izračuna target metrika:

| Model grid | Traženi fizički prostor | Izvorni 90 m prozor | Značenje za postojeći 20×20 agent |
| --- | ---: | ---: | --- |
| 20×20, 100 m | 2.0×2.0 km | 23×23 (2.07 km) | ista veličina i ćelijska skala |
| 20×20, 150 m | 3.0×3.0 km | 34×34 (3.06 km) | isti tensor/akcije; promijenjena fizička skala |
| 20×20, 200 m | 4.0×4.0 km | 45×45 (4.05 km) | isti tensor/akcije; promijenjena fizička skala |
| 20×20, 300 m | 6.0×6.0 km | 67×67 (6.03 km) | isti tensor/akcije; znatno promijenjena fizička skala |
| 40×40, 100 m | 4.0×4.0 km | 45×45 (4.05 km) | drugačiji tensor i 1.600 akcija; checkpoint nije kompatibilan |

## Nalaz

| Varijanta | Ciljni prozor postoji | Prozori s bilo kojim target pikselom | S targetom u sigurnom unutrašnjem dijelu | Medijan / P75 / maksimum target capture | Medijan n−1 front capture |
| --- | ---: | ---: | ---: | ---: | ---: |
| 20×20, 100 m | 25/25 | 4/25 | 2/25 | 0% / 0% / 1.04% | 15.79% |
| 20×20, 150 m | 25/25 | 16/25 | 12/25 | 0.13% / 0.78% / 15.77% | 32.95% |
| 20×20, 200 m | 25/25 | 19/25 | 18/25 | 1.95% / 13.27% / 38.17% | 51.42% |
| 20×20, 300 m | 23/25 | 22/23 (22/25 ukupno) | 20/23 | 15.31% / 50.08% / 100% | 81.05% |
| 40×40, 100 m | 25/25 | 19/25 | 19/25 | 1.95% / 13.27% / 38.17% | 51.42% |

Capture medijana i percentili koriste parove sa dostupnim prozorom; za 20×20/300 m
denominator je 23. Dva izvorna rastera su manja od 67×67 potrebnih piksela: `2014_932`
ima 56×139, a `2015_895` 57×136. Ta dva para nisu izbačena zbog target geometrije.

Širenje fizičkog prostora pomaže, ali samo “bilo koji target pixel” preuveličava
upotrebljivost. U 4 km prostoru target uđe u 19/25 prozora, dok je medijalno i dalje
izvan prozora više od 98% target piksela. Oko 6 km je znatno bolje, ali medijalni capture
je oko 15%, dvije izvorne slike ne mogu smjestiti taj kvadrat, a 75. percentil capturea je
50.1%: najmanje tri četvrtine validnih prozora obuhvata najviše približno polovinu targeta.

Dvije konfiguracije oko 4 km pokazuju tradeoff: 20×20 ćelija od 200 m zadržava tensor i
broj akcija, ali mijenja prostorno značenje svake akcije i simulatorovog širenja; 40×40
ćelija od 100 m zadržava fizičku rezoluciju, ali zahtijeva drugi policy ulaz/izlaz i
checkpoint. Slična target pokrivenost nije dokaz da su te konfiguracije fizički
zamjenjive.

## Odluka i sljedeći korak

Na postojećih 25 parova fiksni 2×2 km prozor nije prostorno dovoljan za real-fire
reality-check. Veći kvadrati poboljšavaju geometrijsku pokrivenost, ali nijedna mjerena
varijanta zasad ne opravdava novi FireCase ili no-action replay: za to još nisu riješeni
FBP vremensko porijeklo, scar na non-fuel ćeliji, teren/vrijeme i suppression. Ne
usvajamo 200 m, 300 m ni 40×40 kao model domenu i ne koristimo ovaj target-only rezultat
za izbor događaja, prozora ili tuning.

Sljedeći prostorni korak je target-blind pre-screen svih TRAIN događaj/dan mogućnosti
koristeći unaprijed deklarisane fizičke domene, a ne samo 25 parova izabranih uz 2 km
agent. Day-pair pravilo mora biti napisano prije screeniranja; target geometrija se može
izračunati tek naknadno kao feasibility dijagnostika. Ako se iz train podataka bira fizička
skala, ona ostaje razvojna odluka i test skup mora ostati netaknut. Prije izrade slučajeva
potrebna je zasebna procjena coarse-grid FBP i policy kompatibilnosti naspram novog 40×40
modela.

## Granice

- TRAIN-only: 2014–2018. Validation/test godišnje arhive nisu otvorene.
- Audit koristi postojeći shortlist; nije iscrpan CFSDS cohort screen.
- Rezolucija provjere je izvornih 90 m arrival piksela. Nema resamplinga, većinskog
  pravila, fuel/DEM/weather poravnanja, raster exporta ili C++ simulacije.
- Target je dnevna satelitska procjena CFSDS, ne tačan satni ground-truth plamen/front.
- Ne testira se gašenje, potiskivanje ni fizička validnost Cell2Fire/FBP konfiguracije.
- Nema treniranja, fine-tuninga, policy benchmarka ili zaključka o smanjenju štete.
- Godišnji fuel vintage i non-fuel scar importer ostaju blokirani prema ADR-020; raniji
  target-blind invariant dokaz važi za jedan TRAIN event/day par.

Mašinski čitljivi detalji, hashes godišnjih TRAIN raster arhiva i per-case metrike su u
[spatial feasibility receipt-u](../../reports/real-fire-data/cfsds-train-spatial-feasibility.json).

Za ponavljanje iz repo roota, nakon što su lokalni TRAIN ZIP-ovi vraćeni prema download
manifestu:

```sh
python3 scripts/audit_cfsds_train_spatial_feasibility.py \
  --raw-root data/raw/cfsds-v1_1
```
