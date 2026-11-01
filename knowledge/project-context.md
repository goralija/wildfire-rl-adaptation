---
type: Project Context
title: Projektni kontekst — stvarne lokacije požara u SimFire-u
description: Kratki trenutni ulaz u cilj, izbor, izvedene provjere i naredni korak.
status: current
sources:
  - resource: /docs/STATUS.md
  - resource: /docs/DESIGN.md
  - resource: /docs/specs/DECISION_RECORDS.md
---
# Projektni kontekst

## Jedna rečenica

Poredimo base i fine-tuned agenta koji postavljaju vatrogasne linije u istoj SimFire
simulaciji, a scenarije gradimo iz stvarnih požarnih lokacija/datuma i okolišnih podataka.

## Trenutni dizajn

- **Prijavljene lokacije incidenata:** USFS FPA-FOD je kandidat za malu, version-pinned
  kohortu; tačka nije nužno potvrđeno mjesto paljenja, a preciznost može biti samo PLSS sekcija.
- **Simulacijski ulazi:** LANDFIRE fuel/elevation + zaseban historijski weather, na istom
  georeferenciranom gridu i sa sačuvanim jedinicama/hashovima.
- **Simulator:** MITRE SimFire 2.0.1 radi u lokalnom Python 3.9.25 venvu; SimHarness/RLlib
  još nije instaliran.
- **Agent:** PPO base i kopija dodatno učena samo na cijelim TRAIN incidentima.
- **Historijski obod/linije:** zasebna kontekstna/replay referenca, ne agentov input ni
  reward u trenutnom protokolu.
- **X/Y format:** [scenario JSON schema](../data/manifests/simfire-scenario.schema.json)
  povezuje izvorni incident s weather/raster fajlovima i simulator postavkama.

Običnim jezikom: [pipeline](../docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md).

## Zašto više ne čekamo BurnMD line-time replay

Mineral Fire audit ima geometrije linija, ali nema pouzdanih vremena njihove gradnje.
`LineDateTi` je prazan za svih 249 linija, a `CreateDate` je vrijeme datoteke/feature zapisa,
ne dokaz kada je ekipa radila. To znači da line replay danas zahtijeva nagađanje. Glavno
pitanje se zato mijenja: učimo i poredimo agenta na simuliranim fire-control zadacima u
scenarijima koji polaze od stvarnih događaja, bez lažne tvrdnje da ćemo ponoviti historiju.

Prethodni CFSDS/Firehose nalazi ostaju arhivirani. BurnMD je dodatna lokalna referenca;
njegova prava na reuse još nisu potvrđena.

## Status i granice

SimFire funkcionalni demo, BurnMD archive/schema audit i fixed-size event-location AOI dry-run su
gotovi. Jedan stvarni FPA-FOD zapis (Dixie 2021) pretvoren je u development scenario-karticu
i provučen kroz AOI dry-run; nije train/test primjer. Ne postoji real fuel/terrain/weather
SimFire run, šira FPA kohorta/split, SimHarness/RLlib run ili trening. `LANDFIRE_EMAIL` nije
postavljen; zadnja provjera pokazala je 3.0 GiB slobodno (2026-11-01), pa je stari 29-MiB
navod zastario.

Izvještavati samo ono što je testirano u simulatoru. Ne pretvarati konačnu historijsku
požarnu površinu u agentovu reward vrijednost niti obećati da će realni požar biti manji.
Trenutna odluka: [ADR-040](../docs/specs/DECISION_RECORDS.md#adr-040--train-on-real-ignition-conditions-with-simulated-actions-2026-11-01), uz lokacijsko pojašnjenje u [ADR-042](../docs/specs/DECISION_RECORDS.md#adr-042--scenario-coordinates-keep-their-source-role-2026-11-01).
