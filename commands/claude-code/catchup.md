# Catchup — Orient a New Session

Pick up where the last session left off, or orient from scratch.

Usage: `/catchup` (auto-detect) or `/catchup phase 2|3|4` (enter specific pipeline phase)

## Why This Exists

Every new session starts with zero context. Without orientation, you waste time rediscovering what was already known, or worse — you make different assumptions than the last session and silently diverge. This skill reads the handoff note from the previous session (if one exists) and loads the minimum context needed to be productive.

For pipeline phases specifically, this skill also enforces context isolation: it loads ONLY the declared inputs for the target phase, not the reasoning that produced them. That isolation is what makes the external check actually external.

## Step 1: Read Previous Session Context

Check if `.claude/handoff.md` exists.

**If it exists:** Read it. This is the previous session's handoff note — it tells you what was done, what's unfinished, and what to do first. Summarize it for the user:

> Last session: <what it was about>
> Accomplished: <key outcomes>
> Left unfinished: <items>
> Suggested first step: <action>

**If it doesn't exist (cold start):** No prior handoff. Read `CLAUDE.md` for project orientation and `docs/ARCHITECTURE.md` for current system state. Check for any in-progress slice. Then ask the user what they want to work on.

## Step 2: Read Current State

Regardless of whether a handoff exists:

1. Run `git log --oneline -5` — recent activity
2. Run `git status --short` — uncommitted changes
3. Check if `.claude/current-slice/slice.yaml` exists

Report:
> Git: branch `<name>`, last commit "<msg>" (<when>), <N> uncommitted files
> Slice: <active slice info or "no active slice">

## Step 3: Route to the Right Mode

Based on what you found:

### Mode A: Pipeline Phase (slice active + phase specified or inferrable)

If `.claude/current-slice/slice.yaml` exists, read it to determine the current phase.

If `$ARGUMENTS` specifies a phase, use that. Otherwise infer from `slice.yaml` status.

Read the phase-specific handoff note if it exists: `.claude/current-slice/handoff-phase-N.md`

Then load ONLY the declared inputs for the target phase:

**Phase 1 (Intent):**
- Load: `docs/ARCHITECTURE.md`, `docs/adr/index.md`
- **Greenfield slices**: Exclude source code (Phase 1 works from architecture docs only)
- **Modification slices**: Also load public interfaces of files in the envelope (function signatures, class definitions, docstrings). Exclude internal implementation logic.

**Phase 2 (Validation):**
- Load: `.claude/current-slice/intent.md`, `docs/ARCHITECTURE.md`, relevant ADRs from intent's `adrs-referenced` field
- Exclude: source code, any implementation ideas, Phase 1's reasoning

**Phase 3 (Implementation):**
- Load: `.claude/current-slice/intent.md`, test files from the validation phase
- Exclude: Phase 2's `approach.md` or reasoning about why tests are shaped the way they are

**Phase 4 (Integration):**
- Load: `.claude/current-slice/intent.md`, `docs/ARCHITECTURE.md`, the implementation (source files in envelope)
- Exclude: Phase 3's `implementation/notes.md` — check the code, not the reasoning

Then — before printing the orientation report below — read `docs/operational-reference.md § Phase Skill Guide` and surface the target phase's **role name**, **primary anti-behavior**, **secondary anti-behaviors**, and **primary + supporting skills** to the operator. This surfacing is the ADR-004 D4 commitment: the role and skill mapping are not dead text, they are read and echoed at every phase entry. For Phase 1 specifically, the primary-skills column is an em-dash (no primary fit) — still print the row so the operator sees the explicit absence rather than inferring a missing assignment. The Phase Skill Guide is a living registry; if an entry looks stale, the registry is the source to update, not this skill.

Report what's loaded AND what's deliberately excluded:
> **Loaded**: intent.md, 3 test files, ARCHITECTURE.md
> **Excluded** (context isolation): Phase 2 approach.md, implementation notes
> **Gate**: PASSED — intent.md committed at <hash>

### Mode B: Continuing Non-Slice Work

If the handoff note describes non-slice work (bug fix, research, architecture discussion):
- Load the files mentioned in the handoff note's "unfinished" section
- Summarize what needs to happen
- No context isolation rules — load whatever's relevant

### Mode C: Fresh Start (no handoff, no slice)

- Read `CLAUDE.md` and `docs/ARCHITECTURE.md`
- Check `docs/adr/index.md` for recent ADRs
- Check `.claude/sweep.yaml` for sweep status
- Ask the user what they want to work on

### Mode D: Dirty Recovery (slice active + uncommitted changes + no recent handoff)

If a slice is active (slice.yaml exists) AND `git status` shows uncommitted changes in slice-related files AND the handoff note is missing or clearly stale (references a different slice or older date):

This likely means a previous session crashed or the user forgot to run `/handoff`. Recover by:

1. Report the dirty state clearly:
   > **Recovery mode**: Slice <ID> is active at phase <status>, but there are uncommitted changes and no matching handoff note. The previous session likely ended without `/handoff`.
2. List the uncommitted changes and ask the user to confirm they are from the active slice
3. If confirmed: proceed as Mode A for the current phase, treating the uncommitted changes as in-progress work
4. If the user says the changes are stale or wrong: suggest `git stash` to preserve them, then proceed normally

## Step 4: Print Orientation

```
## Session Catchup — <date>

<if handoff exists>
**Previous session**: <summary>
**Unfinished**: <items>
</if>

**Mode**: <Pipeline Phase N | Continuing work | Fresh start>
**Loaded**: <list>
<if pipeline> **Excluded** (by design): <list>
<if pipeline> **Gate**: <PASSED | NEEDS: what's missing>

**Next step**: <what to do first>
```

The "Excluded" line makes context isolation visible. Neither the agent nor the user should accidentally load extra context when the isolation is deliberate.
