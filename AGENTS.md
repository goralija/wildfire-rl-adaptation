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
TASK-012 je završen. TASK-015 je proširen na target-blind pre-screen svih 1.301 TRAIN
parova: postojeća v2014b karta klasno prolazi u 701 od 1.295 dostupnih fiksnih prozora,
64 traže sub-cell pregled, 530 pada, a 6 nema prozor. To nije dozvola za replay; broj
slučajeva odobrenih za puni replay i dalje je nula. U službenom CanFG v20191114 ZIP-u
pronađen je interni tekst post-fire pravila, ali on ne dokazuje vremenski cutoff starije
v2014b karte niti tačno određuje regionalno brojanje starosti. v2014b as-of-event
validnost i dalje nije potvrđena. Input-alignment audit je zasebno pokrio samo tri
postojeća FireCase paketa; DEM/weather provenance nije potpuna, a suppression ostaje
unknown. No-action mismatch ostaje otvoren.
TASK-018 dijagnostička faza i TASK-004c episode adapter su završeni lokalno. Početni
input sada ima prototipsko target-blind pravilo: prozor se centrira na centroid day n−1,
a sigurne unutrašnje day n−1 ćelije čine početni front; granica prozora ostaje historijski
scar. Za TRAIN događaj `2018_747` dokazano je da promjena day-n ciljne maske ne mijenja
prozor, modelsku scar/front masku ni `InitialState.csv`. TRAIN-only screen istog pravila
pokazuje slabo preklapanje ciljnog dana za većinu trenutno rangiranih kandidata; to je
dijagnostika prostorne prikladnosti, ne dozvola da se prozor bira prema targetu.
Naknadni prostorni audit na istih 25 parova pokazuje da 2 km nije dovoljno; oko 4 km
medijalno pokriva samo 1.95% targeta, a oko 6 km oko 15.3% i ne stane u dva izvorna
rastera. Nijedna domena nije usvojena; day-pair membership shortlist-a nije dokazano
potpuno outcome-independent jer je tražen target-day red i pozitivna `firearea`.
Sljedeći korak za cohort/prostor je završen: unaprijed definisano pravilo obradilo je svih
1.301 TRAIN rastera i provjerilo pet fizičkih skala. Na 1.010 parova naredni dan ima
mapirane piksele; 291 ostaje sa statusom bez mapiranog targeta. Ovo je geometrijski
pre-screen, ne konačna podobna kohorta. Godišnja fuel mapa još nije napravljena: 2014b
nema potvrđen per-pixel cutoff, a pronađeni v20191114 succession tekst još nema potvrđen
age/regionalni ugovor. Izolovani C++ importer contract sada prihvata eksplicitni
`scar_nf` samo na tačnoj NF ćeliji i čuva ga kao
cumulative damage, ali stvarni CFSDS builder i dalje blokira takav ulaz dok se ne riješi
fuel/source provenance. W.I.S.E. Figure 2 i interni v20191114 rules tekst sada su
pregledani; v2014b cutoff, tačno regionalno/starosno računanje i as-of-event baza ostaju
otvoreni. Alberta
2006–2025 suppression dataset je pronađen, ali CSV download je vratio HTTP 403 i nema
spojenih suppression događaja. Tri spremljena 2018 slučaja imaju BC perimeter crosswalk
kandidate N12395/C11937/N12413; dva imaju djelimične javne izvještaje o aktivnosti, a
nijedan nema potpun action log ili dokaz `none`. W.I.S.E. isključuje požare sa bilo kakvim
CNFDB zabilježenim gašenjem; `unknown` zato nije prihvatljiv dokaz za čisti no-action
slučaj (EXP-024/ADR-034). Zatim slijedi fuel evidence, train terrain/weather provenance,
event-keyed suppression joins i unaprijed definisani replay gate.
Root cause no-action overgrowth nije izolovan, a no-action gate nije prošao.
Ne koristi validation/test ishode za izbor parametara. No-action gate i heldout freeze
moraju proći prije policy benchmarka ili fine-tuninga. Runtime PASS nije dokaz fizičke
validacije ili RL prednosti. Čuvaj ovu razliku u sažecima.

EXP-025 (2026-10-31) checksum-verifikovao je šest ERA5-FWI-SN dnevnih kodova za 2018.
U tri uparena TRAIN dijagnostička replaya zamjena samo FWI kodova promijenila je broj
novih 100 m ćelija za −3, 0 i 0; sve tri predikcije i dalje dodiruju rub cropa. Za buduće
kanadske slučajeve koristi se samo kao dokumentovan dnevni izvor, ponovljen u 24 satna
reda i jasno označen dnevnim; satna meteorologija ostaje odvojen izvor. Ovo nije fizička
validacija niti zatvara TASK-015. EXP-026 je potvrdio da Alberta CSV s action-time poljima
postoji u katalogu, ali mu ovaj environment dobija 403; dostupni GIS sloj nema vrijeme
prve fizičke akcije. Ne tretirati `out of control`, prazno polje ili nedostupan URL kao
dokaz da gašenja nije bilo. Postojeći tri kandidata su BC, pa se suppression label ne
mijenja. Pogledati ADR-035/036 i EXP-025/026.

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
