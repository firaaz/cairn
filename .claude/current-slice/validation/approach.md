# Phase 2 approach — compression/slice-artifact-preservation

## Intent under test

ADR `slice-artifact-preservation` (D1, D2, D2.vii, D6, D7) plus the implementing
plan's Task 1: a private helper `_copy_artifacts_to_sweep_results(slice_id,
pre_close_yaml_text)` in `scripts/slice_orchestrator/lifecycle.py`, wired into
`close_slice` between bundle (Step 2) and wipe (Step 3), with caller-supplied
pre-close `slice.yaml` text captured BEFORE Step 1 mutates `status=complete`.

## Test surface (8 RED tests)

One file: `tests/unit/test_slice_orchestrator_artifact_preservation.py`.

- D2 byte-identity (handoffs)        -> `test_d2_handoff_phase_files_copied_byte_identical`
- D2 byte-identity (phase artifacts) -> `test_d2_phase_artifact_files_copied_byte_identical`
- D2.vii pre-close yaml capture      -> `test_d2_pre_close_slice_yaml_captured_not_post_close`
- D6b F5-tolerance (missing source)  -> `test_d6b_missing_source_skips_silently`
- D7/(c) ENOSPC at copyfile          -> `test_c_operational_copy_failure_raises`
- D7/(c) EACCES at makedirs          -> `test_c_target_dir_creation_failure_raises`
- D6a idempotency on re-invocation   -> `test_d6a_helper_idempotent_on_repeat_invocation`
- D1 ordering (close_slice e2e)      -> `test_d1_close_slice_copies_before_wipe`

Initial pytest run: all 8 fail with `AttributeError: module
'slice_orchestrator.lifecycle' has no attribute '_copy_artifacts_to_sweep_results'`.

## Ambiguities resolved

1. **Import path / patch target.** Plan specifies `from scripts.slice_orchestrator
   import lifecycle` and `patch("scripts.slice_orchestrator.lifecycle...")`.
   `pyproject.toml` sets `[tool.pytest.ini_options] pythonpath = ["scripts"]`,
   making `slice_orchestrator` the top-level package; existing tests
   (`test_close_slice_*.py`, `test_state_schema.py`, etc.) all use
   `import slice_orchestrator as so`. Resolved via pyproject (architecture):
   tests use `from slice_orchestrator import lifecycle` and corresponding
   `patch("slice_orchestrator.lifecycle...")` targets.

2. **Test count: plan/intent say "9 RED", actual code block defines 8.** The
   plan's "Tests Phase 2 writes" code block contains 8 test functions; intent.md
   V-list runs V1-V8 (8 entries). The "9" likely conflated the 9 entries in
   `_ARTIFACT_RELPATHS`. Resolved by writing the 8 tests the plan defines
   verbatim. Coverage of all six listed decisions (D1, D2, D2.vii, D6a, D6b, D7)
   is preserved.

## Out of scope for Phase 2

`.gitignore` (Task 2), `start-slice.full.md` line 210 (Task 3), `ARCHITECTURE.md`
INV-008 (Task 4) - all prose edits, no Phase-2 tests per plan convention. The
co-landing ADR is verified at Phase 4 sweep (V15), not Phase 2.

## Phase 3 expectations

Add `import shutil`, `_ARTIFACT_RELPATHS`, the helper, and the Step-0.5/Step-2.5
wiring in `close_slice` per plan Implementation. All 8 tests turn GREEN; the
existing `test_close_slice_*.py` suite is unaffected (helper writes outside
`.claude/current-slice/`).
