---
type: Literature Review
title: "Pregled literature: RL za gašenje požara pod budžetom"
description: "arXiv 2512.06102 (JaxWildfire) i 22 srodna rada, poređeni s ovim projektom."
status: stable
generated: {by: "process:claude-code", at: "2026-11-11T16:00:00Z"}
sources:
  - resource: https://arxiv.org/abs/2512.06102
  - resource: /docs/specs/DECISION_RECORDS.md
---
# A — Literature review: RL for wildfire suppression under an intervention budget

Prepared 2026-11-11 for the MPVI project (`/Users/harungoralija/Desktop/mpvi`, worktree
`.worktrees/task-026-stage-2`). The work was read-only: no repository file was changed, no training was run
and no paid compute was used. The downloaded PDFs are not kept in the repository; every paper is listed with its public link.

## 0. How to read this report

- **Fact** marks something stated in a paper or in our ADRs. **Interpretation** marks my own reading.
  Confidence levels are high, medium and low.
- **Read level** in the table:
  - *full*: the whole text.
  - *partial*: the named sections only.
  - *abstract*: only the abstract or a publisher/OpenAlex abstract.
  - A claim marked "abstract only" was not checked against methods or numbers.
- **Comparison point (our project, from ADR-030 to ADR-032 and STATUS).**
  - MaskablePPO on SimFire, starting from 98 real TRAIN fires.
  - Episodes are 48 h with 4 decisions each, one per 12 h; SimFire runs in 5-min steps inside each decision.
  - The action is Discrete(9): no-op or a ~1.26 km line in one of 8 sectors. The budget is B ∈ {0,1,2,4}.
  - The base policy was trained for 8,064 decisions, about 2,016 episodes, roughly 20 per fire.
  - On 20 VALIDATION fires, PPO is not distinguishable from a random legal line or from `advancing_front`. `downwind` is best descriptively.
  - Seven of ten base policies always open with the same direction.
  - Training ran at about 3 decisions/s. Stage 2 used 870.6 min of wall clock for 171,360 decisions.
- **Search coverage.**
  - Tools: web search across Google-indexed sources, arXiv, NeurIPS/AAMAS/ICLR-workshop pages, Frontiers, ScienceDirect landing pages and GitHub.
  - Citation lists: the Semantic Scholar API, which hit its rate limit after one call, and the OpenAlex API, used for forward citations of JaxWildfire, SimHarness, Murray et al., Haksar & Schwager and Altamimi et al.
  - Google Scholar was not reachable from the tools.
  - Searches restricted to the *International Journal of Wildland Fire* and to *Fire* (MDPI) returned no RL-for-suppression paper. That is a gap in coverage, not proof of absence.
  - Every paper listed below has a working link. Nothing was added from memory without a link.

---

## 1. The recommended paper: arXiv 2512.06102

**Çakır, Darvariu, Lacerda, Hawes (Oxford Robotics Institute). "JaxWildfire – A GPU-Accelerated Wildfire
Simulator for Reinforcement Learning."** NeurIPS 2025 Workshop *Machine Learning and the Physical Sciences*;
arXiv v1, 5 Dec 2025. <https://arxiv.org/abs/2512.06102>. Read in full: the PDF, plus the HTML for one formula.

**What kind of paper it is (fact, high confidence).** It is a five-page **simulator paper**. It gives no
evidence about whether RL beats heuristics: it has no heuristic baseline and no RL baseline of any kind.

### Problem

The authors argue that RL needs millions of interactions, and that FARSITE, ELMFIRE and even CPU cellular
automata (CA) are too slow for that. The specific bottleneck they name is moving data between simulator and
learner. They name SimFire/SimHarness speed explicitly as "a limiting factor for the scale (and,
consequently, task complexity)" of RL training.

### Simulator

- A probabilistic CA in JAX, built on Alexandridis et al. (2008) and PyTorchFire (Xia & Cheng 2025).
- Each cell has a fire state (unburned, burning or burned), wind speed and direction, a canopy-ignition modifier, a ground-fuel density modifier, and slope towards each of its 8 neighbours.
- Spread potential is `p_base·(1+μ_veg)(1+μ_den)·κ_wind·κ_slope`. It is read as a **Poisson rate of sparks**, so `p_ignite = 1 − exp(−γ(v)·λ)`, with susceptibility `γ` taken from the target cell's fuel.
- A burning cell stays burning with probability `p_continue`.
- There are two routines: stochastic Bernoulli sampling, and a deterministic routine that propagates probabilities. The deterministic one is **differentiable**.
- Inputs: ESA WorldCover land cover and the Copernicus DEM, fetched from a place-name string. Wind can be static or a time series.
- **Humidity and temperature are not modelled**; the authors list them as future work.
- It is compatible with Gymnax.

### Speed (fact)

