---
type: Experiment Report
title: SimFire B=1 — obračun linije, iscrpna tabela i offline učenje
sources:
  - resource: /configs/frozen/feds-b1-exploration-v1.json
  - resource: /src/wildfire_rl/line_damage.py
  - resource: /scripts/enumerate_feds_b1.py
  - resource: /scripts/analyze_feds_b1.py
---
# SimFire B=1 — nastavak nakon faze 2

Stanje 2026-11-19. Grana `codex/simfire-policy-iterations`, baza `f96f744f`.
Korisnik je odabrao SimFire i iterativan, dokumentovan nastavak. ADR-033 bilježi obim,
pretpostavke, fiksne metode i stop-uslove prije analize. Ovo su TRAIN eksperimenti;
VALIDATION nije ponovo korišten, TEST 2024 nije otvoren, CA trening nije pokrenut.

## Pitanje i redoslijed

1. **TASK-028:** Koliko rezultat mijenja konzervativna naplata ćelija linije?
2. **TASK-029:** Koliko najbolji mogući izbor jedne linije može pomoći na istom požaru?
3. **TASK-030:** Može li politika iz trenutnog opažanja naučiti izbor koji pomaže na
   požaru izostavljenom iz fita?

Ovaj redoslijed provjerava prostor za učenje prije novog dugog PPO treninga. Početni
PPO checkpointovi nisu učitani i nisu trenirani. Originalni ADR-031/032 rezultat i
njegove postavke ostaju sačuvani; novi obračun ne mijenja retroaktivno stare brojeve.

## Šta je implementirano

`score_line_damage` računa originalnu novu štetu i uniju te štete s ćelijama linije
unutar novog no-op otiska. Početni scar je isključen iz nove štete; nema dvostrukog
brojanja. Ovo je alternativna modelna konvencija: 180 m ćelija nije izmjerena širina
stvarne vatrogasne linije. Prijavljuju se oba obračuna.

Runner za svaki požar izvršava no-op i osam smjerova u četiri termina (33 niza).
Nelegalan izbor postaje no-op; traženi i efektivni potezi ostaju zabilježeni. Sve
epizode traju četiri odluke / 48 h, i nakon potrošenog budžeta. Mape, WAF 0.10,
ROS 1.0, korak 5 min, `last_write`, `front_edge` i opažanje ostaju isti kao u ADR-032.

Čuva se cijela burn/line maska svakog ishoda, no-op putanja opažanja i legalnih poteza,
hashovi koda, plana, manifesta, vremena i receipt-a. Zasebni heuristički rollout mora
odgovarati tabeli i po broju ćelija i po cijeloj burn maski. Ponovljeni no-op mora biti
identičan. Resume odbija promijenjene postavke, ulaze ili mask artefakt.

## Inputi i razlika u odnosu na prethodni računar

Svih 98 TRAIN mapa bilo je dostupno lokalno. Lokalni weather cache je bio stari,
neispravljeni fajl. Sampler je proširen s `--split train`, uz test koji provjerava da
nikad ne otvara validation arhivu ili njenu geometriju. Ponovo su uzorkovani samo
2018/2019, s ispravnim per-case ćelijama, pre-start zapisom i FEDS local-solar mapiranjem.
Svih šest izvornih arhiva ima iste SHA-256 kao commitovani ADR-032 izvori. Novi weather
hash je `76332f3da26fe02812ca6439fee5dec9f131793227335e0380267d12c0ab937e`;
98 različitih ćelija, najveća udaljenost 2.8025 km.
[Weather profil i hashovi](../../reports/real-fire-data/feds-b1-train-weather-v1.json) su u Gitu;
same vrijednosti i NetCDF ostaju lokalni.

Originalni puni ADR-032 TRAIN benchmark nije dostupan na ovom računaru. Zato pilot
koristi nezavisne svježe scripted runove na istim ulazima. Cijela kohorta se dodatno
poredi s commitovanim no-op i B=1 heurističkim prosjecima. Ni savršeno slaganje agregata
ne bi dokazalo jednakost svakog pojedinačnog požara s nedostupnim starim izvještajem.

## Offline učenje i zaštita od curenja

Svaki od 98 foldova izostavlja cijeli jedan požar. Skaliranje i model koriste samo
ostalih 97. Odluka dobija trenutno opažanje i masku; nema budućih opažanja, vremena,
identiteta požara ili njegovog ishoda. Prije jedine linije putanja je jednaka no-op-u,
zato se svaka B=1 politika može tačno ocijeniti preko tabele bez nove simulacije.

