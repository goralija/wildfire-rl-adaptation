# Izvori i literatura

Provjereno 2026-10-28. Primarni izvori; postojeći rad nije naš rezultat.

| ID | Izvor | Uloga / ograničenje |
| --- | --- | --- |
| S-001 | [Firehose projekat, Shen & Curtis, 2022](https://williamshen-nz.github.io/firehose/) | polazni rad, baseline i već postojeće priority zone |
| S-002 | [Firehose rad](https://williamshen-nz.github.io/firehose/firehose-paper.pdf) | definicija idealizirane intervencije i eksperimenti; studentski projektni izvještaj |
| S-003 | [Firehose izvor](https://github.com/aidan-curtis/firehose/tree/e49a52a9a987a1585d25ddca2f711222ca500ffb) | pregledani kod i modeli, pin u manifestu |
| S-004 | [Pais et al., Cell2Fire, 2021](https://doi.org/10.3389/ffgc.2021.692706) | naučna osnova simulatora; nije validacija našeg adaptera |
| S-005 | [Originalni Cell2Fire](https://github.com/cell2fire/Cell2Fire) | build dokumentacija i upućivanje na drugi fork |
| S-006 | [MITRE SimFire](https://github.com/mitrefireline/simfire), [docs](https://mitrefireline.github.io/simfire/) | alternativni Python backend; ovdje nije instaliran ni benchmarkovan |
| S-007 | [MITRE SimHarness](https://github.com/mitrefireline/simharness) | alternativni RL harness; nema dokaza prenosa Firehose težina |
| S-008 | [Fire2A C2F-W](https://github.com/fire2a/C2F-W) | drugi model goriva/razvoj; nije drop-in Firehose backend |
| S-009 | [Schulman et al., PPO, 2017](https://arxiv.org/abs/1707.06347) | razlog izbora PPO porodice, ne obećanje učinka |
| S-010 | [Huang & Ontañón, 2020](https://arxiv.org/abs/2006.14171) | teorija i empirija invalid action masking |
| S-011 | [Agarwal et al., 2021](https://arxiv.org/abs/2108.13264) | motivacija za intervale i više treninga |
| S-012 | [Gymnasium custom env](https://gymnasium.farama.org/introduction/create_custom_env/) | trenutni reset/step kontrakt, provjeren kroz Context7 |
| S-013 | [MaskablePPO dokumentacija](https://sb3-contrib.readthedocs.io/en/master/modules/ppo_mask.html) | maske pri učenju i predict/evaluation |

Činjenice iz korisničke prepiske i slike imaju lokalnu provenance evidenciju, ne javni URL.

## Razlika prema polaznom radu

Firehose već obuhvata CNN politike, maskiranje, više ignition postavki i prioritetne
nagrade. Naš predloženi doprinos je kontrolisano ispitivanje adaptacije preko budžeta,
uz jasne troškove, kumulativnu štetu, uparene scenarije i analizu ukupne/prioritetne
štete. Originalnost tog uskog doprinosa još zahtijeva širi pregled literature prije
konačne tvrdnje; nije provedena sistematska literature review.

## Runtime continuation sources
- [Autorski SB3 contrib fork](https://github.com/williamshen-nz/stable-baselines3-contrib/tree/43b7fe6fcdda71c2c10de7af0d20f39e48ae5df3): stvarno korišten, verzija 1.5.0.
- [PyTorch 1.13.1 release files](https://pypi.org/project/torch/1.13.1/): potvrđen ARM64 Linux wheel za legacy runtime.
- Checkpoint `system_info.txt`, lokalni C++/Python kod, dataset fajlovi i izvršeni
  stdout/JSON su primarni dokazi nastavka; receipti i hashovi su u reports/firehose-verification/.

## Historijski požari: izvori pregledani 2026-10-28

- S-014: [Kim, Pais & Gonzalez, 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12254405/),
  DOI 10.1038/s41598-025-05706-6; Dogrib kao Cell2Fire validacijski slučaj.
  [Podaci i kod](https://github.com/humnetlab/Cell2Fire/tree/84e3c817ad866358d8db28e87c9445b42aaf7908),
  pin 84e3c817…; zasebno pregledan originalni Dogrib_v624 README (Alberta, 2019-02-03).
- S-015: [Barber et al., 2024, CFSDS](https://pmc.ncbi.nlm.nih.gov/articles/PMC11239873/),
  DOI 10.1038/s41597-024-03436-4; [OSF podaci](https://osf.io/f48ry/),
  DOI 10.17605/OSF.IO/F48RY. Rad opisuje v1; [version record](https://osf.io/download/8fe4u/)
  dokumentuje v1_1 od 2025-06-12. Provjeren javni OSF API: projekt, fajlovi i
  [deklarisana CC-BY 4.0 licenca](https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e96a/).
- S-016: [Gerard, Zhao & Sullivan, WildfireSpreadTS](https://zenodo.org/records/8006177),
  DOI 10.5281/zenodo.8006177; [autorski code/loader](https://github.com/SebastianGer/WildfireSpreadTS).
  Pregledani javni metapodaci; arhiva nije preuzeta niti očišćena u ovom projektu.
- S-017: [MITRE BurnMD](https://github.com/mitrefireline/burnmd/tree/a9e423f15906bc9860be6d80b56e71e4a6ee307c),
  samo LFS metapodaci, mogući SimFire fallback; sadržaj arhive nije pregledan.

[REAL_FIRE_DATASETS](REAL_FIRE_DATASETS.md) čuva preporuku, obim uzorka i nedostatke;
reports/real-fire-data/ čuva download SHA256 i provjere stvarno preuzetih fajlova.
