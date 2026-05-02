---
slice_id: substrate/phase-2-skeptic-stage-surface
issue: 26
severity: S1
invariants-touched: [INV-008]
re-dispatch-of: .claude/completed-slices/substrate-phase-2-skeptic-stage-surface-failed
phase-1-source:
  - docs/plans/2026-05-02-substrate-papercut-bundle-design.md (Slice 2)
  - docs/plans/2026-05-02-substrate-papercut-bundle-plan.md (Slice 2 §)
in-tree-fix: ae9e6c8 (scripts/slice_orchestrator/lifecycle.py)
---

# substrate/phase-2-skeptic-stage-surface — intent (re-dispatch)

## What

Validate, by self-application under the now-fixed orchestrator, that
`commit_phase_handoff` in `scripts/slice_orchestrator/lifecycle.py` stages
every Phase-2 write under `tests/unit/` into the Phase-2 boundary commit when
`current_phase == 2`. Discovery is diff-based against the Phase-1 boundary
commit SHA, not slug-glob.

The behavioural change required by issue #26 is already on HEAD at `ae9e6c8`.
This re-dispatch's contribution is the regression test surface
(`tests/unit/test_phase_2_handoff_staging_surface.py`, four cases R1–R4) and
the demonstration that, under the fixed orchestrator, that test file is itself
naturally captured by the Phase-2 boundary commit on this very slice — the
bisect-anchor contract the prior dispatch attempt could not satisfy.

## Why

Phase-2-skeptic writes RED tests under `tests/unit/`. Pre-fix, those writes
leaked uncommitted past the Phase-2 boundary into Phase 3, breaking git-bisect
on any regression they would later cover. Issue #26 — S1. Phase-4's symmetric
leak was patched at `a8d8f23`; the Phase-2 hole was patched at `ae9e6c8`.

This slice re-runs against that fix to (1) lock in the regression surface so
future drift is caught, and (2) provide the bisect anchor: if the Phase-2
boundary commit on this slice contains the new test file, the fix
demonstrably works under self-application.

The prior dispatch (archived under
`.claude/completed-slices/substrate-phase-2-skeptic-stage-surface-failed/`)
failed because the orchestrator did not yet stage Phase-2's test writes — the
bug fixing itself could not commit the test that proves the bug was fixed.
That circularity is broken once the fix is in the tree before the re-run
begins, which it now is.

Slug-glob discovery remains rejected as naming-fragile; case R2 deliberately
exercises a non-slug-named file to enforce diff-based discovery.

## Boundary

In scope:

- The four-case regression surface
  `tests/unit/test_phase_2_handoff_staging_surface.py` (R1–R4 below).
- Verification that the existing `commit_phase_handoff` Phase-2 branch
  (added at `ae9e6c8`) satisfies all four cases.

Out of scope:

- Phase-3 staging path (handles its own writes via the existing mechanism).
- Phase-4 staging path (already fixed by `a8d8f23`).
- Any change to commit *count* or commit *subject* at the Phase-2 boundary.
- The Phase-1 boundary SHA discovery mechanism itself (read from existing
  orchestrator state, not redesigned here).
- Other paper-cut work tracked elsewhere; pre-existing reds queued for the
  post-INV-008 housekeeping pass.

If Phase 3 finds that the in-tree implementation at `ae9e6c8` is *not*
sufficient to make R1–R4 green, that signals the prior fix was incomplete and
Phase 3 inherits a narrow widening task on the existing Phase-2 branch only —
no second commit, no subject change, additive stage-list only.

## Specification

### Public-interface contract (lifecycle.py — already on HEAD at ae9e6c8)

`commit_phase_handoff(current_phase: int, ...)` — when `current_phase == 2`,
the externally observable Phase-2 boundary commit MUST contain:

1. The existing `handoff-phase-2.md` entry (unchanged from prior shape).
2. Every path under `tests/unit/` whose state diverges (added or modified)
   from the Phase-1 boundary commit and which still exists at staging time.

Idempotency: re-invocation against a tree with no Phase-2 `tests/unit/` diff
is a no-op (stage-list extension is empty; no extra paths, no extra commit).
The Phase-1 boundary SHA is read from existing orchestrator state — its
discovery mechanism is fixed and out of scope here.

The widening is *content* on the existing single Phase-2 boundary commit;
commit count and commit subject at the Phase-2 boundary are unchanged.

### INV-008 preservation

- **DC-3 (idempotent close).** Preserved. Stage-list extension is additive
  and existence-guarded; empty-diff invocations are no-ops.
- **DC-4 (no extra commits at phase boundary).** Preserved. Extension widens
  the *content* of the Phase-2 boundary commit; it does not introduce a
  second commit at the Phase-2 boundary. The redundant-commit guard
  semantics (slice-close-contract D2) are untouched.

### Discovery mechanism (rejected alternative)

Approach (b) — glob `tests/unit/test_<slice_id_slug>*.py` — is explicitly
rejected. Phase-2 RED tests do not always carry a slug-derived filename;
case R2 in the test surface deliberately includes a non-slug-named file to
enforce that the discovery mechanism does not depend on naming convention.

## Verification

### Test surface (Phase 2 RED) — `tests/unit/test_phase_2_handoff_staging_surface.py`

| Case | Setup                                                          | Expectation                                                          |
|------|----------------------------------------------------------------|----------------------------------------------------------------------|
| R1   | Phase-2 wrote 1 test file (slug-named)                         | Phase-2 boundary commit contains it                                  |
| R2   | Phase-2 wrote 3 test files (mixed slug-named + non-slug-named) | All 3 staged in Phase-2 boundary commit                              |
| R3   | Phase-2 wrote 0 test files                                     | Phase-2 boundary commit shape unchanged: only `handoff-phase-2.md`   |
| R4   | Phase-2 wrote 1 test file AND modified `handoff-phase-2.md`    | Both staged in the same Phase-2 boundary commit                      |

A reference skeleton is preserved at
`.claude/completed-slices/substrate-phase-2-skeptic-stage-surface-failed/test_phase_2_handoff_staging_surface.py.reference`
and the skeptic may consult or supersede it; the four-case contract above is
authoritative.

### Acceptance gates

- All four R1–R4 cases must pass under the in-tree orchestrator at `ae9e6c8`
  after the test file is materialised. (Pre-existing fix means these are
  expected to be green on first execution; if any are red, the prior fix is
  incomplete and Phase 3 widens the existing Phase-2 stage-list branch only.)
- Full `tests/unit/` pytest suite — no regressions; INV-008 hardened tests
  (`tests/unit/test_close_slice_hardened.py`,
  `tests/unit/test_cross_slice_isolation.py`,
  `tests/unit/test_agent_prompt_updates.py::test_phase_4_prompt_forbids_self_commit`)
  remain green.
- `git log --pretty=%s -n 5 | grep '^phase-2:'` — every phase-2 boundary
  commit on this branch henceforth includes at least one `tests/unit/...`
  path under `git show --name-only`.

### Bisect anchor (the central contract of this re-dispatch)

The Phase-2 boundary commit *on this slice itself* must contain
`tests/unit/test_phase_2_handoff_staging_surface.py`. The regression test
must be staged by the very fix it exercises — under self-application. This
is the contract whose failure caused the prior dispatch's archive; satisfying
it here is the empirical proof that `ae9e6c8` closed issue #26.
