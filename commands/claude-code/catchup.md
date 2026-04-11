# Catchup — Orient a New Session

Pick up where the last session left off without flooding the session with eager reads.

Usage: `/catchup` (auto-detect) or `/catchup phase 2|3|4` (enter specific pipeline phase)

## Why This Exists

Every new session starts with zero context. Without orientation, you waste time rediscovering what was already known, or worse — you make different assumptions than the last session and silently diverge. The naive fix is to read every file mentioned in the handoff note up front — which pushes a fresh session to ~47k tokens before the user has asked for anything.

ADR-002 (context discipline protocol) replaces eager reads with a tiered model: a strictly bounded Tier 1 pass orients, a Tier 2 subagent (if dispatched at all) answers specific questions with a small return, and Tier 3 is simply the absence of catchup — once the user gives a direct imperative, normal file reading resumes.

## Tier 1 — Strictly Bounded

**Always runs. Reads ONLY these five items:**

- `.claude/handoff.md`
- `.claude/current-slice/slice.yaml`
- `.claude/sweep.yaml`
- `git log --oneline -5`
- `git status --short`

Nothing else is loaded at this tier. No `CLAUDE.md` rereads, no `docs/ARCHITECTURE.md`, no source files, no test files, no ADRs. Produce the orientation summary from these five inputs and **STOP**. Any additional main-context file read means you have crossed into Tier 2 — and Tier 2 has admission criteria.

If `.claude/handoff.md` does not exist, this is a cold start. Still stay within Tier 1: report the cold-start state and ask the user what they want to work on rather than eagerly loading project docs.

### Tier 1 orientation template

```
## Session Catchup — <date>

<if handoff exists>
**Previous session**: <one line from handoff ## State>
**Unfinished**: <items from handoff ## Blocked / Pending>
</if>

**Git**: branch `<name>`, last commit "<msg>", <N> uncommitted files
**Slice**: <active slice info or "no active slice">
**Mode**: <Pipeline Phase N | Continuing work | Fresh start>

**Next step**: <what the handoff ## Next line says, or ask the user>
```

That is the entirety of Tier 1 output. No analysis, no speculation, no "I noticed that…".

## Tier 2 — Dispatched via Subagent, Under Admission Criteria

Tier 2 exists to answer a *specific* question about repo state that Tier 1 data could not answer, or to load a phase's declared inputs when the user has given explicit direction to enter that phase. Tier 2 always runs via a subagent — never by reading files into the main session context. The subagent reads the files, answers the question, and returns a bounded summary.

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

When none of the dispatch conditions hold, do not invent one. Tier 1 plus the user's next message is almost always enough; eagerness here is what caused the 47k baseline this protocol exists to fix.

### Subagent contract block

When Tier 2 is dispatched, brief the subagent with exactly this contract:

```
CONTEXT: <one sentence naming the slice/session state from Tier 1>
QUESTION: <the specific question Tier 2 is being dispatched to answer>
FILES AVAILABLE: <the exact list of files the subagent may read; cap at 5>
YOUR BEHAVIOR: Read only the files listed. Do not expand the file list. Do
  not read transitively via grep or imports. Do not load ADRs, architecture
  docs, or source beyond what is named above unless the question cannot be
  answered without them — and then name the extra file before reading it.
YOUR RETURN: ≤200 words, structured as (1) direct answer, (2) the single
  most load-bearing file:line citation that supports the answer, (3) any
  unresolved ambiguity. No narrative, no summaries of what you read.
DO NOT return: a summary of the repo, a list of every file you opened,
  reflective prose, or advice about what to do next. Answer the question.
```

The 200-word cap is the load-bearing constraint. A subagent that dumps everything it read back into the main context defeats the ~100× savings Tier 2 is supposed to buy. If a legitimate answer genuinely does not fit in 200 words, that is a signal to split the question into two Tier 2 dispatches, not to raise the cap.

## Tier 3 — The Absence of Catchup

Once the user gives a direct work imperative ("fix the bug in X", "rewrite Y", "add Z"), catchup is over. Normal file reading resumes under whatever skill governs the work at hand. There is no Tier 3 bookkeeping — it is simply the boundary past which this skill is no longer running.

