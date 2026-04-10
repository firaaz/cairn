# Handoff — Package Session Context for the Next Session

Close out a working session by capturing what happened, what's left, and what comes next.

Usage: `/handoff` (end of any session) or `/handoff phase` (end of a pipeline phase)

## Why This Exists

Every session accumulates context that's invisible to the next session. When you close a tab, all the "I know what I was doing" reasoning disappears. Without an explicit handoff, the next session wastes time rediscovering what was already known — or worse, makes different assumptions and silently diverges.

This skill is the exit bookend. Its companion `/catchup` is the entry bookend. Together they bridge the gap between sessions, whether you're doing pipeline work, fixing bugs, running research, or anything else.

## Step 1: Take Stock

Start by understanding the current state of the working directory.

1. Run `git status --short` to see uncommitted changes
2. Run `git log --oneline -3` to see recent commits
3. Check if `.claude/current-slice/slice.yaml` exists (determines whether we're in a slice)

If there are uncommitted changes, list them and ask whether to commit before handing off. Uncommitted work is the most common thing lost between sessions — surface it now rather than letting it rot.

## Step 2: Write the Handoff Note

Create (or overwrite) `.claude/handoff.md` with this structure:

```markdown
# Session Handoff — <date>

## What This Session Was About
<One sentence. Be specific: "Implemented Tier 2 query decomposition" not "worked on code.">

## What Was Accomplished
- <Concrete outcome, not activity. "Added X" not "worked on X">
- <Each bullet should be verifiable — someone could check if this is true>

## What's Unfinished or Blocked
- <Specific item, not vague. "test_tier2_decompose fails on multi-table joins" not "some tests fail">
- <If blocked, say why and what would unblock it>

## Next Session Should
1. <First thing to do — the most important or time-sensitive item>
2. <Second thing>
3. <Any cleanup or follow-up>

## Surprises or Discoveries
<Anything unexpected that came up. New constraints, bugs found in unrelated code, 
assumptions that turned out wrong, patterns worth recording in lessons.md.
If nothing surprising happened, say "None" — don't invent drama.>
```

This note is overwritten each session. It represents *current state*, not history. Git history provides the historical record.

## Step 3: Self-Check

Answer in one sentence: **"Does what I produced match what I set out to do?"**

- A direct, specific answer ("Yes — the intent document covers all three zones and is committed") means the session was well-sized.
- Hedging ("Mostly, but I also ended up refactoring the query router") means the session drifted or was too large. Note the drift in the handoff note so the next session knows.

## Step 4: Slice-Specific Handling

If `.claude/current-slice/slice.yaml` exists and `$ARGUMENTS` includes "phase":

1. Read `slice.yaml` to get the current phase number and slice ID
2. Write a phase-specific handoff to `.claude/current-slice/handoff-phase-N.md` with:
   - What this phase produced (the artifact)
   - Whether the phase gate is met (artifact committed?)
   - Any ambiguities discovered that the next phase should know about
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

**Session**: <what it was about>
**Git**: <N uncommitted files / clean>
**Handoff note**: .claude/handoff.md updated
<if slice> **Slice**: SLICE-NNN moved to phase N+1
<if slice> **Phase handoff**: .claude/current-slice/handoff-phase-N.md written

Next session: run `/catchup` to orient.
```
