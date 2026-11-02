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

**Aktivni dizajn je USFS FPA-FOD + LANDFIRE + dnevni gridMET proxy + SimFire (ADR-040).**
Kohorta ima 80 incidenata (40 train / 20 validation / 20 izvorno test); Larch Creek je
otvoren tokom integracionog smoke-a i izbačen iz konačnog testa, tako da ostaje 19
rezervisanih test incidenata. Veliki TIFF-ovi i izolovani Python 3.9.25 runtime su lokalno u
ignorisanom `.local/`, a ne u Gitu.

Gymnasium adapter, pinovani SimFire 2.0.1, karte goriva/terena i dnevni vremenski proxy
postoje za 80 slučajeva. WAF 0.3 i 15 jednominutnih SimFire ćelijskih koraka su početne
inženjerske postavke, ne fizički potvrđene vrijednosti. Smoke je prošao; FPA-FOD/SimFire
agent nije treniran i njegovi checkpointi ne postoje. Mogući ishod opisuje samo SimFire, ne hektare spašene u stvarnom požaru. CFSDS/
Cell2Fire rad je arhiviran.

Aktivni evaluacijski ugovor je
[`docs/research/SIMFIRE_EVALUATION_PROTOCOL.md`](docs/research/SIMFIRE_EVALUATION_PROTOCOL.md)
uz mašinski čitljiv
[`configs/simfire/evaluation-v1.json`](configs/simfire/evaluation-v1.json). Evaluator nema
trening funkciju. Njegov default preflight čita samo VALIDATION; TEST zahtijeva posebne
zastavice `--open-test --final-evaluation` i oba sačuvana PPO checkpointa. Ne pokretati
`learn()` niti otvarati TEST dok korisnik posebno ne odobri tu fazu.

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
- Prije predaje pokreni `PYTHONPATH=src python3 -m unittest discover -s tests -v`, knowledge
  validator i odgovarajući smoke/preflight CLI. **Ako korisnik zabrani trening, ne pokreći
  puni suite:** `tests/test_gym_env.py::test_masks_save_load_and_short_learning` poziva
  `.learn()` nad malim sintetičkim fixtureom. U tom slučaju biraj sigurne ciljane testove,
  knowledge validator i preflight bez simulator koraka.
- Ažuriraj STATUS, NEXT_SESSION, odluke i experiment log nakon značajnog pomaka.
- Ažuriraj i root log/index kad se znanje mijenja; pokreni
  `python3 scripts/validate_knowledge.py --strict` uz requirements/knowledge.txt.
- Nemoj automatski raspoređivati posao članovima tima niti slati poruke profesorima.
