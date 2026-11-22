# Promjene baze znanja

## 2026-11-22: upareni PPO rezultati objavljeni

Grana `codex/paired-ppo-learning` je pushana; [CI na cfc2a2a1](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/45076798202) prolazi sva četiri posla. Status, handoff i verifikacija čuvaju oba neprošla learning kriterija i predloženi TASK-044.


## 2026-11-22: završen upareni PPO learning pilot

[TASK-043/ADR-052](docs/research/PAIRED_PPO_LEARNING.md): finalni PPO SF5,13%/CA6,03%,
ali oba unaprijed zadana learning kriterija false. Svi seedovi/0-512-2048 sačuvani,
heuristike/procenti/ha i nearly-uniform greedy bias jasno odvojeni.413pinned testova,
nezavisni mask/return/statistics audit i puni96native restore PASS. Nema aktivnog
treninga; TASK-044 reward/advantage/reference dijagnoza je sljedeći prijedlog.


## 2026-11-22: background handoff objavljen

Trening TASK-043 nastavlja u nezavisnoj sesiji; sva3radnika prešla64koraka. Grana pushana, [CI na0cb67456](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/45066883345) prolazi sva4posla. Handoff čuva nastavak, bez tvrdnje o završenom učenju.


## 2026-11-22: upareni PPO trening u pozadini

[TASK-043](docs/research/PAIRED_PPO_LEARNING.md):408pinovanih testova i132native preflight
putanje PASS; odobreni45fit/16development pilot pokrenut s3radnika,nice19. Status i
launch receipt čuvaju operativni nastavak; rezultati tek čekaju kompletan audit.


## 2026-11-22: odobren upareni PPO learning pilot

[TASK-043/ADR-051](docs/research/PAIRED_PPO_LEARNING.md): isti45fit/16development u oba backend-a, tri seeda i zamrznuti budžet; plan prije koda/treninga.


## 2026-11-22: zajednički PPO ugovor objavljen

Grana `codex/common-ppo-interface` je pushana; [CI na3ec5d5fc](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44965103408) prolazi sva4posla. Status/handoff/verifikacija čuvaju tehnički obim i sljedeći prijedlog.


## 2026-11-22: završen zajednički PPO ugovor

[TASK-040 B.1/ADR-050](docs/research/COMMON_PPO_INTERFACE.md): isti encoder/model/akcije
i charged reward u oba backend-a,4×64koraka tehnički PASS.397pinovanih testova, stare
cijele native maske/nagrade i checkpoint/restore svih12putanja identični. Nije dokaz
učenja ili fizičke validacije. Sljedeći prijedlog je mali unaprijed registrovani TRAIN
learning pilot s istim heuristikama i apsolutnim/procentnim metrikama.


## 2026-11-22: započet zajednički PPO ugovor

[TASK-040 B.1/ADR-049](docs/research/COMMON_PPO_INTERFACE.md): isti encoder/charged reward i mali tehnički smoke.


## 2026-11-21: frozen61audit objavljen, CI zelen

`codex/ca-expanded-growth-audit` je pushana. [CI na `aa3335a4`](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44907387597)
prolazi sva četiri posla. [Izvještaj](docs/research/EXPANDED_OBSERVED_GROWTH.md),
status i handoff čuvaju nalaze, nerast/domain granice i predloženi TASK-040B.1.
Bez novog PR-a ili mergea.

## 2026-11-21: završen frozen61TRAIN growth audit

[TASK-042/ADR-048](docs/research/EXPANDED_OBSERVED_GROWTH.md): cijeli kompatibilni okvir,
CA0MAE manji67,90%, IoU0,12568vsSF0,08664, uz4observed-zero slučaja koje oba modela
prerastaju. Svi seedi, novi45/old16 i59covered rezovi su vidljivi.388pinovanih testova,
nezavisni metric/raster/reuse i restore PASS. [Rezultati](reports/real-fire-data/expanded-observed-growth-v1.json)
i [verifikacija](reports/real-fire-data/expanded-observed-growth-verification-v1.json) čuvaju dokaze.
TASK-040B.1 zajednički PPO/reward ugovor je sljedeći prijedlog, bez novog većeg treninga.

## 2026-11-21: odobren prošireni TRAIN growth audit

[TASK-042/ADR-047](docs/research/EXPANDED_OBSERVED_GROWTH.md) počinje na novoj grani iz
2de00136. Svih61compatible početaka, isti parametri i3CA seeda; plan prije novih
ishoda, eksplicitan reuse16 i45novih, near/no-growth/domain provjere bez tuninga.

## 2026-11-21: audit opaženog rasta objavljen, CI zelen

Grana `codex/ca-feds-growth-audit` je pushana. [CI na21ff12f2](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44850220640)
prolazi sva četiri posla. [Izvještaj](docs/research/PAIRED_OBSERVED_GROWTH.md) i handoff
čuvaju nalaze, granice i predloženi TASK-042. Nema novog PR-a ili mergea.

## 2026-11-21: završen audit rasta prema FEDS-u

