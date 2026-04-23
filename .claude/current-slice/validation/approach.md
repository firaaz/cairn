# Phase-2 Approach — compression/phase-1-handoff-stage-surface

## What the tests assert

Four tests in tests/unit/test_commit_phase_handoff_stage_surface.py pin the
stage-list of scripts/slice_orchestrator.py:commit_phase_handoff to the
phase-1-writer declared write surface (.claude/agents/phase-1-writer.md:9):

- **R1a** — intent.md stages when present at Phase 1.
- **R1b** — .claude/features/<feature>.yaml stages when present. Feature-id
  resolves from slice.yaml id via _slice_id(); demo/slice-x -> demo.yaml.
- **R2a** — intent.md NOT staged when absent (no call, no exception).
- **R2b** — feature-file NOT staged when absent (no call, no exception).

## Method

Stub slice_orchestrator._git with a recorder capturing positional args;
invoke commit_phase_handoff(1, "summary", "hash"); read the recorded
_git("add", <path>) calls via an _adds() helper tolerant of a leading -f
flag. No subprocess git — Slice E already owns the real-git integration
surface. Stubbing isolates the stage-list contract from git mechanics.

## RED/GREEN matrix (measured, pytest 0.04s)

| Test | Today | After Phase 3 | Role |
|------|-------|---------------|------|
| R1a  | FAIL  | PASS          | primary failing spec |
| R1b  | FAIL  | PASS          | primary failing spec |
| R2a  | PASS  | PASS          | guard-regression (path.exists) |
| R2b  | PASS  | PASS          | guard-regression (path.exists) |

Phase-3 must keep R2a/R2b passing — an unguarded _git("add", ...) on a
missing path regresses those.

## Ambiguity resolved (no RAISE_ISSUE)

Intent.md references commit_phase_handoff(phase=1, state=...) and
_slice_id(state); authoritative signatures are
commit_phase_handoff(phase, summary, commit_hash) and _slice_id() (no
arg — reads SLICE_YAML). Tests use the real signatures.

## Invariants touched by the test surface

- INV-008 DC-4: _git is stubbed so no commits emit; DC-4 drift not
  testable here. Slice E owns the single-commit-site guard.
- INV-003: tests target orchestrator staging only; phase-1-writer
  agent contract unchanged.
