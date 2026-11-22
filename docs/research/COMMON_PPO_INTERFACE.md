---
type: Experiment Report
title: Zajednički PPO ugovor — TASK-040 B.1
---
# Zajednički PPO ugovor

## Rezultat — TASK-040 B.1 završen, 2026-11-22, ADR-050

**Tehnički PASS za oba backend-a.** Sada mogu koristiti isti PPO postupak i isti
obračun cilja nad postojećim common-line interfejsom. Ovo je osnova za budući
kontrolisani trening; nije izmjerena prednost agenta, simulatora ili native CA jedinica.
Plan commit `f1d46d22` prethodi kodu `011b85a1` i tehničkom popravku `bc0b58ba`.
[Sve putanje i dijagnostika](../../reports/real-fire-data/common-ppo-smoke-v1.json),
[nezavisna provjera](../../reports/real-fire-data/common-ppo-independent-v1.json) i
[verifikacija](../../reports/real-fire-data/common-ppo-verification-v1.json) čuvaju trag.

### Šta je konkretno uvedeno

`CommonControlEnv` je opt-in adapter nad istim v2 SimFire/CA bridge okruženjima.
Oba koriste već postojeći deterministički `terrain536` encoder, float32 vektor536,
MaskablePPO MLP sa dvije64-neuronske skrivene razine za politiku i vrijednost,
Discrete9 (no-op +8sektora), identičnu geometriju linije i nonfuel masku. B=1,
48h i4×12h; nema mobilnih jedinica/urban težina ili novog fizičkog modela.

Kategorije goriva i lokalni izrezi iz ranijeg v2 popravka sada se koriste i u ovom
zajedničkom PPO ulazu. To nije zapis bez gubitaka: encoder i dalje sažima kartu.
Identičnost početnog punog v2 opažaja, feature-a i maski potvrđena je za sva3slučaja.
Kasnija opažanja se razlikuju jer simulatori stvaraju različite fronte.

### Zašto nova nagrada

Historijski raw reward je kažnjavao samo novonastalu opožarenu površinu. Evaluacija
je dodatno računala dio linije koji je unutar vlastitog no-op požarnog otiska.
Novi adapter usklađuje povrat s tim istim charged ciljem, bez mijenjanja stare klase
ili starih nalaza/checkpointova:

`C_t = count((burned_t OR (line_t AND own_noop_final)) AND NOT initial)`

`r_t = -(C_t - C_previous)/100 - 0.01*invalid`, uz `C_0=0` i `gamma=1`.

Povrat kroz4koraka zato iznosi `-final_charged_cells/100`, uz eksplicitne invalid
kazne. Ćelija ima3,24ha, bez različite normalizacije po backend-u. Union sprečava
dvostruko brojanje; početna šteta se izuzima iz nove štete, ali ostaje u kumulativnoj
maski. Već izgorjela tretirana ćelija ne postaje spašena. Nelegalan zahtjev postaje
no-op bez troška budžeta; izlazak iz prostora akcija daje grešku. Budžet0 ne završava epizodu.

Privatni no-op endpoint je predikcija **istog simulatora** za isti slučaj, vrijeme
i spread seed. Nije budući FEDS. Služi samo obračunu nagrade, ne ulazi u feature-e
ili masku. Test s promijenjenim privatnim otiskom zadržava identične ulaze/maske.
Učenje dobija simulatorovu nagradu; ovakav cilj nije dokaz stvarne operativne koristi.

Konkretan tehnički primjer: Pine Lodge, SimFire seed17 replay daje2980raw ćelija,
a charged2986. Šest ćelija linije koje bi izgorjele više se ne predstavljaju kao
spašene samo zato što ih raw fire maska nema. Povrat je−29,86. Ovo ilustruje obračun,
ne predstavlja performance nalaz. Dodatni charge je nenult na11od24scripted putanje.

### Provjere i obim smokea

