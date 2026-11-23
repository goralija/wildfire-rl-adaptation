---
type: Agent Instructions
title: Rad na projektu
---
# Rad na projektu

**Najnovije TASK-045 / ADR-056 (2026-11-23) je završeno.**
[Izvještaj](docs/research/CENTERED_PPO_PILOT.md), `codex/centered-ppo-pilot` izc2e53f4c.
Svih6×512koraka/12checkpointova bez greške,20,05min; nema aktivnog treninga ili locka.
Isti original512→centered: SF6,75→3,16%, CA6,36→7,93%; oba zamrznuta kriterija false.
CA porast nije pouzdan, SF rezultat negativan; TRAIN razvojni nalaz, ne fizička
validacija.438pinned/nezavisni audit svih koraka i96putanja PASS. Stari TASK043nalazi
nepromijenjeni. TASK-046 je prijedlog originalreward+separate actor/critic clipping
u istom512budžetu, nije pokrenut. Stvarni holdouti/futureFEDS/nativeparity/merge zatvoreni.
Korisnik i ubuduće preferira background handoff za odobrene duže lokalne poslove:
prvo provjeri start/napredak, zapiši status/PID/ETA i završi chat. Najviše3radnika+
koordinator,nice19/jedna nit; to nije dozvola za neograničeno treniranje. Slijedi
najnoviji NEXT_SESSION; stariji launch PID51639 ispod i u receipts je historija.


**Najnovije TASK-044 / ADR-054 (2026-11-23) je završen** na `codex/ppo-signal-diagnosis`,
izc160fd0e. [Izvještaj](docs/research/PPO_SIGNAL_DIAGNOSIS.md): tačan uniform first-line
SF5,23%/CA6,20%, stariPPO5,13/6,03%, sektori odabrani samo na45fit. Početni gradijentni
mehanizam potvrđen: globalni actor/critic clipping i velika razlika među požarima.
24disposable jednokratne probe nisu nove politike ili dokaz uspješnijeg punog treninga;
centriranje pomaže5/6početnih koraka, CA43kontraprimjer0,62×.423pinned/audit/restorePASS,
oldTASK043rezultati/kriteriji nepromijenjeni. Sljedeći TASK-045512step centering-only
pilot je prijedlog, nije start ili dozvola za neograničen trening. Stvarni holdouti/
futureFEDS/fizička validacija/nativeunitparity/merge ostaju odvojeni.


**Najnovije TASK-043 / ADR-052 (2026-11-22) je završen.** [Izvještaj](docs/research/PAIRED_PPO_LEARNING.md),
`codex/paired-ppo-learning`: svih6×2048koraka/18checkpointova,45fit/16development,
svi modeli sačuvani. PPO SF5,13%/CA6,03%, fixed front11,29/3,35%; nijedan backend
ne prolazi unaprijed zadani opisni learning kriterij. Ne tumačiti integrity PASS
kao RL ili fizičku prednost. Model seedovi nisu novi požari; CAspread0 fiksiran.
Greedy potezi često isti, soft vjerovatnoće skoro uniformne; random_legal seed0
je ovdje isti sektor7svuda.413pinned testova, nezavisni audit i puni restore96putanja
PASS. Nema aktivnog treninga: raniji PID37835/start tekst ispod je historija.
Sljedeći TASK-044 je prijedlog TRAIN dijagnoze signala/reference prije novih treninga,
ne dozvola za automatsko produžavanje. Holdouti/native unit parity/merge ostaju odvojeni.


**Najnoviji nalog je TASK-043 / ADR-051 (2026-11-22):** korisnik odobrava nastavak,
opsežno testiranje i duži lokalni trening uz završetak sesije dok background radi.
[Plan/status](docs/research/PAIRED_PPO_LEARNING.md) i najnoviji NEXT_SESSION su ulaz.
45TRAIN fit/16ranije istraženih development evaluation,3model seeda×2backend-a×2048koraka,
ista B.1 pravila. Maksimalno3radnika+koordinator,nice19/jedna nit. Ne pokretati dupli
koordinator: prvo pročitati lokalni status/lock/PID i receipts. NPZ je inference-only;
prekinut posao ne nastavlja optimizer. Holdouti/merge nisu odobreni; nema rezultata
dok svi guardovi/evaluacije ne prođu. Ranija zabrana automatskog većeg treninga ispod
zamijenjena je samo ovim konkretno odobrenim i zamrznutim pilotom.


