---
type: Backlog
title: Naredni zadaci
---
# Naredni zadaci

## Aktivni CA pravac (2026-11-21)

| Task | Status | Sljedeće |
| --- | --- | --- |
| TASK-035 | završeno, ADR-040 | Native/current forcing ugovor, 240 development epizoda i15 replayeva PASS; 352 testa; sigurnost prijavljena zasebno |
| TASK-036 | faza A završena | SimFire repair ostaje na izvedenoj bazi; nalazi ADR-038 |
| TASK-037 | predloženo, odgođeno | Preostala SimFire fizika/gate/trening |
| TASK-038 | završeno, ADR-042 |3seeda, šest modela, 288development putanja; nijedan kandidat ne prolazi; svi rezultati/sigurnost sačuvani |
| TASK-040 | faza A završena, ADR-044; faza B otvorena | 16 istih TRAIN, identične linije, procenti/ha/no-op i3 CA spread replike; mješoviti rezultati, native resursi/akcije/PPO još nisu upareni |
| TASK-041 | predloženo, sljedeći prioritet | TRAIN audit SF/CA no-op rasta prema istim opaženim FEDS promjenama; prvo zamrznuti plan, bez kalibracije/treninga/holdouta |
| TASK-039 | predloženo, odgođeno iza growth audita | TRAIN-only dijagnoza vlastitih putanja i pokrivenosti učitelja/encoder-a; unaprijed zadat kratki nastavak tek po nalazu |

Starije oznake TASK-035 kao drafta ispod su historija, zamijenjene korisnikovim nalogom
2026-11-21 i ADR-039. TEST 2024 i stvarni VALIDATION nisu otvoreni.


## Poslije popravka opažanja — 2026-11-20 (ADR-038)

| ID | Stanje | Dokaz / naredno |
| --- | --- | --- |
| TASK-036 faza A | završeno | [v2 izvještaj](research/SIMFIRE_OBSERVATION_REPAIR.md); categorical/local/terrain opservacija, nonfuel maska,98 kontrolisanih replayeva i 16 nested kombinacija |
| TASK-035 | draft, nije pokrenut | CA ugovor informacija i tehnički pilot; poslije ovog dodatnog SimFire pokušaja ostaje preporučeni glavni pravac |
| TASK-037 | predloženo, nije pokrenuto | preostali SimFire v2: max/korak kroz novi gate i novu tabelu, pa v2 encoder/checkpoint i BC/PPO; B=2/B=4 odvojeno |

Širi SimFire v2 physics/gate iz starog TASK-036 opisa nije proglašen završenim; sada
je eksplicitno izdvojen u TASK-037. Meni opažanja je završen bez naknadnog tuneovanja.
Fine+gate je bolji TRAIN prosjek, ali interval uključuje 0; nije potvrđena RL prednost.

## Aktivni nastavak — 2026-11-20 (ADR-036)

[Završni audit](research/SIMFIRE_OBSERVATION_AUDIT.md) čuva dokaze i ograničenja.

| ID | Stanje | Ishod / sljedeće |
| --- | --- | --- |
| TASK-034 | završeno | input/observation audit 98, četiri nested porodice bez prolaza, startup race popravljen, dvije native sensitivity probe; ne dokazuje da su sve mogućnosti iscrpljene |
| TASK-035 | draft pripremljen, nije pokrenut | CA ugovor informacija i tehnički pilot; prije treninga zamrznuti opažanje/checkpoint, slučajeve, jedinice i komparatore; [draft](../configs/drafts/ca-controlled-pilot-v1.json) |
| TASK-036 | opcionalni SimFire v2, nije pokrenut | nova fuel/nonfuel/terrain opservacija i rezolucija; max/korak kroz novi TRAIN gate, zatim nova tabela/politike |

Preporuka CA pilota nije tvrdnja da je CA validiran ili da će RL pobijediti. TEST 2024
ostaje zatvoren; novi VALIDATION i dug trening nisu izvedeni. Stariji task statusi ispod
su historija; TASK-034 više nije samo prijedlog.

## Aktivni nastavak — 2026-11-19 (ADR-034)

[SimFire B=1 izvještaj](research/SIMFIRE_B1_EXPLORATION.md) sadrži dokaze i komande.
Ovaj dio zamjenjuje ranije statuse TASK-028–030; stariji prioriteti ispod su historija.

| ID | Stanje | Ishod / sljedeće |
| --- | --- | --- |
| TASK-028 | završeno kao pomoćni obračun | testirana unija linije i no-op otiska; raw i charged prijavljeni; zvanična env nagrada ostaje otvorena odluka |
| TASK-029 | završeno | 98 požara ×33=3.234 ishoda; reference/mask/input hash PASS; ADR-032 agregati se poklapaju; bez ruba |
| TASK-030 | završeno | osam fiksnih metoda, LOO po požaru; nijedna ne prelazi prag u oba zasebna obračuna; novi PPO nije pokrenut |
| TASK-034 | predloženo, nije pokrenuto | TRAIN-only dijagnoza prostornog signala u istom opažanju i stabilnosti selekcije; novi protokol prije scoringa |

Novi kanali, VALIDATION, B=2/B=4, zvanična metrika i remote objava ostaju zasebne odluke.
TEST 2024 ostaje zatvoren; CA faza 3 nije pokrenuta.

## Aktivni prioritet — 2026-11-12 (pregled nakon faze 2)

Plan i razlozi: [pregled 2026-11-11](research/review-2026-11-11/SUMMARY.md). Sve stavke čekaju
Harunovo „da“; ništa nije pokrenuto.

| ID | Stanje | Sljedeće |
| --- | --- | --- |
| TASK-028 | predloženo | ocjena s naplatom linije (ćelija linije koju bi no-op vatra spalila je šteta); test prije koda; kao zvanična metrika traži ADR |
| TASK-029 | predloženo, bez ADR-a (TRAIN, eksploratorno) | iscrpna B=1 tablica: 33 niza po požaru, ishod, opservacije, legalni sektori, ćelije linije, no-op otisak; pilot 20 požara = TRAIN benchmark, pa 98 |
| TASK-030 | predloženo, bez ADR-a (TRAIN, eksploratorno) | offline ocjena: fiksni sektor, podešeno pravilo, selektor, tabelarni RL, BC; LOO po požaru; prag ≥30 ha i ≥25% jaza |
| TASK-031 | opcionalno, ADR ako se usvoji | B=1 tablica s „repom“ od 48 h bez odluka |
| TASK-032 | ADR prije | planer sa zadnjim viđenim vremenom; „vidovita“ gornja granica odvojeno |
| TASK-033 | ADR prije | B=2/B=4, novo VALIDATION korištenje (B=1 glavni test), BC+PPO ili čisti RL |

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
| TASK-026 | faza 1 završena: gate PASS, WAF 0.10 / ROS 1.0 zamrznut, VALIDATION jednom (ADR-031, PR #17 spojen); faza 2 završena: nijedan od šest primarnih testova ne odbacuje, PPO se ne razlikuje od nasumične linije ni od najbolje heuristike (ADR-032, PR #18 spojen); faza 3 uz nalog | korisnikove odluke (glavni simulator, CA observation) → faza 3 CA trening (ADR-030 §7) |
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
