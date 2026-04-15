# Brainstorming + Decomposition Formalization — Session Capture

**Status:** Exploratory session, stopped mid-brainstorm. Not a ready-to-execute plan.
**Date:** 2026-04-14

## Context

User asked a chain of methodology questions about cairn:

1. How does the system handle plans? Is "intent" enough, or do hard cases need development plans?
2. Wouldn't Phase 1 research affect the intent/scope itself?
3. How do we decide what a slice is?

These converged on the same underlying gap: **cairn under-specifies the upstream of the slice pipeline** — brainstorming, decomposition strategy, and slice sizing.

## Problems identified

- **Brainstorming is informal.** Feature files exist (ADR-006) but the process that produces them has no protocol. `/decision` handles decisions formally; brainstorming doesn't have a parallel.
- **No slice-sizing guidance.** ADR-006 defines slices as "the unit of execution" but offers zero heuristics for drawing boundaries. Only a reactive recovery path (D7: "scope too large → park, re-decompose").
- **Phase 1 Intent can't self-validate scope.** It's deliberately forbidden from deep codebase reads, so it can't detect that a slice is mis-sized until Phase 2 Skeptic invests effort.
- **No decomposition strategy is encoded.** The user wants walking-skeleton decomposition (skeleton first, flesh out layers) because AI iterates better against working surfaces. Currently this is tacit knowledge, not protocol.

## User's positions (from clarifying questions)

- Brainstorming should become **feature-level Phase 0**, not slice-level.
- Brainstorming and `/decision` are **independent** — not every brainstorm needs a decision, not every decision needs a brainstorm. A single brainstorm may produce 3-4 slices.
- **No per-slice Design phase for now.** Feature-level brainstorming + good decomposition should be enough. Add per-slice design only if evidence demands it (YAGNI).
- Feature file is the **sole artifact**. No separate design doc. Keep the breakdown high-level, not low-level.
- **Walking skeleton** as the AI-optimized decomposition strategy. Skeleton gives AI concrete feedback loops (tests pass/fail, observable behavior) instead of trying to build deep functionality in isolation.
- Open on how cairn should relate to the mature superpowers `brainstorming` skill.

## Approaches discussed

- **A: New cairn protocol + skill.** Dedicated `/brainstorm` skill and ADR. Full reinvention.
- **B: Extend `/start-slice`.** Absorb brainstorming into slice init. Conflates feature and slice levels.
- **C: Artifact-only, no protocol.** Enrich feature file fields, leave conversation freeform.
- **D: Wrap superpowers brainstorming.** Reuse the mature protocol, redirect the terminal step to produce a cairn feature file instead of a `docs/plans/` design doc. (User pointed this out as worth considering.)

**Open question where session stopped:** If Approach D, how to integrate — intercept the artifact step, chain after, or compose by convention.

## Key constraints surfaced

- Walking skeleton decomposition is cairn-specific heuristic; superpowers brainstorming doesn't know about it.
- Superpowers brainstorming terminates in `writing-plans` skill; cairn needs it to terminate in `/start-slice`.
- Feature file schema (ADR-006 D2) is the canonical artifact; any brainstorming protocol must produce/update it.
- ADR-006 D3 "always-create" policy: every slice belongs to a feature file, even trivial single-slice features. Brainstorming must be lightweight enough to not feel like ceremony for trivial features.

## Related prior work in repo

- `docs/adr/006-feature-slice-model.md` — feature file spec
- `docs/adr/009-phase-pipeline-evaluation.md` — evaluated phase shape; rejected renames but noted ceremony adapts via Skeptic judgment
- `docs/plans/2026-04-11-substrate-and-framework-exploration-notes.md:155-175` — prior 5-phase proposal adding Design phase between Intent and Validation. User chose NOT to adopt this for now, but it's documented if feature-level brainstorming proves insufficient.
- `commands/claude-code/decision.md` — existing protocol to pattern-match against (but lighter for brainstorming)

## If resuming

Next steps would be:
1. Resolve the Approach A/D choice (build from scratch vs. wrap superpowers)
2. If D: decide integration mechanism (intercept / chain / compose)
3. Draft an ADR for the brainstorming protocol
4. Define the walking-skeleton decomposition heuristic in concrete terms (what "skeleton first" means for different work types: code, ADR, hook, etc.)
5. Update `/start-slice` to handle the "no feature file yet" path via the brainstorming protocol
