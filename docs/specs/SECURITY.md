# Privatnost, licence i sigurno izvršavanje

Javni rezultat ne treba email adrese ili originalnu privatnu prepisku. Originali su
u ignorisanom `private/`. Objaviti samo sažetak zahtjeva i provenance hash.
Nema API ključeva ili korisničke autentikacije u pilotu. Ne zapisivati tokene/env dump.

Pretrained ZIP metadata je pregledana bez deserializacije. Pickle/cloudpickle i
PyTorch objekti mogu izvršiti kod pri učitavanju: pregled izvora i izolovani runtime
su preduvjet legacy model testiranja. Pinovati commit i hash, ne slijepo latest.
Očuvati licence i autorstvo; dataset i težine provjeriti posebno prije redistribucije.

Plaćeni resursi i operativne preporuke nisu obuhvaćeni. Pilot nije bezbjednosni sistem.
Open Questions: odabir projektne licence i dozvole za redistribuciju stvarnih mapa.
