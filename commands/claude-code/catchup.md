# /catchup

Orient a new session using the tiered context discipline protocol (context-discipline-protocol).

Usage: `/catchup` (auto-detect) or `/catchup phase 2|3|4` (enter pipeline phase)

## Rules

1. Tier 1 always runs. Read ONLY: `.claude/handoff.md`, `.claude/current-slice/slice.yaml`, `.claude/sweep.yaml`, `git log --oneline -5`, `git status --short`. Produce orientation summary and STOP.
2. DISPATCH Tier 2 subagent if and only if: (a) user asked a factual question Tier 1 did not answer, (b) user directed pipeline phase entry with handoff pointers, (c) verifying a file named in handoff pointers before acting. Do NOT dispatch to "be thorough."
3. Tier 2 subagent contract — CONTEXT: slice/session state. QUESTION: specific question. FILES AVAILABLE: ≤5 files. YOUR BEHAVIOR: read only listed files, no expansion. YOUR RETURN: ≤200 words — direct answer, one file:line citation, unresolved ambiguity. DO NOT return: repo summaries, reflective prose, or next-step advice.
4. Tier 3 is the absence of catchup — once user gives a direct imperative, normal reading resumes.
5. Every report states Mode, Loaded, and Excluded.

## Modes

Four routing modes, all start at Tier 1: ### Mode A dispatches Tier 2 for pipeline phase entry, surfaces Phase Skill Guide roles/skills; ### Mode B stays Tier 1 for non-slice work; ### Mode C is fresh start; ### Mode D is dirty recovery.

## Load full

- If `/catchup phase N` is used: read catchup.full.md for Mode A phase-input tables, orientation template, and role/skill surfacing.
- If handoff missing AND slice active AND uncommitted changes: read catchup.full.md for Mode D dirty-recovery protocol.
