# Sweep notes — substrate/phase-2-skeptic-stage-surface

## Outcome: RAISE_ISSUE

Functional fix is correct (4/4 R1–R4 cases GREEN; lifecycle.py:commit_phase_handoff diff-based discovery works). However, the slice's own self-application failed: the regression test file `tests/unit/test_phase_2_handoff_staging_surface.py` is **untracked** in the working tree and was never committed by either Phase 2 or Phase 3. The bisect anchor in intent.md ("Phase-2 boundary commit on this slice itself must contain the test file") is unsatisfied for chicken-and-egg reasons — the fix lands in Phase 3, but Phase 2 ran with the unfixed orchestrator. Phase-3 builder also did not recover by staging the test in its own commit, leaving the file untracked at slice close.

## Invariants

| Invariant | Statement | Status | Evidence |
|-----------|-----------|--------|----------|
| INV-008 | close_slice is the sole commit source for the terminal `slice: complete` commit; phase-boundary commits widen content but do not multiply (DC-3 idempotent, DC-4 single phase commit). | PASS (substantive) | `scripts/slice_orchestrator/lifecycle.py` — patch is additive content widening at phase==2, guarded by `path.exists()`; `git log --oneline` shows one phase-2 boundary commit (`1f60a25`), one phase-3 boundary (`14e065a`); validate_architecture.py passes (10 invariants). |

## Test results

- `tests/unit/test_phase_2_handoff_staging_surface.py` — 4/4 PASS.
- Full `uv run pytest` — 1177 passed, 2 failed, 3 skipped, 3 xfailed.
  - `tests/unit/test_d3_bypass_log_format.py::test_every_line_matches_classified_regex` — pre-existing (verified at slice init `6c4315f`).
  - `tests/unit/test_extractor_slice.py::test_emits_parent_edge_to_feature` — pre-existing (verified at slice init `6c4315f`); `[XPASS(strict)]` anchored to L-015 substrate Slice 4.
  Both out-of-scope; inherited-red queue per memory `slice_3_inv008_landed.md`.
- `uv run python scripts/validate_architecture.py` — ALL CHECKS PASSED (10 invariants, 18 ADRs).

## Uncommitted-work blocker

- `tests/unit/test_phase_2_handoff_staging_surface.py` — UNTRACKED. Should have been committed in the Phase-3 boundary commit (`14e065a` is empty). DC-4 forbids Phase 4 from committing; route to `/start-slice failed` so Phase 3 can recover or a follow-up slice lands the test file alongside a self-application check.

## Learnings observed (optional)

The self-application gap is structural: any orchestrator-fix slice whose Phase-2 RED tests exercise the very orchestrator path being fixed will see Phase 2 run under unfixed code. Mitigation candidates: (a) Phase-3 builder explicitly re-stages diff-against-Phase-1 paths under `tests/unit/` as a recovery step; (b) introduce a "self-application check" in Phase 4 auditor scope.
