---
type: Implementation Plan
title: OKF 0.2 knowledge migration
status: stable
---
# OKF 0.2 Knowledge Implementation Plan

> For agentic workers: execute inline using the tests and checks below; review the
> full change before publishing. User authorized implementation in the existing PR.

**Goal:** make the repository a portable OKF 0.2 knowledge bundle for people and agents.
**Architecture:** root bundle, existing document paths retained except lowercase reserved
index naming, typed Markdown, progressive navigation, shared agent entry instructions.
**Tech Stack:** Markdown/YAML, Python >=3.11, PyYAML 6.0.3 only for knowledge tooling.
**Spec:** GoogleCloudPlatform/open-knowledge-format SPEC.md, commit
ad30107c31c06aec8a7d5636e0d1058118604e6f; user request recorded in ADR-010.

## Global constraints

- Dataset refinement TASK-012 remains first; no dataset choice or research claim is closed.
- Core simulation stays dependency-free; RL/legacy environments and artifacts are preserved.
- Raw/private/third-party environments are excluded from the published bundle; recovery
  references stay in repository manifests. No absolute workstation paths as prerequisites.
- No invented authorship, verification or external-source timestamps. Structural validation
  does not establish scientific truth or human review.
- Root index declares quoted okf_version 0.2; other indexes/logs follow reserved structure.

## Review focus

- Case-only index rename works on macOS and Linux; existing Markdown links are updated.
- Missing optional metadata/unknown fields and types remain acceptable OKF documents.
- Unsafe/malformed YAML, reserved index/log shape and explicit-offset timestamps are checked.
- Strict project checks catch broken local links and unreachable concepts; the base OKF
  check accepts broken links, as upstream requires. Fenced examples are not live links.
- A fresh clone supplies knowledge and entry points without this chat or ignored local files.

### Task 1: Repository knowledge checker

Files: scripts/validate_knowledge.py, tests/knowledge/test_validate_knowledge.py,
requirements/knowledge.txt, .github/workflows/tests.yml.
Interface: CLI --root PATH [--strict], exit 0 for success, 1 for validation issues.

- [x] Add CLI fixture tests for conformance, strict links/reachability, unsafe YAML and ignores.
- [x] Run tests RED, implement the small checker, run GREEN.
- [x] Add a separate CI knowledge job; leave core dependencies unchanged.

### Task 2: Bundle and navigation

Files: root index.md/log.md, existing tracked Markdown, lowercase directory indexes,
knowledge/okf-profile.json and knowledge authoring guide.
Interface: root index → group indexes → all public concepts/assets.

- [x] Add honest types/titles and curated source metadata; preserve bodies and decision history.
- [x] Add indexes/log, canonical source pin and writing/maintenance conventions.
- [x] Run base and strict checker; fix actual broken references.

### Task 3: People and agent onboarding

Files: AGENTS.md, README.md, HANDOFF.md, small agent compatibility entry files,
knowledge/project-context.md, knowledge/code-map.md, knowledge/maintenance.md.
Interface: shared AGENTS rules and root index; task-specific progressive reading routes.

- [x] Record current state, open decisions, code ownership/routing and reproducible commands.
- [x] Update handoff and next-session instructions; keep authoritative facts in existing docs.
- [x] Validate all routes and run application tests/smoke.

### Task 4: Verification and publication

- [x] Review the migration against the pinned spec, including privacy and known limitations.
- [x] Run clean-clone knowledge checks, unit tests and core smoke; record evidence.
- [x] Commit/push into existing PR #1 and update its description; no merge.
