---
type: Research Review
title: "Pregled nakon faze 2 — literatura i dijagnoza (2026-11-11)"
description: "Odgovori na pet Harunovih pitanja nakon ADR-032, zajednički zaključak, odluke koje čekaju i predloženi redoslijed rada."
status: stable
generated: {by: "process:claude-code", at: "2026-11-12T10:00:00Z"}
sources:
  - resource: /docs/research/review-2026-11-11/LITERATURE.md
  - resource: /docs/research/review-2026-11-11/SHORT_EPISODES.md
  - resource: /docs/research/review-2026-11-11/INTERVENTIONS.md
  - resource: /docs/research/review-2026-11-11/WHAT_IS_REAL.md
  - resource: /docs/research/review-2026-11-11/TUNED_HEURISTICS.md
  - resource: /docs/specs/DECISION_RECORDS.md
---
# Pregled nakon faze 2 (2026-11-11)

Nakon ADR-032 (PPO se ne razlikuje od nasumične linije ni od najbolje TRAIN heuristike)
Harun je postavio pet pitanja. Na svako je odgovorila zasebna analiza. Ovaj dokument
sažima odgovore i predlaže redoslijed rada. Pojedinačni izvještaji su na engleskom i imaju
reference na kod (`fajl:linija`) i ključeve izvještaja.

## Šta je rađeno, a šta ne

- Svih pet analiza je čitanje koda, ADR-ova, izvještaja i literature.
- Nove brojke su izračunate samo iz postojećih TRAIN fajlova (TRAIN benchmark, TRAIN gate,
  TRAIN redovi vremenskog fajla). Skripte i izlazi su u [analysis/](analysis/README.md).
- Jedno probno SimFire pokretanje: `advancing_front`, B=4, 98 TRAIN požara, da se izmjeri
  da li vatra prelazi liniju ([INTERVENTIONS §1.9](INTERVENTIONS.md)).
- Nijedan trening. VALIDATION nije ponovo korišten: njegovi brojevi su samo citirani iz
  ADR-032. TEST 2024 nije otvoren.
- Ništa od ovoga nije odluka. Odluke koje treba donijeti su ispod.

## Pet pitanja i kratki odgovori

| Pitanje | Kratak odgovor | Izvještaj |
| --- | --- | --- |
| 1. Rad arXiv 2512.06102 i srodna literatura: šta smo propustili? | Rad je o brzom GPU simulatoru (JaxWildfire); RL je samo primjer bez heuristika. U 22 pregledana rada RL pobijedi dobru heuristiku samo kad ga ona prvo nauči, i to tijesno. Uspješni radovi imaju 5–50× više epizoda i uglavnom jedan teren. Naš rezultat (bez dokazane razlike) je očekivan. | [LITERATURE](LITERATURE.md) |
| 2. Da li kratke epizode (48 h) koče učenje; pomažu li duže sintetičke simulacije? | Vjerovatno ne (75–80%). Pretpostavka nije tačna: FEDS je svaki TRAIN požar pratio najmanje 108 h (medijan ~11 dana), a 48 h je naš izbor zbog gatea. Vjerovatniji uzroci: slab signal (razlike između požara ~50× veće od efekta linije), premalo treninga (72 PPO ažuriranja), mali prostor za dobitak jedne linije, i agent možda ne vidi ono što određuje najbolji smjer. | [SHORT_EPISODES](SHORT_EPISODES.md) |
| 3. Šta se u simulacijama zapravo radi (avioni, ekipe…)? | Nema aviona, vode, retardanta, vozila ni kontrolisanog paljenja. U SimFire-u je jedini alat jedna trenutna linija ručne ekipe (~1,26 km) po odluci od 12 h, u jednom od 8 smjerova. U probi na TRAIN-u (`advancing_front`, B=4) nijedna ćelija linije nije izgorjela; vatra ide oko krajeva. Sintetički CA ima jedinice (ekipe, dozere) koje putuju i grade liniju. | [INTERVENTIONS](INTERVENTIONS.md) |
| 4. Da li iz stvarnih požara izvodimo logiku širenja? | Djelimično tačno. Iz stvarnih požara dolaze početno stanje, gorivo, reljef i vrijeme. Logika širenja je SimFire-ov Rothermel model; iz podataka je unaprijed zadanim pravilom gatea izabran samo jedan par WAF/ROS od 17 kandidata (WAF 0,10 / ROS 1,0). Simulacija slabo prati stvarni rast, a agent se nikad ne ocjenjuje prema stvarnom požaru. | [WHAT_IS_REAL](WHAT_IS_REAL.md) |
| 5. Da li je bolje optimizovati heuristike treningom? | To je prava vrsta pristupa, ali za sada bez dokaza o dobitku. Prostor za dobitak je u izboru smjera za konkretan požar, ne u izboru heuristike. Jednostavan selektor heuristika ne pomaže na požarima izvan podešavanja. Odluku treba donijeti jednom jeftinom offline analizom. | [TUNED_HEURISTICS](TUNED_HEURISTICS.md) |

