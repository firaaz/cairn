# /handoff

Package session context as a bounded pointer for the next session.

Usage: `/handoff` (any session) or `/handoff phase` (pipeline phase end)

## Rules

1. Read `templates/handoff.md` before writing — it is the shape source of truth.
2. Token budget: 150–400 tokens whole-file (≤2000 chars). Hard upper bound.
3. Four fixed sections: `## State` (1–2 present-tense sentences), `## Next` (one imperative line), `## Blocked / Pending` (≤5 pointer lines), `## Pointers` (file + when-to-read).
4. Voice: imperative and declarative. No first person, no hedging, no "we"/"I"/"maybe".
5. BANNED: reflective summaries, test tallies, apologies, "I tried X but Y", discovery paragraphs, inline rationale.
6. If urge to explain — put it in a commit message, ADR, or docs/lessons.md.
7. Check for uncommitted changes first. Surface before they rot.
8. For `/handoff phase`: write phase handoff to `.claude/current-slice/handoff-phase-N.md`, update slice.yaml status, print context-isolation reminder.
9. As the final step of every `/handoff` invocation, run `bash scripts/verify_handoff.sh` to catch L-005-class side-effect divergence (slice.yaml/commit/phase-handoff skew).

## Load full

- If `/handoff phase` is used and slice.yaml exists: read handoff.full.md for slice-specific handling steps and output template.
