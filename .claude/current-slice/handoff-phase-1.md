---
slice: SLICE-018
phase: 1-intent
branch: slice/housekeeping-stale-22k
as-of: 2026-04-16 5a85197
---

## State
SLICE-018 Phase 1 intent committed. Envelope: `docs/ARCHITECTURE.md`, `tests/unit/test_context_budget.py`. Invariants-touched: INV-004. adrs-referenced: [] (D3 trivial pass).

## Next
Open fresh session, run `/catchup`, then `/start-slice phase 2` to enter Validation (Skeptic).

## Blocked / Pending
- Coordinator approval required before advancing to Phase 2 (per worker briefing).

## Features
- housekeeping: SLICE-018 active at Phase 1 (stale-22k-cleanup); SLICE-017 complete.

## Pointers
- `.claude/current-slice/intent.md` — Phase 2 input; enumerate ambiguities from "Specification Detail" before writing tests.
- `.claude/current-slice/slice.yaml` — status advances intent → validation on Phase 2 entry.
- `tests/unit/test_context_budget.py` — read only public shape (existing test names, regression-guard lines 121/148/149) when designing Phase 2 tests.
- `docs/ARCHITECTURE.md` lines 41–47 — INV-004 block; line 46 description is the Change-1 target.
