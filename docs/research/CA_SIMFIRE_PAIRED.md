---
type: Experiment Report
title: TASK-040 — upareno SimFire i CA poređenje
---
# Upareno SimFire i CA poređenje

Korisnik je zatražio isti početni požar i procentualne učinke, ne samo jaz agenta prema
heuristici. Plan [ADR-043](../specs/DECISION_RECORDS.md) i [JSON](../../configs/frozen/ca-simfire-paired-v1.json)
prethode CA rezultatima. Radi se na codex/ca-simfire-paired iz722d5f2d.

Prvi cilj je common-control bridge: isti16TRAIN požari, puna mapa,48h, isti kapacitet
jedne linije, ista opažanja i obračun. Native CA unit PPO i SimFire sector PPO nisu
istovjetni i ne rangiraju se ovim pilotom. Novi mali RBF agent je isti postupak u oba
backend-a. Nema nove fizičke validacije ili PPO treninga. Rezultati još nisu izvršeni.
