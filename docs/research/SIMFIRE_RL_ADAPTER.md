---
type: Environment Record
title: Gymnasium adapter za stvarnu SimFire kohortu
status: current
sources:
  - resource: /src/wildfire_rl/simfire_gym_env.py
  - resource: /src/wildfire_rl/simfire_policy.py
  - resource: /reports/real-fire-data/simfire-cohort-v2-gym-smoke/receipt.json
---
# Kako agent razgovara sa SimFire-om

## Jednostavno objašnjenje

Za svaki požar simulator učita stvarnu mapu goriva, stvarnu visinsku mapu i početnu ćeliju.
U proxy modu učita i weather parametre izvedene iz dnevnog gridMET konteksta. Agent dobije
mape, trenutno stanje vatre i atmosferu; bira **no-op** (čekaj) ili jednu ćeliju na koju
odmah postavlja SimFire fireline tačku. SimFire odradi narednih 30 minuta i vrati stanje.
Agent dobije negativnu nagradu za nove simulirane izgorjele ćelije.

Ovo je prva radna, pojednostavljena veza između podataka i agenta. Jedna akcija je jedna
tačka od 30 m, ne kompletna linija. Za sada nema hodanja ekipe, vremena gradnje, dostupnosti
posade ni budžeta u radnim satima. Ta pojednostavljenja moramo jasno navesti i kasnije
odlučiti da li ih treba proširiti.

## Šta vidi, šta radi i kako se boduje

- **Ulaz mape:** 22 kanala kategorija FBFM13/ostali kodovi, jedan visinski kanal sa fiksnim
  rasponom 0–5.000 m i jedan kanal stanja vatre. Sve mape su 128×128.
- **Dodatno stanje:** preostali budžet, protekli dio epizode, brzina/smjer vjetra, vlaga i
  oznaka izvora uslova. `demonstration_only` koristi fiksne demo vrijednosti; `gridmet_daily_proxy`
  koristi po-slučaju proxy iz manifestiranog dnevnog gridMET zapisa.
- **Akcije:** `0` je uvijek no-op; ostale akcije predstavljaju jednu neizgorjelu i gorivu
  ćeliju za postavljanje fireline tačke.
- **Budžet:** početna konfiguracija je 32 tačke. Svaka tačka troši jednu. Kada se budžet
  potroši, epizoda se ne prekida — agent i dalje može birati no-op.
- **Vrijeme:** jedna odluka pokreće 30 simuliranih minuta; početni horizont je 24 odluke,
  odnosno najviše 12 sati. SimFire može završiti ranije ako više nema aktivne vatre.
- **Trajanje aktivne ćelije:** 15 SimFire update-a, po jednu simuliranu minutu svaki.
  Stock postavka je 4 update-a; za našu 30 m mrežu to je gasilo neke sporije fronte prije
  nego što bi Rothermel proračun prebacio susjednu ćeliju. Vrijednost 15 je eksplicitna
  inženjerska postavka, još bez nezavisne fizičke kalibracije.
- **Nagrada:** negativan broj novih izgorjelih ćelija podijeljen ukupnim brojem gorivih
  ćelija u mapi. Broji se i ranije izgorjela ćelija; historijska veličina požara se nigdje
  ne koristi kao cilj.
- **Podjela:** environment učitava samo train, validation ili test incidente; reset može
  izabrati tačan scenario ID za uparene poredbene pokrete.

MaskablePPO koristi mali konvolucijski ekstraktor za mapu i ograničenu glavu izlaza za
16.385 mogućih akcija. To izbjegava ravnanje cijele 128×128 mape u ogroman model.

## Vremenski ulaz: stvarni dnevni podatak → SimFire proxy

Izvorni gridMET JSON ostaje netaknut. Mapping skripta pravi zaseban verzionisani JSON koji
čuva vrijednosti, formule, izvorni hash i pretpostavke. Verzija 1 za nominalnu atmosferu:

1. gridMET 10 m brzina (m/s) se pretvori u mph; pošto nemamo visinski profil/canopy,
   koristi se kao približan SimFire 20 ft referentni vjetar.
2. Brzina se pomnoži WAF faktorom 0.3 (djelimično zaklonjen scenario). 0.1 i 0.5 su
   deklarisane niže/više varijante, ne lokalno izmjerene kategorije zaklona.
