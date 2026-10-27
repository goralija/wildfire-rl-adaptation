# API i CLI ugovori

Nema mrežnog API-ja.
`GridFire(Scenario, budget: int, priority_weight=0)`; `reset(seed=0) -> state copy`;
`step(action: int) -> float reward`; `action_masks() -> list[bool]` dužine N+1;
`metrics() -> dict`; `terminated`, `truncated`, `state`, `ever_burned`, `remaining_budget`.
Reset prije koraka. Pogrešan core action/config: ValueError; korak nakon done: RuntimeError.
`choose_action(env, policy, rng) -> int`, RNG je zaseban `random.Random`.

`evaluate(config) -> list[dict]`; `summarize(rows) -> list[dict]` podržava jedan
backend/scenario i referencu none po istim seedovima. Duplikati/neupareni podaci su greška.
`write_run(config, out: Path) -> manifest`, postojeći out: FileExistsError.
`python -m wildfire_rl.cli --config FILE --out NEW_DIR`.
`python -m wildfire_rl.checkpoint_audit ZIP [ZIP...]` čita metadata bez deserializacije.
`python -m wildfire_rl.train --steps 1024 --out NEW_DIR`: optional smoke, 64..1024,
koraci u višekratnicima 64. Nema automatskog dugog treniranja.

Gym: `reset(seed=) -> (dict observation, info)`;
`step(action) -> (observation, reward, terminated, truncated, info)`.
Budžeti/seeds zadani konstruktorom; reset options nisu podržani.
Open Questions: glavni adapter nakon simulator gatea.
