---
type: Handoff
title: Naredni korak — pregled nakon faze 2 (2026-11-12)
---
# Naredni korak

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
