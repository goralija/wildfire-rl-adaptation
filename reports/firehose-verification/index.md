# firehose-verification

## Dokumenti

- [Izvršena Firehose provjera](README.md) - Experiment Report
- [Regression provjera novog real-case imagea](real-case-image-regression.json) - 12 ponovljenih Sub20 inference slučajeva.
- [TASK-004c adapter smoke](task004c-adapter-smoke.json) - fixture + 12 inference slučajeva; terminal/C++ i Python cumulative-state provjera.
- [NF initial-scar compatibility](nonfuel-initial-scar-compatibility.json) - historijski expected-rejection zapis prije izmjene ugovora.
- [NF initial-scar contract](nonfuel-initial-scar-contract.json) - `scar_nf` prihvata samo eksplicitno označenu historijsku štetu na `NF`; tri neispravna slučaja se odbijaju, a puni sintetički rollout potvrđuje da NF ne ulazi u aktivni front.
