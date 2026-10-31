---
type: Runbook
title: Izolovana Firehose provjera bez treniranja
---
# Izolovana Firehose provjera bez treniranja

Testirano na lokalnom Docker Desktopu, Linux ARM64. Legacy runtime nije projektni
Python >=3.11 paket: probe se izvršava kao zaseban fajl u Python 3.8 kontejneru.
Image sadrži originalni GPL Firehose izvor i checkpointove; ne objavljivati ga bez
provjere licenci za uključene podatke i modele.

## Izvori za čisti checkout

```sh
git clone https://github.com/aidan-curtis/firehose.git external/firehose
git -C external/firehose checkout e49a52a9a987a1585d25ddca2f711222ca500ffb
git clone https://github.com/williamshen-nz/stable-baselines3-contrib.git external/sb3-contrib-legacy
git -C external/sb3-contrib-legacy checkout 43b7fe6fcdda71c2c10de7af0d20f39e48ae5df3
```

Za postojeći sparse checkout Firehose moraju biti uključeni `cell2fire/Cell2FireC`,
`cell2fire/firehose`, `cell2fire/utils`, `data/Sub20x20` i dva 20×20 model ZIP-a.
Raw izvori i težine ostaju u ignorisanom external/ direktoriju.

Docker build redom primjenjuje lokalne patch-eve
[`cfsds_initial_state.patch`](cfsds_initial_state.patch) i
[`task004c_state_export.patch`](task004c_state_export.patch) na pinovani upstream izvor.
Opcioni `InitialState.csv` koristi `state,ncell`, a `ncell` je one-based row-major ID:

- `burnt`: historijski scar na gorivoj ćeliji;
- `burning`: aktivni front na gorivoj ćeliji;
- `scar_nf`: historijski scar na ćeliji čija je tačna simulator klasa `NF`.

`scar_nf` je eksplicitna tvrdnja konvertera o porijeklu ćelije, a ne automatsko
zaključivanje iz klase goriva. Dozvoljen je samo za `NF`; `ND`, Water, harvested ćelije,
gorive ćelije i aktivni front ga ne mogu koristiti. Obični `burnt` na `NF` i `burning`
na bilo kojoj ne-gorivoj ćeliji ostaju odbijeni. Pri importu `scar_nf` ulazi u C++
kumulativni `burntCells` i Python episode `ever_affected` skup, pojavljuje se kao scar u
gridu, ali ne ulazi u `burningCells` ili skup raspoloživih ćelija. Fuel mapa ostaje
nepromijenjena. Kada `InitialState.csv` ne postoji, postojeći Firehose slučajevi zadržavaju
dosadašnju logiku i izgled opažanja.

Konverter smije emitovati `scar_nf` tek kad odvojeni izvorni audit potvrdi i historijski
požar tog piksela i da je `NF` nastao iz documented post-fire succession. Sama oznaka
CFSDS scar plus generička `NF` vrijednost nije dovoljna da razlikuje burn scar od Water,
Urban, no-data ili pogrešnog overlay-a. Case builder trenutno i dalje odbija sve početne
scar/front ćelije na non-fuel/water; godišnja fuel mapa i stvarni CFSDS FireCase ostaju
blokirani na vremenskom porijeklu i succession pravilima.

TASK-004c čuva RGB 20×20/400-akcijski i reward/checkpoint ugovor. Za standardne
Firehose mape grid koristi stari kod 1 za aktivno/opožareno kako postojeći modeli
i heuristike ostanu kompatibilni. Samo kad se uveze `InitialState.csv`, grid kodovi
su: 0 neizgorjelo, 1 stariji ožiljak, 2 aktivni front i -1 tretirana ćelija.
`FireEnv.step()` vraća u `info` kumulativno pogođene ID-jeve, aktivne ID-jeve i
`termination_reason`; svi navedeni `ncell` ID-jevi su one-based row-major, a akcije
agenta i dalje ostaju zero-based.

