---
slice: SLICE-013
phase: 2-validation
framing: C (documented baseline + frozen pre-slice evidence)
---

# Validation Approach — SLICE-013 (ruff-cleanup)

## Framing decision

SLICE-013 is a behavior-preserving lint cleanup. The TDD RED step has no behavioral target — DoD item 2 (`intent.md:66`) requires "same set of test outcomes as before the slice," so authoring a new test that currently fails for behavioral reasons is impossible by construction.

Rather than force a synthetic behavioral RED or silently skip the RED step, this slice adopts **framing C**: document the validation surface in this file, and freeze pre-slice evidence transcripts as the literal RED artifact. The lint errors are the failing state; the existing passing test suite is the invariant Phase 3 must preserve.

**This is precedent-setting.** SLICE-013 is the first explicit cleanup-shaped slice in cairn (`intent.md:25`). Future cleanup slices that clear D3 bypass debt, fix formatting drift, or retire deprecated APIs without behavior change should use this same framing unless a later slice formalises a different convention.

## Validation surface

Two properties must hold at Phase 4:

1. **Lint property (primary target of the slice).** `ruff check tests/unit/test_feature_cross_index.py tests/unit/test_invariant_assertions.py` exits 0 with zero errors. The pre-slice state (frozen in `pre-slice-ruff.txt`) exits 1 with exactly three errors: two E741 at `test_feature_cross_index.py:88,95` and one E402 at `test_invariant_assertions.py:1114`.

2. **Behavioral invariant (must NOT change).** `python3 -m pytest tests/unit/test_feature_cross_index.py tests/unit/test_invariant_assertions.py` exits 0 with exactly the same outcome set as pre-slice: 58 passed, 0 failed, 0 skipped. The pre-slice transcript is frozen in `pre-slice-pytest.txt`.

Phase 4 re-runs both commands. The lint property flipping from exit 1 → exit 0 is the GREEN transition. The behavioral invariant holding unchanged (58/58, same test names, same collection count) is the preservation check.

## RED evidence

- `pre-slice-ruff.txt` — verbatim transcript of `ruff check` against the two envelope files, showing exit 1 and the three enumerated errors. This is the RED state for the lint property. Phase 3 makes this transcript no longer reproducible.
- `pre-slice-pytest.txt` — verbatim transcript of `pytest` against the two envelope files, showing exit 0 and 58 passed. This is the invariant baseline. Phase 3 must reproduce this exactly (modulo runtime seconds).

No new test code is added. Authoring a test that asserts `ruff check … exits 0` would merely duplicate what `integration_gate.py` Step 4a already enforces repo-wide on every slice; the redundancy buys no additional coverage.

## Ambiguity enumeration (Skeptic pass)

Each ambiguity either resolves via intent.md, ARCHITECTURE.md, or an ADR — or is escalated. None required escalation beyond the framing decision above.

1. **Exact line targets.** `intent.md:29-49` enumerates the three edits literally, with before/after snippets for edits 1 and 2 and explicit line-range instructions for edit 3 (delete 1112-1114, insert after line 29 before `# --- Fixtures ---` at line 32). Resolved in intent.

2. **E402 fix mechanism.** Multiple paths could clear E402: `# noqa`, file split, relocate import, or ruff config exception. `intent.md:48` and the envelope's `out-of-scope` clause explicitly forbid `# noqa` suppression, and `handoff-phase-1.md:15` records "relocate import to top of file" as the pre-resolved approach. Resolved.

3. **Comment handling for edit 3.** `intent.md:49` specifies that the leading comment `# Import validator functions directly for parsing tests` is dropped when the import block moves up (only two code lines relocate, no comment). Resolved.

4. **Section comment `# === SLICE-011: ...`.** `intent.md:49` states the section comment at line 1105 stays in place. Only the import lines move. Resolved.

5. **Blank-line surround.** `intent.md:48` requires a blank line above and below the inserted import block at its new location. Resolved.

6. **No-RED framing.** Escalated and resolved via framing C (above). Operator confirmed 2026-04-15.

7. **`.claude/d3-bypasses.log` editing.** Out-of-scope (`intent.md:15`). The rolling-window count decays naturally; the log is append-only and not touched by this slice. Resolved.

8. **Production code.** Out-of-scope (`intent.md:58`). `validate_architecture.py` is not modified even though its symbols are imported by the relocated block — only the import location moves. Resolved.

## Phase 3 entry contract

Phase 3 (Implementer) receives exactly two inputs: `intent.md` (specification) and the two frozen transcripts in this directory (validation surface). Phase 3 does NOT read this `approach.md` file beyond this contract section — the framing rationale is Skeptic's work and must not influence Implementer's choices beyond what intent.md already binds.

Phase 3 success criterion: after the three enumerated edits, re-running the two commands in "Validation surface" above produces (1) ruff exit 0, zero errors, and (2) pytest exit 0, 58 passed, 0 failed, 0 skipped.

## Phase 4 evidence requirements

At integration, the slice-close check must produce:

- Post-slice `ruff check` transcript showing exit 0, zero errors (diff against `pre-slice-ruff.txt`).
- Post-slice `pytest` transcript showing exit 0, 58 passed, 0 failed, 0 skipped (diff against `pre-slice-pytest.txt` shows only the runtime-seconds line differs).
- `git diff` against the pre-slice baseline confined to the two envelope files plus `.claude/current-slice/` artifacts (DoD item 5).
- Snapshot diff reports no out-of-envelope changes (DoD item 4).
- No new entries appended to `.claude/d3-bypasses.log` during slice-close (DoD item 6).
