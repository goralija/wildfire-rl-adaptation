---
type: Handoff
title: Handoff za autonomni rad na fazama 1 i 2 (TASK-026), 2026-11-09
description: Prompt za agenta koji samostalno pokreće gate, zamrzavanje, jednu VALIDATION ocjenu i, ako gate prođe, SimFire benchmark sa studijom budžeta.
sources:
  - resource: /docs/specs/DECISION_RECORDS.md
  - resource: /docs/NEXT_SESSION.md
  - resource: /reports/real-fire-data/feds-gridmet-weather-coverage-v1.json
---
# Handoff: autonomne faze 1 i 2 (stanje 2026-11-09, `main` nakon PR #15)

> **Stanje 2026-11-12:** faze 1 i 2 su završene i spojene (ADR-031, ADR-032). Dozvola iz §2 je
> iskorištena: ne pokretati ponovo faze 1 i 2 i ne ocjenjivati ponovo VALIDATION. §4–§6 služe
> samo kao referenca komandi. Ulaz za nastavak je [HANDOFF](../HANDOFF.md).

Ovaj tekst je prompt za sljedećeg agenta. Zalijepi ga cijelog na početak nove sesije.

---

Preuzimaš rad na repozitoriju `goralija/wildfire-rl-adaptation`. Glavni klon je
`/Users/harungoralija/Desktop/mpvi`. Projekat ispituje može li RL agent (MaskablePPO), čiji
se fine-tuning radi za zadani budžet intervencija, smanjiti opožarenu površinu u simulatoru
SimFire. Epizode počinju od stvarnih početnih stanja američkih požara (FPA-FOD + FEDS-CONUS,
LANDFIRE, gridMET).

Korisnik je Harun Goralija. Komuniciraj s njim na bosanskom, kratko i jasno.

## 1. Prvo pročitaj (redom)

1. `AGENTS.md` i `CLAUDE.md`. Ova pravila imaju prednost nad ovim promptom, osim tamo gdje
   ih dopuna ADR-030 o autonomiji (tačka 2 ispod) izričito proširuje.
2. `docs/NEXT_SESSION.md` i `docs/STATUS.md`.
3. `docs/specs/DECISION_RECORDS.md`, sljedeći dijelovi:
   - ADR-029;
   - ADR-030 sa svim dopunama;
   - posebno §3 (gate), §4 (statistika), §7 (faze), dopunu o FEDS vremenu (TASK-027) i
     dopunu o autonomiji (2026-11-09).
4. `docs/research/SIMFIRE_ENVIRONMENT.md`, odjeljke o gridMET-u i FEDS vremenu.
5. `knowledge/workspace-layout.md` i `HANDOFF.md`, zbog `.local/` podataka i venv-a.

Pregled projekta za ljude: https://claude.ai/artifact/EFi7EXKkvehgTt1GYtoi5Q. Kanonski
izvor je repozitorij.

## 2. Šta smiješ sam (Harunova odluka od 2026-11-09)

Harun je odobrio sljedeće, zapisano u dopuni ADR-030 o autonomiji:
- **Faza 1** bez traženja naloga: gate na TRAIN-u, zamrzavanje i jedna VALIDATION ocjena.
- **Faza 2** bez traženja naloga, **samo ako faza 1 prođe**: SimFire benchmark i studija
  budžeta, lokalno, sa 10 seedova.
- **Ako faza 1 padne:** staješ. Ništa se ne zamrzava, VALIDATION se ne ocjenjuje, a Harunu
  javljaš opcije.
- **Redoslijed širenja:** ostaje `spread_aggregation="last_write"`, odnosno pinovani SimFire.
  U benchmarku izbrojiš i prijaviš epizode u kojima linija spali više od no-op-a, kao poznato
  ograničenje. Ne prelaziš na `"max"`.
- **Push i PR** smiješ sam, uz nezavisnu reviziju. **Merge u `main` ne smiješ.** Merge je
  Harunov.

