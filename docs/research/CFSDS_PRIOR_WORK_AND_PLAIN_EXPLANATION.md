---
type: Research Review
title: Kako su raniji radovi pripremali i provjeravali stvarne požare
description: Poređenje CFSDS, W.I.S.E., Cell2Fire/Dogrib i Firehose radova s našim pipelineom, uz laičko objašnjenje preostalih prepreka.
status: reviewed
sources:
  - resource: /docs/research/SOURCES.md
  - resource: /docs/research/CFSDS_TRAIN_INPUT_QC.md
  - resource: /docs/research/CFSDS_NO_ACTION_DIAGNOSIS.md
  - resource: /docs/research/REAL_CASE_PIPELINE.md
  - resource: /docs/STATUS.md
---
# Kako su raniji radovi pripremali i provjeravali stvarne požare

Pregled javnih radova i izvornog Cell2Fire/Firehose projekta, 2026-10-31.
Ovo je pregled ranijeg rada, ne novi rezultat našeg simulatora.

## Kratak odgovor

Pretvoriti podatke u ulaz simulatora **možemo**: već smo napravili tri historijska
FireCase paketa i pokrenuli ih kroz Cell2Fire bez akcija gašenja. Problem nije što niko
ne zna napraviti takvu konverziju. Problem je dokazati da dobijeni ulaz predstavlja
poštenu, dovoljno vjerodostojnu osnovu za tvrdnju da je jedan agent smanjio štetu.

Literatura je riješila različite dijelove ovog zadatka, ali pregledani izvori ne pokazuju
jedan rad koji istovremeno koristi baš naš CFSDS slučaj, baš naš Firehose checkpoint,
istorijski no-action replay i pošteno poređenje fine-tuninga protiv originalnog agenta.
Najbliži prethodnici se mogu složiti kao kockice:

1. **CFSDS** pretvara satelitske detekcije u procijenjene dnevne požarne karte.
2. **W.I.S.E.** koristi isti CFSDS tip dnevnih karata za provjeru širenja kroz kanadski
   FBP model.
3. **Cell2Fire/Dogrib** pokazuje kako se jedan detaljnije dokumentovan stvarni požar
   može pripremiti za Cell2Fire.
4. **Firehose** pokazuje kako trenirati i porediti RL agente preko Cell2Fire simulatora,
   ali na simulator scenarijima, a ne direktno na CFSDS dnevnim ishodima.

Dakle, put postoji. Moramo paziti da ne spojimo rezultate tih različitih zadataka kao
da su jedan već validiran recept.

## Šta se u podacima nalazi, običnim riječima

