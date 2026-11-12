---
type: Playbook
title: Handoff za nastavak projekta
---
# Handoff za nastavak projekta

Stanje **2026-11-12**. Ovaj dokument je ulaz za kolegu ili agenta koji preuzima projekat bez
chat historije. Repozitorij je kanonski izvor; artifact za tim (link ispod) je sažetak za
čitanje.

## Gdje je projekat (jedan pasus)

Pitanje: može li RL agent s budžetom od B vatrogasnih linija smanjiti izgorjelu površinu
više od jednostavnih pravila, i pomaže li fine-tuning za zadani B. Glavni simulator je SimFire
pokrenut od stvarnih početnih stanja 118 američkih požara (98 TRAIN 2018/19, 20 VALIDATION
2023; TEST 2024 zatvoren). Raniji rezultati su poništeni (ADR-029, greška u vremenskim
podacima), greške su ispravljene, a ponovno pokretanje je dalo: **faza 1** gate PASS, zamrznut
WAF 0.10 / ROS 1.0 (ADR-031); **faza 2** nijedan od šest primarnih testova ne odbacuje, PPO
se ne razlikuje od nasumične linije ni od najbolje TRAIN heuristike, fine-tuning po budžetu
ne daje dobitak (ADR-032). **Pregled 2026-11-11** (literatura i dijagnoza, bez novih
treninga) kaže da je to očekivano i predlaže jeftinu TRAIN-only provjeru gornje granice
prije bilo kakvog novog treninga: [sažetak i plan](docs/research/review-2026-11-11/SUMMARY.md).

## Grane i pull requestovi

`main` je na `7be6b56` i **još ne sadrži faze 1 i 2**. Otvoreni PR-ovi idu redom, svaki na
prethodni; spaja ih samo Harun:

1. PR #17 `f/task-026-stage-1` → `main` — faza 1 (ADR-031).
2. PR #18 `f/task-026-stage-2` → `f/task-026-stage-1` — faza 2 (ADR-032).
3. PR #19 `docs/research-review` → `f/task-026-stage-2` — pregled 2026-11-11, ovaj HANDOFF.

Provjera: `gh pr list --state all --limit 5`. Dok nisu spojeni, radi iz najnovije grane
(`docs/research-review`) ili iz worktreea `.worktrees/research-review`. Kad se spoje,
`main` je aktuelan i nove grane se prave iz njega.

## Šta pročitati, redom

1. [AGENTS](AGENTS.md) (pravila), [index](index.md), [projektni kontekst](knowledge/project-context.md).
2. [STATUS](docs/STATUS.md) i [NEXT_SESSION](docs/NEXT_SESSION.md): najnovije sekcije su na vrhu.
3. [Pregled 2026-11-11](docs/research/review-2026-11-11/SUMMARY.md): odgovori na pet pitanja,
   odluke koje čekaju, redoslijed TASK-028–033.
4. ADR-029 do ADR-032 s dopunama u [odlukama](docs/specs/DECISION_RECORDS.md).
5. [Šta politika smije raditi](docs/research/review-2026-11-11/INTERVENTIONS.md): tačan opis
   okruženja, akcija i heuristika (dokumentacija na nekoliko mjesta zaostaje za kodom).
6. Za pokretanje: [HANDOFF_STAGE_1_2](docs/HANDOFF_STAGE_1_2.md) §4–§6 (okruženje, komande
   faza 1 i 2) i [mapa koda](knowledge/code-map.md).

## Šta čeka odluku (Harun)

- Merge PR-ova #17, #18, #19.
- Kako se računa šteta kad linija zauzme ćelije koje bi izgorjele (sada se računaju kao spašene).
- Da li pokrenuti TASK-029/030 (iscrpna B=1 tablica i offline ocjena, samo TRAIN).
- Koji je simulator glavni za poster; da li sintetički CA smije vidjeti vrijeme tekućeg
  koraka; faza 3 (trening CA). Detalji: [NEXT_SESSION](docs/NEXT_SESSION.md), [BACKLOG](docs/BACKLOG.md).

## Pravila koja važe za svakog ko nastavlja

- Agent smije push i PR uz nezavisnu reviziju; **merge u `main` radi samo Harun**.
- TEST 2024 se ne preuzima ni ne otvara. VALIDATION se koristi samo unaprijed registrovano.
- Ne mijenjati gate, kandidate, metrike, statistiku ni pravilo izbora nakon rezultata;
  nova pravila idu u novi ADR prije pokretanja.
- Bez plaćenog ili cloud computea. Dugi poslovi: najviše 4 procesa, `nice -n 19`, i unaprijed
  reći koliko traje (trening ~95 min po seedu).
- Ne commitovati `.local/`, težine modela, sirove podatke, venv. Nikad `git clean -fdx`.
- `spread_aggregation` ostaje `"last_write"`; bez starih checkpointa i bez
  `--allow-legacy-checkpoints`.
