---
slice: identifier-scheme/template-updates
phase: 2-validation→3-implementation
branch: feature/identifier-scheme
as-of: 2026-04-17 5c998e7
---

## State
Phase 2 RED suite committed at `5c998e7`. 20 tests at `tests/unit/test_identifier_scheme_templates.py` map to intent V1–V7 + V12. Envelope expanded via `EXPAND_ENVELOPE=1` to admit the Phase 2 test file; logged at `.claude/current-slice/envelope-expansions.log`.

## Next
Run `/catchup` then `/start-slice phase 3` in a fresh session to enter Implementation (Builder).

## Blocked / Pending
- Test-file envelope already expanded; no further test files permitted → `validation/approach.md` §Envelope expansion.
- Tests assert `.full.md` content only; lightweight `.md` updates are Builder judgment → `validation/approach.md` §A5.

## Pointers
- `.claude/current-slice/intent.md` — sole Phase 3 input alongside the test file.
- `tests/unit/test_identifier_scheme_templates.py` — RED suite to turn GREEN.
- `docs/adr/identifier-scheme.md` §D1/D2/D5/D8/D9 — normative scheme consulted when test wording is ambiguous.
