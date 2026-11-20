---
type: Experiment Report
title: TASK-038 — kratki CA v2 BC/PPO pilot
---
# Kratki CA v2 BC/PPO pilot

Plan zabilježen2026-11-21 prije treninga: [ADR-041](../specs/DECISION_RECORDS.md) i
[zamrznuti protokol](../../configs/frozen/ca-learning-pilot-v1.json). Grana
`codex/ca-learning-pilot`, baza3b7b56a2.32TRAIN slučaja, tri model seeda, fiksni BC60epoha
pa4.096PPO koraka; ocjena oba finalna kandidata na16development požara i3rostera.
Rezultati još nisu pokrenuti. Zatvoreni su proceduralni test i svi stvarni holdouti.
CA je sintetički model bez fizičke validacije. Nema starih checkpointova.
