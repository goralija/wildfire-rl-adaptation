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

## Build i provjera

Iz korijena projekta:

```sh
docker build --file docker/firehose/Dockerfile --tag wildfire-firehose-probe:20261028 .
mkdir -p runs/firehose-new-check
docker run --rm --network none --cpus 2 --memory 2g --pids-limit 128 --read-only   --tmpfs /tmp:rw,nosuid,size=256m --tmpfs /opt/firehose/input:rw,nosuid,size=128m   --cap-drop ALL --security-opt no-new-privileges -e MPLCONFIGDIR=/tmp/mpl   -v "$PWD/runs/firehose-new-check:/outputs"   wildfire-firehose-probe:20261028 timeout 300 python /opt/firehose_verify_batch.py
```

Folder `/outputs/final` mora biti nov. 12 kratkih rollouta ima pojedinačni limit 90 s;
ukupan command cap je 300 s. Nema `learn()` poziva. Raw gridovi i logovi su lokalni,
a mali JSON sažeci i manifesti idu u Git. Runtime nema mrežu i vidi samo output mount.
Build ima mrežu za zvanične Debian/PyPI zavisnosti; `.dockerignore` isključuje privatne
fajlove i moderni .venv iz build contexta.

Za jedan model:

```sh
docker run --rm --network none --cpus 2 --memory 2g --read-only   --tmpfs /tmp:rw,nosuid,size=256m --tmpfs /opt/firehose/input:rw,nosuid,size=128m   -e MPLCONFIGDIR=/tmp/mpl -v "$PWD/runs/firehose-new-check:/outputs"   wildfire-firehose-probe:20261028 timeout 100 python /opt/firehose_probe.py   --policy ppo-fixed --seed 123 --budget 8 --sync-reset --out /outputs/one-model
```

Originalno prvo opažanje se čuva bez `--sync-reset`; ta opcija je eksplicitna korekcija
warmup opažanja/brojača za dijagnostiku. Nova istraživačka integracija tek slijedi.
Za drugu arhitekturu/OS potrebno je zasebno provjeriti build i wheel dostupnost;
postojeći freeze nije obećanje x86/GPU/Colab kompatibilnosti.
