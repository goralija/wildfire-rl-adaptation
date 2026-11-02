---
type: Project Status
title: Status — stvarni FPA-FOD požari, LANDFIRE i SimFire
sources:
  - resource: /docs/research/SIMFIRE_FPA_COHORT.md
  - resource: /docs/research/SIMFIRE_RL_ADAPTER.md
  - resource: /docs/research/EXPERIMENT_LOG.md
  - resource: /docs/specs/DECISION_RECORDS.md
---
# Gdje smo sada

## Cilj, najjednostavnije

Napraviti agenta koji u istoj simulaciji postavlja vatrogasne linije, pa uporediti početnog
agenta i agenta koji je dodatno učio na različitim požarnim okruženjima. Okruženja počinju
od stvarnih požarnih lokacija i stvarnih mapa goriva/terena. SimFire stvara iskustva i
nagradu. Ne tvrdimo da je simulator dokazao koliko bi stvarni požar bio manji.

## Stvarno završeno

- **80 stvarnih požara je izabrano iz službene USFS FPA-FOD baze.** Podjela po cijelim
  požarima: 40 train (2018–2019), 20 validation (2023), 20 test (2024). Filter je veliki
  požar od najmanje 5.000 acres, jedna od 10 zapadnih država, poznat datum/lokacija i MTBS
  ID samo za kasniji vizualni kontekst. Konačna površina/perimetar ne ulaze agentu u mapu
  ni reward. [Opis kohorte](research/SIMFIRE_FPA_COHORT.md), [manifest](../data/manifests/simfire-fpa-fod-cohort-v2.json).
- **Za svih 80 požara postoje stvarne karte goriva i terena.** Preuzeti su LF2016 ili
  LF2022 FBFM13 prema godini i LF2020 elevation. Svaki raster je 128×128 ćelija od 30 m;
  CRS, granice, dimenzija, kodovi i SHA-256 su sačuvani i provjereni. Raw TIFF fajlovi su
  u ignorisanom `.local/simfire-cohort-v2/`, nisu u Gitu.
- **Početna ćelija je definisana za svih 80.** U 71 slučaju prijavljena tačka je već u
  gorivoj ćeliji; u 9 se koristi najbliža goriva ćelija, najviše oko 62 m dalje. Pravilo
  gleda samo kartu goriva prije događaja, nikad završni obod. [Izvještaj](../reports/real-fire-data/simfire-cohort-v2-seed-selection.json).
- **RL runtime je instaliran lokalno.** Izolovani Python 3.9.25 venv sada sadrži SimFire
  2.0.1, PyTorch 2.3.1, Gymnasium 1.1.1, Stable-Baselines3 2.7.1 i sb3-contrib 2.7.1.
  Tačne verzije su pinovane; ništa od toga nije instalirano u sistemski Python.
- **Prvi Gymnasium adapter radi.** Učitava stvarne rastere, provjerava njihove hashove,
  pretvara visinu u SimFire jedinice i podržava 40/20/20 split. No-op je uvijek dostupan;
  jedna akcija postavlja jednu fireline tačku i troši jedan budžet. Aktivna ćelija vatre
  može gorjeti najviše 15 jednominutnih koraka. To je izričita postavka adaptera za mrežu od
  30 m; zamjenjuje SimFire stock vrijednost 4 i nije fizički kalibrisana.
- **Osam dnevnih gridMET polja preuzeto je i provjereno za svih 80 požara.** Svaki JSON
  čuva jedinice, uzorkovanu ćeliju i hash; to su dnevne procjene za približno 4 km mrežu.
- **Vremenski proxy je napravljen za svih 80 slučajeva.** Nominalno tretira 10 m vjetar kao
  približan 20 ft vjetar, primjenjuje WAF 0.3, pretvara smjer “odakle” u smjer “prema kojem”
  i procjenjuje vlagu iz dnevne maksimalne temperature/minimalne vlažnosti. Pretpostavke su
  zapisane uz slučaj; ovo nije izmjerena gorivna vlaga ni satni replay.
- **Proxy smoke je prošao kroz po jedan stvarni slučaj iz sva tri splita.** Provjerena je
  legalna akcija MaskablePPO-a, jedna postavljena fireline tačka i no-op nakon potrošenog
  budžeta. Hashovi mapiranih ulaza učitani su za sve slučajeve splitova. WAF 0.1/0.3/0.5
  smoke je prošao; to provjerava kod, ne fiziku. `learn()` nije pozvan. [Receipti i slike](../reports/real-fire-data/).
- **Provjereno je i ponašanje bez poteza.** Sa stock trajanjem od 4 minute Owyhee primjer
  se ugasio nakon 8 minuta sa 2 ćelije. Nakon eksplicitne postavke na 15 minuta Owyhee je
  trajao 675 min i zahvatio 8.792 ćelije; Hayden je dosegao horizont od 720 min/1.059 ćelija;
  Larch Creek je trajao 84 min/24 ćelije. To su izlazi simulatora, ne prognoze stvarne
  opožarene površine. Larch Creek je korišten za tehnički smoke i izbacuje se iz budućeg
  završnog poređenja; ostaje 19 neotvorenih incidenta u test skupu prema
  [membership manifestu](../data/manifests/simfire-fpa-fod-evaluation-membership-v1.json).
  [No-op receipti](../reports/real-fire-data/).

