---
type: Backlog
title: Naredni zadaci
---
# Naredni zadaci

## Aktivni prioritet — 2026-11-09 (ADR-029, ispravke prije ponovnog pokretanja)

Rezultati ADR-022–028 su nevažeći zbog gridMET greške; redoslijed i prihvat su u
[NEXT_SESSION](NEXT_SESSION.md).

| ID | Stanje | Sljedeće |
| --- | --- | --- |
| TASK-021 | završeno (PR #8) | CI posao `numeric` s tačnim spiskom preskočenih testova |
| TASK-022 | završeno (PR #9) | IoU rasta, downwind elipsa, `growth_gate` |
| TASK-023 | završeno (PR #12) | linije, observation bez prognoze, statistika §4, zaštite |
| TASK-024 | završeno (PR #11) | CA: napredak, ćelije linije, prihvat §5, opisni real-case test |
| TASK-025 | završeno (ADR-030) | odluke zapisane; implementacija opcija u TASK-023/024 |
| TASK-026 | faza 1 završena: gate PASS, WAF 0.10 / ROS 1.0 zamrznut, VALIDATION jednom (ADR-031, PR čeka merge); faza 2 u toku ([handoff](HANDOFF_STAGE_1_2.md)); faza 3 uz nalog | faza 2 benchmark i studija budžeta → faza 3 CA trening (ADR-030 §7) |
| TASK-027 | završeno (PR #15) | duplikat uklonjen (98 TRAIN, ADR-030 §6); FEDS `t` = prolaz u lokalnom sunčevom vremenu → UTC po dužini (dopuna ADR-030, [dokazi](research/SIMFIRE_ENVIRONMENT.md)); novi gridMET sha256 `7a51aadd…`; RNG reset riješen |


## Aktivni prioritet — 2026-11-04 (noćni rad, koraci 5–8)

TASK-019 je izveden do kraja: ulazi su reproducirani, dijagnoza i preregistrovana 3×3
mreža (ADR-023) nisu dale prolaz; gate je zamrznut kao FAIL_exploratory (ADR-024).
Validation je skoriran jednom po zapisu. TASK-020 je pojednostavljen u ADR-025 (jedinica =
smjena ekipe od 20 ljudi, linija od 7 ćelija, bez gradnje kroz vrijeme). TASK-005/006 su
izvedeni kao mala eksploratorna studija na free-burn stress zapisu (ADR-026); rezultati su
u [policy benchmarku](../reports/real-fire-data/feds-simfire-policy-benchmark-v1.json).

| ID | Stanje | Sljedeće |
| --- | --- | --- |
| TASK-019 | završeno, gate FAIL | timski odlučiti o growth-aware gateu ili modelu zaustavljanja/gašenja prije bilo kakve tvrdnje o kalibraciji |
| TASK-020 | ADR-025 minimum | gradnja linije kroz vrijeme, 16 sektora, više jedinica po odluci |
| TASK-005/006 | eksploratorno izvedeno | više seedova/koraka, observation koji vidi buduće rastuće dijelove fronta, opcija više linija po 12h |
| TASK-007 | nije rađeno | ablacija prioritetnih područja (prvo izbačeno zbog vremena) |
| TASK-009 | čeka | grafikoni i poster; `scripts/plot_budget_benchmark.py` daje osnovni grafikon |

## Prioritet — 2026-11-03 (historijski)

ADR-016/018 definišu SimFire/FEDS pravac i prošireni, unaprijed spremljeni FPA-FOD
candidate frame. Originalna kohorta ne prolazi (19/40 train, 7/20 validation); prošireni
okvir daje 99/208 train i 20/56 validation sa punih 48h referenci, pa data-coverage
gate prolazi. TRAIN no-op ekran je zatim izvršen na svih 99 slučajeva i pao prema
persistence/elipsa referencama (ADR-022). Sljedeći posao je dijagnostika i ponovljeni
TRAIN-only gate; benchmark PPO ostaje blokiran. Tehnički PPO smoke je dostupan.

Napor je okvirni agentov prijedlog u aktivnim radnim satima, bez roka i dodjele članovima.

| ID | Prioritet / stanje | Isporuka i provjera | Napor |
| --- | --- | --- | --- |
| TASK-001 | P0 završeno | znanje, izvori, rubrika, specs, status; AC-001 | bootstrap |
| TASK-002 | P0 završeno | synthetic budžet/no-op/damage + testovi; AC-002..003 | bootstrap |
| TASK-003 | P0 završeno | paired baselines, manifest/CSV/SVG, replay; AC-004..005 | bootstrap |
| TASK-004 | runtime završeno; research gate djelimičan | build, oba modela, seed/replay i budžetski no-op provjereni; AC-006 | ostvareno |
| TASK-013 | završeno: podrška handoffu | OKF repo bundle, ulazi/navigacija, održavanje, validator/testovi/CI | ostvareno |
| TASK-012 | zatvoreno za aktivni plan | aktivni izvor je SimFire + FPA-FOD/FEDS prema ADR-016; raniji Canada/CFSDS izbor je historijski i odvojen | ostvareno |
| TASK-014 | lokalno završeno 2026-10-30; drugi host nije provjeren | moderni `.venv` i odvojeni legacy Docker izgrađeni; package/source/image hashovi i smoke/inference receipt zapisani | ostvareno lokalno |
| TASK-015 | P0, djelimično završeno | odabrana CFSDS putanja; 44 preliminarna compact-crop kandidata podijeljena 20/9/15; tri train slučaja su pokrenuta, jedan je odbijen zbog water/nonfuel ćelija; treba fuel-vintage, suppression i vremenski QC prije benchmarka | 2–4 h + data QC |
| TASK-004c | P0, djelimično | multi-cell C++ početni state radi; preostaje kumulativna šteta i terminalni razlog containment naspram isteka weather horizonta za RL evaluator | 3–6 h |
| TASK-017 | završeno 2026-10-30 | `InitialState.csv` uvozi raniji scar i više aktivnih ćelija; fixture i stvarni `2018_747` C++ import/replay su uspješni | ostvareno |
| TASK-018 | P0 završeno 2026-11-03 | Lokalno checksum-verifikovati FEDS, ponoviti originalnu kohortu (19/7 FAIL), auditovati unaprijed definisani širi frame (99/20 PASS), izvesti 119 full-48h episode zapisa; test 2024 zatvoren | ostvareno |
| TASK-019 | P0 follow-up nakon screen-a | Kohortni no-op screen je završen (99/99; 8 WAF); gate FAIL prema persistence/elipsi. Dijagnosticirati shared forcing/raster/SimFire odgovor i ponoviti isti TRAIN gate | 4–8 h + model QC |
| TASK-020 | P0 poslije no-op gatea | Fireline build-over-time, wait/16 front sektora, 20 ljudi × 8h i 0/1/2/4 smjene; precizna potrošnja i nastavak nakon praznog budžeta | zavisi od rollout mjerenja |
| TASK-016 | P0, tri pilot konverzije; no-action gate nije prošao | FireCase JSON→raster/weather→Cell2Fire radi; tri train-only replaya šire 66/237/73 ha prema 15.39/12.15/12.15 ha; jedan kandidat odbijen na fuel provjeri; prvo ulazni QC i dijagnostika širenja, bez fine-tuninga | 6–12 h + GIS/model |
| TASK-004b | historijski prijedlog; superseded ADR-016 | Raniji SimFire fallback spike je zamijenjen aktivnim TASK-018/019 tokom | — |
| TASK-005 | P1 nakon gatea | budžetski adapter + frozen benchmark + cijena 10 rollouta | 3–6 h |
| TASK-006 | P1 | 3 training seeda, fine-tuning po B, matched controls, hierarchical CI; AC-007 | zavisi od mjerenja |
| TASK-007 | P1 nakon minimuma | priority weight ablation, ukupna vs priority šteta; AC-008 | 4–8 h + compute |
| TASK-008 | P2 | joint budget features/weight transfer i ablation bez njih | samo uz prostor |
| TASK-009 | P1 predaja | glavni grafikoni, poster, interpretacija i usmeni | 4–8 h |

Aktivni redoslijed po ADR-022: dijagnostika neuspjelog TASK-019 no-op screen-a→mali
zajednički kandidat set i ponavljanje TRAIN gatea→tek nakon prolaza i zamrzavanja
parametara preuzimanje validation rastera→definicija matched akcija/heuristika/PPO
benchmarka→završno otvaranje test split-a. Firehose TASK-004c,
CFSDS TASK-015/016 i njihovi adapteri ne prenose se automatski.

Historijski redoslijed ispod čuva TASK-012/014/015/004c/017/016 nalaze iz CFSDS/
Cell2Fire pravca. ADR-016 je novija odluka i ima prednost za aktivni benchmark.
Ne počinjati fine-tuning dok se ne izmjere rollout/training trošak i zamrzne test ID skup.
Historijski TASK-011a/011b ostaje opcion i iza glavnog simulator gatea.
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

TASK-012 je zatvoren u ranijem CFSDS tracku; ADR-016 sada usmjerava aktivni benchmark.
FireSpread_MedEU/EFFIS ostaju moguća kasnija regionalna studija jer evropski NFFL kodovi
ne ulaze direktno u kanadski simulator. Agentove akcije i nagrade generiše simulator;
opaženi perimetri nisu oznake najboljeg gašenja.

TASK-014 (P0 environment reproduction) je lokalno PASS: macOS ARM64/Python 3.12.4
moderni project venv, Linux ARM64/Python 3.8 legacy Docker i GIS paketi. Testovi, strict
knowledge checker, CLI, GIS reprojection smoke, moderni PPO smoke i 12 Firehose inference
slučajeva su u reports/environment-setup/. Drugi OS/arch nije provjeren.

TASK-015 (P0 input/cohort quality): geometrijski screen za 2014–2024 zadržao najviše pet
candidate slučajeva po godini: 20 train, 9 validation, 15 test. To nije iscrpan spisak
niti finalni benchmark. Pripremiti FBP 2019/2024 vintages za kasnije godine, provjeriti
fuel/terrain/weather poravnanje na više train cropova, spojiti suppression dokaze, pa
tek onda zaključati heldout event IDs.

TASK-017 je završen za početni historical state bridge. `InitialState.csv` prenosi ranije
opožarene ćelije (`burnt`) i više aktivnih front ćelija (`burning`). Fixture i stvarni
`2018_747` import/reset prošli su u C++; ostatak cumulative-damage/terminal-state praćenja
je TASK-004c.

TASK-016 sada ima tri FireCase konverzije i tri no-action train replaya (`2018_747`,
`2018_241`, `2018_1770`); za prvi je dodatno urađeno šest seedova. Sva tri odstupaju od
dnevnog CFSDS cilja, a predikcije dotiču rub modelskog prozora. `2014_538` je odbijen jer
neke historijske ćelije mapiraju na water/nonfuel. Suppression status ostaje nepoznat.
Prije RL benchmarka provjeriti gorivo, vrijeme, FBP parametre i extent; kalibraciju raditi
samo na train/calibration eventima.
