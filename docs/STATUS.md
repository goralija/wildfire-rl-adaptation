---
type: Project Status
title: Trenutno stanje — 2026-10-30
sources:
- resource: /reports/firehose-verification/verification.json
- resource: /docs/WORK_LOG.md
---
# Trenutno stanje — 2026-10-30

## Baza znanja u repozitoriju
Repo je OKF 0.2 bundle s [root indeksom](../index.md),
[sažetim kontekstom](../knowledge/project-context.md), [mapom koda](../knowledge/code-map.md)
i [pravilima održavanja](../knowledge/maintenance.md). Dokumenti imaju tipove,
lowercase indekse i navigaciju; agent ulazi dijele isti AGENTS kontekst. Zaseban
knowledge checker/CI čuva strukturu i lokalne linkove. Migracija ne zatvara dataset
refinement niti uvodi naučnu/humanu verifikaciju sadržaja.
Provjera: [63 Markdown fajla, 15 knowledge testova i clean-clone dokaz](../reports/knowledge-validation.json).
Osnovni aplikacijski paket i dalje nema dodatne zavisnosti; PyYAML je samo knowledge alat.

## Lokalni workspace
Trenutni projektni checkout je repo root na grani `feature/project-bootstrap`, koja
odgovara `origin/feature/project-bootstrap` na commitu `1499890`. `main` je i dalje na
početnom commitu; feature grana nije spojena. U ovom workspaceu nema zasebnog nested
`.worktrees/project-bootstrap/` checkouta: aktivna grana je na root putanji. Runbook za
čiste klonove i lokalno ignorisane artefakte je u
[workspace layout dokumentu](../knowledge/workspace-layout.md).
[Provjera preseljenja](../reports/workspace-relocation.json): 13,246 ne-venv fajlova
i 11 backup fajlova sa istim hashovima, 19 sačuvanih verzija paketa, ispravljene
lokalne venv putanje, 26 aplikacijskih/15 knowledge testova i 64-file OKF provjera.

## Najnoviji pomak
**Cell2Fire je kompajliran i oba postojeća 20×20 Firehose PPO checkpointa rade.**
Izvršeno je 12 kratkih inference rollouta, bez treniranja, u odvojenom Linux ARM64
kontejneru sa SB3/contrib 1.5.0 i Gym 0.21.0. Runtime gate je prošao.

- Isti input/seed ponavlja kompletan niz akcija/state hashova; drugačiji C++ seed mijenja širenje.
- Budžet B=8 se poštuje; zatim no-op do simulator done. Težine ostaju nepromijenjene.
- Svi subprocess returncodeovi su 0. Kontrole: no-action, min-L2, max-L2 i dva checkpointa.
- Zabilježen input hash, izvorni commitovi, model hashovi, verzije i Docker image ID.
- Dataset card: 141 fajl, 400 ćelija (307 gorivih), 130 weather fajlova sa po 8 redova.

## Izabrani real-fire podaci i stvarni pilot — 2026-10-30