If you find yourself still "orienting" after the user has given a direct imperative, that is drift. Stop catching up and start the work.

## Routing modes

The Tier model above describes *how much* you are allowed to load at any point in catchup. The routing modes below describe *which kind* of session you are resuming. Every mode starts at Tier 1; only Mode A unconditionally crosses into Tier 2 (and it does so via subagent, like all Tier 2 dispatches).

### Mode A — Pipeline phase entry (dispatches Tier 2 for declared inputs)

When `/catchup phase N` is used and the handoff pointers explicitly list files for Phase N, dispatch a Tier 2 subagent (Tier 2 condition 2 above) with a contract that loads ONLY the declared inputs for the target phase. The subagent returns a ≤200-word role surface report; it does not dump the files into main context.

**Phase 1 (Intent):**
- Subagent loads: `docs/ARCHITECTURE.md`, `docs/adr/index.md`
- Greenfield slices: exclude source code. Modification slices: also load public interfaces of envelope files (signatures, class defs, docstrings). Exclude internal implementation logic.

**Phase 2 (Validation):**
- Subagent loads: `.claude/current-slice/intent.md`, `docs/ARCHITECTURE.md`, relevant ADRs from intent's `adrs-referenced` field
- Excludes: source code, any implementation ideas, Phase 1's reasoning

**Phase 3 (Implementation):**
- Subagent loads: `.claude/current-slice/intent.md`, test files from the validation phase
- Excludes: Phase 2's `approach.md` or reasoning about why tests are shaped the way they are

**Phase 4 (Integration):**
- Subagent loads: `.claude/current-slice/intent.md`, `docs/ARCHITECTURE.md`, the implementation (source files in envelope)
- Excludes: Phase 3's `implementation/notes.md` — check the code, not the reasoning

Before finalising the orientation report, read `docs/operational-reference.md § Phase Skill Guide` and surface the target phase's **role name**, **primary anti-behavior**, **secondary anti-behaviors**, and **primary + supporting skills**. This surfacing is the ADR-004 D4 commitment: roles and skills are echoed at every phase entry. For Phase 1 specifically, the primary-skills column is an em-dash (no primary fit) — still print the row so the operator sees the explicit absence rather than inferring a missing assignment. The Phase Skill Guide is a living registry; if an entry looks stale, the registry is the source to update, not this skill.

### Mode B — Continuing non-slice work

If the handoff note describes non-slice work (bug fix, research, architecture discussion), stay in Tier 1 unless the user's direct imperative demands Tier 2. Load whatever the work itself needs under normal skill governance — at that point catchup has exited into Tier 3 and this skill is no longer running.

### Mode C — Fresh start (no handoff, no slice)

Stay in Tier 1. Report the cold-start state and ask the user what they want to work on. Do not pre-emptively read `CLAUDE.md`, `docs/ARCHITECTURE.md`, or ADR indexes — that is Tier 2 territory and none of the admission conditions hold yet.

### Mode D — Dirty recovery (slice active + uncommitted changes + no recent handoff)

If a slice is active AND `git status` shows uncommitted changes AND the handoff note is missing or clearly stale:

1. Report the dirty state clearly:
   > **Recovery mode**: Slice <ID> is active at phase <status>, but there are uncommitted changes and no matching handoff note. The previous session likely ended without `/handoff`.
2. List the uncommitted changes and ask the user to confirm they are from the active slice
3. If confirmed: proceed as Mode A for the current phase, treating the uncommitted changes as in-progress work
4. If the user says the changes are stale: suggest `git stash` to preserve them, then proceed normally

Dirty recovery still obeys the Tier 1 / Tier 2 boundary — do not eagerly read the uncommitted files into main context. If verification is needed, dispatch Tier 2.

## What Tier 1 reports must make visible

Every orientation report must make the isolation visible: state Mode, say what was Loaded (for Tier 1, that is always the five-item read list), and — when a phase entry dispatches Tier 2 — say what was deliberately Excluded. Neither the agent nor the user should accidentally load extra context when the isolation is deliberate.
