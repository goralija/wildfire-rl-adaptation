---
type: Reference
title: OKF 0.2 profil ovog repozitorija
description: Primijenjeni format, kanonski izvor, granice provjere i pravila pisanja metapodataka.
status: stable
generated: {by: "process:codex", at: "2026-10-28T12:55:34Z"}
sources:
  - id: okf-spec
    resource: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/ad30107c31c06aec8a7d5636e0d1058118604e6f/SPEC.md
    title: Open Knowledge Format v0.2 specification
  - resource: /scripts/validate_knowledge.py
---
# OKF 0.2 u ovom projektu

Bundle root je korijen repozitorija. Specifikacija je pinovana na Google Cloud
commit `ad30107c31c06aec8a7d5636e0d1058118604e6f`, ne na promjenjivi main.[^okf-spec]
[Mašinski čitljiv projektni profil](okf-profile.json) bilježi pin i granicu bundlea;
taj JSON je naš dodatak, nije obavezni OKF konfiguracijski fajl.

## Primijenjeni format

- Javni Git-visible `.md` fajlovi su koncepti s YAML frontmatterom i nepraznim `type`.
  Tipovi su otvoreni; naslov/opis/status i ostali podaci su dodatni, ne obavezni svuda.
- `index.md` i `log.md` su rezervisani lowercase nazivi. Root index deklarira
  `okf_version: "0.2"`; indeksi služe navigaciji, a log ima najnovije ISO-datumske unose prvi.
- Veze u tijelu su obični Markdown linkovi, uglavnom relativni radi GitHub prikaza.
  Koncept ID je putanja bez `.md`. U metadata `sources` koristimo bundle-relative
  putanje s početnim `/` ili javne URL-ove.
- `sources` navodi stvarno korištene materijale. `generated` bilježi poznatog autora/
  proces trenutnog sadržaja; `verified` samo stvarne provjere. Datetime provenance
  koristi eksplicitan UTC offset. Nepoznate historijske datume/verifiere izostavljamo.

Ove konvencije dolaze iz pinovane specifikacije.[^okf-spec] Postojeći sadržaj je
sačuvan, uz tip/naslov i odabrane poznate izvore. Migracija ne tvrdi novo autorstvo
ili novu sadržajnu verifikaciju ranijih dokumenata.

## Projektna provjera i šta znači rezultat

[Validator](../scripts/validate_knowledge.py) koristi PyYAML safe loader, ne izvršava
Markdown/YAML sadržaj i nema mrežu. U Git klonu uzima samo neignorisane Markdown
fajlove; u izdvojenom folderu bez `.git` provjerava cijelo `.md` stablo. Zato u takav
export ne uključivati ignorisane raw/private/venv foldere.

```sh
python3 -m pip install -r requirements/knowledge.txt
python3 scripts/validate_knowledge.py
python3 scripts/validate_knowledge.py --strict
```

Osnovna provjera pokriva primijenjene OKF strukture i korištena provenance polja.
`--strict` dodatno provjerava lokalne ciljeve i dostupnost svih koncepata iz root
indeksa: to je projektni kvalitet navigacije, nije univerzalni OKF uslov. Validator
nije potpuna implementacija svih opcionalnih attestation/computation porodica;
ovaj bundle ih ne koristi. Ne dodavati `Attested Computation` bez stvarnog ugovora i
proširenja odgovarajućih provjera. Nedostajući link je dozvoljen u osnovnom OKF čitanju.

Prolazak provjere znači strukturnu ispravnost i, u strict modu, lokalnu navigaciju.
Ne dokazuje fiziku simulatora, brojke, rezultate eksperimenata ili ljudsku potvrdu.
Pravila održavanja i jedinstveni izvori istine su u [maintenance](maintenance.md).

[^okf-spec]: [Kanonska pinovana specifikacija](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/ad30107c31c06aec8a7d5636e0d1058118604e6f/SPEC.md), posebno §3–9 i §11–12.