**Najnovije TASK-040 B.1 / ADR-050 (2026-11-22) je završen** na
`codex/common-ppo-interface`, iz45d41fcf. [Izvještaj](docs/research/COMMON_PPO_INTERFACE.md):
isti terrain536/MLP/9akcija/B1/4×12h i opt-in charged reward u oba backend-a; privatni
vlastiti no-op samo za nagradu, bez future FEDS-a u opažanju/maski.4×64koraka tehnički
PASS, iste početne težine/schedule,397pinned testova, cijele native maske/checkpoint
replay/restore identični. Ovo ne dokazuje učenje ili fizičku validaciju. Naredni
prijedlog je novi mali preregistrovani TRAIN learning pilot uz iste heuristike, ha i
procente. Bez automatskog dugog treninga ili holdouta; native mobile-unit parity otvoren.
Pročitati najnovije STATUS/NEXT_SESSION; raniji prijedlog B.1 ispod je zamijenjen.


Repo je OKF 0.2 knowledge bundle. Na početku sesije pročitaj [index.md](index.md),
[projektni kontekst](knowledge/project-context.md), [STATUS](docs/STATUS.md),
[NEXT_SESSION](docs/NEXT_SESSION.md) i najnovije [odluke](docs/specs/DECISION_RECORDS.md).
Zatim koristi [mapu zadataka/koda](knowledge/code-map.md) za relevantne izvore i testove.
Korisnikove direktne upute imaju prednost; kasniji ADR može zamijeniti raniji.

**Najnovije je TASK-042 / ADR-048 (2026-11-21), završen** na
`codex/ca-expanded-growth-audit`, iz2de00136. [Izvještaj](docs/research/EXPANDED_OBSERVED_GROWTH.md):
svih61compatible TRAIN, isti zamrznuti no-op SF/3CA. PrimaryCA0 MAE2.132,29vsSF6.642,37ha
(−67,90%), IoU0,12568vs0,08664 na57observed-positive; oba opisna intervala povoljna.
Sva4observed-zero slučaja oba modela prerastaju, GoldstoneN1 ostaje problem;59fully-covered
osjetljivost prijavljena. Nije fizička validacija/native PPO rangiranje.388pinned testova
prolazi, nezavisna aritmetika/raster/reuse/restore PASS. Naredni prijedlog TASK-040 B.1:
zajednički PPO input/encoder/akcije/reward ugovor i kratak tehnički smoke, bez automatskog
velikog treninga. Native unit parity ostaje otvoren, TASK-039 odgođen. Holdouti zatvoreni.
Najviše3radnika plus koordinacija,nice19/jedna nit; kasniji ADR ima prednost nad historijom.

**Najnovije je ADR-046 (2026-11-21): TASK-041 završen** na `codex/ca-feds-growth-audit`
iz640a910e. [Izvještaj](docs/research/PAIRED_OBSERVED_GROWTH.md): isti16TRAIN, zamrznuti
SF/CA no-op prema exact-time FEDS-u. CA0 MAE1.317,67ha vsSF9.736,40 (−86,47%), IoU
0,1604vs0,1029, ali spatial interval uključuje0. Sva3CA spread seeda su prijavljena.
Martinov observed obod izlazi iz domene;15fully-covered osjetljivost ostaje povoljna
za razmjer. Goldstone/near-stalled i dalje problem.381pinovani test, replay/restore PASS.
Nije fizička validacija/native PPO rangiranje. Sljedeći prijedlog TASK-042: proširiti
isti zamrznuti no-op audit na61compatible TRAIN uz domain/no-growth QC; novi plan prije
skora. TASK-040 faza B otvorena, TASK-039 odgođen. Nema holdouta, treninga ili mergea.
Najviše3radnika uz koordinaciju, nice19/jedna nit; najnoviji ADR ima prednost nad historijom.

**Najnovije je ADR-044 (2026-11-21): TASK-040 faza A završena** na
`codex/ca-simfire-paired`, iz `722d5f2d`. [Izvještaj](docs/research/CA_SIMFIRE_PAIRED.md)
čuva16 istih stvarnih TRAIN početaka, identična opažanja/linije,48h i isti obračun.
CA no-op rast je oko5,4puta manji; procentni poredak heuristika se mijenja, RBF dobitak
je nestabilan preko3 spread seeda. Ovo nije poređenje starih PPO modela ili fizička
validacija.369 pinovanih testova prolazi, native replay/restore PASS. Nema automatskog
opravdanja prelaska na CA. Naredni prijedlog TASK-041 je TRAIN poređenje no-op rasta
sa opaženim FEDS promjenama; TASK-040 native faza B ostaje otvorena, TASK-039 odgođen.
Nema aktivnog treninga, stvarnog VALIDATION/TEST ili mergea. Max3 radnika uz koordinaciju,
nice19. Najnoviji STATUS/NEXT_SESSION imaju prednost nad historijskim sekcijama ispod.

