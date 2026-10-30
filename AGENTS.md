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

**Odabrana je putanja Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire (ADR-013).**
TASK-012 je završen. TASK-015 ima preliminarni train-only fuel audit: 10/20 kandidata
prolazi samo taj gate; vrijeme, teren, gašenje i no-action mismatch ostaju otvoreni.
TASK-018 dijagnostička faza i TASK-004c episode adapter su završeni lokalno. Sljedeći
fokus je preostali TASK-015 train-only fuel-vintage/terrain/weather/suppression QC. Root
cause no-action overgrowth nije izolovan, a no-action gate nije prošao. Ne koristi
validation/test ishode za izbor parametara. No-action gate i heldout freeze moraju proći
prije policy benchmarka ili fine-tuninga. Runtime PASS nije dokaz fizičke validacije ili
RL prednosti. Čuvaj ovu razliku u sažecima.

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
- Ne pokreći plaćeni compute, dugo treniranje, globalne instalacije, push/merge ili cloud deploy
  bez odgovarajućeg korisničkog naloga. Kratki lokalni testovi su normalni dio rada.
- Prije predaje pokreni `PYTHONPATH=src python3 -m unittest discover -s tests -v` i smoke CLI.
- Ažuriraj STATUS, NEXT_SESSION, odluke i experiment log nakon značajnog pomaka.
- Ažuriraj i root log/index kad se znanje mijenja; pokreni
  `python3 scripts/validate_knowledge.py --strict` uz requirements/knowledge.txt.
- Nemoj automatski raspoređivati posao članovima tima niti slati poruke profesorima.
