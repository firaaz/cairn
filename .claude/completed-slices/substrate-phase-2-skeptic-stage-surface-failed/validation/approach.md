# Phase 2 RED — approach

## What is asserted

`commit_phase_handoff(phase=2, ...)` must extend its staging set to include
every path under `tests/unit/` that diverged (added/modified) from the
Phase-1 boundary, guarded by `path.exists()`, alongside the existing
`handoff-phase-2.md` stage. The Phase-2 boundary remains a single commit
(INV-008 DC-4 — content widening, not commit-count widening); a re-run
against an empty diff is a no-op (INV-008 DC-3).

## Test surface (`tests/unit/test_phase_2_handoff_staging_surface.py`)

| Case | Setup | Today | Post-fix |
|------|-------|-------|----------|
| R1   | 1 slug-named `tests/unit/` file on disk; diff returns it | RED — only handoff-md staged | path staged |
| R2   | 3 mixed-naming files on disk; diff returns all 3 | RED — none staged | all 3 staged |
| R3   | 0 files; diff empty | trivially green | still green (no `tests/unit/` adds) |
| R4   | 1 file + modified handoff-phase-2.md; diff returns the file | RED — only handoff-md staged | both staged in one commit |

R3 is a contract-guard against an unguarded extension (e.g. a
slug-globbed sentinel that always stages something). R4 also asserts at
most one `_git("commit", ...)` call at the boundary, pinning DC-4.

## Discovery mechanism

Diff-based: tests stub `_git` so any `git diff ...` invocation returns
configured paths. The Phase-1 boundary SHA-resolution mechanism
(state-file vs. `git log` walk vs. caller-supplied) is intentionally
unpinned — Phase-3 implementer chooses. R2's non-slug-named entry pins
that discovery is *not* slug-glob.

## Ambiguity audit

- **Public signature** of `commit_phase_handoff(phase, summary,
  commit_hash)` — verified via package re-exports and existing
  `test_commit_phase_handoff_stage_surface.py`. No guess.
- **Path.exists() guard** — explicit in intent §Specification step 3.
- **SHA resolution** — left unpinned (decoupled via `_git` stub).
- **Commit shape** — explicit in intent §INV-008 DC-4.

No unresolved ambiguity warranting `RAISE_ISSUE`.

## Out of scope (per intent §Boundary)

Phase-3 staging (handles its own writes); Phase-4 staging (already
fixed at `a8d8f23`); commit count/subject changes; the Phase-1 boundary
discovery mechanism itself.