- On an A100 it is 6–35× faster than PyTorchFire for a single simulation, and 18–51× faster in the `for_i` mode, which keeps no history.
- With `vmap` and 64 environments on a 64×64 grid, the text states a peak throughput of "2.5^16 steps/s".
  - That is the typeset value in the HTML. Plain PDF extraction renders it as "2.516".
  - The figure's y-axis only runs from 2^10 to 2^16.
  - **The number is ambiguous and probably a typo. The figure's axis tops out at 2^16; I give no number of my own.**

### Calibration (fact)

- Gradient-based calibration on one historical fire, Bear 2020, using BCE plus pooled MSE and Adam.
- JaxWildfire reaches IoU 0.424 against 0.348 for calibrated PyTorchFire, averaged over 5 seeds.
- Only one fire was used, and no held-out fire.

### RL demonstration: state, action, reward, horizon and training (fact)

| Item | What the paper states |
|---|---|
| Task | A synthetic 20×20 grid with one "air tanker" agent and fixed wind. The initial fire and agent positions are randomised. |
| Observation | "Partial egocentric observations". No size is given. |
| Action | The agent "controls the valve (open/closed) to drop limited water resources". Appendix Fig. 6 says it also "learns to move towards the fire", so movement exists but the action set is not listed. |
| Effect of water | It turns a burning cell into a burned one. |
| Reward | A per-step penalty proportional to the number of burning cells, plus +10 at the end if the fire is fully extinguished. |
| Horizon and decision frequency | One decision per CA step. Fig. 6 shows steps up to 24. No episode length is given. |
| Algorithm and training budget | PPO in the PureJaxRL style (citing Lu et al. 2022). One learning curve over about 12,000 "training steps" with undefined units; mean return goes from negative to positive. No seeds, episodes or wall-clock are reported. |
| Baselines and results | None. There are no heuristic, random or no-op numbers and no held-out evaluation. The only claim is that "the agent learns to extinguish the fire in this scenario". |

### Limitations

- **Stated by the authors:** no heterogeneous multi-agent teams (ground vehicles, drones), and no humidity or temperature.
- **Added by me (interpretation, high confidence):**
  - Calibration rests on a single fire.
  - The RL task is a toy: 20×20, aerial water and no fireline. It is not a budgeted ground-line problem.
  - With no baseline, the RL result cannot be compared with anything.

### Code and data availability (fact, checked 2026-11-11)

- The appendix says they "aim to publicly release" the code.
- <https://github.com/ori-goals/JaxWildfire> holds only a README saying "The code repository will be released soon". The last push was 2025-11-13, and the repository has no licence.
- The Bear 2020 data come from the PyTorchFire Mendeley dataset.

### Citations both ways

- **Backward:** Alexandridis 2008, PyTorchFire (Xia & Cheng, *Environmental Modelling & Software* 188, 2025), SimFire (Doyle et al. 2024), SimHarness (Tapley et al. 2023), Cell2Fire (Pais et al. 2021), FARSITE, ELMFIRE, Gymnax, JaxMARL, and PPO/DPO.
- **Forward, at OpenAlex/Semantic Scholar on 2026-11-11:** three citing works.
  - Matei et al. 2026, aerial suppression planning (arXiv 2606.13633), included below.
  - "Neural-parameterized cellular automata for wildfire spread" (*Ecological Informatics* 2026, arXiv 2606.11676), which is a spread model.
  - Suêtes (arXiv 2609.36381), a weather dynamical core that is not relevant.

### What it means for us (interpretation)

- It answers no question about RL against heuristics (high confidence).
- Its useful point is that **simulator speed caps RL scale**, and that it names SimFire as slow.
- Our ~3 decisions/s (about 430 internal SimFire steps/s) is in that regime (medium confidence).
- It is not usable today, because the code has not been released.
- Our own synthetic CA, at about 40 decisions/s per process (SYNTHETIC_CA_ENV.md), is the only fast simulator we actually have.

---

## 2. The most relevant related papers

The columns cover year and venue, the simulator, the action space, the horizon and number of decisions, the
training scale, the baselines, whether RL beat the heuristics and by how much, and the read level. "RL vs
heuristic" is taken from each paper's own tables; "in-sample" means the evaluation reused the training
instance or distribution.