I dalje ne smiješ:
- otvarati TEST 2024 (ne preuzimaš ga, ne učitavaš i ne nudiš kao opciju);
- pokretati fazu 3 (CA trening);
- koristiti plaćeni ili cloud compute;
- dodjeljivati posao Amaru ili Belminu, niti pisati profesorima;
- brisati `.local/` (nikad `git clean -fdx`);
- dirati necommitovane fajlove u `.worktrees/overnight-steps-5-8`
  (`scripts/live_feds_policy_viewer.{py,html}`, `scripts/trace_feds_policy_episodes.py`);
- commitovati težine modela, sirove podatke ili sadržaj `.local/`;
- mijenjati gate, kandidate, metrike, statistiku ili pravilo izbora nakon što vidiš ijedan
  rezultat. Ako ti se čini da nešto treba promijeniti, **staneš i pitaš**.

## 3. Šta je ispravljeno i zašto je ovo prvi važeći pokušaj

Svi brojevi iz ADR-022–028 su nevažeći i ne citiraju se kao nalazi. Od tada su ispravljeni:
- **Vrijeme.** Svaki požar ima svoju gridMET ćeliju (≤5 km). Ranije su svi požari jedne
  godine dijelili vrijeme prvog požara.
- **FEDS `t`.** Čita se kao VIIRS prolaz u 01:30/13:30 lokalnog sunčevog vremena, a ne kao
  UTC. Pod UTC čitanjem pola segmenata dobijalo je vrijeme dan ranije.
- **Observation.** Agent vidi posljednji gridMET dan strogo prije segmenta, a na početku
  `pre_start` dan.
- **Linije.** Linije su 4-povezane, a njihova jačina ne zavisi od koraka simulatora.
- **Gate.** Mjeri IoU samo rasta, na požarima koji rastu, prema elipsi niz vjetar.
- **Manifest.** Duplikat je uklonjen: 98 TRAIN i 20 VALIDATION.
- **Statistika.** 10 seedova; sign-flip test s Holmovom korekcijom; poređenje s nasumičnom
  linijom i s najboljom TRAIN heuristikom.

Rezultat može ispasti i loš. Cilj je ispravan rezultat, a ne pobjeda agenta.

## 4. Lokalno okruženje

1. Iz ažuriranog `main`-a napravi worktree, npr.
   `git worktree add -b f/task-026-stage-1 .worktrees/task-026-stage-1 main`.
2. U tom worktreeu napravi pravi folder `.local/gridmet/`. U njega symlinkuj **samo** `.nc` i
   `.sha256` fajlove iz `.worktrees/overnight-steps-5-8/.local/gridmet/`. Stari fajl
   `feds-episode-weather-v1.json` (`7b0aa405…`) tamo je dokaz greške: ne prepisuj ga i ne
   linkuj ga.
3. **Kopiraj** (ne symlinkuj) fajl s vremenom
   `/Users/harungoralija/Desktop/mpvi/.local/backups/gridmet/feds-episode-weather-v1-7a51aadd.json`
   u `.local/gridmet/feds-episode-weather-v1.json`. Provjeri da je sha256
   `7a51aadd46b894d9cd80835d7953107271b3182c776d7bb464d7abae826afac1`, jer je taj hash
   upisan u `reports/real-fire-data/feds-gridmet-weather-coverage-v1.json`.
   - Ako se hash ne slaže, ili ako moraš ponovo pokrenuti sampler, dobijaš novi hash, jer
     sampler upisuje `created_utc`. Taj novi hash onda mora ući u izvještaj i u freeze zapis.
4. `.local/feds-simfire-cases` i `.local/feds-conus` mogu biti symlinkovi na iste foldere u
   `overnight-steps-5-8/.local/`, jer ih runner samo čita.
5. Postavi okruženje:

