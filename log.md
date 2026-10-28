# Promjene baze znanja

## 2026-10-28: Workspace raspored

- [Runbook](knowledge/workspace-layout.md) definiše mpvi glavni klon, .worktrees i ignorisani .local prostor, uz očuvanje PR-a i dataset prioriteta.
- [Dokaz preseljenja](reports/workspace-relocation.json) čuva hash/package/test provjere i ponovljeni setup iz novog klona.

## 2026-10-28: OKF 0.2 bundle u repozitoriju

- Dodani typed koncepti, lowercase indeksi, [kontekst](knowledge/project-context.md), [mapa koda](knowledge/code-map.md) i [održavanje](knowledge/maintenance.md).
- Root [index](index.md) i [AGENTS](AGENTS.md) vode do izvora i dokaza bez vanjske baze/chat historije; mali agent ulazi dijele ista pravila.
- [OKF profil](knowledge/okf-format.md) pinova specifikaciju; zaseban checker/CI provjerava strukturu i projektne linkove, bez tvrdnje o naučnoj verifikaciji.
- [Završni receipt](reports/knowledge-validation.json) čuva 63-file provjeru, 15 knowledge testova, clean-clone rezultate i hashove; pregled i regresijske ispravke su u [REVIEW](docs/REVIEW.md).

## 2026-10-28: Dataset refinement ostaje otvoren

- Korisnik je ispravio redoslijed: [TASK-012](docs/BACKLOG.md) je prvi projektni korak, izbor i obim još nisu usaglašeni; ADR-009.
- Handoff i PR usklađeni; postojeći runtime nalazi ostaju važeći.

## 2026-10-28: Bootstrap, runtime i pregled izvora

- Sačuvani [pilot](reports/pilot/README.md), [Firehose dokazi](reports/firehose-verification/README.md) i [Dogrib/CFSDS profili](reports/real-fire-data/README.md).
- Detaljan redoslijed, komande, rulings i pregledi su u [WORK_LOG](docs/WORK_LOG.md) i [REVIEW](docs/REVIEW.md).
