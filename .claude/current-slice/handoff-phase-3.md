---
slice: SLICE-018 (identifier-scheme/hook-relpath-bypass)
phase: 4-integration
branch: slice/identifier-scheme-hook-relpath
as-of: 2026-04-16 3131096
---

## State
Phase 3 implementation committed. `checks/reversibility-guard.sh` derives `PROJECT_ROOT` and a canonical `${FILE#$PROJECT_ROOT/}` then `${...#.slice-system/}` form before ADR pattern matching; `-f` probe uses `$PROJECT_ROOT/$CANONICAL`. Slice suite green; V9 (`test_hook_tolerance.py`) green unmodified.

## Next
Run `/start-slice phase 4` to verify INV-005, run full suite + `scripts/validate_architecture.py`, and audit for adjacent regressions.

## Blocked / Pending
- Phase 4 input: implementation + intent.md + ARCHITECTURE.md + INV-005 only. MUST NOT load `validation/approach.md` or `implementation/notes.md` reasoning unless auditing a specific decision.
- Two envelope-compliance tests (`test_sweep_debt_cleanup::test_v4`, `test_slice_005_design_decomposition::test_v7`) pass at clean tree post-commit; verified via stash.
- V9 (`tests/unit/test_hook_tolerance.py` 25/25) must stay green unmodified.
- Sweep cadence: `.claude/sweep.yaml` interval 1, last 17, current 18 → integration sweep #13 follows slice close.

## Pointers
- `.claude/current-slice/intent.md` — Phase 4 spec source; V1–V12 verification table
- `checks/reversibility-guard.sh` — envelope; canonical-form normalization at top, ADR cases on `$CANONICAL`
- `tests/unit/test_hook_relpath_bypass.py` — Phase 4 must run green
- `.claude/current-slice/implementation/notes.md` — read only if auditing a specific D1–D6 decision
