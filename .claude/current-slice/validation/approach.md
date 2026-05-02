# Approach — substrate/phase-2-staging-untracked-enumeration

## Intent restatement
Extend `lifecycle.commit_phase_handoff` (`phase == 2` arm, lines 232-243)
to ALSO enumerate untracked test files via
`git ls-files --others --exclude-standard -- tests/unit/`, union with
the existing diff-based set, preserve the `path.exists()` guard.
INV-008 DC-3 (idempotent close) and DC-4 (single boundary commit)
preserved by construction — additive content widening of the existing
commit, no new commit emitted.

## RED tests (appended to `tests/unit/test_phase_2_handoff_staging_surface.py`)

- **R5 — untracked-only.** `diff_paths=[]`, `untracked_paths=[one new
  test]`, file seeded on disk. Asserts the untracked path appears in
  `_git("add", …)` calls and that `commit_calls <= 1`. RED today
  (orchestrator never calls `ls-files`).
- **R6 — union.** `diff_paths=[modified-tracked]`,
  `untracked_paths=[new file]`, both seeded. Asserts BOTH paths stage
  in the same boundary commit. RED today (only diff arm runs).
- **R7 — DC-3 guard.** `untracked_paths=[phantom]` NOT seeded on disk.
  Asserts the phantom path is NOT staged. Passes trivially today (no
  ls-files iteration at all); post-fix, this pins that the
  `path.exists()` guard MUST apply uniformly to the ls-files arm —
  guards against an unguarded Phase-3 implementation that crashes on
  a removed-between-discovery-and-staging path.

R1-R4 unchanged. The shared helper `_patched_so` gained an optional
`untracked_paths=None` parameter (default empty); fake `_git` answers
`head == "ls-files"` from it. Legacy callers omit the kwarg → R1-R4
behave identically.

## Ambiguities resolved

- **ls-files invocation form** not pinned by tests — fake matches on
  `head == "ls-files"`. Implementer is free to choose flag order.
- **SHA resolution** unchanged (already in tree); fake returns dummy
  SHA for `log` / `rev-parse`.
- **Order of staged paths** not asserted — tests check membership.

## Coupling cluster

Single cluster: `scripts/slice_orchestrator/lifecycle.py` and
`tests/unit/test_phase_2_handoff_staging_surface.py`. The
neighbour-test `test_commit_phase_handoff_stage_surface.py` is
included as a regression-watch surface (Phase-3 must not regress its
existing greens while widening the same function).
