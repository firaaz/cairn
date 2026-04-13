# SLICE-005 Phase 3 Implementation Notes

## Architecture validator regression (expected)

Three new firm/accepted ADRs (005, 006, 008) trigger the architecture validator's Check B ("every firm/accepted ADR has at least one invariant in ARCHITECTURE.md"). ADR-007 is provisional and exempt.

This regression is expected per `intent.md` out-of-scope: "docs/ARCHITECTURE.md regeneration — happens via /refresh-architecture after ADRs land."

Resolution: `/refresh-architecture` at Phase 4 entry will add invariants for the new ADRs and resolve Check B. This is the sole regression introduced by Phase 3.

## V7 envelope compliance and test_context_budget interaction

`docs/plans/measurements/2026-04-12-slice-003.txt` was dirty at Phase 3 entry (noted in handoff). `test_context_budget.py` also writes to this file during its run, re-dirtying it mid-suite. V7 was already RED at baseline for this reason (the measurement file was dirty before Phase 3 started). V7 passes in isolation (18/18 SLICE-005 tests GREEN). The V7 failure in the full suite is a pre-existing test-ordering interaction, not a Phase 3 regression.

## Decisions the intent didn't pin down

- **ADR file naming**: Used descriptive kebab-case slugs: `005-semantic-identity.md`, `006-feature-slice-model.md`, `007-parallelism-v1.md`, `008-context-tiers-integration.md`. Numeric prefixes retained for consistency with existing ADRs (the rename is a future implementation slice per ADR-005 D3).
- **ADR topic fields**: Chose `naming` (005), `architecture` (006), `scope` (007), `process` (008) based on content alignment with existing ADR topic conventions.
- **ADR-007 supersedes format**: Used list entries with parenthetical scope notation: `"ADR-003 D4 (partial: parallelism deferral only)"` to make partial supersession clear in frontmatter.
- **ADR-008 INV-002 disposition**: Confirmed "accommodates without amendment" after analyzing that the cross-feature index fits within the 150-400 token budget at expected v1 scale (2-5 features).
