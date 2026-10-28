---
type: Research Protocol
title: Istraživački protokol — draft v1, 2026-10-28
status: draft
sources:
- resource: /docs/research/REQUIREMENTS_AND_RUBRIC.md
- resource: /docs/specs/DECISION_RECORDS.md
---
# Istraživački protokol — draft v1, 2026-10-28

## Pitanje i hipoteze

RQ-001: Može li prilagodba unaprijed treniranog MaskablePPO agenta različitim
budžetima smanjiti kumulativnu opožarenu površinu u odnosu na zamrznuti početni
model i heuristike pri istim scenarijima, budžetima i informacijama?
RQ-002: Kako se mijenja kompromis ukupne štete i zaštite prioritetnih područja?
H1: prilagođeni agent smanjuje štetu kroz više budžeta. H2: prioritetna adaptacija
smanjuje prioritetne gubitke, uz moguće povećanje ukupne štete. Obje mogu biti odbačene.

## Šta mijenjamo

Minimalni glavni eksperiment: isti checkpoint, arhitektura, opažanje i akcije;
fine-tuning zasebno na B={2,4,8,16}, uz zajednički budžetski/no-op adapter.
To izoluje promjenu parametara politike od promjene arhitekture.
Dodatni, ambiciozniji eksperiment: zajednička politika uslovljena početnim i
preostalim budžetom, trenirana preko više B. To mijenja opažanje i možda izlaz;
zahtijeva pravilo prenosa težina i matched kontrolu bez tih featurea.
Ne učitati 400-action checkpoint u 401-action env i tvrditi da je neizmijenjen.

Zamrznuti agent nakon B intervencija izvršava no-op do kraja, kao i svi ostali.
Ako nema learned no-op izlaz, budžetski adapter ga prisilno šalje nakon B;
takva evaluacija mjeri kvalitet izbora prvih B akcija, a ne naučeno čuvanje budžeta.
Za učenje vremena intervencija treba dodatni no-op izlaz sa jasno opisanim
proširenjem glave i kontrolama. Ovo je otvorena odluka nakon feasibility gatea.

## Kontrole

- Bez akcije B=0: donja granica intervencijskog napora; isti požar do kraja.
- Random-valid, min-L2 i max-L2 prema zapaljenim ćelijama i udaljenosti od ignitiona.
- Jednostavna priority heuristika sa istim informacijama kao priority agent.
- Zamrznuti pretrained agent pod istim B i wrapperom.
- Fine-tuned agent, ista inicijalizacija i jednak broj simulator koraka po B.
- Ako resursi dozvole: from-scratch agent sa istim dodatnim training troškom,
  i joint-budget politika. Jasno razlikovati ukupni od dodatnog compute troška.

## Podaci i split

Početak: jedna 20×20 mapa, fiksni pa random ignition; ista meteorologija i tempo akcija.
Odvojiti trening/validaciju/test po **scenario ID-u** (mapa, ignition, weather trace,
simulator seed), a ne samo po broju Python seeda. Zamrznuti test manifest prije tuninga.
`configs/splits.json` je prijedlog, ne gotov glavni dataset split.
Provjeriti da sve ćelije imaju konzistentnu projekciju/rezoluciju i da su priority
maske poravnate, NODATA isključen iz imenilaca, ignition na gorivu.

Pilot koristi jednu sintetičku mapu, 12 seedova i 300 baseline epizoda.
Njegovi seedovi nisu dokaz generalizacije; glavni eksperimenti trebaju novi odvojeni
manifest. Testovi sintetičkog enginea ne validiraju Cell2Fire ili SimFire.

## Metrike

Primarno: `burned_fraction = |ever_burned| / |initial_burnable|`, manje je bolje.
Ako je ćelija već gorjela, kasniji tretman ne briše štetu.
`priority_burned_fraction = |ever_burned ∩ priority| / |priority ∩ initial_burnable|`.
Uz praznu priority zonu pilot vraća 0; glavni izvještaj takvu metriku označi N/A.
`interventions`: stvarno potrošene ćelije, uvijek <=B. Prijaviti i trajanje, runtime,
invalid actions i udio epizoda koje dosegnu horizont uz aktivan požar.
`area_saved`: uparena razlika no-action minus policy, u procentnim poenima.
Učinkovitost po intervenciji sekundarna; ne dijeliti nulom i ne nagrađivati samo neaktivnost.

Primarno poređenje adaptacije treba biti fine-tuned minus **frozen**, uz zasebne
heurističke usporedbe. Sadašnji pilot summary podržava no-action reference;
prije glavnih rezultata proširiti reference i višestruke training seedove (TASK-006).

## Poštena statistika

Za svaki policy/B isti skup scenario ID-eva, nezavisan RNG politike i simulatora.
Sadašnji engine koristi random brojeve po (seed,time,edge), što omogućava uparivanje
bez pomjeranja RNG toka nakon različitih akcija. Ne pretpostavljati da drugi simulator
ima isto svojstvo samo zato što je seed isti.
Plan glavnog minimuma: 3 nezavisna training seeda × 30 test scenarija × 4 B po modelu;
5 training seedova ako runtime dopušta. Jedna mapa ograničava zaključak na tu mapu.
Ne tretirati 90 rollouta istog checkpointa kao 90 nezavisnih treninga.
Prijaviti uparene razlike, 95% intervale, median/IQM gdje je korisno i pojedinačne runove.
Za glavni RL koristiti hijerarhijski bootstrap (training seed, pa scenario), ne sadašnji
jednonivojski pilot bootstrap. 2,000 resampliranja je pilot implementacija.
Izabrati primarni test i B prije konačnog izvođenja; sekundarna poređenja označiti
kao eksplorativna. Ne birati najbolji seed ili video kao dokaz prosječnog uspjeha.

## Compute i stop pravila

Prvo mjeriti 10 rollouta i 1,024 training koraka; procijeniti runtime prije 100k+.
Predloženi početni fine-tuning cap je 50k koraka po training seedu/B; to je pretpostavka
za planiranje, ne obaveza. Ne pokretati tu matricu dok simulator gate i procjena ne prođu.
Pilot RL smoke je maksimalno 1,024 koraka na CPU-u. Nema plaćenog cloud pokretanja.
Nulti rezultat ili nepouzdan simulator znače smanjiti obim i dokumentovati nalaz.

## Grafikoni i zaključak

1. Ukupna šteta prema B sa intervalima i svim kontrolama.
2. Prioritetni gubici prema B i Pareto ukupna/prioritetna šteta.
3. Krive učenja prema simulator koracima i vremenu, ne samo epizodama.
4. Isti unaprijed izabrani scenarij kao mapa stanja kroz vrijeme za sve politike.
5. Tabela efekata i limita. Bez prenošenja idealizovanih rezultata na realnu intervenciju.

## Dopuna iz runtime provjere — 2026-10-28
Firehose je izvršen. Originalni grid=1 kombinuje burning i burnt; postojeći min/max-L2
stoga bira iz pogođenog footprinta, a ne nužno aktivne fronte. Prije glavnih rezultata
jasno označiti legacy baseline ili dodati stvarni active-state export. Svim politikama
primijeniti isti ispravljeni warmup observation/damage adapter. Originalni FireSizeReward
penalizuje footprint kroz vrijeme; prelazak na incremental damage reward bio bi dodatna
promjena uz budget adaptaciju i zahtijeva zasebnu kontrolu/ablation. Done na weather
horizontu nije containment. Dataset split i priority maska još nisu gotovi.