[TASK-041/ADR-046](docs/research/PAIRED_OBSERVED_GROWTH.md) na16istih TRAIN početaka:
CA0 ima86,47%manju area grešku, ali spatial interval uključuje0. Sva3seeda i15fully-covered
osjetljivost prijavljeni; Martin izlazi iz mape, Goldstone near-stalled ostaje problem.
381pinovani test i nezavisni replay/raster/restore checkovi prolaze. [Rezultati](reports/real-fire-data/paired-observed-growth-v1.json)
i [verifikacija](reports/real-fire-data/paired-observed-growth-verification-v1.json) čuvaju sve redove.
TASK-042 na61compatible TRAIN je sljedeći prijedlog, bez automatskog treninga/holdouta.

## 2026-11-21: odobren TRAIN audit opaženog rasta

[TASK-041/ADR-045](docs/research/PAIRED_OBSERVED_GROWTH.md) je započet u izdvojenoj
grani iz640a910e. Plan prethodi scoringu; ista16slučaja i zamrznuti SF/CA parametri,
provjera vremena i coverage, bez novog treninga ili holdouta.

## 2026-11-21: uparena studija objavljena, CI zelen

Grana `codex/ca-simfire-paired` je pushana. [CI na042a5c73](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44846740515)
prolazi sva četiri posla. [Izvještaj](docs/research/CA_SIMFIRE_PAIRED.md) i handoff
čuvaju završenu fazu A, mješovit nalaz i predloženi TASK-041. Bez novog PR-a/mergea.

## 2026-11-21: isti početci i linije, mješovit SimFire/CA nalaz

[TASK-040 faza A](docs/research/CA_SIMFIRE_PAIRED.md) / ADR-044 je završena.16stvarnih
TRAIN početaka sa istim uslovima, primarni CAseed0 i dodatne dvije zaključane spread
replike. Agent dobija veći sekundarni procentni prosjek, ali nestabilno; heuristike
mijenjaju poredak i no-op rast je oko5,4puta manji. Pooled ponderisanje mijenja neke
smjerove poređenja. Nema automatskog opravdanja migracije ili native PPO rangiranja.
369pinovanih testova i native/replay/restore provjere prolaze. [Verifikacija](reports/synthetic/ca-simfire-paired-verification-v1.json)
i [lokalni paket](reports/synthetic/ca-simfire-paired-artifacts-v1.json) čuvaju dokaze.
Sljedeći prijedlog TASK-041 je TRAIN growth audit prema opaženom FEDS-u; faza B otvorena.

## 2026-11-21: CA learning grana objavljena, CI zelen

`codex/ca-learning-pilot` je pushana. [CI na1d4209be](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44840927699)
prolazi sva četiri posla; [izvještaj](docs/research/CA_LEARNING_PILOT.md) čuva sve modele,
ograničenja i sljedeći TASK-039. Bez novog PR-a/mergea ili uploada težina.

## 2026-11-21: CA v2 BC/PPO završen

2026-11-21 — TASK-038 završen na codex/ca-learning-pilot iz3b7b56a2. Plan6f2e4b61,
kodfca17851; prije dev ocjene RNGfa55b3a3 i2env51bbdff2 regresije.32TRAIN,96demo epizoda,
1.152stanja.3model seeda,60BC epoha pa4.096PPO koraka svaki; konačni poslovi oko7,5min.
Svih288devputanja PASS. BC3,08%, PPO2,98%, teacher7,46%; nijedan kandidat ne prelazi
prag. Sigurnost2–5susreta po modelu prema20, svi0gubitaka.362pinovana testa,347modernih
(3skip),286core(40skip), aktivni checkpoint roundtrip, CLI i knowledge PASS. ADR-042,
EXP-026 i izvještaj čuvaju sve modele i granice. TASK-039 prijedlog TRAIN dijagnoze,
bez novog treninga/testa. Modeli/demonstracije lokalni, no old checkpoint/real holdout.

[Detaljni izvještaj](docs/research/CA_LEARNING_PILOT.md).

## 2026-11-21: CA grana objavljena i CI zelen

`codex/ca-controlled-pilot` je pushana; [CI](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44836958711)
na3ad3f72c prolazi četiri posla. [CA izvještaj](docs/research/CA_CONTROLLED_PILOT.md)
i handoff čuvaju završeni TASK-035 i sljedeći TASK-038. Bez PR-a/mergea.

## 2026-11-21: CA ugovor i pilot završeni

2026-11-21 — Korisnik je odobrio CA iz SimFire repair grane. Izdvojen worktree/grana
`codex/ca-controlled-pilot`, baza664d890d. Plan c8d8563c/ADR-039 prije koda7b45ee19 i
nice19 worker provjere8ba4ced2. Observation-only heuristike dobijaju isto native/current
forcing kao budući agent.240 development epizoda prolazi; direct7,46% uz20 bliskih
susreta/0 gubitaka. Prvi slučaj15/15 replay identičan.352 pinovana testa, moderni337/3skip,
core284/38skip, CLI i knowledge15/15/strict86 PASS. ADR-040/EXP-025 i javni izvještaj
čuvaju nalaze i granice; nema RL, starog checkpointa ili holdouta. TASK-035 završen,
TASK-038 je naredni encoder/provenance/kratki BC-PPO protokol. Nema mergea ili novog PR-a.

