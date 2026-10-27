# Naredni zadaci

Napor je okvirni agentov prijedlog u aktivnim radnim satima, bez roka i dodjele članovima.

| ID | Prioritet / stanje | Isporuka i provjera | Napor |
| --- | --- | --- | --- |
| TASK-001 | P0 završeno | znanje, izvori, rubrika, specs, status; AC-001 | bootstrap |
| TASK-002 | P0 završeno | synthetic budžet/no-op/damage + testovi; AC-002..003 | bootstrap |
| TASK-003 | P0 završeno | paired baselines, manifest/CSV/SVG, replay; AC-004..005 | bootstrap |
| TASK-004 | P0 prvo sljedeće | Firehose gate, build+seed+checkpoint inference; AC-006 | do 4 h |
| TASK-004b | P0 uslovno | SimFire fallback spike ako gate padne; novi ADR | 2–4 h |
| TASK-005 | P1 nakon gatea | budžetski adapter + frozen benchmark + cijena 10 rollouta | 3–6 h |
| TASK-006 | P1 | 3 training seeda, fine-tuning po B, matched controls, hierarchical CI; AC-007 | zavisi od mjerenja |
| TASK-007 | P1 nakon minimuma | priority weight ablation, ukupna vs priority šteta; AC-008 | 4–8 h + compute |
| TASK-008 | P2 | joint budget features/weight transfer i ablation bez njih | samo uz prostor |
| TASK-009 | P1 predaja | glavni grafikoni, poster, interpretacija i usmeni | 4–8 h |

Dependency: 001→002→003→004→005→006→007→009; 004b samo nakon dokumentovanog FAIL.
Odmah planirati mape/weather licences i test split tokom TASK-004, bez velikih preuzimanja.
Nema obaveze implementacije svakog proširenja: glavni minimum i kvalitet evaluacije imaju prednost.