- Simulatorski rezultat nije dokaz o stvarnom gašenju; gate PASS nije fizička validacija.

## Okruženje i podaci

**Novi računar.** Sve se obnavlja iz javnih izvora; ništa iz `.local/` nije u gitu.

1. SimFire okruženje (Python 3.9, pinovano):
   [SIMFIRE_ENVIRONMENT](docs/research/SIMFIRE_ENVIRONMENT.md), komande `uv venv` i
   `uv pip install -r requirements/simfire-macos-arm64-py39.freeze.txt`.
2. Ulazi: `scripts/build_feds_simfire_inputs.py --fetch-split train`, zatim
   `--fetch-split validation`; `scripts/fetch_gridmet_archives.py --year 2018 2019 2023`;
   `scripts/sample_gridmet_episode_weather.py`. Tačne komande su u SIMFIRE_ENVIRONMENT.
3. Ponovno generisan vremenski fajl dobija **novi sha256** (sampler upisuje `created_utc`).
   Zamrznuti zapis faze 1 navodi `7a51aadd…`. Za VALIDATION okruženje i benchmark odbijaju
   fajl čiji se hash ne slaže sa zamrznutim zapisom; na TRAIN-u se hash samo bilježi u
   izvještaj. Za poređenje s fazama 1 i 2 treba kopija tog fajla od Haruna; novi hash traži
   novi ADR prije korištenja VALIDATION-a. Manifest epizoda je u gitu (sha256 `013be9a1…`).
4. Provjera: `$P -m unittest discover -s tests` (282 prolaze s lokalnim podacima),
   `python3 scripts/validate_knowledge.py --strict`, `git diff --check`.

**Harunov računar** (`/Users/harungoralija/Desktop/mpvi`):

- Python: `.worktrees/overnight-steps-5-8/.local/simfire-venv/bin/python`.
- Vremenski fajl `7a51aadd…`: `.local/backups/gridmet/feds-episode-weather-v1-7a51aadd.json`.
- Faza 1, puni gate izvještaji: `.worktrees/task-026-stage-1/.local/gate/adr030/`.
- Faza 2: `.worktrees/task-026-stage-2/.local/ppo/adr030/` (40 modela),
  `.local/bench/adr030-train.json` (`709050e6…`), `.local/bench/adr030-validation.json` (`e8068e6b…`).
- Stari, neispravni vremenski fajl `7b0aa405…` u `.worktrees/overnight-steps-5-8/.local/gridmet/`
  je dokaz greške: ne dirati. Ne dirati ni necommitovane fajlove u tom worktreeu.
- Zaostali worktreeji (`.claude/worktrees/task-021…024`, `.worktrees/task-027-feds-utc-dedup`)
  i 8 neaktivnih Python procesa u `.worktrees/synthetic-ca-training` (od 5. 11.) uklanjaju se
  samo uz Harunovo „da“.

## Artifact za tim

Pregled za čitaoca koji ne zna projekat, s dijagramima i grafikonima:
https://claude.ai/artifact/EFi7EXKkvehgTt1GYtoi5Q. Privatan je; Harun ga dijeli kroz meni
Share. Prati stanje repozitorija; kad se razilaze, važi repozitorij. Ko ga ažurira prvo ga
pročita preko linka, pa objavi na isti link. Kopija HTML-a je u
[docs/team-overview](docs/team-overview/README.md), za otvaranje bez pristupa linku.

## Historija

Canada + CFSDS/Cell2Fire, Firehose i noćni SimFire koraci 5–8 su raniji pravci; njihovi
brojevi se ne citiraju kao nalazi (ADR-029). Trag je u
[experiment logu](docs/research/EXPERIMENT_LOG.md) i [odlukama](docs/specs/DECISION_RECORDS.md).

### Sintetički CA (ADR-028; brojevi poništeni ADR-029)