[Detaljni izvještaj](docs/research/CA_CONTROLLED_PILOT.md) i [rezultati](reports/synthetic/ca-controlled-development-v2.json).

## 2026-11-20: v2 grana objavljena, CI zelen

`codex/simfire-observation-repair` je pushana, sa kodnim/rezultatskim commitom
`1cabe778`. GitHub workflow44817109635 prolazi core3.11/3.13, numeric i knowledge.
Publication receipt čuva commit i potvrđuje iste numeric source hashove kao lokalna
provjera. Novi PR nije potreban i nije otvoren; PR #20 je ostavljen za kolege. Nema
mergea, novog computea ili uploada velikog paketa. Status/handoff/raspored su usklađeni.

## 2026-11-20: TASK-036 observation v2 izveden (ADR-038)

- [Popravak opažanja](docs/research/SIMFIRE_OBSERVATION_REPAIR.md) je stvarno implementiran:
  kategorije/nonfuel, fine-global/native-local prikaz i opciona nonfuel maska.
- 98 replayeva i 3136 kandidata se poklapaju sa starim zapisom; legacy RBF pipeline PASS.
- Fine+gate 123,72 prema 101,04 charged ha; +22,68 s intervalom[−32,30;83,61]. Nijedan
  naučeni kandidat ne prelazi prag.344 pinovana testa i 7 native replayeva prolaze.
- PR #20 ostaje otvoren za kolege; nova izvedena grana se push-a bez novog PR-a po nalogu.
  CA TASK-035 draft i preostali SimFire TASK-037 su odvojeni; nema novih holdout/treninga.

## 2026-11-20: Korisnik je odobrio SimFire popravak i pregled PR-a

Grana `codex/simfire-observation-audit` je pushana i otvoren je
[PR #20](https://github.com/goralija/wildfire-rl-adaptation/pull/20). GitHub konektor je
vratio403 za kreiranje; postojeći gh CLI je uspješno otvorio isti odobreni PR.
Korisnik daje još jedan pokušaj SimFire-u: popravak kategorijskog goriva i prostornog
opažanja na novoj izvedenoj grani, prije CA. Razlog prethodnog stopa i redoslijed su
dokumentovani. Nema mergea ili novih mjerenja u ovoj publikacijskoj dopuni.

## 2026-11-20: TASK-034 završen, ADR-036

- [SimFire audit](docs/research/SIMFIRE_OBSERVATION_AUDIT.md): 98 input/observation provjera,
  četiri nested porodice bez prolaza praga i dvije namjerno odabrane native probe.
- Potvrđeni startup mkdir race je ispravljen testom prije koda. Fuel/front aliasing i
  last_write osjetljivost su izmjereni; metri/stopa i smjerovi nisu pokazali kvar.
- Pinovani suite 327/327, moderni 312 (3 skip), core 272 (35 skip); CLI PASS.
- Preporuka TASK-035 je kontrolisani CA ugovor/pilot, draft nije izvršen. SimFire v2 je
  opcionalni TASK-036; ne tvrdi se da su svi potencijali ili greške iscrpljeni.
- Novi rad je lokalni na `codex/simfire-observation-audit`; nema novih PPO/CA treninga,
  holdout pristupa ili remote objave. Handoff i ulazi znanja su usklađeni.

## 2026-11-19: korisnik je zatražio push SimFire grane

- `codex/simfire-policy-iterations` je pushana na origin i prati istoimenu remote granu.
- HANDOFF, STATUS, NEXT_SESSION i README odražavaju objavu; PR i merge nisu urađeni.
- Veliki TRAIN artefakti ostaju lokalni; nije bilo novog eksperimenta.

## 2026-11-19: SimFire TASK-028–030 završeni (ADR-034)

- Lokalna grana `codex/simfire-policy-iterations`, baza `f96f744f`; tuđi rad i glavni checkout sačuvani.
- TRAIN weather obnovljen; oba obračuna testirana; svih 98×33 ishoda provjereno, bez ruba;
  nezavisne reference i ADR-032 no-op/heuristički agregati se poklapaju.
- Osam LOO metoda ocijenjeno zasebno za raw/charged. Nijedna ne prelazi prag. Charged
  ridge-10: +6,98 ha prema pravilu, −13,63 ha bez najveće OOF razlike; nema potvrđene prednosti.
- [Izvještaj](docs/research/SIMFIRE_B1_EXPLORATION.md), [EXP-022](docs/research/EXPERIMENT_LOG.md),
  [rezultati](reports/real-fire-data/feds-b1-offline-v1.json) i [manifest lokalnog paketa](reports/real-fire-data/feds-b1-artifact-manifest-v1.json).
- Root README usklađen s ADR-029/031/032/034 umjesto poništenih nalaza.
- Pinovani runtime 314/314 testova (0 skip), CLI i knowledge PASS. Nema novih PPO/CA,
  VALIDATION/TEST, push/merge ili fizičke validacije. TASK-034 je prijedlog sljedeće dijagnoze.

## 2026-11-12: pregled nakon faze 2 i novi HANDOFF

- Pet analiza nakon ADR-032 (literatura, kratke epizode, intervencije, šta je stvarno,
  optimizovane heuristike) je u [docs/research/review-2026-11-11](docs/research/review-2026-11-11/SUMMARY.md),
  sa skriptama i izlazima TRAIN-only analiza. Bez treninga; VALIDATION nije ponovo korišten.
- Glavni nalazi: rezultat ADR-032 je očekivan; 48 h nije ograničenje podataka; linija se u
  SimFire-u računa kao spašena površina (odluka otvorena); predložen TASK-028–033.
- [HANDOFF](HANDOFF.md) je prepisan kao jedini ulaz za nastavak (stanje grana i PR-ova,
  redoslijed čitanja, odluke, pravila, okruženje); STATUS, NEXT_SESSION, BACKLOG, kontekst i
  agent ulazi upućuju na njega. Napomene o zastarjelim opisima dodane su u
  `SIMFIRE_ENVIRONMENT.md` i `SYNTHETIC_CA_ENV.md`.
- EXP-021 bilježi TRAIN-only analize i probni run. Nezavisna revizija PR-a #19 je našla da su
  PR #17 i #18 već bili spojeni; HANDOFF, STATUS i NEXT_SESSION su ispravljeni, PR #19 cilja `main`.

## 2026-11-10: TASK-026 faza 2, benchmark i studija budžeta (ADR-032)

- 10 seedova, 40 PPO politika, TRAIN benchmark (98 požara) za izbor heuristike i jedan
  VALIDATION benchmark (20 požara, 3,520 epizoda) na zamrznutom zapisu WAF 0.10 / ROS 1.0.
- Nijedan od šest primarnih testova ne odbacuje nultu hipotezu nakon Holmove korekcije:
  osnovni PPO se ne razlikuje od nasumične legalne linije ni od `advancing_front`
  ([analiza](reports/real-fire-data/feds-simfire-budget-benchmark-adr030-v1.json),
  [ADR-032](docs/specs/DECISION_RECORDS.md)). Fine-tuning po budžetu ne daje mjerljiv dobitak.
- Linija spali više od no-opa u 48 od 2,379 epizoda s linijom. Sedam od deset osnovnih
  politika uvijek kreće istim smjerom, a tri fine-tune politike nikad ne postave liniju.
- Nezavisna revizija PR-a #18 nije našla blokere; dopune su u ADR-032 (preciznije
  formulacije, rezultat bez najvećeg požara, provjere u skripti za zapis o pokretanju).
