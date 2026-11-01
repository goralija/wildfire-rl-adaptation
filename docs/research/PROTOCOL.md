---
type: Research Protocol
title: Protokol — stvarni požarni uslovi u SimFire-u
status: draft-provisional
sources:
  - resource: /docs/DESIGN.md
  - resource: /docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md
  - resource: /docs/specs/DECISION_RECORDS.md
---
# Protokol: historical ignition scenarios + SimFire policy comparison

Ovaj draft zamjenjuje obavezni BurnMD historical-action replay iz ranijeg protokola.
Prethodni CFSDS/Firehose protokol je sačuvan u
[arhivi](PROTOCOL_CFSDS_ARCHIVE.md). Trenutna odluka je [ADR-040](../specs/DECISION_RECORDS.md#adr-040--train-on-real-ignition-conditions-with-simulated-actions-2026-11-01).

## Pitanje

Da li se base PPO dodatno naučen na real-fire-derived scenarijima ponaša bolje u SimFire-u
od svog zamrznutog početnog modela i jednostavnih pravila, kada svi dobiju iste početne
uslove, weather, trajanje i linijski budžet?

Primarni ishod je razlika u **simuliranoj** opožarenoj površini. Historijski konačni obod
ne postaje cilj za štimanje ni reward. Ne zaključujemo direktno o tome koliko bi se stvarni
požar promijenio.

## Jedan scenario i ulazi

- Incident je jedinica selekcije i train/validation/test splita.
- Prvi dataset za širi uzorak je kandidat USFS FPA-FOD: zvanični source ID, verzija, datum,
  lokacija i lokacijska preciznost moraju biti sačuvani. Koordinata nije automatski tačna
  na 30 m.
- Za svaki incident koristimo fiksnu veličinu prozora oko reported ignition. Kasniji obod
  ni linije ne određuju koji dio karte agent vidi.
- Fuel, elevation i weather se uzimaju iz posebno navedenih izvora. CRS, vintage, grid,
  timezone, jedinice, mapping i SHA-256 se bilježe u
  [scenario manifestu](../../data/manifests/simfire-scenario.schema.json).
- Agent ne dobija konačni fire-size, kasnije fire perimeter ni ljudske akcije. Ti slojevi
  mogu biti prikazani sa strane kao historijski kontekst.
- Ne napredovati dok fali verified scenario input; ne popunjavati izmišljene weather ili
  fuel vrijednosti kao stvarne.

## Agenti, budžet i kontrole

- **Base:** PPO naučen na raznovrsnim SimFire funkcionalnim scenarijima.
- **Fine-tuned:** kopija istog base checkpointa, dodatno učena samo na TRAIN incidentima
  kroz simulatorove nagrade.
- **Kontrole:** no-action i barem jedna unaprijed definisana linijska heuristika.
- Svi koriste iste observation/action semantike, kraj horizonta, scenario ulaze, seedove,
  budžete i simulator verziju. Potrošen budžet ne prekida širenje požara.
- Budžet je simulirana količina poteza/dužina linije, osim ako se zasebno dokažu odgovarajući
  stvarni crew/hour podaci.

## Event-level split

1. Definisati kriterije kohorte bez pokretanja politike.
2. Deduplikovati fire records i crosswalk ID-jeve, sačuvati izvornu lokacijsku nesigurnost.
3. Dodijeliti cijeli incident train/validation/test dijelu; ništa iz istog požara ne smije
   procuriti kroz drugi dan, crop ili tile.
4. Sačuvati split manifest i hash prije treninga. Test incidenti se ne koriste za izbor
   fuel/weather vintagea, horizon, wind parametara ili policy hyperparametara.

## Validacija i vizualizacije

Prvi gate je **input integration**, ne historical-action replay: jedan incident mora
učitati stvarne fuel/elevation/weather podatke, mapirati ignition u grid, završiti bez
greške i sačuvati receipt/hash. Zatim QA pregledava lokaciju, skalu, fuel klase, no-data i
weather jedinice.

Izlaz prikazuje ulazni raster, prijavljeno paljenje i precision napomenu, simuliranu
vatru/akcije kroz vrijeme, budžet, seed i geografski scale bar. Ako se pokaže finalni
historijski perimeter, to je odvojena linija/reference i nije model reward target.

Primarno: simulirana opožarena površina po paru scenario/seed; razlika fine-tuned minus
base. Dodatno: dužina linije, potrošen budžet, aktivni front, vrijeme do zaustavljanja ili
horizonta, i interval neizvjesnosti kroz više incidenata. Nema jedne odabrane animacije bez
tabele svih evaluiranih incidenata.

## Faze i gates

1. Zamrznuti mali, licencno pregledan FPA-FOD uzorak i event-level split.
2. Napraviti jedan manifest i pribaviti verified fuel, elevation i historical weather.
3. Pokrenuti jedan real-input SimFire integration smoke i provjeriti kartu/receipt.
4. Instalirati/pinovati kompatibilan SimHarness/RLlib ili dokumentovani Gym adapter; kratko
   CPU smoke prije treninga.
5. Definisati budget semantics/no-op/heuristic i zamrznuti train/held-out manifests.
6. Naučiti base PPO i fine-tuned kopiju; paired held-out runovi i vizualizacije.

Trening ne počinje prije faza 1–5. Mineral BurnMD action replay može se paralelno istražiti
ako se pronađe pouzdan timestamp izvor; to nije gate glavnog ogleda.

## Ograničenja

SimFire predstavlja pojednostavljenu fiziku. I FPA-FOD ignition i weather imaju prostorno/
vremensku nesigurnost. Rezultat odgovara samo na pitanje „koji agent je imao manje štete u
ovim podešenim simulacijama?“ Ne dokazuje da je alternativni potez u stvarnom požaru
uzročno smanjio konačnu površinu.
