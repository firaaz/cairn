---
id: decision-defect-escalation
name: "Decision-defect escalation — a fix that only passes by weakening a constraint is a wrong decision, not a patch"
status: accepted
carrier: rationale-only
firmness: provisional
supersedes: null
superseded-by: null
topic: process
invariants-touched: []
date: 2026-06-05
---

# Decision-defect escalation — a fix that only passes by weakening a constraint is a wrong decision, not a patch

## Status

Accepted. **Provisional** — supersedes nothing, modifies no invariant, ships no hook or field.
The one enforcement artifact (a close-review / Phase-4 prompt line) and any automatic escalation are
deferred (D4–D5); the rule itself is the commitment.

## Date

2026-06-05

## Context

A session reconsidering next-task selection started from "what's the next task" and exposed a deeper
gap: cairn's flat backlog blurs **decided work** (ADRs awaiting implementation) with **reactive
work** (bug fixes), and treats every item as one undifferentiated "open" thread. Two facts break the
flat view — ADRs are not equal in magnitude, and a bug can be either an implementation defect *or*
evidence that a decision was wrong. Patching the second kind at the implementation level is silent
architectural debt: you band-aid the symptom of a wrong decision and the architecture rots.

The session rejected a series of imported prioritization frames (GTD, Eisenhower, OKR,
SpecKit-constitution) and a static decision/implementation taxonomy as either foreign to cairn's
primitives or behavior-neutral relabeling. It converged — via an `adr-impl-flow` agent team
resolving two open points (`.claude/skill-runs/adr-impl-flow-decisions/context.md`) — on a single
discipline that reuses detectors cairn already runs. This ADR records that discipline and follows
`intent-contract-cost-model`'s posture: commit the rule, defer the machinery.

## Decision

**D1 — The rule (the decision).** A bug-fix is a **decision-defect** when it can only go green by
*weakening a governing constraint* — i.e. by editing an `INV-xxx` assertion (or the test grounding
it) in `docs/ARCHITECTURE.md`, or by tripping the active intent contract's `must-not-violate` /
`wrong-if`. A decision-defect must be **escalated to a decision** (new / superseding ADR), not
patched at the implementation level. The primary signal is *leading* — it fires on the first patch.

**D2 — Classify by altitude, not source.** Work routes by *level* (decision vs implementation), not
*origin* (ADR vs bug). A bug can be either level; an ADR is usually decision-level. This is a lens
applied at fix-time, not an intake field — the level is discovered through the work, not knowable
upfront.

**D3 — Recurrence backstop (already-practiced).** D1 misses a decision-defect whose first fix looked
clean against every stated constraint. The lagging backstop is **recurrence-by-root-cause**: the
same root-cause class fixed ≥2× is itself an escalation trigger. This names existing practice — the
`cluster:*` GitHub labels and the L-011 promote-on-recurrence idiom — and adds no mechanism.

**D4 — Escalation is operator-driven (now).** The detector surfaces the flag; the **operator**
adjudicates whether to escalate. Automatic triager escalation is **deferred**, gated on triager
hardening (gh#18) and on the detector earning trust. Measure before enforce.

**D5 — Explicit non-commitment (no new machinery now).** This ADR ships **no hook, no field, no
ranker**. The only enforcement artifact — one prompt line in the close-review / Phase-4 brief that
asks the D1 predicate — is deferred and low-priority; it lands when the pattern next bites. A
size/effort annotation for ordering ≥2 competing decision-grade items is explicitly **not** built
(YAGNI; the operator eyeballs the rare tie).

## Consequences

**Easier:**
- Catches the silent-debt failure (patching a wrong decision) using detectors that already exist —
  `validate_architecture.py`, the close-review clause-check, the triager → `/decision` route. Near-zero build.
- Decision-grade problems route to `/decision` instead of accreting as implementation patches, keeping
  the architecture honest so future implementation stays cheap.
- Commits only the rule + reuse; bets nothing on unbuilt machinery — the right posture for an
  unmeasured discipline.

**Harder / honest:**
- **Unwritten-constraint false-negative** (the deep one): a decision-defect on a surface no INV or
  contract clause covers slips *both* signals on the first instance — nothing to "violate." Only
  recurrence (D3, lagging) or a fresh-context reader (intent-challenge / close-review) catches it.
  cairn cannot mechanically close this; it is the natural-language-coverage limit `spec` §49 already
  disclaims. Accepted; lean on fresh-context review.
- **Firmness staleness:** an INV mislabeled `provisional` / `advisory` that is actually load-bearing
  under-escalates. Operator-maintained field = drift surface.
- **Triager is the least-hardened node (gh#18):** the route-up path exists but is under-tested;
  harden before any automatic escalation is leaned on.
- Operator-driven means the discipline depends on the operator running the D1 predicate at fix-time
  until the prompt-line lands.

## Alternatives Considered

- **Static decision/implementation 2×2 taxonomy** (classify every item at intake). *Rejected:* the
  level is usually discovered through the work, not knowable upfront; a taxonomy relabels without
  changing behavior. Replaced by the fix-time checkpoint (D2).
- **Import a prioritization framework** (GTD / Eisenhower / OKR / SpecKit-constitution, or a
  WSJF/RICE-style scored ranker). *Rejected:* foreign to cairn's primitives, and the scored variants
  reintroduce the frozen-weight drift the repo designs out (`board-as-roadmap-substrate` F5). The
  importance/urgency distinction is instead derived from cairn's own decision/implementation levels.
- **Automatic triager escalation now.** *Rejected for now:* depends on gh#18 hardening and an
  unproven detector. Operator-driven first (D4); automate once the signal earns trust. Recorded as
  the active follow-on.
- **Build the size/effort annotation now.** *Rejected:* YAGNI; ties between decision-grade items are
  rare in a single-operator project and eyeballable. Deferred until it bites.