- Izbor heuristike i hashovi modela su zaključani commitom prije VALIDATION-a
  ([lock](reports/real-fire-data/feds-simfire-budget-validation-lock-adr030-v1.json)); trening
  i oba benchmarka su sažeti u
  [zapisu o pokretanju](reports/real-fire-data/feds-simfire-budget-run-record-adr030-v1.json),
  koji piše `scripts/summarize_budget_adaptation_run.py`.
- Simulatorski rezultat na free-burning zapisu; nije dokaz o stvarnom gašenju. Faza 3 čeka
  korisnikovu odluku.

## 2026-11-09: TASK-026 faza 1, gate PASS i zamrzavanje (ADR-031)

- Gate po ADR-030 §3 na 98 TRAIN požara: 8 od 17 kandidata prolazi; zamrznut je WAF 0.10 /
  ROS 1.0 (IoU rasta 0.0958 prema 0.0258 za elipsu na 82 rastuća požara, bez dodira s rubom).
  [Sažetak gatea](reports/real-fire-data/feds-simfire-train-growth-gate-v1.json),
  [freeze zapis](configs/frozen/feds-simfire-growth-gate-freeze-v1.json).
- VALIDATION je ocijenjen jednom: 0.0983 prema 0.0278 na 18 rastućih požara
  ([izvještaj](reports/real-fire-data/feds-simfire-validation-growth-gate-v1.json)).
- Granica: oba IoU su ispod 0.10 i simulator prerasta nerastuće požare (oko 9,000 ha po
  požaru na TRAIN-u). PASS nije fizička validacija ([ADR-031](docs/specs/DECISION_RECORDS.md)).
- Pravilo izbora je u `scripts/select_feds_growth_gate.py`, commitovano s testom prije
  pokretanja. Faza 2 se radi na grani `f/task-026-stage-2`.
- Nezavisna revizija PR-a #17 nije našla blokere; dopune su u ADR-031 (koliko je elipsa
  niska letvica, skripta za VALIDATION sažetak, dodatni testovi).

## 2026-11-09: TASK-027 spojen; faze 1 i 2 autonomno

