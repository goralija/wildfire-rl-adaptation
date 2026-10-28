# Naredni zadaci

Napor je okvirni agentov prijedlog u aktivnim radnim satima, bez roka i dodjele članovima.

| ID | Prioritet / stanje | Isporuka i provjera | Napor |
| --- | --- | --- | --- |
| TASK-001 | P0 završeno | znanje, izvori, rubrika, specs, status; AC-001 | bootstrap |
| TASK-002 | P0 završeno | synthetic budžet/no-op/damage + testovi; AC-002..003 | bootstrap |
| TASK-003 | P0 završeno | paired baselines, manifest/CSV/SVG, replay; AC-004..005 | bootstrap |
| TASK-004 | runtime završeno; research gate djelimičan | build, oba modela, seed/replay i budžetski no-op provjereni; AC-006 | ostvareno |
| TASK-012 | P0 prvo sljedeće, otvoreno | dataset refinement: uloga, izbor/obim, model/scenario veza, splitovi i metrike; prijedlog za usaglašavanje | 1–2 h za prijedlog |
| TASK-004c | P0 tehnički nastavak nakon refinementa | warmup/damage adapter, C++ termination reason i active/burnt export u usaglašenom obimu | 3–6 h |
| TASK-004b | P0 uslovno | SimFire fallback spike ako gate padne; novi ADR | 2–4 h |
| TASK-005 | P1 nakon gatea | budžetski adapter + frozen benchmark + cijena 10 rollouta | 3–6 h |
| TASK-006 | P1 | 3 training seeda, fine-tuning po B, matched controls, hierarchical CI; AC-007 | zavisi od mjerenja |
| TASK-007 | P1 nakon minimuma | priority weight ablation, ukupna vs priority šteta; AC-008 | 4–8 h + compute |
| TASK-008 | P2 | joint budget features/weight transfer i ablation bez njih | samo uz prostor |
| TASK-009 | P1 predaja | glavni grafikoni, poster, interpretacija i usmeni | 4–8 h |

Redoslijed nastavka: 012→usaglašen obim→004c→005→006→007→009;
001–004 su ostvarena osnova, 004b samo nakon dokumentovanog FAIL.
Odmah planirati mape/weather licences i test split tokom TASK-004, bez velikih preuzimanja.
Nema obaveze implementacije svakog proširenja: glavni minimum i kvalitet evaluacije imaju prednost.

TASK-010 (P2 minor, ~15 min): make malformed root JSON config (`null`, list) return
ValueError/CLI usage error rather than traceback. Test first. Does not block valid runs.

TASK-011 (P1 ograničena historijska provjera; poslije TASK-004c, nije novi preduslov
za svako RL poređenje): izvori i mali uzorci već su pregledani; vidjeti
research/REAL_FIRE_DATASETS.md i reports/real-fire-data/.

- 011a: Dogrib vremenski/prostorni/provenance alignment, nonfuel neslaganja i kratki
  simulator-only replay. Prihvat: isti početni perimetar, domen i završni trenutak,
  documented weather/timezone, IoU/F1/area error uz seedove; bez tvrdnje o nezavisnoj
  generalizaciji i bez tihe kalibracije na testu. Prvo timebox 2–4 h za izvedivost.
- 011b: 3–5 drugih CFSDS događaja samo ako se mogu pripremiti kompletni FBP/terrain
  i weather inputi; event holdout prije tuninga, provjera rasterskih oznaka i licence.
  Prvo timebox 2–4 h za izvedivost; ako inputi nisu dostupni, dokumentovati budući rad.
- Ne pretvarati temu u novi model predikcije širenja i ne preuzimati WildfireSpreadTS
  arhivu od 48.4 GB radi početne provjere.

TASK-012 (P0, neposredni fokus): pregled izvora nije konačan izbor dataseta. Razjasniti
ulogu stvarnih referenci u odnosu na simulator inpute i RL iskustvo, konkretne događaje/
mape i potrebne ulaze, rezoluciju/domen kompatibilan s modelom, scenario jedinicu,
kalibraciju/splitove i metrike. Prihvat: kratak prijedlog u REAL_FIRE_DATASETS uz
jasno označene otvorene odluke za usaglašavanje. Dogrib/CFSDS ostaju kandidati;
postojeći uzorci nisu zamrznut test skup. Tek prema dogovorenom obimu slijedi
implementacijski plan. TASK-011 je moguća izvedba historijske validacije, ne već
usaglašena obaveza cijelog projekta.
