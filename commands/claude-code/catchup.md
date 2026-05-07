# /catchup

Orient a fresh session. The bookend to `/handoff` — handoff writes the pointer at session end; catchup reads it at session start.

Usage: `/catchup`

## Rules

1. **Read these four sources in order, then stop.** Don't dispatch subagents, don't invoke skills, don't pre-explore the codebase. The point is a quick read so the user can drive next.
   - `.claude/handoff.md` — the State / Next / Blocked / Pointers from the prior session.
   - `git log --oneline -10` — what shipped recently.
   - `git status -s` — working-tree state (uncommitted changes, untracked files).
   - `.claude/active-envelope.yaml` if present — surface `mode:` and a one-line summary of `paths:` so the user knows what the write gate looks like this session.
2. **Synthesise a brief catchup.** Branch + tip SHA, what the prior session left as Next, anything in Blocked / Pending, anything in working tree that needs attention, and (if the envelope file is present and `mode: operator`) what's in scope for writes.
3. **Stop after the catchup.** No "what would you like to do next?" prompts beyond a single sentence offering to proceed with the handoff's Next item or wait for direction.

## Anti-patterns

- Do not read ADRs, plans, or `docs/` files unless the handoff's Pointers explicitly cites them and the user has asked a question that requires them.
- Do not run the test suite or validator — the catchup is orientation, not verification.
- Do not propose changes. Catchup ends; the user decides.

## When the handoff is missing or stale

- Missing: say so, fall back to `git log --oneline -20` + `git status -s` + the most recent project memory entries by date.
- Stale (handoff `as-of` SHA != current branch tip): note the SHA gap and surface commits between the two before drawing conclusions.
