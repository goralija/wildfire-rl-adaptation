---
type: Experiment Report
title: RL smoke — samo tehnički dokaz
---
# RL smoke — samo tehnički dokaz

CPU, novi MaskablePPO, 6×6 synthetic, 1,024 koraka. Learn/save/load i masked rollout
izvršeni. Nema pretrained težina ili fine-tuninga. Smoke rollout je iz training
distribucije, ne held-out evaluacija. Checkpoint je lokalno u runs/rl-smoke-final/,
a u Git ide samo mali manifest sa hashom i environmentom.
