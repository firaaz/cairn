# Phase 4 Handoff — cost-discipline/lever-1-tier-retune

**Status:** OK — slice ready for close.

## What Phase 4 verified

- Three declared invariants (INV-003 phase-lock-and-role-declaration, INV-008 slice-close-contract, INV-009 cost-per-slice-budget): PASS — see `integration/sweep-notes.md` for file:line citations.
- Slice's own RED-test file `tests/unit/test_slice_orchestrator_model_config.py`: 32/32 pass, including default-resolution + env-override-precedence coverage on both retuned rows.
- Full pytest: 932 pass / 3 skip / 8 fail. All 8 failures are pre-existing and trace to the known `cairn-substrate-and-fastmcp` ADR-without-ARCHITECTURE-invariant condition; intent §Verification explicitly tolerates them.
- `scripts/validate_architecture.py`: pre-existing failure, same root cause, tolerated by intent.

## Source delta confirmed in committed scope

- `scripts/slice_orchestrator/core.py:41-47` — `phase-3-implementer.effort` = `high`; `phase-4-integrator.model` = `claude-opus-4-7`. (commit c683a9d)
- `tests/unit/test_slice_orchestrator_model_config.py` — extended assertions covering new defaults + override-precedence regression guards. (commit c683a9d)
- `docs/operational-reference.md` env-var table cells (~409-411) — Default columns updated, retune rationale parentheticals appended. (commit d7a820d)

`_resolve_model_config` body unchanged; env-var override surface unchanged; `--model` / `--effort` splice unchanged.

## Working-tree state

Clean. The orphan orchestrator-events capture work that the prior Phase-4 dispatch flagged (`_record_orchestrator_event`, lifecycle event-recording sites, `test_orchestrator_events_capture.py`) has been removed from the worktree. Operator triage from the prior RAISE_ISSUE was honored: brief-aligned delta retained, orphan feature carved out for a separate slice.

Only uncommitted entries are the expected Phase-4 artifacts:
- `.claude/current-slice/slice.yaml` (current_phase = 4)
- `.claude/current-slice/integration/sweep-notes.md`
- `.claude/current-slice/handoff-phase-4.md`

## For close_slice

- `.claude/sweep.yaml` updated.
- `.claude/handoff.md` updated to reflect closure + queue substrate Slice 2 / orchestrator-events-capture / inv004 rebaseline.
- Memory note `project_per_phase_model_and_thinking` should be updated post-close with this slice's empirical-signal closure.

## DC-4 reminder

Phase 4 did not run `git commit`. Terminal `slice: complete` commit is the orchestrator's `close_slice` responsibility.

---
# Phase 4 Sweep — cost-discipline/lever-1-tier-retune

## Invariant verification

| Invariant | Status | Evidence |
|---|---|---|
| INV-003 phase-lock-and-role-declaration | PASS | scripts/slice_orchestrator/core.py:41-47 — only tier value cells changed; role keys, ordering, phase-loop unchanged. |
| INV-008 slice-close-contract / slice-artifact-preservation | PASS | scripts/slice_orchestrator/lifecycle.py — no _git site, close-path, or _ARTIFACT_RELPATHS change in committed slice scope. |
| INV-009 cost-per-slice-budget (advisory) | PASS | scripts/slice_orchestrator/core.py:41-47 — one input (default tier) changed by design; INV_009_* thresholds untouched. |

## Verification commands

- uv run pytest -q tests/unit/test_slice_orchestrator_model_config.py -> 32 passed.
- uv run pytest -q -> 932 passed, 3 skipped, 8 failed (all pre-existing, out-of-scope; trace to known cairn-substrate-and-fastmcp ADR-without-ARCHITECTURE.md-invariant condition):
  - tests/unit/test_validate_architecture.py::test_v1_cairn_self_dogfood_baseline
  - tests/unit/test_adr_rename_sweep.py::TestV7Validator::test_validate_architecture_exits_0
  - tests/unit/test_adr_rename_sweep.py::TestContractC3CurrentCorpusPasses::test_sweep_tests_pass_on_live_corpus
  - tests/unit/test_adr_rename_sweep.py::TestContractC4RobustnessUnderGrowth::test_valid_new_adr_keeps_suite_green
  - tests/unit/test_invariant_assertions.py::TestCairnSelfDogfood::test_cairn_self_validation_still_passes
  - tests/unit/test_invariant_assertions.py::TestSlice011ZeroWarnings::test_zero_check_d_failures
  - tests/unit/test_slice_orchestrator_package_split.py::test_v5_architecture_validator_post_split
  - tests/unit/test_sweep_debt_cleanup.py::test_v5_architecture_validator
- uv run python scripts/validate_architecture.py -> FAILED (1 issue, same root cause). Pre-existing, out-of-scope per intent §Verification.

## Closes-when verification (intent.md §Verification)

- OK: extended model-config tests pass (32/32), no regressions in passing baseline.
- OK: AGENT_MODEL_CONFIG literal at scripts/slice_orchestrator/core.py:41-47 matches intent table — phase-3-implementer = (claude-sonnet-4-6, high); phase-4-integrator = (claude-opus-4-7, low); P1/P2/triager unchanged.
- OK: docs/operational-reference.md env-var table cells for CAIRN_EFFORT_PHASE_3_IMPLEMENTER (default high) and CAIRN_MODEL_PHASE_4_INTEGRATOR (default claude-opus-4-7) updated with retune rationale parentheticals (lines ~409-411). Edit 3 landed at d7a820d.
- OK: _resolve_model_config body unchanged (env-var precedence + opus-high unknown-role fallback intact).
- TOLERATED: architecture validator fails on pre-existing cairn-substrate-and-fastmcp issue.

## Working-tree state at Phase-4 entry

Clean. The prior Phase-4 dispatch flagged orphan orchestrator-events capture work; that work has been excised from the worktree. git diff --stat HEAD against scripts/ and tests/ is empty; only .claude/current-slice/slice.yaml (current_phase bump) and Phase-4 artifacts are uncommitted, as expected.

Brief-aligned source delta committed at c683a9d (core.py two-row retune + RED-test extension). Edit-3 docs cells committed at d7a820d.
