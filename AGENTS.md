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

**Trenutni dizajn je scenarij iz stvarne požarne lokacije + SimFire (ADR-040).** Uči se i
poredi ponašanje agenta u simulatoru na provjerljivim stvarnim lokacijama, datumima, gorivu,
terenu i vremenu. Historijski završni obod nije ulaz/nagrada, a stvarno smanjenje štete se
ne tvrdi. Kandidat za raspodjelu incidenata je USFS FPA-FOD; BurnMD ostaje opciona referenca
za ljudske linije.

Trenutno: SimFire 2.0.1 radi u lokalnom Python 3.9.25 venvu; sačuvani su i generisani demo
i 30-minutni smoke nad stvarnim LANDFIRE gorivom/terenom. Dixie FPA-FOD kartica zadržava
incident-referentnu koordinatu (nije potvrđen ignition) i tačan EPSG:32610 grid 128×128×30m.
Javni LANDFIRE ImageServer i ERA5 niz su preuzeti lokalno i provjereni; input TIFF/JSON su u
ignorisanom `.local/real-input-dixie/`. ERA5 nije ubačen u SimFire: vremenska zona discovery
HHMM nije potvrđena, 10m vjetar nije midflame vjetar, a RH nije gorivna vlaga. Prvi smoke
koristi demo atmosferu i nije historijski replay ili naučni rezultat. SimHarness/RLlib,
višedogađajna kohorta i weather/moisture mapping još nisu završeni.

Ne blokirati glavni policy eksperiment na nepostojećim Mineral line-time vrijednostima;
njihovo korištenje je opcioni replay track. Ne trenirati niti tvrditi RL prednost dok barem
jedan scenarij nema provjeren fuel/terrain/weather ulaz i stabilan trening runtime. Ne
tvrdimo da model smanjuje stvarni požar; prijavljujemo isključivo testirane simulacije.
CFSDS/Cell2Fire rad je sačuvan kao arhivirani prethodni track u
`docs/STATUS_CFSDS_ARCHIVE.md` i `HANDOFF_CFSDS_ARCHIVE.md`.

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
