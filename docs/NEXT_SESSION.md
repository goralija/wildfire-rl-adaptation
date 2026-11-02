---
type: Handoff
title: SimFire benchmark — nastavak nakon FEDS crosswalk gatea
---
# Naredna sesija

## Trenutno stanje — 2026-11-03

Aktivna korisnička odluka je novi agentni benchmark u SimFireu, sa stvarnim
FPA-FOD uslovima, FEDS-CONUS vremenskim obodima i ograničenim FLE/ICS-209 kontekstom.
Radi se u izolovanom worktreeu iz `main`:
`.worktrees/fireline-simfire-benchmark`, grana `codex/fireline-simfire-benchmark`.
Glavni checkout ima tri tuđe necommitovane izmjene, a stara research grana je sačuvana;
nijedna nije mijenjana ni masovno prenesena.

Crosswalk audit nije preuzeo godišnje FEDS fajlove. Konačni strogi kriterij traži da
najraniji FEDS obod unutar 3 km od FPA-FOD tačke bude zabilježen od `t_st` do `t_st`
+24 h, uz FEDS datum `t_st` u prozoru -1/+2 dana od FPA discovery datuma. Rezultat je
13/40 train i 7/20 validation sa jedinstvenim događajem i ≥2 uzastopna 12h stanja;
prag 20/8 **pada u oba splita**. Validation dio je tačno postfiltriran iz sačuvanih
kandidatskih vremenskih sažetaka jer Zenodo DNS nije bio dostupan pri nastavku; nema
nove mrežne provjere validation izvora.

FLE spajanje postoji za 13/20 validation slučajeva, ali za 0/40 train slučajeva jer
njihovi FPA ID formati nemaju odgovarajući WFIGS IRWIN ID u direktnom joinu. ArcGIS
FLE rezultat je incidentni grupisani sažetak, ne linijska geometrija. Test nije učitan.
Nema SimFire porta, no-op kalibracije, PPO treninga ni agentnih rezultata.

## Artefakti i izvori

- [Odluka i detaljna metodologija](research/FPA_FEDS_CROSSWALK.md)
- [Kombinovani crosswalk rezultat](../reports/real-fire-data/fpa-feds-fle-crosswalk-v1.json)
- [Train detalji](../reports/real-fire-data/fpa-feds-fle-crosswalk-train-v1.json)
- [Validation kandidati prije strogog filtera](../reports/real-fire-data/fpa-feds-fle-crosswalk-validation-candidate-search-v1.json)
- [Validation detalji](../reports/real-fire-data/fpa-feds-fle-crosswalk-validation-v1.json)
- [Train/validation cohort manifest](../data/manifests/fireline-benchmark-cohort-v1.json)
- [Izvori i istraživački nalazi](research/SOURCES.md)
- [Aktivna odluka ADR-017](specs/DECISION_RECORDS.md)

## Sljedeći korak

Ne popuštati ni mijenjati join pravilo nakon rezultata. Pripremiti novu, eksplicitnu
prijedlog-kohortu za train/validation koja primjenjuje isti fiksni kriterij i zadržava
test 2024 zatvoren. Ne koristiti završne obode ili FLE ishode pri izboru kandidata.
Ako se pragovi 20/8 ne mogu ispuniti u unaprijed dozvoljenim splitovima, vratiti
korisniku alternative (druga unaprijed odabrana kohorta ili izvor) prije simulator rada.

Tek nakon prolaza novog data gatea:

1. Selektivno prenijeti provjereni SimFire adapter i scenario ugovor, bez 133k linija
   CFSDS izvještaja/generisanih artefakata.
2. Importovati opaženi FEDS stanje za svaku odluku: istorijski opožarena unutrašnjost,
   aktivni front i 180m/256×256 strateška karta. Vrijeme ide u 12h koracima, horizont
   je fiksnih 48h.
3. Izvršiti no-op poređenje sa persistence i jednostavnom elipsnom referencom. Provjeriti
   dodatnu opožarenu površinu, rub mape i pristranost oblika. Opaženi završni obod je
   samo post-hoc evaluacija; simulator se nastavlja i nakon njega i nakon praznog budžeta.
4. Ako no-op gate ne prođe, zaustaviti agentni rad. Kalibrisati mali broj zajedničkih
   parametara samo na trainu, izabrati na validationu, zaključati prije testiranja.
5. Zatim implementirati i testirati liniju koja se gradi tokom vremena, budžet
   0/1/2/4 smjena, 20 ljudi × 8h, sektore fronta/čekanje i precizno računovodstvo.
   Sve politike dobijaju isti scenario, seedove, budžet, trajanje i informacije.
6. Nakon mjerenja vremena kratkih rollouta tek odlučiti o PPO treningu. Test split
   koristiti samo za završni izvještaj.

## Istorijska putanja

Stari [CFSDS/Cell2Fire rad](../data/manifests/cfsds-v1_1-pilot-cohort.json) i njegovi
replayi ostaju u repou kao odvojeni nalazi. Oni nisu SimFire benchmark niti zamjena za
pre-agent FEDS gate.

## Provjere pred predaju

Pokrenuti ciljane crosswalk testove, cijeli `PYTHONPATH=src python3 -m unittest discover -s tests -v`,
synthetic CLI smoke i `python3 scripts/validate_knowledge.py --strict`; provjeriti
`git diff --check`. Ne instalirati pakete globalno, ne pokretati dugo/plaćeno treniranje,
ne pushati/mergovati i ne objavljivati sirove podatke ili težine.
