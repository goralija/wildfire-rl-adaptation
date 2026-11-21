---
type: Experiment Report
title: TASK-042 — prošireni zamrznuti TRAIN audit rasta
sources:
  - resource: /configs/frozen/expanded-observed-growth-v1.json
  - resource: /docs/research/PAIRED_OBSERVED_GROWTH.md
---
# Zamrznuti SimFire/CA rast na svih61 kompatibilnih TRAIN početaka

2026-11-21: korisnik odobrava TASK-042 iz ADR-046. Nova grana
`codex/ca-expanded-growth-audit`, baza2de00136. [Plan](../../configs/frozen/expanded-observed-growth-v1.json)
i ADR-047 prethode novim simulacijama i scoringu. Nema novih rezultata ili podešavanja.

**Pretpostavka:** povoljniji razmjer CA na16slučajeva treba provjeriti na cijelom
unaprijed poznatom kompatibilnom TRAIN okviru. To nije novi holdout ili test svih98.
**Provjerljiv cilj:** svih61eligible ID-jeva iz TASK-040 ulaznog QC-a, isti početni
scar/front, puna256mreža180m,48h, zamrznuti SF i3CA spread seeda, iste growth metrike.

Prethodnih16prediction NPZ-a kopiraju se samo uz originalni receipt/hash/runtime/source
provjeru, s eksplicitnim provenance zapisom. Preostalih45daje180novih no-op putanja.
Pilot su prva2nova ID-ja po unaprijed zadanom redoslijedu. Svi45novi SF endpointi moraju
biti identični originalnoj98TRAIN arhivi; prvi novi CA slučaj ponavlja sve3replike i5maski.
Nema scoringa dok svi backend-i nisu zaključani. Najviše3radnika uz koordinaciju,
nice19/jedna nit, najavljeno5–15min plus testovi. Ne učitavaju se PPO težine.

Primarno ostaje raw48h mean new-area IoU na istim observed-positive slučajevima i mean
apsolutna greška novih hektara na svim potpunim slučajevima, CA0primaran. Sve3CA replike
i njihov srednji scalar rezultat prijavljuju se kao ranije. Zasebno fully-covered,
prethodnih16/novih45 i grupe: nulti rast; pozitivan rast manji od10%početne scar|front
površine; rast najmanje10%. To je nova eksplicitna grupa prema novim ćelijama, različita
od starog total-area ratio gatea ako FEDS izgubi ranije ćelije. Slučaj se ne izbacuje
po rezultatu, missing nije0, nulti nazivnik nijeepsilon, rubno cenzurisanje ostaje vidljivo.

Plan5d72b974 prethodi implementaciji/scoringu;7novih testova prolazi, prvi red log
je sačuvan prije modula. Nema duplih selected FEDS fire/time ključeva.

Status: plan prije implementacije/scoringa. Native PPO faza B i TASK-039 nisu riješeni.
Nema kalibracije, dugačkog treninga, stvarnog VALIDATION/TEST ili tvrdnje fizičke validacije.