**Prethodno je ADR-042 (2026-11-21): TASK-038 CA v2 BC/PPO završen** na
`codex/ca-learning-pilot`, iz3b7b56a2. [Izvještaj](docs/research/CA_LEARNING_PILOT.md):
3model seeda,60BC epoha i4.096PPO koraka po seedu,288development putanja PASS.
BC3,08%, PPO2,98% prema7,46% heuristike; nijedan kandidat ne prelazi prag. Modeli imaju
manje bliskih susreta u uzorku, svi0gubitaka; nema RL/fizičke validacije.362pinovana testa
prolaze. Numeric NPZ težine su lokalne i provenance-guarded, bez starog checkpointa.
Naredni TASK-039 je prijedlog TRAIN dijagnoze/pokrivenosti vlastitih putanja. Nema aktivnog
treninga, proceduralnog testa, stvarnog VALIDATION/TEST ili dugog computea. Max4procesa nice19.

**Prethodno je ADR-040 (2026-11-21): TASK-035 CA ugovor/pilot završen** na
`codex/ca-controlled-pilot`, iz `664d890d` SimFire repair grane po korisnikovom nalogu.
[CA izvještaj](docs/research/CA_CONTROLLED_PILOT.md):240 razvojnih epizoda i15 replayeva
PASS; direct_flank7,46% spašeno uz20 bliskih susreta/0 gubitaka, bez naučenog modela.
352 pinovana testa prolaze. Naredni TASK-038: v2 encoder/provenance i unaprijed zadat
kratki BC/PPO; dugi trening i proceduralni test nisu pokrenuti. Stvarni VALIDATION/TEST
ostaju zatvoreni. Native opažanje/current forcing zajednički su za sve politike.
Stariji tekst o odgođenom CA ispod je historija. CA nije fizički validiran ili Cell2Fire.

**Prethodno je ADR-038 (2026-11-20): TASK-036 faza A je završena na
`codex/simfire-observation-repair`.** [Izvještaj](docs/research/SIMFIRE_OBSERVATION_REPAIR.md)
razdvaja potvrđeni popravak informacije i nesiguran policy dobitak. Svih 98 replayeva,
1568 OOF lookupova,7 native sekvenci i 344 pinovana testa prolaze. Fine+gate je jači
TRAIN kandidat, nije nezavisno potvrđena prednost. Prethodni PR #20 je otvoren i zelen;
novi PR nije potreban po korisniku. Push izvedene grane je odobren, nema mergea.
TASK-035 CA je pripremljen draft; TASK-037 je opcionalni preostali SimFire physics/gate
put. Nema automatskog PPO/CA treninga ili novog VALIDATION/TEST pristupa.

**Najnoviji nalog (2026-11-20): još jedan SimFire pokušaj kroz TASK-036, popravak
opažanja prije CA.** PR #20 prethodnog audita je otvoren za pregled. Nastavak iz ove
grane ide u `codex/simfire-observation-repair`; precizni plan se piše prije mjerenja.
Novi PR nije obavezan po korisniku. CA pilot TASK-035 se odgađa. TEST i novo VALIDATION
korištenje ostaju zatvoreni. Korisnik je odobrio push/PR i opciju mergea, ali se ovdje
bira nova izvedena grana i otvoren pregled prethodnog rada, bez mergea.

**Aktuelan je ADR-036 (2026-11-20): TASK-034 je završen na
`codex/simfire-observation-audit`.** [Izvještaj](docs/research/SIMFIRE_OBSERVATION_AUDIT.md)
razdvaja provjerene greške, modelna ograničenja i otvoreno. Startup mkdir race je
ispravljen; četiri nested porodice ne prelaze prag. Preporučen je TASK-035, CA ugovor i
tehnički pilot; draft nije izvršen/odobren kao gotov protokol. SimFire v2 je mogući
TASK-036. Nema aktivnog runa. TEST/novo VALIDATION korištenje i automatski CA trening
ostaju zatvoreni; ne prikazivati ranije poništene CA brojeve kao rezultate.


**Prethodni ciklus je ADR-034 (2026-11-19): TASK-028–030 su završeni na grani
`codex/simfire-policy-iterations`.** Puna TRAIN B=1 tabela 98×33 i osam LOO metoda
su provjereni; nijedna metoda ne prelazi prag. Novi PPO nije pokrenut. TASK-034 je
prijedlog dijagnoze prostornog signala, ne pokrenuti eksperiment. Koristi
[izvještaj](docs/research/SIMFIRE_B1_EXPLORATION.md),
STATUS i NEXT_SESSION. Stari tekst o čekanju odobrenja tih TRAIN koraka je historijski;
VALIDATION, TEST, CA faza 3 i remote objava nisu automatski odobreni.

