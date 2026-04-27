---
slice: compression/lever-Z-fixup
phase: 2-validation
branch: feature/compression
as-of: 2026-04-27
---

## State
Phase-2 RED tests written; all five files RED at commit time per cluster-RED-test discipline. Coupling clusters declared (one per S1, S2, S3, S4.a, S4.b — S4 file-disjoint split per intent §S4). Approach.md ≤300 prose words. Validation directory: `.claude/current-slice/validation/{approach.md,coupling-clusters.yaml}`.

L-014 self-application dogfood RAN per slice-specific directive. Inversion findings load-bearing — see Blocked/Pending #1.

## Next
Operator routes the L-014 inversion candidates (envelope-expansion vs alternate path), then `/start-slice phase 3` dispatches Phase-3 implementer per the five clusters.

## Blocked / Pending
1. **L-014 inversion candidates surfaced (load-bearing).** Three existing tests will silently invert/skip when Phase-3 lands S1 and S4.a. Operator decision required before Phase-3 dispatch:
   - `tests/unit/test_phase_1_writer_query_first.py::test_v7_tools_frontmatter_excludes_read_and_bash` (lines 53-55) — asserts `"Bash" not in tools`. **Inverted by S1**. Proposed envelope expansion: add `tests/unit/test_phase_1_writer_query_first.py` so Phase-3 may amend the inverted assertion (drop the `"Bash" not in tools` line; keep the `"Read" not in tools` assertion which S1 leaves intact).
   - `tests/unit/test_slice_orchestrator_artifact_preservation.py` (`ARTIFACT_FILES` line 49 + `test_d2_phase_artifact_files_copied_byte_identical` lines 86-99) — fixture writes `envelope-expansions.log` at the bare path; S4.a redirects helper to `integration/`, so test silently loses coverage. Proposed envelope expansion: add the file so Phase-3 may move the fixture entry to `integration/envelope-expansions.log`.
   - `tests/unit/test_orchestrator_events_capture.py::populated_current_slice` (line 73) — same bare-path fixture; same silent-skip on S4.a. Proposed envelope expansion: add the file so Phase-3 may move the fixture entry.
2. Phase-1 dispatch defect still active until S1 lands (recursive bootstrap pattern unchanged).
3. `_reconcile_resume_state` orphan, cost re-measurement, and substrate Slice 4+ all remain out-of-scope (carried forward from Phase-1 packet).
4. `INV-004` turn-1 token-budget OOS env-dependent failure (`test_inv004_turn1_token_budget`) is pre-existing per Phase-1 packet and not introduced by this slice.

## Pointers
- `.claude/current-slice/intent.md` — full S1-S5 spec, envelope, Closes-when, hard non-goals.
- `.claude/current-slice/validation/approach.md` — cluster→RED-test mapping + L-014 dogfood findings.
- `.claude/current-slice/validation/coupling-clusters.yaml` — five clusters, file-disjoint split for S4.
- `.claude/current-slice/handoff-phase-1.md` — Phase-1→2 packet (still relevant for Blocked/Pending continuity).
- `tests/unit/test_phase_1_writer_query_first.py:53-55` — L-014 inversion candidate #1 (S1).
- `tests/unit/test_slice_orchestrator_artifact_preservation.py:49,86-99` — L-014 inversion candidate #2 (S4.a).
- `tests/unit/test_orchestrator_events_capture.py:73` — L-014 inversion candidate #3 (S4.a).
- `scripts/slice_orchestrator/lifecycle.py:101` and :131 — `_ARTIFACT_RELPATHS` definition + the iteration site that drives the silent-skip path.
