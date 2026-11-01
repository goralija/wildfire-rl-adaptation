---
type: Design
title: Real-fire-derived SimFire policy experiment
status: current-provisional
sources:
  - resource: /docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md
  - resource: /docs/specs/DECISION_RECORDS.md
  - resource: /data/manifests/simfire-scenario.schema.json
---
# Trenutni dizajn — agent na scenarijima izvedenim iz stvarnih požara

## Pitanje koje ćemo mjeriti

Da li se generički PPO agent, dodatno učen na **raspodjeli uslova iz stvarnih požara**,
ponaša bolje unutar SimFire simulacije od istog zamrznutog agenta i jednostavnih pravila,
kada svi dobiju ista goriva, teren, vremenske uslove, trajanje i budžet za linije?

Ovo mjeri rezultat u simulatoru. Ne tvrdi da bi agent u stvarnosti sigurno smanjio neki
požar za određen broj hektara.

## Zašto smo pojednostavili put

Mineral Fire audit je pokazao da su linije nacrtane, ali vremena izgradnje nisu zabilježena
u poljima koja bi nam omogućila pouzdan vremenski replay. Pokušaj da ih odredimo iz
`CreateDate` bi značio nagađanje. Zato historijski replay linija više nije preduslov za
glavno pitanje. BurnMD ostaje opcioni izvor linijskih prikaza; osnovni benchmark koristi
historijske lokacije/datume požara i nezavisno provjerene pejzažne/vremenske ulaze.

Praktični kandidat za distribuciju prijavljenih lokacija požara je službeni USFS FPA-FOD. Njegov trenutni
sedmi edition sadrži lokaciju, datum i konačnu veličinu miliona požara, ali tačka nekih
slučajeva može biti precizna tek do PLSS sekcije oko 1 sq mi. Zato ćemo upisati poznatu
preciznost i ne pretvarati izvornu tačku u lažnu 30-m preciznost.

Prva probna kartica je Dixie Fire iz 2021. (`FOD_ID 401019270`). To je konkretan zapis za
provjeru pretvaranja i vizualnog toka, ne odluka da taj jedan požar bude cijeli trening ili
test skup. Skripta može dohvatiti jedan FPA-FOD zapis, sačuvati mali izvorni fajl s hashom
i napraviti scenario JSON. Službeni FPA-FOD archive kaže da se podaci mogu koristiti bez
dodatne dozvole ili naknade uz propisani citat; zasebne fuel, terrain i perimeter karte i
dalje imaju vlastite uslove korištenja.

## X i Y, bez stručnog žargona

- **Y je historijski zapis:** ID, prijavljeni datum i mjesto požara, uz napomenu koliko je
  lokacija tačna. Konačna površina ili perimetar ostaju samo za odvojenu referencu.
- **X je ono što SimFire treba:** mreža goriva, visina terena, vremenski uslovi, mjesto
  početne lokacije unutar mreže i dužina simulacije.
- **Pretvarač** čita Y, pronalazi dozvoljene izvore goriva/terena/vremena za taj dan,
  isječe fiksni prozor oko prijavljene lokacije i pravi scenario JSON koji pokazuje na velike
  GeoTIFF/weather fajlove. Specifikacija je u
  [scenario šemi](../data/manifests/simfire-scenario.schema.json).
- **Agent ne vidi kasniji razvoj požara.** Historijski perimetar ni linija ne ulaze u
  njegovu mapu niti u nagradu u ovoj verziji protokola.

## Uloge podataka

| Podatak | Uloga | Smije li agent vidjeti? |
| --- | --- | --- |
| Početna lokacija/datum i poznata tačnost | Odabir početka scenarija i splitova | Da, kao stvarna početna informacija s prijavljenom nesigurnošću |
| Fuel karta i teren | Simulator/opažanje agenta | Da, nakon provjere licence, vintagea i poravnanja |
| Weather | Simulator/opažanje agenta | Da, samo nakon konverzije jedinica/vremena i zapisivanja izvora |
| Konačna površina/perimetar | Kontekst i odvojena mapa poređenja | Ne; nije nagrada i ne određuje ishod alternativne politike |
| BurnMD linije | Opcioni sloj ljudskih akcija za vizualizaciju/replay | Ne u osnovnom benchmarku; vrijeme je nepotpuno za Mineral |

## Pošteno poređenje

1. Biramo skup incidenata i dijelimo po ID-u cijelog požara prije treninga.
2. Za svaki incident pravimo isti unaprijed zadani format i dimenziju mape; budući
   perimetri ne određuju veličinu prozora.
3. Treniramo base PPO na širokim funkcionalnim SimFire mapama; sačuvamo kopiju težina.
4. Fine-tunujemo kopiju samo na TRAIN scenarijima izvedenim iz stvarnih ulaznih uslova.
5. Na istim held-out scenarijima, seedovima, vremenu i linijskom budžetu mjerimo simuliranu
   opožarenu površinu, potrošnju i stabilnost. Upoređujemo base, fine-tuned, no-action i
   jasne heuristike.
6. Prikažemo stvarni ulazni pejzaž, početno mjesto i svaku simuliranu trajektoriju. Ako se
   nacrta stvarni završni perimetar, jasno je odvojen i označen kao historijska referenca.

## Granice i preduslovi

- BurnMD licenca ostaje neriješena; raw i derivati ostaju lokalno dok se uslovi ne potvrde.
- SimFire samostalno radi u Python 3.9.25. SimHarness/RLlib još nije instaliran.
- Mineralov LF2016 FBFM13 fallback je četiri godine prije događaja; to je privremeni
  tehnički kandidat, ne potvrđena godišnja fuel mapa.
- Dixie LF2016 FBFM13 i LF2020 elevation rasteri su pribavljeni i uvezeni u kratki smoke.
  Fuel je pet godina stariji od požara, zato je pre-event kandidat, ne potvrđen 2021 snapshot.
- ERA5 niz za datum postoji, ali nije ulaz modela: vjetar je na 10 m, RH nije gorivna vlaga,
  a FPA discovery HHMM nema potvrđenu zonu. Real-layer smoke zato jasno koristi demo atmosferu.
- SimHarness/RLlib nije instaliran. Ne trenirati niti izvještavati policy prednost dok se ne
  opravdaju fuel vintage/weather tretman, ne napravi višedogađajni split i ne podigne stabilan
  RL runtime.

Trenutni najizvodljiviji sljedeći korak: izabrati vremenski adekvatan fuel sloj za uzorke,
riješiti ili eksplicitno zadržati izvan modela ERA5 vjetar/vlagu, pa sastaviti FPA-FOD kohortu
sa splitom po incidentu. Potpuni workflow: [pipeline](research/REAL_IGNITION_SCENARIO_PIPELINE.md).