| # | Paper (link) | Year / venue | Simulator | Action space | Horizon / decisions | Training scale | Baselines | Did RL beat heuristics, by how much | Read |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Çakır et al., **JaxWildfire** <https://arxiv.org/abs/2512.06102> | 2025, NeurIPS ML4PS workshop | Own JAX CA; synthetic 20×20 for RL | Water valve plus movement (not fully listed) | One decision per CA step; ≥24 steps shown | ~12k "training steps" (units undefined), 1 curve | None | **No comparison** | full |
| 2 | Tapley et al., **SimFire/SimHarness** <https://arxiv.org/abs/2311.15925> | 2023, NeurIPS CCAI workshop (proposals) | **SimFire** (Rothermel, LANDFIRE), 128×128 at 30 m, Coalinga CA | Agent moves (4 directions) and digs fireline per cell; 4 actions per sim step | ~591 steps per episode (8.27M ÷ 14k) | **14,000 episodes, 8,273,288 steps**; Rainbow-style DQN; 16 CPU, 2 GPU | No-op only, shown qualitatively in 3 scenarios | **No heuristic.** Only a qualitative "saved land" against no-op | full |
| 3 | Shen & Curtis, **Firehose** <https://williamshen-nz.github.io/firehose/firehose-paper.pdf>, code <https://github.com/aidan-curtis/firehose> | 2022, MIT course project report (not peer reviewed) | **Cell2Fire**, 20×20 and 40×40 | "Harvest" one cell per step (400 or 1,600 discrete actions); also continuous coordinates | Until the fire ends; one action per sim step | **5M steps** (random ignition), **20M** (20×20 random), 10M (40×40 fixed); 3 seeds | Random, Min-L2 (suppress near ignition), Max-L2 (frontier) | Fixed ignition: yes, magnitude only shown in plots. **Random ignition: no RL method matched Min/Max-L2 at 5M steps.** At 20M, MaskablePPO "nearly matched" on mean reward and won 46.8% of 1,000 ignitions (Max-L2 36%, Min-L2 16.4%, random 0.8%). **40×40 random: failed.** Discrete actions ≈ −40 return against continuous ≈ −80 | full |
| 4 | Murray et al., **DRL for firebreak placement** <https://arxiv.org/abs/2404.08523>; published version *Applied Soft Computing* 2025 <https://doi.org/10.1016/j.asoc.2025.113043> | 2024 arXiv / 2025 ASOC | **Cell2Fire**, real Alberta landscapes Sub20 (400 cells) and Sub40 (1,600) | Choose one cell per step (masked) until 5% of cells are treated | 20 (Sub20) or 80 (Sub40) decisions; reward only at the end | Table 3: 20,000 "epochs" (curves are per episode); 100k–200k demonstrations; **one landscape per model** | DPV heuristic (also the demonstrator), random | **Yes, small:** Sub20 burned 11.31–12.86% against DPV 12.90% (random 16.1%). Sub40 21.55–21.78% against 23.25% (random 28.36%). The best model is 1.6–1.7 percentage points (7–12% relative) better than DPV; the worst Sub20 model is level with it (12.86 against 12.90). **Without demonstrations "neither convergence nor good performance"** (Fig. 15). In-sample, single instance | full (arXiv v1; the ASOC version may differ) |
| 5 | Hammond, Schaap, Sabatelli, Wiering, **Forest fire control with LfD + RL** <https://orbi.uliege.be/handle/2268/250331> (thesis <https://fse.studenttheses.ub.rug.nl/20402/1/AI_BA_2019_DirkJelleSchaap.pdf>) | 2020, IJCNN | Own grid simulator, 10×10 and 14×14 | Bulldozer moves and digs line | Until containment or burn-out | **10 runs × 10,000 episodes** | Scripted "circle the fire" baseline (also the demonstrator) | With **0 demo episodes all four algorithms were below the baseline**. With 1,000 demo episodes, 3 of 4 were above it (Dueling SARSA 1745 against 1129 average reward on 10×10) | partial (thesis full; IJCNN results tables) |
| 6 | Haksar & Schwager, **Distributed deep RL for fighting forest fires with aerial robots** <https://msl.stanford.edu/bibliography/haksar_distributed_2018.html> | 2018, IROS | Factored-MDP forest model | Per-UAV local actions (9 per UAV according to Firehose's description) | n/a | n/a | Hand-tuned heuristic | The abstract says RL "outperforms" it and scales across forest size and number of UAVs. **No numbers seen** | abstract |
| 7 | Pais, **Vulcano** (AAMAS 2020 extended abstract) <https://aamas.csc.liv.ac.uk/Proceedings/aamas2020/pdfs/p1960.pdf>, code <https://github.com/cpaismz89/Vulcano_DRL> | 2020, AAMAS | Built on Cell2Fire (its ref. [18] is the Cell2Fire preprint); real Canadian landscapes up to 40×40 | Per agent: 4 moves, harvest, wait | Episode until fire end | **100,000 episodes** | Other RL algorithms (PG/AC, DDQN, HQL, COMA) | The "30% less burned area" compares centralised with decentralised RL. **No quantified heuristic comparison** in the abstract. The state includes expected fire progress and a **weather forecast** | full (3 pp.) |
| 8 | Altamimi et al., **Large-scale wildfire mitigation through DRL** <https://doi.org/10.3389/ffgc.2022.734330> | 2022, *Frontiers in Forests and Global Change* | Abstract stand-level spatial MDP | Treatment per stand, one stand per step | Horizon = number of stands | n/a in what I read | Exact value iteration (small cases), genetic algorithm | Matches the exact optimum where it is computable and beats the GA on large instances. This is fuel management, not suppression | partial (abstract, model) |
| 9 | McGregor et al., **Fast optimization of wildfire suppression policies with SMAC** <https://arxiv.org/abs/1703.09391> | 2017, arXiv (OSU) | FARSITE + FVS full simulator via the MFMCi surrogate | Suppress / let-burn per ignition, through a **14-threshold decision-tree policy** | 100 years | 360 sampled policies to build the surrogate; SMAC on the surrogate; ≥50 full-sim checks | Suppress-All, Let-Burn-All | **No deep RL.** Black-box search over an interpretable parameterised policy found good policies quickly, and surrogate values were confirmed on the full simulator | full |
| 10 | Bertsimas, Griffith, Gupta, Kochenderfer, Mišić, Moss, **MCTS vs mathematical optimisation for dynamic resource allocation** <https://arxiv.org/abs/1405.5498> | 2014, arXiv preprint | Stochastic grid fire-spread MDP (tactical wildfire) | Assign suppression teams to cells each epoch | Multi-step; rollout horizon 10 | Online planning, ~10 s per decision | Random suppression; the "FW" weight-based heuristic | **MCTS and MO both "greatly improve" on the heuristic.** MO beats MCTS as instances grow; with very large action spaces MCTS can fall **below** the heuristic. A good heuristic rollout policy "makes a material difference" | partial (abstract, contributions, §3.4, §5.2, conclusion) |
| 11 | Diao, Singla, Mukhopadhyay, Eldawy, Shachter, Kochenderfer, **Uncertainty aware wildfire management** <https://arxiv.org/abs/2010.07915> | 2020, arXiv | Simple grid spread model, fixed wind | Suppress k cells per step (POMDP) | Until burn-out | Online POMCPOW (no training) | Greedy "max-utility observed-fire cell" | Online planning beats greedy on all grids from 4×4 to 16×16, by more on larger grids; numbers only in plots | partial (method, experiments) |
| 12 | Petersen et al., **Modelling and optimisation of extinction actions for wildfire suppression** <https://doi.org/10.1080/00102202.2023.2246195> | 2023, *Combustion Science and Technology* | Physics-based CA with Lagrangian fire particles; water and firebreaks | Allocate a fixed set of extinction actions | n/a | MCTS (online) | Human intuition | MCTS "outperforms human intuition" for medium fires and helps on large ones | abstract |
| 13 | Matei et al., **Aerial wildfire suppression planning with a hybrid CNN-CA fire model** <https://arxiv.org/abs/2606.13633> | 2026, arXiv | Frozen learned CNN-CA trained on 6 real fires; case study Bear 2020 (**in the training set**) | Drop yes/no plus continuous pose per aircraft per step (63,000 variables) | 20-day event | 6,000 rollouts per planner; the two-stage plan used ~21,700 | Random, **doctrine "tactical" heuristic**, greedy, CMA-ES, DE, PSO | **No RL.** Gradient planning through the differentiable simulator gives objective 7.04 against 15.29 for the tactical heuristic. **The tactical heuristic (7 rollouts) beat greedy (17.82), CMA-ES (18.80), DE and PSO, each given 6,000 rollouts.** Results are conditional on the frozen simulator | partial (abstract, §1–2, §5.4) |
| 14 | Boussioux, Jacquillat, Reger, Wachspress, **Predictive and prescriptive AI toward optimizing wildfire suppression** <https://arxiv.org/abs/2605.04510> | 2026, arXiv (math.OC) | Data-driven spread model (double ML on historical crew assignments and growth) | Crew-to-fire assignments over a season | Days, many fires | Branch-and-price-and-cut | Random, distance-, area- and impact-based priority rules | Optimisation "can double the effectiveness of suppression" in burned-area reduction against practical rules. Key method point: **historical suppression confounds growth data**, so they use double ML | partial (abstract, intro, benchmark statement) |
| 15 | Siedler, **Auto-curricula MARL with GNN communication for wildfire resource distribution** <https://arxiv.org/abs/2204.11350> | 2022, ICLR workshop GMS | Own procedural Unity environment (lookout towers) | Resource sharing between towers | 500 steps per episode | **5×10^7 steps** | **Weak** greedy baseline that never shares resources | RL reward ~900–1,000 against ~111–122. Single-environment policies dropped on unseen environments (1,073 → 590 single-agent). Procedural + auto-curriculum gave 907 ± 143 against 876 ± 131 (overlapping) | partial (abstract, §4) |
| 16 | Mathur et al., **FireCastRL** <https://arxiv.org/abs/2601.14238> | 2026, arXiv (IEEE 2025) | CA with Rothermel spread, 240×160, real terrain and gridMET wind | Helitack: 4 moves plus drop | Until the fire ends | **3×10^5 steps**, PPO with CNN, attention and LSTM | **Weak:** rule that drops "without observing the fire's state" | One reported comparison: 1,529 against 4,931 cells burned. No seeds or CI | full |
| 17 | Bardtke et al., **MARL framework for aerial wildfire fighting** <https://doi.org/10.3390/engproc2026133188> | 2026, EASN conference proceedings | SoSID toolkit (CA) | Aerial agents | n/a | n/a | Heuristic "inspired by real-world firefighting practice" | Beats it **only when spread sensitivity is low**. It "declines as spread sensitivity increases … overfitting"; the authors suggest a curriculum | abstract |
| 18 | Ulloa-Fierro et al., **Bayesian-optimised network-interdiction heuristic for firebreak placement** <https://doi.org/10.1016/j.ecoinf.2026.104104> | 2026, *Ecological Informatics* | Simulated fire-scenario ensembles on Alberta landscapes of 400, 1,600 and 10,000 cells | Firebreak edges (prevention) | n/a | Beam search; BO calibrates the heuristic's weight | "Two state-of-the-art methods" (not named in the abstract) | Lower expected burned area by 10–12% (400 cells) and 33–39% (1,600). At 10,000 cells a **purely topological greedy rule was best**. Not RL, and the baselines are unnamed | abstract |
| 19 | Harris, Forbes, Taimre, **Logic-based Benders decomposition for wildfire suppression** <https://arxiv.org/abs/2209.01371> | 2022, arXiv | Minimum-travel-time spread on a graph | Place suppression resources at given times | One plan | Exact optimisation | MIP, iterated local search | Solves instances to proven optimality. Shows the place-resources problem has an exact OR form | abstract + intro |
| 20 | Cartwright et al., **Communication-aware decentralised MARL for UAV wildfire suppression** <https://doi.org/10.3390/drones10080580> | 2026, *Drones* | Probabilistic grid with wind | UAV moves and suppression | n/a | Decentralised DQN | MARL variants | Selective experience sharing improves containment. **No heuristic stated** | abstract |
| 21 | Gahtan, Shpund, Bronstein, **Differentiable Randers-Finsler eikonal solvers** (App. E, sim-to-real) <https://arxiv.org/abs/2603.00035> | 2026, *Computer Graphics Forum* / arXiv | Trained on Sim2Real-Fire FARSITE simulations | **Spread prediction, not control** | n/a | n/a | Model trained on real fires | Zero-shot sim-trained model: ρ 0.588 and IoU 0.342 on 43 real fires. Real-trained: ρ 0.503 and IoU 0.159 on 8 fires. **Different test sets, so not paired** | partial (App. E) |
| 22 | Li et al., **Sim2Real-Fire dataset** <https://proceedings.neurips.cc/paper_files/paper/2024/hash/02e978a2cc9a1d0d4376a7deb01db612-Abstract.html> | 2024, NeurIPS Datasets & Benchmarks | 1M simulated scenarios (FARSITE, WFDS, WRF-SFIRE) plus 1K real fires for testing | Forecast and backtracking | n/a | n/a | n/a | Not control. Relevant only as the sim-trained, real-tested prediction setting | abstract |

