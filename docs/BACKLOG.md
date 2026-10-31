---
type: Backlog
title: Naredni zadaci
---
# Naredni zadaci

Napor je okvirni agentov prijedlog u aktivnim radnim satima, bez roka i dodjele članovima.

| ID | Prioritet / stanje | Isporuka i provjera | Napor |
| --- | --- | --- | --- |
| TASK-001 | P0 završeno | znanje, izvori, rubrika, specs, status; AC-001 | bootstrap |
| TASK-002 | P0 završeno | synthetic budžet/no-op/damage + testovi; AC-002..003 | bootstrap |
| TASK-003 | P0 završeno | paired baselines, manifest/CSV/SVG, replay; AC-004..005 | bootstrap |
| TASK-004 | runtime završeno; research gate djelimičan | build, oba modela, seed/replay i budžetski no-op provjereni; AC-006 | ostvareno |
| TASK-013 | završeno: podrška handoffu | OKF repo bundle, ulazi/navigacija, održavanje, validator/testovi/CI | ostvareno |
| TASK-012 | završeno 2026-10-30 | prema korisnikovoj uputi odabrana Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire; historijske granice služe zasebnom reality-checku, a agent uči iz simulatora | ostvareno |
| TASK-014 | lokalno završeno 2026-10-30; drugi host nije provjeren | moderni `.venv` i odvojeni legacy Docker izgrađeni; package/source/image hashovi i smoke/inference receipt zapisani | ostvareno lokalno |
| TASK-015 | P0, djelimično završeno | full target-independent screen: svih 1.301 TRAIN rastera obrađeno; 1.010 imaju target mapu, 291 nemaju mapirane target piksele; 20×20/100 m prozor nađen za 1.295; nijedna domena još nije usvojena; `scar_nf` importer contract je provjeren; W.I.S.E. Figure 2 je javno transkribovana, ali v2014b cutoff, starosna semantika/specijalne klase, DEM/weather lineage i suppression join ostaju otvoreni; Alberta CSV endpoint je vratio HTTP 403 | dokaz fuel vintagea + pribavljanje/join suppression podataka + kompletna DEM/weather provenance + preregistrovani replay gate |
| TASK-018 | P0, dijagnostička faza završena 2026-10-30; uzrok nije izolovan | poređenje hashova/postavki i unaprijed fiksirani vremenski presjeci na tri train replaya; metadata horizon bug ispravljen; rub/domenska ograničenja potvrđena; bez heldout kalibracije ili treninga | ostvareno |
| TASK-004c | P0, adapter završen lokalno 2026-10-30 | C++/Python kumulativna šteta, zaseban scar/front i named terminal receipt; fixture + 12/12 inference rollouta, bez treninga; fizički no-action gate ostaje otvoren | ostvareno |
| TASK-017 | završeno 2026-10-30 | `InitialState.csv` uvozi raniji scar i više aktivnih ćelija; fixture i stvarni `2018_747` C++ import/replay su uspješni | ostvareno |
| TASK-016 | P0, tri pilot konverzije; no-action gate nije prošao | FireCase JSON→raster/weather→Cell2Fire radi; tri train-only replaya šire 66/237/73 ha prema 15.39/12.15/12.15 ha; 2014_538 fuel-rejected; fuel gate 10/20 train kandidata pass-only; TASK-018 je dokumentovao vremensku osjetljivost, ulazne razlike i edge/domain limite; nema fine-tuninga | 6–12 h + GIS/model |
| TASK-004b | P0 uslovno | SimFire fallback spike ako gate padne; novi ADR | 2–4 h |
| TASK-005 | P1 nakon gatea | budžetski adapter + frozen benchmark + cijena 10 rollouta | 3–6 h |
| TASK-006 | P1 | 3 training seeda, fine-tuning po B, matched controls, hierarchical CI; AC-007 | zavisi od mjerenja |
| TASK-007 | P1 nakon minimuma | priority weight ablation, ukupna vs priority šteta; AC-008 | 4–8 h + compute |
| TASK-008 | P2 | joint budget features/weight transfer i ablation bez njih | samo uz prostor |
| TASK-009 | P1 predaja | glavni grafikoni, poster, interpretacija i usmeni | 4–8 h |