Grana `codex/synthetic-ca-training` nastavlja `codex/overnight-steps-5-8` (PR #4), koja
nastavlja `codex/fireline-simfire-benchmark` (PR #3). Nijedna nije spojena u `main`.

```sh
git clone --branch codex/synthetic-ca-training https://github.com/goralija/wildfire-rl-adaptation.git
cd wildfire-rl-adaptation
```

**Okruženje.** Sav sintetički rad koristi Python 3.9 venv iz
[`requirements/simfire-macos-arm64-py39.freeze.txt`](requirements/simfire-macos-arm64-py39.freeze.txt)
(numpy 1.26.4, torch 2.3.1, gymnasium 1.1.1, sb3/sb3-contrib 2.7.1). Postupak je u
[SIMFIRE_ENVIRONMENT](docs/research/SIMFIRE_ENVIRONMENT.md). Komande ispod pretpostavljaju
`P=".local/simfire-venv/bin/python"` i `PYTHONPATH=src PYTHONWARNINGS=ignore`.

**Šta treba za šta.**

| Posao | Treba stvarne podatke? | Treba težine? |
|---|---|---|
| Testovi, sintetički trening, BC, validacija na sjemenima | ne | ne (osim `--resume`) |
| Jednokratni test na 119 startova, dijagnostika, viewer | da: `.local/feds-simfire-cases` i gridMET | da |

**Težine** (~27 MB svaka) nisu u gitu. Prilozi su draft GitHub releasea
`synthetic-policy-v1`, koji vide samo članovi s pristupom repou. Preuzmi ih u
`.local/synthetic/locked/` i provjeri hash prije učitavanja (zip sadrži pickle):

```sh
mkdir -p .local/synthetic/locked
gh release download synthetic-policy-v1 --repo goralija/wildfire-rl-adaptation --dir .local/synthetic/locked
for m in policy-v1 bc2 main1-best; do shasum -a 256 -c reports/synthetic/$m.sha256; done
```

**Stvarni ulazi.** `.local/feds-simfire-cases` (~46 MB) i gridMET vrijeme obnavljaju se
iz javnih izvora po [SIMFIRE_ENVIRONMENT](docs/research/SIMFIRE_ENVIRONMENT.md):
`build_feds_simfire_inputs.py --fetch-split train`, zatim `--fetch-split validation`
(freeze zapis je commitan), plus `sample_gridmet_episode_weather.py`. Test split 2024
se ne preuzima. Fajl s vremenom iz TASK-027 (sha256 `7a51aadd…`, prolaz FEDS `t` u lokalnom
sunčevom vremenu) je u `.local/gridmet/` worktreea `task-027-feds-utc-dedup`, s kopijom u
`.local/backups/gridmet/` glavnog klona; worktree koji pokreće fazu 1 kopira ga u svoj
`.local/gridmet/` i provjerava hash. Svako ponovno generisanje daje novi hash (`created_utc`),
koji se onda mora upisati u izvještaj i freeze zapis.

**Komande** (stvarno korištene; sve izlaze u ignorisani `.local/`):

```sh
$P -m unittest discover -s tests -p "test_synthetic*.py"
# PPO od nule (main-1, ~4.5h na 6 procesa)
$P scripts/train_synthetic_ppo.py --steps 1500000 --eval-every 100000 --eval-seeds 64 --out .local/synthetic/runs/main-1
# Plan B: imitacija direct_flank (bc-2), pa PPO fine-tune (ft-1 -> policy-v1)
$P scripts/bc_warm_start.py --init .local/synthetic/runs/main-1/final_model.zip --teacher direct_flank --rounds 40 --episodes-per-round 42 --epochs 8 --keep-rounds 3 --workers 7 --out .local/synthetic/runs/bc-2/bc_model.zip
$P scripts/train_synthetic_ppo.py --resume .local/synthetic/runs/bc-2/bc_model.zip --steps 600000 --eval-every 100000 --eval-seeds 64 --learning-rate 1e-4 --ent-coef 0.001 --clip-range 0.1 --start-stage B --out .local/synthetic/runs/ft-1
# Prihvatanje na sjemenima 0-255 (pravilo iz ADR-028)
$P scripts/evaluate_synthetic_policies.py --seeds 256 --first-seed 0 --workers 7 --subset-from-seed 64 --policies noop,random,direct_flank,protect_urban,downwind_indirect,ppo=.local/synthetic/locked/policy-v1.zip --out .local/synthetic/acceptance.json
# Jednokratni test zaključanih politika na stvarnim startovima
$P scripts/evaluate_real_cases.py --policy-locked --comparator-heuristic direct_flank --workers 7 --policies noop,random,direct_flank,protect_urban,downwind_indirect,ppo=.local/synthetic/locked/main1-best.zip,ppo=.local/synthetic/locked/bc2.zip,ppo=.local/synthetic/locked/policy-v1.zip --out .local/synthetic/real-cases.json
$P scripts/diagnose_synthetic_calibration_gap.py --all --policy-locked --out .local/synthetic/calibration-gap.json
# Viewer: http://127.0.0.1:8766, politika protiv no-op na jednom stvarnom startu
$P scripts/synthetic_case_viewer.py --port 8766
```

**Otvorena timska odluka.** policy-v1 je izjednačen s `direct_flank` (prihvatanje FAIL),
a jasno je bolji od no-op. Treba odlučiti da li se ide dalje (DAgger, duži fine-tune,
oracle osnova za plafon) ili se rad zaključuje sa sadašnjim rezultatom. Za novi pokušaj
predlažemo novu preregistraciju i prihvatanje na novim sjemenima, jer su sjemena 0–255
već korištena za izbor checkpointa (napomena o selekciji u ADR-028). Detalji su u [NEXT_SESSION](docs/NEXT_SESSION.md) i ADR-028.
