---
slice: sweep-debt-cleanup
date: 2026-04-13
phase: 1-intent
invariants-touched: []
adrs-referenced: [ADR-007]
envelope:
  - "docs/plans/measurements/2026-04-12-slice-003.txt"
  - "docs/operational-reference.md"
  - "tests/unit/test_sweep_debt_cleanup.py"
out-of-scope:
  - "INV-006/INV-007 implementation (feature-slice model — separate implementation slices per ADR-006/ADR-008)"
  - "SLICE-002 P0b resolve/supersede (requires /decision)"
  - "INV-001 scar-class commit discipline (D2 machine-check scope)"
---

### What and Why

Integration sweep #3 (2026-04-13) identified two concrete debt items carried forward from sweep #2. Both are small documentation drift repairs that do not change invariants or require ADR supersession. Clearing them eliminates a test failure and aligns the Phase Skill Guide with ADR-007 D3's committed decisions.

### Specification Detail

**Item 1 — Stale measurement artifact.** `docs/plans/measurements/2026-04-12-slice-003.txt` has uncommitted working-tree changes (token count 20074→19950, aspirational MISS→PASS) from a hook recalculation. The uncommitted diff causes `test_v7_envelope_compliance` to fail because `git diff --name-only HEAD` picks up the modified file outside SLICE-005's allowed patterns. Fix: commit the corrected measurement values.

**Item 2 — `using-git-worktrees` exclusion drift.** ADR-007 D3 (2026-04-12) un-excluded `using-git-worktrees` and returned it as a conditional Phase 3 supporting skill. `dispatching-parallel-agents` was correctly moved to Phase 3 supporting skills in `operational-reference.md:95`, but `using-git-worktrees` remains in the exclusions section at line 104 with stale wording ("v1 single-slice work does not need them"). Fix: move `using-git-worktrees` from the exclusions list to Phase 3 supporting skills, with conditional wording per ADR-007 D3 ("when subagent-driven tasks require workspace isolation, or for cross-slice parallel work").

### Boundary

- No invariant text changes. The Phase Skill Guide skill mapping is a living registry (operational-reference.md:76) and updates are ordinary documentation edits.
- No ADR creation or supersession.
- No changes to hooks, validators, or pipeline mechanics.
- The `test_v7_envelope_compliance` test itself is not modified — its failure is resolved by committing the stale working-tree artifact.

### Verification

1. `python3 -m pytest tests/ -x` passes with 0 failures (currently 1 failure in test_v7_envelope_compliance).
2. `using-git-worktrees` appears in the Phase 3 supporting skills column of `operational-reference.md` Phase-to-skill mapping table.
3. `using-git-worktrees` does NOT appear in the "Explicit exclusions" section of `operational-reference.md`.
4. `git diff --name-only HEAD` returns empty after all changes are committed.
5. `python3 scripts/validate_architecture.py` passes.
