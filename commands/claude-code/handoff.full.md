# Handoff — Full Reference

Close out a working session by writing a pointer, not a story.

Usage: `/handoff` (end of any session) or `/handoff phase` (end of a pipeline phase)

## Why This Exists

Every session accumulates context that is invisible to the next session. The naive fix is to write a long narrative — what happened, what was discovered, what to watch out for. That narrative smuggles mental state across a boundary the pipeline deliberately erected: the next session is supposed to load a *fresh* perspective on the artifacts, not inherit the previous session's framing. It also costs ~3k tokens per catchup, which the session then pays for every subsequent turn.

context-discipline-protocol (context discipline protocol) replaces the narrative with a bounded pointer. The handoff note is the team interface: it tells the next session where to look, not what to think.

## Target format

The output of this skill is a file at `.claude/handoff.md` that strictly follows `templates/handoff.md`. Read the template before writing the handoff — it is the source of truth for shape and tone. Do not invent new sections; do not expand any section into prose.

**Token budget: 150–400 tokens** (measured against the whole file including frontmatter). This is a hard upper bound and a soft lower bound. If you cannot say what you need inside 400 tokens, you are writing the wrong kind of artifact — commit messages, ADRs, and `docs/lessons.md` are where reflection goes.

Voice: imperative and declarative only. Present tense for state, imperative for the next action. No first person, no hedging, no "we", no "I", no "maybe".

## Step 1: Take Stock

1. Run `git status --short` to see uncommitted changes
2. Run `git log --oneline -3` to see recent commits
3. Check if `.claude/current-slice/slice.yaml` exists (determines whether we're in a slice)

If there are uncommitted changes, list them and ask whether to commit before handing off. Uncommitted work is the most common thing lost between sessions — surface it now rather than letting it rot.

## Step 2: Write the Handoff Note

**Before writing `slice.yaml` / `sweep.yaml` / `handoff.md`, Read the file first (CC 2.1.110+ requires Read before Write).**

Overwrite `.claude/handoff.md` with content that conforms to `templates/handoff.md`. The four body sections are fixed:

- **`## State`** — 1–2 present-tense sentences. Current state, not history. "identifier-scheme/doc-sweep Phase 3 complete at <sha>; sweep tests GREEN." Not "I finished implementing the seven envelope files and verified the tests pass."
- **`## Next`** — one imperative, one line, specific. "Run `/start-slice phase 4` to enter Integration." Not "continue the slice."
- **`## Blocked / Pending`** — up to five one-line items, each a pointer. No rationale. If something needs rationale, it belongs in a commit message or ADR.
- **`## Pointers`** — one line per file the next session should read, with a short note on *when* to read it. The body of the pointed-at file carries the detail; the handoff only indexes.

After writing, count the characters of the file. If it exceeds 2000 characters (the ~400 token budget), cut prose until it fits. Shrinking is almost always possible — narrative dressing, apologies, and "note that…" asides are the first things to go.

## Step 3: Banned shapes

The following sections and patterns MUST NOT appear in the handoff note. They are not a style preference — they are the failure mode this slice is closing:

- Reflective summaries of what the session did
- Pass/fail test tallies or test output
- Apologies, rationale, "I tried X but Y", or any first-person reasoning
- Paragraphs of discovery or surprise
- Inline explanation of *why* the next step is the next step — just state it

If you feel an urge to explain, that is a signal the explanation belongs in a commit message, an ADR, or `docs/lessons.md`. Put it there and leave the handoff alone.

## Step 3b: Cross-Feature Index

Per ADR `identifier-scheme` D8, the `## Features` section is a normative one-line-per-feature cross-feature index. Each active feature gets one line using the feature's `name:` where available (with `id:` as fallback) plus a short status phrase. Only the structural shape is normative — prose within each line is author judgment.

If any feature files exist under `.claude/features/`, write a `## Features` section in the handoff note. Worked example (ADR `identifier-scheme` D8):

```markdown
## Features
- identifier-scheme: template-updates Phase 2→3; rename sweeps queued
- housekeeping: inv004-rebaseline + stale-22k-cleanup complete
- v1-defense-d2: code-invariant-binding + assertion-block-migration queued
```

If no features are active, omit the section.

If decomposition changed during the session (slices added, reordered, or dropped), prompt the operator to update the feature file before finishing the handoff.

## Step 4: Slice-Specific Handling

If `.claude/current-slice/slice.yaml` exists and `$ARGUMENTS` includes "phase":

1. Read `slice.yaml` to get the current phase number and slice ID
2. Write a phase-specific handoff to `.claude/current-slice/handoff-phase-N.md` using the same `templates/handoff.md` shape and the same 150–400 token budget. The phase handoff carries only: the artifact produced, whether the phase gate is met, and any ambiguity the next phase must know. No reflection.
3. Update `slice.yaml` → `status` to the next phase name
4. Print the context isolation reminder:

> **Phase N complete.** Close this session now. In the next session, run `/catchup` — it will load only the artifacts the next phase is supposed to receive, preserving context isolation.

The reminder matters because continuing in the same session defeats the purpose of phase isolation. The next phase's value comes from a fresh perspective on the artifacts, without the reasoning that produced them.

## Step 5: Non-Slice Sessions

If there's no active slice (or `$ARGUMENTS` doesn't include "phase"), skip the slice-specific handling. The generic handoff note from Step 2 is sufficient.

