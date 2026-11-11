---
type: Project Status
title: Trenutno stanje — 2026-11-10
sources:
- resource: /reports/firehose-verification/verification.json
- resource: /docs/WORK_LOG.md
---
# Trenutno stanje — 2026-11-10

## Najnovije — 2026-11-10: faza 2 je završena, PPO se ne razlikuje od jednostavnih pravila (ADR-032)

Benchmark i studija budžeta u SimFire-u na zamrznutom zapisu iz faze 1, po ADR-030 §4, bez
izmjena nakon rezultata. Grana `f/task-026-stage-2`, PR čeka korisnikov merge.

- **Trening.** 10 seedova (11–20): osnovni PPO na B=2 i tri fine-tunea po seedu, ukupno 40
  politika i 171,360 odluka na 98 TRAIN požara.
- **Zaključano prije VALIDATION-a.** Najbolja TRAIN heuristika na B=2 je `advancing_front`
  (−194.4 ha prema no-opu; `downwind` −187.7). Izbor i hashovi 40 modela su commitovani prije
  jedinog VALIDATION benchmarka.
- **Šest primarnih testova: nijedan ne odbacuje nultu hipotezu.** Osnovni PPO minus nasumična
  legalna linija: −5.5 / +13.6 / +40.4 ha na B=1/2/4. Osnovni PPO minus `advancing_front`:
  −14.9 / −2.1 / −36.8 ha. Svi intervali uključuju nulu; najmanji Holm p je 0.145.
- **Fine-tuning po budžetu** ne daje mjerljiv dobitak.
- **Prema no-opu** (samo provjera): svaka porodica politika u prosjeku spali manje, 0.3–8% od
  prosjeka no-opa (3,464 ha po požaru). `downwind` je najbolji na svakom budžetu.
- **Linija spali više od no-opa** u 48 od 2,379 epizoda s linijom (2.0%), na 3 od 20 požara.
- **Šta su politike naučile.** Sedam od deset osnovnih politika u svakoj epizodi kreće istim
  smjerom, bez obzira na požar; 40 politika daje 10 različitih ponašanja, a tri fine-tune
  politike nikad ne postave liniju.
- **Granice.** 20 VALIDATION požara i široki intervali (oko ±100 ha na B=2), pa „ne razlikuje
  se“ nije isto što i „nije bolji“. Tri od šest procjena mijenjaju predznak kad se izostavi
  scenarij s najvećom apsolutnom razlikom u tom poređenju. Rezultat važi za free-burning
  zapis iz ADR-031 i nije dokaz o stvarnom gašenju.
- **Dalje.** Faza 3 ne kreće bez korisnikove odluke o glavnom simulatoru i o observationu u
  sintetičkom CA. TEST 2024 je zatvoren.
- **Dokazi.** [ADR-032](specs/DECISION_RECORDS.md), EXP-020,
  [analiza](../reports/real-fire-data/feds-simfire-budget-benchmark-adr030-v1.json),
  [zapis o pokretanju](../reports/real-fire-data/feds-simfire-budget-run-record-adr030-v1.json),
  [grafikon](../reports/real-fire-data/feds-simfire-budget-benchmark-adr030-v1.png).

## 2026-11-09: faza 1 je prošla (ADR-031)

Prvi gate na ispravljenim ulazima (vrijeme `7a51aadd…`, manifest `013be9a1…`), po pravilu
iz ADR-030 §3 koje nije mijenjano nakon rezultata. Grana `f/task-026-stage-1`, PR čeka
korisnikov merge.

- **TRAIN gate: PASS.** 17 fiksnih kandidata × 98 požara, svi bez grešaka. Prolazi 8 od 17;
  7 pada zbog dodira s rubom mape, 2 zbog IoU rasta ispod elipse.
- **Izabrano i zamrznuto: WAF 0.10 / ROS 1.0.** Na 82 rastuća požara srednji IoU rasta je
  0.0958 prema 0.0258 za elipsu, bez dodira s rubom. SimFire je bolji od elipse na 59 od 82.
  Zapis: `configs/frozen/feds-simfire-growth-gate-freeze-v1.json` (sha256 `7639e3a9…`),
  dodan u allowlist u istom commitu, prije VALIDATION-a.
- **VALIDATION, jednom.** 20/20 bez grešaka i bez dodira s rubom; na 18 rastućih IoU rasta
  0.0983 prema 0.0278. Nije korišten za izbor.
