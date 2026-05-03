---
title: Substrate paper-cut bundle + issue #26 — slice plan
date: 2026-05-02
branch: feature/compression-followup
status: design-approved
---

# Substrate paper-cut bundle + issue #26

## Context

The 2026-05-02 integration sweep (`.claude/sweep-results/2026-05-02-sweep.md`) closed
`compression/upgrade-doc-bug-fixes` PASS-with-known-debt and surfaced four substrate
paper-cuts under § Substrate paper-cuts. Pre-design investigation reclassified one of
them (see § Reclassification of paper-cut #3) and confirmed the remaining three plus
the open S1 issue #26 as the actual scope.

This plan covers two slices on `feature/compression-followup` (branch ceiling
2026-05-11).

## Reclassification of paper-cut #3

The sweep report attributed the malformed `.claude/sweep.yaml` to a "phase-4-integrator
stage-surface leak (issue #26)." This attribution is wrong:

- `commit a8d8f23` (2026-04-21) extended `close_slice` staging in
  `scripts/slice_orchestrator/lifecycle.py:540` to include `.claude/sweep.yaml` and
  `.claude/handoff.md`. Phase-4 staging surface was fixed at that point.
- The malformed `sweep.yaml` content originated in `commit 6cfa4d0` (compression program
  merge, 2026-04-21), pre-dating `a8d8f23`'s downstream effect on this branch.
- Issue #26 itself states: *"No expansion to Phase 4. Phase 4 is `slice: complete`
  territory — already covered by `close_slice` and Slice E's prior fix landed at
  `a8d8f23`."*
- The 2026-05-02 sweep (commit `cf4a5cb`) rewrote `sweep.yaml` to protocol shape. No
  active bug remains.

**Action:** drop paper-cut #3 from scope. Note the misattribution in the next handoff
so the lesson does not get re-discovered.

## Slice 1 — `substrate/papercut-bundle`

Three trivial fixes bundled because each is a one-line touch in a different module and
none has cross-cutting consequences.

### Envelope

| # | Path | Change |
|---|------|--------|
| 1 | `checks/scope-guard.sh:60` | Add `.claude/d1-bypasses.log` and `.claude/d3-bypasses.log` to the admin-allowlist `case` so Write/Edit appends do not require `EXPAND_ENVELOPE=1` or a Bash heredoc bypass. |
| 2 | `commands/claude-code/integration-sweep.md:11` | Change `python3 scripts/integration_gate.py` to `uv run python scripts/integration_gate.py`. Aligns the documented invocation with the venv requirement (the script imports `pydantic`, which only exists under `.venv`). |
| 4 | `scripts/verify_handoff.sh:35-40` | Extend check (c) regex with a fourth accepted subject form: `^sweep: `. Sweep commits currently fail check (c); the failure is latent because `verify_handoff.sh` is not on the pre-commit hook chain, but it is invoked by `close_slice` and exercised by `tests/unit/test_orchestrator_bug_fixes.py`. |

### Test surface

- `tests/unit/test_scope_guard_admin_allowlist.py::test_d1_d3_bypass_logs_admin_allowed`
  — exercise scope-guard.sh against a Write hook input for each log path; expect exit 0
  even without slice envelope coverage.
- `tests/unit/test_verify_handoff_sweep_subject.py::test_check_c_accepts_sweep_prefix`
  — invoke `verify_handoff.sh` against a synthetic HEAD whose subject begins with
  `sweep: `; expect exit 0.
- **No new test for paper-cut #2.** Pure doc change; existing CI runs under uv so
  there is no regression surface to assert against. The risk is limited to a future
  reader copy-pasting the old command outside venv, which the doc fix prevents.

### Out of scope

- The actual integration_gate.py script behavior. We are not adding a re-exec or
  bootstrap path; the documented invocation is the authoritative entry point.
- The pre-commit hook chain. Adding `verify_handoff.sh` to pre-commit is a separate
  question with its own design — extending the regex is sufficient for the existing
  callers.

## Slice 2 — `substrate/phase-2-skeptic-stage-surface` (issue #26)

Defers to issue #26 body for fix shape and test matrix. Summary follows so this plan
stands alone.

### Envelope

- `scripts/slice_orchestrator/lifecycle.py` — extend `commit_phase_handoff` so that
  when `current_phase == 2`, the staging set includes every file under `tests/unit/`
  whose state diverges from the Phase-1 boundary commit (added or modified).
- `tests/unit/test_phase_2_handoff_staging_surface.py` — new file, four cases per
  issue #26 § Test surface (R1–R4):
  - R1: Phase-2 wrote 1 test file → Phase-2 commit contains it.
  - R2: Phase-2 wrote 3 test files (slug-named + non-slug-named) → all 3 staged.
  - R3: Phase-2 wrote 0 test files → Phase-2 commit shape unchanged (handoff-phase-2.md
    only).
  - R4: Phase-2 wrote a test file AND modified handoff-phase-2.md → both staged.

### Discovery mechanism

Issue #26 recommends approach (a): diff `tests/unit/` against the Phase-1 boundary
commit and stage everything new/modified. Approach (b) (glob on slug pattern) is
rejected for being naming-convention-fragile.

### INV-008 preservation

Per issue #26 §INV-008 preservation:

- DC-3 (idempotency) preserved — the extension is additive stage-list, the
  `if path.exists()` guard makes re-runs no-op.
- DC-4 (no extra commits at phase boundary) preserved — extension widens the existing
  Phase-2 commit's content; it does not introduce new commits.

### Out of scope

- Phase-3 staging behavior — already handles its own writes via the existing path.
- Phase-4 staging behavior — already fixed by `a8d8f23`.

## Sequencing

1. **Slice 1 first.** Three trivial fixes; fast feedback that the substrate-fix
   workflow is healthy. Closes ahead of any deeper investigation.
2. **Slice 2 second.** S1 severity but more invasive (real lifecycle.py change with
   four-case regression matrix). Wants Slice 1's clean close behind it for clearer
   bisect surface if anything regresses.
3. Both slices land on `feature/compression-followup`. The branch ceiling is
   2026-05-11; six other followup slices remain queued, so the ceiling is the
   binding constraint. If Slice 1 + Slice 2 take ≥1 day each, revisit ceiling
   after Slice 2.

## What this plan deliberately omits

- *Architecture / data flow.* Both slices are single-file behavioral patches with no
  cross-component flow.
- *Error handling.* Each fix is additive — extends accepted sets, preserves prior
  behavior. No new error paths.
- *Performance.* Neither change is on a hot path (scope-guard.sh runs per Write/Edit
  hook event; lifecycle.py runs once per phase boundary). Existing performance
  envelope is unaffected.
