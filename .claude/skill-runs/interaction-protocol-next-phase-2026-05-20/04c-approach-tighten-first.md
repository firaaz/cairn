# Approach TIGHTEN-FIRST — Steelman

## Premise reckoning

The pre-mortem's contestation of Claims 1 and 7 is correct, and TIGHTEN-FIRST must not rest on the false premise.

- `docs/adr/adr-contract-execution-scope-clause.md:5-29`: the artifact/execution-scope conflation was diagnosed at the **plan-level contract** (the `feature-schema-d5-reconciliation` arc inside Trial B), and the fix shipped as an optional `execution-scope:` clause for ADR contract blocks. Trial B's *ADR-contract block* (`identifier-scheme.md:6-22`) did not bend.
- `docs/lessons.md:472` (L-024) captures N≥3 as plan-doc/process lesson, not contract-block-shape lesson.
- `docs/adr/identity-and-scope-deferral.md:51` D3.3 explicitly treats the execution-scope fix as load-bearing: a new structural insight only triggers reconsideration if "not absorbed by `[[adr-contract-execution-scope-clause]]`."

So TIGHTEN-FIRST cannot be motivated by "Trial B bent → contract pattern is brittle." That motivation is consumed. **Reframe**: TIGHTEN-FIRST is **the post-Trial-A consolidating grammar spec the execution-scope ADR itself defers to** — `adr-contract-execution-scope-clause.md:103` explicitly names "a consolidating ADR (post-Trial-A) may eventually be needed to spec the contract grammar as a whole." Independent reasons remain: per-clause audience-tag ambiguity (Trial A is agent-to-agent, Trial B validator-facing, Trial C would be operator-facing — same slots, three jobs), and undocumented `wrong-if` vs `evidence` semantics. The execution-scope ADR addresses neither.

## Core idea