**Other works found and not tabled.** They are less relevant (evacuation, monitoring or survey work), or
they had only an abstract with no comparison.
- PyroRL, an evacuation environment: <https://doi.org/10.21105/joss.06739>.
- Tupayachi et al., ANNSIM 2024, A2C with a discrete-event digital twin, no baseline in the abstract: <https://doi.org/10.23919/annsim61499.2024.10732085>.
- Miller et al., SISY 2026, an RL unit-placement module with a rule-based constraint layer, no baseline in the abstract: <https://doi.org/10.1109/sisy71351.2026.11738544>.
- FORFIS, a firefighting simulator for teaching: <https://arxiv.org/abs/2305.17967>.
- MITRE SimFire and SimHarness repositories: <https://github.com/mitrefireline>.
- Cheng et al. 2026, drone dispatch for WUI fires using a benefit-per-energy heuristic dispatcher (not RL): <https://doi.org/10.1016/j.jnlssr.2026.100323>.
- Julian & Kochenderfer, wildfire *surveillance* with deep RL: <https://arxiv.org/abs/1810.04244>.
- CA gyms cited by SimHarness (repositories checked, HTTP 200; not analysed): gym-cellular-automata <https://github.com/elbecerrasoto/gym-cellular-automata> and Wildfire-Control-Python <https://github.com/dashdeckers/Wildfire-Control-Python>. SimHarness attributes the latter to Travis Hammond, first author of row 5; that it is the code for row 5 is my inference.

