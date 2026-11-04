---
type: Environment Specification
title: Sintetičko CA trening okruženje s fizički ograničenim jedinicama (v1, 2026-11-04)
---
# Sintetičko CA trening okruženje (v1)

Status: **prijedlog i implementacija u toku**, grana `codex/synthetic-ca-training`.
Ovo je vlastiti, pojednostavljeni probabilistički cellular-automaton (CA) simulator.
Nije Cell2Fire, nije SimFire i nije fizički validiran. Odluka je zapisana u ADR-028.

## Zašto

Prethodni put (ADR-021 do ADR-027) trenirao je agenta na samim FEDS/LANDFIRE stvarnim
slučajevima kroz SimFire koji ne prolazi kalibracijski gate. Uz to, linija se pojavljivala
trenutno, u jednom 12h koraku, bez jedinice koja se kreće i gradi liniju određenom brzinom.
Trening na stvarnim slučajevima, uz teleportaciju resursa i nekalibriran simulator, ne
dozvoljava tvrdnju da je agent naučio nešto prenosivo.

## Podjela podataka (činjenica u kodu, ne preporuka)

| Uloga | Izvor | Sjeme / slučajevi |
|---|---|---|
| Trening | proceduralno generisani pejzaži i vrijeme | seed ≥ 1 000 000 |
| Validacija tokom treninga | isti generator, fiksni skup | seed 0–255 |
| Završni test | 119 lokalnih FEDS slučajeva (99 bivši TRAIN + 20 bivši VALIDATION) | samo nakon zaključavanja politike |

Stvarni rasteri se nikad ne koriste kao predlošci za trening. Generator koristi vlastite,
dokumentovane priore za udio goriva, ne histogram stvarnih slučajeva. TEST 2024 ostaje
zatvoren dok ga korisnik izričito ne otvori.

## Šta "test na stvarnim podacima" znači

Stvarni požari nisu imali agenta, pa učinak intervencije na njima nije opservabilan. Test
koristi stvarni pejzaž (FBFM13 gorivo, LANDFIRE elevacija), stvarno gridMET vrijeme i
stvarni početni FEDS perimetar, a širenje se računa **ovim** simulatorom. Agent se poredi s
no-op i heurističkim politikama na istim slučajevima, istim resursima i istim slučajnim
brojevima. Zasebna dijagnostika poredi no-op rast u simulatoru s opaženim FEDS rastom
(12h–48h). To je jaz kalibracije; prijavljuje se, ne koristi se kao gate.

## Simulator

- Mreža ćelija od 180 m, isto kodiranje goriva kao LANDFIRE FBFM13 (1–13, 91–99).
- Unutrašnji korak 2 min, odluka agenta svakih 30 min (15 unutrašnjih koraka).
- Stanja ćelije: neizgorjelo, gori (s preostalim vremenom gorenja), izgorjelo.
  Kumulativna šteta se nikad ne briše. Linija je zaseban sloj i ne briše štetu.
- Vjerovatnoća paljenja od jednog gorućeg susjeda: `p = 1 − exp(−R·Δt / d)`, gdje je `R`
  usmjerena brzina širenja, a `d` udaljenost centara (180 m ili 254.6 m dijagonalno).
  Paljenje od više susjeda: `1 − Π(1 − p_j)`.
- `R = R0(gorivo) · f_vjetar · f_nagib · f_vlaga`. `R0` je tabelarna brzina Anderson (1982)
  za svaki FBFM13 model. Faktori vjetra i nagiba su po obliku Alexandridis et al. (2008),
  normalizovani na referentni vjetar tabele. Izvori i brojevi su u `synthetic_ca.py`.
- Vrijeme gorenja ćelije zavisi od grupe goriva (trava kratko, drvna masa dugo).
- Rijetko paljenje iskrama niz vjetar, tako da linija nije apsolutno neprobojna.
- Urbane ćelije (91) su **prioritetna imovina**: mogu se zapaliti od susjeda uz manju
  vjerovatnoću, a u nagradi nose veliku težinu. Voda (98) je neprohodna i negoriva.
- Slučajnost dolazi iz brojača po (sjeme epizode, unutrašnji korak). Agentova i no-op
  rollout zato dijele iste slučajne brojeve (common random numbers).

## Resursi i fizička ograničenja

- Konačan broj jedinica po epizodi (2–6), dvije vrste: ručna ekipa od 20 ljudi i dozer.
- Jedinice stižu s udaljenosti od požara i u različito vrijeme; ne nastaju niotkud.
- Kretanje i gradnja koriste akumulator napretka u metrima. Jedinica pređe ćeliju tek kad
  skupi dovoljno metara po brzini kretanja. Linija u ćeliji je gotova tek kad skupi dužinu
  ćelije po brzini gradnje (ADR-025: ručna ekipa ≈ 1.26 km po smjeni od 12h).
- Dozer ne radi iznad graničnog nagiba. Nijedna jedinica ne ulazi u ćeliju koja gori ili
  je izgorjela tokom trajanja vatre, niti u vodu.
- Ako vatra zahvati ćeliju u kojoj je jedinica, jedinica je izgubljena i nagrada dobija
  veliki negativan iznos. Ljudski život uključuje i vatrogasce.
- "Stani" je uvijek dozvoljeno; nestanak resursa ne završava epizodu.

## Akcije i opažanje

- `MultiDiscrete([17] × 6)`: po jedinici `stani`, `kreni u smjeru 1–8`, `gradi liniju i
  napreduj u smjeru 1–8`. Neaktivni slotovi i nedozvoljeni potezi su maskirani.
- Mapa: 128×128 ćelija (23 km). Opažanje je mapa 64×64 (2×2 pooling), kanali: gorivo po
  grupi, gori, izgorjelo, linija, urbano, nagib, i položaj svake jedinice. Uz mapu ide
  vektor po jedinici: lokalni prozor 5×5 u punoj rezoluciji, vrsta, napredak i dostupnost.
  Globalno: vjetar, vlaga, vrijeme, broj jedinica.

## Nagrada

Korisnikova intuicija je da nagrada raste kad agent smanji brzinu rasta požara (ha po
jedinici vremena), a da se kazni kad rast ostane isti ili poraste. Doslovna formula
"promjena stope rasta" se teleskopira: zbir po epizodi je krajnja minus početna stopa, pa
ignoriše ukupnu izgorjelu površinu i nagrađuje prirodno gašenje. Zato je osnovna nagrada
kontrafaktualna:

`r_t = (D_noop,t − D_agent,t) / skala − kazne`

`D_x,t` je težinski broj novoizgorjelih ćelija u koraku `t` (vegetacija 1, urbano 50).
No-op rollout se računa na istim slučajnim brojevima. Agent dobija pozitivnu nagradu kada
uspori rast u odnosu na ono što bi se desilo bez njega, nula kada ga ne mijenja, a
negativnu ako ga ubrza. Zbir po epizodi je ukupna sačuvana težinska površina. Doslovna
"trend" nagrada ostaje opcija `reward_mode="growth_trend"` za ablaciju.

## Trening i validacija

- MaskablePPO (sb3-contrib 2.7.1), 8 paralelnih okruženja, CNN nad mapom.
- Kurikulum: kraći horizonti i manji početni požari, zatim duži (12h do 48h).
- Validacija na fiksnih 64–256 sintetičkih sjemena nakon svakog bloka treninga. Čuva se
  najbolji checkpoint po validaciji. Iste postavke važe za heuristike.
- Glavna metrika: udio sačuvane težinske štete u odnosu na no-op, uz izgubljene jedinice.
