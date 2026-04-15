---
slice: SLICE-013
phase: 1-intent
branch: dev
as-of: 2026-04-15 8ff6754
---

## State
Phase 1 intent committed. `intent.md` specifies three exact lint edits; envelope is `tests/unit/test_feature_cross_index.py` and `tests/unit/test_invariant_assertions.py`. `adrs-referenced: []` and `invariants-touched: []` — D3 gate trivially passes.

## Next
Enter Phase 2 — Skeptic enumerates ambiguities, writes `.claude/current-slice/validation/approach.md`. No new tests required (cleanup slice; no behavior change).

## Blocked / Pending
- E402 fix approach pre-resolved during planning — relocate import to top of file (not `# noqa`, not file split)
- Pre-existing tests in both files must pass unchanged after Phase 3 — Skeptic verifies this is the validation surface

## Pointers
- `.claude/current-slice/intent.md` — Phase 2 sole input; specification detail names the three edits
- `docs/operational-reference.md` § Phase Skill Guide → Phase 2 — load at Phase 2 entry for Skeptic role + skill mapping
- `.claude/sweep-results/2026-04-15-sweep.md` — context: which D3 bypass entry this slice clears
