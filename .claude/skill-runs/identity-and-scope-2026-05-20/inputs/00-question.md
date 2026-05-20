# Decision question

> What are the **identity** and **scope** of Cairn?

Triggered by `docs/plans/2026-05-19-adaptive-reliability-direction.md`, which
proposes pivoting Cairn from "a high-consequence four-phase methodology" to
"an adaptive reliability layer for AI-assisted development" with 4 tiers
(Tier 0 hygiene → Tier 3 formal flow).

## Six review questions (from the direction doc)

1. Does the tier model solve the adoption problem without diluting Cairn's
   reliability promise?
2. Are Tier 0 and Tier 1 valuable enough for ordinary repositories?
3. Is Tier 3 still meaningfully different from "just use Claude/Codex
   carefully"?
4. Should tiers be selected by deterministic scoring, user declaration, or
   both?
5. What is the smallest slice that proves this direction without re-opening
   the full methodology design?
6. Which current docs/tests must be rebaselined first so `dev` is coherent?

## What I want out of this decision

Not just "accept/amend/reject the tier model." The deeper question:
**what is Cairn for, who is it for, and what does it ship?**

Possible identity poles (not exhaustive — Phase 2 will enumerate):
- A. High-consequence four-phase methodology (status quo framing)
- B. Adaptive reliability layer with graduated tiers (direction-doc proposal)
- C. Discipline-as-discipline: a set of hooks/validators that encode named
     failure modes, no tier hierarchy — operator picks tools à la carte
- D. Something else (TBD in Phase 2)

## Constraints carried in from prior analysis (2026-05-19)

- Trial B verdict: contract correctly detected drift; lesson is "distinguish
  artifact-scope (blast radius) from execution-scope (enabling work
  permitted)." This is a structural-altitude signal, not just a rule-tuning
  signal.
- 5 failing tests on `dev` are Trial-A-completion + INV-011/012 coverage
  mechanical debt, not evidence of methodology split.
- Substrate program retired at M4 (`cairn-substrate-and-fastmcp-superseded`);
  standing dep set is pydantic + typer + pyyaml. Direction doc's "hooks /
  validators / contracts / short guidance" framing aligns with current
  trajectory.
- Cairn's primary user is the operator (Firaaz) doing cairn-on-cairn.
  "Ordinary repositories" adoption framing has no external pull demonstrated
  yet.
- Two open trials: Trial A (handoff contract) still in flight; Trial B (ADR
  contract) closed with "works, but might be too strict" verdict.