- **Elipsa je niska letvica.** Do +48h dodaje u prosjeku 23 ćelije, a rastući požari su
  u FEDS-u dobili 1,219. Prolazi i kandidat bez vjetra (WAF 0, 0.0545). Na rastućim požarima
  izabrana postavka raste 1.8× više od opaženog.
- **Granice.** Oba IoU rasta su ispod 0.10. Na 16 nerastućih TRAIN požara no-op dodaje u
  prosjeku 8,976 ha više nego što je FEDS opazio do +48h, a srednja apsolutna greška
  površine je 4,120 ha (persistence 2,371 ha). PASS znači da SimFire smješta rast bolje od
  fiksne elipse; nije fizička validacija ni kalibracija simulatora.
- **Dalje.** Faza 2 je izvedena s ovim zapisom (gore, ADR-032). Merge i faza 3 ostaju
  korisnikovi; TEST 2024 je zatvoren.
- **Dokazi.** [ADR-031](specs/DECISION_RECORDS.md), EXP-019,
  [TRAIN gate](../reports/real-fire-data/feds-simfire-train-growth-gate-v1.json),
  [VALIDATION](../reports/real-fire-data/feds-simfire-validation-growth-gate-v1.json).

## 2026-11-09: rezultati ADR-022–028 nevažeći do ponovnog pokretanja (ADR-029)

- **Greška u podacima.** gridMET uzorkovanje je za svaki požar u godini koristilo ćeliju
  prvog požara te godine: 97/99 TRAIN i 19/20 VALIDATION požara imalo je tuđe vrijeme
  (medijan 782 km). Ispravka je u PR #3 (lokalna regeneracija: 118 ćelija za 119 požara,
  najviše 2,8 km).
- **Posljedica.** SimFire gate (ADR-022–024), validacija, benchmark i studija budžeta
  (ADR-024–027) i test CA politika na 119 požara (ADR-028) nisu važeći zaključci.
  Sintetička provjera na proceduralnim požarima (ADR-028, seedovi 0–255) ne koristi gridMET,
  ali ima druge greške (napredak linije, ćelije linije kao "spašene").
- **Stanje grana.** PR-ovi #3–#5 su spojeni u `main` merge commitima kao historija; grane
  ostaju. Ispravke idu kao novi PR-ovi (TASK-021–024), zatim odluke (TASK-025) i ponovno
  pokretanje (TASK-026). Plan: [NEXT_SESSION](NEXT_SESSION.md), odluka: ADR-029.
- **Ispravke spojene (2026-11-09).** TASK-021–024 su nezavisno revidirani, popravljeni i
  spojeni (PR #8, #9, #11, #12); 223 testa prolaze lokalno, CI `numeric` provjerava tačan
  spisak preskočenih. Faza 1 čeka TASK-027, novi gridMET fajl i nalog.
- **TASK-027 (2026-11-09, grana `f/task-027-feds-utc-dedup`).** Manifest ima jedan zapis po
  FEDS požaru: 98 TRAIN i 20 VALIDATION (columbus isključen). FEDS `t` nije UTC nego oznaka
  VIIRS prolaza u lokalnom sunčevom vremenu; korisnik je izabrao preračun 01:30/13:30 lokalno
  → UTC po dužini (dopuna ADR-030). Novi gridMET fajl je napravljen lokalno (sha256
  `7a51aadd…`, 118 ćelija za 118 slučajeva, svi s `pre_start`); hash je u
  [coverage reportu](../reports/real-fire-data/feds-gridmet-weather-coverage-v1.json).
  Spojeno kao PR #15. Faze 1 i 2 agent smije pokrenuti sam (faza 2 samo ako faza 1 prođe;
  dopuna ADR-030, [handoff](HANDOFF_STAGE_1_2.md)). Faza 1 je izvedena (gore, ADR-031).
- **Odluke za ponovno pokretanje (ADR-030).** Gate na IoU rasta prema downwind elipsi,
  vrijeme prethodnog segmenta u observationu, linija neovisna o koraku, 10 seedova i
  poređenje s nasumičnom linijom; ponovno pokretanje ide u tri faze uz nalog za svaku.


## Najnovije — 2026-11-05: sintetički CA trening (ADR-028)

