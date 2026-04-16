---
slice: SLICE-017 housekeeping/inv004-rebaseline
phase: 2-validation
branch: feature/identifier-scheme
as-of: 2026-04-16 973d351
---

## State
Phase 2 gate met. `tests/unit/test_context_budget.py` holds `test_inv004_turn1_token_budget` (existing; RED at 28511 > 22000) and `test_inv004_architecture_rebaselined` (new; RED on missing `≤30,000` ceiling and `SLICE-017` / `2.1.110` citations).

## Next
Phase 3: bump `BUDGET_HARD=30_000`, `BUDGET_ASPIRATIONAL=25_000`, update the file docstring (`22k`→`30k`), amend the INV-004 paragraph in `docs/ARCHITECTURE.md` (append provenance), re-run `test_inv004_turn1_token_budget` to regenerate `docs/plans/measurements/2026-04-12-slice-003.txt`, commit `uv.lock` as-is.

## Blocked / Pending
- (none — envelope fully declared in `intent.md`; carry-overs pre-staged in working tree)

## Pointers
- `.claude/current-slice/intent.md` — Phase 3 sole input alongside the test files
- `tests/unit/test_context_budget.py` — validation suite Phase 3 must make GREEN
- (Auditor-only) INV-004 invariant-check description retains `22k token budget` literal per intent-as-stated scope — intentional, not a Phase 3 target and not a Phase 4 regression
