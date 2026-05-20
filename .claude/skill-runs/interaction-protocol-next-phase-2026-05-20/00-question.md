# Interaction-protocol next-phase — decision

**Question:** After Trial A landed and Trial B closed with the operator verdict "works, but might be too strict," what is the next phase of the `cairn-as-interaction-protocol` reframe?

## Three branches on the table

- **Branch RETROFIT (Trial-B-tail).** Apply Trial B's identifier-scheme contract pattern to legacy artifacts that violate it: the 14 ADRs missing `name:` field, the 6 slice ids violating kebab-case, and any similar drift surfaced by the Trial-B audit. Defer Trial C.
- **Branch TRIAL-C (slice-intent contract).** Move to the highest-friction test of the contract pattern: bind a `contract:` block to slice `intent.md` artifacts produced by Phase 1 (Reader). This is the rubber-stamping target — slice intents are the most-LLM-authored, most-prone-to-drift artifact in the methodology.
- **Branch TIGHTEN-FIRST.** Take the "too strict" verdict from Trial B's close (commit `a0e3fe6`) as a signal: refine the contract-block shape itself before extending to a third surface. Examples: relax mandatory keys, introduce contract-block versioning, separate `must-satisfy`/`must-not-violate` granularity, etc. Then decide RETROFIT vs. TRIAL-C from a stronger base.

## Context inputs

- Trial A plan + outcome: `docs/plans/2026-05-13-cairn-as-interaction-protocol.md`, commit `53a7c58`.
- Trial B plan + outcomes: `docs/plans/2026-05-14-cairn-adr-contract-trial-b.md` (spec) and `docs/plans/2026-05-14-cairn-adr-contract-trial-b-impl.md` (impl).
- Trial B close: commit `45c31a8` ("chore(handoff): Trial B closed; legacy-label retrofit deferred"); operator verdict at `a0e3fe6` ("works, but might be too strict").
- Trial B's deferred audit findings (legacy ADRs missing `name:`, slice-id kebab-case violations).
- INV-002 closure: commit `d35ded5` (2026-05-20, this session) — INV-002 now bound via test-ref to `tests/unit/test_handoff_contract.py`.
- Recent /decision arc that fed Trial B's close: `feature-schema-d5-reconciliation` (commit `e0ea977`) and `identity-and-scope-deferral` (commit `801e580`).

## Why this is decision-weight

The branch picked sets the scope of cairn's next ADR territory:
- RETROFIT is operational/no-ADR — no decision-weight by itself, but choosing it defers Trial C and TIGHTEN-FIRST indefinitely.
- TRIAL-C produces a new contract surface (slice intent) with cross-cutting consequences for Phase 1 dispatch, Phase 2 RED-test validity, and the cairn-tdd-feature skill flow.
- TIGHTEN-FIRST proposes an amendment to the existing contract-block shape — directly amending Trial-A/Trial-B's already-firm bindings (INV-002 + identifier-scheme ADR contract).

## Decision shape

Three-way at the top. Each branch has distinct downstream cost shape and distinct risk surface. Pre-mortem must enumerate failure modes per branch; Phase 2 enumerates approaches *within* the chosen branch (or argues the cross-branch trade differently).

## Triggered by

- Operator goal "do C" → step B (this /decision) after closing INV-002 (step A).
- Trial B verdict "might be too strict" (commit `a0e3fe6`).
- Trial A plan doc lines 212–214 flagging the post-trial fork as operator-decision territory.
