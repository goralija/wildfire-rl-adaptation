---
type: Integration Plan
title: Sažeta integracija SimFire i CA jezgre
---
# Manja grana za integraciju

## Opseg prije izmjena — 2026-11-24, ADR-058

Korisnik traži da izbacimo maksimalno nerelevantnih promjena. Istraživačka grana
`codex/separate-clip-pilot` na `c4062a84` ostaje sačuvana. Nova
`codex/ca-core-integration` polazi direktno iz `origin/main=f96f744f`.
Glavni klon i postojeći lokalni podaci/modeli se ne prepisuju.

**Pretpostavka:** za merge trebaju radni interfejsi i provjerene ispravke; historija
svake optimizer probe i sve per-case tabele ne trebaju biti dio integracijskog diffa.
**Provjerljivi cilj:** oko50fajlova i nekoliko hiljada dodanih redova, umjesto
228fajlova/345.775redova. Stara grana ima324.652dodanih redova u83report fajla.

Ostaju: TRAIN-only weather filtriranje, sigurna inicijalizacija output direktorija,
kategorijsko/lokalno/terrain opažanje i nonfuel maska, zajednička B1 akcija/nagrada,
CA bridge, osnovni MaskablePPO/numeric NPZ interfejs i relevantni regresijski testovi.
Native CA opservacijski ugovor ostaje kao priprema daljeg rada, bez tvrdnje o parity.

Izostaju: offline model pretrage, centrirani reward i zasebni clipping eksperimenti,
njihovi runneri/plot/bundle alati, velike tabele i duplirani startup/status zapisi.
Oni ostaju na arhivskoj grani i u njenom `.local` prostoru. Modeli se ne promoviraju.

Zavisnost encoder-a od starih offline learnera uklanja se izdvajanjem samo postojećeg
terrain536 zapisa. Prije predaje traži se identičnost njegovih vrijednosti sa
sačuvanim v2 opažajima, puni testovi, synthetic i native smoke, knowledge checker
i mali provenance sažetak. Originalni simulatori, četiri odluke, no-op i kumulativna
šteta ostaju isti. TEST2024 i novi VALIDATION/futureFEDS ostaju zatvoreni.

## Status

Plan izdvajanja je zapisan prije implementacije. Trening TASK-046 je završio za
18,49min bez greške; prikazani finalni procenti još čekaju završnu lokalnu provjeru.
Ova faza ne otvara novi optimizer test. Poslije provjera slijedi review manje grane.
