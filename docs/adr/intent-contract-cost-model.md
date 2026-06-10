---
id: intent-contract-cost-model
name: "Intent-contract cost model — user approves the promise, agent owns the proof"
status: accepted
contract:
  must-satisfy:
    - "contract depth graduates by change size from the scope-statement floor (carrier: templates/intent.md graduated-contract rules + .claude/skills/cairn-intent)"
  evidence:
    - "templates/intent.md Contract section"
firmness: provisional
supersedes: null
superseded-by: null
resolved-by: trial-e-closure-adjudication
topic: architecture
invariants-touched: []
date: 2026-05-31
---

# Intent-contract cost model — user approves the promise, agent owns the proof

## Status

Accepted (post-`/decision` arc `intent-contract-model`, 2026-05-31; Phases 0–3 run
subagent-driven, then trimmed on operator review). **Provisional** — supersedes nothing, modifies
no invariant; Phase 5 not required. Coexists with `cairn-tdd-feature`; four-phase retirement stays
gated on Trial E per `intent-management-loop`/D7.

## Date

2026-05-31

## Context

Trial D's m2 measurement halted when the operator found hand-authoring the EARS contract painful
even on the lightest intent (`.claude/skill-runs/trial-d-measurement/README.md`). The operator
confirmed heavy-band authoring cost is a *recurring* driver (not an n=1 artifact). A subagent-driven
`/decision` (Phases 0–3; arc artifacts under `.claude/skill-runs/intent-contract-model-decision/`)
explored a full "band-dependent promise model" with traceability + severity + a fidelity challenge.
On review that draft over-committed: it shipped *enforcement machinery* whose catching-value is
**unmeasured** to justify a *cost-model* decision, defaulted users into ceremony, and buried the one
elegant idea. This ADR keeps only what the evidence supports: the invariant, and cost-removal.

## Decision

**D1 — The cost model (the decision).** The user approves the **promise** — the plain-language
*what*. The agent owns the **proof** — formalization, tests, evidence. Approval and verification
share one object. Everything below is subordinate to this.

**D2 — Immediate commitment (value-independent).** Remove operator hand-authoring of EARS: where a
feature is formalized at all, the agent drafts the formal contract from the operator-approved
promise; the operator never hand-writes EARS clauses. **Light/trivial work carries a thin prose
intent only — no formal `## Contract`** (the m2 fix). This commits cost-*removal* and bets nothing
on the formal layer's catching-value.

**D3 — Deferred commitment (measured follow-on).** Heavy-band *enforcement* — derived banding,
promise↔clause traceability, agent-declared/challenger-attacked severity, and the front-loaded
fidelity challenge — is **not shipped now**. It is a future ADR, gated on Trial E showing the formal
proof adds value under the agent-owned model, and it ships as one bundle (the fields never precede
the workflow that drafts them; the operator never reviews formal machinery). Its design constraints
are recorded below so the follow-on does not re-derive them.

**D4 — Explicit non-commitment.** This decision introduces **none** of the following now: a
`band: light` field; a default-HEAVY posture; or any `## Promise` / `pid` / `traces-to` / `severity`
grammar. No new gate, no new template field ships under this ADR.

**D5 — Trial consequence.** Trial E measures whether the formal proof adds value **under the
agent-owned model** — i.e. now that the operator no longer hand-authors it, does the formal contract
catch anything a thin prose intent plus the existing gates would not. That measurement gates D3.

## Consequences

**Easier:**
- Heavy-band authoring stops being operator hand-EARS; light work sheds the contract entirely (the m2 pain disappears at its source).
- The decision commits only cost-*removal*, so it bets nothing on still-unmeasured enforcement value — the right posture for a cost-model decision.
- The elegant invariant (D1) is the headline, not buried under machinery.

**Harder / honest:**
- In the interim, heavy-band agent-drafted formalization is reviewed by the **operator + the existing gates** (`premise_guard` grounding, `atomicity`, the four-phase Skeptic / front-challenge) — there is no *new automated* intent-fidelity backstop until D3 lands. The floor concern (below) is real and explicitly unaddressed by new machinery until then; we accept today's defenses in the interim.
- "Agent drafts, operator approves the promise" is a real authorship move; its safety rests on the human origin of *what* (the promise) plus the deferred fidelity bundle — D3 must land before heavy-band agent-drafting is leaned on at scale.

## Deferred design constraints (for the future heavy-band bundle)

Preserved from the `/decision` arc's pre-mortem and adversarial stress (full detail in
`.claude/skill-runs/intent-contract-model-decision/{framing,context}.md`). The heavy-band
enforcement follow-on **must** answer these; they are not solved here:

1. **Ceiling-not-floor.** A promise bounds *scope*, never the *floor* (severity / must-fail). The m5
   A10 "fail-loud / declare-unsafe" canary can be drafted as "the validator shall report a result"
   — grounded, atomic, within-promise — and ship as log-and-exit-0. The bundle must declare and
   attack the floor (see `docs/lessons.md` L-028), or wrong-intent ships green.
2. **Band determination must be derived, not declared.** Default-HEAVY is adoption-hostile;
   user self-classification is a burden; either way "whoever picks the band picks whether the floor
   exists." The band must be inferred from the work (cites sources / declares invariants / touches
   enforcement) and folded into the promise the operator already approves — never a separate knob.
3. **Quadratic at scale.** Traceability is O(pids×clauses) and a single-pass fidelity challenge
   skims at 30+ clauses; "one promise you approve" must not degrade into a pid-taxonomy.
4. **Distribution staleness.** New gates/fields render as inert prose on a consumer running stale
   hook wiring (`.slice-system` lag, `intent-management-loop`/R1); enforcement must ship via the
   plugin-release path, and no global `*_FIX` bypass (becomes a universal silent disable, L-018).
5. **Approval timing.** Promise-approval upstream of the gates can force a re-approval when
   post-approval formalization reds `premise_guard`; ground premises on the prose promise at
   approval and defer only EARS-shaping.
6. **Same-family residual.** A fresh-context fidelity challenger raises the floor but ~60%
   co-misses (`intent-management-loop`/D4, EXPOSED); cross-family escalation is the named fallback.

## Alternatives Considered

- **Ship the full band-dependent promise model now** (band rule + `traceability_guard` + `severity`
  + fidelity challenge). *Rejected:* commits enforcement machinery against unmeasured value
  (backwards for a cost-model decision), default-HEAVY is adoption-hostile, and it front-loads
  user-facing fields before the workflow that drafts them. Its mechanisms are recorded above as
  deferred design constraints, not discarded.
- **Graduated-mandate, operator-authors** (resolve banding only; keep operator hand-authoring on
  heavy). *Rejected:* leaves the heavy-band authoring cost the operator confirmed is real, and
  Phase 3 showed its "mechanical band immunity" is false. **Recorded as the active alternative**, not
  eliminated: if the agent-owned model's Trial-E measurement fails, this ADR is the right candidate
  for supersession.
- **Atomicity advisory-only / lazy-formalize-at-close.** *Rejected:* weakest floor / reopens the
  slice-#25 wrong-premise propagation past the grounding gate.
