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
- Unutrašnji korak 2 min, odluka agenta svakih 60 min (30 unutrašnjih koraka).
- Stanja ćelije: neizgorjelo, gori (s preostalim vremenom gorenja), izgorjelo.
  Kumulativna šteta se nikad ne briše. Linija je zaseban sloj i ne briše štetu.
- Vjerovatnoća paljenja od jednog gorućeg susjeda: `p = 1 − exp(−k·R·Δt / d)`, gdje je
  `R` usmjerena brzina širenja, `d` udaljenost centara (180 m ili 254.6 m dijagonalno), a
  `k = 0.31` kontaktna kalibracija. Paljenje od više susjeda: `1 − Π(1 − p_j)`.
- `R = R_bezvjetra · (1 + φ(U)·h(θ)) · f_nagib · f_vlaga · f_dan`.
  - `R_bezvjetra` je izveden tako da čelo pri 5 mi/h (2.24 m/s) srednjeg vjetra plamena
    daje Anderson (1982) tabelu.
  - `φ(U) = φ_ref·(U/U_ref)^1.5`, `h(θ) = ((1 + cos θ)/2)²` (čelo 1, bok 0.25, začelje 0).
  - `f_nagib = exp(0.078·nagib°)` (oblik Alexandridis et al. 2008), ograničeno na ±25°.
  - Vlaga je linearno prigušenje: 1 pri 8%, 0 pri pretpostavljenih 30%. Dnevni ciklus je
    0.3 noću do 1.0 u rano poslijepodne.
  - `φ_ref` po grupi (trava 10, grmlje 6, šuma i otpad 4), vlaga ekstinkcije i dnevni ciklus
    su pretpostavke, ne fitovane vrijednosti.
- Kalibracija `k` je mjerena na ravnim linijskim požarima pri referentnom vjetru. Nakon nje
  emergentna brzina čela za FBFM 1, 2, 4, 5, 8 i 10 odstupa od tabele najviše 12%.
- Vrijeme gorenja ćelije: minimalno trajanje po grupi (trava 30, grmlje 60, šuma 180,
  otpad 240 min; pretpostavka) plus vrijeme prelaska ćelije bez vjetra, najviše 12h.
- Rijetko paljenje iskrama niz vjetar, tako da linija nije apsolutno neprobojna.
  Dijagonalni prelaz između dvije ortogonalno susjedne ćelije linije je blokiran.
- Urbane ćelije (91) su **prioritetna imovina**: pale se sporo od susjeda (pretpostavka
  1.5 m/min) i u nagradi nose težinu 50. LANDFIRE 91 je razvijeno zemljište (uključuje i
  puteve), pa je ovo gruba zamjena za prisustvo ljudi. Voda (98) je neprohodna.
- Slučajnost je counter-based hash po (sjeme epizode, unutrašnji korak, ćelija, namjena).
  Agentova i no-op rollout zato dijele iste slučajne brojeve (common random numbers).
- Brzina: oko 40 odluka/s po procesu na 128×128.

## Resursi i fizička ograničenja

| Jedinica | Kretanje | Linija (ch/h, primjeri) | Ograničenje | Izvor |
|---|---|---|---|---|
| Ručna ekipa, 20 ljudi (Type II) | 3 km/h van staze, usporenje na nagibu | FM1 18, FM2 16, FM8 5, FM9 16, FM10 4 | nema | PMS 410-1 App. A p. A-30; Sullivan et al. 2020 |
| Dozer (Type II) | 2.5 km/h (pretpostavka) | FM1–2 105, FM4 47.5, FM8 87.5, FM10 15 | ≤45% nagiba; ×0.6 na 26–40%, ×0.3 iznad | PMS 410-1 p. A-34 |

- Konačan broj jedinica po epizodi (2–4), dvije vrste. Jedinice stižu tokom prva 3h,
  2–4 km od požara, na mjesto koje tad ne gori.
- Kretanje i gradnja koriste akumulator napretka u metrima. Jedinica pređe ćeliju tek kad
  skupi dovoljno metara. Linija u ćeliji je gotova kad se izgradi 180 m linije.
- Jedinica ne ulazi u ćeliju koja gori niti u vodu, a izgorjelu ("crnu") površinu smije.
- **Sigurnost (LCES):**
  - Kad je vatra na ≤2 ćelije, jedinica automatski bježi pretragom u širinu prema
    najbližem sigurnom mjestu: crno, negorivo, linija ili ≥5 ćelija od vatre. Bijeg ide
    do 2 ćelije po 2 min (pretpostavka: dijelom vozilom).
  - Ako vatra ipak zahvati ćeliju jedinice, a susjedna ćelija je otvorena, to je bliski
    susret: jedinica se izmješta, uz kaznu 0.1.
  - Ako je jedinica okružena, to je zarobljavanje: jedinica je izgubljena, uz kaznu 1.0,
    što je jednako gubitku cijele sačuvane površine epizode.
  - Pravilo sigurnosne zone (4× visina plamena; Butler & Cohen 1998) je ispod rezolucije
    od 180 m.