Kad C++ završi, ispisuje jedan `FIREHOSE_TERMINAL_STATE` JSON red sa zajedničkim
stanjima i razlogom: `weather_horizon`, `front_extinguished`, `grid_exhausted` ili
`no_ignition`. Na vremenskom limitu terminalni aktivni rub se sačuva prije nego ga
Cell2Fire prebaci u završni burnt set. Terminalni C++ spisak je izvor kumulativne
štete; Python `FireEnv` ga kopira u trajni episode counter. Categorical grid daje
prednost tretiranju (`-1`), pa cell koja je u istoj simulacijskoj etapi pogođena i
tretirana može nestati iz pozitivnih grid vrijednosti. Probe zato provjerava da su
sve pozitivne grid ćelije u terminalnom skupu, a svaka razlika mora pripadati i
terminalnom skupu tretiranih ćelija. Neobjašnjeno neslaganje ili neklasifikovan
završetak ruši smoke. Probe timeout, adapter step limit i subprocess greška imaju
odvojene razloge i ne predstavljaju fizičko gašenje požara.

## Build i provjera

Iz korijena projekta:

```sh
docker build --file docker/firehose/Dockerfile --tag wildfire-firehose-probe:task004c .
mkdir -p runs/firehose-new-check
docker run --rm --network none --cpus 2 --memory 2g --pids-limit 128 --read-only   --tmpfs /tmp:rw,nosuid,size=256m --tmpfs /opt/firehose/input:rw,nosuid,size=128m   --cap-drop ALL --security-opt no-new-privileges -e MPLCONFIGDIR=/tmp/mpl   -v "$PWD/runs/firehose-new-check:/outputs"   wildfire-firehose-probe:task004c timeout 300 python /opt/firehose_verify_batch.py
```

Folder `/outputs/final` mora biti nov. 12 kratkih rollouta ima pojedinačni limit 90 s;
ukupan command cap je 300 s. Nema `learn()` poziva. Raw gridovi i logovi su lokalni,
a mali JSON sažeci i manifesti idu u Git. Runtime nema mrežu i vidi samo output mount.
Build ima mrežu za zvanične Debian/PyPI zavisnosti; `.dockerignore` isključuje privatne
fajlove i moderni .venv iz build contexta.

Za jedan model:

```sh
docker run --rm --network none --cpus 2 --memory 2g --read-only   --tmpfs /tmp:rw,nosuid,size=256m --tmpfs /opt/firehose/input:rw,nosuid,size=128m   -e MPLCONFIGDIR=/tmp/mpl -v "$PWD/runs/firehose-new-check:/outputs"   wildfire-firehose-probe:task004c timeout 100 python /opt/firehose_probe.py   --policy ppo-fixed --seed 123 --budget 8 --sync-reset --out /outputs/one-model
```

## Početni historijski front

Ovaj kratki inference-only check provjerava import jedne stare opožarene ćelije i
dva aktivna fronta. Pokreće se unutar imagea, nakon Docker builda:

```sh
mkdir -p runs/initial-state-check
docker run --rm --network none --cpus 2 --memory 2g --pids-limit 128 --read-only \
  --tmpfs /tmp:rw,nosuid,size=256m --tmpfs /opt/firehose/input:rw,nosuid,size=128m \
  --cap-drop ALL --security-opt no-new-privileges -e MPLCONFIGDIR=/tmp/mpl \
  -v "$PWD/runs/initial-state-check:/outputs" \
  wildfire-firehose-probe:task004c python /opt/firehose_verify_initial_state.py
```

Provjeravač učitava malu fixturesku mapu: 1 ranije izgorjela ćelija i 2 aktivne
ćelije ruba. Bez RL modela i bez intervencija provjerava da C++ prijavi isto stanje,
da se Python početna slika poklapa s C++ gridom i da se proces uredno završi.
Fixture potvrđuje sam C++ import sa minimalnom mapom, ne stvarnu požarnu fiziku.
Dodatno je pokrenut pravi CFSDS slučaj `2018_747`: 175 ranije izgorjelih ćelija i 31
aktivna ćelija na frontu. Šest no-action C++ ponavljanja, bez treninga i intervencija,
dalo je istu završnu mapu: 66 ha prema 15.39 ha opaženih; svih šest dotaklo je rub
modelskog prozora. To je mismatch dijagnostika, ne fizička validacija. Vidi [case
manifest](../../reports/real-fire-data/2018_747-case.json), [replay report](../../reports/real-fire-data/2018_747-day228-replay.json),
[seed ponavljanja](../../reports/real-fire-data/2018_747-seed-sweep.json) i
[mapu](../../reports/real-fire-data/2018_747-day228.png). Fixture sažetak,
Docker image ID i hashovi su u
[`initial-state-import-smoke.json`](../../reports/real-fire-data/initial-state-import-smoke.json).

