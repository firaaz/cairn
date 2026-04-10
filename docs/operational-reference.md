# Development System

Operational quick reference for the slice-based development pipeline. **For the full theory, failure modes, empirical support, and adversarial review framing, see `docs/development-system-spec-v1.md`** — that document is the canonical spec. This file is the operational quick reference and should be loaded at the start of any slice.

A slice is a vertical feature cut that goes through four phases: Intent → Validation → Implementation → Integration. Each phase runs in a fresh session, takes a declared input artifact, and commits a declared output artifact. Phase transitions are enforced by git commits, not by session state.

## Routing: Decision vs. Slice

Before starting work, decide:

- **Touches invariants, boundaries, data ownership, or module structure** → run `/decision` first to produce an ADR. The ADR updates `docs/ARCHITECTURE.md`, then a slice implements it.
- **Implementation within existing boundaries** → go straight to `/start-slice`.

Rule of thumb: if the work could change what downstream slices can assume, it needs `/decision`. If it only fills in detail within an existing assumption, it needs `/start-slice`.

## The Four Phases

### Phase 1: Intent

**Input:** Task description + `docs/ARCHITECTURE.md` + relevant ADRs.
**Output:** `.claude/current-slice/intent.md`.

**Rules:**
- **Greenfield slices** (new modules): Do NOT read source code. Work from architecture docs only.
- **Modification slices** (changing existing behavior): Read only the public interfaces of files in the envelope (function signatures, class definitions, docstrings). Do NOT read internal implementation logic. *(No hook enforces this — discipline only. See spec-v1 §14 incident #4.)*
- Write `intent.md` with the four zones: YAML envelope, what/why/boundary, specification detail, verification.
- Declare which invariants and ADRs are touched.

**Exit gate:** `intent.md` committed to git.

### Phase 2: Validation

**Input:** `intent.md` only (+ `docs/ARCHITECTURE.md` and targeted ADRs if referenced).
**Output:** Test suite in `tests/` + `.claude/current-slice/validation/approach.md`.

**Rules:**
- The Phase 2 agent has NEVER seen how the implementation will work.
- Before writing tests, enumerate ambiguities in the intent. Resolve each by reference to `docs/ARCHITECTURE.md`/ADRs, or flag for human resolution.
- Write tests against the stated intent and specification details, NOT against hypothetical implementation.
- Tests must be runnable: pytest files, not pseudocode.

**Exit gate:** Validation suite committed to git.

### Phase 3: Implementation

**Input:** `intent.md` + the validation test files (NOT Phase 2's reasoning or `approach.md`).
**Output:** Code that passes the validation suite.

**Rules:**
- The implementing agent has never seen the reasoning behind the validation suite.
- Fast feedback runs continuously via the reality hook (`ruff format` + `ruff check` on every edit).
- Full test suite runs at logical-unit boundaries.
- Record decisions the intent didn't pin down in `.claude/current-slice/implementation/notes.md`.

**Exit gate:** All validation tests pass. Implementation committed to git.

### Phase 4: Slice Integration

**Input:** Implementation + `intent.md` + `docs/ARCHITECTURE.md` + invariants touched.
**Output:** Pass/fail on declared invariants, recorded in `.claude/current-slice/integration/sweep-notes.md`.

**Rules:**
- Run the full test suite (not just slice tests): `uv run python -m pytest`.
- Run the architecture validator: `uv run python scripts/validate_architecture.py`.
- Verify each declared invariant with `grep`/file evidence — assertions backed by what you actually found, not from memory.
- Check for regressions in adjacent code.

**Exit gate:** All tests pass, invariants verified, committed to git.

**Failure handling:** If Phase 4 fails because the implementation is wrong, mark the slice failed (`/start-slice failed`), archive it to `.claude/completed-slices/<ID>-failed/`, and start a new slice with the failure as input context. Do NOT patch the implementation to force Phase 4 to pass — that recreates the correlated-error problem the system is designed to prevent.

**Escape hatch:** If Phase 4 fails because an invariant is outdated (not because the implementation is wrong), write a new ADR superseding the old invariant, run `/refresh-architecture`, then re-run Phase 4.

## Context Isolation Rules

- Each phase starts fresh. No memory of previous phase's reasoning.
- Only the declared artifacts cross between phases.
- The intent document must stand alone — a reader with no other context should understand the slice from `intent.md` alone.
- Phase 1 must NOT read source code (greenfield) or must limit to public interfaces (modification).
- Phase 2 must NOT write code.
- Phase 3 must NOT expand scope beyond the envelope.

## Slice Directory Structure

```
.claude/current-slice/
  slice.yaml              # Metadata
  intent.md               # Phase 1 output
  validation/
    approach.md           # Phase 2 approach summary (tests live in tests/)
  implementation/
    notes.md              # Phase 3 deviation notes
  integration/
    sweep-notes.md        # Phase 4 observations
```

### slice.yaml Format

```yaml
id: SLICE-NNN
title: "Short description"
status: intent | validation | implementation | integration | complete | failed
started: YYYY-MM-DD
completed: null
invariants-touched: []
adrs-referenced: []
adrs-created: []
```

### intent.md Template

```yaml
slice: <short-name>
date: <YYYY-MM-DD>
phase: 1-intent
invariants-touched: []
adrs-referenced: []
envelope:
  - "src/path/to/*.py"
  - "tests/unit/path/to/test_*.py"
out-of-scope:
  - "description of what this slice does NOT touch"
```

```markdown
### What and Why
<What behavior change does this slice introduce? 2-3 sentences.>

### Specification Detail
<Protocol-level commitments: wire formats, key patterns, return shapes, error codes.>

### Verification
<Specific checks. Not "test it" — concrete assertions.>
```

## Phase Gate Enforcement

Phase transitions are enforced by git, not by session state:
- Phase 2 cannot start until `intent.md` is committed.
- Phase 3 cannot start until the validation suite is committed.
- Phase 4 cannot start until the implementation is committed.

The `/start-slice` skill checks for these artifacts in git history before advancing.

## Session Handoff Protocol

Every phase transition — and every session end — involves a handoff:

1. **At end of session:** Run `/handoff` (or `/handoff phase` for pipeline work). This commits artifacts, writes a handoff note to `.claude/handoff.md`, and updates slice status if applicable.
2. **Close the session.** For pipeline phases, this is not optional — the fresh context IS the external check.
3. **At start of next session:** Run `/catchup`. This reads the handoff note, loads phase-appropriate context, and enforces context isolation for pipeline work.

The handoff note (`.claude/handoff.md`) is overwritten each session. It represents current state, not history. Git provides the historical record.

For pipeline phases, `/catchup` loads ONLY the declared inputs for the target phase and explicitly reports what was excluded.

## Integration Sweep

Runs every N slices (cadence in `.claude/sweep.yaml`). Phase 4 provides per-slice integration; the sweep provides cross-slice integration.

**Sweep process:**
1. Load invariants from `docs/ARCHITECTURE.md`.
2. Enumerate possible cross-slice failure modes BEFORE checking.
3. Check each invariant against the current codebase with file:line evidence.
4. Run cross-module checks (imports, lint, types).
5. Produce a pass/fail summary.

If a sweep finds failures, create new slices to fix them through the normal 4-phase pipeline. Do NOT retroactively edit completed slices.

```yaml
# .claude/sweep.yaml
last-sweep-at-slice: 0
sweep-interval: 3
current-slice-number: 0
```

## ADR Rules During a Slice

If implementation requires violating an invariant:

1. STOP implementation.
2. Write a new ADR in `docs/adr/` with proper YAML frontmatter (`status: provisional`, `firmness: provisional`).
3. Update `docs/adr/index.md`.
4. Run `/refresh-architecture` to update `docs/ARCHITECTURE.md`.
5. Get explicit human approval before proceeding.
6. Record the new ADR in `slice.yaml` under `adrs-created`.

ADRs are append-only. Never edit an accepted ADR's body. To change a decision, write a new ADR that supersedes it.

## Scenario Verification

Before declaring any system component, skill, or slice complete, trace the primary user journey through it:

1. Write the sequence of concrete actions a user takes.
2. At every boundary (session, phase, handoff, artifact), verify the mechanism exists.
3. If the answer to "how does the user do this?" is "they'll figure it out" — that's a gap, not an answer.

Three levels:
- **Skill level:** Does invoking this skill handle every state it might encounter (no slice active, mid-slice, broken state)?
- **Slice level:** Can a user complete all 4 phases across separate sessions (entry, work, exit, re-entry)?
- **System level:** Does the full inventory of skills cover the full lifecycle (decide → create ADR → start slice → 4 phases → sweep → repeat)?

## Session Sizing

A phase fits if:
- The agent never has to ask itself what it was doing.
- The deliverable matches the opening statement.
- A fresh agent reading only the deliverable can understand what was done.

Soft target: under ~30K tokens loaded context, under ~10K tokens output per phase. Adjust based on experience.

## Hooks

Three hooks wired in `.claude/settings.json`:

- **`reversibility-guard.sh`** (PreToolUse on `Bash|Edit|Write`): blocks destructive ops (`rm -rf`, `git push --force`, `git reset --hard`, `git clean -fd`, `DROP TABLE`/`DROP DATABASE`), `.env*` writes, lock file writes; enforces ADR append-only.
- **`scope-guard.sh`** (PreToolUse on `Edit|Write`): blocks writes outside the current slice's `intent.md` envelope. Goes dormant when slice status is `complete` or `failed`. Override via `EXPAND_ENVELOPE=1` (logged to `.claude/current-slice/envelope-expansions.log`).
- **`reality-check.sh`** (PostToolUse on `Edit|Write`): runs `ruff format` and `ruff check --fix` on Python files.

Hooks are friction-plus-walls, not security boundaries. A determined or careless agent can route around the friction layer; the wall layer (the explicit patterns above) holds.