## Zajednički zaključak

1. **Rezultat bez dokazane razlike je očekivan**, s obzirom na literaturu, količinu treninga i to što
   je 98 različitih požara s po ~20 epizoda najteži zabilježeni slučaj.
2. **Ključno otvoreno pitanje je da li se najbolja linija može predvidjeti iz onoga što
   politika vidi.** Ako ne može, ne pomažu ni duži trening, ni duže epizode, ni heuristike.
3. **Duže epizode i sintetički požari nisu prvi korak.** Granica od 48 h je naš izbor.
   SimFire ne uzima logiku širenja iz stvarnih požara, pa bi „zakonitosti iz stvarnih
   požara“ bile nov rad. Postojeći sintetički CA već ima duge požare i tamo je agent izgubio
   od pravila (ti brojevi su poništeni ADR-029, pa je to samo indicija).
4. **Tačno u ideji o dužim epizodama:** rez na 48 h ne broji efekat linije poslije 48 h.
   To se jeftino rješava ako se ista simulacija pusti dalje bez odluka („rep“).
5. **20 VALIDATION požara može otkriti samo veliku razliku.** Iz širine intervala ADR-032:
   oko 28 ha na B=1, ali 120–180 ha na B=2 i B=4. Iz rasipanja razlika između heuristika na
   TRAIN-u prag je veći, 117–168 ha već na B=1; stvarni prag za podešeno pravilo je vjerovatno
   između ([TUNED_HEURISTICS §1.5](TUNED_HEURISTICS.md)). Svaki novi pokušaj treba imati B=1
   kao glavni test.

## Nalazi koji traže odluku

