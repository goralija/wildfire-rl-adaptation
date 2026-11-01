---
type: Research Design
title: Prvobitni pivot — historijski požari i vatrogasne linije
description: Laičko i tehničko objašnjenje prelaska s CFSDS/Cell2Fire na BurnMD/SimFire kao bolje usklađenog eksperimenta.
status: current-provisional
sources:
  - resource: /docs/specs/DECISION_RECORDS.md
  - resource: /docs/research/SOURCES.md
---
# Prvobitni pivot na BurnMD i SimFire (historijski zapis)

> Ova stranica čuva prvobitni prijedlog od 2026-11-01. Mineral podaci su naknadno
> pregledani i line-time polja su prazna; **ADR-040 je promijenio trenutni dizajn** tako
> da glavni policy ogled ne čeka historijski-action replay. Aktuelni put je
> [scenario pipeline](REAL_IGNITION_SCENARIO_PIPELINE.md) i [DESIGN](../DESIGN.md).

**Ovo je bio prijedlog prije Mineral audit-a.** BurnMD je izabrani kandidat za glavni
skup stvarnih slučajeva; SimFire + SimHarness su izabrani kandidati za simulator i RL
okruženje. Standalone SimFire sada radi u lokalnom Python 3.9.25 environmentu. Još nisu
potvrđeni prava na BurnMD podatke, njihov sadržaj ni spajanje stvarnog događaja; SimHarness
trening runtime nije pokrenut. Zato prvo radimo izvodljivostni prolaz, a ne trening.

## Ukratko, bez stručnih izraza

Ranije smo pokušavali iz satelitske karte napraviti požar koji Cell2Fire pokrene bez
gašenja, pa tražili da model skoro isto izgori kao stvarni požar. Ali za naše izabrane
slučajeve nismo znali kad su vatrogasci djelovali, a historijska karta goriva i mala mapa
donijele su dodatne probleme. Nismo mogli razdvojiti grešku simulatora od razlike između
stvarnog i zamišljenog gašenja.

Sad biramo podatke koji sadrže **i kretanje stvarnog požara i nacrtane vatrogasne linije**.
SimFire omogućava da agent bude vatrogasac na mapi: kreće se i postavlja liniju. Zatim
uporedimo osnovnog agenta, istog agenta nakon dodatnog učenja na drugim historijskim
slučajevima i nekoliko jednostavnih pravila. Svi dobijaju isti požar, vrijeme i isti budžet.

Analogija: ranije smo pokušavali ponoviti utakmicu bez zapisnika da li je iko igrao odbranu.
Sad tražimo utakmice gdje imamo i tok igre i zabilježene odbrambene poteze. Simulator je
i dalje maketa utakmice; rezultat nam govori šta strategije rade **u toj maketi**, a ne
koliko bi hektara sigurno bilo spašeno u stvarnom požaru.

## Šta nam daje novi izvor

BurnMD opisuje 308 srednjih požara u zapadnom SAD-u iz 2018–2021. Rad navodi dnevne
granice požara, operativne procjene i podatke o vatrogasnim mjerama, uključujući linije.
Autori su neke datume provjeravali satelitskim MODIS/VIIRS opažanjima. To je bliže našem
zadатку od CFSDS-a jer uključuje tragove gašenja, a ne samo kartu gdje je vatra bila.

BurnMD nije savršen dnevnik vatrogasaca. Neki zapisi mogu imati neprecizno vrijeme;
linijski sloj sadrži i neizvedene ili planirane linije koje moramo odvojiti od stvarno
izgrađenih. Dataset ne daje pouzdan broj ljudi i mašina za svaku liniju, a njegov rad
koristi pretpostavke o veličini ekipe i brzini gradnje da procijeni vrijeme. BurnMD rad
također navodi da vremenske prilike nisu dio tadašnje baze. Zato ćemo vrijeme pribaviti
zasebno, a ne pretvarati nepotpuna polja u sigurnu činjenicu.

