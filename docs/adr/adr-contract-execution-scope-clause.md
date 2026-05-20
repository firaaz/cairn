---
id: adr-contract-execution-scope-clause
name: "ADR contract grammar — execution-scope clause separates artifact blast radius from enabling work"
status: accepted
firmness: provisional
contract:
  must-satisfy:
    - D1 contract blocks MAY include execution-scope as an optional top-level field
    - D2 execution-scope enumerates enabling work permitted to land the contract artifact without expanding must-satisfy artifact-scope
  must-not-violate:
    - any consumer reads execution-scope as broadening must-satisfy clauses
    - execution-scope is interpreted as the artifact blast radius
  wrong-if:
    - a contract trial bends rather than stops because enabling work was needed but unenumerated
    - the same arc must rerun because a contract that should have allowed enabling work blocked it
  evidence:
    - this ADR own contract block includes a populated execution-scope field
    - the Phase-3 stress test at .claude/skill-runs/identity-and-scope-2026-05-20/outputs/phase-3-stress.md survives review
  execution-scope:
    - docs/adr/index.md update registering this ADR
    - docs/lessons.md L-025 entry capturing the structural lesson
    - cross-reference link from identity-and-scope-deferral
supersedes: null
supersedes-sections: []
superseded-by: null
topic: process
invariants-touched: []
date: 2026-05-20
---

# adr-contract-execution-scope-clause: ADR contract grammar — execution-scope clause separates artifact blast radius from enabling work

## Status

Accepted, provisional. Retrofit to existing contract-bearing ADRs is NOT mandated by this decision; see D3.

## Date

2026-05-20

## Context

Trial B (`docs/plans/2026-05-14-cairn-adr-contract-trial-b.md`, verdict at commit `a0e3fe6`) bound a `contract:` block to `docs/adr/identifier-scheme.md` with `must-satisfy / must-not-violate / wrong-if / evidence` clauses. During Trial B's `/decision` sub-arc (the schema-reconciliation that produced `[[schema-amendment-threshold]]`), the contract's plan-level `must-not-violate` clause ("no new files outside ADR + test file") correctly fired on a breach — but the breach was enabling work the arc legitimately needed (an extra ADR, a `docs/lessons.md` edit, an `ARCHITECTURE.md` annotation). The trial verdict (commit `a0e3fe6`):

> Contract detected drift correctly; trial bent rather than stopped. Insight feeds into next trial's contract design: distinguish artifact-scope (blast radius) from execution-scope (enabling work permitted).

The structural finding: the existing contract grammar conflates two altitudes.

1. **Artifact-scope (blast radius).** What the contract governs — the file or set of files whose correctness the contract asserts. `must-satisfy / must-not-violate / wrong-if / evidence` clauses operate at this altitude. A breach at this altitude means the artifact is wrong.

2. **Execution-scope (enabling work permitted).** What surrounding changes the arc may land to satisfy the artifact contract — index updates, lesson entries, cross-reference fixes, schema migrations on adjacent files. A breach at this altitude under the current grammar (no execution-scope field) means the arc trips on its own blanket "no new files" clause, which is not the failure the contract was designed to catch.

`feedback_plan_contract_scope_separation.md` operator memory had captured the lesson: "enabling work like /decision sub-arcs is not scope creep; future trial contracts should enumerate permitted enabling work explicitly." This ADR formalizes that capture as an optional contract-grammar clause.

### Why not handle this as a watching-mark per schema-amendment-threshold/D2?

`[[schema-amendment-threshold]]/D2` sets an N≥3 threshold for amending firm schema ADRs on the basis of single-file drift; the protocol for N=1 is "watching-mark in lessons.md." Three reasons that protocol does not strictly bind here:

1. **Different schema layer.** schema-amendment-threshold/D2's literal example is `identifier-scheme/D5` (feature-metadata schema). The ADR contract grammar is itself in-design — Trial A introduced the handoff-contract shape, Trial B introduced the ADR-contract shape, both still emerging. It is not a firm schema being amended; it is a grammar accreting clauses.
2. **Insight altitude.** Trial B's lesson is structural (two altitudes were conflated), not field-drift. Watching-mark protocol counts instances of the same field being added; the execution-scope insight applies to the grammar as a whole, not a single field.
3. **Optional vs. required.** This ADR adds an optional clause; it does not change required-field semantics of any existing contract. Contracts that omit `execution-scope:` remain valid and behave identically to today.

The watching-mark alternative was considered (Alternatives Considered, below).

## Decision

### D1 — Optional `execution-scope:` field

Contract blocks (as introduced by Trial A for handoff and Trial B for ADRs) MAY include `execution-scope:` as a top-level field alongside `must-satisfy / must-not-violate / wrong-if / evidence`. The field is a list of permitted enabling-work targets — file paths, glob patterns, or descriptive predicates — that the arc may modify or create without breaching the contract.

### D2 — Semantics

`execution-scope:` enumerates the surrounding edits permitted to land the artifact contract. It does NOT:

- expand `must-satisfy`'s artifact-scope — the contract still asserts only what `must-satisfy` claims about the named artifact
- relax `must-not-violate` for the named artifact
- license unrelated changes — listed targets must serve the arc that owns the contract

A breach is: an arc edits a file not in the contract's `execution-scope:` AND not the artifact itself. (If `execution-scope:` is absent, the contract behaves as today — every edit must serve the artifact directly per `must-not-violate`'s usual reading.)