Odabrana je **Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire** jer najbolje odgovara
postojećem simulatoru i 20×20 agentu. CFSDS v1.1 ima 5,435 kanadskih požara za
2002–2024, 90 m satelitski interpolisanu dnevnu kartu gorenja. Službeni CFSDS rad
opisuje MODIS/VIIRS hot-spot interpolaciju; noviji W.I.S.E. rad ponavlja da je za
kompatibilan no-action benchmark potrebno znatno strože birati događaje. [CFSDS rad](https://doi.org/10.1038/s41597-024-03436-4), [W.I.S.E. procjena](https://doi.org/10.1071/WF26072).

Preuzeto je 23 godišnja ZIP para 2002–2024 (102,405,239 bajtova ukupno) lokalno u
Git-ignorisan `data/raw/cfsds-v1_1`; datoteke su provjerene prema OSF manifestu. Prvi
screen za godine 2014–2024 pregledao je 3,141 događaj/82,015 dnevnih redova i
zadržao najviše pet geometrijski pogodnih događaja po godini: ukupno 44, podijeljena
po godini požara u 20 train, 9 validation i 15 test kandidata. Ovaj spisak nije
iscrpan niti pun benchmark; svi dani jednog požara ostaju u istoj particiji.
[Screen izvještaj](../reports/real-fire-data/cfsds-cohort-screen.json),
[kohort manifest](../data/manifests/cfsds-v1_1-pilot-cohort.json).

**Prvi simulator slučaj `2018_747`, target 16.08.2018:** napravljena je 20×20 × 100 m
karta s Canadian FBP 2014b gorivima, MRDEM 30 m terenom, ERA5-Seamless satnim vremenom,
prethodnim požarnim stanjem i zasebnim targetom za naredni dan. Sve ćelije u scar/front
/target su na podržanom C-3 ili D-1 gorivu. C++ je prihvatio 175 ranije opožarenih i
31 aktivnu ćeliju. Šest no-action seedova (123–128; bez treniranja/intervencija) završilo
je uspješno. Svih šest dalo je istu mapu od 66 ha prema CFSDS cilju 15.39 ha (IoU 0.2187),
a novo širenje dodirnulo je 19 rubnih ćelija našeg 2×2 km isječka. Trajanje runova se
razlikovalo. Dakle konverzija radi, ali
ovaj replay pokazuje veliko neslaganje i rubni efekat; ne validira fiziku niti dokazuje
korist agenta. [Replay mjere](../reports/real-fire-data/2018_747-day228-replay.json),
[mapa](../reports/real-fire-data/2018_747-day228.png).

**Dodatne train provjere, bez treniranja:** `2018_241` i `2018_1770` su pretvoreni i
pokrenuti od historijskog stanja bez početnog zagrijavanja. Bez gašenja je simulator u
prvom slučaju zahvatio svih 400 ćelija: 237 ha novog gorenja prema 12.15 ha opaženih
(IoU 0.0376). U drugom je dodao 73 ha prema 12.15 ha (IoU 0.1361). `2018_241` je dao
iste mjere i kad uključimo 20 minuta zagrijavanja, pa to zagrijavanje nije glavni uzrok
neslaganja. Kandidat `2014_538` nije prošao konverziju jer dio historijskog scar/fronta
upada na vodu ili ne-gorivo u FBP 2014b karti. Ovi nalazi potvrđuju da geometrijski
odabrani kandidati još nisu provjereni slučajevi. [2018_241 mjere](../reports/real-fire-data/2018_241-day227-replay.json),
[2018_1770 mjere](../reports/real-fire-data/2018_1770-day224-replay.json),
[odbijeni `2014_538`](../reports/real-fire-data/2014_538-fuel-rejection.json).

Nakon izmjene probe opcije i C++ initial-state podrške, novi isolated Docker image je
ponovo prošao svih 12 kratkih postojećih Sub20 inference slučajeva; PPO težine su ostale
iste. Sažetak: [regression receipt](../reports/firehose-verification/real-case-image-regression.json).

CFSDS target je dnevna satelitska procjena, ne tačan satni ground-truth front; suppression
status nije spojen. FBP karta je 250 m resamplovana na 100 m, DEM 30 m, a vrijeme je
reanalysis tačka 5.2 km od centra. Dnevni FWI kodovi su ponavljani kroz 24 sata zbog
nedostatka satnih vrijednosti u CFSDS. Za heldout 2019/2022–24 još treba odgovarajuće
fuel-map vintages (2019/2024) i kvalitetni inputi. BiH/MedEU ostaje kasnija odvojena
studija jer njegovi evropski NFFL fuel kodovi nisu isti kao Canadian FBP.

Sljedeći posao: sistemski provjeriti gorivo, vrijeme, FBP parametre i veličinu domene na
train slučajevima, pa utvrditi postoji li konfiguracija Cell2Fire koja prođe no-action
gate bez podešavanja na validation/test ciljevima. Preostaje TASK-004c terminal/damage
export; multi-cell
initial-state import (TASK-017) i tri train FireCase konverzije/no-action replaya (TASK-016)
su ostvareni. Glavno treniranje je na čekanju dok no-action gate ne bude prihvatljiv
na više train slučajeva; test skup se ne koristi za kalibraciju.

## Environment reproducibility — 2026-10-30

U feature checkoutu je napravljen moderni Python 3.12.4 `.venv` s optional RL, GIS i
knowledge alatima. Geospatial stack je izolovan: rasterio 1.4.4, geopandas 1.2.0,
pyproj 3.8.0, xarray/rioxarray, netCDF4, SciPy, CDS API klijent i ostale zavisnosti;
GeoTIFF nearest-neighbour reprojection/import smoke je prošao. Kombinovani freeze je
`requirements/research-macos-arm64-py312.freeze.txt`. Prošlo je 26 aplikacijskih testova, 15 knowledge testova, strogi checker za
67 Markdown fajlova, synthetic CLI smoke i 1,024-koračni synthetic PPO
smoke. Legacy Firehose image je svježe izgrađen na Linux ARM64 iz pinovanih upstream
commitova; 12/12 inference slučajeva su prošli, sa ugašenom mrežom i bez treninga.
Tačne verzije i image/source hashovi su u [environment receipt](../reports/environment-setup/README.md).
Ovaj setup ostavlja known adapter mismatch aktivnim; environment PASS nije research-ready.

Dogrib gorivo/elevation dijele blok sa Sub20 mapom, pa nije nezavisan test prostorne
generalizacije. MedEU je zaseban mogući evropski track, ali nije potreban za glavni
Canadian FBP projekat i još nije pretvoren u simulator input.

## Ograničenja koja su stvarno potvrđena
Legacy fixed-model reset i brojač za početni Sub20 warmup i dalje imaju poznatu razliku
(206 naspram 207); eksplicitni sync reset je daje 207/207. Stvarni CFSDS pilot koristi
poseban multi-cell importer i provjerava početni C++ grid. Preostali TASK-004c treba da
izveze kumulativnu štetu i jasan terminalni razlog za online RL adapter. Simulatorov
`done` ne razlikuje containment od vremenskog horizonta; zato **research_ready=false**.

## Ostalo što radi
Baza zahtjeva/rubrike/literature/odluka, synthetic-v1 engine i pet baseline politika,
upareni eksperimenti i manifesti, 300-epizodni sintetički replay, moderni Gym/PPO smoke.
Prethodni sintetički artefakti ostaju historijski dokaz; nisu Cell2Fire rezultati.

## Dokazi
- [Runtime nalazi](research/FIREHOSE_VERIFICATION.md), [dataset](research/DATASET.md).
- `reports/firehose-verification/`: input inventar, 12 rezultata, summary, checks, environment.
- 26 testova prolazi s modernim optional environmentom; 22 core + 4 optional RL testa.
- Originalni Firehose i contrib checkouti ostaju neizmijenjeni; samo build flagovi i
  eksplicitna dijagnostika reset/seed ponašanja su dodani u naš kod.
- Docker/legacy i moderni .venv su odvojeni. Legacy inference je bez treniranja i
  plaćenog compute-a. Kod/dokumentacija su objavljeni kroz [PR #1](https://github.com/goralija/wildfire-rl-adaptation/pull/1).

Sljedeće: pilot replay review i fuel/terrain/weather/domain dijagnostika → nekoliko
train-only no-action replaya → FBP fuel vintages za heldout godine + suppression/QC
spajanje → zamrzavanje event testa → preostali TASK-004c adapter → upareni benchmark /
treniranje samo nakon prolaza replay gatea.
Nema provjere fizike simulatora na BiH podacima, potvrde RL prednosti ili generalizacije.
Deadline/compute i licence za sirove podatke ostaju otvoreni.

## Pregled i odgođena sitnica
I bootstrap i novi runtime pregled su prošli bez kritičnih ili važnih nalaza.
Novi pregled nezavisno potvrđuje testove, evidence/provenance i dataset hashove.
Jedan stari minor ostaje TASK-010:
JSON null config u synthetic CLI-u daje traceback umjesto uredne poruke.

## Handoff za kolegu
[HANDOFF](../HANDOFF.md) sadrži prenosiv clone/setup, put do legacy runtimea,
pribavljanje lokalnih podataka i trenutno stanje replaya.
Za objavu ponovo prolazi svih 26 testova u modernom environmentu. Čisti lokalni
Git klon s novim venvom i bez dodatnih paketa prolazi 22 testa (4 optional preskočena)
i synthetic smoke; originalni lokalni setup nije preduslov za taj početak.
Korisnik je odobrio objavu cijele feature grane i PR prema početnom mainu; ADR-008.