- "Stani" je uvijek dozvoljeno; nestanak resursa ne završava epizodu.

## Akcije i opažanje

- `MultiDiscrete([17] × 4)`: po jedinici `stani`, `kreni u smjeru 1–8`, `gradi liniju i
  napreduj u smjeru 1–8`. Neaktivni slotovi i nedozvoljeni potezi su maskirani. Slotovi su
  poredani: dozeri pa ručne ekipe, svaki po vremenu dolaska.
- Mapa 128×128 ćelija (23 km). Opažanje je 64×64 (2×2 pooling) sa 13 kanala: gori,
  izgorjelo, linija, urbano, brzina goriva, negorivo, voda, nagib, elevacija i položaj svake
  jedinice. Uz mapu ide vektor po jedinici: lokalni prozor 15×15 u punoj rezoluciji (gori,
  izgorjelo, blokirano), vrsta, napredak, dolazak i pomak do najbliže vatre i naselja.
  Globalno: vjetar, vlaga, doba dana, vrijeme epizode, broj aktivnih jedinica.

## Nagrada

Korisnikova intuicija je da nagrada raste kad agent smanji brzinu rasta požara (ha po
jedinici vremena), a da se kazni kad rast ostane isti ili poraste. Doslovna formula
"promjena stope rasta" se teleskopira: zbir po epizodi je krajnja minus početna stopa, pa
ignoriše ukupnu izgorjelu površinu i nagrađuje prirodno gašenje. Zato je nagrada
kontrafaktualna:

`r_t = (D_noop,t − D_agent,t) / max(W_noop, 20) − 1.0·izgubljene − 0.1·bliski susreti`

- `D_x,t` je težinski broj novoizgorjelih ćelija u satu `t` (vegetacija 1, urbano 50).
- No-op rollout se računa jednom pri resetu, na istim slučajnim brojevima.
- Povrat epizode je udio sačuvane težinske štete.
- Oba rollouta nastavljaju 12h nakon horizonta, s linijama koje ostaju. Samo odgađanje
  vatre zato ne donosi nagradu.
- Ako agentova vatra ranije potpuno stane, ostatak no-op štete se odmah pripisuje.

## Generator epizoda

- Pejzaž: fraktalna elevacija (reljef 30–1200 m), režim goriva (travnjak, grmlje, šuma,
  miješano; vlastiti prior), rijeke, poljoprivreda u dolinama, golo na vrhovima i 0–4
  naselja.
- Vrijeme: 10 m vjetar ~ lognormal oko 4 m/s, dnevni ciklus, smjer kao slučajni hod,
  WAF 0.1–0.5. U 50% epizoda vrijeme je u 12h blokovima kao gridMET.
- Početak: paljenje u središnjoj trećini, slobodan rast 2–12h, zatim isto pravilo
  (`scar`, `front`) → stanje kao za stvarne slučajeve.
- Randomizacija domena: `spread_scale` log-uniformno 0.3–1.2, stopa iskri 0–4·10⁻⁴.
- Epizode u kojima no-op doda manje od 30 ćelija (≈100 ha) ponovo se uzorkuju (do 16
  pokušaja), jer ne nose signal. Prije ovog pravila medijan rasta je bio 15 ćelija.

## Trening i validacija

- MaskablePPO (sb3-contrib 2.7.1), 6 paralelnih okruženja, NatureCNN nad mapom i MLP
  nad vektorima (`scripts/train_synthetic_ppo.py`).
- Kurikulum: faza A (horizont 12–24h, 2–3 jedinice), zatim faza B (12–48h, 2–4).
- Validacija na fiksnim sintetičkim sjemenima nakon svakog bloka treninga. Čuva se
  najbolji checkpoint po validacijskom povratu. Iste postavke važe za heuristike
  (`scripts/evaluate_synthetic_policies.py`).
- Glavna metrika: udio sačuvane težinske štete u odnosu na no-op, uz izgubljene jedinice
  i bliske susrete.

## Heurističke politike (osnova za poređenje)

Kod je u `src/wildfire_rl/synthetic_heuristics.py`. Heuristike vide samo ono što je i u
opažanju agenta: trenutnu vatru, liniju, gorivo, jedinice i trenutni vjetar. Ne vide
no-op rollout niti buduće vrijeme.