### D3 — Retrofit policy

Existing contract-bearing ADRs (`docs/adr/identifier-scheme.md`, any handoff-contract bindings in `.claude/handoff.md`) are NOT mandated to add `execution-scope:`. They behave as today. Future trials and contracts SHOULD adopt the clause if their arc anticipates enabling-work needs.

This decision is provisional — if Trial C or a future contract trial produces a structural insight not absorbed by this clause, supersession is straightforward.

### D4 — Dogfood

This ADR's own `contract:` block (frontmatter) includes a populated `execution-scope:` field listing the three enabling-work edits that landing this ADR requires: index registration, lesson entry, and cross-reference from the companion ADR. The clause is exercised by its own introduction.

## Consequences

**Easier:**

- Future contract trials can declare enabling work up-front rather than discovering it during the arc and bending the contract.
- The `feedback_plan_contract_scope_separation.md` operator memory's prescription ("future trial contracts should enumerate permitted enabling work explicitly") has a concrete grammar to use.
- Reviewing a contract is two-altitude: artifact-scope clauses describe what the artifact must be; `execution-scope:` describes what the arc may touch in landing it.
- Trial A's handoff contract (still in flight) can adopt the clause if its design needs it; this ADR does not force adoption.

**Harder:**

- Authors writing contracts now have one more field to consider; misclassifying a change as enabling-work (when it should be inside `must-satisfy`'s artifact-scope) is a new error mode.
- The grammar accretes one more clause without a top-down formal spec. A consolidating ADR (post-Trial-A) may eventually be needed to spec the contract grammar as a whole.
- Tooling that parses contract blocks must learn the new optional field. Today no such tooling exists in the repo; if it lands later, it must accept-or-ignore `execution-scope:`.

## Alternatives Considered

**Alternative A — Watching-mark per schema-amendment-threshold/D2 (N=1).** Capture Trial B's lesson in `docs/lessons.md` as L-NNN, do not introduce a grammar clause until N≥3 trials show the same need. **Rejected** on three counts (see Context):

1. schema-amendment-threshold/D2 governs firm-schema amendment under single-file drift; the contract grammar is in-design and not yet firmly schematized.
2. The insight is structural (two altitudes) rather than field-drift (one missing field on one file).
3. The clause is optional and additive; existing contracts behave identically with or without it. The risk of premature schema lock-in that motivates D2's N≥3 threshold does not apply.

That said: this ADR records the insight at lesson-level too (cross-referenced from `docs/lessons.md`), so the structural finding is captured both in the grammar and in the lesson narrative.

**Alternative B — Full contract-grammar spec ADR (top-down).** Author a comprehensive ADR formalizing the entire `must-satisfy / must-not-violate / wrong-if / evidence / execution-scope` grammar with semantics for each clause, validation rules, and possibly a JSON Schema. **Rejected** as premature: Trial A is still in flight; Trial A's handoff-contract design may surface additional clauses or refinements. Locking the grammar now risks supersession by Trial A's outcome. A post-Trial-A consolidating ADR is the right time for top-down spec, not now.

**Alternative C — Edit identifier-scheme.md to add execution-scope to its existing contract block.** **Rejected** by CLAUDE.md ADR-body append-only rule (`reversibility-guard.sh` enforces frontmatter-only edits on existing ADRs). Even if mechanically allowed, this would conflate the identifier-scheme decision with the contract-grammar decision — two different concerns.

**Alternative D — Defer entirely until Trial A closes.** **Rejected** because Trial B's lesson is concrete and Trial A's outcome may take weeks; deferring loses the lesson's freshness and leaves the next contract author without a remedy for the same failure mode. The provisional firmness of this ADR makes supersession-after-Trial-A inexpensive if needed.

## Risk Register

| Scenario | Severity | This ADR's handling |
|----------|----------|---------------------|
| R1: Authors misclassify changes as enabling-work to evade `must-satisfy` | Possible / medium | D2 explicitly states `execution-scope:` does not relax artifact-scope clauses. Misuse is a documented error mode, not a grammar bug. |
| R2: Tooling lands later and chokes on the new field | Possible / low | D3 makes the field optional; tooling can ignore unknown fields safely. No current tooling parses contract blocks. |
| R3: Trial A's outcome produces a conflicting grammar refinement | Possible / medium | Provisional firmness; supersession is the standard remedy. The clause's optional nature minimizes blast radius if Trial A redefines the field's semantics. |
| R4: This clause becomes the only ad-hoc grammar extension, and the full spec ADR (Alternative B) is never written | Likely / low | This ADR's `## Consequences` "Harder" section names the consolidating-spec ADR as a follow-up. The risk is documentation debt, not correctness. |
| R5: schema-amendment-threshold/D2 is read as binding here by a future reader | Possible / low | Context section + Alternative A explicitly engage the question and explain why the protocol does not strictly bind. |

## Cross-references

- Trial B verdict: commit `a0e3fe6`, `docs/plans/2026-05-14-cairn-adr-contract-trial-b.md`
- Companion ADR: [[identity-and-scope-deferral]]
- Operator memory captured the prescription: `feedback_plan_contract_scope_separation.md`
- Related: `[[schema-amendment-threshold]]`, `[[identifier-scheme]]`
- Decision arc: `.claude/skill-runs/identity-and-scope-2026-05-20/outputs/`
