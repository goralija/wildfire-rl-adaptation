---
type: Agent Instructions
title: Claude project entry point
---
# Project context

**Aktivno TASK-046 / ADR-057 (2026-11-23):** korisnik nastavlja i traži konačan
završetak ove faze prije mergea. [Plan](docs/research/SEPARATE_CLIP_PILOT.md),
`codex/separate-clip-pilot` izb00e55e2, plan208b95d5 prije koda. Samo separate
actor/critic norm bound0,5 uz originalreward i iste6×512/45fit/16development/seedove.
TASK046 je posljednja optimizer ablation; TASK047 zatvara fazu synthesisom i pregledom
cijelog stacka prema mainu, bez uslova da PPO pobijedi. Predloženi TASK048 je nova
CA control/native parity faza, ne nova izmjena ovog benchmarka. Prvo testovi/preflight,
potom odobreni background run/ETA; status/lock/PID provjeriti prije svakog nastavka.
Najviše3radnika+koordinator,nice19/jedna nit. Nema više od512, tuning poslije nalaza,
stvarnog VALIDATION/TEST/futureFEDS ili mergea prije završnog integracijskog pregleda.


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


Najnovije TASK-042 / ADR-048: [prošireni audit](docs/research/EXPANDED_OBSERVED_GROWTH.md)
je završen na61compatible TRAIN. PrimaryCA0 area greška manja67,90%, IoU0,12568vs0,08664,
ali svi4observed-zero slučaja oba modela prerastaju. Native PPO/fizička validacija nije
urađena. Sljedeći prijedlog TASK-040 B.1 je zajednički PPO/reward ugovor i tehnički smoke,
ne automatski veći trening ili native unit parity. Holdouti zatvoreni; pročitati STATUS.

Prethodno: TASK-038/ADR-042 je završen kratki CA BC/PPO na `codex/ca-learning-pilot`;
pročitati [learning pilot](docs/research/CA_LEARNING_PILOT.md) i najnoviji STATUS prije rada.

Aktivni nalog 2026-11-21 je TASK-035, završeni kontrolisani CA pilot (ADR-039–040), na
`codex/ca-controlled-pilot` iz SimFire repair grane. Pročitati [pilot](docs/research/CA_CONTROLLED_PILOT.md)
i najnovije STATUS/NEXT_SESSION; stariji tekst o odgođenom CA je historija.

Follow [AGENTS.md](AGENTS.md). Read [index.md](index.md) and
[knowledge/project-context.md](knowledge/project-context.md), then the current
[STATUS](docs/STATUS.md), [NEXT_SESSION](docs/NEXT_SESSION.md) and task-specific links.
Current state (2026-11-09, ADR-029): the results of ADR-022 to ADR-028 are invalid
until rerun. The gridMET sampler gave every fire in a year the weather of that year's
first fire (fixed). PRs #3–#5 (SimFire/FEDS gate, steps 5–8, synthetic CA) are merged
into main as history; do not cite their numbers as findings. The fix tasks
TASK-021–024 and TASK-027 are merged (PR #15: 98 TRAIN, FEDS `t` read as the local-solar
overpass, regenerated gridMET file); decisions are in ADR-030 and its addenda. Stages 1 and 2
of the TASK-026 rerun may run without a further go-ahead (stage 2 only if stage 1 passes);
merges and stage 3 stay with the user (see docs/HANDOFF_STAGE_1_2.md). Stage 1 passed
(ADR-031: WAF 0.10 / ROS 1.0 frozen, VALIDATION scored once; a pre-set gate, not a physical
validation). Stage 2 is complete (ADR-032: none of the six primary tests rejects; base PPO is
not distinguishable from a random legal line or the best TRAIN heuristic; a simulator result). Stage 3
waits for the user's decision.
The SimFire TRAIN-only TASK-028–030 iterations are complete on codex/simfire-policy-iterations (ADR-034, 2026-11-19): 98x33 outcomes, eight LOO methods, no candidate meets the registered continuation threshold. TASK-034 has since been completed; see ADR-036 below. Follow STATUS, NEXT_SESSION and docs/research/SIMFIRE_B1_EXPLORATION.md. VALIDATION, TEST 2024 and CA stage 3 stay closed.
Keep decisions and evidence in the
repository, following [maintenance](knowledge/maintenance.md). This file is a routing
shim; shared rules live in AGENTS.md.

Latest 2026-11-20 (ADR-036): TASK-034 is complete on codex/simfire-observation-audit.
Read docs/research/SIMFIRE_OBSERVATION_AUDIT.md. A startup race is fixed, four nested
families do not meet the threshold, and numerical/observation limitations are explicit.
TASK-035 CA contract/pilot is a draft, not training approval; TEST and new VALIDATION stay closed.

Latest ADR-038 (2026-11-20): the authorized observation-v2 repair is complete on
codex/simfire-observation-repair. Read docs/research/SIMFIRE_OBSERVATION_REPAIR.md.
Information aliases are repaired; the fixed fine rule has an uncertain TRAIN gain,
while no learned candidate meets the threshold. Prior PR20 remains open; new PR optional.
TASK035 CA is a draft and TASK037 holds remaining SimFire work. No automatic holdout/training.