| Provjera | Ishod |
| --- | --- |
| 3TRAIN slučaja ×2backend-a, no-op cijela putanja | Svih30maski identično TASK-042 arhivi, uključujući CA u istom pinovanom runtimeu |
| 4scripted sekvence ×3slučaja ×2backend-a |24putanje, finalne opožarene/linijske maske i score identični izvornim tabelama |
| Tehnički PPO |2backend-a ×seed17/29 ×64koraka =256koraka,64pune epizode; svih4modela imaju finite update |
| Jednaki uslovi |Isti536encoder/MLP/hiperparametri, početne težine po seedu identične, isti ciklus16epizoda6/5/5 |
| Numeric checkpoint |4NPZ-a, hash/contract/tensor provjere, bez pickle-a; inference, bez optimizer resume stanja |
| Deterministički replay |12putanja ×4odluke; težine/logits/feature-i/maske/akcije i svih60kumulativnih maski identični poslije učitavanja |
| Nezavisni obračun |24native +12policy putanja,180kumulativnih maski,30reference maski i256training koraka PASS |
| Testovi |397pinovanih/0skip,382modernih/4skip,308core/46skip,15knowledge; CLI i strict91PASS |

Scripted sekvence su no-op, odmah osna linija s ponovljenim zahtjevom poslije
utrošenog budžeta, dijagonalna linija i odgođena linija. Sedam invalid zahtjeva je
eksplicitno evidentirano; maskirani PPO nema invalid zahtjeva. Svih4modela i sve
dijagnostike su prijavljeni, bez izbora najboljeg ili reward praga za prihvat.

Cijeli uspješni smoke traje119,91s, sekvencijalno nice19/jedna numerička nit.
SimFire train+checkpoint replay po seedu38,29/37,42s, CA5,70/5,66s; ovo je lokalno
tehničko mjerenje, nije opšti speed benchmark. Fizički parametri/WAF/ROS nisu podešavani.

Prva proba je zaustavljena nakon native provjera: pregledom je uočen nedostajući
CA `scenario_id` u step info, potreban loggeru. Regresija prvo daje KeyError, pa
zajednički adapter normalizuje metapodatak. Isti zamrznuti plan je u cijelosti ponovljen
u novom folderu; nema biranja rezultata. Prvi nepotpuni izlaz je sačuvan lokalno.

### Reprodukcija i granice

Pinovani runtime je isti za oba backend-a: Python3.9.25, NumPy1.26.4, Torch2.3.1,
SB3/contrib2.7.1, Gym1.1.1, SimFire2.0.1, SciPy1.13.1. Setup:
[runtime](SIMFIRE_ENVIRONMENT.md). U task worktreeu, sa tačnim TRAIN ulazima i weather
hashom iz frozen plana, izabrati nov izlazni ID:

```sh
nice -n 19 .local/simfire-venv/bin/python scripts/smoke_common_ppo.py --out .local/common-ppo-NEW
.local/simfire-venv/bin/python scripts/verify_common_ppo.py --folder .local/common-ppo-NEW --out .local/common-ppo-NEW/independent.json
.local/simfire-venv/bin/python scripts/bundle_common_ppo.py pack --folder .local/common-ppo-NEW --out .local/common-ppo-bundle-NEW
```

Guard odbija promijenjeni weather/table/runtime, ulazne receipt-e i no-op arhive.
Svaki sačuvani model vezan je za source/plan/runtime/backend/seed/encoder/reward ugovor.
Lokalni paket (3.326.232B,217fajlova plus manifest) sadrži source, konfiguracije,3TRAIN ulaza, stare reference, nove putanje
i numeric checkpointove; ništa od težina/raw mapa nije u Gitu. Njegov restore i hashovi
su u [artifact receiptu](../../reports/real-fire-data/common-ppo-artifacts-v1.json) i
[restore provjeri](../../reports/real-fire-data/common-ppo-restore-v1.json).

Prvi restore je otkrio da paketu nedostaje YAML template; packer je dopunjen. Finalni
paket ponavlja svih12putanja/60maski uz postojeće biblioteke, bez ponovnog treninga.

### Sljedeći predloženi korak