Korisnik je 2026-11-04 tražio da se agent trenira samo na sintetičkim požarima, uz
fizička ograničenja jedinica, a da se stvarni podaci ostave za test. Rad je na grani
`codex/synthetic-ca-training`, izvedenoj iz `codex/overnight-steps-5-8`; ništa nije spojeno.

- **Okruženje.** Vlastiti CA ([spec](research/SYNTHETIC_CA_ENV.md)):
  - vjerovatnoća paljenja po tipu goriva (Anderson 1982), uz vjetar, nagib, vlagu i
    dnevni ciklus;
  - ručne ekipe i dozeri s brzinama iz PMS 410-1 (bez teleportacije);
  - kontrafaktualna nagrada protiv no-op rollouta na istim slučajnim brojevima;
  - LCES povlačenje, kazna za bliske susrete i velika kazna za izgubljenu jedinicu.
- **Trening.** PPO od nule (main-1) nije dostigao heuristiku. Plan B (imitacija
  direct_flank, pa PPO) dao je zaključanu politiku `policy-v1`.
- **Sintetička provjera (0–255).** policy-v1 je izjednačen s najboljom heuristikom
  (FAIL po preregistrovanom kriteriju) i jasno bolji od no-op (+0.10 povrata).
- **Stvarni slučajevi (119, jednokratno, simulirani ishod).** policy-v1 čuva 12% više od
  no-op (CI [8.9%, 15.4%]). Sačuvana površina je jednaka kao kod bočnog napada, uz upola
  manje bliskih susreta.
- **Jaz kalibracije.** Medijan IoU na 48h je 0.27–0.30; simulator uglavnom prerasta
  stvarne (gašene) požare.
- **Granica tvrdnje.** Rezultati su simulatorski i nisu dokaz o stvarnom gašenju.
- **Gdje su detalji.** ADR-028 i dopune, EXP-015–017, [izvještaji](../reports/synthetic/index.md).

## Najnovije — 2026-11-04: koraci 5–8 izvedeni (noćni samostalni rad)

