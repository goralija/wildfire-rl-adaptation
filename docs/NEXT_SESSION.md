---
type: Handoff
title: Naredni korak — nakon CA pilota (2026-11-21)
---
# Naredni korak

## TASK-038 završen — CA v2 BC/PPO (ADR-042, 2026-11-21)

Na `codex/ca-learning-pilot` iz3b7b56a2 završen je [kratki CA learning pilot](research/CA_LEARNING_PILOT.md).
Plan6f2e4b61 prethodi treningu.32TRAIN požara ×3rostera daju96demonstracija/1.152stanja;
tri seeda17/29/43 uče60BC epoha pa svaki tačno4.096PPO koraka. Svi posjećuju96TRAIN kombinacija.

Svih6 modela ×16development požara ×3rostera =288putanja prolazi tehničke provjere.
BC prosjek3,08%, BC+PPO2,98%, referenca direct_flank7,46% spašene težinske štete.
PPO minus BC −0,105p.p., opisni interval[−2,08;+1,21]. Nijedan kandidat ne prolazi
registrovani kriterij nastavka. Modeli imaju2–5 bliskih susreta po seedu prema20 kod
heuristike, svi0gubitaka u uzorku; nema dokaza RL prednosti ili stvarne sigurnosti.

362pinovana testa, moderni347/3skip, core286/40skip, dodatni aktivni checkpoint testovi,
knowledge15/15/strict87 i CLI PASS. Numeric NPZ težine su lokalne s provjerenim hashovima;
stari checkpointovi nisu korišteni. Završni poslovi traju oko7,5min na nice19, max4procesa.
Naredni prijedlog TASK-039: TRAIN dijagnoza učiteljskih/modelskih putanja i kodiranja,
pa kratak unaprijed zadat nastavak ako je opravdan. Dugi trening, proceduralni test i
stvarni VALIDATION/TEST ostaju zatvoreni; nema aktivnog runa. CA nije fizički validiran.

Redoslijed: provjeriti sačuvane manifeste i rezultate, pročitati ADR-042, potom TASK-039
plan prije novih poteza/treninga. Ne ponavljati završeni pilot bez razloga i ne otvarati
testne liste. Stari tekst TASK-038 kao prijedloga ili rada u toku je historija.


## CA ugovor i pilot završeni — TASK-035 / ADR-040 (2026-11-21)

Korisnikov CA nastavak je izveden na `codex/ca-controlled-pilot`, iz `664d890d` završene
SimFire repair grane. [Izvještaj](research/CA_CONTROLLED_PILOT.md) i zamrznuti plan čuvaju
razlog prelaska: naučeni SimFire modeli nisu nadmašili jaču heuristiku; nije proglašena
iscrpljenost SimFire-a. Plan commit `c8d8563c` prethodi kodu i rezultatima.

CA v2 daje isto native opažanje i current forcing svim politikama; heuristike rade samo
iz opažanja/maski. Svih16 development požara ×3 rostera ×5 politika =240 epizoda prolazi.
`direct_flank` čuva7,46% težinske štete prema0,24% randoma; opisna razlika7,23p.p.,
95% interval[0,44;16,49]. Ima20 bliskih susreta i0 gubitaka kroz48 epizoda. Nema RL modela
ili potvrđene sigurnosne prednosti. Prvi case replay15/15 je identičan.

352 pinovana testa bez skipa; moderni337/3 skip i core284/38 skip, CLI i knowledge PASS.
TASK-035 je završen. Naredni TASK-038 je v2 encoder/provenance i kratak preregistrovan
BC/PPO, uz jaku heuristiku i odvojene sigurnosne kriterije. TASK-037 SimFire je odgođen.
Train/test proceduralne liste su rezervisane, nisu generisane/skorirane; stvarni
VALIDATION i TEST 2024 ostaju zatvoreni. Stari checkpointovi i dugi trening nisu korišteni.
CA je vlastiti pojednostavljeni simulator, ne Cell2Fire ili fizička validacija.

Redoslijed nastavka: pročitati CA izvještaj/ADR-040, provjeriti manifeste i sačuvane
ishode, zatim napisati TASK-038 plan prije novih modela ili metrike. Ne ponavljati
završeni pilot bez razloga. Nijedan dugi posao trenutno ne radi.


### Objava CA grane

