---
slice: m5-plugin-distribution
phase: adr-and-plans-landed
branch: dev
as-of: 2026-05-08 1f2d88e
---

## State
M5 plugin distribution + symlink retire ADR landed via `/decision` (Phases 0/0.5/1/2/3/5; firm; INV-011 added). Per-feature plan trio committed (F1 packaging, F2 consumer-doc, F3 migration) via parallel async subagents under `TeamCreate` scaffolding. dev is 12 commits ahead of `origin/dev`. Validator + suite green.

## Next
1. Dispatch F1 (`cairn-m5-f1-packaging`) via `cairn-tdd-feature` — unblocker. F2 + F3 carry F1-followup placeholders.
2. F2, then F3 once F1 deliverables (manifests + `role_guard.py:28,121` fix + validator) land on disk.
3. Push `dev` → `origin/dev` (12 commits ahead).

## Blocked / Pending
- F1-blocked: F2 marketplace-URL + validator-output placeholders; F3 manifest preflight.
- F2-blocked: F3 runbook home (CONSUMER.md vs new `docs/upgrading-from-symlink.md`).
- 6 amendment ADRs (cost-per-slice-budget, parallelism-v1, phase-pipeline-evaluation, feature-slice-model, context-tiers-integration, identifier-scheme).
- M5.1: slash-command shipping, multi-consumer rollout, doc-link validator.
- INV-004 re-baseline once CC system-prompt overhead stabilises.

## Pointers
- `docs/adr/m5-plugin-distribution-and-symlink-retire.md` (9 D-commitments + INV-011)
- `docs/plans/2026-05-08-cairn-m{5,6}-f{1,2,3}-*.md` (the trio)
- `.claude/skill-runs/m5-plugin-decision/` + `m5-feature-plans/brief.md`
- `.claude/active-envelope.yaml` (operator mode; widen per-feature as you dispatch)
- `.claude/skill-runs/cairn-m5-f1-packaging/` (F1 audit closed — sweep-notes.md OK)
