---
type: Diagnostic Report
title: "CFSDS no-action rast: dijagnostika tri train slučaja"
description: Train-only analysis of saved simulator timelines, weather/fuel inputs, map limits, and stopping behavior for three existing CFSDS replays.
status: stable
sources:
  - resource: /reports/real-fire-data/cfsds-no-action-timeline.json
  - resource: /docs/research/CFSDS_TRAIN_QC.md
  - resource: /docs/research/REAL_CASE_PIPELINE.md
  - resource: /docs/research/SOURCES.md
---
# CFSDS no-action rast: dijagnostika tri train slučaja

## Sažetak za tim

Ova analiza objašnjava zašto su tri postojeće **simulacije bez intervencije** izbacile
više opožarene površine od CFSDS dnevnog cilja. Nije pokrenuto treniranje, nije mijenjan
model radi boljeg slaganja i nisu korišteni validation/test ciljevi.

Glavna potvrđena stvar je da se simulatorova završna karta i CFSDS cilj ne zaustavljaju
nužno u isto vrijeme. CFSDS daje interpolisani **dnevni** obuhvat, ali ne kaže u kojem
minutu je svaki dio izgorjeo. Cell2Fire napreduje u minutnim koracima, a Firehose agent
dobija priliku za odluku svakih osam simuliranih minuta. Simulator se može završiti kada
više nema aktivnog fronta, kada su sve ćelije u malom prozoru pogođene ili kada istekne
24-satni niz vremena. To nisu međusobno isti razlozi.

Mjere na unaprijed izabranim vremenskim presjecima potvrđuju da vrijeme snažno utiče na
površinu, ali tri požara rastu različitim brzinama. Zato se iz postojećih podataka ne može
izabrati jedan validan trenutak prekida koji bi svakom požaru dao “tačan” dnevni cilj.
Za sada ostaje potvrđeno da osnovni no-action replay ne prolazi reality-check. Uzroci
prevelike brzine širenja još nisu razdvojeni.

## Šta je mjereno

- Polazna tačka su **isključivo** već postojeći train slučajevi `2018_747`, `2018_241` i
  `2018_1770` te njihove sačuvane C++ `ForestGrid` vremenske serije.