1. **Linija se računa kao spašena površina.** U SimFire okruženju ćelija linije nikad ne
   izgori, pa se ne broji kao šteta ni kad bi je no-op vatra spalila
   (`src/wildfire_rl/feds_simfire_env.py:444-452`). To daje do ~26 ha zasluge po liniji na
   B=1, odnosno do 21–26% dobitka heuristika. U sintetičkom CA-u je to ispravljeno (ADR-030 §5,
   PR #11). Prije bilo kakve optimizacije treba odlučiti kako se šteta računa. Promjena
   zvanične metrike traži ADR, jer mijenja brojeve ADR-032.
2. **Heuristike nemaju rezervni smjer.** Kad željeni sektor nije dozvoljen, `downwind` i
   `advancing_front` ne rade ništa. Efekat je mali (najviše ~10 od ~1.000 odluka). Ne mijenjati
   zaključanu `advancing_front`; dodati nove varijante.
3. **Nasumična politika koristi isti seed za svaki požar**, pa ponavlja iste smjerove
   (već otvoreno pitanje iz ADR-032).
4. **Dokumentacija se na sedam mjesta razilazi s kodom** ([INTERVENTIONS §5](INTERVENTIONS.md)).
   Napomene su dodane u `SIMFIRE_ENVIRONMENT.md` i `SYNTHETIC_CA_ENV.md`. ADR-ovi su
   append-only i nisu mijenjani; tačan opis je u INTERVENTIONS. Najvažnije: dijagonalna
   linija ima 1,27 km, ne „do 1,8 km“ kako kaže ADR-025.
5. **Odluke od ranije i dalje čekaju:** koji je simulator glavni za poster, da li sintetički
   CA smije vidjeti vrijeme tekućeg koraka, i faza 3. Vidi [NEXT_SESSION](../../NEXT_SESSION.md).

## Predloženi redoslijed (samo TRAIN, dok se ne odluči drugačije)

Procjene su za 4 procesa niskog prioriteta na Harunovom računaru; pod opterećenjem
računati 1,5–2× duže. Zadaci su upisani u [BACKLOG](../../BACKLOG.md) kao TASK-028 do TASK-033.

1. **TASK-028: naplata linije u ocjeni.** Pomoćna funkcija koja liniji naplaćuje ćelije
   koje bi no-op vatra spalila; računa oba načina. Oko pola dana koda, s testom prije koda.
2. **TASK-029: iscrpna tablica za B=1 na TRAIN-u.** Svih 33 niza akcija po požaru; čuva
   ishod, opservaciju u svakoj odluci, dozvoljene sektore, ćelije linije i no-op otisak.
   Probni prolaz na 20 požara (~15 min) mora dati iste ishode kao TRAIN benchmark; zatim
   svih 98 (50–75 min). Simulator se ponaša deterministički (0 konflikata među nizovima
   opaženim u TRAIN benchmarku), pa bi to bila tačna gornja granica za B=1; pilot to provjerava.
3. **TASK-030: offline ocjena na toj tablici.** Fiksni sektor, podešeno pravilo, selektor,
   tabelarni RL i kloniranje heuristike; svaki požar se ocjenjuje izvan podešavanja (LOO po
   požaru); sa i bez naplate linije. Minute do sat CPU-a. **Nastaviti samo ako je dobitak
   izvan podešavanja ≥30 ha i ≥25% jaza do gornje granice.** Ako je ~0, to je rezultat:
   „prava linija se ne može predvidjeti iz opservacije“.
4. **TASK-031 (opcionalno): isto za B=1 s „repom“ od 48 h bez odluka** (2–2,5 h), prije
   bilo kakvog zaključka o vremenu postavljanja linije.
5. **TASK-032: planer** koji kratko simulira unaprijed sa posljednjim viđenim vremenom
   (oko dan koda, 3–4 h računanja), uz odvojeno prijavljenu „vidovitu“ gornju granicu.
   Traži ADR prije pokretanja (privilegovane informacije).
6. **TASK-033: B=2 i B=4**, novo korištenje VALIDATION-a (unaprijed registrovano, B=1
   glavni test), pa tek onda BC+PPO ili čisti RL. Sve traži ADR.

Ne traže ADR, ali traže Harunovo „da“: TASK-028 kao eksploratorna pomoćna funkcija, TASK-029 i
TASK-030, označeni kao eksploratorni, bez promjene zaključanog koda ili metrike. TASK-028 kao
zvanična metrika, TASK-031–033 (uključujući B=2/B=4) i svaka izmjena `advancing_front` traže
ADR ili dopunu.

## Granice ovog pregleda

- Google Scholar nije bio dostupan; citati su praćeni preko OpenAlex-a. Nekoliko radova je
  pročitano samo kroz sažetak; to je označeno u [LITERATURE](LITERATURE.md).
- Procjene vjerovatnoće (npr. 75–80%, 35–45%) su procjene analitičara, ne mjerenja.
- Brojke „simulirani rast je unutar 2× stvarnog na 12 od 82 požara“ i analize iz TRAIN
  benchmarka su izračunate u ovom pregledu i nisu prošle nezavisnu reviziju kao ADR-032.