- PR #15 je spojen nakon nezavisne revizije. Korisnik je odobrio da agent sam pokrene fazu 1
  i, ako prođe, fazu 2; merge i faza 3 ostaju njegovi ([dopuna ADR-030](docs/specs/DECISION_RECORDS.md)).
- Prompt za sljedećeg agenta: [HANDOFF_STAGE_1_2](docs/HANDOFF_STAGE_1_2.md).

## 2026-11-09: TASK-027, duplikat i FEDS vremenska zona

- Generator manifesta zadržava jedan zapis po FEDS požaru (najniži `fod_id`); columbus je
  isključen, manifest ima 98 TRAIN i 20 VALIDATION ([crosswalk](docs/research/FPA_FEDS_CROSSWALK.md)).
- FEDS `t` nije UTC: to je AM/PM oznaka VIIRS prolaza po lokalnom sunčevom vremenu, upisana
  kao 00:00/12:00 ([dokazi](docs/research/SIMFIRE_ENVIRONMENT.md)). Korisnik je izabrao
  preračun 01:30/13:30 lokalno → UTC po dužini ([dopuna ADR-030](docs/specs/DECISION_RECORDS.md)).
- Novi gridMET fajl (sha256 `7a51aadd…`) ima `pre_start` i vlastitu ćeliju za svih 118
  slučajeva; hash i poređenje sa starim fajlom su u coverage reportu. Sljedeće: PR, revizija,
  pa nalog za fazu 1.

## 2026-11-09: ispravke TASK-021–024 revidirane i spojene

- Svaki PR je pregledao zaseban recenzent s ograničenim kontekstom; nalazi su popravljeni
  prije merge-a: tačan spisak preskočenih testova u CI-ju, gate po ADR-030 §3, elipsa od
  vodeće ivice fronta, observation bez buduće prognoze (pre-start dan), linija bez
  "štednje", fiksna heuristika i opisni real-case test u CA. Dopune ADR-030 to bilježe.
- Sljedeće: TASK-027 i novi gridMET fajl, pa faza 1 uz nalog ([NEXT_SESSION](docs/NEXT_SESSION.md)).

## 2026-11-09: dopuna ADR-030, ćelije linije i nagrada

