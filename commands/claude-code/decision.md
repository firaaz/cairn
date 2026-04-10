# Decision — Architectural Decision Protocol

Make an architectural or design decision with structural safeguards against correlated errors.

Usage: `/decision <question>`

## Why This Is Heavy

Decisions are the most upstream task in this system. Every invariant, every slice, every test, every line of implementation flows from decisions. A bad decision that feels right (correlated error from a single model/context) will produce a confident, well-tested, completely wrong system. The cost of getting a decision wrong is the cost of all downstream work that builds on it.

This protocol is deliberately heavier than a quick judgment call. It uses context isolation, forced enumeration, adversarial stress-testing, and evidence-backed reasoning to catch the errors that a single-pass analysis systematically misses.

## When to Use This

Use this for decisions that will become ADRs — anything that affects invariants, boundaries, data ownership, or module structure. If the decision changes what downstream slices can assume, it goes through this protocol.

For local implementation decisions within a slice (which function to use, how to structure a loop), skip this and just note it in `implementation/notes.md`.

## Phase 0: Constraint Harvest

Before proposing anything, understand what's already decided.

1. Read `docs/ARCHITECTURE.md` — extract every invariant that this decision could affect
2. Read `docs/adr/index.md` — identify ADRs in related topics
3. Read the relevant ADRs (not all of them — only the ones touching related topics/invariants)
4. Read `docs/lessons.md` — check for patterns from prior decisions

Produce a **constraint envelope**: a list of specific constraints this decision must respect, each with its source (ADR number, invariant number, or lesson).

If you find constraints that conflict with each other, stop and surface the conflict to the user before proceeding. Conflicting constraints mean a prior decision needs revisiting, and that's a different task.

## Phase 0.5: User-Journey Trace

Before proposing any solution, trace the workflow this decision enables end-to-end. This step exists because the v0 build shipped without session handoff skills — an obvious gap that would have been caught instantly by walking through the user journey.

1. Write a numbered sequence of concrete user actions that this decision enables or changes
2. At every **session boundary**: what does the next session need to know, and how does it get that information?
3. At every **artifact boundary**: who produces this, who consumes it, and what happens if it's missing or malformed?
4. At every **state transition**: what mechanism moves the system from state A to state B?

If any step has no mechanism — if the answer is "the user will figure it out" — that's a gap in the decision, not a gap in the user. Surface it before proceeding.

The journey trace feeds directly into the pre-mortem: gaps in the journey ARE failure scenarios.

## Phase 1: Pre-Mortem

Before proposing any solution, imagine it failed.

Ask yourself: *"It's 3 months from now and this decision turned out to be wrong. What happened?"*

Write down at least 3 failure scenarios:
- **Technical failure**: What technical assumption could be wrong?
- **Scale failure**: What works now but breaks at 10x the current load/data/complexity?
- **Integration failure**: How could this decision interact badly with other parts of the system?

These failure scenarios become the test cases for Phase 3. They're much easier to generate before you're invested in a specific approach.

## Phase 2: Forced Enumeration

Enumerate at least 3 viable approaches. For each:

| Approach | Core Idea | Fits Constraints? | Pre-Mortem Exposure | Downstream Impact |
|----------|-----------|-------------------|--------------------|--------------------|
| A | ... | Which constraints it honors/violates | Which failure scenarios it's vulnerable to | What it makes easier/harder for future slices |
| B | ... | ... | ... | ... |
| C | ... | ... | ... | ... |

Rules:
- Every approach must be genuinely viable, not a strawman. If you can't think of 3 real options, you don't understand the design space well enough — do more research.
- For each approach, cite evidence from the codebase (file:line) or docs (ADR-NNN), not from memory. Memory is where correlated errors hide.
- Rate each approach against the pre-mortem failure scenarios. An approach that survives all three failure scenarios is stronger than one that only survives the happy path.

## Phase 3: Adversarial Stress Test

Take the strongest approach from Phase 2 and attack it.

**Disconfirming search**: Actively look for evidence that this approach is wrong.
- Search the codebase for patterns that would conflict with this approach
- Check if any existing ADR's consequences section warns against something this approach does
- Look for edge cases in the data or usage patterns that this approach doesn't handle

**Steel-man the opposition**: Take the second-best approach and argue its case as strongly as possible. What does it handle that the preferred approach doesn't?

**Assumption audit**: List every assumption the preferred approach depends on. For each:
- Is this assumption verified (cite evidence) or believed (state the belief)?
- If the assumption is wrong, does the approach degrade gracefully or fail catastrophically?

If the stress test reveals a serious flaw, go back to Phase 2 and re-evaluate. If the preferred approach survives, proceed.

## Phase 4: Decision Record

Write the decision as a formal ADR using `/new-adr`. The ADR should include:

- **Context**: What prompted this decision (constraint harvest results)
- **Decision**: The chosen approach with specific commitments
- **Consequences**: What changes, including which invariants are affected
- **Alternatives Considered**: The full enumeration from Phase 2 with reasons for rejection
- **Risk Register**: The pre-mortem failure scenarios and how the chosen approach handles each

## Phase 5: Independent Verification (for firm decisions)

If this decision will have `firmness: firm` — meaning it requires ceremony to change later — run an independent verification:

1. Commit the ADR draft
2. Start a fresh session (or spawn a subagent with only these inputs):
   - The decision question
   - The constraint envelope from Phase 0
   - `docs/ARCHITECTURE.md`
   - Relevant ADRs
   - Do NOT include your reasoning, enumeration, or stress test results
3. In the fresh context, run Phases 1-3 again independently
4. Compare the two sessions' conclusions:
   - **Same approach chosen**: High confidence. Proceed.
   - **Different approach, same constraints identified**: The approaches are trading off different things. Surface the trade-off to the user for a human judgment call.
   - **Different constraints identified**: One session found constraints the other missed. Merge the constraint sets and re-evaluate.

This independent verification is expensive (~2x the token cost) but cheap compared to the cost of a wrong firm decision propagating through dozens of downstream slices.

For `firmness: provisional` decisions, skip Phase 5 — provisional decisions are expected to be revisited as the project learns more.

## Phase 6: Propagation

After the ADR is accepted:

1. Run `/refresh-architecture` to update ARCHITECTURE.md
2. Check if any in-progress slice's intent.md needs updating (new constraints may invalidate existing intents)
3. If this decision superseded an existing ADR, verify the old ADR's frontmatter was updated
4. Record any cross-cutting patterns in `docs/lessons.md`

## Quick Reference: Decision Quality Checklist

Before finalizing, verify:
- [ ] Every constraint in the envelope has a source citation
- [ ] At least 3 approaches were genuinely considered
- [ ] The pre-mortem generated failure scenarios the chosen approach actually addresses
- [ ] Evidence is from files/docs, not from model memory
- [ ] The stress test attacked the preferred approach, not just the alternatives
- [ ] Assumptions are listed and classified (verified vs believed)
- [ ] The ADR's consequences section is honest about what gets harder, not just what gets easier
- [ ] User journey traced end-to-end with no unmechanized handoffs
