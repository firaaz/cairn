---
slice: identifier-scheme/template-updates
phase: 2-validation→3-implementation
branch: feature/identifier-scheme
as-of: 2026-04-17 5c998e7
---

## State
Phase 2 RED suite committed at `5c998e7`. 20 tests at `tests/unit/test_identifier_scheme_templates.py` cover intent V1–V7 + V12. Envelope expanded via `EXPAND_ENVELOPE=1` to admit the Phase 2 test file.

## Next
Run `/catchup` then `/start-slice phase 3` in a fresh session to enter Implementation (Builder).

## Blocked / Pending
- `docs/plans/measurements/2026-04-12-slice-003.txt` uncommitted drift → obs §8.1 #8.
- Feature 1 migration remainder: adr-rename-sweep → slice-and-feature-rename → doc-sweep (serial) → design §7.
- Feature 2 ADR (phase automation) unblocks after Feature 1 drain → coord design §9.
- `/handoff` skill hardening (worker A P2/P3/P4 side-effect gap) → obs §6, §8.1.
- Test fix `test_log_has_exactly_four_lines` + ADR-007 graduation → sweep #14, obs §8.2.

## Features
- identifier-scheme: template-updates Phase 2→3; 3 rename sweeps remain before Feature 2 unblocks.
- housekeeping: complete (SLICE-017/018).
- v1-defense-d2: SLICE-010/011 queued.
- v1-defense-d3: SLICE-018 landed; substrate queued.

## Pointers
- `.claude/current-slice/handoff-phase-2.md` — Phase 3 Builder state + envelope-expansion note.
- `.claude/current-slice/intent.md` — sole Phase 3 input alongside the test file.
- `tests/unit/test_identifier_scheme_templates.py` — RED suite to turn GREEN.
- `docs/adr/identifier-scheme.md` §D1/D2/D5/D8/D9 — consult when test wording is ambiguous.
