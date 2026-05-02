---
slice: substrate/phase-2-staging-untracked-enumeration
phase: 4
status: OK
---

## Summary
Phase-2 staging arm in `lifecycle.py` now unions `git ls-files --others --exclude-standard -- tests/unit/` with the existing `git diff` set, closing the untracked-test blind spot from issue #26. R5–R7 RED tests added in af0b5e0 → c2065e2 GREEN. INV-008 preserved (additive widening; single phase-boundary commit; idempotency guard intact).

## Verification
- `uv run pytest`: 1180 passed; 2 pre-existing fails (d3 log line 18; extractor XPASS) — out of scope.
- `validate_architecture.py`: PASS (10 invariants, 18 ADRs).
- INV-008 proxy: `def close_slice` present at `scripts/slice_orchestrator/lifecycle.py:473`.

## Next
Sweep cadence: bump interval. Open follow-ups unchanged (d3 log; substrate Slice 4 / L-015; phase-2-skeptic write-timing).

---
# Sweep notes — substrate/phase-2-staging-untracked-enumeration

## Pytest
1180 passed, 3 skipped, 3 xfailed, 2 failed (pre-existing, out of scope):
- `test_d3_bypass_log_format::test_every_line_matches_classified_regex` — line 18 malformed (tracked: v1-defense-d3/bypass-log-test-resilience).
- `test_extractor_slice::test_emits_parent_edge_to_feature` — XPASS-strict from squash-merge collapse (tracked: substrate Slice 4 / L-015).

Both predate this slice and are listed in `.claude/handoff.md` Blocked/Pending.

## validate_architecture.py
ALL CHECKS PASSED — 10 invariants verified, 18 ADRs checked.

## Invariants

| ID | Statement | Status | Evidence |
|----|-----------|--------|----------|
| INV-008 | Proxy check: verifies the close_slice function exists in the orchestrator package (the function whose lifecycle is contracted by INV-008). Migrates to test-ref on tests/unit/test_close_slice_hardened.py::test_close_slice_twice_is_noop when the implementing slice lands the test file. | PASS | scripts/slice_orchestrator/lifecycle.py:473 (`def close_slice`); slice fix is additive widening of phase-2 staging arm — no new commits emitted, idempotency guard preserved. |

## Scope check
Diff touches: `scripts/slice_orchestrator/lifecycle.py` (phase-2 staging block), `tests/unit/test_phase_2_handoff_staging_surface.py` (R5–R7 added), `.claude/features/substrate.yaml`, `.claude/current-slice/*`. Within declared envelope.

## Learnings observed (optional)
