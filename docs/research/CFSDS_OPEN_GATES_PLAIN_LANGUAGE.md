---
type: Explainer
title: Zašto stvarni CFSDS simulator još nije spreman za trening
description: Laičko objašnjenje svakog otvorenog istraživačkog uslova i dokaza koji bi ga zatvorio.
status: current
sources:
  - resource: /docs/STATUS.md
  - resource: /docs/research/EXPERIMENT_LOG.md
  - resource: /docs/specs/DECISION_RECORDS.md
---
# Zašto stvarni CFSDS simulator još nije spreman za trening

## Ukratko

Program možemo pokrenuti. Problem nije instalacija simulatora: problem je što za
odabrane stare požare još ne znamo da li su ulazna karta goriva i poređenje s opaženim
požarom vremenski i fizički pošteni. Trening sad bi pokazao samo da agent radi u jednoj
nepotvrđenoj simulaciji; ne bi dokazao da bi stvarno spasio šumu.

| Pitanje | Šta znamo običnim jezikom | Šta bi ga stvarno zatvorilo |
| --- | --- | --- |
| Radi li softver? | Da. Cell2Fire i postojeći agenti se izvršavaju. To dokazuje da se program pali, ne da dobro oponaša prirodu. | Već zatvoreno kao tehnički uslov; fizičko poređenje je zasebno. |
| Jesu li vremenski indeksi opasnosti od požara pouzdani? | Našli smo provjerljiv kanadski dnevni izvor. U tri iste kopije simulatora promjena tih indeksa promijenila je broj novih modelskih ćelija za −3, 0 i 0. Sve tri simulacije i dalje su izašle do ruba male karte. | Daily FWI ulaz je spreman za buduće, dokumentovane slučajeve. Ovo ne popravlja pogrešno gorivo, gašenje ili premalu mapu. Vidi [EXP-025](EXPERIMENT_LOG.md#exp-025--era5-fwi-sn-daily-weather-paired-train-replays-2026-10-31). |
| Znamo li da su požari rasli bez gašenja? | Ne. Tri trenutna događaja su iz BC. Javne vijesti opisuju rad ekipa za najmanje dva; treći ima samo statusne izvještaje. Status “van kontrole” ne znači “niko nije gasio”. | Potreban je službeni zapis po incidentu i datumu o prvoj fizičkoj akciji/ekipama ili slučaj se mora isključiti iz čistog no-action poređenja. Nepoznat podatak ne računamo kao “nije bilo”. Vidi [EXP-024](EXPERIMENT_LOG.md#exp-024--wise-suppression-exclusion-and-national-burn-history-dating-2026-10-31). |
| Možemo li naći zapis o gašenju? | Alberta katalog oglašava tabelu s početkom fizičkog gašenja, ali download sada vraća 403. Dostupna Alberta karta ima lokaciju i status, ali ne vrijeme prve intervencije. To ne rješava BC požare koje trenutno imamo. | Dobiti zvaničnu fire-level tabelu za Alberta TRAIN događaj, povezati je po broju/godini/lokaciji i uzeti samo dan koji je strogo prije prve akcije. Ili naći drugi odgovarajući TRAIN izvor s istim dokazom. Vidi [EXP-026](EXPERIMENT_LOG.md#exp-026--alberta-suppression-source-schema-and-access-audit-2026-10-31). |
| Je li gorivo na karti isto kao na dan požara? | Nije dokazano. Oznaka `2014b` ne govori do kojeg su datuma ažurirani ožiljci. Novija karta koristi podatke koji sežu do 2018. i ne smije se samo prekopirati na stariji događaj. Korištenje kasnijih požara u ranijoj karti bilo bi kao da agent unaprijed zna šta će izgorjeti. | Potreban je dokumentovan cutoff stare karte ili izgradnja datumski ispravne karte iz izvora i pravila koja se mogu provjeriti po svakom pikselu. Sadašnji overlay je samo provjera da se klase goriva mogu preklopiti; nijedan kandidat time nije dobio puno odobrenje. Vidi [fuel pregled](CFSDS_FUEL_VINTAGE_REVIEW.md) i [EXP-023/024](EXPERIMENT_LOG.md). |
| Je li karta dovoljno velika? | Ne za ove tri simulacije. Mreža je 20×20 ćelija po 100 m, dakle otprilike 2×2 km. Svaka predikcija došla je do ivice. Kad vatra stigne do zida karte, model nema prostor da nastavi i izmjerena površina više nije čisto poređenje. | Treba unaprijed fiksirati veći geografski prostor, dokazati da cilj stane bez biranja po ciljnoj mapi i uskladiti ga s agentom. Predtrenirani agent očekuje 20×20 ulaz/400 akcija; samo povećanje karte mijenja problem i može zahtijevati drugu arhitekturu ili trening od nule. Vidi [prostorni audit](CFSDS_SPATIAL_FEASIBILITY.md). |
| Znamo li tačan sat kad su ćelije izgorjele? | Ne. CFSDS daje procijenjeni dan, ne tačan sat za svaku ćeliju. Zato se ne može provjeriti precizna satna putanja ili razlikovati širenje prije i poslije smjene vremena i ekipa. | Za dnevno poređenje prihvatiti i jasno navesti dnevnu nesigurnost; za satne tvrdnje potreban je gušći satelitski/operativni zapis. Ne izmišljati sat iz dnevne karte. |
| Možemo li reći “agent bi smanjio stvarnu štetu”? | Još ne. Požari su vjerovatno bili gašeni, a simulacija ih bez intervencije previše širi i udara u rub. Manja simulirana površina može značiti da agent dobro bira akcije, ali može značiti i da su mu pravila previše povoljna. | Prvo treba validan ulazni replay i realističan budžet/trošak akcija. Dok se to ne dokaže, poštena formulacija je “smanjio je simuliranu štetu u ovom modelu”, ne “spasio bi X hektara u stvarnosti”. |

## Zašto ne popuniti rupe pretpostavkom

Ako prazno polje gašenja proglasimo “nije bilo gašenja”, ako noviju kartu nazovemo
istorijskom ili ako pustimo vatru da izađe s ruba mreže kao da je to prirodni kraj, dobit
ćemo uredan broj, ali broj koji zavisi od naše pretpostavke. Agent bi mogao naučiti
artefakt karte, a ne bolju strategiju. Zato se “unknown” ne prevodi u “none”, a uspješno
pokretanje ne prevodi u fizičku validaciju.

## Put koji najviše štiti projekat

1. Zadržati 2018 kopije kao dijagnostiku; ne koristiti ih za dokaz agenta.
2. Za novi TRAIN kandidat unaprijed definisati target-blind dan/front i prostor.
3. Pribaviti event-keyed podatak o prvoj fizičkoj intervenciji; izabrati samo ciljni dan
   prije akcije ili označiti slučaj neupotrebljivim za no-action.
4. Pribaviti vremenski ispravnu FBP mapu i provjerljiva pravila za ranije ožiljke.
5. Napraviti kompletan ulaz s checksumovima; pokrenuti no-action replay i zahtijevati
   da rezultat ne udara u rub i da se slaže s opaženim dnevnim rastom u unaprijed
   registrovanoj toleranciji.
6. Tek tada zamrznuti held-out skup i porediti osnovnog i prilagođenog agenta.

Ako službeni zapisi potrebni za korake 3–4 nisu dostupni, “savršeno” rješenje nije
izmišljanje vrijednosti. Tada imamo dva poštena izbora: promijeniti izvor/dizajn studije
ili ograničiti tvrdnju na kontrolisani simulator. Trenutni `research_ready=false` je
tačan status, ne greška u instalaciji.

## Dokazi

- [Status i najnoviji rezultati](../STATUS.md)
- [CFSDS no-action analiza](CFSDS_NO_ACTION_DIAGNOSIS.md)
- [Fuel vintage i istorijski cutoff](CFSDS_FUEL_VINTAGE_REVIEW.md)
- [Cijeli train day-pair screen](CFSDS_FULL_DAY_PAIR_SCREEN.md)
- [EXP-025/026 i svi raniji eksperimenti](EXPERIMENT_LOG.md)
- [Odluke ADR-033–036](../specs/DECISION_RECORDS.md)
