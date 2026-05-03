---
slice_id: substrate/phase-2-skeptic-stage-surface
issue: 26
severity: S1
invariants-touched: [INV-008]
phase-1-source: docs/plans/2026-05-02-substrate-papercut-bundle-design.md (Slice 2), docs/plans/2026-05-02-substrate-papercut-bundle-plan.md (Slice 2 §)
---

# substrate/phase-2-skeptic-stage-surface — intent

## What

Extend `commit_phase_handoff` in `scripts/slice_orchestrator/lifecycle.py` so that
when `current_phase == 2`, the staging set additionally includes every path under
`tests/unit/` whose state diverges (added or modified) from the Phase-1 boundary
commit. Discovery is diff-based against the Phase-1 boundary SHA, not slug-glob.

## Why

Phase-2-skeptic writes RED tests under `tests/unit/`. The orchestrator's current
`commit_phase_handoff` does not stage those files when `current_phase == 2`, so
Phase-2's tests leak uncommitted into Phase 3 instead of being captured in the
phase-2 boundary commit. Issue #26 — S1. Phase-4's analogous leak was already
patched at `a8d8f23`; this slice closes the symmetric Phase-2 hole. Slug-glob
discovery (approach b) is rejected as naming-convention-fragile; diff-based
discovery (approach a) survives test-naming drift.

## Boundary

In scope: `commit_phase_handoff`'s Phase-2 branch only — additive stage-list widening
under `tests/unit/`, guarded by `path.exists()` so re-runs are no-op. Out of scope:
Phase-3 staging (handles its own writes); Phase-4 staging (`a8d8f23`); any change
to commit *count* or commit *subject*; the Phase-1 boundary discovery mechanism
itself (read from existing orchestrator state).

## Specification

### Public-interface change (lifecycle.py)

`commit_phase_handoff(current_phase: int, ...)` — when `current_phase == 2`:

1. Resolve the Phase-1 boundary commit SHA from existing orchestrator state.
2. Run `git diff --name-only <phase_1_boundary> -- tests/unit/` to enumerate paths
   added or modified under `tests/unit/` since Phase 1 closed.
3. For each enumerated path, if `path.exists()` (idempotency guard for re-runs and
   for paths deleted between Phase 2 RED and the staging call), add it to the
   stage list alongside the existing `handoff-phase-2.md` stage entry.
4. Continue to the existing single `git commit` for the Phase-2 boundary. The
   commit subject and the commit *count* are unchanged — this is content widening
   on the existing commit, not a new commit.

### INV-008 preservation

- **DC-3 (idempotent close).** Preserved. The widened stage list is additive and
  guarded by `path.exists()`; re-running `commit_phase_handoff` against a tree
  with no Phase-2 diff is a no-op (`git diff` returns empty, no extra paths
  staged, no extra commit).
- **DC-4 (no extra commits at phase boundary).** Preserved. Extension widens the
  *content* of the Phase-2 boundary commit; it does not introduce a second
  commit at the Phase-2 boundary. The orchestrator's redundant-commit guard
  semantics (slice-close-contract D2) are untouched.

### Discovery mechanism (rejected alternative)

Approach (b) — glob `tests/unit/test_<slice_id_slug>*.py` — is explicitly rejected.
Phase-2 RED tests do not always carry a slug-derived filename; the R2 case in the
test surface deliberately includes a non-slug-named file to enforce that the
discovery mechanism does not depend on naming convention.

## Verification

### Test surface (Phase 2 RED)

`tests/unit/test_phase_2_handoff_staging_surface.py` — four cases:

| Case | Setup | Expectation |
|------|-------|-------------|
| R1 | Phase-2 wrote 1 test file (slug-named) | Phase-2 commit contains it |
| R2 | Phase-2 wrote 3 test files (mixed slug-named + non-slug-named) | All 3 staged in Phase-2 commit |
| R3 | Phase-2 wrote 0 test files | Phase-2 commit shape unchanged: only `handoff-phase-2.md` |
| R4 | Phase-2 wrote 1 test file AND modified `handoff-phase-2.md` | Both staged in same Phase-2 commit |

### Acceptance gates

- All four R1–R4 cases RED before Phase 3, GREEN after.
- Full `tests/unit/` pytest suite — no regressions; INV-008 hardened tests
  (`tests/unit/test_close_slice_hardened.py`, `tests/unit/test_cross_slice_isolation.py`,
  `tests/unit/test_agent_prompt_updates.py::test_phase_4_prompt_forbids_self_commit`)
  remain green.
- `git log --pretty=%s -n 5 | grep '^phase-2:'` — every phase-2 commit on this
  branch henceforth includes at least one `tests/unit/...` path under
  `git show --name-only`.

### Bisect anchor

Phase-2 boundary commit on this slice itself must contain
`tests/unit/test_phase_2_handoff_staging_surface.py` — the regression test must
be staged by the very fix it exercises.
