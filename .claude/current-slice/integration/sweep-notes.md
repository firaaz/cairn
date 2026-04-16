# SLICE-018 Phase 4 — Integration Sweep Notes

**Verdict: PASS.** All declared gates met. One D3 finding surfaced for follow-up (not loggable in-place without breaking this slice's own Phase 2 contract).

## Gate evidence

| Gate | Command | Result |
|---|---|---|
| Full test suite | `uv run python -m pytest` | 240 passed in 16.83s (exit 0) |
| Architecture validator | `uv run python scripts/validate_architecture.py` | 7 invariants, 9 ADRs, ALL CHECKS PASSED (exit 0) |
| Integration gate | `uv run python scripts/integration_gate.py` | Step 3 PASS · Step 4a PASS · Step 4b PASS (exit 0) |
| Ruff check | via integration_gate Step 4a | PASS |

## Invariants touched

`slice.yaml:7 invariants-touched: []`. Trivial pass — no invariant assertion required.

## Envelope compliance

Intent verification Step 7: "`git diff --name-only` between Phase 1 HEAD and Phase 3 HEAD lists only `.claude/d3-bypasses.log`."

Actual `git diff --name-only 61d2664 602ebd2`:
- `.claude/d3-bypasses.log` — declared envelope ✓
- `.claude/current-slice/envelope-expansions.log` — slice-state, always allowed (`operational-reference.md:349`)
- `.claude/current-slice/handoff-phase-1.md` — slice-state
- `.claude/current-slice/handoff-phase-2.md` — slice-state
- `.claude/current-slice/implementation/notes.md` — slice-state
- `.claude/current-slice/slice.yaml` — slice-state
- `.claude/current-slice/validation/approach.md` — slice-state
- `.claude/handoff.md` — always allowed
- `tests/unit/test_d3_bypass_log_format.py` — Phase 2 validation test, recorded in `envelope-expansions.log:1` via `EXPAND_ENVELOPE=1`

Intent Step 7 was overstated — it omitted scope-guard's always-allowed categories (slice-state, handoff, test files). The operational rule (`operational-reference.md:349-350`) is what governs; the actual diff fits that rule. No envelope violation.

## Test post-state (from `test_d3_bypass_log_format.py`)

All 10 Phase 2 tests pass:
- Line count = 4 (`test_log_has_exactly_four_lines`)
- All four lines match `^SLICE-\d+ \d{4}-\d{2}-\d{2} (slice-caused|pre-existing|false-positive): .+$`
- Class distribution `{slice-caused: 0, pre-existing: 4, false-positive: 0}`
- Order `[SLICE-012, SLICE-014, SLICE-016, SLICE-017]`
- Reason preservation (012/014/016) byte-verified
- SLICE-017 line byte-identical to pre-migration
- Trailing newline exactly one

## D3 finding — surfaced, not logged in-place

`uv run python scripts/snapshot_diff.py --diff` (exit 1):

```
Out-of-envelope changes detected:
  tests/unit/test_d3_bypass_log_format.py (new)
```

**Classification (git rule, ADR d3-bypass-classification Decision 1):** `slice-caused`. The path appears in this slice's own commits (Phase 2 commit `6273cf7`). Not pre-existing, not false-positive — it's legitimate Phase 2 output added via `EXPAND_ENVELOPE=1` (named mechanism) but not covered by intent's envelope (Decision 2 `exempt:` syntax does not yet exist).

**Why it is NOT appended to `.claude/d3-bypasses.log`:** Appending would take the log to 5 lines and add a `slice-caused` class token, breaking three Phase 2 contract assertions:
- `test_log_has_exactly_four_lines` (line 64)
- `test_all_lines_classified_pre_existing` (line 80 — pins `{slice-caused: 0, pre-existing: 4, false-positive: 0}`)
- `test_line_order_is_chronological` (line 85 — pins four-ID list)

The Auditor does not rewrite the implementation (ADR-004 D2). Editing Phase 2 tests to admit a fifth line would re-litigate the slice's declared verification shape.

**Structural observation:** SLICE-018's own terminal phase surfaces a D3 finding that its own intent.md post-state pinning forbids the slice from logging. This is a known limitation of this specific slice, not a defect — the migration was defined as a one-time reclassification of exactly four historical entries, and the Phase 2 suite enforces that scope. The finding is dispatched to coordinator input (see Follow-up below) rather than into the log itself.

## Regressions in adjacent code

None. Legacy envelope tests — `test_slice_005_design_decomposition::test_v7_envelope_compliance` and `test_sweep_debt_cleanup::test_v4_envelope_compliance` — pass. The handoff-phase-3 prediction that these would fire on SLICE-018's `git diff HEAD` was mistaken: after Phase 3 committed `.claude/d3-bypasses.log`, the only uncommitted dirty file is `docs/plans/measurements/2026-04-12-slice-003.txt`, which is covered by both tests' allowlists (`test_slice_005_design_decomposition.py:249` allows `^docs/plans/measurements/`; `test_sweep_debt_cleanup.py:144` includes it in the SLICE-007 envelope).

One transient regression was Auditor-induced and reverted: during verification the Auditor ran `snapshot_diff.py --snapshot`, which regenerated `.claude/structural-snapshot.json`, triggering `test_v7_envelope_compliance` until `git restore` reverted the file. Documented here so future Auditors avoid the trap: **run `snapshot_diff.py --diff` only; never `--snapshot` during Phase 4**.

## Follow-up (coordinator input)

1. **SLICE-018 snapshot_diff finding** — `tests/unit/test_d3_bypass_log_format.py` is out-of-envelope by D3's strict rule. Cannot be logged in `.claude/d3-bypasses.log` without violating SLICE-018's Phase 2 post-state pins. Either (a) log in a separate out-of-band record for this slice only, (b) wait for ADR Decision 2's `exempt:` syntax and handle analogous cases prospectively, or (c) accept that the slice that normalizes the log format cannot self-reference its own D3 events.
2. **Auditor hazard documented above** — `snapshot_diff.py --snapshot` during Phase 4 writes a dirty file that trips `test_v7_envelope_compliance`. Consider guarding against accidental use in Phase 4 docs.
3. **Handoff-phase-3 prediction accuracy** — the handoff author predicted legacy envelope tests would fire; they didn't, because those tests' allowlists already accommodate the file paths in play. Not a defect, but a note for calibrating future handoff predictions.

## Phase 4 output

This file + unchanged log (`.claude/d3-bypasses.log` at 4 lines) + integration commit. Ready for `/handoff phase` then `/start-slice complete`.
