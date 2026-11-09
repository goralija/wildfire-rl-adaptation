---
type: Playbook
title: Glavni klon, worktree-i i lokalni artefakti
description: Raspored mpvi foldera, siguran rad u .worktrees i ignorisani .local prostor.
sources:
  - resource: /AGENTS.md
  - resource: /.gitignore
  - resource: https://git-scm.com/docs/git-worktree
---
# Workspace raspored

```text
mpvi/                          glavni Git klon i koordinacija (main)
  .git/                        zajednička Git historija i refs
  .worktrees/
    <task>/                    jedan worktree po zadatku/grani (npr. ispravke TASK-021–024)
  .local/                      lokalno, ne objavljuje se u Git
    backups/                   sačuvani bundle-i i lokalne kopije
    scratch/                   radni CSV-ovi, testni grafovi i privremene analize
```

`mpvi` je naziv lokalnog klona, ne dodatni folder oko `repository/`. Svaki worktree
ima svoj checkout i granu, uz zajedničku Git bazu. Postojeći PR worktree se preselio,
sa svojim ignorisanim podacima/okruženjem; nije ponovo kreiran iz praznog checkouta.

## Gdje raditi

- Glavni klon služi koordinaciji i ažuriranju maina. Implementacija ide u postojeći
  odgovarajući ili novi task worktree pod glavnim `.worktrees/` folderom.
- Na glavnom klonu pokreni `git worktree list` i otvori odgovarajuću putanju.
  Ne prebacuj granu glavnog klona radi feature rada.
- `.local/` može postojati u glavnom klonu za zajedničke lokalne artefakte i u
  pojedinačnom worktreeu za njegove privremene fajlove. Oba su ignorisana.
- Postojeći `runs/`, `artifacts/`, `data/raw/`, `external/`, `.venv/` i `private/`
  ostaju ignorisani prema svojoj namjeni. Male provjerene rezultate i provenance
  potrebne kolegi prebaci u `reports/`/manifeste, uz provjeru licence/privatnosti.
- `.local` i `.worktrees` nisu backup sami po sebi. Ne koristiti `git clean -fdx`
  nad njima: takva komanda briše ignorisani rad.

## Stanje nakon spajanja PR-ova #1–#5 (2026-11-09)

PR #1 (bootstrap) i PR-ovi #3–#5 (SimFire/FEDS i sintetički CA) su spojeni u `main`
merge commitima; njihove grane su sačuvane na remoteu kao historija. Glavni klon na `main`
sada sadrži cijeli projekat i kanonski [AGENTS](../AGENTS.md); privremeni ignorisani
root pointer više nije potreban. Novi rad počinje iz ažuriranog `main`
(`git pull --ff-only` na glavnom klonu), u novom worktreeu pod `.worktrees/`.
Stariji worktree-i (`project-bootstrap`, `overnight-steps-5-8`, `synthetic-ca-training`)
ostaju dok njihovi vlasnici ne sačuvaju lokalne, nepraćene fajlove; ne brisati ih
automatski.

## Novi klon i nastavak

Prenosive komande su u [HANDOFF](../HANDOFF.md). Za novi zadatak prvo pročitaj
[AGENTS](../AGENTS.md), provjeri postojeće worktree-e i odaberi ispravnu baznu granu:
projektni kod je na `main`, pa nova grana kreće iz ažuriranog `main`.
Prije kreiranja provjeri da Git ignoriše odredišni `.worktrees/` folder.

Za stvarno preseljenje koristi `git worktree move`; pri pomjeranju glavnog klona
Git podržava `git worktree repair` za ponovno povezivanje checkouta. Python venv
može sadržavati apsolutne putanje, pa nakon selidbe treba obnoviti ili provjeriti
entrypoint-e i editable instalaciju. To nije tvrdnja da je venv prenosiv između OS-ova.
Provjeri status/refs, hashove podataka/modela, aplikacijske testove, smoke i OKF checker.