- Cilj je CFSDS površina iz sljedećeg dana. Ona je izvedena kriging interpolacijom
  satelitskih detekcija; nije sat-po-sat izmjeren obod požara. [CFSDS opis](SOURCES.md#s-015)
  dokumentuje dnevne agregate i ograničenu dostupnost nezavisnih ground-truth granica.
- Za svaku postojeću vremensku seriju izračunata je predviđena nova površina i IoU na
  unaprijed zadanim presjecima 30, 60, 120, 240, 480, 720 i 1.440 minuta. Kada je požar
  simulacijom ranije završen, kasniji presjeci ponavljaju njegovu završnu kartu.
- Izračun koristi isti fractional target raster i istu definiciju novog gorenja kao
  postojeći evaluator. Ulazni hashovi, seedovi, verzije slika i svi presjeci su u
  [mašinski čitljivom nalazu](../../reports/real-fire-data/cfsds-no-action-timeline.json).

Ponoviti analizu kada kolega ima lokalne `runs/` izlaze:

```sh
PYTHONPATH=src python3 scripts/analyze_cfsds_replay_timeline.py \
  --case-dir runs/real-case/2018_747-day228 \
  --probe-dir runs/real-case/2018_747-day228/probe-seeds/no-action-zero-warmup \
  --out /tmp/2018_747-timeline.json
```

Za druga dva požara promijeniti `--case-dir` na `2018_241-day227` ili
`2018_1770-day224`, a `--probe-dir` na pripadajući `probe/no-action-zero-warmup`.
Raw ulazi i grids ostaju lokalni i ignorisani u Gitu. Za čist checkout prvo treba
ponoviti case konverziju i replay prema [runbooku](REAL_CASE_PIPELINE.md).

## Potvrđene vrijednosti

| Train događaj | Cilj CFSDS (ha) | Simulacija: 30 min | 60 min | 120 min | 240 min | 480 min | 720 min | 1.440 min / završno |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `2018_747` | 15.39 | 18 | 29 | 42 | 65 | 66 | 66 | 66 ha; završila na 244 min |
| `2018_241` | 12.15 | 8 | 23 | 46 | 87 | 192 | 237 | 237 ha; završila na 694 min |
| `2018_1770` | 12.15 | 0 | 4 | 13 | 21 | 33 | 51 | 73 ha; dosegla 1.439 min |

Završno predviđanje je 4.29×, 19.50× i 6.01× dnevnog cilja; završni IoU je .2187,
.0376 i .1361. To su postojeće završne metrike, a ne nove replays.

| Događaj | Početno izgorjelo / aktivni rub | Gorivne klase u 20×20 | ERA5 tačka od centra | Prvi dodir ivice | Stanje kad je C++ stao |
| --- | ---: | --- | ---: | ---: | --- |
| `2018_747` | 175 / 31 ćelija | C3: 211, D1: 189 | 5.20 km | 34 min | 272/400 pogođeno; 0 aktivnih, 128 neizgorjelih |
| `2018_241` | 140 / 23 ćelije | C3: 342, D1: 58 | 5.16 km | 37 min | svih 400 pogođeno do 693 min; zadnji grid ima 4 aktivne ćelije |
| `2018_1770` | 287 / 17 ćelija | C2: 400 | 2.44 km | 52 min | 377/400 pogođeno; dosegnut puni weather horizon |

Ista službena FBP 2014b mapa od 250 m korištena je u sva tri slučaja i prebačena na
modelsku mrežu od 100 m; lookup tabela i source hash su isti. To znači da je osnovna
konverzija gorivnih kodova zajednička. Međutim, “gorivni gate PASS” samo znači da su
historijske scar/front/target ćelije preklopljene s kodovima koje simulator dopušta da
gore. Ne potvrđuje da 2014b karta, gruba rezolucija ili FBP ponašanje tačno predstavljaju
lokaciju i godinu požara. Ova tri isječka sadrže samo C2/C3/D1, pa im nisu potrebni
posebni parametri za miješanu šumu ili travu; nullable parametri u manifestu nisu
objašnjenje ovog odstupanja. Vidi [fuel-only metod](CFSDS_TRAIN_QC.md).

## Zašto je raniji horizon podatak bio zbunjujući

Jedan raw probe JSON imao je `weather_horizon_minutes: 480`. To polje je bilo pogrešno
izračunato kao `60 × steps_per_action` — miješalo je broj minuta između agentovih odluka
sa dužinom vremenskih podataka. Nije mijenjalo ulaz simulatora niti tok replaya.

Sačuvani `Weather.csv` ima 24 satna reda. Pinovani C++ kod Cell2Fire koristi 60 minuta
po vremenskom redu i `Fire-Period-Length=1`, pa je maksimalni vremenski opseg
24 × 60 / 1 = **1.440 simuliranih minuta**. `steps_per_action=8` znači da Firehose pošalje
sljedeću akciju nakon osam simuliranih fire-perioda (oko osam minuta); to ne znači osam
sati. Korekcija probe sada čita stvaran broj redova iz `Weather.csv`; njena provjera je
u `tests/test_firehose_probe.py`.

Ovo razdvaja dvije situacije koje su prije bile spojene u `simulator_reported_finished`:

- `2018_1770` je dosegao kraj od 24 satna vremenska reda. Output grida ima 1.439 minuta
  proteklog modelskog vremena, a nema aktivnih ćelija nakon završnog horizon koraka.
- `2018_241` je popunio cijeli prozor od 2×2 km; kod 693 minuta više nema neizgorjele
  ćelije, pa kasnije vrijeme ne može prikazati širenje izvan mreže.
- `2018_747` je završio prije vremenskog maksimuma sa 128 neizgorjelih ćelija i bez
  aktivnog fronta. To je kompatibilno sa simulatorovim ranijim terminalnim uslovom, ali
  prethodni probe receipt nije zapisao imenovan terminalni razlog.

Tačan terminalni razlog zato ostaje obaveza TASK-004c. C++ izvor dozvoljava završetak
zbog isteka horizon-a, nestanka aktivnog fronta ili nedostatka preostalih ćelija, dok
Python probe sve bilježi kao `upstream_done`.

## Šta zajednički ulazi potvrđuju

### Vrijeme i FWI

Case builder pravi 24 lokalna ERA5-Seamless reda. Tačke su 2.4–5.2 km od dnevnog CFSDS
centroida; to su obližnje reanalysis tačke, ne stanice na požaru. Dinamički satni vjetar
varira tokom dana. CFSDS FWI komponente su dnevni sažeci, pa se FFMC, BUI i ostali kodovi
u `Weather.csv` ponavljaju umjesto da se izračunaju iz sata u sat. Core C++ FBP korak
uzima vjetar, smjer, FFMC i BUI iz trenutno odabranog weather reda. Historijski
`summary_weather.ws` je zasebna dnevna vrijednost: približno 6.50, 2.36 i 13.85 km/h za
ove događaje; ERA5 satni vjetar oko 12:00 je 6.6, 3.1 i 20.6 km/h. Razlika, najizraženija
u `2018_1770`, je razlog da uskladimo vremenski izvor/profil; nije sama po sebi dokaz
greške u jedinicama ili uzrok prevelikog rasta.

### Početni front, potiskivanje i mapa

Početno stanje koristi 17–31 aktivnih ćelija iz day n−1 površine koje su susjedne
sljedećem dnevnom cilju; stariji scar je posebno uvezen. CFSDS ne sadrži tačan minut
požara niti događajni zapis gašenja za ove ID-jeve. Početni obod je zato prostorno
zasnovan na dnevnim rasterima, ali stvarna aktivna linija i potiskivanje nisu potvrđeni.

Sva tri modelirana požara dodiruju ivicu 20×20 prozora u 34–52 minuta. `2018_241` napuni
cijelih 400 ćelija. To je potvrđen problem veličine domena: mapa koja je odsječena na
ivici ne govori koliko bi požar nastavio izvan 2 km. Rub ne uzrokuje preveliki rast
unutar prozora; on ograničava koliko ga možemo izmjeriti i može ga potcijeniti.

### Stohastičnost i warmup

Za `2018_747` šest seedova 123–128 već je dalo istu završnu kartu i 66 ha, iako se vrijeme
do završetka razlikovalo. Za `2018_241` poređenje 20-minutnog warmupa sa nula-minutnim
warmupom dalo je iste završne metrike. To slabi objašnjenje da su seed ili warmup glavni
uzrok za ta dva slučaja. `2018_1770` ima samo jedan seed; tu se seed efekat nije izolovao.

## Razdvajanje nalaza od hipoteza

**Potvrđeno:** no-action simulacije premašuju dnevne ciljeve, vrijeme poređenja je važno,
požari dodiruju rub mreže, jedan popunjava cijelu mrežu, hourly ERA5 vjetar se koristi s
dnevnim FWI komponentama, a suppression status je nepoznat.

**Vjerovatna ali nepotvrđena objašnjenja:** nepoznato istorijsko gašenje; razlika između
dnevnog maska-cilja i tačnog unutardnevnog vremena; geografski gruba 9–25 km reanalysis
meteorologija; stalni dnevni FWI kodovi; aktiviranje svih susjednih prethodno-dnevnih
ćelija odjednom; fuel-map vintage/resolucija; i aproksimacija 20×20 prozora. Ova tri
replaya ne izoluju pojedinačni uzrok.

Mali train-only dokaz iz literature daje koristan kontekst, ali nije rezultat našeg
modela: procjena CFSDS v1.1 kroz W.I.S.E. izvještava preuveličavanje površine za
nepodešeni osnovni scenario i grid-edge dodire u 25.7% slučajeva. Njihov odvojeni
“najbolji trajanje/pravac” scenario koristi budući CFSDS odgovor da odabere parametre;
to je upper-bound dijagnostika, ne pošten test operativnog modela. W.I.S.E. nije naš
Firehose/Cell2Fire engine, pa njegove metrike ne prenosimo na ovaj projekat.
[Izvor: Bennett et al. 2026, S-019](SOURCES.md#s-019).

## Sljedeći koraci

1. TASK-004c adapter je naknadno dovršen: C++ eksportuje kumulativnu štetu/front/treatment
   i terminal reason; fixture i 12/12 inference slučajeva prolaze. Ovaj adapter popravlja
   mjerenje, ali ne mijenja nijedan raniji no-action replay niti rješava fizički mismatch.
2. Definisati unaprijed zajednički vremenski horizont za no-action baseline i sve agentne
   politike. Ne birati trajanje po požaru koristeći njegov target raster.
3. Razdvojeno pripremiti train-only kontrolu satnog vremena/FWI (isti ostali ulazi,
   jedna promjena odjednom) i provjeru fuel-vintage/istorijskog scar successional pravila.
   Svaki slučaj mora zapisati stare i nove input hashove.
4. Ispitati veći prostorni prozor kao zasebnu feasibility promjenu; 40×40 mijenja
   broj ćelija/akcija i ne može se predstaviti kao isti 20×20 agent.
5. Prije policy benchmarka zatvoriti no-action gate, riješiti suppression evidence gdje
   postoji i zamrznuti heldout event ID-jeve. Ne trenirati niti kalibrisati na validation/test.

Nastavak TASK-004c integracije i ograničenja: [adapter smoke receipt](../../reports/firehose-verification/task004c-adapter-smoke.json).