Author one consolidating contract-grammar ADR defining: clause vocabulary (`must-satisfy / must-not-violate / wrong-if / evidence / execution-scope`), per-clause semantics, audience annotation. **Success criterion:** every existing contract (Trial A handoff, Trial B identifier-scheme, the execution-scope ADR's own dogfood block) parses unchanged under the new grammar, and a contract for a third surface can be authored without re-litigating clause semantics.

## Mechanism

- New ADR `contract-grammar-v1.md`, status `accepted`, firmness `provisional`.
- `supersedes-sections: [adr-contract-execution-scope-clause/D1, adr-contract-execution-scope-clause/D2]` — absorbs execution-scope into the unified grammar; per `identifier-scheme.md:85` ("Decisions survive across ADR states via amendment"), section-level supersession is the established pattern.
- Adds one optional clause-shape: `audience:` (free-form: `validator | phase-agent | operator | reader`).
- New `tests/unit/test_contract_grammar.py` — fixture-driven; loads existing contract blocks as YAML, asserts each parses.

**Engaging Scenario 2 (`03-premortem.md:29`, supersession-of-justification trap):** don't supersede the firm parts. `identifier-scheme.md`'s contract block (lines 6-22) is bound by `test_identifier_scheme_contract.py`; that stays untouched. The consolidation only sections-supersedes `adr-contract-execution-scope-clause` (firmness: `provisional`, line 5), whose own line 85 calls supersession "straightforward." **N≥3 does not bind** (`schema-amendment-threshold.md:51`): that trigger governs WIDEN of a firm schema's required-field set on single-file drift. This is neither WIDEN nor a firm-schema amendment — it is grammar consolidation of a provisional ADR, which `adr-contract-execution-scope-clause.md:103` itself names as follow-up.

## Constraint fit

- **Honors:** `01-constraints.md:5-22` — INV-002/003/005/006 untouched; identifier-scheme D1–D9 untouched; `test_identifier_scheme_contract.py` unchanged. ADR append-only respected.
- **Honors:** `adr-contract-execution-scope-clause.md:85` — supersession invitation explicit.
- **Risks violating schema-amendment-threshold N≥3:** addressed above (`schema-amendment-threshold.md:51` scope is firm-schema field-drift, not provisional consolidation).
- **Risks:** `feedback_designs_through_decision` memory says consolidating-grammar ADRs are decision-weight and need `/decision`. Mitigated: TIGHTEN-FIRST *is* the /decision; the ADR is its artifact.

## Engagement with pre-mortem attacks

1. **"Tightening without a second instance over-fits to Trial B"** (`03-premortem.md:27`). **Counter:** the reframed TIGHTEN-FIRST consolidates three already-existing instances — Trial A handoff contract, Trial B identifier-scheme contract, the execution-scope ADR's own dogfood block. N=3 *for consolidation purposes* is already met. It documents de-facto convergence, not invents new shape.

2. **"Exploratory ADR refining a firm one is status-mismatch"** (`03-premortem.md:29`). **Counter:** the consolidating ADR lands `accepted, provisional` — not `exploratory`. It section-supersedes only the `provisional` execution-scope ADR. The `firm` identifier-scheme contract block is preserved because the grammar describes what it already is. No firmness inversion.

3. **"Backward-compat governance gap"** (`03-premortem.md:31`). **Counter:** consolidation IS the policy. No v1/v2 split — prior contracts are grandfathered by parsing as fixtures. Future contracts cite `contract-grammar-v1`. Gap closed *because* TIGHTEN-FIRST exists.

## What TIGHTEN-FIRST achieves that RETROFIT/TRIAL-C don't

Claim 5's meta-attack (`03-premortem.md:56`) — that "ascending decision-weight" presumes risk-tolerance is the bottleneck, not calendar-time — applies but cuts differently. The reframed TIGHTEN-FIRST is "consolidate while three instances are fresh, before reader confusion compounds." Distinct value:

- **Audience disambiguation for future readers.** A reader cold-opening `docs/adr/` sees three contracts with three subtly different implicit grammars. Each new author re-derives. Same failure mode `semantic-identity` solved with `name:` — reach-into-prose anti-pattern (`identifier-scheme.md:43`).
- **TRIAL-C unblocked, not delayed.** Without consolidation, a Trial C author chooses between Trial B's validator-shape, Trial A's agent-shape, or invents a third. Audience-tag gives an explicit template. Otherwise Trial C silently produces a fourth de facto instance.
- **Small, bounded cost.** One provisional ADR, one fixture-test, no changes to existing tests. 1–2 sessions. Provisional firmness makes Trial-C-driven supersession cheap.

## Downstream impact

- **Easier:** TRIAL-C authors start at "which clauses, which audience" rather than "what is a contract." RETROFIT unaffected.
- **Harder:** TRIAL-C deferred 1–2 sessions. One more provisional ADR in flight. If TRIAL-C surfaces a missing clause, supersession churn.

## Honest costs

- **Calendar time:** 1–2 sessions; real cost is TRIAL-C deferral.
- **Strongest argument against:** `adr-contract-execution-scope-clause.md:116` says "post-Trial-A consolidating ADR is the right time for top-down spec, not now." Spirit reads "post-enough-instances." Trial C is the natural third instance; consolidating before it commits to a grammar that may need v2 immediately. The execution-scope ADR chose deferral; TIGHTEN-FIRST is in tension with that explicit choice.
- **Premature optimization (per contested premise):** even under the consolidation reframe, TIGHTEN-FIRST is optimization-of-documentation, not optimization-of-protocol. Trial B's verdict was "works" (`a0e3fe6`). Reader-disambiguation is real but speculative; the one-operator-on-cairn-on-cairn constraint (`identity-and-scope-deferral.md:33`) makes reader confusion an unlikely actual bottleneck. **Forced-enumeration honest verdict: TIGHTEN-FIRST is the weakest of the three branches when calendar-time and learning-velocity dominate, and the strongest only if the operator's actual constraint is "stop accreting implicit grammar variants before the count passes three."**
