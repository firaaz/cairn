---
slice: SLICE-017 housekeeping/inv004-rebaseline
phase: 1-intent
branch: feature/identifier-scheme
as-of: 2026-04-16 d65e50c
---

## State
`intent.md` committed at d65e50c. Envelope: `tests/unit/test_context_budget.py`, `docs/plans/measurements/2026-04-12-slice-003.txt`, `docs/ARCHITECTURE.md`, `uv.lock`. `adrs-referenced: []` — D3 gate passes trivially.

## Next
Fresh session → `/catchup phase 2` → `/start-slice phase 2`.

## Blocked / Pending
- `uv.lock` + measurement file uncommitted → carry-over, Phase 3 commits under new budget
- No ADR for this re-baseline → ARCHITECTURE.md "pending ADR" parenthetical preserved as-is

## Pointers
- `.claude/current-slice/intent.md` — Phase 2 sole input (modification slice; public interfaces of envelope readable)
- `docs/ARCHITECTURE.md § INV-004` — current "≤22,000" text; Phase 3 amends to "≤30,000"
- `tests/unit/test_context_budget.py` — BUDGET_HARD=22_000 / BUDGET_ASPIRATIONAL=20_000 current; targets 30_000 / 25_000
