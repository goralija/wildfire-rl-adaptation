---
type: Design
title: Real-fire-derived SimFire policy experiment
status: current-provisional
sources:
  - resource: /docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md
  - resource: /docs/research/SIMFIRE_FPA_COHORT.md
  - resource: /docs/research/SIMFIRE_RL_ADAPTER.md
  - resource: /docs/specs/DECISION_RECORDS.md
---
# Trenutni dizajn — stvarni požari kao SimFire scenariji

## Pitanje koje ćemo mjeriti

Da li agent koji je dodatno učio na različitim uslovima iz stvarnih požara postavlja
vatrogasne linije bolje od istog početnog agenta i jednostavnih pravila **u istoj
simulaciji**, kada svi dobiju iste karte, vrijeme, trajanje i budžet?

Ovo mjeri rezultat u SimFire-u. Ne može dokazati da bi agent u stvarnosti smanjio neki
historijski požar za određeni broj hektara.

## Šta znače podaci X i Y

- **Y su historijski zapisi:** datum i prijavljena lokacija svakog požara iz baze US Forest
  Servicea. Izvor ne sadrži pouzdane poteze vatrogasaca koji bi agent mogao imitirati.
- **X su ulazi za simulator:** karta vrsta goriva, visina terena, atmosferski uslovi, početna
  ćelija i trajanje. Za svaki slučaj postoji mali JSON koji pokazuje na rastere i bilježi
  porijeklo, verziju, hash i ograničenja.
- **SimFire stvara iskustvo agenta:** agent vidi mapu i trenutno stanje vatre, postavi
  pojednostavljenu liniju ili izabere čekanje, a simulator vraća promjenu požara i nagradu.
- **Završna historijska površina i obod su samo kasniji kontekst.** Ne ulaze u agentovu
  nagradu niti određuju kako se požar širi u alternativnom simuliranom pokušaju.

## Podaci koji su pripremljeni

Koristimo 80 cijelih incidenata iz službene USFS FPA-FOD baze: 40 za trening (2018–2019),
20 za provjeru postavki (2023) i 20 za završni test (2024). Uzorak je iz deset zapadnih
država, traži požare od barem 5.000 acres, poznat datum/lokaciju i MTBS identifikator za
kasniju vizualnu referencu. Od 373 zapisa koji su prošli početni filter, ponovljivo je
odabrano 20 po godini. To je mali, namjenski uzorak velikih požara, ne reprezentativan
uzorak svih požara SAD-a.

Za svih 80 slučajeva preuzeti su stvarni LANDFIRE FBFM13 raster goriva i LF2020 visinski
raster. Svaki prozor ima 128×128 ćelija po 30 m, projektovan je u lokalni UTM koordinatni
sistem i prošao je provjere CRS-a, granica, dimenzija, vrijednosti i hash-a. Za 71 požar
izvorna prijavljena ćelija je goriva; kod 9 je korištena najbliža goriva ćelija, najviše oko
62 m dalje. To je praktično početno mjesto, ne potvrđen GPS položaj paljenja.

Fuel mapa je uvijek prije datuma požara, ali nije terensko snimanje baš na taj dan:
LF2016 se koristi za train 2018–2019, LF2022 za 2023–2024. Terrain je LF2020. Sirovi
GeoTIFF-ovi ostaju ignorisani u `.local/simfire-cohort-v2/`; Git čuva male scenario kartice,
izvorne zapise, hashove i izvještaje. Potpuni opis i komande su u
[`SIMFIRE_FPA_COHORT.md`](research/SIMFIRE_FPA_COHORT.md).

## Šta je pokretljivo, a šta nije potvrđeno

SimFire 2.0.1, Python 3.9.25, Gymnasium i MaskablePPO lokalno su postavljeni. Adapter
provjerava rastere i može učitati train, validation ili test dio. Za svih 80 incidenata
postoje dnevne gridMET vrijednosti i poseban proxy ulaz u formatu koji adapter čita.
Tehnički smoke je pokrenuo po jedan slučaj iz svakog splita; sve mapping provjere su prošle
pri učitavanju. WAF 0.1/0.3/0.5 varijante su prošle isti kratki smoke. `learn()` nije
pozvan. Adapter bilježi 15 jednominutnih koraka kao maksimalno trajanje jedne zapaljene
ćelije; stock 4 koraka su se pokazala prekratkim za neke 30 m raster-frontove. Ovo je
inženjerski popravak pokretljivosti, ne fizička kalibracija.

Proxy namjerno ne glumi savršeno historijsko mjerenje: gridMET je dnevni (~4 km), 10 m vjetar
je korišten kao približan 20 ft referentni vjetar prije faktora zaklona, a sitna gorivna
vlaga je procjena EMC iz dnevne maksimalne temperature/minimalne RH. Tačan sat paljenja,
canopy/profil vjetra i stvarna vlaga nisu poznati. Ovaj environment je pokretljiv i
ponovljiv za simulacijski ogled, ali nije fizički validiran za rekonstrukciju pojedinačnih
požara. Pogledati [mapping receipt](../reports/real-fire-data/simfire-cohort-v2-gridmet-simfire-mapping.json)
i [weather chart](../reports/real-fire-data/simfire-cohort-v2-gridmet-overview.png).

## Radni ugovor agenta

Početna akcija je jedna tačka vatrogasne linije na gorivoj ćeliji od 30 m. Tačka se postavi
odmah, bez kretanja ekipe ili vremena gradnje, i troši jednu od 32 budžetske jedinice.
No-op je uvijek moguć. Simulator napreduje 30 minuta po odluci, do 24 odluke (12 sati).
Nagrada je negativan prirast novih simuliranih opožarenih ćelija. Ovo je jednostavan radni
adapter za razvoj, ne model raspoređivanja stvarnih vatrogasnih posada. Puni ugovor je u
[`SIMFIRE_RL_ADAPTER.md`](research/SIMFIRE_RL_ADAPTER.md).

## Uslovi prije glavnog treninga

1. Zaključati poredbene politike: no-op, deterministička heuristika, base PPO i njegov
   fine-tuned nastavak. Iste mape/uslovi, budžet, horizont i evaluacijska sjemena za sve.
2. Zamrznuti broj trening seedova, metrike, pravilo izbora checkpointa i evaluacijski zapis.
   Validation se koristi za odluke; Larch Creek je već korišten u tehničkom smoke-u i mora
   biti izostavljen; preostalih 19 test ID-jeva ostaje zatvoreno do finalne procjene prema
   [membership manifestu](../data/manifests/simfire-fpa-fod-evaluation-membership-v1.json).
3. Dodati ili potvrditi dry-run preflight/training runner, koji ispiše split IDs, config i
   hashove bez poziva `learn()`.
4. Trening se pokreće zasebno, nakon eksplicitnog zahtjeva; trening i fine-tuning nisu dio
   ove pripremne promjene.
5. Sačuvati epizodne receipte i georeferencirane karte/animacije za isti skup scenarija,
   seedova i uslova. Zaključak ostaje samo o simulatoru, ne o stvarno spašenim hektarima.

No-op horizon probe su sačuvane za Owyhee (675 min/8.792 ćelije), Hayden (720 min/1.059)
i Larch Creek (84 min/24). To je provjera izvršavanja; simulirane površine nisu fizički
validirane.

Trenutni status i vlasnici sljedećih koraka vode se u [STATUS](STATUS.md) i
[BACKLOG](BACKLOG.md).