Grana [codex/ca-controlled-pilot](https://github.com/goralija/wildfire-rl-adaptation/tree/codex/ca-controlled-pilot)
je commitana i pushana. [CI na kodnom/rezultatskom commitu3ad3f72c](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44836958711)
prolazi sva četiri posla. Publication zapis je u CA verification JSON-u; kasnija dopuna
publikacijskih podataka ne mijenja numerički kod. Nema novog PR-a, mergea ili aktivnog runa.


## Objava i pregled (2026-11-20)

Grana [codex/simfire-observation-repair](https://github.com/goralija/wildfire-rl-adaptation/tree/codex/simfire-observation-repair)
je pushana. [CI kodnog/rezultatskog commita1cabe778](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44817109635)
prolazi core3.11/core3.13, numeric i knowledge. Nema mergea ili novog PR-a po posljednjoj
korisnikovoj poruci; [PR #20](https://github.com/goralija/wildfire-rl-adaptation/pull/20)
prethodnog rada ostaje otvoren. [Publication receipt](../reports/real-fire-data/feds-observation-repair-publication-v2.json)
čuva tačan testirani commit. Kasnija dopuna publikacijskih podataka ne mijenja numerički
kod. Veliki lokalni paket nije uploadovan.

## Nakon v2 popravka — redoslijed (ADR-038, 2026-11-20)

1. Pročitati [završni v2 izvještaj](research/SIMFIRE_OBSERVATION_REPAIR.md) i rezultate.
   FazaA TASK-036 je završena. Ne ponavljati 98 replayeva ili 16 fit kombinacija ako
   sačuvani manifesti i hashovi prolaze. V2 i jača fine+gate heuristika su referenca
   za svaki naredni SimFire pokušaj; ne vraćati se na slabiji comparator bez objašnjenja.
2. Kolege mogu pregledati [PR #20](https://github.com/goralija/wildfire-rl-adaptation/pull/20)
   prethodnog rada i izvedenu `codex/simfire-observation-repair` granu. Novi PR nije
   potreban po korisniku; ništa nije mergeano. Pratiti CI objavljene grane.
3. Predloženi naredni glavni korak je TASK-035: CA ugovor informacija i tehnički pilot
   iz postojećeg drafta. Ne vraćati stare poništene checkpointove ili automatski trenirati;
   prvo definisati opaženo vrijeme, verzije, slučajeve, budžete i jake heuristike.
4. Ako se dalje bira SimFire, TASK-037: max/korak kroz novi TRAIN gate i novu tabelu;
   zatim custom v2 encoder/checkpoint i unaprijed zadati BC/PPO protokol. Povratak na
   B=2/B=4 ne može koristiti B=1 tabelu poslije prve linije.
5. TEST 2024 i nova VALIDATION upotreba ostaju zatvoreni. Raw env nagrada nije promijenjena
   u charged; taj trening ugovor mora biti eksplicitan prije novog PPO-a.

Popravak informacija je potvrđen. Njegov policy dobitak je preliminaran, nijedan
naučeni kandidat ne prolazi, a svih mogućih algoritama/SimFire grešaka nije dokazano odsustvo.

## Korisnikov nastavak — popravak opažanja prije CA (2026-11-20)

Završeni rad je pushan i otvoren kao [PR #20](https://github.com/goralija/wildfire-rl-adaptation/pull/20)
prema `main`, za pregled kolega. PR ostaje otvoren. Korisnik je odobrio još jedan
SimFire pokušaj: TASK-036 sada ima prioritet pred CA pilotom TASK-035.
Nastavak ide iz ove grane u `codex/simfire-observation-repair`, u izdvojenom worktreeu;
novi PR nije potreban po posljednjoj korisnikovoj poruci. Precizni plan ide prije
novih mjerenja. VALIDATION/TEST i novi CA trening ostaju zatvoreni.

## 2026-11-20 — završen TASK-034 (ADR-036)

Ulaz je [završni pregled](research/SIMFIRE_OBSERVATION_AUDIT.md): četiri nested porodice
bez prolaza praga, svi input/observation checkovi, potvrđeni startup fix i mala native
sensitivity studija. Nema aktivnog runa; ne ponavljati eksperimente bez provjere artefakata.

1. Predloženi glavni nastavak: **TASK-035 — CA ugovor informacija i tehnički pilot**,
   [pripremljen draft](../configs/drafts/ca-controlled-pilot-v1.json). Prvo zapisati šta
   CA opaža (sada koristi weather.at(decision)), verziju opservacije i checkpointa,
   razdvojene proceduralne slučajeve, jedinice i budžete. Ne učitavati stare poništene politike.
2. Potom no-op i jake heuristike uz isti scenario, informacije i common random numbers;
   kratki BC/PPO tek po novom protokolu i unaprijed zadanom kriteriju. Sada nije pokrenuto.
3. Opcionalni **TASK-036 — SimFire v2**: kategorijski fuel/nonfuel, reljef/finija opservacija,
   max/korak kroz novi TRAIN growth gate, pa nova tabela i komparatori. To je preostali
   smisleni pravac, ne dokaz da je svaka SimFire mogućnost iscrpljena.
4. TEST 2024 ostaje zatvoren; nema novog VALIDATION odobrenja. Stari CA ADR-028 nalazi
   ostaju poništeni. Novi rad je na lokalnoj grani `codex/simfire-observation-audit`;
   prethodna grana je na originu, ova nije pushana/mergeana. Lokalni paket treba sačuvati.

Preporuka CA pilota je obrazloženi projektni izbor, ne fizička validacija CA ili dokaz
RL prednosti. Precizni CA protokol još nije prihvaćen niti izvršen.

## 2026-11-19 — završen odobreni SimFire ciklus (ADR-034)

TASK-028–030 su završeni na lokalnoj grani `codex/simfire-policy-iterations`.
[Izvještaj i komande](research/SIMFIRE_B1_EXPLORATION.md) su ulaz za nastavak.
Puna tabela 98 požara i svih osam LOO metoda su provjereni; nijedna metoda nije
prešla prag iz ADR-033. Po tom stop-uslovu nisu pokretani novi PPO, holdout ili
CA eksperimenti. PR #19 je već u `main`-u; nova grana je pushana na origin
po korisnikovom nalogu 2026-11-19, bez PR-a ili mergea.

1. Pročitati ADR-034, izvještaj i [manifest lokalnog paketa](../reports/real-fire-data/feds-b1-artifact-manifest-v1.json).
   Ne ponavljati 93-minutnu enumeraciju ako su sačuvani artefakti i hashovi ispravni.
2. Predloženi TASK-034: zapisati mali TRAIN-only protokol za prostorni signal u istom
   opažanju i stabilnost izbora kroz požare. Ne birati nove metode ili pragove na
   postojećim OOF rezultatima pa ih predstavljati kao nezavisnu potvrdu.
3. Zvanični obračun linije, novi observation kanali, B=2/B=4 i novo VALIDATION korištenje
   ostaju otvorene odluke. TEST 2024 ostaje zatvoren; CA nije aktivni pravac.
4. Push grane je urađen; PR i merge nisu. Sačuvati lokalni paket iz `.local/b1/artifacts/`;
   veliki artefakti nisu uploadovani. Njihovo remote arhiviranje ostaje zaseban nalog.

Starije sekcije ispod su historija; njihovo čekanje odobrenja TASK-028–030 je razriješeno.

## Najnovije — 2026-11-12: pregled završen; prvo provjera gornje granice na TRAIN-u

Faze 1 i 2 su gotove, a [pregled 2026-11-11](research/review-2026-11-11/SUMMARY.md) je
odgovorio na pet pitanja nakon ADR-032. Polazna tačka za novu osobu ili agenta je
[HANDOFF](../HANDOFF.md).

1. **Harun:** merge PR #19 (pregled i HANDOFF). Faze 1 i 2 su već u `main`-u (PR #17, #18).
2. **Harun odlučuje:**
   - kako se računa šteta kad linija zauzme ćelije koje bi izgorjele (sada „spašene“);
   - da li se pokreću TASK-029 i TASK-030 (samo TRAIN, eksploratorno, bez ADR-a);
   - ranije otvoreno: glavni simulator za poster, CA observation, faza 3.
3. **Sljedeći posao uz „da“** ([BACKLOG](BACKLOG.md)):
   - TASK-028: pomoćna funkcija za ocjenu s naplatom linije (test prije koda);
   - TASK-029: iscrpna B=1 tablica (33 niza po požaru), pilot na 20 TRAIN požara mora dati
     iste ishode kao TRAIN benchmark, pa svih 98 (ukupno ~1,5 h na 4 procesa);
   - TASK-030: offline ocjena pravila, selektora i tabelarnog RL-a uz LOO po požaru; nastaviti
     samo ako je dobitak izvan podešavanja ≥30 ha i ≥25% jaza.
4. Planer, B=2/B=4, novo korištenje VALIDATION-a i novi trening traže ADR prije pokretanja.

## 2026-11-10: faze 1 i 2 su gotove; čekaju se korisnikove odluke

Faza 2 je izvedena po ADR-030 §4 na zamrznutom zapisu: nijedan od šest primarnih testova ne
odbacuje nultu hipotezu, a osnovni PPO se ne razlikuje od nasumične legalne linije ni od
najbolje TRAIN heuristike (intervali su široki). Brojevi su u [ADR-032](specs/DECISION_RECORDS.md) i
[STATUS](STATUS.md).

1. **Korisnik:** pregled i merge PR-a faze 1 (`f/task-026-stage-1`), zatim PR-a faze 2
   (`f/task-026-stage-2`, otvoren prema grani faze 1).
2. **Korisnik odlučuje prije faze 3:** koji je simulator glavni za poster, i da li sintetički
   CA smije posmatrati forcing tekućeg koraka (`src/wildfire_rl/synthetic_env.py`;
   HANDOFF_STAGE_1_2, §8).
3. **Pitanja koja je faza 2 otvorila** (nisu odlučena, ne mijenjaju ADR-030 §4):
   - Većina politika nauči jedan fiksan smjer. Da li vrijedi duži trening ili drugačiji
     observation, ili se nalaz prijavljuje kakav jeste.
   - Nasumična legalna linija je jedna realizacija (isti seed u svakom scenariju). Prosjek
     preko više nasumičnih seedova bio bi pošteniji komparator, ali to je nova odluka.
   - `downwind` je na VALIDATION-u bolji od `advancing_front`, koji je izabran na TRAIN-u s
     razlikom od 6.7 ha.
4. Zaostali worktreeji se uklanjaju samo uz korisnikovo „da“.

## 2026-11-09: faza 1 PASS (ADR-031)

Gate na TRAIN-u je prošao po ADR-030 §3: zamrznut je WAF 0.10 / ROS 1.0
(`configs/frozen/feds-simfire-growth-gate-freeze-v1.json`, sha256 `7639e3a9…`), a VALIDATION
je ocijenjen jednom. Brojevi i granice su u [ADR-031](specs/DECISION_RECORDS.md) i
[STATUS](STATUS.md).

1. **Korisnik:** pregled i merge PR-a faze 1 (grana `f/task-026-stage-1`).
2. **Faza 2 (autonomno):** grana `f/task-026-stage-2`, izvedena iz grane faze 1.
   Trening po ADR-026 sa 10 seedova, TRAIN benchmark za izbor heuristike, jedan VALIDATION
   benchmark, analiza po ADR-030 §4 i broj epizoda u kojima linija spali više od no-op-a.
   Komande su u [HANDOFF_STAGE_1_2](HANDOFF_STAGE_1_2.md), §6. Rezultat ide u novi ADR i EXP-020.
3. **Faza 3 ne kreće** bez korisnikove odluke o glavnom simulatoru i o observationu u
   sintetičkom CA (HANDOFF_STAGE_1_2, §8).

Zamrznuti zapis je free-burning scenarij koji prolazi unaprijed zadano pravilo, ne kalibrisan
model: na nerastućim požarima znatno prerasta opaženo. To ograničenje važi i za fazu 2.

## 2026-11-09: rezultati ADR-022–028 su nevažeći, prvo ispravke (ADR-029)

Revizija PR-ova #3–#5 našla je grešku u gridMET uzorkovanju: 97/99 TRAIN i 19/20
VALIDATION požara dobili su vrijeme drugog požara. Greška je ispravljena (PR #3), PR-ovi
#3–#5 su spojeni u `main` kao historija, a **brojevi iz ADR-022–028 se ne citiraju** dok
se ne ponove. Detalji i potpun spisak grešaka: [ADR-029](specs/DECISION_RECORDS.md).

**Redoslijed.** Ispravke TASK-021–024 su urađene, nezavisno revidirane, popravljene i
spojene 2026-11-09 (PR-ovi #8, #9, #12, #11); pravila koja su pritom precizirana su u
dopunama ADR-030.
1. **TASK-021 — CI: urađeno (PR #8).** Posao `numeric` pokreće sve testove osim
   SimFire/sb3/lokalnih podataka; preskočeni testovi moraju tačno odgovarati
   `tests/ci_expected_skips.txt`.
2. **TASK-022 — metrike i gate: urađeno (PR #9).** IoU samo rasta, downwind elipsa od vodeće
   ivice fronta, `growth_gate` po ADR-030 §3 (rastući požari, IoU po požaru zbirno kroz
   četiri tačke).
3. **TASK-023 — SimFire okruženje: urađeno (PR #12).** Linije bez dijagonalnih rupa, budžet po
   dužini, linija ne "štedi" kad čeka i drži do efektivnih 980 ft/min, agent vidi gridMET
   dan strogo prije sljedećeg segmenta (novi pre-start zapis), statistika ADR-030 §4,
   checkpointi vezani za postavke, ista zaštita VALIDATION-a i fiksni korak od 5 min u
   no-op putanji, lokalni RNG.
4. **TASK-024 — sintetički CA: urađeno (PR #11).** Napredak vezan za ćeliju, ćelije linije
   u no-op otisku se plaćaju i u nagradi, prihvat po ADR-030 §5, test na stvarnim
   slučajevima je opisni s unaprijed zadanom heuristikom.
5. **TASK-025 — odluke: urađeno u [ADR-030](specs/DECISION_RECORDS.md).** Agent vidi
   vrijeme prethodnog segmenta; umanjenje linije se skalira s korakom, a korak je fiksno
   5 minuta; gate se mjeri IoU-om rasta na požarima koji rastu (≥1.10× površine za 48h)
   prema downwind elipsi, bez dodira s rubom; benchmark ima 10 seedova i glavna poređenja
   PPO prema nasumičnoj liniji i najboljoj TRAIN heuristici (tačni test, Holm); u CA je
   glavni ishod spašena površina, a sigurnost uslov neinferiornosti; sugar-pine ostaje,
   columbus ispada (98 TRAIN).
6. **TASK-026 — ponovno pokretanje u tri faze, svaka uz izričit nalog (ADR-030 §7).**
   Faza 1 bez treninga (manifest bez duplikata, nove gridMET vrijednosti s hashom, gate,
   zamrzavanje, jedna VALIDATION ocjena) tek kad su TASK-021–024 spojeni i FEDS vremenska
   zona provjerena. Faza 2: SimFire benchmark i studija budžeta. Faza 3: ponovni trening CA
   politika, tek nakon odluke koji je simulator glavni za poster.
7. **TASK-027 — spojeno (PR #15, 2026-11-09), nakon nezavisne revizije.**
   Columbus je isključen pravilom u generatoru manifesta (98 TRAIN, 20 VALIDATION). FEDS `t`
   je oznaka VIIRS prolaza u lokalnom sunčevom vremenu, ne UTC; korisnik je izabrao preračun
   01:30/13:30 lokalno → UTC po dužini ([dopuna ADR-030](specs/DECISION_RECORDS.md),
   [dokazi](research/SIMFIRE_ENVIRONMENT.md)). Novi gridMET fajl: sha256
   `7a51aadd46b894d9cd80835d7953107271b3182c776d7bb464d7abae826afac1`, manifest
   `013be9a1…`. RNG reset je riješen u TASK-023.

**Faze 1 i 2, autonomno (dopuna ADR-030 o autonomiji); faza 1 je izvedena, vidi vrh.** Agent smije sam
pokrenuti gate, zamrzavanje i jednu VALIDATION ocjenu, a fazu 2 samo ako gate prođe; merge
i faza 3 ostaju korisnikovi. Prompt s komandama, uslovima zaustavljanja i izvještajem:
[HANDOFF_STAGE_1_2](HANDOFF_STAGE_1_2.md). Fajl s vremenom (`7a51aadd…`) je u
`.local/backups/gridmet/` glavnog klona; kopira se u `.local/gridmet/` worktreea i provjerava hash.

Paralelni PR-ovi (TASK-021–024) ne mijenjaju zajedničke fajlove znanja (STATUS,
NEXT_SESSION, BACKLOG, log, agent ulazi); promjene opisuju u PR-u, a znanje se ažurira pri
merge-u.


## Najnovije — 2026-11-05: sintetički CA (ADR-028), grana `codex/synthetic-ca-training`

**Stanje.** policy-v1 je zaključan (hash u `reports/synthetic/policy-v1.sha256`; težine su prilog draft releasea
`synthetic-policy-v1`, lokalno u ignorisanom `.local/synthetic/locked/`; preuzimanje u
[HANDOFF](../HANDOFF.md)). Jednokratni test na stvarnim slučajevima je
izveden. Svaki novi checkpoint koji ide na stvarne slučajeve prvo se zaključava i
prijavljuje kao nova verzija, jer višestruki pokušaji na istih 119 slučajeva unose selekciju.

**Odluke za tim:**
- Da li je izjednačenje s heuristikom dovoljno za poster ili tražimo agenta koji je
  pobjeđuje. Kandidati za to: DAgger, duži fine-tuning, više sjemena, više jedinica i
  oracle baseline.
- Da li heuristike treba povezati s doktrinarnim izvorima (vidi "Porijeklo heuristika" u
  spec dokumentu).

**Tehnički nastavak:**
1. DAgger umjesto čiste imitacije, pa PPO s value pre-trainingom.
2. Ablacija doslovne "growth trend" nagrade, za objašnjenje u radu.
3. Vizualizacija epizoda je urađena: `scripts/synthetic_case_viewer.py` (lokalni viewer,
   politika naspram no-op na jednom stvarnom startu, s FEDS obodima).

**Komande** (iz roota worktreea, `PY=.local/simfire-venv/bin/python`, `PYTHONPATH=src`):
`scripts/evaluate_synthetic_policies.py`, `scripts/train_synthetic_ppo.py`,
`scripts/bc_warm_start.py`, `scripts/evaluate_real_cases.py --policy-locked`,
`scripts/diagnose_synthetic_calibration_gap.py --all --policy-locked`,
`scripts/synthetic_case_viewer.py`. Tačne argumente stvarnih runova daje [HANDOFF](../HANDOFF.md).


## Trenutno stanje — 2026-11-04

Grana `codex/overnight-steps-5-8` je izvedena iz `codex/fireline-simfire-benchmark`
(PR #3) i sadrži korake 5–8. Ništa nije spojeno u `main`. Lokalni ulazi, venv, modeli i
puni izvještaji su u ignorisanom `.local/` na Harunovom računaru; obnova je opisana u
[environment recordu](research/SIMFIRE_ENVIRONMENT.md).

1. **Gate (korak 5) je FAIL.** Dijagnoza i preregistrovana mreža su u ADR-023/024.
   Zamrznuti gate zapis gotovo ne širi vatru. Strogo pravilo je strukturno naklonjeno
   persistence referenci jer su mnogi FEDS požari stvarno zaustavljeni.
2. **Validation (korak 6)** je skoriran jednom po zapisu. Stress zapis (WAF .01 / ROS 1.0)
   prolazi strogo pravilo na 20 VALIDATION slučajeva, iako je pao na TRAIN-u.
3. **Intervencije i benchmark (korak 7, ADR-025)** postoje i testirani su.
4. **Prilagodba budžetu (korak 8, ADR-026/027)**: osnovni PPO pobjeđuje no-op, fine-tuning
   po budžetu ne daje mjerljivu korist, a downwind heuristika je jednako dobra ili bolja.
   Sve je simulatorski i eksploratorno.

## TASK-019 hipoteze — šta je provjereno (pozitivno i negativno)

| Hipoteza | Provjera | Rezultat |
|---|---|---|
| Nepotpune/izmijenjene FEDS arhive | MD5 svih 6 slojeva nakon prekinutog sekvencijalnog preuzimanja (exit 144 = namjerno ugašen i zamijenjen paralelnim) | sve OK, nema `.partial` |
| Vremensko poravnanje 0–48h | svih 119 epizoda: start maske = prvi FEDS timestamp, četiri razmaka od tačno 12h; runner provjerava start | OK |
| Konvencija vjetra | gridMET `th` je odakle puše; kod rotira +180° u SimFire smjer kuda; jedinični test; `vs` m/s → ft/min × WAF | OK; smjer nije uzrok (dijagnoza: deficit nije u smjeru nego u tome koji požar raste) |
| Isti grid za SimFire, persistence, elipsu | isti 256×256/180 m raster, isti `all_touched`, ista inicijalna maska u sve tri metode | OK |
| Nulti vjetar (sanity) | WAF 0 na 99 TRAIN (ADR-022): IoU .4768, i dalje raste u ~63% timepointa | rast bez vjetra postoji (Rothermel + nagib); potvrđuje pretjeran rast na statičnim požarima |
| Ulazi drugačiji od Belminovih | 99/99 LANDFIRE/maski + 9 gridMET identični hashovi; WAF .01 reproduciran tačno | nije uzrok |
| Prag paljenja / vijek ćelije | ROS × WAF mreža (ADR-023) | smanjuje lažni rast, ali do persistence se dolazi tek gašenjem skoro svega; FAIL |
| Trening samo na TRAIN | env odbija ne-TRAIN bez eksplicitnog `split`; trening skripta fiksira `split="train"` | OK |

Neprovjereno: vremenska zona FEDS `t` (pretpostavka UTC; TASK-027 je kasnije pokazao da nije UTC), finija vlaga goriva od `fm100`,
model zaustavljanja/gašenja. **Svi rezultati koraka 7–8 su "gate FAIL, nije mjerodavno"**
u smislu kalibracije; validation je preuzet i skoriran po korisnikovom odobrenju za
eksploratorni nastavak (ADR-024).

**Ako TASK-019 popravka učini da gate prođe:** prvo ponoviti gate na TRAIN-u, tek onda
validation, a eksploratorne rezultate koraka 6–8 označiti kao zastarjele (ADR-024 dopuna).

## Odluke za tim (ne donositi ih bez korisnika)

- Prihvatiti li stress scenarij kao radni simulator za predaju ili tražiti growth-aware
  gate, npr. ocjenu samo na požarima koji u FEDS-u rastu ili jednostavan model
  zaustavljanja/gašenja, prije bilo kakve tvrdnje o kalibraciji.
- Spojiti li ovu granu u PR #3 ili je držati kao zaseban draft PR.
- Šta od TASK-007 (prioritetna područja) i TASK-020 (gradnja linije kroz vrijeme, više
  linija po odluci) ulazi u obim prije postera.

## Najkorisniji tehnički nastavak

1. **Jači signal budžeta:** dozvoliti više jedinica po 12h odluci ili duži aktivni vijek
   ćelije, da veći budžet ima gdje djelovati. To je nova preregistracija (novi ADR), a ne
   izmjena ADR-026.
2. **Više seedova i koraka** ako tim želi uže intervale. Trenutni trošak je oko 8 odluka/s
   na 7 procesa.
3. **TASK-007:** težina prioritetnih ćelija u nagradi i ablacija ukupne naspram
   prioritetne štete.
4. **TASK-009:** grafikon `reports/real-fire-data/feds-simfire-policy-benchmark-v1.png` i
   ADR-027 tabela su polazište za poster. TEST 2024 otvoriti tek za završni obračun s
   unaprijed zaključanim politikama.

## Komande

Sve iz roota worktreea, uz `PYTHONPATH=src`, `SDL_VIDEODRIVER=dummy`, `OMP_NUM_THREADS=1`
i `MPLCONFIGDIR=.local/mpl-cache`:

```sh
scripts/run_budget_adaptation_experiment.sh            # trening po ADR-026 (SEEDS, BASE_STEPS, FT_STEPS)
OUT=.local/bench/NEW.json scripts/run_budget_adaptation_benchmark.sh
.local/simfire-venv/bin/python scripts/analyze_budget_adaptation.py .local/bench/NEW.json
.local/simfire-venv/bin/python scripts/plot_budget_benchmark.py .local/bench/NEW.json --out .local/bench/NEW.png
```

## Provjere prije predaje

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src .local/simfire-venv/bin/python -m unittest discover -s tests
PYTHONPATH=src python3 -m wildfire_rl.cli --config configs/smoke.json --out runs/NEW-ID
python3 scripts/validate_knowledge.py --strict
UV_CACHE_DIR=.local/uv-cache uv pip check --python .local/simfire-venv/bin/python
git diff --check
```

Ne otvarati TEST 2024. Ne pokretati plaćeni compute, push u tuđu granu ili merge bez
korisnikovog naloga. CFSDS/Cell2Fire rezultati ostaju historijski i odvojeni.
