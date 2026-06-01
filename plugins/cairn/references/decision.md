# /decision

Make an architectural decision with structural safeguards against correlated errors.

Usage: `/decision <question>`

## Rules

1. Use for decisions that become ADRs — invariants, boundaries, data ownership, module structure.
2. Phase 0 — Constraint Harvest: read ARCHITECTURE.md invariants, relevant ADRs, lessons.md. Produce constraint envelope with source citations.
3. Phase 0.5 — User-Journey Trace: walk the enabled workflow end-to-end. Every session/artifact/state boundary must have a mechanism.
4. Phase 1 — Pre-Mortem: ≥3 failure scenarios (technical, scale, integration) BEFORE proposing solutions.
5. Phase 2 — Forced Enumeration: ≥3 genuinely viable approaches. Comparison table with constraint fit, pre-mortem exposure, downstream impact. Evidence from files, not memory.
6. Phase 3 — Adversarial Stress Test: disconfirming search, steel-man runner-up, audit every assumption (verified vs believed).
7. Phase 4 — Write ADR via `/new-adr` with context, decision, consequences, alternatives, risk register.
8. Phase 5 — Independent Verification (firm only): fresh context reruns Phases 1-3 without your reasoning. Compare conclusions.
9. Phase 6 — Propagation: `/refresh-architecture`, check in-progress slices, update superseded ADRs, record patterns in lessons.md.

## Load full

- If running Phase 2 forced enumeration: read decision.full.md for the comparison table template and evidence-citation rules.
- If running Phase 5 independent verification for a firm decision: read decision.full.md for the verification protocol and outcome classification.