CFSDS koristi satelitske "vruće tačke" koje ukazuju gdje je satelit registrovao aktivan
požar, pa statistički procjenjuje kojeg je dana požar stigao do pojedinih dijelova
završnog oboda. Autori koriste MODIS i VIIRS detekcije te kriging/interpolaciju. Zato
oznaka u ćeliji znači otprilike **"prema dostupnim satelitskim opažanjima, požar je
ovdje stigao ovog dana"**, a ne **"satelit je tačno vidio da se ova ćelija zapalila u
14:37"**. U originalnom radu autori izričito kažu da je prava terenska potvrda rijetka;
raspoloživi službeni obodi takođe imaju vlastita ograničenja. [CFSDS rad](https://doi.org/10.1038/s41597-024-03436-4)

Laička analogija: zamisli da preko šume nekoliko puta dnevno preleti kamera i ostavi
rijetke pribadače na mjestima gdje vidi toplotu. CFSDS pomoću tih pribadača nacrta
razumnu dnevnu mapu. Mapa može imati ćelije od 90 ili 180 metara, ali to **ne znači** da
je satelit direktno i precizno izmjerio svaku takvu ćeliju; sitniji kvadrati su procjena
iz rjeđih opažanja. Takođe ne znamo tačan redoslijed kojim su se ćelije palile unutar
istog dana.

## Šta su drugi uradili

| Rad | Šta su napravili | Šta je korisno za nas | Šta njihov rezultat ne dokazuje |
| --- | --- | --- | --- |
| Barber i dr., CFSDS (2024) | Od MODIS/VIIRS detekcija i konačnih oboda izveli procijenjene dnevne karte i prateće okolišne podatke. | Daje nam stvarne historijske događaje, dnevni target i način da poredimo karte. | Ne daje tačan satni front, stvarne poteze vatrogasaca ni sve ulaze koje simulator traži. |
| Bennett i dr., W.I.S.E. (2026) | Pokrenuli kanadski FBP-bazirani W.I.S.E. nad 19.848 dana širenja iz 2.210 požara u CFSDS 1.1. | Ovo je najbliži direktni primjer pripreme dnevnih CFSDS karata za model širenja. | W.I.S.E. nije naš Firehose/Cell2Fire RL eksperiment niti ispituje koristi od odluka agenta. |
| Kim i dr., Dogrib/Cell2Fire (2025) | Složili su stvarni Dogrib teren, 100 m FBP mapu, DEM, vrijeme stanice i poznatu lokaciju paljenja; poređali simulaciju s opečenom površinom. | Pokazuje konkretnu pretvorbu jednog stvarnog slučaja u Cell2Fire. | Poboljšanje nakon podešavanja na istoj opečenoj površini nije nezavisni dokaz da će se model prenijeti na druge požare. |
| Shen i Curtis, Firehose (2022) | Trenirali RL agente u Cell2Fire okruženjima 20×20, 40×40 i prilagođenim simulacijama te ih poredili s jednostavnim pravilima. | Pokazuje da se Firehose RL petlja može trenirati i evaluirati protiv baseline politika. | Njihov agent nije time automatski naučio iz CFSDS-a niti je rezultat validacija na stvarnom historijskom obodu. |

### 1. CFSDS: od satelitskih tačaka do dnevne karte

Originalni CFSDS rad opisuje kako su detekcije toplote od MODIS-a i VIIRS-a filtrirane
prema požarnim obodima, pa vremenski interpolirane metodom kriging. Svakom pikselu je
pridružen procijenjeni dan dolaska požara. Autori zatim porede dnevne obode s pažljivo
odabranim službenim obodima. U dostupnim poređenjima CFSDS ima prosječni Sørensen–Dice
rezultat 0,73 ± 0,31, naspram 0,47 ± 0,32 za FIRED, ali autori upozoravaju da ima malo
nezavisnih "ground truth" podataka i da službene karte nisu savršene. To je dobar dokaz
da je CFSDS koristan i bolje vremenski razrađen izvor za modeliranje, ne dokaz da je
svaka pojedinačna ćelija savršeno označena. [CFSDS rad i tehnička provjera](https://doi.org/10.1038/s41597-024-03436-4)

### 2. W.I.S.E.: najbliži primjer — i vrlo poučna zamka

W.I.S.E. koristi CFSDS 1.1 i kanadski FBP. Autori su za dan `n` pripremili gorivo,
teren, vrijeme, prethodno izgorjelo područje i obod za provjeru. Ranije spaljene ćelije
maskiraju kao negorivo; visinu, nagib i ekspoziciju računaju iz MRDEM terena; koriste
ERA5-Land kao približni vremenski izvor i porede simulirane i opažene površine. Dnevne
rastere su prebacili u zajednički sistem i rezoluciju 90 m. To potvrđuje da se CFSDS
može povezati s fizičkim modelom širenja. Važno za našu kohortu: autori su izbacili
požare za koje je CNFDB bilježio **bilo kakvo gašenje**, jer njihov model ne računa
intervenciju. Zato ni mi ne možemo istorijski požar sa `suppression_status=unknown`
predstavljati kao požar bez gašenja. [W.I.S.E. metoda](https://doi.org/10.1071/WF26072)

Ali CFSDS ne govori koji je tačno piksel gorio prvi unutar dana. W.I.S.E. zato početni
front bira tako što uzima piksele od jučerašnjeg oboda koji dodiruju **sutrašnju**
opečenu površinu. Autori priznaju da to koristi buduću informaciju. Za njihovu dnevnu
procjenu može se čitati kao idealizovan način da se početna aktivna linija približi
stvarno opaženom širenju; za našu strogu test-proceduru to bi bilo kao da učeniku, prije
nego što riješi zadatak, damo dio sutrašnjeg odgovora da mu označimo gdje počinje.

Isto važi za njihove dijagnostičke scenarije. Osnovni scenario daje prosječni F1 0,259.
Scenario 2 bira trajanje koje se najbolje poklopi s poznatom CFSDS ciljnom kartom za svaki
pojedinačni dan, pa F1 naraste na 0,498. Scenario 3 koristi ciljnu kartu i za odabir
vjetra, pa F1 naraste na 0,539. Autori ih opisuju kao idealizovane granice/sensitivity
analize i upozoravaju da su nerealno dobre za operativnu upotrebu jer koriste buduću
informaciju. Uz to, 25,7% osnovnih simulacija doseglo je ivicu ulazne mreže, gdje se
širenje vještački zaustavilo. [W.I.S.E. rezultati i ograničenja](https://doi.org/10.1071/WF26072)

Ovo direktno odgovara na tvoju nedoumicu: **drugi su sastavili i pokrenuli slične
podatke; mi ne izmišljamo konverziju.** Oni su istovremeno pokazali i da dobijanje
uvjerljivog i poštenog rezultata traži odvojene provjere, a "bolji F1 nakon gledanja
targeta" nije isto što i unaprijed bolji agent.

W.I.S.E. je dodatno izbacio slučajeve gdje CNFDB bilježi gašenje. Naša tri sačuvana
2018 kandidata nemaju potpunu evidenciju koja dokazuje da se na požaru nije djelovalo;
za dva incident-crosswalk kandidata postoje parcijalni javni izvještaji o radu/resursima,
a treći ima samo statusne izvještaje. Zato se ti paketi mogu koristiti za dijagnostiku
ulaza, ali ne prolaze strogi “neugašeni požar” uslov za čist no-action replay.

### 3. Dogrib: stvarni slučaj direktno u Cell2Fire

Rad iz 2025. koristi otvoreni Dogrib požar iz 2001. u Alberti. Za Cell2Fire su pripremili
kanadsku FBP fuel mapu rezolucije 100 m, visinu/nagib/ekspoziciju, vremensku seriju
stanice Yaha Tinda i poznatu koordinatu paljenja. Simulirali su osam sati i poređali
rezultat sa stvarnim ožiljkom požara. U radu navode da je osam sati odabrano tako da
simulacija pokrije oko 90% ukupno opožarene površine, a teren je postavljen na veoma
suhi D1L1 scenario. Njihova optimizacija faktora širenja prema istom ožiljku povećala je
F1 sa 0,74 na 0,83 za taj slučaj. Kod i primjer ulaza su javni.
[Dogrib/Cell2Fire rad i podaci](https://doi.org/10.1038/s41598-025-05706-6)

Analogija: kao da napraviš maketu mjesta, podesiš model tako da liči na fotografiju
požara i potvrdiš da program ume da je izvrši. Ako biraš podešavanja gledajući baš tu
fotografiju, dokazao si da umeš prilagoditi maketu tom primjeru. Još nisi dokazao da će
isto podešavanje predvidjeti drugi požar. To je razlog što se podešava na TRAIN, a
nezavisna provjera ostavlja za događaje koje nije koristio pri podešavanju.

### 4. Firehose: RL agent preko simulacija

Firehose radi drugi dio problema. Agent dobija stanje mreže, bira ćeliju u koju troši
akciju/intervenciju, a Cell2Fire simulira šta se poslije događa. Autori testiraju
20×20/40×40 primjere iz Cell2Fire i vlastito okruženje; u radu navode 5 miliona koraka
treninga. Naučeni agent može nadmašiti jednostavna pravila kada je mjesto paljenja
poznato, ali se muči kada je mjesto paljenja nasumično. To je dokaz da RL i simulator mogu
zajedno raditi, ali nije dokaz da je njihov trening koristio CFSDS kao stvarni dnevni
target. [Firehose rad](https://williamshen-nz.github.io/firehose/firehose-paper.pdf)

Zato RL ne uči samo iz stare karte požara kao što učenik uči iz zbirke riješenih
zadataka. Agent mora probati akciju, a simulator mora izračunati njenu posljedicu.
Historijski zapis obično sadrži samo **jedan** ishod požara — onaj koji se zaista dogodio,
uz moguće vatrogasne akcije. Ne sadrži paralelne verzije istog požara: "šta bi bilo da
agent nije uradio ništa", "šta ako je stavio liniju ovdje" i "šta ako ju je stavio
ondje". Te nepostojeće verzije stvara simulator.

## Kako se naš izvor Y prevodi u simulator X

| Izvorni podatak Y | Šta simulator X očekuje | Prevod koji treba uraditi | Pouzdano ograničenje |
| --- | --- | --- | --- |
| CFSDS raster dana dolaska/gorenja | Mreža ćelija i početno stanje | Reprojekcija/izrez u izabranu mrežu; `arrival_day < n` postaje raniji požarni trag; target dan `n` čuvamo zasebno | CFSDS ne daje tačan sat ni redoslijed paljenja u danu |
| FBP karta goriva | FBP kod za svaku simulator ćeliju | Prostorno poravnanje i dokumentovano pravilo za raniji ožiljak | Mapa mora odgovarati vremenu požara ili se jasno označiti kao aproksimacija |
| DEM visina | Visina, nagib i ekspozicija za svaku ćeliju | Zajednički koordinatni sistem i veličina ćelije, pa izračun nagiba/ekspozicije | Moramo sačuvati tačnu verziju i izvor ćelija |
| Satno vrijeme / reanalysis | Redovi vremena koje model čita | Vrijeme, smjer/brzina vjetra, vlaga, padavine i FWI vrijednosti u ispravnim jedinicama | Reanalysis je rekonstrukcija, ne lokalno mjerenje u plamenu |
| Dan `n-1` i target dan `n` | Početni scar/front i nezavisan target za poređenje | Početni front birati samo iz informacija dostupnih do dana `n-1`; masku dana `n` ne proslijediti builderu | Odabir fronta gledajući target je "odgovor unaprijed" |
| Akcije vatrogasaca, ako postoje | Istorijska intervencija / kontekst | Koristiti samo dokazive akcije i njihove vrijeme/prostor; inače označiti kao unknown | Bez loga intervencija ne znamo da li upoređujemo prirodni rast ili rast pod gašenjem |

Laička slika: **Y je dnevnik i mapa s nekoliko vremenskih fotografija; X je komandna
igraonica simulatora.** Moramo iz dnevnika napraviti teren, vrijeme, zapaljeni početak i
pravila igre. Slike nam pomažu provjeriti simulaciju poslije toga, ali ne smijemo ih
ubaciti kao tajni trag koji agent vidi unaprijed.

## Zašto su naša trenutna tri pokušaja izgledala loše

U tri ranije sačuvana TRAIN slučaja već smo napravili X-pakete i pokrenuli simulator.
No-action simulacije su dodale približno 66, 237 i 73 ha, naspram CFSDS dnevnih ciljeva
oko 15,39, 12,15 i 12,15 ha. Svaka je dotakla rub 20×20 prozora za 34–52 minute, a jedan
slučaj je ispunio svih 400 ćelija. Ove su stare probe koristile target-aware builder i
služe samo za dijagnostiku; ne predstavljaju čistu validaciju novog ulaza. Detalji su u
[TRAIN no-action dijagnozi](CFSDS_NO_ACTION_DIAGNOSIS.md) i
[input QC-u](CFSDS_TRAIN_INPUT_QC.md).

Analogija za rub: simuliramo šumu na poslužavniku 2×2 km. Vatra stigne do ivice poslužavnika,
pa dalje nema kvadrata za rast. Rezultat unutar poslužavnika je mjerljiv, ali ne možemo
tvrditi koliko bi požar narastao van njega. Širi poslužavnik daje više prostora, ali ako
svaki kvadratić postane drugačije veličine ili udvostručimo mrežu, mijenjamo i ono što
agent vidi i koju fizičku površinu njegova akcija pokriva.

Poznati su nam i otvoreni razlozi zašto istorijski target nije jednostavan "tačan odgovor":

- mapa daje dan, ne satni redoslijed;
- satelitske ćelije su interpolacija iz rjeđih opažanja;
- za postojeće TRAIN slučajeve nije potvrđena dnevna evidencija gašenja;
- historijska FBP mapa nema potvrđen datum do kojeg uključuje ožiljke;
- vremena/teren za tri legacy paketa nemaju savršeno pinovanu historijsku provenijenciju;
- domen 2×2 km je premalen za brzi rast u tim primjerima.

To nisu izgovori da ne radimo; to su kontrolne tačke da rezultat poslije možemo braniti.

## Šta smijemo tvrditi u različitim fazama

1. **Simulator tehnički radi:** program prihvata pripremljeni scenario i završava run.
   Ovo već imamo za runtime i tri no-action historijska paketa.
2. **Ulaz je sastavljen bez gledanja targeta:** svi početni ulazi su određeni iz
   informacija dostupnih do unaprijed određenog starta, a target se koristi tek za
   završno poređenje. Imamo prototipski dokaz za jedan slučaj, ne kompletan novi cohort.
3. **No-action model približno reprodukuje historijski dnevni rast:** isto pravilo,
   unaprijed fiksan vremenski prozor i prihvatljiva greška na train slučajevima. Ovo još
   nismo postigli; postojeći pilot promašuje rast i udara u rub.
4. **Agent smanjuje štetu unutar simulacije:** porediti ga s osnovnim agentom/no-opom i
   heuristikama na potpuno istim scenarijima, seedovima, vremenskom horizontu i budžetu.
   Ovo još nije testirano za CFSDS.
5. **Agent bi smanjio stvarnu historijsku štetu:** to je najjača tvrdnja i ne slijedi
   automatski iz koraka 4. Trebaju nam vjerodostojan model, transparentna neizvjesnost i
   intervencijski podaci ili vrlo pažljivo ograničen counterfactual zaključak.

## Konkretan sljedeći redoslijed

1. Zaključati pravilo koje pravi početni scar/front samo iz pre-target podataka i držati
   target raster tehnički odvojen od simulator inputa.
2. Izabrati reprezentativne TRAIN slučajeve koji imaju dovoljan prostor, dozvoljene i
   dokazive fuel klase, ponovljive weather/terrain ulaze i dokumentovano ograničenje oko
   suppression evidencije. Ne mijenjati slučaj zato što se model na njemu loše poklopio.
3. Odlučiti i unaprijed zapisati fizičku skalu mreže, trajanje i seedove. Ako se mijenja
   od 20×20/100 m, postojeći Firehose checkpoint više nije automatski isti agent u istoj
   igri.
4. Prvo ponoviti **no-action replay** i tražiti stabilno, prihvatljivo slaganje prije
   akcija. Ako model sistematski previše širi, treniranje agenta neće popraviti fiziku.
5. Tek nakon no-action gatea odvojiti TRAIN za trening, VALIDATION za odluke/podešavanje,
   a TEST čuvati netaknut. Fiksirati osnovni checkpoint, heuristike, budžet, horizont,
   seedove i metrike.
6. Trenirati/fine-tuneati samo na TRAIN simulator epizodama; izvještavati zasebno o
   poboljšanju simuliranog ponašanja i o slaganju modela sa opaženim obodom.
7. Napraviti karte koje odvojeno prikazuju satelitski target, no-action rezultat i agentov
   rezultat, uz označene neizvjesnosti i skalu ćelije.

## Zaključak za laika

Ne pokušavamo napraviti nemoguću pretvorbu. Već smo dokazali da se format može složiti i
da simulator može izvršiti slučaj. Pravo pitanje je: **da li igraonica dovoljno liči na
stvarnu šumu i da li je test namješten bez gledanja odgovora?** Literatura kaže: CFSDS se
koristi za ovakve mape; W.I.S.E. je pokazao i način i zamku; Dogrib potvrđuje da Cell2Fire
može raditi s realnim inputima; Firehose potvrđuje RL petlju. Niko od tih pojedinačnih
rezultata ne zamjenjuje naš no-action gate i poštenu usporedbu base/fine-tuned agenta.

**Trenutna statusna riječ ostaje `research_ready=false`.** Tehničko okruženje postoji;
validan, dovoljno poravnat i nepristrasan real-fire eksperiment još nije spreman.
