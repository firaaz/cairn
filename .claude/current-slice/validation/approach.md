# Phase 2 Validation Approach — compression/slice-1-foundation

## Strategy

RED unit tests per task (1.4–1.7) plus one integration test at `tests/integration/test_compressed_slice_end_to_end.py` that serves as the central autonomous-slice gate. Each unit test file maps 1:1 onto a task in the implementation plan; the integration test proves the composite goal — a trivial slice runs four phases via the orchestrator with zero human intervention.

## Ambiguities resolved

1. **A1 fix class (Path X vs Y).** Resolved out-of-band via `/tmp/cairn-a1-spike-1776679039/` baseline + Spike 2 (`bypassPermissions`). Winner: Path X, one-line orchestrator change (`PERMISSION_MODE = "bypassPermissions"`). Evidence: `docs/plans/2026-04-20-a1-spike-results.md`. This unblocks Phase 3 and is recorded here so Phase 3 does not re-litigate.
2. **Role-guard hook position.** Plan §1.4 Task requires matcher `Write|Edit|MultiEdit|NotebookEdit`. Test `test_settings_json_registers_role_guard_pretooluse` pins exactly one registration with that matcher.
3. **Debug-log filename.** Plan §1.7 pins `{slice-id-slug}-phase-{n}-{role}-{timestamp}.log` — slice id slashes replaced with `-`. Test `test_debug_log_filename_uses_slice_id_and_phase` asserts both tokens present.
4. **Multi-line JSON parser fallback order.** Plan §1.6 specifies line-scan first, balanced-brace walk second. Test `test_line_scan_fallback_still_works` pins backward compatibility; `test_pretty_printed_json_tail_parses` pins forward capability.
5. **Dispatch return contract separation.** `dispatch_phase_agent` returns `{status, ...}`; `dispatch_triager` returns `{action, ...}`. Triager malformed output no longer writes a failure log (plan §1.5). Three tests pin this.

## Amendment

Phase 2 Skeptic committed 20 RED tests in commit `90be69b` but was blocked from writing this file and `coupling-clusters.yaml` by A1. Artifacts seeded from the main operator session after the spike resolved the fix class. Triager escalation correctly exited the orchestrator rather than synthesizing missing context.

## Tests committed (RED)

`tests/unit/test_dispatch_contract_separation.py`, `test_multiline_json_tail.py`, `test_role_guard_wired.py`, `test_orchestrator_live_stderr.py`; `tests/integration/test_compressed_slice_end_to_end.py`. All RED pre-Phase-3 except the portion of `test_role_guard_wired.py` that is collaterally GREEN on the pre-existing role_guard.py behavior.