Prijavljeni meni: postojeći `advancing_front` i `downwind`; najbolje fiksno vrijeme i
smjer izabrano na fit požarima; linearni ridge fitted-Q s alpha 1/10/100; tabelarni
fitted-Q; imitacija učitelja pomoću pet najbližih fit požara. Fitted-Q uči unazad kroz
četiri odluke: linija dobija konačni dobitak, čekanje vrijednost sljedećeg stanja.
Učitelj imitacije bira najbolji preostali niz koristeći buduće simulirane ishode
samo na fit požarima. Fitted-Q vrijednost čekanja ima donju granicu 0: uvijek
postoji poznata opcija da se nikad ne interveniše. To sprečava biranje predviđenog
gubitka zbog još lošije ekstrapolirane vrijednosti čekanja; ne garantuje stvarni dobitak.
Oracle na izostavljenom požaru vidi sve buduće
ishode i služi samo kao gornja granica, nikad kao dozvoljena politika.

Oba obračuna imaju zaseban fit. Prikazuju se svi kandidati, ne samo najbolji. Opisni
95% intervali su paired percentile bootstrap fiksnih OOF razlika (10.000 uzoraka,
seed 0), bez ponovnog fita modela. Foldovi dijele fit požare, pa ovo nije nezavisan
potvrdni interval. Izbor metode na istim LOO rezultatima je istraživačka selekcija.

Prag za nastavak iz ranijeg pregleda: najmanje 30 ha i 25% oracle jaza iznad
`advancing_front`. Neuspjeh ovog konačnog menija ne dokazuje da dobra odluka uopće
nije predvidiva iz opažanja.

## Rezultati

U toku: završen je pilot 20/20; puna tabela i offline analiza slijede. Brojevi se
upisuju nakon završetka i provjera, bez promjene unaprijed zadatih metoda ili praga.

## Reprodukcija

Koristi pinovani Python 3.9 SimFire venv iz [environment runbooka](SIMFIRE_ENVIRONMENT.md).
Podaci i puni izlazi su ignorisani. `P` ispod je putanja do tog interpretera; nije
potrebna ista lična putanja ili stari checkout. Obnovi TRAIN mape i gridMET arhive
2018/2019 iz javnih izvora; validation se ovdje ne preuzima.

```sh
export PYTHONPATH=src SDL_VIDEODRIVER=dummy OMP_NUM_THREADS=1
export MPLCONFIGDIR="$PWD/.local/mpl-cache" XDG_CACHE_HOME="$PWD/.local/cache"
P=.local/simfire-venv/bin/python
"$P" scripts/sample_gridmet_episode_weather.py --split train \
  --out .local/gridmet/feds-episode-weather-v1.json \
  --coverage-report .local/b1/weather-coverage.json
nice -n 19 "$P" scripts/enumerate_feds_b1.py \
  --weather .local/gridmet/feds-episode-weather-v1.json \
  --input-root .local/feds-simfire-cases --out .local/b1/cases --case-limit 20 --workers 4
# Tek nakon uspješnog pilot reference checka: ista komanda bez --case-limit.
"$P" scripts/summarize_feds_b1.py .local/b1/cases/table-98.json \
  --input-root .local/feds-simfire-cases --out .local/b1/table-check.json
nice -n 19 "$P" scripts/analyze_feds_b1.py .local/b1/cases/table-98.json \
  --out .local/b1/analysis.json
"$P" scripts/plot_feds_b1.py .local/b1/analysis.json --out .local/b1/analysis.png
```

Regeneracija weather JSON-a mijenja hash zbog vremena kreiranja. Resume zahtijeva isti
fajl i identične source hashove; za novi input ili izmijenjeni runner koristi novi
output folder. Objavljeni sažeci sadrže hashove lokalnih potpunih izlaza. Git klon
ne sadrži same velike tabele, raw rastere ili environment.

## Tehničke provjere

[Lokalni verification receipt](../../reports/real-fire-data/feds-b1-verification-v1.json)
čuva verzije, source hashove i hashove logova. Pinovani SimFire 2.0.1 je na izvornom
commitu `04905b19fe8c10dc08d64faddd00303e0561bb66`, Python 3.9.25 / NumPy 1.26.4.

- Pinovani runtime: **312 testova, 0 preskočenih, PASS**.
- Moderni venv: **299 testova, 3 preskočena, PASS** (nedostupne dodatne zavisnosti).
- Osnovni Python: **261 test, 34 preskočena, PASS** (opcionalni paketi).
- Knowledge unit testovi: **15/15 PASS**; strogi checker: **83 Markdown fajla PASS**.
- Synthetic CLI smoke: PASS, samo tehnička provjera pipelinea.

Dugi runovi koriste četiri nice-19 radnika. Tokom tri test suite-a jedan radnik je
pauziran 211.4 s i potom nastavljen; vrijeme slučaja uključuje pauzu. Raw podaci i
tuđi worktree nisu mijenjani. GitHub CI i nezavisna revizija ove grane nisu izvršeni.
Nijedna od ovih provjera ne potvrđuje fizičku tačnost ili prednost politike.

## Otvoreno

SimFire nije fizički validiran ovim radom. LOO na TRAIN-u nije završni test, a studija
B=1 ne rješava korist prilagodbe na B=2/B=4. Nova VALIDATION upotreba, dodatni budžeti
i promjena zvanične metrike zahtijevaju novi protokol prije rezultata.