3. Meteorološki `wind_from` se okrene za 180° u SimFireov smjer `toward`.
4. Simard EMC procjena koristi dnevnu maksimalnu temperaturu i minimalnu RH, pa se postotak
   pretvori u SimFire fraction. To je suha procjena ravnoteže, ne izmjereno stanje sitnog
   goriva. Ekstremi mogu biti u različito vrijeme, a prethodna kiša i sušenje nisu modelirani.
5. Jedan dnevni proxy se drži stalnim kroz epizodu do 12 h. To nije replay tačnog sata paljenja.
   gridMET dan je ponoć–ponoć MST, dok FPA-FOD discovery HHMM ovdje nema vremensku zonu.

NFDRS model-G FM100 ostaje dodatni kontekst; ne predstavljamo 100-satno gorivo kao fine
fuel-moisture ulaz. Originalni dnevni zapisi, proxy fajlovi i receipti su odvojeni kako bi se
mogle porediti pretpostavke bez prepisivanja izvora.

## Runtime i provjera

SimFire ostaje na Pythonu 3.9.25. Lokalno su instalirani kompatibilni paketi:
PyTorch 2.3.1, Gymnasium 1.1.1, Stable-Baselines3 2.7.1 i sb3-contrib 2.7.1. Ovo je lokalni
macOS ARM64 snapshot, ne univerzalni setup. Tačne verzije su u
[`simfire-rl-macos-arm64-py39.freeze.txt`](../../requirements/simfire-rl-macos-arm64-py39.freeze.txt).

```sh
.local/simfire-venv/bin/python scripts/smoke_simfire_gym_env.py
.local/simfire-venv/bin/python scripts/smoke_simfire_gym_env.py --weather-mode gridmet_daily_proxy
```

Smoke je pokrenuo po jedan scenario iz svakog splita, postavio jednu linijsku tačku,
provjerio no-op nakon potrošenog budžeta i inicijalizirao MaskablePPO koji je izabrao legalnu
akciju. Pri WAF 0.1, 0.3 i 0.5 je potvrđeno da je override stigao do simulatora i receipta;
to nije validacija vremenske fizike. **Nije pozvan `learn()`; model nije treniran.** Demo
receipt je u [`simfire-cohort-v2-gym-smoke`](../../reports/real-fire-data/simfire-cohort-v2-gym-smoke/),
a proxy receipt u [`simfire-cohort-v2-gridmet-weather-smoke`](../../reports/real-fire-data/simfire-cohort-v2-gridmet-weather-smoke/).

Zaseban no-op probe koristi samo akciju čekanja kroz najviše 24 odluke, bez vatrogasne
linije i bez agenta. Sa WAF 0.3 i trajanjem ćelije 15 min, sačuvani rezultati su Owyhee
675 min/8.792 ćelije, Hayden 720 min/1.059 ćelija i Larch Creek 84 min/24 ćelije. Ovo
pokazuje različito ponašanje okruženja na tri slučaja; nije dokaz da su te površine tačne
za stvarne događaje. Kod, JSON receipti i karte su u
[`simfire-cohort-v2-gridmet-noop-horizon`](../../reports/real-fire-data/simfire-cohort-v2-gridmet-noop-horizon/)
i [`smoke-otvorenom test slučaju`](../../reports/real-fire-data/simfire-cohort-v2-gridmet-noop-test-exposed/).

## Šta još treba prije vjerodostojnog poređenja

Tehnički environment smoke-radi s realnim fuel/terrain ulazima i dnevnim proxyjima za svih
80 scenarija; svaki split se može odvojeno učitati, a proxy checksum provjerava se pri
učitavanju. Ovo znači da je put podataka izvršiv i ponovljiv, ne da SimFire tačno reprodukuje
stvarne požare.

Prije poređenja politika treba zaključati tri kontrole (no-op, deterministička heuristika,
base PPO), jednake scenario IDs, vremenske uslove, budžet/horizont i evaluacijske seedove,
metriku, način izbora checkpointa te pravilo da se test split otvori tek na kraju. Trenutni
adapter još nema evaluacijski ugovor ni potvrđene naučene težine. Trening se namjerno ne
pokreće u fazi pripreme.

Tehničke provjere su otvorile test incident Larch Creek (`fpa-fod-401411292-larch-creek`);
izostaviti ga iz završnog benchmarka. Sačuvati preostalih 19 test požara za završnu uparenu
evaluaciju i taj izuzetak zapisati u zaključani manifest.
