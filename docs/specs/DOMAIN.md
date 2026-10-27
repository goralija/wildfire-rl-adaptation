# Pojmovi i životni ciklus

Ćelija: indeks `row * cols + col`, od nule, konstantna prostorna jedinica u istoj mapi.
Synthetic-v1 stanja: FUEL=0, FIRE=1, BURNED=2, TREATED=3, NONFUEL=4.
Scenario: layout, ignition, prioritetna maska, parametri širenja, warmup i horizont.
Realizacija: scenario + simulator seed. Politika ima zaseban RNG.
Intervencija: trajni idealizovani tretman jedne FUEL/FIRE ćelije, cijena 1.
Budget B: maksimalni zbir intervencija tokom cijele epizode; nije broj timestepova.
No-op: indeks N, bez troška. Firehose legacy koristi drugačiji no-op kontrakt.

Reset -> ignition -> unaprijed zadani warmup bez intervencija -> action ->
sinhrono širenje -> opažanje; kraj kada nema aktivnog požara, ili truncation na horizontu.
Sva ikad zapaljena mjesta ostaju u `ever_burned`; broj aktivnih ćelija nije konačna šteta.
Gym opažanje uključuje stanja, burn age, kumulativnu štetu, priority masku, početni i
preostali budžet i vrijeme. Ovo nije opažanje starog Firehose modela.

Open Questions: fizička površina ćelije i vremenska jedinica za glavni backend.
