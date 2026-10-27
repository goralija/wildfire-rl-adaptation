# Zahtjevi

| ID | Zahtjev | Faza | Prihvat |
| --- | --- | --- | --- |
| FR-001 | trajna baza zahtjeva, izvora, odluka i statusa | sada | AC-001 |
| FR-002 | eksplicitni budžet, cijena i no-op, bez ranog kraja | sada | AC-002 |
| FR-003 | kumulativna ukupna i prioritetna šteta | sada | AC-003 |
| FR-004 | iste realizacije i budžeti za baseline poređenja | sada | AC-004 |
| FR-005 | CSV, manifest i označena vizualizacija | sada | AC-005 |
| FR-006 | učitavanje izvornog pretrained agenta | glavni rad | AC-006 |
| FR-007 | fine-tuning i poređenje s frozen modelom | glavni rad | AC-007 |
| FR-008 | prioritetni kompromis i ablation | poslije glavnog minimuma | AC-008 |

NFR-001: core nema trećih Python zavisnosti. NFR-002: novi izlaz ne prepisuje stari.
NFR-003: manifest sadrži config/source hash, Git i environment. NFR-004: privatni podaci
ne ulaze u Git. NFR-005: izvještaj jasno odvaja izvršeno i planirano.

Priča: kao član tima želim ponoviti isti scenario i razumjeti svaku razliku u rezultatima.
Open Questions: potvrditi glavni compute cap i konačan broj scenarija.
