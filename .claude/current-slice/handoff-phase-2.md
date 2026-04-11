# SLICE-001 Phase 2 Handoff — validator-symlink-fix

## What Phase 2 Produced

Pytest validation suite at `tests/unit/test_validate_architecture.py` covering intent V1-V6, plus `.claude/current-slice/validation/approach.md` (Phase 2 reasoning trace — not a Phase 3 input).

## Phase Gate

**Met.** Tests committed to git on branch `dev`.

Verification command: `git log --oneline -- tests/unit/test_validate_architecture.py` returns at least one line.

## Initial Test State (on the current, unfixed validator)

Running the suite against `scripts/validate_architecture.py` at its current state produces **1 passed, 5 failed** in ~0.4s:

- **V1 — `test_v1_cairn_self_dogfood_baseline`**: GREEN. Cairn's self-validation is already correct. The fix must not regress it.
- **V2 — `test_v2_consumer_via_symlink_with_env_var`**: RED (`Invariants verified: 1` leak).
- **V3 — `test_v3_consumer_via_symlink_no_env_var`**: RED (`Invariants verified: 1` leak).
- **V4 — `test_v4_consumer_invoked_from_subdirectory`**: RED (`Invariants verified: 1` leak).
- **V5 — `test_v5_consumer_with_broken_substrate`**: RED (validator returns exit 0 + ALL CHECKS PASSED, reading cairn's consistent substrate instead of the broken tmp fixture).
- **V6 — `test_v6_resolution_failure_no_viable_root`**: RED (same false-green pathology as V5).

Every red failure has the same root cause: `Path(__file__).resolve().parent.parent` canonicalizes the `.slice-system` symlink back to cairn's install directory, so the validator reads cairn's 1-invariant/1-ADR substrate rather than the caller's intended target.

## Test Invocation

cairn has no `pyproject.toml`. Run the suite via uv's ephemeral tool runner:

```
uvx pytest tests/unit/test_validate_architecture.py -v
```

Phase 3 must observe the initial 1-passed/5-failed state before making any source change, then drive all 6 tests to green.

## Envelope Reminder

Declared envelope from `intent.md`:

- `scripts/validate_architecture.py` — the one source file Phase 3 modifies.
- `tests/unit/test_validate_architecture.py` — already committed by Phase 2. Phase 3 **must not edit the tests** to force green. If a test looks wrong, flag it and stop; do not patch around it.
- `CHANGELOG.md` — Phase 3 moves the `[Unreleased] § Known issues` entry for the symlink bug into `[Unreleased] § Fixed` with a reference to this slice.

Do not expand the envelope without setting `EXPAND_ENVELOPE=1` (which logs to `.claude/current-slice/envelope-expansions.log`).

## Free Parameters

The intent is mechanism-agnostic. Any resolution mechanism that drives V2-V6 to green without regressing V1 satisfies the spec. Two candidates surfaced during Phase 1 and Phase 2:

1. **Drop `.resolve()`**: change the module-load resolution to `Path(__file__).parent.parent`. One-character fix. `__file__` preserves the symlink-visible path; pure-string `.parent.parent` yields the directory containing `.slice-system/` when invoked via the symlink, and cairn's root when invoked directly.
2. **Env → git → fallback chain**: `$CLAUDE_PROJECT_DIR` → `git rev-parse --show-toplevel` → `Path(__file__).parent.parent`. Multi-mechanism; more code.

Phase 3 picks. Record the choice and reasoning in `.claude/current-slice/implementation/notes.md`. If a third mechanism emerges during implementation, use it and document the deviation.

**Non-negotiable**: no silent fallback that can read the wrong project's docs. V6 enforces this directly; if V6 passes, the property holds.

## Context Isolation — What Phase 3 Should NOT Load

- `.claude/current-slice/validation/approach.md` — Phase 2 reasoning trace. Loading it would leak test-shaping rationale into implementation.
- `.claude/current-slice/handoff-phase-1.md` — Phase 1→2 bridge. Phase 2 consumed it.
- `docs/2026-04-11-review-from-rag-session.md` — external review. Phase 2 loaded it to calibrate assertion design against captured output format; Phase 3 has the test suite itself as the contract and does not need the review's prose.
- `.claude/handoff.md` reasoning body — session-level orientation only.

## Open Items Outside This Slice

- `docs/2026-04-11-review-from-rag-session.md` remains untracked. Not Phase 3's concern. A future non-slice commit or documentation slice will decide its placement; Phase 3 should neither move it, commit it, nor reference it from `CHANGELOG.md`.
- Findings 2, 3, 4 from the external review remain queued as separate cairn concerns per the session 0 handoff. Not Phase 3's concern.