Javni MITRE repozitorij sadrži arhivu `BurnMD.zip` od 345 MB kroz Git LFS. Repou je
priložena Apache-2.0 licenca, ali nismo našli jasnu, zasebnu licencu za sadržaj ZIP-a.
**Nećemo pretpostaviti da licenca programskog koda automatski pokriva dataset.** Prvi
zadatak provjerava uslove korištenja i sadržaj; sirovi arhiv ostaje izvan Git-a.

## Zašto baš SimFire/SimHarness

SimFire koristi model širenja vatre zasnovan na Rothermelu, čita stvarne američke slojeve
goriva i terena iz LANDFIRE-a, i prikazuje širenje i postavljene linije. SimHarness je RL
okvir napravljen za taj simulator. Njegov agent može da se **pomjera i izabere vrstu
intervencije** — liniju, mokru liniju ili brzu privremenu liniju. To daje smislenije
značenje „budžeta“ od ranijeg brisanja jedne ćelije jednim potezom.

Objavljeni primjer SimFire-a koristio je stvarni LANDFIRE teren i gorivo iz 2019. u
okolini Mineral Firea 2020. Taj požar je i BurnMD primjer. Zato je **Mineral Fire 2020
predložen kao prvi tehnički probni slučaj**, ne kao konačni testni događaj. Rad SimFire-a
opisuje RL demonstraciju, ali ostavlja detaljniju provjeru širenja kao budući rad. Dakle,
zamjena simulatora sama po sebi ne rješava fizičku pouzdanost.

Postoji i ozbiljan praktični rizik: objavljeni SimFire traži Python 3.9, dok glavni projektni
venv koristi Python 3.12. SimFire i SimHarness bi se zato morali instalirati u zasebno
izolovano okruženje. Njihove objavljene verzije i dokumentacija nisu dokaz da će raditi na
našem računaru bez popravki.

## Novo istraživačko pitanje

**Da li dodatno učenje na scenarijima izvedenim iz stvarnih požara poboljšava planiranje
vatrogasnih linija u SimFire-u u odnosu na isti, zamrznuti početni agent i jednostavna
pravila, kada svi imaju isti budžet i iste informacije?**

- **Osnovni agent:** PPO agent prethodno naučen na raznovrsnim SimFire mapama.
- **Prilagođeni agent:** kopija tog agenta dodatno naučena samo na TRAIN požarima iz
  BurnMD-a.
- **Poređenje:** zamrznuti osnovni agent, prilagođeni agent, ne-akcija i jedna ili dvije
  jasne linijske heuristike.
- **Budžet:** isprva broj/dužina dozvoljenih poteza za pravljenje linije, ne izmišljeni broj
  vatrogasaca ili litara vode. Tek kad izvor pouzdano daje vrijeme ekipe, budžet se može
  pretvoriti u procijenjene radne sate.
- **Test:** požari odvojeni po cijelom incidentu, tako da nijedan dan istog požara ne završi
  i u treningu i u testu. Testni događaji se ne koriste za biranje postavki.

Firehose checkpointi ne mogu se direktno prenijeti. Njihov agent bira jednu ćeliju u
20×20 mapi; SimHarness agent se kreće i bira vrstu linije. To su različite igre i različiti
izlazi. Zadržavamo ranije Firehose rezultate kao dokaz da prethodni runtime radi, ali novi
osnovni checkpoint treniramo u SimFire arhitekturi.

## Kako će izgledati poštena provjera

1. Iz BurnMD-a uzmemo jedan incident s dovoljno jasnim početkom požara, vremenom i stvarno
   izgrađenim linijama. Mineral Fire 2020 je prvi kandidat.
2. Napravimo mapu stvarnog goriva i terena, uz provjerenu vremensku verziju. Dodamo
   vremensku seriju iz zasebnog, zapisanog izvora.
3. Simulatoru i agentu damo samo podatke koji bi bili dostupni do vremena odluke. Kasniji
   obod i kasnije linije ostaju u fascikli za provjeru, ne ulaze u opažanje agenta.
