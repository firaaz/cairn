---
slice: v1-defense-d3/bypass-log-test-resilience
date: 2026-05-02
phase: 1-intent
invariants-touched: []
adrs-referenced:
  - d3-bypass-classification
envelope:
  - ".claude/d3-bypasses.log"
  - "tests/unit/test_d3_bypass_log_format.py"
out-of-scope:
  - "lines 1-17 of .claude/d3-bypasses.log (already classified — byte-immutable)"
  - "CLASSIFIED_LINE_RE widening (already supports SLICE-NNN | hierarchical ids and optional `(A-D)` qualifier per test line 24)"
  - "docs/adr/d3-bypass-classification.md (append-only per checks/reversibility-guard.sh)"
  - "scripts/snapshot_diff.py (envelope-exempt parsing — separate ADR D2 follow-through, not this slice)"
  - "checks/*.sh hooks (no write-time validator introduced — out of scope per ADR provisional firmness + v0 reset)"
  - "appended log lines after current line 19 (none exist yet; future entries are not this slice's concern)"
  - "test_housekeeping_post_slice_a_tidy.py::test_item_d_no_empty_current_slice_subdirs (separate failure surfaced by sweep-4; tracked separately)"
---

# Intent — v1-defense-d3/bypass-log-test-resilience

## What and Why

`tests/unit/test_d3_bypass_log_format.py::test_every_line_matches_classified_regex` halts `integration_gate -x` on every sweep because two entries written by `substrate/orchestrar-paths` (lines 18–19 of `.claude/d3-bypasses.log`) lack the `<class>:` token mandated by ADR `d3-bypass-classification` Decision 1. The entries' reasons self-describe as pre-existing (kuzu MCP tests outside scope; stale snapshot baseline) but the classification token is missing, so `CLASSIFIED_LINE_RE` rejects them.

The test is correct; the substrate is malformed. Brief framing ("test resilience") is satisfied by making the substrate well-formed so the test stops being a recurring sweep-noise source — not by relaxing the schema. Relaxing would defeat ADR D1's purpose (distinguishing `false-positive` from `pre-existing` so the rolling-window counter targets noise, not debt).

This slice backfills the two unclassified entries with `pre-existing:` (the migration pattern established for SLICE-012/014/016 historical reclassification, ADR D1 last paragraph). After backfill, `pytest -x` clears past line 19; integration_gate stops halting on this file.

## Specification Detail

### S1 — Backfill line 18 with `pre-existing:` classification

`.claude/d3-bypasses.log` line 18, currently:

```
substrate/orchestrator-paths 2026-04-30 integration_gate fails on 4 pre-existing kuzu MCP tests (issue #25 scope); invariant+ruff PASS
```

becomes:

```
substrate/orchestrator-paths 2026-04-30 pre-existing: integration_gate fails on 4 pre-existing kuzu MCP tests (issue #25 scope); invariant+ruff PASS
```

Class is `pre-existing` because the kuzu MCP test failures are tracked under issue #25 and predate the slice's start commit (git-verifiable per ADR D1 class definition).

### S2 — Backfill line 19 with `pre-existing:` classification

`.claude/d3-bypasses.log` line 19, currently:

```
substrate/orchestrator-paths 2026-04-30 snapshot baseline 2026-04-30T00:37 is many slices stale; reported new files are pre-existing housekeeping outside slice envelope
```

becomes:

```
substrate/orchestrator-paths 2026-04-30 pre-existing: snapshot baseline 2026-04-30T00:37 is many slices stale; reported new files are pre-existing housekeeping outside slice envelope
```

Class is `pre-existing` because the stale baseline predates the slice's start commit; reason text already names the path as housekeeping outside the envelope.

### S3 — Lines 1–17 byte-immutable

No edits to lines 1–17. `test_slice_017_line_byte_identical` and the migration-anchor pins for SLICE-012/014/016 must continue to pass without modification.

### S4 — Trailing newline preserved

After backfill, `.claude/d3-bypasses.log` ends with exactly one `\n`. `test_trailing_newline_exactly_one` continues to pass.

