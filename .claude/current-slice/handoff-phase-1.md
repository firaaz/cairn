# SLICE-001 Phase 1 Handoff — validator-symlink-fix

## What Phase 1 Produced

`.claude/current-slice/intent.md` — the canonical spec for the slice. Contains:

- **YAML envelope**: `scripts/validate_architecture.py`, `tests/unit/test_validate_architecture.py`, `CHANGELOG.md`
- **Core invariant**: "The validator never silently reads a project whose root the caller did not intend."
- **Four calling contexts** the fix must handle: cairn self-dogfood, consumer via symlink with env var, consumer via symlink without env var, consumer from subdirectory.
- **Six verification scenarios** (V1-V6) plus an integration regression check (V7 for Phase 4).
- **Deliberate mechanism-agnosticism** in the non-binding guidance section — Phase 3 chooses the specific resolution mechanism; the intent commits only to observable behavior.

## Phase Gate

**Met.** intent.md committed to git as `b1c4764` on branch `dev`.

Verification command: `git log --oneline -- .claude/current-slice/intent.md` returns at least one line.

## Ambiguities Phase 2 Should Resolve

### A1 — V6 diagnostic wording is over-specified for some implementation choices

V6 as written says the validator must "write a diagnostic message to stderr that explains which resolution mechanisms were attempted and why none succeeded." This wording presupposes a chain of resolution mechanisms. If Phase 3 chooses a single-mechanism implementation (see A3 below for a candidate), there's nothing to "chain" and the diagnostic becomes a simpler "docs/ARCHITECTURE.md not found at <resolved path>" message.

**Phase 2 should test the property, not the wording.** The property is: *"Under no resolution-failure condition does the validator silently read a project whose root the caller did not intend."* The existing exit-code-2 "missing required files" path already satisfies this property regardless of which mechanism computed the (wrong) root — if the resolved path has no `docs/ARCHITECTURE.md`, the validator exits 2 with an existing diagnostic. Phase 2 should write the V6 test around "validator exits 2 when resolved root has no valid substrate" rather than "diagnostic string matches regex X."

### A2 — "Broken state" test (V5) needs a distinct fixture from the happy-path test (V2)

V2 uses a happy-path consumer fixture (invariant + matching ADR). V5 uses a broken fixture (invariant referencing a nonexistent ADR). These are separate temp directories to avoid mutation between tests. Phase 2 should use independent `tempfile.TemporaryDirectory()` scopes or pytest fixtures with function-scoped lifetimes.

### A3 — External review provides an independent analysis and a candidate fix

The working tree contains an untracked document: `docs/2026-04-11-review-from-rag-session.md`. It is a methodology review from a real consuming project (`complex-rag-analysis` session 15) that independently diagnosed the same bug this slice fixes. **This document predates the slice and is external evidence, not Phase 1 reasoning** — Phase 2 is free to load it without compromising context isolation. The phase-2 agent should decide case-by-case whether external analyses count as declared inputs; flagging here so the choice is conscious.

The review's **Finding 1 Option 1** proposes a minimal fix: replace `Path(__file__).resolve().parent.parent` with `Path(__file__).parent.parent` — drop `.resolve()`. Rationale: Python's `__file__` reflects the invocation path (symlink-preserving), and `Path.parent` is pure string manipulation (no canonicalization). When invoked via `<host>/.slice-system/scripts/...`, `parent.parent` yields `<host>`. When invoked via `<cairn>/scripts/...`, it yields `<cairn>`. Both cases correct.

**Implication for Phase 2 test design**: whichever mechanism Phase 3 adopts, the V2-V4 happy-path tests should verify the observable behavior (validator reads correct substrate under each calling context) without binding to a specific mechanism. The tests must pass whether Phase 3 implements the handoff-suggested chain (env → git → fallback) or the review's single-operation fix, or anything else that satisfies the spec.

### A4 — CHANGELOG.md is in the envelope but should not be touched by Phase 2

The envelope lists `CHANGELOG.md` so Phase 3 can move the [Unreleased] § Known issues entry into [Unreleased] § Fixed when the implementation lands. Phase 2 should **not** touch CHANGELOG.md — it is a Phase 3 write. If a Phase 2 test needs to check CHANGELOG state, that is a regression to flag (the test shouldn't need it).

## Scope Reminder

Phase 2's only output is `tests/unit/test_validate_architecture.py` plus a brief `.claude/current-slice/validation/approach.md`. No modifications to `scripts/validate_architecture.py`. No touching `CHANGELOG.md`. Do not expand the envelope without an explicit `EXPAND_ENVELOPE=1` logged event.

## Context Isolation Note

Phase 2 should load:
- `.claude/current-slice/intent.md` (primary spec)
- `docs/ARCHITECTURE.md` (for invariant context, even though intent declares none touched)
- `docs/adr/001-bootstrap-exception.md` (referenced in intent)
- **Optional**: `docs/2026-04-11-review-from-rag-session.md` (external input, see A3)

Phase 2 should NOT load:
- `scripts/validate_architecture.py` internals (only its top-level docstring and line 22 if needed for the bug being tested — this is a modification slice targeting exactly one line)
- `CLAUDE.md` (not a phase-2 declared input; would leak project orientation into test design)
- This handoff file's reasoning sections (read the artifacts themselves, not the commentary)