**Patterns across the table (facts, high confidence).**
- Only 3 of the 22 report a quantified RL-against-heuristic comparison in which the heuristic is non-trivial: Firehose, Murray and Hammond.
- All three are in-sample or on a single instance, use 1–10 seeds and give no confidence intervals.
- None of the 22 evaluates a learned suppression policy on held-out real fires.
- None uses a budget-varying fine-tuning design like ours.

---

## 3. Approaches we have not tried that worked elsewhere

These are ordered by how cheaply they fit our setup. "Evidence" is what the source shows. "Fit" is my
interpretation of how it maps onto our MDP.

1. **Measure the headroom with exhaustive or tree search per fire before more RL.**
   - *Evidence.* Online planning beat good heuristics without any training phase in Bertsimas et al. (MCTS and MO against the FW heuristic), Diao et al. (POMCPOW against greedy) and Petersen et al. (MCTS against human intuition, abstract only). Bertsimas also found that a strong heuristic rollout policy matters, and that MCTS can drop **below** the heuristic when the action space is large.
   - *Fit (interpretation, high confidence on the arithmetic).* Our open-loop action tree is tiny: with 4 decisions and up to 9 actions each, there are at most 33 sequences at B=1, 417 at B=2 and 6,561 at B=4.
   - The benchmark is deterministic (project-context.md), so an **oracle best sequence per fire** is exact. A B=1 oracle on 98 TRAIN fires is about 3.2k episodes, below one training seed.
   - This would show whether *any* policy can beat `downwind` by a margin that 20 VALIDATION fires could detect. If the oracle gap is under ~100 ha at B=2, no learner can show a significant gain at n=20 (see ADR-032 interval widths).
   - Not run, by instruction.
