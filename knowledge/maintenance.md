---
type: Playbook
title: Održavanje baze znanja i handoffa
description: Kako sačuvati odluke, dokaze, otvorene teme i navigaciju za narednu osobu ili agenta.
status: stable
generated: {by: "process:codex", at: "2026-10-28T12:55:34Z"}
sources:
  - resource: /AGENTS.md
  - resource: /docs/specs/DECISION_RECORDS.md
---
# Pravila održavanja

## Čitanje na početku rada

Ulaz je [index.md](../index.md). Pročitaj [projektni kontekst](project-context.md),
[STATUS](../docs/STATUS.md), [NEXT_SESSION](../docs/NEXT_SESSION.md), najnoviji ADR
i dokumente relevantne za zadatak prema [mapi](code-map.md). Čitaj progresivno;
kanonski dokumenti i izvori su bitniji od prisjećanja na chat.

## Agent ulazi

| Mehanizam | Repo fajl | Zajednički nastavak |
| --- | --- | --- |
| AGENTS-kompatibilni alati, uključujući Cursor | [AGENTS.md](../AGENTS.md) | Root index, kratki kontekst, status i zadatak |
| Claude Code | [CLAUDE.md](../CLAUDE.md) | Isti AGENTS i kontekst |
| Gemini CLI | [GEMINI.md](../GEMINI.md) | Isti AGENTS i kontekst |
| GitHub Copilot | [repo instrukcije](../.github/copilot-instructions.md) | Isti AGENTS i kontekst |

Ovo su ulazni mehanizmi opisani u [Cursor](https://cursor.com/docs/rules),
[Claude](https://support.claude.com/en/articles/14553240-give-claude-context-claude-md-and-better-prompts),
[Gemini](https://geminicli.com/docs/cli/gemini-md/) i
[Copilot](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions)
dokumentaciji. Prepoznavanje zavisi od alata i uključenih repo instrukcija; agent
nakon učitavanja ulaza treba otvoriti navedene dokumente. Ne održavati zasebne kopije
cijelog konteksta u svakom ulaznom fajlu.

## Gdje upisati promjenu

| Promjena | Kanonsko mjesto |
| --- | --- |
| Novo trenutno stanje ili blokada | [STATUS](../docs/STATUS.md) |
| Redoslijed i prihvat narednog zadatka | [BACKLOG](../docs/BACKLOG.md), [NEXT_SESSION](../docs/NEXT_SESSION.md), [HANDOFF](../HANDOFF.md) |
| Nova ili izmijenjena odluka | novi ADR u [append-only logu](../docs/specs/DECISION_RECORDS.md); navesti šta zamjenjuje |
| Hipoteza, metrika ili promjena metode | [PROTOCOL](../docs/research/PROTOCOL.md) i pogođeni spec; označiti prijedlog/draft |
| Dataset izvor, obrada ili split | [DATASET](../docs/research/DATASET.md), [REAL_FIRE_DATASETS](../docs/research/REAL_FIRE_DATASETS.md), [manifesti](../data/index.md) |
| Izvršen eksperiment ili provjera | [EXPERIMENT_LOG](../docs/research/EXPERIMENT_LOG.md), mali report/manifest s kod/config/input/model identitetima |
| Šta je sesija uradila | [WORK_LOG](../docs/WORK_LOG.md), pa sažet novi najviši unos u [log.md](../log.md) |
| Novi koncept/putanja | najbliži lowercase index.md; provjeriti dostupnost iz root indeksa |

## Razlikuj činjenice i preporuke

- Preuzimanje, parser, smoke, fizička validacija i naučni rezultat su različite stvari.
  Navedi tačno šta je provjereno, komandom/dokazom i na kojoj platformi.
- Status koncepta `stable` znači da je dokument spreman za čitanje; ne znači da je
  hipoteza dokazana ili da su dataset/prijedlog prihvaćeni. Čitaj sadržaj i ADR.
- Ne dodavati `verified` zato što je tekst migriran ili linter prošao. Takav check
  potvrđuje strukturu/linkove, ne sadržaj. Čovjek se ne navodi kao verifier bez stvarnog pregleda.
- Korisnikove najnovije upute imaju prednost. Staru odluku sačuvaj i dodaj novu;
  ažuriraj aktivne sažetke da se istraženi kandidat ne pretvori u navodni dogovor.
- Ne unositi lične putanje kao operativni preduslov. Privatni originali ostaju
  ignorisani; javni sažetak/manifest čuva ono što treba za nastavak.

## Prije commita i predaje

```sh
python3 -m venv /tmp/wildfire-knowledge-venv
/tmp/wildfire-knowledge-venv/bin/python -m pip install -r requirements/knowledge.txt
/tmp/wildfire-knowledge-venv/bin/python -m unittest discover -s tests/knowledge -v
/tmp/wildfire-knowledge-venv/bin/python scripts/validate_knowledge.py --strict
PYTHONPATH=src python3 -m unittest discover -s tests -v
git diff --check
```

Koristi postojeći prikladan venv ako ga imaš; zadana /tmp putanja je primjer izolacije,
ne dio baze znanja. Za izmijenjeni runtime pokreni odgovarajući smoke/runbook i
zapiši ishode. CI pokreće osnovne testove i zaseban knowledge job. Nove uzorke/model
ne objavljuj samo zato što su javno dostupni; provjeri porijeklo i licencu.
