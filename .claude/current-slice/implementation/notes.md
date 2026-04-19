---
slice: compression/orchestrator-hardening
phase: 3-implementation
as-of: 2026-04-19
---

## Builder decisions (intent left to judgment)

**Constant name.** `PERMISSION_MODE = "acceptEdits"` — module-level, top-of-file next to `DEFAULT_TIMEOUT_HARD`. Intent F1 pins UPPERCASE + value; name is Builder's choice. Chose the shortest descriptive name.

**Brief serialisation format.** `brief: "<verbatim>"` (double-quoted). `read_slice_state` at `scripts/slice_orchestrator.py:47-69` strips paired surrounding quotes after `partition(':')`, so quoted round-trips cleanly. Unquoted would also round-trip for simple briefs but would break on leading-whitespace edge cases; quoted is the conservative default and matches the existing `name:` line's convention. Embedded double-quotes in briefs are not escaped (none of the RED tests exercise it; intent lists no such requirement).

**Brief injection scope.** `run_phase_loop` reads brief via new helper `_slice_brief()` and adds it to the `inputs` dict for every phase dispatch, not just Phase 1. Intent F2 mandates Phase 1 coverage; broader propagation is zero extra complexity and matches "brief survives across the dispatches" (intent §F2 rationale). Only added when non-empty so seeded slice.yaml without `brief:` behaves unchanged.

**Edit sites vs. envelope markers.**
- Intent cited `105-133, 237, 335` for envelope modification sites. Post-edit line numbers shift because `dispatch_agent` cmd list is now multi-line. The four touched regions are: constant near line 37 (new), `dispatch_agent` cmd list at ~111 (rewritten), `_slice_brief` helper after `_slice_id` (new), `run_phase_loop` inputs assembly at ~239 (brief injection), `init_new_slice` slice.yaml write at ~343 (brief line added).

## Verification

- 8 target tests GREEN: `uv run pytest tests/unit/test_orchestrator_hardening.py` → 8 passed.
- F3 state-machine tests still GREEN: `test_v2_6_run_phase_loop_failed_retries_once` + `test_a8_retry_uses_same_inputs_and_envelope` pass.
- 14 pre-existing failures confirmed unchanged via baseline stash-test (4 state-machine + 7 hook-path + 2 housekeeping + 1 item_d). All out-of-envelope per intent §Boundary and sweep-#20 deferrals.
- Ruff clean on all three envelope files.

## Out-of-envelope pre-existing failures (Phase 4 handoff)

The intent's §Verification item 5 expected 3 pre-existing failures remaining; the real count is 14. The delta (11 tests) is out-of-envelope and queued for the housekeeping micro-slice per Phase-2 handoff. The Phase 4 Integrator will observe this drift; approach.md §"Pre-existing failures" from Phase 2 already documents it.