2. **Heuristic demonstrations, then RL (DQfD or BC+PPO) in SimFire.**
   - *Evidence.* Murray et al.: without demonstrations there was no convergence; with them, RL beat the demonstrator by at most 1.6–1.7 percentage points of burned area. Hammond et al.: with 0 demonstration episodes every algorithm was below the scripted baseline; with 1,000, three of four were above it.
   - *Caveat from Murray et al.* Performance "is anchored to that of the demonstrator". That matches our CA result, where BC+PPO tied `direct_flank`.
   - *Fit (medium).* This is cheap to try with `downwind` as the demonstrator. Expect at best a small gain over `downwind`, not a step change.
3. **A counterfactual (no-op-relative) reward in SimFire.**
   - *Evidence.* SimHarness, which uses SimFire like we do, rewarded the per-step difference between new damage under no-op and under the agent, normalised by the final no-op burned area. It added a +0.25/area bonus per newly placed line to encourage exploration. Its results are qualitative only.
   - *Fit (interpretation, medium).*
     - Our SimFire reward is absolute: −new burned cells/100. Line effects are 0.3–8% of the no-op mean (ADR-032), while fire-to-fire variance in burned area is large (mean 3,464 ha, median 685 ha).
     - In PPO the critic must predict each fire's free-burn growth from a 4×16×16 pooled map before the advantage carries any line signal.
     - That is a plausible reason why 7 of 10 seeds converged to a fixed direction.
     - Our CA already uses a counterfactual reward. Porting it to SimFire costs one paired no-op rollout per episode. The rollout is deterministic, so it can be cached per fire and segment.
4. **Give the policy (and the heuristics) forecast information, as a labelled ablation.**
   - *Evidence.* SimHarness observes the current and *final* no-op fire maps. Vulcano observes "expected fire progress" and a weather forecast.
   - *Fit.* ADR-030 §1 deliberately withholds the upcoming forcing and already allows a perfect-forecast variant as a labelled ablation.
   - Interpretation (medium): when comparing with those papers, our information set is strictly poorer. Part of their success may come from the extra information, not from learning.
5. **A parameterised heuristic tuned by black-box search (SMAC, Bayesian optimisation or CMA-ES), instead of a free policy.**
   - *Evidence.* McGregor et al. optimised a 14-threshold tree policy with SMAC on a surrogate and validated it on the full simulator. Ulloa-Fierro et al. calibrated a firebreak heuristic's weight with BO and beat two state-of-the-art methods (abstract only).
   - *Counter-evidence.* In Matei et al., generic CMA-ES, DE and PSO **lost** to a doctrine heuristic. Black-box search over raw placements is worse than structure.
   - *Fit (medium).* Expose 2–4 parameters, such as offset distance, sector rule (downwind or front-advancing) and when to spend budget, and tune them on TRAIN. This is closer to "tune the heuristic" than "learn from scratch".