### Historijski scar na non-fuel ćeliji

Fixture [`nonfuel_initial_scar_fixture.csv`](nonfuel_initial_scar_fixture.csv) izričito
označava `ncell=4` kao `scar_nf`; ćelija 4 je `NF` u standardnoj Sub20 mapi, a ćelija 1
je gorivi aktivni front. Provjeravač pokreće kratku no-action epizodu do terminalnog
vremenskog horizonta i potvrđuje da `ncell=4` ostaje u C++ terminalnom i Python cumulative
damage skupu i u gridovima, ali se ne pojavi u aktivnom frontu ni u jednom koraku. Tri
nevaljana slučaja ostaju odbijena: neoznačeni `burnt` na NF, `burning` na NF i `scar_nf`
na gorivoj ćeliji. Raniji expected-rejection run je sačuvan kao historijski zapis u
[`nonfuel-initial-scar-compatibility.json`](../../reports/firehose-verification/nonfuel-initial-scar-compatibility.json);
novi ugovor ima zaseban receipt
[`nonfuel-initial-scar-contract.json`](../../reports/firehose-verification/nonfuel-initial-scar-contract.json).

Ovo je mali importer/state smoke na sintetičkoj Sub20 mapi, ne fizikalna validacija ni
potvrda da je neki CFSDS `NF` cell zaista post-fire scar. Operativni CFSDS converter i
dalje odbija početni scar/front na non-fuelu dok source vintage i succession lineage
nisu dokazani.

Nakon što su pinovani upstream checkouti dostupni, rebuildaj image i pokreni kratku
izolovanu provjeru (za svaki ponovljeni run izaberi novi output folder):

```sh
docker build --file docker/firehose/Dockerfile --tag wildfire-firehose-probe:task015-nonfuel-scar-contract .
mkdir -p runs/nonfuel-initial-scar-check-new
docker run --rm --network none --cpus 2 --memory 2g --pids-limit 128 --read-only \
  --tmpfs /tmp:rw,nosuid,size=256m --tmpfs /opt/firehose/input:rw,nosuid,size=128m \
  --cap-drop ALL --security-opt no-new-privileges -e MPLCONFIGDIR=/tmp/mpl \
  -v "$PWD/runs/nonfuel-initial-scar-check-new:/outputs" \
  wildfire-firehose-probe:task015-nonfuel-scar-contract python /opt/firehose_verify_nonfuel_initial_scar.py
```

Očekivani rezultat je `PASS_EXPLICIT_NF_SCAR_IMPORT_CONTRACT`; verzionisani receipt sa
fixture, patch i image hashovima je
[`nonfuel-initial-scar-contract.json`](../../reports/firehose-verification/nonfuel-initial-scar-contract.json).
Ne koristi se trening, policy niti CFSDS validation/test slučaj. Runtime prolaz potvrđuje
import/state invariant, ne fizičko ponašanje požara.

TASK-004c adapter je implementiran i provjeren fixtureom plus 12 kratkih Sub20 inference
rollouta; mašinski sažetak i image ID su u
[`task004c-adapter-smoke.json`](../../reports/firehose-verification/task004c-adapter-smoke.json).
Test potvrđuje tehničko poravnanje terminalnog C++ kumulativnog skupa i Python brojača,
uz posebno objašnjenje ćelija koje su skrivene oznakom tretiranja. Ne provjerava fiziku
požara niti zatvara CFSDS no-action gate. `--sync-reset` ostaje opcionalna dijagnostika
za poređenje reset varijanti; FireEnv sada resetuje warmup observation prema C++ gridu.
Sljedeće je dovršiti train-only fuel-vintage/terrain/weather/suppression QC i tek zatim
odlučiti o dodatnim kontrolisanim replayima.
Za drugu arhitekturu/OS potrebno je zasebno provjeriti build i wheel dostupnost;
postojeći freeze nije obećanje x86/GPU/Colab kompatibilnosti.
