# Kriteriji prihvata i trag zahtjeva

| ID | Provjerljivi kriterij | Veza | Zadatak |
| --- | --- | --- | --- |
| AC-001 | README vodi do statusa, protokola, rubrike i odluka | G-003, FR-001 | TASK-001 |
| AC-002 | budget=0 dozvoljava samo no-op; B potrošen ne završava požar | FR-002, BR-001..004 | TASK-002 |
| AC-003 | ugašena ranije gorjela ćelija ostaje šteta; priority frakcija provjerena ručno | FR-003, BR-005..007 | TASK-002 |
| AC-004 | ponovljeni config daje iste metrike; policy RNG ne mijenja fire RNG | FR-004, BR-009 | TASK-003 |
| AC-005 | run daje CSV/manifest/SVG i odbija postojeći folder | FR-005, NFR-002..003 | TASK-003 |
| AC-006 | pinned Firehose model izvrši inference u obnovljivom environmentu | FR-006 | TASK-004 |
| AC-007 | najmanje 3 trening seeda, frozen i tuned na istim test scenarijima/B | G-001, FR-007 | TASK-005..006 |
| AC-008 | oba gubitka i tradeoff sa/bez priority prilagodbe | G-002, FR-008 | TASK-007 |

Bootstrap Done: AC-001..005, dokazi testova/pilota, private ignorisan, source audit,
jasno navedena neispunjena AC-006..008 i handoff. Optional modern RL smoke nije AC-006.
Glavni projekt Done: simulator gate, potpuno reproducibilni glavni eksperimenti,
interpretacija/ograničenja, poster i dokumentovani doprinosi tima.
Open Questions: profesorov krajnji rok i eventualni dodatni formalni uslovi predaje.