### S5 — No regex change, no test relaxation

`CLASSIFIED_LINE_RE` is unchanged. `test_every_line_matches_classified_regex` becomes greener purely because the substrate is now well-formed across all 19 lines. Phase 2 (Skeptic) MAY add a structural assertion that pins both `substrate/orchestrator-paths` lines as `pre-existing` (parallel to the SLICE-012/014/016 migration-anchor pins) to prevent silent reclassification; the assertion is in scope but optional — Skeptic's call.

### S6 — No new substrate files, no hook, no ADR edit

The fix is two single-line backfills. No new validator, no new YAML key, no ADR supersession. ADR `d3-bypass-classification` `firmness: provisional` and the v0 reset commitment together mean substrate growth is to be avoided; backfill alone is the minimum-viable mitigation.

## Boundary

**In scope.** Two single-line backfills in `.claude/d3-bypasses.log` (lines 18 and 19). Optional Phase-2 structural pin in `tests/unit/test_d3_bypass_log_format.py` for the two backfilled lines.

**Out of scope.** Listed exhaustively in the envelope `out-of-scope` block above. Notably: regex widening (already done in a prior slice — see CLASSIFIED_LINE_RE line 24), `snapshot_diff.py` exempt-list parsing (ADR D2's separate follow-through), and any write-time linter or hook for the log (deliberately not introduced per ADR's provisional firmness).

## Verification

### Substrate assertions (Phase 4 Auditor-runnable)

- **V1** `sed -n '18p' .claude/d3-bypasses.log` matches `^substrate/orchestrator-paths 2026-04-30 pre-existing: integration_gate fails on 4 pre-existing kuzu MCP tests \(issue #25 scope\); invariant\+ruff PASS$`.
- **V2** `sed -n '19p' .claude/d3-bypasses.log` matches `^substrate/orchestrator-paths 2026-04-30 pre-existing: snapshot baseline 2026-04-30T00:37 is many slices stale; reported new files are pre-existing housekeeping outside slice envelope$`.
- **V3** `git diff --unified=0 HEAD -- .claude/d3-bypasses.log` shows exactly two changed lines (line 18 and line 19); no other line is touched. Lines 1–17 byte-identical to pre-slice HEAD.
- **V4** `tail -c 1 .claude/d3-bypasses.log | od -An -c` shows `\n`; `tail -c 2 .claude/d3-bypasses.log | od -An -c` does NOT show `\n \n` (exactly one trailing newline).

### Behavioral assertions (Phase 4 Auditor-runnable)

- **V5** `uv run pytest tests/unit/test_d3_bypass_log_format.py -x` exits 0 with all tests green. In particular `test_every_line_matches_classified_regex` no longer fails on lines 18/19.
- **V6** `uv run pytest tests/unit/test_d3_bypass_log_format.py::test_log_has_at_least_four_lines` passes (the `>=4` floor is preserved; we did not shrink the log).
- **V7** `uv run pytest tests/unit/test_d3_bypass_log_format.py::test_slice_017_line_byte_identical` passes (migration-anchor immutability preserved).

### Schema-counter assertions (ADR D1 alignment)

- **V8** No new `false-positive` entries are introduced by this slice; the rolling-window noise count stays at zero. (Backfill of `pre-existing` classes is logged but not counted, per ADR D1 rolling-window rule change.)
- **V9** Both backfilled lines pass the `pre-existing` class's git-verifiability test: their named drift (kuzu MCP tests, stale snapshot baseline) predates the `substrate/orchestrator-paths` start commit on 2026-04-30 — verifiable via `git log --before=2026-04-30 -- <path>`.

### Integration-gate effect (release criterion)

- **V10** Next `/integration-sweep` run does not list `test_d3_bypass_log_format.py` as a halt site for `integration_gate -x`. The recurring sweep-noise failure surfaced in sweeps from 2026-04-18 (`identifier-scheme/doc-sweep`) through 2026-05-02 (`compression/upgrade-doc-bug-fixes` — sweep #4) is eliminated.
