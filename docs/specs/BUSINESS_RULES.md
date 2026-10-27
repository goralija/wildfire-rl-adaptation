# Pravila i metrike

BR-001: B je nenegativan cijeli broj; validna nova intervencija košta 1.
BR-002: no-op uvijek vrijedi, ništa ne troši, ali požar napreduje.
BR-003: iscrpljen B ne znači done. Aktivni požar se prati do kraja ili horizonta.
BR-004: validne ćelije su FUEL/FIRE, bez NONFUEL/BURNED/TREATED i ponavljanja.
BR-005: svi ever-burned ostaju u šteti, uključujući zapaljene prije prvog poteza.
BR-006: broj početno gorivih ćelija je fiksan imenilac; ne smanjuje se tretmanom.
BR-007: priority gubitak je presjek ever-burned i gorive priority maske / veličina maske.
BR-008: terminated = nema FIRE; truncated = dostignut horizont uz FIRE.
BR-009: iste informacije, mapa, ignition, weather, simulator seed, tempo i B za kontrole.
BR-010: nema prepisivanja izlaznih run direktorija.

Pilot reward je negativna novonastala opožarena frakcija minus lambda puta nova
priority frakcija. Početna šteta je dio metrike, iako je nastala prije prve nagrade.
Pilot nema vjetar, teren, spot fires, vlage ili realistične resurse. Četiri susjeda;
samo stare FIRE ćelije šire u jednom koraku; gorenje traje `burn_duration` koraka.

Strogi core odbija invalidnu akciju bez mutacije. Gym adapter je pretvara u kažnjeni
no-op i prijavljuje `invalid_action=True`, radi standardnih random-action checkera.
MaskablePPO mora koristiti masku pri train i predict; maskirane akcije ne treba slati.

Open Questions: zadržati Firehose harvest i njegov action timing ili opravdati izmjenu.
