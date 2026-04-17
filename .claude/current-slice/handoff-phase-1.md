---
slice: identifier-scheme/adr-rename-sweep
phase: 1-intent
branch: feature/identifier-scheme
as-of: 2026-04-17 0a63f39
---

## State
`intent.md` committed at 0a63f39. Phase 2 gate met: intent in git; `adrs-referenced: [identifier-scheme]` exists at `docs/adr/identifier-scheme.md`.

## Next
Run `/start-slice phase 2` in a fresh session.

## Blocked / Pending
- Skeptic must enumerate which tests/unit/*.py files legitimately keep ADR-NNN assertions. Intent names `test_hook_tolerance.py` and `test_hook_relpath_bypass.py` as protected; others should migrate.
- CHANGELOG entry format — intent specifies content (header, rename table, consumer note, D7 link) but not CHANGELOG-section placement. Skeptic should reconcile with existing CHANGELOG conventions.
- Slug choice is mechanical per intent (filename tail unchanged). Skeptic should confirm no ADR-003 slug objection before Phase 3 commits the long slug `cliff-failure-mode-and-v1-defenses`.

## Pointers
- `.claude/current-slice/intent.md` — sole input for Phase 2 (+ `docs/adr/identifier-scheme.md` as the referenced ADR).
- `docs/operational-reference.md § Phase 2 Validation` and `§ Phase Skill Guide` — Skeptic role, anti-behaviors, and skill mapping.
