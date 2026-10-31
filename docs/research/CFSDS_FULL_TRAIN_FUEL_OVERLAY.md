---
type: Experiment Report
title: Full TRAIN CFSDS fuel-class overlay
status: stable
sources:
  - resource: /scripts/audit_cfsds_full_train_fuel_overlay.py
  - resource: /reports/real-fire-data/cfsds-full-train-fuel-overlay.json
  - resource: /reports/real-fire-data/cfsds-full-train-fuel-overlay.csv
  - resource: /reports/real-fire-data/cfsds-train-full-day-pair-screen.json
  - resource: /reports/real-fire-data/canfg-fuel-archive-member-review.json
---
# Full TRAIN CFSDS fuel-class overlay

## Pitanje i laičko značenje

Koliko unaprijed izabranih TRAIN slučajeva možemo prostorno preklopiti preko dostupne
Canadian FBP karte goriva, a da se početno stanje požara ne oslanja na sutrašnji požar?

Kao da provjeravamo da li početni dio slagalice stane preko karte: gledamo ranije
opožarenu površinu i ivicu na dan prije predviđanja. Kartu goriva iz 2014b zatim
provjeravamo ispod tih ćelija. Prolaz znači samo da se vidljive ćelije slažu s podržanim
klasama na toj karti. Ne znači da je karta stvarno važila za tu godinu, da simulator
pravilno širi požar, niti da je slučaj spreman za učenje agenta.

## Postupak

- Ulaz je svih 1.301 red iz postojećeg [target-independent day-pair screena](CFSDS_FULL_DAY_PAIR_SCREEN.md).
  Ne biramo nove događaje, dane ili prozore. Taj screen je unaprijed izabrao najraniji
  ulazni dan s barem tri 90 m piksela i zatim naredni kalendarski dan kao ishod.
- Zadržavamo fiksnu mrežu **20×20 ćelija po 100 m**. Izvorni cilj-prozor je 23×23 ćelije
  po 90 m; 1.295 od 1.301 rastera mogu ga smjestiti.
- Početni požarni ožiljak i aktivni dan-n−1 front grade se funkcijom
  `derive_pre_target_state_masks`. Ona koristi samo oznake prije dana `n`, a vanjski
  prsten početnog prozora ostaje historijski ožiljak. Ciljna maska dana `n` računa se
  odvojeno, tek kao provjera ishoda nakon izbora para i prozora.
- Canadian FBP raster v2014b preslikava se najbližom klasnom vrijednošću na izvorni
  90 m prozor i na modelsku mrežu. Požarni piksel ili većinska modelska ćelija na vodi,
  ne-gorivu, nejasnoj ili nepokrivenoj klasi označava neprolaz. Površinski preklop koji
  je manji od pola ćelije posebno se označava za pregled.
- Nema čitanja Firegrowth tabela, simulatora, validation/test godina, C++ replaya,
  treniranja ni kalibracije.

## Nalaz

| Provjera | Broj slučajeva | Značenje |
| --- | ---: | --- |
| Početni ožiljak/front prolazi samo provjeru klase goriva | 701 | Nema preklopa na zabranjenoj klasi; vintage nije potvrđen |
| Početni ožiljak/front traži pregled manjeg preklopa ćelije | 64 | Ne odbacuje se bez pregleda |
| Početni ožiljak/front pada provjeru klase goriva | 530 | Voda, ne-gorivo, nejasna ili nepokrivena klasa ispod požarnih ćelija |
| Fiksni prozor nije moguće postaviti | 6 | Existing 20×20/100 m skala ne stane u izvorni raster |
| Modelska većinska front/cilj geometrija susjedna je i bez rubnog dodira | 477 | Samo prostorni par na izabranoj skali; nije replay-gate prolaz |

Za 1.010 slučajeva CFSDS prikazuje neke požarne piksele na ciljnom danu negdje u
izvornom rasteru; kod 930 slučajeva dio susjednog cilja ulazi u odabrani prozor. Ta
provjera koristi budući ishod samo nakon odabira, zato je dijagnostika, a ne dokaz da je
uzorak ili model podešen bez curenja.

Od tih ciljnih maski u prozoru, 583 prolaze samo klasu goriva, 68 traži pregled, a 279
je na nekompatibilnoj klasi. U 365 prozora nema susjedne ciljne maske; to ne znači da
cijeli požar nije rastao, nego da taj model-prozor nema takvu opaženu masku. Još šest
slučajeva nema model-prozor.

## Tumačenje za projekat

**2014b karta ne može još postati odobren ulaz.** Rezultat sužava prostorni problem:
701 prozor prolazi samo klasni preklop na postojećoj karti. Međutim, pouzdanost da je
v2014b bila vremenski ispravna za te konkretne požare nije utvrđena. Ne koristimo ove
701 kao gotovu kohortu, ne pravimo godišnje fuel karte i ne pokrećemo replay dok se ne
riješe vremensko porijeklo goriva i ostali ulazi.

Puni rezultat ima [zbirni JSON receipt](../../reports/real-fire-data/cfsds-full-train-fuel-overlay.json)
i [pojedinačni CSV za svih 1.301 par](../../reports/real-fire-data/cfsds-full-train-fuel-overlay.csv).
JSON bilježi izvorne hashove, verzije biblioteka, pravilo i agregate; CSV čuva
kompaktan status po događaju bez kopiranja velikih međurezultata.

## Ponovljivost

Iz repozitorija pokrenuti:

```sh
.venv/bin/python scripts/audit_cfsds_full_train_fuel_overlay.py \
  --raw-root data/raw/cfsds-v1_1 \
  --fuel-zip data/raw/cwfis-fuels/National_FBP_Fueltypes_version2014b.zip
```

Zahtijevaju se ignorisane CFSDS TRAIN arhive i v2014b fuel ZIP iz javnog CWFIS izvora.
Sirovi rasteri nisu dio Gita. Službena arhiva v2014b i inventar detalja su u
[source-gate pregledu](CFSDS_FUEL_VINTAGE_REVIEW.md) i
[mašinskom inventaru ZIP paketa](../../reports/real-fire-data/canfg-fuel-archive-member-review.json).
