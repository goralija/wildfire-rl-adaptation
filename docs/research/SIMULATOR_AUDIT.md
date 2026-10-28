---
type: Audit
title: Simulator i pretrained feasibility audit
---
# Simulator i pretrained feasibility audit

Datum provjere: 2026-10-28. **Firehose s njegovom izmijenjenom Cell2Fire jezgrom**
prošao je runtime provjeru oba modela. Nastavljamo taj backend; istraživački gate
čeka observation/damage/termination adapter (TASK-004c).

| Kandidat | Prednost | Cijena/rizik | Odluka sada |
| --- | --- | --- | --- |
| Firehose/Cell2Fire fork | izvorni RL rad i dostupni 20×20 checkpointi | legacy Gym/SB3, vlastiti contrib fork, C++ build i fiksni seed | prvo ograničena reprodukcija |
| Originalni Cell2Fire / Fire2A C2F-W | alternativni razvoj simulatora i modela goriva | interaktivni Firehose protokol nije automatski prisutan | ne zamijeniti binarni fajl bez testa |
| MITRE SimFire + SimHarness | Python simulator, RL harness, Rothermel i mitigacije | drugi kontrakt opažanja/akcija, setup i compute još nisu mjereni | fallback ako prva opcija ne prođe |
| Vlastiti synthetic-v1 | radi bez zavisnosti i provjerava metodologiju | nema kalibracije, vjetra, terena, GIS-a ili realizma | samo tehnički pilot |

## Dokaz iz izvornog koda

Firehose commit: `e49a52a9a987a1585d25ddca2f711222ca500ffb`.
Pinovani linkovi: [gym_env.py](https://github.com/aidan-curtis/firehose/blob/e49a52a9a987a1585d25ddca2f711222ca500ffb/cell2fire/gym_env.py),
[process.py](https://github.com/aidan-curtis/firehose/blob/e49a52a9a987a1585d25ddca2f711222ca500ffb/cell2fire/firehose/process.py),
[C++ loop](https://github.com/aidan-curtis/firehose/blob/e49a52a9a987a1585d25ddca2f711222ca500ffb/cell2fire/Cell2FireC/Cell2Fire.cpp),
[dependencies](https://github.com/aidan-curtis/firehose/blob/e49a52a9a987a1585d25ddca2f711222ca500ffb/requirements.txt).

Utvrđeno statičkim pregledom: akcija koristi Python indeks od nule, pretvoren u C++
indeks od jedan. Python no-op -1 postaje C++ 0 koji se preskače. Intervencija trajno
uklanja gorivu ili zapaljenu ćeliju. Proces koristi `--seed 123`; sama promjena Python
seeda ne daje nezavisne realizacije simulatora. Maska pamti ranije akcije, ali ne
implementira novi ukupni budžet. `reset()` vraća nultu mrežu umjesto učitanog početnog
požara. Treba testirati prvo opažanje i brojače, ne samo pokrenuti trening.

Dostupna dva 20×20 ZIP-a imaju SB3 verziju **1.5.0**, stari Gym i custom
`firehose.models.PaddedNatureCNN`. Metadata audita: `checkpoint-audit.json`.
ZIP JSON je pročitan bez pickle/cloudpickle/torch deserializacije; težine nisu učitane.
Root requirements ne pinova verzije i koristi vlastiti contrib Git fork.
Mac Makefile ima lokalnu Eigen putanju; kod traži Eigen, Boost i OpenMP.
Te zavisnosti nisu pronađene na očekivanim lokalnim Homebrew putanjama.
Ovo je bio početni statički nalaz. Build i inferencija su sada izvršeni; vidi
[FIREHOSE_VERIFICATION](FIREHOSE_VERIFICATION.md). Fizikalna validacija nije izvršena.

Firehose autori već demonstriraju reward za prioritetna područja
[na projektnoj stranici](https://williamshen-nz.github.io/firehose/).
Zato prioritetne zone same za sebe ne čine novi doprinos ovog projekta.

## TASK-004: gate, najviše 4 radna sata prije odluke

1. Izolovan Linux/Colab environment; zabilježiti OS, interpreter, commitove, build komandu
   i tačan contrib commit. Ne instalirati legacy zavisnosti u moderni `.venv`.
2. Kompajlirati Firehose binarni fajl bez zamjene originalnim upstream Cell2Fire.
3. Na 20×20: no-op i min/max-L2 rollout, prekid/cleanup, vrijeme 10 epizoda,
   kumulativna šteta i početno opažanje. Potvrditi da no-op zaista nastavlja simulaciju.
4. Propagirati simulator seed kao eksplicitni parametar u našem adapteru/patchu;
   isti seed + isti input moraju ponoviti izlaz, različiti seedovi moraju provjereno
   mijenjati stohastičku realizaciju. Hash ulaza i bilježiti izlazne kodove.
5. U izolovanom legacy runtimeu učitati provjereni 20×20 model i jedan masked inference.
   Dokumentovati tačan oblik/skaliranje opažanja i action masku.
6. Dokazati da novi budžet i no-op adapter čuvaju osnovni kontrakt težina.
   Uvođenje nove dimenzije opažanja/akcije zahtijeva eksplicitnu migraciju težina.

PASS: sve gore reprodukovano, nema tihih subprocess grešaka, simulator odvojen od
seedova agenta, i procjena glavne matrice staje u dogovoreni compute.
FAIL: zapisati log i preostalu prepreku, pa 2–4 sata SimFire spikea s no-op,
mitigation i provjerom seeda. Promjenu cilja s pretrained fine-tuninga na novo
pretreniranje jasno evidentirati; ne predstavljati to kao odobren profesorov dogovor.

## Ponovno preuzimanje

```sh
git clone https://github.com/aidan-curtis/firehose.git external/firehose
git -C external/firehose checkout e49a52a9a987a1585d25ddca2f711222ca500ffb
PYTHONPATH=src python3 -m wildfire_rl.checkpoint_audit external/firehose/pretrained_models/20x20-fixed-ppo-maskable.zip external/firehose/pretrained_models/20x20-random-20m-ppo-maskable.zip
```

Vanjski kod ostaje ignorisan. Licencu i porijeklo mapa provjeriti prije redistribucije.
Za poređenje kandidata: [Cell2Fire](https://github.com/cell2fire/Cell2Fire),
[C2F-W](https://github.com/fire2a/C2F-W), [SimFire](https://github.com/mitrefireline/simfire),
[SimHarness](https://github.com/mitrefireline/simharness).

## Dopuna nakon izvršavanja
Docker build i 12 inference slučajeva su prošli. Nemoj ponavljati ovaj početni statički
plan kao da runtime nije pokrenut. Detalji, ograničenja i konkretan naredni zadatak su u
[FIREHOSE_VERIFICATION](FIREHOSE_VERIFICATION.md); dataset u [DATASET](DATASET.md).