Novi unaprijed registrovan mali TRAIN learning pilot: fiksni fitting/evaluation slučajevi,
isti encoder/PPO/budžet koraka i seedovi u oba backend-a, bez izbora po rezultatu.
Potrebno je istovremeno prijaviti charged ha i procenat prema vlastitom no-op, te
odnos prema **istim** fiksnim heuristikama na **istim** slučajevima. Veći procenat na
CA sa znatno drugačijim požarom sam po sebi ne dokazuje bolji agent. Nulti no-op daje
undefined procenat, ne nulu/epsilon. Prvo izmjeriti budžet vremena, bez automatskog
dugog treninga ili stvarnog VALIDATION/TEST.

TASK-040 B.1 je završen. Native mobile-unit/resource parity ostaje otvoreni dio B,
TASK-039 je odgođen, TASK-037 opcionalni SimFire pravac. Ova3već istražena TRAIN
slučaja i64koraka ne daju generalizaciju, statistički RL dobitak ili fizičku validaciju.
TASK-042 nalaz o opaženom rastu ostaje odvojeni raniji rezultat.

### Objava B.1

Grana [codex/common-ppo-interface](https://github.com/goralija/wildfire-rl-adaptation/tree/codex/common-ppo-interface)
je pushana. [CI rezultatskog commita3ec5d5fc](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44965103408)
prolazi sva4posla: core3.11/3.13,numeric uz exact skip listu i knowledge. Naknadna
dopuna objave ne mijenja numerički source, plan ili rezultate. Nema novog PR-a/mergea.

## Plan prije implementacije i ishoda — 2026-11-22, ADR-049

Korisnikovo „hajde nastavi“ nastavlja predloženi TASK-040 B.1 iz ADR-048.
Rad je u `codex/common-ppo-interface`, iz `45d41fcf`; nema mergea ili dužeg treninga.
[Zamrznuti plan](../../configs/frozen/common-ppo-smoke-v1.json) određuje tehnički prihvat.

**Činjenica:** postojeći SimFire i CA bridge daju raw nagradu, a TASK-040 evaluacija
računa charged štetu. Stari native CA urban/unit PPO ima drugačiji MDP.
**Pretpostavka:** isti mali encoder i PPO mogu koristiti oba common-line backend-a.
**Provjerljivi cilj:** isti ulaz536, Discrete9, maske, B=1 i4×12h, te povrat jednak
negativnoj finalnoj charged šteti/100 umanjen za eksplicitne invalid kazne.

Novi opt-in wrapper koristi postojeći v2/terrain536 zapis i ne mijenja fiziku ili
historijski raw reward. Privatni no-op otisak vlastitog simulatora služi samo reward
knjigovodstvu, bez FEDS budućnosti ili njegove dostupnosti politici/maski. Prethodno
izgorjelo ostaje izgorjelo; union sprečava dvostruko brojanje. No-op ostaje legalan,
epizoda traje četiri odluke i poslije utrošenog budžeta.

Prvo testovi štete/nagrade/maski/budžeta, zatim native provjere na prva tri ranije
registrovana TASK-040 TRAIN slučaja: Goldstone, Weston Pass, Pine Lodge. Novi no-op
whole-mask mora odgovarati TASK-042 arhivi; i CA se provjerava u istom pinovanom
runtimeu kao SimFire. Početni opažaji/feature-i/maske moraju biti identični.

Tek zatim četiri kratka treninga: dva backend-a × seed17/29 ×64 koraka, isti MLP64×64,
PPO parametri i ciklični raspored16 epizoda (6/5/5). Nema izbora najboljeg modela ili
rangiranja. Numeric NPZ inference checkpoint mora sačuvati težine/logits/akcije i
cijele determinističke replay maske. Težine/raw ulazi ostaju lokalni.

Procjena izvršavanja5–15min, nice19, jedna numerička nit, sekvencijalno. Tehnički
PASS ne dokazuje učenje, fizičku validaciju ili prednost CA/SimFire-a. Native mobilni
resursi ostaju otvoreni dio TASK-040 B. Veći trening traži novi unaprijed zapisan plan.