4. Prvo pustimo u simulator historijski zabilježene linije na njihovim vremenima.
   Uporedimo nekoliko vremenskih presjeka simulatora s opaženim obodima. Ovo je novi
   **historical-action replay gate**: ne tražimo „požar bez gašenja“ kad su ga ljudi gasili.
5. Ako ovaj test pokaže da se ulazi i historijske akcije mogu ispravno prikazati, tek onda
   pravimo alternativne poteze agenta i poređenja po budžetu.
6. Svaki rezultat izvještava koliko je **simulirana** opožarena površina i kako izgleda
   oblik požara. Historijski konačni obod je referenca za vizuelni kontekst, ne odgovor na
   pitanje šta bi se desilo pod drugim potezima.

Ako dataset ne može dati pouzdane datume izgradnje, filter za izgrađene linije ili dozvolu
za korištenje, ne treniramo na njemu. Tada ćemo zadržati samo ono što se može pouzdano
potkrijepiti i suziti tvrdnju; nećemo nadomjestiti nepoznato izmišljenim podacima.

## Kako ćemo pokazati rezultate

Za svaki odabrani događaj čuvamo georeferenciranu kartu s gorivom/terenom, početnim
požarom, historijskim obodima i linijama. Zatim pravimo animaciju za tri pogleda: historijski
zapis, simulator s historijskim linijama i isti simulator s potezima svake politike.
Uz animaciju ide tabela po vremenu: veličina požara, potrošeni budžet, dužina linija i da li
je simulator prekinuo zbog zaustavljenog požara ili isteka trajanja. U svakoj slici piše
rezolucija i da je riječ o modelu.

To daje uvjerljiviju demonstraciju od jedne brojke, a istovremeno pokazuje gdje se model
razlikuje od stvarnog slučaja.

## Šta raniji CFSDS rad znači nakon promjene

CFSDS istraživanje nije izbrisano i nije bilo uzalud. Naučili smo kako provjeravati
porijeklo podataka, izbjegavati da target procuri u ulaze, ponavljati scenarije i praviti
mape. Ti alati i izvještaji ostaju u repozitoriju kao **arhivirana prethodna putanja**.

Zaustavljamo samo pretpostavku da moramo riješiti CFSDS 2014b gorivo, 2018 suppression
crosswalk i 2 km Cell2Fire izrez prije nego što možemo postaviti RL pitanje. Njihovi stari
nalazi ostaju tačni za stare ulaze, ali više ne određuju glavni projekat.

## Sljedeći provjerljivi koraci

1. Preuzeti ili pribaviti BurnMD lokalno u Git-ignorisan prostor; zabilježiti hash, sadržaj,
   manifest i licencu.
2. Provjeriti može li se jedan incident, prvo Mineral Fire, povezati s dnevnim obodima,
   stvarno izgrađenim linijama, vremenom i koordinatama bez upotrebe kasnijih informacija.
3. U izolovanom Python 3.9 okruženju instalirati tačno pinovane SimFire/SimHarness verzije.
4. Pokrenuti jednu no-agent SimFire epizodu i napraviti prvu kartu/animaciju.
5. Uvesti historijske linije i provjeriti jedan vremenski replay. Ako ovo padne, zabilježiti
   tačan razlog i procijeniti minimalni adapter prije RL rada.

Prvobitni prijedlog je čekao ova četiri tehnička prolaza. Poslije Mineral audit-a,
historijski line replay je prebačen u opcioni track. U svakom dizajnu nema tvrdnje o
stvarno spašenom prostoru.

## Izvori

- BurnMD dataset/paper i problemi u vremenskim podacima: [SOURCES S-017, S-053](SOURCES.md).
- SimFire, njegov kod i verzija Python-a: [SOURCES S-054](SOURCES.md).
- SimHarness i njegova akcijska semantika: [SOURCES S-055](SOURCES.md).
- Objavljeni SimFire primjer kod Mineral Firea i ograničenje validacije: [SOURCES S-056](SOURCES.md).
- Formalna odluka: [ADR-037](../specs/DECISION_RECORDS.md#adr-037--pivot-to-burnmd-simfire-and-historical-action-replay-2026-11-01).