Korisnik je 2026-11-03 tražio samostalan rad kroz korake 5–8 bez pitanja, uz nastavak
kao eksploratorni rad ako gate ponovo padne. Rad je na grani `codex/overnight-steps-5-8`,
izvedenoj iz `codex/fireline-simfire-benchmark` (PR #3); ništa nije spojeno.

**Korak 5 — kalibracija (FAIL).** Ulazi su ponovo izgrađeni na drugom računaru i
bajt-identični su commitanim hashovima; WAF .01 run reproducira ADR-022 tačno.
[Dijagnoza](../reports/real-fire-data/feds-simfire-train-noop-diagnosis-v1.json): IoU
deficit dolazi iz požara koji u FEDS-u gotovo ne rastu; na brzo rastućim SimFire već
pobjeđuje persistence. Preregistrovana 3×3 mreža (ROS × WAF, ADR-023) nije prošla; najbolji
kandidat ROS .35 / WAF .05 (IoU .5266 prema .5343) je zamrznut kao `FAIL_exploratory`, ali
praktično ne širi vatru (medijan 0 novih ćelija za 48h).

**Korak 6 — validation.** Validation rasteri (20/20) su preuzeti; preuzimanje je krenulo oko minutu prije freeze commita, ali ništa nije simulirano ni skorirano prije njega (ADR-024). Validation rezultati su dobijeni poslije pada gatea i nisu korišteni za izbor kandidata, parametara ni odluku o gateu. Svaki
zamrznuti zapis skoriran jednom ([izvještaj](../reports/real-fire-data/feds-simfire-validation-noop-v1.json)):
gate freeze IoU .5419 prema persistence .5432 (FAIL); free-burn stress zapis (WAF .01 /
ROS 1.0, ADR-024) IoU .5452 i 1,275 ha prema 1,502 ha, pa prolazi strogo pravilo samo na
VALIDATION-u. Zbog pada na TRAIN-u i 20 slučajeva to nije dokaz kalibracije.

**Korak 7 — intervencije i benchmark (ADR-025).** Jedinica budžeta = smjena ekipe od 20
ljudi = linija od 7 ćelija (~1.26 km), uz NWCG raspon učinka. Linija se postavlja 360 m
ispred vodećeg dijela fronta u izabranom sektoru. Četiri heuristike (no-op, random,
downwind, advancing-front) dobijaju istu opservaciju i masku kao PPO. Upareni benchmark
provjerava determinizam na B=0.

**Korak 8 — prilagodba budžetu (ADR-026/027), na stress zapisu.** 5 seedova × (osnovni PPO
na B=2 + fine-tune na B=1, B=4 i kontrola B=2) = 20 modela; 1,920 uparenih VALIDATION
epizoda. No-op dodaje 324 ha po požaru. Zamrznuti osnovni PPO smanjuje štetu kod B=2 i
B=4 (−16.6 i −19.7 ha, dvoslojni 95% CI ispod nule); kod B=1 je efekat (−5.1 ha) granični.
**Fine-tuning po budžetu nema mjerljive koristi** (−0.4 i +0.6 ha prema osnovnom; +0.9 i
−1.6 ha prema kontroli), ali s 5 seedova se efekti od oko ±12–20 ha ne mogu isključiti
(ADR-027 dopuna). Ni na 99 TRAIN požara fine-tuning ne pomaže, pa to nije overfitting nego
slab signal budžeta. Downwind heuristika (−28 ha za B=2/4) je jednako dobra ili bolja.
[Sažetak](../reports/real-fire-data/feds-simfire-policy-benchmark-v1.json),
[grafikon](../reports/real-fire-data/feds-simfire-policy-benchmark-v1.png).

**Granice.** Sve su to simulatorski rezultati na nekalibrisanom free-burn scenariju, ne
fizička validacija niti dokaz stvarne koristi gašenja. Većina simuliranih požara se ugasi
u prvih 12h, pa veći budžet rijetko ima gdje da se potroši. Prioritetna područja (TASK-007)
nisu rađena. TEST 2024 je i dalje zatvoren.

## 2026-11-03: SimFire/FEDS data i runtime setup



Korisnikov benchmark pravac ostaje SimFire + FPA-FOD/FEDS-CONUS, uz FLE/ICS-209 kao
ograničeni post-hoc kontekst. Originalna 60-case FPA-FOD kohorta, ponovljena nad
lokalnim checksum-verifikovanim FEDS arhivama, ima 19/40 train i 7/20 validation
slučajeva; zato ne prolazi prag 20/8.

Da se ne dodaje jedan požar post-hoc, napravljena je eksplicitno dokumentovana šira
kandidat-kohorta iz cijelog sačuvanog FPA-FOD screen okvira za iste dozvoljene godine:
208 train zapisa (2018/2019) i 56 validation (2023). Uz nepromijenjeno FEDS spajanje,
99 train i 20 validation slučajeva imaju jedinstven početni match i ≥2 uzastopna 12h
stanja; svih 119 imaju punih pet 12h stanja od početka epizode do +48h. Pre-agent data
coverage gate za taj revidirani okvir je **PASS**. Candidate frame uključuje samo
prijavljene požare ≥5.000 acres u deset zapadnih država, zato nije reprezentativan za
sve požare; završna površina/MTBS ne ulaze u FEDS ID spajanje ni agentovu informaciju.

FEDS `lf_perimeter` i `lf_fireline` arhive za 2018/2019/2023 su checksum-verifikovane.
Aktivni front je dostupan na tačnom početnom vremenu za svih 119 epizoda (99 train,
20 validation). Geometrijski preflight potvrđuje da cijeli početni obod/front stane u
256×256×180m mapu za 119/119 slučajeva. U gridMET-u su uzorkovana četiri 12h forcing
intervala za svaki slučaj (396 train, 80 validation); wind-adjustment faktor nije
izabran. Test 2024 nije preuzet ni učitan.

Python 3.9.25 SimFire venv je postavljen u ignorisanom `.local/simfire-venv`; svih 85
paketa prolazi `uv pip check`. LANDFIRE fuel/elevation i FEDS početne maske su preuzeti
i provjereni za **99/99 train** slučajeva. Njihov coverage report bilježi SHA-256 za 198
GeoTIFF-ova. Validation rasteri ostaju odloženi dok se train parametri ne zaključe.
60-min demo-weather integration smoke radi, ali nije historijska validacija.

Dodani su 48h no-op runner i metrički helpers. Jedan TRAIN Plateau pilot pokazuje oštar
WAF prag: 0.20–0.60 daje 61.56 ha (tri nova rastera, IoU .64) naspram 71.28 ha opaženih;
0.65 daje 1,244 ha u prvih 12h, a 0.75–1.0 višestruko više i dodiruju rub do 48h.
Taj pilot nije bio cohort-level gate. Testni interni korak od 5 minuta čuva 90-min
ćelijsko trajanje kao 18 update-a; visoko-šireći 48h pilot trajao je oko 40 sekundi.

### TRAIN-only no-op screening — završeno, gate FAIL

Osam WAF kandidata pokrenuto je na svih 99 TRAIN slučajeva, svaki kroz 48h i četiri
poređenja (396 case-timepointa po kandidatu), uz isti 5-min interni korak i seed=0.
Svaki run je završio 99/99 slučajeva bez greške. Future FEDS obodi učitavani su tek
nakon simulacije i korišteni samo za post-hoc scoring. Referentne metode su početna-mask
persistence i unaprijed definisana 2:1 downwind elipsa.

| WAF | Mean IoU | Mean apsolutna greška površine (ha) | Rubni kontakti |
|---:|---:|---:|---:|
| 0.0000 | 0.4768 | 2,263.1 | 0 |
| 0.0025 | 0.4769 | 2,265.0 | 0 |
| 0.0100 | 0.4769 | 2,262.1 | 0 |
| 0.0250 | 0.4679 | 2,314.2 | 0 |
| 0.0500 | 0.4386 | 2,483.8 | 0 |
| 0.1000 | 0.3854 | 3,360.1 | 1 |
| 0.2000 | 0.2984 | 7,176.8 | 22 |
| 0.6050 | 0.1425 | 27,624.2 | 157 |

Persistence ima mean IoU **0.5343** i mean area error **2,351.7 ha**; elipsa ima
**0.5308** i **2,346.6 ha**. Nijedan WAF nije nadmašio obje reference po oba kriterija
uz nula rubnih kontakata. Zato **TRAIN no-op gate nije prošao** i WAF/timebase nisu
zaključani. Najniži WAF-i su nešto bolji po površinskoj grešci, ali gube oko 0.054
mean IoU prema objema referencama. Detaljni receipt i hashovi su u
[TRAIN no-op screen reportu](../reports/real-fire-data/feds-simfire-train-noop-screen-v1.json);
raw 1MB izlazi svakog kandidata ostaju ignorisani u `.local/`.

Jedna timebase osjetljivost za WAF 0.01 na 1-min koraku takođe završila je 99/99 bez
grešaka i rubnog kontakta; mean IoU .4771 naspram .4769 na 5-min koraku (razlika
.0003). Nalaz je praktično isti, pa 3/10/15-min koraci nisu pokretani; interni korak
ostaje neizabran.

Korisnik je tražio da može trenirati bez novog setup ciklusa. Dodani su TRAIN-only
Gymnasium/MaskablePPO adapter i CLI nad 99 dostupnih TRAIN epizoda: 48h/four 12h odluka,
budžet, no-op i osam kratkih sektorskih fireline akcija. Potvrđeni su reset/step na
stvarnom Plateau inputu, fiksni horizont nakon gašenja vatre, te četiri budžet/šteta
regresijska testa. Dodatni TRAIN action smoke sa budžetom 1 postavio je legalnu
fireline akciju, potrošio jednu jedinicu i završio sva četiri koraka. Završio je bounded
smoke od 64 PPO koraka; checkpoint je sačuvan i ponovo učitan, pa je odrađen dodatni
4-korak TRAIN rollout na
`fpa-fod-400500346-south`. Checkpoint i receipt su samo u ignorisanom
`.local/feds-ppo-smoke-waf-0.605-64steps/`. WAF se mora eksplicitno zadati i ostaje
provisional.

Završna QA: SimFire Python 3.9 suite 65/65 PASS; project Python 3.12 suite 62 PASS uz
9 optional-dependency skips; strict knowledge validation 69 Markdown PASS; CLI smoke,
85-package `uv pip check` i `git diff --check` PASS.

**Research gate je pao na TRAIN no-op poređenju:** prije validacijskih mapa treba
dijagnosticirati zašto SimFire prostorni rast zaostaje za obje reference i definisati
novi zajednički kandidat. Validation rasteri nisu preuzeti; 2024 TEST ostaje zatvoren.
Tehnička PPO putanja radi, ali duži policy trening/benchmark nije mjerodavan dok gate ne
prođe. Komande i ograničenja su u
[environment record](research/SIMFIRE_ENVIRONMENT.md),
[ADR-022](specs/DECISION_RECORDS.md), [NEXT_SESSION](NEXT_SESSION.md) i
[TRAIN reportu](../reports/real-fire-data/feds-simfire-train-noop-screen-v1.json).

Rad je izolovan na `codex/fireline-simfire-benchmark`, izveden iz `main`. Tri
necommitovane izmjene u glavnom checkoutu i stara `research/cfsds-train-qc` grana su
sačuvane. U ovoj grani nema tuđih report fajlova, sirovih arhiva, model težina ili
long-running treninga.

## Historijski status — CFSDS/Firehose, 2026-10-30

Sadržaj ispod ovog naslova dokumentuje raniji CFSDS/Cell2Fire track i runtime rad.
Njegovi nalazi nisu prošireni na novi SimFire/FEDS benchmark.

## Baza znanja u repozitoriju
Repo je OKF 0.2 bundle s [root indeksom](../index.md),
[sažetim kontekstom](../knowledge/project-context.md), [mapom koda](../knowledge/code-map.md)
i [pravilima održavanja](../knowledge/maintenance.md). Dokumenti imaju tipove,
lowercase indekse i navigaciju; agent ulazi dijele isti AGENTS kontekst. Zaseban
knowledge checker/CI čuva strukturu i lokalne linkove. Migracija ne zatvara dataset
refinement niti uvodi naučnu/humanu verifikaciju sadržaja.
Provjera: [63 Markdown fajla, 15 knowledge testova i clean-clone dokaz](../reports/knowledge-validation.json).
Osnovni aplikacijski paket i dalje nema dodatne zavisnosti; PyYAML je samo knowledge alat.

## Lokalni workspace
Trenutni projektni checkout je repo root na grani `feature/project-bootstrap`, koja
odgovara `origin/feature/project-bootstrap` na commitu `1499890`. `main` je i dalje na
početnom commitu; feature grana nije spojena. U ovom workspaceu nema zasebnog nested
`.worktrees/project-bootstrap/` checkouta: aktivna grana je na root putanji. Runbook za
čiste klonove i lokalno ignorisane artefakte je u
[workspace layout dokumentu](../knowledge/workspace-layout.md).
[Provjera preseljenja](../reports/workspace-relocation.json): 13,246 ne-venv fajlova
i 11 backup fajlova sa istim hashovima, 19 sačuvanih verzija paketa, ispravljene
lokalne venv putanje, 26 aplikacijskih/15 knowledge testova i 64-file OKF provjera.

## Najnoviji pomak
**Cell2Fire je kompajliran i oba postojeća 20×20 Firehose PPO checkpointa rade.**
Izvršeno je 12 kratkih inference rollouta, bez treniranja, u odvojenom Linux ARM64
kontejneru sa SB3/contrib 1.5.0 i Gym 0.21.0. Runtime gate je prošao.

- Isti input/seed ponavlja kompletan niz akcija/state hashova; drugačiji C++ seed mijenja širenje.
- Budžet B=8 se poštuje; zatim no-op do simulator done. Težine ostaju nepromijenjene.
- Svi subprocess returncodeovi su 0. Kontrole: no-action, min-L2, max-L2 i dva checkpointa.
- Zabilježen input hash, izvorni commitovi, model hashovi, verzije i Docker image ID.
- Dataset card: 141 fajl, 400 ćelija (307 gorivih), 130 weather fajlova sa po 8 redova.

## Izabrani real-fire podaci i stvarni pilot — 2026-10-30

Odabrana je **Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire** jer najbolje odgovara
postojećem simulatoru i 20×20 agentu. CFSDS v1.1 ima 5,435 kanadskih požara za
2002–2024, 90 m satelitski interpolisanu dnevnu kartu gorenja. Službeni CFSDS rad
opisuje MODIS/VIIRS hot-spot interpolaciju; noviji W.I.S.E. rad ponavlja da je za
kompatibilan no-action benchmark potrebno znatno strože birati događaje. [CFSDS rad](https://doi.org/10.1038/s41597-024-03436-4), [W.I.S.E. procjena](https://doi.org/10.1071/WF26072).

Preuzeto je 23 godišnja ZIP para 2002–2024 (102,405,239 bajtova ukupno) lokalno u
Git-ignorisan `data/raw/cfsds-v1_1`; datoteke su provjerene prema OSF manifestu. Prvi
screen za godine 2014–2024 pregledao je 3,141 događaj/82,015 dnevnih redova i
zadržao najviše pet geometrijski pogodnih događaja po godini: ukupno 44, podijeljena
po godini požara u 20 train, 9 validation i 15 test kandidata. Ovaj spisak nije
iscrpan niti pun benchmark; svi dani jednog požara ostaju u istoj particiji.
[Screen izvještaj](../reports/real-fire-data/cfsds-cohort-screen.json),
[kohort manifest](../data/manifests/cfsds-v1_1-pilot-cohort.json).

**Prvi simulator slučaj `2018_747`, target 16.08.2018:** napravljena je 20×20 × 100 m
karta s Canadian FBP 2014b gorivima, MRDEM 30 m terenom, ERA5-Seamless satnim vremenom,
prethodnim požarnim stanjem i zasebnim targetom za naredni dan. Sve ćelije u scar/front
/target su na podržanom C-3 ili D-1 gorivu. C++ je prihvatio 175 ranije opožarenih i
31 aktivnu ćeliju. Šest no-action seedova (123–128; bez treniranja/intervencija) završilo
je uspješno. Svih šest dalo je istu mapu od 66 ha prema CFSDS cilju 15.39 ha (IoU 0.2187),
a novo širenje dodirnulo je 19 rubnih ćelija našeg 2×2 km isječka. Trajanje runova se
razlikovalo. Dakle konverzija radi, ali
ovaj replay pokazuje veliko neslaganje i rubni efekat; ne validira fiziku niti dokazuje
korist agenta. [Replay mjere](../reports/real-fire-data/2018_747-day228-replay.json),
[mapa](../reports/real-fire-data/2018_747-day228.png).

**Dodatne train provjere, bez treniranja:** `2018_241` i `2018_1770` su pretvoreni i
pokrenuti od historijskog stanja bez početnog zagrijavanja. Bez gašenja je simulator u
prvom slučaju zahvatio svih 400 ćelija: 237 ha novog gorenja prema 12.15 ha opaženih
(IoU 0.0376). U drugom je dodao 73 ha prema 12.15 ha (IoU 0.1361). `2018_241` je dao
iste mjere i kad uključimo 20 minuta zagrijavanja, pa to zagrijavanje nije glavni uzrok
neslaganja. Kandidat `2014_538` nije prošao konverziju jer dio historijskog scar/fronta
upada na vodu ili ne-gorivo u FBP 2014b karti. Ovi nalazi potvrđuju da geometrijski
odabrani kandidati još nisu provjereni slučajevi. [2018_241 mjere](../reports/real-fire-data/2018_241-day227-replay.json),
[2018_1770 mjere](../reports/real-fire-data/2018_1770-day224-replay.json),
[odbijeni `2014_538`](../reports/real-fire-data/2014_538-fuel-rejection.json).

Nakon izmjene probe opcije i C++ initial-state podrške, novi isolated Docker image je
ponovo prošao svih 12 kratkih postojećih Sub20 inference slučajeva; PPO težine su ostale
iste. Sažetak: [regression receipt](../reports/firehose-verification/real-case-image-regression.json).

CFSDS target je dnevna satelitska procjena, ne tačan satni ground-truth front; suppression
status nije spojen. FBP karta je 250 m resamplovana na 100 m, DEM 30 m, a vrijeme je
reanalysis tačka 5.2 km od centra. Dnevni FWI kodovi su ponavljani kroz 24 sata zbog
nedostatka satnih vrijednosti u CFSDS. Za heldout 2019/2022–24 još treba odgovarajuće
fuel-map vintages (2019/2024) i kvalitetni inputi. BiH/MedEU ostaje kasnija odvojena
studija jer njegovi evropski NFFL fuel kodovi nisu isti kao Canadian FBP.

Sljedeći posao: sistemski provjeriti gorivo, vrijeme, FBP parametre i veličinu domene na
train slučajevima, pa utvrditi postoji li konfiguracija Cell2Fire koja prođe no-action
gate bez podešavanja na validation/test ciljevima. Preostaje TASK-004c terminal/damage
export; multi-cell
initial-state import (TASK-017) i tri train FireCase konverzije/no-action replaya (TASK-016)
su ostvareni. Glavno treniranje je na čekanju dok no-action gate ne bude prihvatljiv
na više train slučajeva; test skup se ne koristi za kalibraciju.

## Environment reproducibility — 2026-10-30

U feature checkoutu je napravljen moderni Python 3.12.4 `.venv` s optional RL, GIS i
knowledge alatima. Geospatial stack je izolovan: rasterio 1.4.4, geopandas 1.2.0,
pyproj 3.8.0, xarray/rioxarray, netCDF4, SciPy, CDS API klijent i ostale zavisnosti;
GeoTIFF nearest-neighbour reprojection/import smoke je prošao. Kombinovani freeze je
`requirements/research-macos-arm64-py312.freeze.txt`. Prošlo je 26 aplikacijskih testova, 15 knowledge testova, strogi checker za
67 Markdown fajlova, synthetic CLI smoke i 1,024-koračni synthetic PPO
smoke. Legacy Firehose image je svježe izgrađen na Linux ARM64 iz pinovanih upstream
commitova; 12/12 inference slučajeva su prošli, sa ugašenom mrežom i bez treninga.
Tačne verzije i image/source hashovi su u [environment receipt](../reports/environment-setup/README.md).
Ovaj setup ostavlja known adapter mismatch aktivnim; environment PASS nije research-ready.

Dogrib gorivo/elevation dijele blok sa Sub20 mapom, pa nije nezavisan test prostorne
generalizacije. MedEU je zaseban mogući evropski track, ali nije potreban za glavni
Canadian FBP projekat i još nije pretvoren u simulator input.

## Ograničenja koja su stvarno potvrđena
Legacy fixed-model reset i brojač za početni Sub20 warmup i dalje imaju poznatu razliku
(206 naspram 207); eksplicitni sync reset je daje 207/207. Stvarni CFSDS pilot koristi
poseban multi-cell importer i provjerava početni C++ grid. Preostali TASK-004c treba da
izveze kumulativnu štetu i jasan terminalni razlog za online RL adapter. Simulatorov
`done` ne razlikuje containment od vremenskog horizonta; zato **research_ready=false**.

## Ostalo što radi
Baza zahtjeva/rubrike/literature/odluka, synthetic-v1 engine i pet baseline politika,
upareni eksperimenti i manifesti, 300-epizodni sintetički replay, moderni Gym/PPO smoke.
Prethodni sintetički artefakti ostaju historijski dokaz; nisu Cell2Fire rezultati.

## Dokazi
- [Runtime nalazi](research/FIREHOSE_VERIFICATION.md), [dataset](research/DATASET.md).
- `reports/firehose-verification/`: input inventar, 12 rezultata, summary, checks, environment.
- 26 testova prolazi s modernim optional environmentom; 22 core + 4 optional RL testa.
- Originalni Firehose i contrib checkouti ostaju neizmijenjeni; samo build flagovi i
  eksplicitna dijagnostika reset/seed ponašanja su dodani u naš kod.
- Docker/legacy i moderni .venv su odvojeni. Legacy inference je bez treniranja i
  plaćenog compute-a. Kod/dokumentacija su objavljeni kroz [PR #1](https://github.com/goralija/wildfire-rl-adaptation/pull/1).

Sljedeće: pilot replay review i fuel/terrain/weather/domain dijagnostika → nekoliko
train-only no-action replaya → FBP fuel vintages za heldout godine + suppression/QC
spajanje → zamrzavanje event testa → preostali TASK-004c adapter → upareni benchmark /
treniranje samo nakon prolaza replay gatea.
Nema provjere fizike simulatora na BiH podacima, potvrde RL prednosti ili generalizacije.
Deadline/compute i licence za sirove podatke ostaju otvoreni.

## Pregled i odgođena sitnica
I bootstrap i novi runtime pregled su prošli bez kritičnih ili važnih nalaza.
Novi pregled nezavisno potvrđuje testove, evidence/provenance i dataset hashove.
Jedan stari minor ostaje TASK-010:
JSON null config u synthetic CLI-u daje traceback umjesto uredne poruke.

## Handoff za kolegu
[HANDOFF](../HANDOFF.md) sadrži prenosiv clone/setup, put do legacy runtimea,
pribavljanje lokalnih podataka i trenutno stanje replaya.
Za objavu ponovo prolazi svih 26 testova u modernom environmentu. Čisti lokalni
Git klon s novim venvom i bez dodatnih paketa prolazi 22 testa (4 optional preskočena)
i synthetic smoke; originalni lokalni setup nije preduslov za taj početak.
Korisnik je odobrio objavu cijele feature grane i PR prema početnom mainu; ADR-008.
