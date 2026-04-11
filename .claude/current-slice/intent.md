---
slice: handoff-catchup-protocol-rewrite
date: 2026-04-11
phase: 1-intent
invariants-touched: [INV-002]
adrs-referenced: [ADR-002]
envelope:
  - "commands/claude-code/handoff.md"
  - "commands/claude-code/catchup.md"
  - "commands/claude-code/start-slice.md"
  - "templates/handoff.md"
  - ".claude/learning.md"
  - "docs/operational-reference.md"
  - "tests/unit/test_context_discipline_protocol.py"
out-of-scope:
  - "Self-learn automation at /handoff (invocation of claude-md-management skills) — SLICE-003"
  - "3× promotion rule and learning.md threshold review — SLICE-003"
  - "Any change to the four-phase pipeline shape"
  - "scope-guard.sh and reversibility-guard.sh internals"
  - "CLAUDE.md edits — D1 startup floor cuts already shipped"
  - "SessionStart hook override for superpowers — D1.2, deferred"
  - "docs/spec-v1.md edits beyond cross-references"
  - "Consumer-project rollout (consumers inherit via `.slice-system → .` symlink)"
---

# Intent: SLICE-002 — Rewrite handoff and catchup protocols for context discipline

## What and Why

Measured across 10 recent cairn and consumer sessions, a freshly-oriented session sits at ~47k tokens on turn 1 — well past the ~30–40k sweet spot — because `/handoff` writes a ~3k-token narrative and `/catchup` eagerly reads every file its instructions mention. Root cause is not size bloat; it is a design mismatch where handoffs carry reflective prose (smuggling mental state across the role-reset boundary) and catchup reads into main context where a subagent dispatch would cost ~100× less. Full baseline and analysis in `docs/plans/2026-04-11-context-discipline-design.md`.

This slice implements **ADR-002 / INV-002** — the context-discipline protocol committed in `docs/adr/002-context-discipline-protocol.md`. ADR-002 codifies the three load-bearing layers as an architectural commitment; this slice delivers their working form by rewriting the handoff and catchup skill templates, the slice-closure step in `/start-slice`, and the operational reference so that the commitment is enforced in the tooling agents actually use. The three layers, verbatim from ADR-002: (1) handoffs are pointers with annotations, not narratives, (2) catchup runs a minimal Tier 1 pass and dispatches Tier 2 only under explicit admission criteria, (3) slice closure wipes `.claude/current-slice/` so the next slice inherits no residue. Expected result: post-catchup context drops from ~47k → ~28–30k tokens per session, a ~10–18k saving.

## Specification Detail

### 1. Handoff format contract (`templates/handoff.md`)

New file. Imperative/declarative voice only. **Token budget: 150–400** (hard upper bound, soft lower bound). Shape:

```
---
slice: <SLICE-id or "none">
phase: <1-intent | 2-validation | 3-implementation | 4-integration | complete | n/a>
branch: <branch-name>
as-of: <YYYY-MM-DD commit-sha>
---

## State
<1–2 present-tense sentences. Current state, not history.>

## Next
<One imperative. One line. Specific.>

## Blocked / Pending
- <short item> → <pointer>
  (max 5 lines, each a one-liner + pointer, no rationale)

## Pointers
- `path/to/file.md` — what's there + when to read it
```

### 2. Banned sections (contractual)

The rewritten `commands/claude-code/handoff.md` skill template MUST NOT instruct the agent to produce any of these sections, and must not contain them as examples of the target output:

- "What This Session Was About"
- "What Was Accomplished"
- "Surprises or Discoveries"
- "Self-Check" (or "Self Check")
- Narrative paragraphs of reasoning
- Test run output or pass/fail tallies

These belong elsewhere: commit messages, `git log`, ADRs, or `docs/lessons.md`. The handoff carries state + next step, not reflection.

### 3. Catchup tier model (`commands/claude-code/catchup.md`)

The skill template must enforce three tiers with explicit admission criteria.

