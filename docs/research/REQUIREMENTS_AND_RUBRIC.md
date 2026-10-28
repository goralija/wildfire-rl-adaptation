---
type: Requirements
title: Zahtjevi i kriteriji profesora
---
# Zahtjevi i kriteriji profesora

Izvori: privatna prepiska od 2026-10-21 i slika rubrike koju je korisnik dostavio
2026-10-28. Ispod je sažetak, bez email adresa i sirove privatne prepiske.
Originali se čuvaju lokalno u ignorisanom `private/`; hash vrijednosti su u manifestu.

## Potvrđeno
- Odabrana tema su intervencije pri šumskim požarima pomoću RL-a.
- Profesor traži preciznu definiciju intervencije i onoga što se mijenja prilagodbom.
- Samo manji budžet mogao bi dati preuzak ili trivijalan doprinos.
- Predloženo pitanje: prilagodba prethodno treniranog agenta različitim budžetima,
  poređenje s početnim agentom i heuristikama, posebno prioritetna područja.
- Jasno istraživačko pitanje i odgovarajuće metrike su ključni.
- Tim je u inicijalnoj prijavi naveo Colab i prednost fine-tuningu; dostupnost računa,
  GPU-a, vremena i kredita nije potvrđena.
- Korisnik dopušta drugačiji simulator i bilo kakav smislen raspored repozitorija.

## Prepis bodovanja sa slike

| Kriterij | Udio | Planirani dokaz |
| --- | ---: | --- |
| Definicija problema: jasnoća, relevantnost, izvori i literatura | 10% | pitanje, formalizacija, SOURCES i bibliografija |
| Kreativnost: originalnost problema i pristupa rješavanju | 20% | budžetska adaptacija, ablation, kompromis zaštite |
| Arhitektura i optimizacija modela: izbor rješenja, optimizacija i metrike | 20% | zamrznuti model vs fine-tuning vs baseline, ista evaluacija |
| Kvalitet podataka: priprema, čišćenje, označavanje i izvori | 10% | data card, hash, provjera rastera i splitova |
| Čist kod i dokumentacija: modularnost, čitljivost i GitHub dokumentacija | 15% | paket, testovi, runbook, manifest i odluke |
| Grafikoni i vizualizacije: jasnoća, relevantnost i interpretabilnost | 10% | krive šteta/budžet, intervali, prioritetni gubici i scenariji |
| Kvalitet postera: profesionalnost, jasnoća i informativnost | 5% | sažet poster sa metodom, nalazima i ograničenjima |
| Zaključci i budući koraci: interpretacija rezultata, metrike i dalji razvoj | 10% | test zaključaka, negativni nalazi, ograničenja i dalji rad |
| **Ukupno** | **100%** | slika navodi ukupno 60 bodova |

Slika zasebno navodi pojedinačni usmeni 0–100%. Nije jasno kako se taj postotak
kombinuje s ukupnim bodovima; formula se ne pretpostavlja. Rok i format postera nisu dati.

## Radne pretpostavke
A-001: počinjemo mapom 20×20 zbog provjere troška, zatim više mapa ako resursi dopuštaju.
A-002: jedna intervencija je idealizirani trajni tretman ćelije uz jedinični trošak.
A-003: budžeti 0, 2, 4, 8, 16 su početni pilot, ne profesorov zahtjev.
A-004: prioritetna područja su sintetički označene zone, ne stvarna naselja.
