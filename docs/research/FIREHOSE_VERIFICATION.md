# Firehose/Cell2Fire izvršavanje — 2026-10-28

## Zaključak
**Runtime provjera je prošla:** izvorni Cell2Fire fork je kompajliran, oba postojeća
20×20 MaskablePPO checkpointa su učitana i izvršena u simulatoru. Nije bilo treniranja.
Firehose ostaje odabrani kandidat za narednu fazu; trenutno nema razloga za promjenu
simulatora. Potpuni istraživački gate još traži ispravljen observation/metrics adapter.

Dokazi: [verification.json](../../reports/firehose-verification/verification.json),
[summary.csv](../../reports/firehose-verification/summary.csv),
[pojedinačni runovi](../../reports/firehose-verification/README.md).

## Tačno okruženje
- Firehose: `e49a52a9a987a1585d25ddca2f711222ca500ffb`.
- Autorski contrib fork: `43b7fe6fcdda71c2c10de7af0d20f39e48ae5df3`, SB3/contrib 1.5.0.
- Python 3.8.20, Gym 0.21.0, PyTorch 1.13.1 CPU, numpy 1.23.5, Linux ARM64.
- Originalni checkpoint navodi Python 3.8.12 / PyTorch 1.11.0 / numpy 1.22.2;
  ovo potvrđuje kompatibilno izvršavanje, ne bit-identičnu originalnu mašinu.
- Službeni Python base image pinovan digestom u Dockerfileu. Izlazni image i sve
  verzije su u environment manifestu/freeze fajlu.
- C++ kod nije mijenjan: override compile/link flags za Eigen, OpenMP i ARM64,
  bez x86-only `-m64`. `Makefile_serial` koristi stvarni OpenMP runtime, 1 thread.
- Runtime bez mreže, read-only root, bez capabilities, CPU/memory cap i timeout.
  Host izlaže samo prazan run folder; sav vanjski kod/modeli su u imageu.
- Moderni Python 3.13 `.venv` nije mijenjan. Rani Python 3.10 image/managed runtime
  nisu korišteni nakon što je metadata pokazala da checkpoint potiče iz Pythona 3.8.

## Šta je izvršeno
12 kratkih rollouta: no-action, min-L2, max-L2, fixed i random-ignition pretrained
modeli; ponavljanje seeda 123, seedovi 124/125 i provjera reset sinhronizacije.
Mapa je Sub20x20; ignition 372 (one-based), kao u upstream fixed-model evaluaciji,
a ne 381 iz dostavljenog `Ignitions.csv`. Weather je `Weather.csv`, rows mode,
20 početnih fire perioda, 8 fire perioda po akciji, ROS-CV=0.5, 1 thread.
Svi runovi imaju identičan input hash, 58 odluka i C++ returncode 0.

- Isti seed i politika ponavljaju cijeli niz state hashova i akcija.
- Drugi simulator seed mijenja širenje. Seed se eksplicitno prepisuje u C++ komandi;
  samo Python RNG ne bi bio dovoljan zbog originalnog hardcodiranog `--seed 123`.
- B=8 strogo ograničava broj zahtjeva; zatim slijedi besplatan legacy no-op -1 do done.
  Izlaz politike ostaje Discrete(400), bez dodavanja 401. learned akcije.
- Oba checkpointa zadržavaju identične hashove policy tensorâ prije i poslije inferencije.
- Nijedan od osam zahtjeva u model runovima nije ciljao nonfuel ćeliju. To ne dokazuje
  ispravnost originalne maske u svim scenarijima: ona prvenstveno uklanja ranije akcije.

Primjer seeda 123/B=8: fixed PPO ima 207 ikad opaženo pogođenih ćelija, no-action 217,
min-L2 193, max-L2 217, random-ignition PPO 211. Ovo je **provjera izvršavanja na jednom
scenariju**, ne poređenje kvaliteta, statistički rezultat ili dokaz RL prednosti.

## Utvrđeni problemi prije glavnih eksperimenata

1. **Početno opažanje i ranija šteta.** Nakon warmupa CSV ima 7 pogođenih ćelija,
   a upstream reset vraća prazno stanje. Kod fixed PPO-a originalni brojač na kraju
   daje 206, a unija svih sačuvanih gridova 207. Opcija `--sync-reset` učitava stvarni
   warmup CSV i inicijalizuje brojače; tada oba daju 207. Ta sinhronizacija ne mijenja
   arhitekturu/težine, ali mijenja kontrakt prvog opažanja i mora biti jednaka svim
   politikama u glavnom eksperimentu. Originalno i korigovano ponašanje su odvojeno sačuvani.
2. **Grid 1 nije samo aktivni požar.** C++ `outputGrid()` označava i burningCells i
   burntCells vrijednošću 1. Zato `state > 0`, upstream `num_cells_on_fire` i
   min/max-L2 ne razlikuju aktivnu frontu od ranije opožarenog. Ne interpretirati te
   brojače kao aktivni požar. Originalni FireSizeReward zato penalizuje pogođeni footprint,
   ne samo aktivni plamen; zamjena rewarda bila bi zasebna promjena za ablation.
3. **Kraj epizode nije potvrda gašenja.** Osam weather redova ograničava horizont
   na 480 minuta. Svih 58 odluka je konzistentno s tim capom nakon warmupa i koraka
   po 8 minuta. `done` ne razlikuje containment od kraja weather horizonta, a godišnji
   prelaz premješta preostale burning ćelije u burnt skup. Treba eksplicitni reason i
   active/burnt brojači prije tog prelaza. Do tada ne prijavljivati stopu containmenta.
4. **Dataset coverage.** Postoje 129 alternativnih weather traceova uz bazni fajl,
   ali rows mode sam ih ne bira. Provenance i izrada tih alternativa nisu potvrđeni.
   Nema priority maske za Sub20x20; treba je posebno definisati i verzionisati.

## Tehnički nastavak nakon dataset refinementa — TASK-004c

Neposredni projektni fokus je TASK-012 — razjašnjenje i usaglašavanje podataka,
vidjeti [REAL_FIRE_DATASETS](REAL_FIRE_DATASETS.md). Ispod ostaje poznata tehnička
prepreka prije glavnih eksperimenata postojećim pristupom.
Formalizovati tanki adapter sa stvarnim početnim opažanjem, trajnim damage skupom,
validnim gorivim akcijama i prisilnim no-op nakon B. Eksportovati termination reason i
active/burnt state iz C++ prije resetovanja terminalnog stanja. Dodati integracijske
testove, uz očuvanje RGB 3×20×20 i 400-action kontrakta pretrained modela.
Tek zatim freeze scenario split i krenuti u frozen benchmark/fine-tuning.
Nema izvedene preporuke za stvarne požare ili provjere tačnosti simulatora na BiH podacima.