**Tier 1 — always runs, strictly bounded.** Reads ONLY:
- `.claude/handoff.md`
- `.claude/current-slice/slice.yaml` (if present)
- `.claude/sweep.yaml` (if present)
- `git log --oneline -5`
- `git status --short`

Produces the orientation summary. STOPS. No additional main-context file reads without crossing into Tier 2.

**Tier 2 — dispatched via subagent.** The skill template must contain this admission-criteria block verbatim (Phase 2 will grep for it as a literal substring):

```
DISPATCH Tier 2 subagent if and only if:
  1. User asked a specific factual question that Tier 1 data did not answer, OR
  2. User directed entry into a specific pipeline phase and the handoff pointers
     explicitly list files for that phase, OR
  3. You are about to take an action that requires verifying the current state
     of a specific file, AND that file is named in the handoff pointers.

DO NOT DISPATCH Tier 2 if:
  - You are orienting "just in case"
  - Tier 1 data sufficed to answer the user
  - The user has not given you a concrete direction
  - You want to "be thorough"
```

The skill template must also contain a subagent contract block with (at minimum) the literal keys `CONTEXT:`, `QUESTION:`, `FILES AVAILABLE:`, `YOUR BEHAVIOR:`, `YOUR RETURN`, and `DO NOT return:`. The contract caps the subagent return at ~200 words/tokens regardless of underlying file size.

**Tier 3 — end of catchup.** The skill template must state that once the user gives a direct work imperative, catchup is over and normal file reading is appropriate. No bookkeeping needed for Tier 3 — it is the absence of catchup, not a third protocol step.

### 4. Slice closure wipes `.claude/current-slice/` (`commands/claude-code/start-slice.md`)

The `/start-slice` skill's Step 7 (Complete a Slice) must, after committing the final slice state, remove every file under `.claude/current-slice/`. The commit that carries the `status: complete` update IS the git-history record of the slice — nothing else is preserved. Acceptable implementations:

- The completion commit itself stages the removals alongside the status update (one commit, cleanest).
- A separate close commit immediately follows the completion commit.

No file under `.claude/current-slice/` may survive the close sequence. There is **no archive directory** — the string `.claude/archive/` must not appear anywhere in the rewritten skill template (git history + `.claude/learning.md` cover the post-mortem case).

Failed-slice recovery (Step 8) is out of scope for this slice; its existing `.claude/completed-slices/` path remains, because the failure case preserves debugging context that the normal close does not need.

### 5. Learning staging ground (`.claude/learning.md`)

Slice #2 creates this file, empty except for a short header:

```
# Session Learning Staging Ground

Append-only. Free-form entries captured at session end. Promotion to CLAUDE.md happens via the 3× rule in a later slice.
```

File size at close of Slice #2: < 500 bytes. Slice #2 does not wire any skill to write to this file — that is SLICE-003.

### 6. Operational reference update (`docs/operational-reference.md`)

Add a new top-level section titled exactly `## Context Discipline Protocol`, placed after `## Session Handoff Protocol`. The new section must document, in operational terms:

- The 150–400 token handoff budget and pointer-not-payload rule
- The banned-sections list (at least the four literal phrases from §2)
- The Tier 1 / Tier 2 / Tier 3 catchup model, including the Tier 1 read list and the Tier 2 admission criteria
- The subagent contract template (may reference the canonical copy in `catchup.md` rather than duplicating)
- The wipe-on-close rule for `.claude/current-slice/`
- The existence of `.claude/learning.md` as a staging ground, with automation explicitly marked "deferred to SLICE-003"

The existing `## Session Handoff Protocol` section must either be merged into the new section or rewritten to cross-reference it. No section in `operational-reference.md` may describe the handoff as a narrative artifact after this slice lands.

## Boundary

Already listed in the YAML `out-of-scope` block. Reiterating the non-obvious items:

- **No handoff automation.** `commands/claude-code/handoff.md` after this slice still ends by telling the user "run `/catchup` next session" — it does NOT invoke `claude-md-management` skills. SLICE-003 adds that.
- **No 3× rule, no promotion review, no threshold logic.** SLICE-003.
- **No edits to `.claude/handoff.md` content format in consumer projects.** Consumers pick up the new format by re-running `/handoff` against the new skill template.
- **No changes to hook behavior.** `scope-guard.sh`, `reversibility-guard.sh`, `reality-check.sh` are untouched.
- **No new ADR written during this slice.** ADR-002 was authored as a pre-slice step before Phase 1 began (see "Decision points" in the Phase 1 session transcript and `docs/adr/002-context-discipline-protocol.md`). If Phase 2 or Phase 3 surfaces a protocol commitment not already captured in ADR-002, the mid-slice ADR-creation path in `docs/operational-reference.md` §"ADR Rules During a Slice" applies.

## Verification

Phase 2 writes `tests/unit/test_context_discipline_protocol.py`. Each assertion below must have a concrete, runnable test. Tests are file-content and structure checks — no runtime behavior to exercise.

### V1. Handoff template exists and is tight
- `templates/handoff.md` is a regular file.
- `len(read_text()) <= 2000` (approximates ≤400 tokens, per 5 chars/token).
- Frontmatter block contains keys `slice`, `phase`, `branch`, `as-of`.
- Body contains the four section headers: `## State`, `## Next`, `## Blocked / Pending`, `## Pointers`.

### V2. Handoff skill template is free of the old narrative format
- `commands/claude-code/handoff.md` contains NONE of these literal substrings (case-insensitive): `What This Session Was About`, `What Was Accomplished`, `Surprises or Discoveries`, `Self-Check`, `Self Check`.
- It references `templates/handoff.md` as the target format.
- It explicitly states the 150–400 token budget (the literal substring `150` and `400` both appear within 100 characters of the word `token`).

### V3. Catchup skill template encodes the tier model
- `commands/claude-code/catchup.md` contains headers or labeled blocks for `Tier 1`, `Tier 2`, and `Tier 3`.
- It contains the literal substring `DISPATCH Tier 2 subagent if and only if:` exactly as written in §3 of this intent.
- It contains a subagent contract block in which all of these literal keys appear: `CONTEXT:`, `QUESTION:`, `FILES AVAILABLE:`, `YOUR BEHAVIOR:`, `YOUR RETURN`, `DO NOT return:`.
- Tier 1's read list explicitly enumerates all five items: `.claude/handoff.md`, `.claude/current-slice/slice.yaml`, `.claude/sweep.yaml`, `git log --oneline -5`, `git status --short`.

### V4. Start-slice closure wipes current-slice
- `commands/claude-code/start-slice.md` Step 7 (Complete a Slice) contains an instruction to remove or wipe all files under `.claude/current-slice/` (one of: `wipe`, `rm -r`, `git rm`, `remove`, `delete`) within 300 characters of the literal `.claude/current-slice`.
- The literal substring `.claude/archive/` does NOT appear in `commands/claude-code/start-slice.md`.
- Failed-slice recovery (Step 8) is unchanged — it still moves to `.claude/completed-slices/<ID>-failed/`. (Phase 2 asserts this has not been refactored.)

### V5. Learning staging ground exists and is minimal
- `.claude/learning.md` is a regular file.
- First non-blank line is exactly `# Session Learning Staging Ground`.
- File size < 500 bytes.

### V6. Operational reference documents the new protocol
- `docs/operational-reference.md` contains the literal header `## Context Discipline Protocol`.
- That section (from its header to the next `## ` header or EOF) contains all of: `150`, `400`, `Tier 1`, `Tier 2`, `DISPATCH`, `wipe` or `remove`, `learning.md`, `SLICE-003`.
- The existing `## Session Handoff Protocol` section either no longer exists or contains a cross-reference (markdown link or literal phrase `Context Discipline Protocol`) to the new section.

### V7. No stale narrative-format residue anywhere under `commands/` or `templates/`
- Grep across `commands/` and `templates/`: literal phrases `Surprises or Discoveries` and `What This Session Was About` appear 0 times.

All seven tests are required for the phase gate from Phase 2 to Phase 3.