## Šta još nije gotovo — i zašto nema treninga

1. **Dnevni gridMET proxy nije tačan replay događaja.** gridMET koristi približno 4 km
   ćeliju i dan ponoć–ponoć po MST; FPA-FOD sat paljenja nema potvrđenu vremensku zonu.
   Proxy drži jedan dnevni uslov stalnim kroz simuliranu epizodu.
2. **Vremenska pretvorba nije fizički validirana.** GridMET daje vjetar na 10 m, a profil
   vjetra i zaklon na svakoj lokaciji nisu izmjereni. Procjena ravnotežne vlage nije
   izmjerena vlaga trave/lišća i ne prati prethodnu kišu i sušenje.
3. **Fuel mape su prije požara, ali nisu snimak tačno na dan požara.** LF2016 je 2–3
   kalendarske godine star za train; LF2022 je 1–2 godine star za validation/test.
4. **Akcije su pojednostavljene.** Fireline tačka postavlja se odmah bilo gdje na mapi;
   kretanje ekipe, vrijeme gradnje i dostupni resursi nisu modelirani. Budžet 32 tačke,
   odluka svakih 30 minuta i horizont do 12 sati su početne pretpostavke.
5. **Poredbena pravila i inference runner su pripremljeni; agent nije treniran.** Ugovor
   fiksira no-op, front-edge heuristiku, base PPO i fine-tuned PPO, 5 istih seedova, budžet,
   horizont, primarni ishod, interval neizvjesnosti i checkpoint izbor na validation. TEST
   ostaje zatvoren u runneru dok se ne potvrdi završna evaluacija. Nema naučenih težina ni
   policy rezultata. Jedan postojeći test paketa pokreće 16 koraka učenja na malom
   sintetičkom `GridFire` fixtureu u privremenom folderu; to nije FPA-FOD/SimFire trening
   niti checkpoint. Vidi [protokol](research/SIMFIRE_EVALUATION_PROTOCOL.md),
   [konfiguraciju](../configs/simfire/evaluation-v1.json) i
   [pokretač](../scripts/evaluate_simfire_benchmark.py).
   Validation preflight je prošao za svih 20 slučajeva: raster/weather proxy hashovi su
   provjereni, Hayden observation je u dozvoljenom formatu, no-op je legalan, nijedan
   simulacijski korak nije napredovao i rezervisani testni inputi nisu otvoreni.

Znači: **imamo izvršiv put od 80 stvarnih slučajeva preko dnevnih weather proxyja do
SimFire-a, sa stvarnim mapama goriva/terena, ponovljivim no-op probama i unaprijed opisanim
načinom poređenja.** Preflight provjerava validation ulaze bez napredovanja simulacije.
Četverominutna
stock postavka bila je prekratka za dio simuliranih 30 m ćelija; adapter sada bilježi i
koristi 15 jednominutnih koraka. To poboljšava pokretljivost, ali samo po sebi ne potvrđuje
fizičku tačnost. Jedan testni požar korišten je u tehničkoj provjeri i neće ući u završno
poređenje. FPA-FOD/SimFire agent trening nije pokrenut. Prije tumačenja poređenja treba
fizički pregledati postavke širenja i definisati base/fine-tuning trening recept. Detalji su u
[dataset kartici](research/SIMFIRE_FPA_COHORT.md), [adapteru](research/SIMFIRE_RL_ADAPTER.md)
i [mapping receiptu](../reports/real-fire-data/simfire-cohort-v2-gridmet-simfire-mapping.json).

## Sljedeći redoslijed

1. Na drugom računaru/klonu ponoviti setup i pokrenuti samo validation preflight:
   `.local/simfire-venv/bin/python scripts/evaluate_simfire_benchmark.py --preflight-only`.
2. Prije treninga zasebno zapisati porijeklo i raspored generičkog base PPO treninga, broj
   trening-koraka i checkpoint frekvenciju finog učenja, te pregledati fizičke pretpostavke
   za vjetar/vlagu i 15-minutni vijek ćelije.
3. Trening ostaje zaustavljen dok ga korisnik izričito ne odobri. Poslije treninga validation
   bira checkpoint; rezervisanih 19 test incidenata otvara se samo za finalnu uparenu
   evaluaciju.
4. Završni report čuva epizode, uparene razlike po požaru i buduće karte/animacije.

## Stari CFSDS/Firehose rad

Ostaje sačuvan kao arhiva i referenca, ali trenutni aktivni dizajn je USFS FPA-FOD +
LANDFIRE + SimFire prema [ADR-040](specs/DECISION_RECORDS.md#adr-040--train-on-real-ignition-conditions-with-simulated-actions-2026-11-01).
Mineral/BurnMD linijski replay nije preduslov glavnog eksperimenta.
