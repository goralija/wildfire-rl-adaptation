---
type: Experiment Report
title: Sintetičko CA okruženje — trening i jednokratni test (ADR-028)
---
# Sintetičko CA okruženje — trening i test

Rezultati treninga na sintetičkim požarima i jednokratnog testa na stvarnim FEDS
slučajevima. Svi ishodi su simulirani; ništa nije fizička validacija. Odluke i brojevi
su u ADR-028 i njegovim dopunama u [odlukama](../../docs/specs/DECISION_RECORDS.md).

- `acceptance-main1-best.json` - PPO od nule protiv heuristika, sjemena 0–255: FAIL.
- `acceptance-policy-v1.json` - BC + PPO; izjednačeno s direct_flank (FAIL), jasno bolje od no-op.
- `real-cases-test-v1.json` - 119 FEDS startova, zaključane politike, jednokratno.
- `calibration-gap-v1.json` - no-op CA protiv opaženih FEDS perimetara, 12–48h.
- `main-1-validation.jsonl`, `ft-1-validation.jsonl` - validacijske krive (sjemena 0–63).
- `bc-2-log.json` - imitacija direct_flank, 40 rundi.
- `policy-v1.sha256`, `bc2.sha256`, `main1-best.sha256` - SHA-256 zaključanih modela.
  Težine nisu u gitu; nalaze se kao prilozi draft GitHub releasea `synthetic-policy-v1`
  (vidljiv samo članovima s pristupom repou), a postupak je opisan u [HANDOFF](../../HANDOFF.md).