- Ćelija linije koju no-op vatra zahvati računa se kao šteta i u nagradi za trening, ne
  samo u evaluaciji (odluka korisnika uz PR #11). [Odluke](docs/specs/DECISION_RECORDS.md).

## 2026-11-09: ADR-030, odluke prije ponovnog pokretanja

- Gate na IoU rasta prema downwind elipsi na požarima koji rastu; vrijeme prethodnog
  segmenta u observationu; linija neovisna o koraku; 10 seedova i poređenje s nasumičnom
  linijom; CA: spašena površina primarno, sigurnost kao uslov; 98 TRAIN (bez duplikata).
- [odluke](docs/specs/DECISION_RECORDS.md), [NEXT_SESSION](docs/NEXT_SESSION.md).

## 2026-11-09: revizija PR-ova #3–#5, gridMET ispravka i ADR-029

- gridMET uzorkovanje je koristilo ćeliju prvog požara u godini za sve ostale (97/99
  TRAIN, 19/20 VALIDATION pogrešno); ispravljeno u PR #3.
- Rezultati ADR-022–028 su nevažeći do ponovnog pokretanja; PR-ovi spojeni kao historija.
- Plan ispravki TASK-021–027: [NEXT_SESSION](docs/NEXT_SESSION.md),
  [odluka](docs/specs/DECISION_RECORDS.md).

## 2026-11-05: sintetički CA trening i jednokratni test (ADR-028)

- Novi CA simulator, okruženje s fizički ograničenim jedinicama i kontrafaktualna nagrada.
- PPO od nule nije prošao; imitacija + PPO je dala policy-v1, izjednačenu s heuristikom
  i jasno bolju od no-op. Na 119 stvarnih startova čuva 12% više od no-op (simulirani
  ishod). Jaz kalibracije: medijan IoU 0.27–0.30 na 48h.
- [STATUS](docs/STATUS.md), [NEXT_SESSION](docs/NEXT_SESSION.md),
  [spec](docs/research/SYNTHETIC_CA_ENV.md), [izvještaji](reports/synthetic/index.md).

## 2026-11-04: koraci 5–8 (noćni samostalni rad)

- Ulazi ponovo izgrađeni i reproducirani (isti hashovi, isti WAF .01 IoU). Dijagnoza
  pada gatea i preregistrovana 3×3 mreža (ADR-023): bez prolaza; gate zamrznut kao
  `FAIL_exploratory` (ADR-024).
- Validation skoriran jednom po zapisu; free-burn stress zapis deklarisan za korake 7–8.
- ADR-025: jedinica budžeta = smjena ekipe od 20 ljudi = linija od 7 ćelija; heuristike i
  upareni benchmark. ADR-026/027: 5 seedova, 20 modela, 1,920 VALIDATION epizoda; osnovni
  PPO pobjeđuje no-op, fine-tuning po budžetu nema mjerljive koristi.
- [STATUS](docs/STATUS.md), [NEXT_SESSION](docs/NEXT_SESSION.md),
  [benchmark](reports/real-fire-data/feds-simfire-policy-benchmark-v1.json),
  [odluke](docs/specs/DECISION_RECORDS.md).

## 2026-11-03: Handoff i agent upute usklađeni s ADR-022

- Ažurirani su AGENTS, Claude/Gemini/Copilot ulazi, project context, HANDOFF, README,
  backlog, code map i data/research ulazi da razlikuju data-coverage PASS od TRAIN
  no-op FAIL.
- Ispravljena je zastarjela uputa da je TASK-012/CFSDS još aktivan i da no-op kohortni
  gate tek slijedi. Stariji eksperimenti i odluke ostaju u historiji.
- Sljedeći korak je dijagnostika i ponovljeni zajednički TRAIN gate; validation rasteri
  i TEST 2024 ostaju zatvoreni do prolaza/odgovarajuće faze.

## 2026-11-03: TRAIN-only SimFire no-op screen — gate FAIL

- Osam WAF kandidata je poređeno na istih 99 TRAIN slučajeva i 396 vremenskih tačaka po kandidatu, uz no-op, persistence i fiksnu 2:1 elipsu.
- WAF .01 sa 1-min internim korakom dao je IoU .4771 (naspram .4769 na 5 min), bez rubnog kontakta; zaključak se nije promijenio.
- Nijedan kandidat nije prošao; persistence IoU=.5343, elipsa=.5308, najbolji SimFire=.4769. WAF .605 ima rubne kontakte u 61/99 slučajeva.
- Nije izabran WAF/timebase. Validation rasteri i 2024 TEST ostaju zatvoreni; benchmark PPO čeka dijagnostiku i prolaz novog TRAIN gatea.
- [Izvještaj](reports/real-fire-data/feds-simfire-train-noop-screen-v1.json), [status](docs/STATUS.md), [ADR-022](docs/specs/DECISION_RECORDS.md), [environment record](docs/research/SIMFIRE_ENVIRONMENT.md).

## 2026-11-03: TRAIN-only FEDS/SimFire PPO putanja

- Na korisnikov direktni zahtjev dodan je Gymnasium env i MaskablePPO CLI za 99 TRAIN
  slučajeva. Epizoda ima 48h/četiri 12h koraka; budžet ne prekida epizodu, no-op je uvijek
  legalan, a kumulativno opožarene ćelije ostaju šteta i kad ih SimFire prepiše linijom.
- Agent ne prima buduće FEDS obode; reward koristi samo dodatni simulator burn. Akcijski
  prostor (no-op + 8 kratkih sektorskih fireline poteza) je prototip, ne operativno
  validiran model gašenja.
- Python 3.9.25 venv package check je vraćen na PASS. Pošto je ciljni UV interpreter
  zaglavljen, `bin/python` poziva isti provjereni 3.9 runtime iz sačuvanog susjednog
  worktreea; lokalne biblioteke ostaju u aktivnom venv-u.
- Završio je 64-step CPU PPO smoke, checkpoint save/reload i završni TRAIN rollout.
  Izlaz ostaje ignorisan pod `.local/feds-ppo-smoke-waf-0.605-64steps`. WAF .605 je samo
  provisionalni smoke ulaz; nije kalibrisan. TRAIN cohort gate je naknadno dovršen i
  pao; vidi novi screening izvještaj. Validation mape i test 2024 nisu otvoreni.
- [ADR-021](docs/specs/DECISION_RECORDS.md), [environment/runbook](docs/research/SIMFIRE_ENVIRONMENT.md),
  [TRAIN env](src/wildfire_rl/feds_simfire_env.py), [CLI](scripts/train_feds_simfire.py)
  i [regresijski testovi](tests/test_feds_simfire_env.py).

## 2026-11-03: lokalni FEDS audit, širi candidate frame i SimFire runtime lock

- Checksum-verifikovane su train/validation FEDS perimetar arhive 2018/2019/2023; 2024
  test nije preuzet. Originalna kohorta lokalno daje 19/40 train i 7/20 validation, i
  dalje ispod 20/8. Širi, unaprijed spremljeni FPA screen frame daje 99/208 i 20/56 te
  119 punih FEDS 48h epizoda. Ova eksplicitna izmjena je u [ADR-018](docs/specs/DECISION_RECORDS.md).
- Dodani su local MD5 audit, checksum-aware, year-limited FEDS downloader i episode
  manifest builder. Crosswalk provjerava kompletan event time series nakon ranog
  3km matcha; 14 ciljanih testova prolazi.
- SimFire 2.0.1 pinovan je na upstream commit; Python 3.9 ARM64 freeze/setup je odvojen
  od projekta Python ≥3.11. [Environment record](docs/research/SIMFIRE_ENVIRONMENT.md).
- Active-front, 180m grid i inputi prolaze za 119 train/validation startova, a svih 99
  train slučajeva imaju checksum-verifikovane LANDFIRE rastere. Jedan 48h historijski
  Plateau no-op pilot otkriva strm WAF prag; parametar nije izabran i no-op gate ostaje
  otvoren. Sljedeće: cohort train kalibracija i persistence/elipsa prije validation.
  To nije fizička validacija; nema PPO treninga ni test pristupa.

## 2026-11-03: SimFire/FEDS podaci i pre-agent gate

- Po korisničkoj odluci novi aktivni pravac je SimFire + FPA-FOD/FEDS-CONUS, uz
  ograničeni FLE/ICS-209 post-hoc kontekst. Stari CFSDS/Cell2Fire izbor ostaje historijski.
- Napravljen je test-excluded manifest od 40 train i 20 validation požara; FEDS tražen
  prostornim HTTP Range upitima, bez preuzimanja 1.2 GB godišnjih fajlova.
- Strogi datum/tačka/3 km crosswalk traži obod u prvih 24h od `t_st`; nalazi 13/40
  train i 7/20 validation sa ≥2 uzastopna 12h FEDS stanja. Prag 20/8 pada u oba splita.
  Eksplorativnih 17/12 slučajeva koristilo je preširok vremenski kriterij i supersedovano je.
- FLE grupisani incidentni sažetak: 0/40 train, 13/20 validation. Test nije učitan.
  SimFire nije portovan, no-op replay/PPO nisu pokrenuti. Validation je deterministički
  postfiltriran iz sačuvanih kandidata; nova Zenodo provjera nije uspjela zbog DNS-a.
- [Detaljna metoda i ograničenja](docs/research/FPA_FEDS_CROSSWALK.md),
  [kombinovani JSON](reports/real-fire-data/fpa-feds-fle-crosswalk-v1.json),
  [ADR-017](docs/specs/DECISION_RECORDS.md), [radni dnevnik](docs/WORK_LOG.md).

## 2026-10-30: CFSDS putanja izabrana i prvi stvarni C++ replay

- Po korisnikovoj uputi odabrana je Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire, jer je to najbolji fit postojećem simulatoru. Stvarni historijski rast ostaje zaseban reality-check; RL iskustvo generiše simulator.
- Preuzeto je 2002–2024 CFSDS u Git-ignorisan raw storage; source size/SHA-256 manifest je u `reports/real-fire-data/cfsds-download-manifest.json`. Geometrijski screen za 2014–2024 zadržava do pet kandidata godišnje, 44 ukupno (20 train, 9 validation, 15 test) po požar-godini. To nije iscrpan niti finalan benchmark.
- TASK-017 `InitialState.csv` adapter importuje ranije izgorjeli scar i više aktivnih ćelija. Fixture i stvarni C++ import prošli su.
- Case builder `scripts/build_cfsds_case.py` pretvara `2018_747` u 20×20/100m Firehose ulaze: FBP 2014b gorivo, MRDEM 30m, satni ERA5-Seamless weather i historical start state. Naredni dan ostaje odvojen u `truth/`, ne u agent inputu.
- Novi real-case Docker image je ponovo prošao 12/12 postojećih Sub20 smoke/inference slučajeva; svi C++ kodovi su 0, a PPO težine nepromijenjene. Receipt: `reports/firehose-verification/real-case-image-regression.json`.
- Šest no-action C++ seedova (123–128, bez treninga/intervencija) dalo je identičnu završnu mapu od 66 ha prema CFSDS cilju 15.39 ha; area-weighted IoU 0.2187; svih 6 predikcija je dodirnulo 19 rubnih ćelija modelskog prozora, dok se trajanje simulacije razlikovalo. [Seed-sweep izvještaj](reports/real-fire-data/2018_747-seed-sweep.json). Suppression status je nepoznat. Ovo je mismatch dijagnostika, ne fizikalna validacija ni dokaz politike.
- Case manifest, replay JSON, mapa i update odluka/statusa/backloga su u reports/data/docs. Dodatno pokrenuto pet seed ponavljanja; ukupno šest runova imaju isti input/final mask, dok je trajanje 206–363 simulator minute. Nema treniranja, remote objave, commit-a ili merge-a u ovom koraku.

## 2026-10-30: još dva CFSDS train replaya i fuel QC nalaz

- Pretvoreni su i pokrenuti `2018_241` i `2018_1770` s istim 20×20/100m setupom, satnim ERA5-Seamless vremenom, MRDEM 30m i `steps-before=0`. Bez akcija simulator daje 237 ha / 12.153 opaženih (IoU .0376; 400/400 ćelija zahvaćeno) i 73 ha / 12.151 ha (IoU .1361). Oba imaju po jedan seed.
- `2018_241` je ponovljen sa 20 minuta početnog simulator zagrijavanja: završni grid i mjere ostali su isti. `2018_747` seed 123 takođe je ponovljen bez zagrijavanja, uz iste 66 ha/.2187 mjere.
- Geometrijski kandidat `2014_538` nije prošao converter: bar jedna historijska scar/front/target ćelija postaje water/nonfuel pod Canadian FBP 2014b; nije pokrenut u C++.
- Ažuriran je plotting CLI da datume i event ID čita iz case manifesta. Sačuvani su novi FireCase manifesti, replay JSON-ovi, warmup poređenje, tri karte i fuel-rejection receipt. Nalaz je da se screening po geometriji mora dopuniti fuel QC, a simulator treba kalibraciju/ulaznu dijagnostiku prije RL treniranja.


## 2026-10-30: lokalni BiH FireSpread_MedEU pregled

- Skinut je FireSpread_MedEU v2 ZIP od 2.75 MB u Git-ignorisan `data/raw/` samo za prostorni screening. Presjek sa Natural Earth državnom granicom otkrio je 7 BiH kandidata: EFFIS IDs 12321, 13228, 22108, 25244, 25274, 43482, 205938. Hashovi, datumi, kvalitet i granice metode su u [spatial-screen izvještaju](reports/real-fire-data/medeu-spatial-screen.json); raw nije u Git-u.
- `205938` ima 4 dnevna koraka vrlo visoke kvalitete, ali extenta 4.14×4.18 km; `43482` je 216.87 ha, ali extent 2.56×1.71 km. Oboje prevazilazi postojeći 2×2 km agentov prozor.
- Skinuta je i EFFIS European Fuel Map 2017 (18.2 MB; 250 m; NFFL/Anderson). Overlap daje kodove 4/5/9 za `205938` i 3/5 za `43482`; ovaj format goriva nije kompatibilan direktno s trenutnim Canadian FBP buildom. Rastera, hashova, licencnih napomena i model ograničenja ima u istom [spatial-screen izvještaju](reports/real-fire-data/medeu-spatial-screen.json).
- Preporuka je uslovna: CFSDS ako zadržimo Canadian FBP/Cell2Fire; MedEU ako želimo BiH historijske slučajeve, uz izbor regionalnog fuel modela, license provjeru, potvrdu event lokacija i grid odluku.
- Ažurirani su [X/Y pipeline](docs/research/REAL_CASE_PIPELINE.md), [dataset pregled](docs/research/REAL_FIRE_DATASETS.md), `DATASET`, HANDOFF, STATUS, backlog, manifests, izvori i environment receipt. Nema simulator conversion/replay, treninga ili potvrđene fizike.

## 2026-10-30: dataset prijedlog i ponovljen environment setup

- Početni cross-dataset pregled i environment setup su zabilježeni; noviji rezultat je BiH prostorni screen opisan iznad. Aktuelna preporuka zavisi od toga da li ostajemo na Canadian FBP ili prelazimo na BiH/regionalni model.
- Dodane su odluke koje ostaju otvorene, CFSDS v1.1 istraživanje, model/scenario split ugovor i TASK-014/015/004c redoslijed.
- [Environment receipt](reports/environment-setup/README.md): Python 3.12.4 moderni venv, 26+15 testova, smokeovi i Linux ARM64 legacy image/inference; bez treninga Firehosea.
- Ponovljeni pinovani Sub20 inventar odgovara hash-manifestu; ignition 381/372 su dvije različite gorive ćelije, a Data.csv ima jedan krnji red. Nema konačnog dataset izbora ili fizikalne validacije.

## 2026-10-28: Workspace raspored

- [Runbook](knowledge/workspace-layout.md) definiše mpvi glavni klon, .worktrees i ignorisani .local prostor, uz očuvanje PR-a i dataset prioriteta.
- [Dokaz preseljenja](reports/workspace-relocation.json) čuva hash/package/test provjere i ponovljeni setup iz novog klona.

## 2026-10-28: OKF 0.2 bundle u repozitoriju

- Dodani typed koncepti, lowercase indeksi, [kontekst](knowledge/project-context.md), [mapa koda](knowledge/code-map.md) i [održavanje](knowledge/maintenance.md).
- Root [index](index.md) i [AGENTS](AGENTS.md) vode do izvora i dokaza bez vanjske baze/chat historije; mali agent ulazi dijele ista pravila.
- [OKF profil](knowledge/okf-format.md) pinova specifikaciju; zaseban checker/CI provjerava strukturu i projektne linkove, bez tvrdnje o naučnoj verifikaciji.
- [Završni receipt](reports/knowledge-validation.json) čuva 63-file provjeru, 15 knowledge testova, clean-clone rezultate i hashove; pregled i regresijske ispravke su u [REVIEW](docs/REVIEW.md).

## 2026-10-28: Dataset refinement ostaje otvoren

- Korisnik je ispravio redoslijed: [TASK-012](docs/BACKLOG.md) je prvi projektni korak, izbor i obim još nisu usaglašeni; ADR-009.
- Handoff i PR usklađeni; postojeći runtime nalazi ostaju važeći.

## 2026-10-28: Bootstrap, runtime i pregled izvora

- Sačuvani [pilot](reports/pilot/README.md), [Firehose dokazi](reports/firehose-verification/README.md) i [Dogrib/CFSDS profili](reports/real-fire-data/README.md).
- Detaljan redoslijed, komande, rulings i pregledi su u [WORK_LOG](docs/WORK_LOG.md) i [REVIEW](docs/REVIEW.md).