```sh
P=/Users/harungoralija/Desktop/mpvi/.worktrees/overnight-steps-5-8/.local/simfire-venv/bin/python
export PYTHONPATH=src SDL_VIDEODRIVER=dummy OMP_NUM_THREADS=1 MPLCONFIGDIR=.local/mpl-cache XDG_CACHE_HOME=.local/cache
```

Provjera prije rada, iz korijena worktreea:

```sh
$P -m unittest discover -s tests          # s lokalnim podacima: OK, bez preskočenih
python3 scripts/validate_knowledge.py --strict
shasum -a 256 .local/gridmet/feds-episode-weather-v1.json data/manifests/feds-episode-cohort-v1.json
```

- Manifest mora imati sha256 `013be9a1632abcbc29d86f4bc16af89d3c074503f5899d1e39903d76ec2c28d5`.
- `scripts/run_ci_tests.py` lokalno javlja dva `LocalCaseTest` testa jer lokalni podaci
  postoje. To je očekivano. Pravu CI provjeru radi CI, ili čist checkout bez `.local/`.
- Za duge poslove drži računar budnim (`caffeinate -i`) i pokreći ih u pozadini.

## 5. Faza 1 — gate na TRAIN-u (ADR-030 §3)

**Kandidati su fiksni (17).** Svi idu uz lifetime 90 min, korak 5 min i seed 0:
- WAF {0, .0025, .01, .025, .05, .10, .20, .605} uz ROS 1.0;
- ROS {0.35, 0.5, 0.7} × WAF {0.05, 0.2, 0.4}.

**Koraci:**

1. **Test pa skripta za izbor.** Prvo napiši test, pa skriptu, npr.
   `scripts/select_feds_growth_gate.py`. Skripta čita svih 17 izvještaja i primjenjuje
   pravilo:
   - kandidat prolazi ako su svi TRAIN slučajevi završeni bez greške, nema nijednog
     kontakta s rubom i `growth_gate` kaže prolaz (srednji IoU rasta SimFire-a na rastućim
     požarima veći od elipsinog);
   - među prolaznim se bira najveći IoU rasta, a kod izjednačenja manja srednja apsolutna
     greška površine.

   Testom pokrij prolaz, pad, izjednačenje, nepotpun izvještaj i kontakt s rubom. Pravilo
   uzmi doslovno iz ADR-030 §3 i dopune o gateu.
2. **Izmjeri trajanje** na prvom kandidatu i javi procjenu u log. Oslonac: no-op smoke na
   jednom slučaju trajao je oko 5 s u jednom procesu. 98 × 17 slučajeva sa 7 workera trebalo
   bi trajati red veličine pola sata do sat, ali se oslanjaj na mjerenje.
3. **Pokreni svih 17**, u pozadini, sa `--resume` ako se prekine:

```sh
$P scripts/evaluate_feds_train_noop.py --wind-adjustment-factor W --ros-multiplier R \
   --workers 7 --out .local/gate/adr030/waf-W-ros-R.json
```

4. **Zapiši sažetak svih 17** u `reports/real-fire-data/feds-simfire-train-growth-gate-v1.json`.
   Za svakog kandidata upiši:
   - `growth_gate` i broj rastućih i nerastućih požara;
   - IoU rasta za SimFire i za elipsu;
   - greške i kontakte s rubom;
   - lokalnu putanju i sha256 punog izvještaja;
   - sha256 fajla s vremenom i manifesta.

   Nerastuće požare prijavi zasebno (preveliki rast u ha i ćelijama). Oni ne odlučuju gate.
5. **Ako nijedan kandidat ne prođe:**
   - zapiši FAIL u izvještaj, novi ADR-031 i EXPERIMENT_LOG;
   - ništa ne zamrzavaj i VALIDATION ne ocjenjuj;
   - commit, push i PR uz reviziju;
   - **stani** i Harunu daj 2–3 opcije s posljedicama.