**Temelj ispravki je ADR-029 (2026-11-09): rezultati ADR-022–028 su nevažeći dok se ne
ponove.** gridMET uzorkovanje je davalo svim požarima jedne godine vrijeme prvog požara
(ispravljeno). PR-ovi #3–#5 (SimFire/FEDS gate, koraci 5–8, sintetički CA) su u `main`
kao historija; njihovi brojevi se ne citiraju kao nalazi. Ispravke TASK-021–024 su
spojene; odluke su u ADR-030 i dopunama. TASK-027 je spojen (PR #15: 98 TRAIN, FEDS `t` kao
lokalni prolaz, novi gridMET fajl). Faze 1 i 2 ponovnog pokretanja (TASK-026) agent smije
pokrenuti sam, fazu 2 samo ako faza 1 prođe; merge i faza 3 ostaju korisnikovi (dopuna ADR-030,
[handoff](docs/HANDOFF_STAGE_1_2.md)). Faza 1 je prošla (ADR-031: zamrznut WAF 0.10 / ROS 1.0,
VALIDATION ocijenjen jednom; unaprijed zadano pravilo, ne fizička validacija). Faza 2 je
završena (ADR-032: nijedan od šest primarnih testova ne odbacuje; PPO se ne razlikuje od nasumične
linije ni od najbolje heuristike; simulatorski rezultat). Faza 3 čeka korisnikovu odluku.
Pregled nakon faze 2 ([sažetak](docs/research/review-2026-11-11/SUMMARY.md), 2026-11-11) predlaže
TASK-028–030 (samo TRAIN, eksploratorno), također uz korisnikovo „da“. Ulaz za nastavak je [HANDOFF](HANDOFF.md).
TEST 2024 ostaje zatvoren. TASK-012/CFSDS/Cell2Fire je historijski odvojeni pravac.
Runtime PASS nije dokaz fizičke validacije ili RL prednosti. Čuvaj ovu razliku u sažecima.

Održavanje znanja: [maintenance](knowledge/maintenance.md), format:
[OKF profil](knowledge/okf-format.md). Novi `.md` koncept dobija YAML `type` i vezu iz
najbližeg `index.md`; ne izmišljati sources, generated/verified ili ljudsku potvrdu.
CI checker provjerava strukturu/linkove, ne istinitost naučnih nalaza.

- Radi u izdvojenom task worktreeu; sačuvaj tuđe izmjene.
- Worktree-i ovog projekta idu u `.worktrees/` glavnog klona, prema
  [workspace rasporedu](knowledge/workspace-layout.md). Prvo provjeri `git worktree list`;
  nastavi u odgovarajućem postojećem worktreeu. `.local/` je ignorisan radni prostor.
- Prije implementacije navedi pretpostavke i provjerljivi cilj; promjene drži malim.
- Činjenice, pretpostavke i prijedloge označi odvojeno. Uz vanjski nalaz navedi izvor i datum.
- Sintetički pilot ne prikazuj kao Cell2Fire, fizički validiran simulator ili istraživački rezultat.
- Za budžet, štetu, maske i statistiku dodaj test prije promjene ponašanja.
- Za oba agenta koristi iste scenarije, budžete, vremenski horizont i dostupne informacije.
- Ne prekidaj epizodu kada nestane budžeta. No-op mora ostati dostupan.
- Čuvaj kumulativnu štetu; tretirana prethodno zapaljena ćelija ostaje opožarena.
- Ne učitavaj neprovjerene pickle/torch checkpointove izvan izolovanog environmenta.
- Ne commituj privatnu prepisku, emailove, `.venv`, vanjski repo, velike mape ili težine.
- Dugi poslovi na Harunovom računaru: najviše 4 procesa uz `nice -n 19`, uz najavu trajanja
  (Harunova uputa, 2026-11-10; sa 7 procesa računar se preoptereti).
- Ne pokreći plaćeni compute, dugo treniranje, globalne instalacije, push/merge ili cloud deploy
  bez odgovarajućeg korisničkog naloga. Kratki lokalni testovi su normalni dio rada.
- Prije predaje pokreni `PYTHONPATH=src python3 -m unittest discover -s tests -v` i smoke CLI.
- Ažuriraj STATUS, NEXT_SESSION, odluke i experiment log nakon značajnog pomaka.
- Ažuriraj i root log/index kad se znanje mijenja; pokreni
  `python3 scripts/validate_knowledge.py --strict` uz requirements/knowledge.txt.
- Nemoj automatski raspoređivati posao članovima tima niti slati poruke profesorima.
