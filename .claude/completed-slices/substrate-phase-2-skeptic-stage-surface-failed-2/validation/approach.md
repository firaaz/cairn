# Phase 2 approach — substrate/phase-2-skeptic-stage-surface (re-dispatch)

## Contract under test

`commit_phase_handoff(phase, summary, commit_hash)` — when `phase == 2`,
the Phase-2 boundary commit must additionally stage every `tests/unit/`
path appearing in `git diff --name-only <phase-1-boundary> -- tests/unit/`
that still exists on disk, alongside the existing `handoff-phase-2.md`
stage. One commit only (DC-4); empty diff → no extra adds (DC-3).

## Test surface (4 cases, RED/guard split)

- **R1** single slug-named test file → staged.
- **R2** three mixed-naming files (one deliberately non-slug-named) → all
  staged. Pins diff-based discovery against any glob-by-slug regression.
- **R3** zero test files → no `tests/unit/` adds, only `handoff-phase-2.md`.
  Contract-guard against unconditional/sentinel staging; preserves commit
  shape under empty diff.
- **R4** one test file + modified `handoff-phase-2.md` → both stage in a
  single Phase-2 commit (`commit_calls <= 1`). Preserves the existing
  handoff-md stage; widens content not count.

## Ambiguity resolutions (recorded inline in the test docstring)

1. Public signature is `(phase, summary, commit_hash)` — verified via the
   companion `test_commit_phase_handoff_stage_surface.py` and
   `slice_orchestrator.__init__.py` re-exports.
2. Phase-1 boundary SHA resolution mechanism is **not** pinned by these
   tests. The fake `_git` returns `"deadbee0\n"` for `log`/`rev-parse` and
   the configured path list for `diff`, so any resolution path the
   implementer chose remains contract-compatible. `_git_stdout` already
   normalises `CompletedProcess` and `str` returns (lifecycle.py:192).
3. Test fixture matches the existing `_patched_so` convention used by
   `test_commit_phase_handoff_stage_surface.py` — same `monkeypatch.chdir`
   + `SLICE_YAML` rebinding pattern; identical `_adds()` collector handles
   both `_git("add", path)` and `_git("add", "-f", path)` shapes.

## Self-application result

All 4 cases pass against HEAD (in-tree fix at ae9e6c8). Phase 3 expectation
is verification-only: no implementation widening required. The bisect
anchor will be satisfied when the Phase-2 boundary commit on this slice
naturally stages this very test file via the diff-discovery branch.