Redoslijed nastavka: 012 (završeno) → 014 local PASS (završeno) → 015 train fuel/input
QC (djelimično) + 018 no-action dijagnostička faza (završena, uzrok još nije izolovan)
→ 004c cumulative-damage/terminal-reason adapter (završen lokalno) → 015 preostali
fuel-vintage/terrain/weather/suppression QC → unaprijed definisani train-only kontrolisani
replayi / 016 dodatni slučajevi → no-action gate odluka + heldout freeze → 005 benchmark/time
→ 006 fine-tune → 007 → 009.
TASK-017 initial-state import je završen. TASK-004b je samo fallback nakon dokumentovanog
FAIL. TASK-005/006 ne počinju prije no-action gatea i heldout freezea; adapter PASS je
tehnički preduslov, ne zamjena za no-action gate.
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

TASK-012 je zatvoren: glavni pravac je Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire.
FireSpread_MedEU/EFFIS ostaju moguća kasnija regionalna studija jer evropski NFFL kodovi
ne ulaze direktno u kanadski simulator. Agentove akcije i nagrade generiše simulator;
opaženi perimetri nisu oznake najboljeg gašenja.

TASK-014 (P0 environment reproduction) je lokalno PASS: macOS ARM64/Python 3.12.4
moderni project venv, Linux ARM64/Python 3.8 legacy Docker i GIS paketi. Testovi, strict
knowledge checker, CLI, GIS reprojection smoke, moderni PPO smoke i 12 Firehose inference
slučajeva su u reports/environment-setup/. Drugi OS/arch nije provjeren.

TASK-015 (P0 input/cohort quality): geometrijski screen za 2014–2024 zadržao najviše pet
kandidata po godini: 20 train, 9 validation, 15 test. Train-only audit (`docs/research/CFSDS_TRAIN_QC.md`)
obrađuje 20 train parova: 10 prolazi samo gorivnu provjeru, 10 pada; postojeća tri replaya
su među prolazima. Validation/test rasteri nisu otvarani. Kohorta nije iscrpna niti je
heldout benchmark zamrznut. Pre-target maska za `2018_747` koristi samo
`arrival_day < target_doy`; receipt je `reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json`.
Target-blind initial-state prototip bira crop blizu day n−1 centroida; invariance proof
pokazuje da target-mask promjena ne utiče na simulator input
(`reports/real-fire-data/cfsds-target-blind-input-invariance.json`). Train-only shortlist
screen sadrži makar jedan target pixel u samo 4/25 postojećih 2 km prozora. Bounded domain
audit poredi iste parove: 4 km prozori hvataju makar target pixel u 19/25, ali medijalno
samo 1.95% targeta; 6 km medijan je 15.31%, ali dva rastera ne mogu smjestiti prozor.
Nijedna domena nije usvojena; metoda i ograničenja su u
`docs/research/CFSDS_SPATIAL_FEASIBILITY.md` i `reports/real-fire-data/cfsds-train-spatial-feasibility.json`.
Puni day-pair membership i prostorni screen sada su završeni target-independent pravilom
(EXP-013/ADR-023). Ovo nije godišnja fuel mapa: nema potvrđenog baznog vremenskog cutoffa
ni autoritativnog succession crosswalka. Kasniji EXP-015/ADR-025 implementirali su i
provjerili `scar_nf` importer contract za izolovani adapter; to ne odobrava annual map niti
CFSDS builder ulaz. Pogledati ADR-020/023/025 i EXP-010/013/015. Još trebaju FBP
vintage/source provjera, train terrain/weather poravnanje, suppression dokazi i unaprijed
definisani replay gate. Raniji 10/20 fuel-only rezultat koristio je prethodnu kohortu/
izreze i ne važi za novi puni screen. EXP-014 našao je CWFIS site-wide Open Government
Licence - Canada i službena pravila za baseline FBP klasu. EXP-016 je ispravio raniji
nalaz: W.I.S.E. Figure 2 je javno transkribovana, ali starosna semantika/specijalne klase
i stvarni v20191114 artifact nisu provjereni; v2014b NFDB/NBAC cutoff i dalje nije
dokumentovan. Službeni Alberta 2006–2025 fire-level suppression dataset je pronađen, ali
CSV endpoint vraća HTTP 403 i nema join-a. Zato nema sigurnog godišnjeg fuel vintagea;
DEM/weather i druge provincijske suppression izvore još treba povezati. Importer ugovor
za historical scar je testiran na sintetičkom fixtureu i sam ne otključava CFSDS builder.
Target capture se ne koristi za izbor.