6. **Ako jedan prođe:**
   1. Napravi `configs/frozen/feds-simfire-growth-gate-freeze-v1.json` po uzoru na postojeći
      `feds-simfire-gate-freeze-v1.json`. Zapis mora imati:
      - `selected_on_split: "train"` i `gate_status: "PASS"`;
      - `frozen_params` sa **svih šest** polja `SimFireParams`: `wind_adjustment_factor`,
        `internal_update_minutes: 5`, `active_cell_lifetime_minutes: 90`, `ros_multiplier`,
        `fireline_attenuation: "per_minute"` i `spread_aggregation: "last_write"`;
      - `weather_sha256` novog fajla i sha256 manifesta;
      - sažetak izbora.
   2. **U istom commitu** dodaj sha256 tog zapisa u
      `configs/frozen/validation-freeze-allowlist.json`. Commituj **prije** VALIDATION-a.
   3. VALIDATION ocijeni **jednom**, s istim parametrima:

```sh
$P scripts/evaluate_feds_train_noop.py --split validation --frozen-params configs/frozen/feds-simfire-growth-gate-freeze-v1.json \
   --wind-adjustment-factor W --ros-multiplier R --workers 7 --out .local/gate/adr030/validation-frozen.json
```

   4. Rezultat zapiši bez ponovnog biranja, i kad je lošiji od TRAIN-a. VALIDATION ne služi
      za izbor ni za odluku o nastavku: faza 2 kreće ako je TRAIN gate prošao.
7. **Dokumentacija:** novi ADR-031 s rezultatom faze 1, EXP-019 u
   `docs/research/EXPERIMENT_LOG.md`, te ažurirani STATUS, NEXT_SESSION, BACKLOG, `log.md` i
   WORK_LOG.
8. **Commit, push i PR** na granu `f/task-026-stage-1`. Zatim pokreni nezavisnog recenzenta
   (subagent) sa **suženim kontekstom**: samo broj PR-a, putanje koda i pravila
   repozitorija, bez tvog objašnjenja. Svaki nalaz provjeri u kodu, popravi i zabilježi.
   **Ne spajaj.**

## 6. Faza 2 — benchmark i studija budžeta (samo ako je faza 1 PASS)

Radi u novoj grani izvedenoj iz grane faze 1, npr. `f/task-026-stage-2`. Freeze zapis i
allowlist moraju biti u tom checkoutu. PR otvori prema grani faze 1, ili prema `main`-u ako
je Harun već spojio fazu 1. To napiši u opisu PR-a.

1. **Trening po ADR-026, sa 10 seedova (ADR-030 §4).** Osnova je B=2, zatim fine-tune na B=1
   i B=4 te kontrola iste dužine na B=2:

```sh
PY=$P PARAMS=configs/frozen/feds-simfire-growth-gate-freeze-v1.json OUT=.local/ppo/adr030 \
  SEEDS="11 12 13 14 15 16 17 18 19 20" BASE_STEPS=8064 FT_STEPS=3024 \
  scripts/run_budget_adaptation_experiment.sh
```

   - Izmjeri prvi seed i javi procjenu. Raniji logovi kažu oko 8 odluka/s na 7 procesa, što
     daje oko 35–40 min po seedu, ukupno nekoliko sati.
   - Skripta preskače gotove checkpointe, pa se može nastaviti nakon prekida.
   - Checkpointi su vezani za receipt s postavkama. Ne koristi stare checkpointe ni
     `--allow-legacy-checkpoints`.
2. **TRAIN benchmark** služi za izbor najbolje heuristike i za provjeru na trening skupu:

```sh
PY=$P PARAMS=configs/frozen/feds-simfire-growth-gate-freeze-v1.json RUNS=.local/ppo/adr030 \
  SEEDS="11 12 13 14 15 16 17 18 19 20" SPLIT=train OUT=.local/bench/adr030-train.json \
  scripts/run_budget_adaptation_benchmark.sh
```

3. **VALIDATION benchmark, jednom**, sa svim politikama i heuristikama zaključanim prije
   pokretanja:

```sh
PY=$P PARAMS=configs/frozen/feds-simfire-growth-gate-freeze-v1.json RUNS=.local/ppo/adr030 \
  SEEDS="11 12 13 14 15 16 17 18 19 20" SPLIT=validation OUT=.local/bench/adr030-validation.json \
  scripts/run_budget_adaptation_benchmark.sh
```

4. **Analiza i grafikon.** Najbolja heuristika se bira iz TRAIN izvještaja, nikad iz
   VALIDATION-a:

```sh
$P scripts/analyze_budget_adaptation.py .local/bench/adr030-validation.json \
   --train-report .local/bench/adr030-train.json --out reports/real-fire-data/feds-simfire-budget-benchmark-adr030-v1.json
$P scripts/plot_budget_benchmark.py .local/bench/adr030-validation.json --out reports/real-fire-data/feds-simfire-budget-benchmark-adr030-v1.png
```

5. **Prijavi** sljedeće:
   - šest primarnih testova (PPO prema nasumičnoj liniji i prema najboljoj TRAIN heuristici,
     za B = 1, 2, 4), s Holmovom korekcijom;
   - sekundarna poređenja fine-tuninga;
   - poređenje s no-op-om, samo kao provjeru zdravog razuma;
   - broj scenarija koji su se promijenili i rezultat bez najvećeg scenarija;
   - **broj epizoda u kojima linija spali više od no-op-a** (isti scenarij, budžet i seed).
     Ako skripta to ne broji, napiši mali test i računaj iz izvještaja.
6. **Dokumentacija:** dopuna ADR-031 ili novi ADR-032, EXP-020, a zatim STATUS, NEXT_SESSION,
   BACKLOG, `log.md` i WORK_LOG. Commit, push, PR i nezavisna revizija kao u fazi 1.
   **Ne spajaj.**

## 7. Kada staješ i pitaš Haruna

- Gate je FAIL.
- Bilo koja greška u runneru ili nepotpun izvještaj, ako ga `--resume` ne riješi.
- Hash fajla s vremenom ili manifesta ne odgovara upisanom.
- Neki test pada, a uzrok nije očigledan i lokalan.
- Učinilo ti se da treba promijeniti kandidata, metriku, statistiku, budžet, korak ili
  postavku širenja.
- Posao bi trajao znatno duže od procjene, npr. više od 12 h za fazu 2.
- Faza 2 je završena. Faza 3 ne kreće bez Harunove odluke.

## 8. Otvoreno, nije tvoje da odlučuješ

- **Sintetički CA observation.** `src/wildfire_rl/synthetic_env.py` u observationu daje
  vrijeme trenutnog koraka, a to je i forcing simulacije. To je isto ono što ADR-030 §1
  izbjegava za SimFire. Odluka je potrebna prije faze 3; ne utiče na faze 1 i 2.
- **Koji simulator je glavni za poster.**
- **Zastarjeli worktreeovi** u `.claude/worktrees/task-021…024` i
  `.worktrees/task-027-feds-utc-dedup`: uklanjaju se samo uz Harunovo „da“. Fajl s vremenom
  iz posljednjeg je već kopiran u `.local/backups/gridmet/`.

## 9. Kad završiš

Harunu daj kratak izvještaj na bosanskom:
1. Šta je urađeno i gdje je zapisano (PR linkovi, fajlovi, hashovi).
2. Gate: PASS ili FAIL, izabrani kandidat, IoU rasta za SimFire i elipsu, te broj rastućih
   i nerastućih požara.
3. VALIDATION ocjena, ako je rađena.
4. Faza 2, ako je rađena: šest primarnih testova (procjena, interval, Holm p), te broj
   epizoda u kojima linija spali više od no-op-a.
5. Šta čeka njegovu odluku: merge PR-ova, faza 3, CA observation.

Rezultate ne prikazuj jačim nego što jesu. Rezultat simulatora nije dokaz o stvarnom
gašenju, a PASS gatea nije fizička validacija simulatora. Ponudi i ažuriranje artifact
pregleda.