Still suggest: "Run `/catchup` at the start of your next session to pick up where you left off."

## Step 6: Final Output

Print a concise summary for the user:

```
## Handoff Complete

**Handoff note**: .claude/handoff.md updated (<N> chars, within 2000-char budget)
<if slice> **Slice**: SLICE-NNN moved to phase N+1
<if slice> **Phase handoff**: .claude/current-slice/handoff-phase-N.md written

Next session: run `/catchup` to orient.
```

The one piece of telemetry worth printing is the byte count — it surfaces budget compliance without the user having to check manually. Everything else the user can read from git and the handoff file itself.

## Step 7: Run the Verifier

As the final step of every `/handoff` invocation, run `bash scripts/verify_handoff.sh`. This closes L-005 — the failure mode where `/handoff` exits claiming success while `slice.yaml.status`, the phase-commit handoff file, and the git log diverge from one another.

### Verifier contract

The verifier performs three checks and exits non-zero on the first failure. Each failure prints a stderr line that names the check, the expected state, the observed state, and the remediation command.

**Check (a) — status/commit alignment.** If the last commit subject is `phase-<N>: ...`, `.claude/current-slice/slice.yaml`'s `status:` field must reference phase `N` or `N+1` (or a terminal label like `complete`/`failed`). Divergence means `/handoff` updated the commit but not `slice.yaml`, or vice versa.

**Check (b) — phase handoff existence.** If the last commit subject is `phase-<N>: ...`, the file `.claude/current-slice/handoff-phase-<N>.md` must exist. This catches the case where the phase-commit was made without first writing the phase handoff note Step 4 requires.

**Check (c) — subject-prefix gate.** The last commit subject MUST begin with one of:
- `handoff:` (generic session-end handoff)
- `phase-<N>:` (pipeline phase-commit)
- `slice: <name> — complete` (slice-close commit, em-dash separator)

Any other prefix (`chore:`, `fix:`, `wip`, etc.) is a sign the handoff ran without the expected commit being made.

### Exit codes

| Exit code | Meaning |
|-----------|---------|
| `0` | All three checks pass. |
| `1` | A check failed. Stderr names the failing check and remediation. |
| `2` | Prerequisite missing (e.g., no commits in the repo yet). |

### Error shape

Stderr lines follow the pattern:

```
verify_handoff: check (<a|b|c>) FAILED — <one-line summary>
  <expected-state description>
  <observed-state description>
  remediation: <concrete command to fix>
```

Stdout is always empty; the verifier's contract is pass/fail via exit code plus stderr diagnostics.

### Failure modes the verifier catches

- `slice.yaml.status` reads `3-implementation` but the last commit is `phase-2: validation complete` — `/handoff` wrote the commit but forgot to update `status:`.
- Last commit is `phase-2: ...` but `.claude/current-slice/handoff-phase-2.md` does not exist — the phase handoff was never written.
- Last commit is `chore: bump version` — `/handoff` ran on a session where the operator committed something unrelated immediately prior, so the verifier flags the non-handoff commit as the tip.
