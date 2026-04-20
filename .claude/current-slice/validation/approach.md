# Phase 2 Approach — compression/slice-3-observability-and-close-slice

## Mapping intent → tests

Source of truth = **intent.md contract-to-test map**; augmented with the
per-file function inventory in
`docs/plans/2026-04-20-observability-and-close-slice-design.md §Testing`. When
the two conflict the intent wins (DC-6 has 13 rows; slug-collision tripwire
is in scope).

| Contract | Tests |
|---|---|
| INV-008 DC-3 | `test_close_slice_hardened.py::test_close_slice_twice_is_noop`, `…::test_close_slice_short_circuits_on_already_closed_state` |
| INV-008 DC-4 (code) | `test_close_slice_hardened.py::test_run_phase_loop_skips_commit_at_phase_4_boundary`, `…::test_close_slice_produces_single_slice_complete_commit` |
| INV-008 DC-4 (prompt) | `test_agent_prompt_updates.py::test_phase_4_prompt_explicitly_forbids_self_commit` |
| INV-008 DC-7 | `test_cross_slice_isolation.py` (4 tests incl. `test_slug_collision_exits_failed`) |
| DC-5 wipe | `test_close_slice_hardened.py` (`test_wipe_*`) |
| DC-6 resume | `test_resume_reconcile.py::test_resume_matrix_row[row-1..13]` + `test_resume_unmatched_triple_refuses_with_triple_printed` |
| Obs D2 MD derived | `test_observability_writer.py::test_md_is_derived_from_json_state`, `…::test_write_result_md_only_runs_on_terminal_transition` |
| Obs D3 decouple | `test_heartbeat.py::test_heartbeat_never_writes_result_json`, `…::test_state_writer_never_writes_heartbeat` |
| Obs D4 schema | `test_state_schema.py` (4 tests) |
| Obs D6 error policy | `test_observability_writer.py::test_atomic_write_*`, `…::test_degraded_status_replaces_in_progress_on_retry_exhaustion`, `test_heartbeat.py::test_heartbeat_one_restart_attempt_then_degrade` |
| Obs D7 degradation persists | `test_observability_writer.py::test_degradation_reason_persists_through_terminal_transition` |
| P1/P2 prompts | `test_agent_prompt_updates.py` (heredoc + no-preemptive-refuse) |
| atexit / signal | `tests/integration/test_signal_observability.py` (3 tests) |

## Overlap with pre-existing suite

`tests/unit/test_close_slice_invocation.py` already asserts the Slice-2-era
invocation contract. Slice 3 keeps it GREEN and adds `test_close_slice_hardened.py`
with net-new DC-3 idempotency, DC-4 `handoff: phase 4 complete` absence, and
DC-5 wipe assertions. Both must pass post-Phase-3.

## RED expectation

Every new test fails at Phase 2 via one of:

- `AttributeError` on `_atomic_write`, `_persist_state`, `_generate_result_md`,
  `_write_result_md`, `_append_index_entry`, `_observability_paths`,
  `_update_state`, `_state`, `_HeartbeatDaemon`, `_is_slice_already_closed`,
  `_wipe_current_slice`, `_reconcile_resume_state`,
  `_register_atexit_terminal_writer`.
- Assertion failure on current `close_slice` / `run_phase_loop` behavior.
- Grep failure on agent prompts (no P1/P2/DC-4 clauses yet).

Verified: 57 new tests RED; 592 pre-existing tests remain GREEN (11 pre-existing
failures unrelated to this slice).

## Out of scope for Phase 2

No production code. `scripts/slice_orchestrator.py` and phase-agent prompts
are untouched; those belong to Phase 3.
