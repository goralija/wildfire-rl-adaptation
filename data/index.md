# Podaci i provenance

- [Originalna FPA-FOD train/validation kohorta](manifests/fireline-benchmark-cohort-v1.json) - lokalni FEDS audit za staru 60-case kohortu: 19/40 train, 7/20 validation (pada); aktivni širi okvir je sljedeća stavka.
- [FPA-FOD kandidat-frame](manifests/fpa-feds-candidate-frame-v1.json) - svi spremljeni train 2018/2019 i validation 2023 screen zapisi; bez test 2024.
- [FEDS epizode za no-op poređenje](manifests/feds-episode-cohort-v1.json) - 98 train i 20 validation požara (jedan zapis po FEDS požaru, ADR-030 §6; columbus isključen kao duplikat sugar-pine) s punim FEDS 48h referentnim tokom; data coverage prolazi, ali TRAIN no-op screen ne prolazi poređenje s referencama; nije fizička validacija.
- [SimFire/FEDS input/runtime record](../docs/research/SIMFIRE_ENVIRONMENT.md) - Python 3.9.25 venv, aktivne fronte, 180m mreža, LANDFIRE i gridMET provenance.
- [CFSDS pilot cohort manifest](manifests/cfsds-v1_1-pilot-cohort.json) - historijska Cell2Fire putanja i prvi stvarni replay.

## Dokumenti

- [Podaci, porijeklo i Git politika](README.md) - Dataset Reference
