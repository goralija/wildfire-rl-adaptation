# Trenutno stanje — 2026-10-28

## Najnoviji pomak
**Cell2Fire je kompajliran i oba postojeća 20×20 Firehose PPO checkpointa rade.**
Izvršeno je 12 kratkih inference rollouta, bez treniranja, u odvojenom Linux ARM64
kontejneru sa SB3/contrib 1.5.0 i Gym 0.21.0. Runtime gate je prošao.

- Isti input/seed ponavlja kompletan niz akcija/state hashova; drugačiji C++ seed mijenja širenje.
- Budžet B=8 se poštuje; zatim no-op do simulator done. Težine ostaju nepromijenjene.
- Svi subprocess returncodeovi su 0. Kontrole: no-action, min-L2, max-L2 i dva checkpointa.
- Zabilježen input hash, izvorni commitovi, model hashovi, verzije i Docker image ID.
- Dataset card: 141 fajl, 400 ćelija (307 gorivih), 130 weather fajlova sa po 8 redova.

## Novi nalazi o stvarnim požarima
Preuzeti su mali historijski uzorci Dogrib/CFSDS, ukupno 3.68 MB; hashovi i offline
provjera su sačuvani. [Preporuka](research/REAL_FIRE_DATASETS.md): Dogrib kao prvi
historijski slučaj za simulator, mali CFSDS podskup za kasniju nezavisnu provjeru.
Stvarni podaci nisu strogi preduslov za osnovno RL poređenje; kvalitet ulaza i granice
zaključaka moraju biti jasni. Fizika simulatora na ovim uzorcima još nije validirana.

Dogrib gorivo/elevation dijele blok sa Sub20 mapom, pa nije nezavisan test prostorne
generalizacije. Sub20 origin ne odgovara tom izrezu. CFSDS uzorak ima 38 rastera i
372 dnevna reda; treba dopunu FBP mapa i vremena za Cell2Fire. TASK-011 čuva tačan obim.

## Ograničenja koja su stvarno potvrđena
Početni upstream reset vraća prazno stanje iako warmup ima 7 pogođenih ćelija.
U fixed-model provjeri brojač je 206 umjesto 207 iz grid historije; eksplicitna
sync-reset provjera daje 207/207. C++ grid vrijednost 1 spaja aktivno i ranije gorjelo;
done ne razlikuje containment od weather horizonta. Zato **research_ready=false**.
Task-004c treba formalni adapter i terminalni C++ export prije glavne evaluacije.

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
- Docker/legacy i moderni .venv su odvojeni. Nema treninga, remote push-a ili plaćenog compute-a.

Glavni sljedeći korak: TASK-004c, zatim freeze scenarija, frozen benchmark i tek fine-tuning.
Nema provjere fizike simulatora na BiH podacima, potvrde RL prednosti ili generalizacije.
Deadline/compute i licence za sirove podatke ostaju otvoreni.

## Pregled i odgođena sitnica
I bootstrap i novi runtime pregled su prošli bez kritičnih ili važnih nalaza.
Novi pregled nezavisno potvrđuje testove, evidence/provenance i dataset hashove.
Jedan stari minor ostaje TASK-010:
JSON null config u synthetic CLI-u daje traceback umjesto uredne poruke.

## Handoff za kolegu
[HANDOFF](../HANDOFF.md) sadrži prenosiv clone/setup, put do legacy runtimea,
pribavljanje ignorisanih podataka i prvi zadatak s kriterijima prihvata.
Za objavu ponovo prolazi svih 26 testova u modernom environmentu. Čisti lokalni
Git klon s novim venvom i bez dodatnih paketa prolazi 22 testa (4 optional preskočena)
i synthetic smoke; originalni lokalni setup nije preduslov za taj početak.
Korisnik je odobrio objavu cijele feature grane i PR prema početnom mainu; ADR-008.
