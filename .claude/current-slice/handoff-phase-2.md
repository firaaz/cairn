---
slice: identifier-scheme/doc-sweep
phase: 2-validation
branch: feature/identifier-scheme
as-of: 2026-04-18 2661e0b
---

## State
Phase 2 validation committed at 2661e0b. Tests: 2 RED (verification items 1-2) + 1 GREEN canary committed; approach.md documents classification, PRESERVE allowlist (6 sites), ARCHITECTURE.md regen path, `operational-reference.md:257` stale-tense known-issue, Phase 4 Auditor checklist.

## Next
In Phase 3 (Builder): execute the sweep — per-occurrence id migration using `ADR_EDITORIAL_FIX=1` for ADR body edits, `/refresh-architecture` for `ARCHITECTURE.md`, option 2 (migrate + tense fix) for `operational-reference.md:257` per approach.md.

## Blocked / Pending
- 6 PRESERVE sites must remain unchanged → `test_preserve_allowlist_entries_still_present` canary
- `operational-reference.md:257` stale-tense — Builder records choice in `implementation/notes.md`
- `ARCHITECTURE.md` via `/refresh-architecture`; if generator emits legacy ids, escalate

## Pointers
- `.claude/current-slice/intent.md` — spec source
- `.claude/current-slice/validation/approach.md` — classification, decisions, Phase 4 checklist
- `tests/unit/test_identifier_scheme_sweep.py` — RED contract to satisfy