| Politika | Šta radi (svaki sat, za svaku jedinicu) |
|---|---|
| `noop` | sve jedinice stoje; automatsko povlačenje i dalje važi |
| `random` | nasumična dozvoljena akcija |
| `direct_flank` | prilaz na 3 ćelije (~540 m) od najbliže goruće ćelije, zatim gradnja linije tangencijalno oko požara, okrenuto prema strani niz vjetar; pola jedinica ide u jednom, pola u drugom smjeru |
| `downwind_indirect` | linija poprečno na vjetar, 8 ćelija ispred čela, jedinice raspoređene bočno |
| `protect_urban` | prsten linije 2 ćelije oko najugroženijeg naselja; bez ugroženog naselja ponaša se kao `direct_flank` |

### Porijeklo heuristika (napomena za dokumentaciju)

- **Autorstvo.** Heuristike je napisao Claude za ovaj projekat (2026-11-04) kao osnovu
  za poređenje. Nisu preuzete iz rada, biblioteke ni validiranog algoritma.
- **Inspiracija.** Labavo prate standardne taktike gašenja šumskih požara, po opštem
  znanju: direktni napad po boku od sidrišta prema čelu, indirektni napad linijom ispred
  čela i zaštitu objekata.
  - Opisi taktika **nisu provjereni u doktrinarnom izvoru** (npr. NWCG IRPG PMS 461,
    Fireline Handbook PMS 410-1). Iz PMS 410-1 su uzete samo brzine gradnje linije.
  - Slična "downwind" heuristika postojala je u ADR-025, ali je ova napisana iznova.
- **Parametri.** Odstojanje 3 ćelije, 8 ćelija ispred čela, prsten 2 ćelije i sva
  geometrija su vlastiti izbor. Nisu podešavani ni kalibrisani.
- **Kako ih predstaviti.** Kao jednostavne, ručno pisane, fiksne baseline-ove, ne kao
  "ono što bi vatrogasci uradili". Ako ih rad predstavi kao doktrinarne taktike, prvo
  treba provjeriti i navesti izvore te uskladiti opise.

### Uloga heuristika i značenje rezultata

- **Prostor za poboljšanje.** Heuristike prvo pokazuju da agent u okruženju uopšte može
  nešto promijeniti. To je headroom gate u ADR-028: najbolja taktika mora sačuvati
  ≥ 5%, uz 95% CI razlike prema nasumičnoj politici iznad 0.
- **Rezultat gate-a v4** (sjemena 0–127, puni kurikulum):

  | Politika | Prosjek sačuvano | Medijan | Izgubljene jedinice |
  |---|---|---|---|
  | random | 1.5% | 0% | 0 |
  | direct_flank | 11.6% | 1.6% | 0 |
  | protect_urban | 8.9% | 0.1% | 0 |
  | downwind_indirect | 4.0% | 0% | 3 |

  - "Sačuvano" je prosjek udjela težinske štete sačuvane u odnosu na isti požar bez
    intervencije, na istim slučajnim brojevima.
  - Medijan je mnogo niži od prosjeka. Na većini požara ni najbolja taktika ne mijenja
    mnogo; prosjek vuče manji broj požara (često sporijih) na kojima linija stigne.
  - Ključ za mjesto okupljanja jedinica kasnije je promijenjen (ponovna upotreba
    požara u treningu). Heuristike se zato ponovo mjere na konačnom okruženju i na
    sjemenima 0–255, zajedno s agentom.
- **Ljestvica za agenta.** Heuristike su fiksna pravila: rade isto bez obzira na gorivo,
  vjetar, teren, vrstu i dolazak jedinica ili blizinu naselja. Agent treba naučiti da se
  prilagođava situaciji, pa ga prihvatamo samo ako na validaciji pobijedi **najbolju**
  heuristiku (paired 95% CI iznad 0) i ne gubi više jedinica od nje.
- **Šta ishod znači.**
  - Ako agent ne pobijedi heuristike, nije naučio ništa korisnije od jednostavnog pravila.
  - Ako ih pobijedi, to pokazuje da je bolji od *ovih* jednostavnih pravila u *ovom*
    simulatoru. To nije dokaz da je bolji od iskusnih vatrogasaca: heuristike nisu
    podešavane ni provjerene s praksom, pa je ljestvica relativno niska.
- **Moguća stroža poređenja kasnije:**
  - heuristike s parametrima podešenim na validacijskim sjemenima;
  - "oracle" koji za svaki požar naknadno uzme najbolju heuristiku. Pobjeda nad njim
    pokazala bi da agent bira taktiku prema situaciji.