TASK-018 isporuka: poređeni su isti case-manifest/input hashovi, fuel/FBP, weather/FWI,
početni front i 20×20 domen. Sačuvani postojeći grids analizirani su na fiksnih 30–1.440
simuliranih minuta; potvrđeni su različiti završni uslovi i rani rubni kontakt. Uzrok
prekomjernog rasta nije izolovan jer suppression status i intradnevni ground truth
nedostaju, a vrijeme širenja zavisi od slučaja. Ne mijenjati validation/test ciljeve niti
PPO težine. Vidjeti `docs/research/CFSDS_NO_ACTION_DIAGNOSIS.md` i
`reports/real-fire-data/cfsds-no-action-timeline.json`.

TASK-004c je implementiran: probe horizon računa iz redova vremena; C++ završetak šalje
`weather_horizon`, `front_extinguished`, `grid_exhausted` ili `no_ignition`, aktivni front,
kumulativni affected i treated ID-jeve. Python brojač se na terminalnom receiptu uskladi
sa C++ izvorom istine. Grid-vs-terminal provjera dopušta samo razliku za ćelije koje su
istovremeno u C++ affected i treated skupovima; runtime dokaz je u
`reports/firehose-verification/task004c-adapter-smoke.json`. Batch pokriva 12 Sub20
inference slučajeva, ali svi su završili na weather horizon; ostale C++ terminal grane
još nisu potvrđene integracijskim slučajem.

TASK-017 je završen za početni historical state bridge. `InitialState.csv` prenosi ranije
opožarene ćelije (`burnt`) i više aktivnih front ćelija (`burning`). Fixture i stvarni
`2018_747` import/reset prošli su u C++; kumulativni damage/terminal receipt sada je
TASK-004c adapter isporuka.

TASK-016 sada ima tri FireCase konverzije i tri no-action train replaya (`2018_747`,
`2018_241`, `2018_1770`); za prvi je dodatno urađeno šest seedova. Sva tri odstupaju od
dnevnog CFSDS cilja, a predikcije dotiču rub modelskog prozora. `2014_538` je odbijen jer
neke historijske ćelije mapiraju na water/nonfuel. Suppression status ostaje nepoznat.
Prije RL benchmarka provjeriti gorivo, vrijeme, FBP parametre i extent; kalibraciju raditi
samo na train/calibration eventima.
C++ fixture je prvobitno reproducirao odbijanje `burnt` stanja na `NF` ćeliji; kasniji
EXP-015/ADR-025 dodali su i testirali eksplicitni `scar_nf` ugovor za izolovani adapter.
To ne odobrava godišnju fuel mapu niti CFSDS builder ulaz. Target-aware
front izbor je zamijenjen prototipom i testiran za target-mask invariance na `2018_747`;
shortlist screen pokazuje slabu prostornu podobnost za većinu trenutnih kandidata. Bounded
2–6 km domain audit je zabilježen u ADR-022/EXP-012; veća domena poboljšava target capture,
ali ne opravdava replay niti je izabrana. Puni target-independent day-pair i TRAIN screen
su zabilježeni u ADR-023/EXP-013; raniji 10/20 `PASS_FUEL_ONLY` odnosio se na stare izreze
i ne kvalifikuje nove parove. Slijede train-only FBP vintage/source provjera,
terrain/weather poravnanje i suppression dokazi prije preregistrovanog replaya.
