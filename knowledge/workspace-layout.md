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
    project-bootstrap/         feature/project-bootstrap, otvoreni PR #1
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

## Dok PR #1 nije spojen

Remote/local main još imaju samo početni commit. Zato je projektni sadržaj trenutno
u `.worktrees/project-bootstrap/`; to je očekivano i ne znači da je projekt izgubljen.
Selidba foldera ne mergea PR. Nakon odobrenog mergea glavni main može preuzeti sadržaj
standardnim `git pull --ff-only` postupkom.

Dok je main prazan, lokalni `.git/info/exclude` štiti `.worktrees/` i `.local/` na
glavnom checkoutu. Verziona politika istih foldera je u feature `.gitignore` i dolazi
na main zajedno s PR-om. Na ovom računaru privremeni ignorisani root `AGENTS.md`
samo upućuje na kanonski AGENTS/index u PR worktreeu; nije druga baza znanja.

## Novi klon i nastavak

Prenosive komande su u [HANDOFF](../HANDOFF.md). Za novi zadatak prvo pročitaj
[AGENTS](../AGENTS.md), provjeri postojeće worktree-e i odaberi ispravnu baznu granu:
dok PR nije spojen, njegova grana sadrži projektni kod; kasnije to postaje main.
Prije kreiranja provjeri da Git ignoriše odredišni `.worktrees/` folder.

Za stvarno preseljenje koristi `git worktree move`; pri pomjeranju glavnog klona
Git podržava `git worktree repair` za ponovno povezivanje checkouta. Python venv
može sadržavati apsolutne putanje, pa nakon selidbe treba obnoviti ili provjeriti
entrypoint-e i editable instalaciju. To nije tvrdnja da je venv prenosiv između OS-ova.
Provjeri status/refs, hashove podataka/modela, aplikacijske testove, smoke i OKF checker.
