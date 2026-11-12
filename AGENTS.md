---
type: Agent Instructions
title: Rad na projektu
---
# Rad na projektu

Repo je OKF 0.2 knowledge bundle. Na početku sesije pročitaj [index.md](index.md),
[projektni kontekst](knowledge/project-context.md), [STATUS](docs/STATUS.md),
[NEXT_SESSION](docs/NEXT_SESSION.md) i najnovije [odluke](docs/specs/DECISION_RECORDS.md).
Zatim koristi [mapu zadataka/koda](knowledge/code-map.md) za relevantne izvore i testove.
Korisnikove direktne upute imaju prednost; kasniji ADR može zamijeniti raniji.

**Aktivno stanje je ADR-029 (2026-11-09): rezultati ADR-022–028 su nevažeći dok se ne
ponove.** gridMET uzorkovanje je davalo svim požarima jedne godine vrijeme prvog požara
(ispravljeno). PR-ovi #3–#5 (SimFire/FEDS gate, koraci 5–8, sintetički CA) su u `main`
kao historija; njihovi brojevi se ne citiraju kao nalazi. Ispravke TASK-021–024 su
spojene; odluke su u ADR-030 i dopunama. TASK-027 je spojen (PR #15: 98 TRAIN, FEDS `t` kao
lokalni prolaz, novi gridMET fajl). Faze 1 i 2 ponovnog pokretanja (TASK-026) agent smije
pokrenuti sam, fazu 2 samo ako faza 1 prođe; merge i faza 3 ostaju korisnikovi (dopuna ADR-030,
[handoff](docs/HANDOFF_STAGE_1_2.md)). Faza 1 je prošla (ADR-031: zamrznut WAF 0.10 / ROS 1.0,
VALIDATION ocijenjen jednom; unaprijed zadano pravilo, ne fizička validacija). Faza 2 je
završena (ADR-032: nijedan od šest primarnih testova ne odbacuje; PPO se ne razlikuje od nasumične
linije ni od najbolje heuristike; simulatorski rezultat). Faza 3 čeka korisnikovu odluku.
Pregled nakon faze 2 ([sažetak](docs/research/review-2026-11-11/SUMMARY.md), 2026-11-11) predlaže
TASK-028–030 (samo TRAIN, eksploratorno), također uz korisnikovo „da“. Ulaz za nastavak je [HANDOFF](HANDOFF.md).
TEST 2024 ostaje zatvoren. TASK-012/CFSDS/Cell2Fire je historijski odvojeni pravac.
Runtime PASS nije dokaz fizičke validacije ili RL prednosti. Čuvaj ovu razliku u sažecima.

Održavanje znanja: [maintenance](knowledge/maintenance.md), format:
[OKF profil](knowledge/okf-format.md). Novi `.md` koncept dobija YAML `type` i vezu iz
najbližeg `index.md`; ne izmišljati sources, generated/verified ili ljudsku potvrdu.
CI checker provjerava strukturu/linkove, ne istinitost naučnih nalaza.

- Radi u izdvojenom task worktreeu; sačuvaj tuđe izmjene.
- Worktree-i ovog projekta idu u `.worktrees/` glavnog klona, prema
  [workspace rasporedu](knowledge/workspace-layout.md). Prvo provjeri `git worktree list`;
  nastavi u odgovarajućem postojećem worktreeu. `.local/` je ignorisan radni prostor.
- Prije implementacije navedi pretpostavke i provjerljivi cilj; promjene drži malim.
- Činjenice, pretpostavke i prijedloge označi odvojeno. Uz vanjski nalaz navedi izvor i datum.
- Sintetički pilot ne prikazuj kao Cell2Fire, fizički validiran simulator ili istraživački rezultat.
- Za budžet, štetu, maske i statistiku dodaj test prije promjene ponašanja.
- Za oba agenta koristi iste scenarije, budžete, vremenski horizont i dostupne informacije.
- Ne prekidaj epizodu kada nestane budžeta. No-op mora ostati dostupan.
- Čuvaj kumulativnu štetu; tretirana prethodno zapaljena ćelija ostaje opožarena.
- Ne učitavaj neprovjerene pickle/torch checkpointove izvan izolovanog environmenta.
- Ne commituj privatnu prepisku, emailove, `.venv`, vanjski repo, velike mape ili težine.
- Dugi poslovi na Harunovom računaru: najviše 4 procesa uz `nice -n 19`, uz najavu trajanja
  (Harunova uputa, 2026-11-10; sa 7 procesa računar se preoptereti).
- Ne pokreći plaćeni compute, dugo treniranje, globalne instalacije, push/merge ili cloud deploy
  bez odgovarajućeg korisničkog naloga. Kratki lokalni testovi su normalni dio rada.
- Prije predaje pokreni `PYTHONPATH=src python3 -m unittest discover -s tests -v` i smoke CLI.
- Ažuriraj STATUS, NEXT_SESSION, odluke i experiment log nakon značajnog pomaka.
- Ažuriraj i root log/index kad se znanje mijenja; pokreni
  `python3 scripts/validate_knowledge.py --strict` uz requirements/knowledge.txt.
- Nemoj automatski raspoređivati posao članovima tima niti slati poruke profesorima.
