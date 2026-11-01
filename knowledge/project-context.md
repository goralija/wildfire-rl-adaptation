---
type: Project Context
title: Projektni kontekst — stvarna požarna okruženja u SimFire-u
description: Aktivni dizajn, kohorta, RL adapter i otvoreni uslovi prije treninga.
status: current
sources:
  - resource: /docs/STATUS.md
  - resource: /docs/research/SIMFIRE_FPA_COHORT.md
  - resource: /docs/research/SIMFIRE_RL_ADAPTER.md
  - resource: /docs/specs/DECISION_RECORDS.md
---
# Projektni kontekst

## Jedna rečenica

Uporediti PPO agenta i dodatno učenog PPO agenta u SimFire-u, pri čemu se mape i početni
uslovi scenarija izvode iz stvarnih požara, a agentova iskustva i nagrade dolaze iz
simulacije.

## Trenutni dizajn

- 80 FPA-FOD požara: 40 train / 20 validation / 20 test; cijeli incident ostaje u jednom
  split-u.
- Stvarni pre-event LANDFIRE FBFM13 fuel i elevation rasteri za svih 80; fiksni projected
  UTM grid, 128×128, 30 m ćelije.
- Pinovani SimFire 2.0.1, Python 3.9.25, Gymnasium/SB3/sb3-contrib adapter i CNN politika.
- Agent bira no-op ili jednu 30 m fireline tačku. Jedna akcija troši jedan budžet; nema
  kretanja posade ni vremena gradnje u prvom adapteru.
- FPA final size i MTBS perimetri ostaju samo post-result kontekst, izvan agenta i rewarda.

## Šta je spremno, a šta nije

Fuel i terrain su preuzeti/hash-provjereni za svih 80 požara. Osam dnevnih gridMET polja
postoji za svih 80, a odvojeni weather proxy priključen je u adapteru. Proxy koristi
približno 10 m→20 ft vjetar, WAF 0.3, obrtanje smjera vjetra i Simard EMC procjenu iz dnevne
max temperature/min RH. WAF 0.1/0.3/0.5 smoke prolazi tehnički. To ne potvrđuje lokalni
vjetar ili stvarnu vlagu goriva; dnevni gridMET (~4 km) nije satni replay.

Proxy adapter, rasteri i Gymnasium smoke su pokretljivi; `learn()` nije pozvan i težine ne
postoje. Baseline, evaluacijski seedovi i test protokol nisu zamrznuti. Vidi [status](../docs/STATUS.md),
[kohortu](../docs/research/SIMFIRE_FPA_COHORT.md), [adapter](../docs/research/SIMFIRE_RL_ADAPTER.md)
i [mapping receipt](../reports/real-fire-data/simfire-cohort-v2-gridmet-simfire-mapping.json).
Adapter koristi 15 jednominutnih koraka kao maksimalno trajanje jedne ćelije vatre; stock
četiri koraka su se gasila prerano u jednom 30 m primjeru. To je inženjerska postavka,
ne potvrđena požarna fizika. Test slučaj Larch Creek je korišten u smoke-u i izostavlja se
iz završne procjene; 19 test incidenata ostaje zatvoreno. Trening nije počeo.

## Granice tvrdnje

Rezultat eventualno može reći da je određena politika smanjila **simulirano** opožareno
područje na zamrznutim test scenarijima. Ne može reći da bi požar u stvarnosti bio manji za
isti iznos. Dodatna otvorena odluka: da li istraživački cilj ostaje “historijski uslovi” ili
se sužava na stvarne mape/lokacije uz unaprijed izabranu kontrolisanu simuliranu atmosferu.