6. **Much more experience, which needs a faster simulator.**
   - *Evidence.* Every positive RL result used far more episodes than our ~2,016 base episodes:
     - SimHarness: 14,000 episodes.
     - Hammond: 10,000 episodes per run.
     - Murray: about 20,000 per *single* landscape.
     - Vulcano and Siedler: about 100,000 each (Siedler's 5×10^7 steps at 500 steps per episode).
     - Firehose: 5–20M steps, and it still failed to generalise on 40×40.
   - JaxWildfire and Firehose (Cell2Fire at about 2 steps/s, "the most critical" issue) both name simulator speed as the binding constraint.
   - *Fit (medium).* At about 3 decisions/s SimFire cannot reach these scales locally. Our CA, at about 40 decisions/s, is the only fast simulator available to us; JaxWildfire's code is not released.
7. **Per-fire (fixed-instance) optimisation instead of one policy for all fires.**
   - *Evidence.* Murray trains one model per landscape. Firehose succeeded with a fixed ignition and failed with random ignitions. Siedler's single-environment policies degraded sharply on unseen environments.
   - *Fit.* For a decision-support framing, per-fire search (item 1) is the honest analogue. A generalising policy over 98 heterogeneous real fires is the hardest regime in this literature.
8. **Richer line parameterisation (distance, length, anchoring).**
   - *Evidence.* Firehose found per-cell discrete actions much better than continuous coordinates (−40 against −80 return) and proposed fully convolutional heatmap actions, which were not finished. Matei's doctrine heuristic places footprints *across the local spread direction* at the active front, or at the forecast front half a day ahead.
   - *Fit (low).* ADR-032 reports that half of the placed lines change nothing. A fixed 360 m offset may often be in the wrong place, so a distance or timing parameter could matter more than direction. This is a hypothesis.
9. **Curriculum and procedural generation.**
   - *Evidence.* Siedler's auto-curriculum on procedural environments helped on unseen procedural environments, but the gain is within one standard deviation. Bardtke et al. *suggest* a curriculum after overfitting.
   - *Fit (low).* There is no evidence for transfer to real fires.
10. **Reward shaping by distance to the fire.**
    - *Negative evidence.* Firehose's DIST-PENALTY gave "no significant improvement or speed-up".
    - Not recommended as a first step.

Multi-agent methods (Vulcano's COMA, Haksar, Cartwright) do not fit a single 12-hourly line decision. I list
them only for completeness.

---

## 4. Conclusions from prior work that should change our direction

1. **"RL rarely beats a good heuristic unless it is seeded by that heuristic, and then only by a little."**
   - *Facts:*
     - Murray et al. needed demonstrations and won by at most 1.6–1.7 percentage points.
     - Hammond et al. were below the baseline with 0 demonstrations.
     - Firehose, without demonstrations and at 20M steps, only "nearly matched" Min/Max-L2 on random ignitions.
     - Where RL "beat" heuristics by large factors, the heuristic was blind or degenerate: FireCastRL's rule ignores the fire state, and Siedler's greedy rule never shares resources.
     - Bardtke et al. beat a practice-based heuristic only in low-spread regimes.
   - *Interpretation, medium-high confidence:* our null result is the expected outcome, not an anomaly.
2. **"Training scale in the literature is 5–50× ours in episodes, and the successes are per-instance."**
   - *Fact:* see §3 item 6.
   - *Caveat:* units differ. One of our decisions is 144 SimFire steps, about 12 h of fire, so "decisions" are not comparable with their "steps"; episodes are the fairer unit.
   - *Interpretation, medium:* ~20 episodes per fire, against a per-fire action tree of 417 at B=2, is far too little to learn a fire-conditional policy. Collapse to a single direction is the typical symptom.
3. **"Generalising across ignitions or landscapes is where RL fails."**
   - *Facts:* Firehose (fixed ignition succeeds, random fails, 40×40 random fails), Siedler (single-environment policies degrade) and Bardtke (overfits to the spread regime).
   - *Interpretation, medium-high:* 98 different real fires are the hardest regime reported. Policy collapse is consistent with this literature.
4. **"Positive results are weakly evaluated."**
   - *Fact, high confidence:* the positive results use 1–3 seeds (Firehose), single instances (Murray, Matei), qualitative scenarios (SimHarness) or single comparisons (FireCastRL). None has held-out real-fire tests or confidence intervals.
   - *Interpretation, high:* our pre-registered, paired and Holm-corrected null on held-out fires is *stricter* than anything in this set. It does not contradict their claims, and should be presented that way.
5. **"Search or planning with the model beats heuristics with no training."**
   - *Facts:* Bertsimas (MCTS and MO), Diao (POMCPOW) and Petersen (MCTS), plus gradient planning through a differentiable model in Matei.
   - *Interpretation, medium:* when the simulator is the ground truth anyway, as in our benchmark, per-fire search is the stronger comparison than PPO and a direct measure of headroom.
6. **"Real suppression is baked into real perimeters."**
   - *Facts:* Matei et al. state that their training perimeters "reflect fire growth during real suppression", so their baseline is not an unsuppressed fire. Boussioux et al. treat historical crew assignments as confounders, using double ML.
   - *Interpretation, high:* this is the same mechanism behind our SimFire overgrowth of non-growing FEDS fires (ADR-031). A free-burn simulator initialised from real perimeters misrepresents contained fires. The literature treats this as a modelling problem, not a calibration one.
7. **"Simulator speed limits what RL can be asked to do."**
   - *Facts:* JaxWildfire's motivation; Firehose's Cell2Fire at about 2 steps/s.
   - *Interpretation, medium:* at about 3 decisions/s, SimFire suits evaluation and planning more than large-scale RL training.

---

## 5. The three specific questions

**(a) Do short episodes or few decisions limit learning?**
- *Fact:* no paper I found varies decisions per episode or horizon as an experimental factor. **There is no direct evidence.**
- *Indirect facts:*
  - Successful setups use 20 to several hundred decisions per episode: Murray 20–80, SimHarness about 591 steps, Firehose one per simulation step. They also use many more episodes.
  - Murray identifies the *sparse, end-of-episode* reward as a learning obstacle.
  - McGregor et al. optimise a policy with one binary decision per ignition over 100 years, but with a structured policy and black-box search, not deep RL.
- *Interpretation (medium):*
  - With 4 decisions and a dense per-decision reward, credit assignment over time is *not* our bottleneck. The problem is close to a contextual bandit.
  - What limits learning is the signal-to-noise ratio: small line effects against large fire-to-fire variance under an absolute reward, combined with few samples per fire.
  - "Short horizons make credit assignment impossible" is therefore **not** supported as an explanation for our result (low-medium confidence).

**(b) Do synthetic fires fitted to real-fire statistics transfer?**
- *Fact:* **no evidence for control policies.**
  - The only real-fire transfer result I found is for *spread prediction*: Appendix E of the eikonal paper, where a model trained on FARSITE scenarios scored ρ 0.588 zero-shot on 43 real fires.
  - It is unpaired with the real-trained comparison (8 fires) and concerns prediction, not intervention.
  - Sim2Real-Fire (NeurIPS 2024) is a prediction benchmark of this same kind.
  - Siedler's curriculum gains are measured on procedural environments only.
- *Interpretation (medium):*
  - Transfer of a suppression policy from synthetic to real fires is untested in this literature.
  - The intervention effect is not observable in real data (Boussioux needed causal adjustment just to estimate crew effects).
  - Any "real-case test" of a CA-trained policy, like our stage 3, therefore remains a simulator-on-real-inputs result, as SYNTHETIC_CA_ENV.md already says.
  - The advantage of a fast CA is volume of experience, not realism.

**(c) Does optimising heuristic parameters with RL or search beat pure RL?**
- *Fact:* **no head-to-head comparison in the wildfire literature.** The closest evidence:
  - McGregor et al.: a 14-parameter interpretable policy optimised by SMAC worked well, with no RL comparison.
  - Ulloa-Fierro et al.: a heuristic with a BO-calibrated weight beat two state-of-the-art firebreak methods (abstract only; methods unnamed). At the largest scale, a simple topological greedy rule won.
  - Matei et al.: generic black-box search over raw placements lost to a doctrine heuristic, and gradient planning won. Structure beats unstructured search.
  - Bertsimas et al.: a good heuristic as the MCTS rollout policy materially improved MCTS.
  - Murray and Hammond: heuristic-seeded RL is the only RL variant that beat its heuristic.
- *Interpretation (low-medium):* the pattern favours *structure from heuristics*, whether as a demonstrator, a rollout policy or a parameterised family, over RL from scratch. No source shows that tuning heuristic parameters beats heuristic-seeded RL, or the reverse.
- No wildfire residual-RL paper was found. Residual policy learning exists in robotics (Silver et al. 2018, <https://arxiv.org/abs/1812.06298>; Johannink et al. 2019, <https://arxiv.org/abs/1812.03201>), but it is untested for fire.

---

## 6. Suggested next steps, ranked (interpretation, not run)

1. **Run a per-fire oracle or exhaustive search on TRAIN at B=1, then B=2.** This measures headroom over `downwind` and `advancing_front`. If the headroom is below what 20 VALIDATION fires can detect, report that as the main finding: in this simulator a fireline choice barely matters.
2. If there is headroom, try the following in order. Each needs a pre-registration under ADR-030 rules, since VALIDATION is used once.
   - A counterfactual reward in SimFire.
   - A `downwind`-demonstrated BC+PPO.
   - A 2–4 parameter heuristic tuned by search on TRAIN.
3. Larger-scale RL only on the fast CA, and transfer claims labelled as untested.

## 7. Gaps and caveats in this review

- **Not obtained:**
  - Google Scholar.
  - The Semantic Scholar citation lists beyond one call.
  - Full texts of Haksar & Schwager, Petersen, Ulloa-Fierro, Bardtke, Cartwright, and the ASOC version of Murray.
  - Searches of IJWF and *Fire* (MDPI) restricted to those journals found no RL-for-suppression paper.
- **Negative search results** for terms the brief named:
  - No RL gym built on FARSITE or Prometheus. FARSITE appears only inside McGregor et al.'s surrogate, and Prometheus only as Vulcano's weather and ignition data source.
  - No RL-for-suppression paper from ICML, IJCAI or an AAAI workshop.
  - No wildfire residual-RL paper.
  - No paper varying decisions per episode.
  - No control policy transferred from synthetic to real fires.
- **Murray et al. numbers** are from arXiv v1. The published ASOC 2025 version may differ.
- **Firehose** is a course report; its numbers are in-sample with 3 seeds.
- I found no paper on budget fine-tuning or budget adaptation for wildfire RL. Our budget study appears to have no direct precedent here. That is a negative search result, so treat it with medium confidence.
