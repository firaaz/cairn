# Phase 0 — Constraint Harvest

## Hard constraints (any branch must respect)

- **INV-002 is firm and machine-bound via test-ref.** `docs/ARCHITECTURE.md:23-27`; binding 53a7c58. Handoff frontmatter (four required sections, token budget 150–400) enforced by `tests/unit/test_handoff_contract.py`. Cannot be amended without ADR supersession. (context-discipline-protocol, invariant-binding-strategy)

- **INV-003 phase topology locked at four phases.** `docs/ARCHITECTURE.md:30-36`; Intent (Reader) → Validation (Skeptic) → Implementation (Builder) → Integration (Auditor). Phase names and roles immutable; changes require phase-lock-and-role-declaration supersession. (phase-lock-and-role-declaration)

- **INV-005 identifier scheme is firm: entities carry immutable `id:` and mutable `name:`.** `docs/adr/identifier-scheme.md:6-28` (accepted 2026-04-15). Contract block enforced by `tests/unit/test_identifier_scheme_contract.py` (Trial B T1–T6). Supersedes semantic-identity. (identifier-scheme)

- **INV-006 feature-slice model is firm.** `.claude/features/<id>.yaml` carries required fields: `id`, `name`, `intent`, `shaped-from`. No `epic:` field. Schema amendment requires N≥3 independent features per schema-amendment-threshold/D2. (feature-slice-model, schema-amendment-threshold)

- **Trial A (2026-05-13, commit 53a7c58) locked in.** Handoff-as-pointer protocol replaced sectioned-narrative. Context-discipline-protocol three-tier model committed. Cannot be superseded without ADR supersession. (context-discipline-protocol)

- **Trial B (closed 2026-05-14, verdict a0e3fe6) landed identifier-scheme contract block.** `tests/unit/test_identifier_scheme_contract.py` T1–T6 enforce D1+D2+D3+D5+D9 against filesystem. Deferred: legacy-label retrofit (10 of 33 ADRs lack `name:` or `title:`; advisory ceiling captured). (identifier-scheme contract, Trial B spec)

- **Trial B verdict: "works, but might be too strict."** Commit a0e3fe6: plan-level contract's must-not-violate ("no new files outside ADR + test file") conflated artifact-scope with execution-scope. /decision arc (feature-schema-d5-reconciliation) legitimately landed ADR (schema-amendment-threshold), lesson (L-024), ARCHITECTURE.md edits. Trial bent rather than stopped. Implication: next trial must distinguish artifact-scope from execution-scope in contract. (a0e3fe6 message)

- **Schema amendment via N≥3 trigger is firm.** `docs/adr/schema-amendment-threshold.md:49-61` (firm, 2026-05-14). N=1: migrate + watching-mark. N≥3: WIDEN via supersession default. Watching-mark filed: orchestrator-paths instance 1/3. (schema-amendment-threshold/D2–D4)

- **Invariant-binding-strategy validator types firm:** git-log-walk (INV-001, 2fb83f6), structural-parser reserved. Both codified as implemented in ARCHITECTURE.md. (invariant-binding-strategy/D1–D3)

## Soft constraints / preferences (operator-revealed)

- **Trial B "too strict" verdict signals contract-shape refinement is in scope.** Artifact-scope / execution-scope conflation is latent failure mode in contract pattern itself, not one-off trial bug. TIGHTEN-FIRST would surface issues before extending to slice intent. (a0e3fe6)

- **Plan-level contracts should enumerate enabling work.** Per a0e3fe6: "Either enumerate permitted enabling work, or split must-not-violate into artifact / execution clauses with different escalation rules." (a0e3fe6 implication)

- **Slice intent is "most-LLM-authored, most-prone-to-drift artifact."** `00-question.md:8`. TRIAL-C's rubber-stamp target. Implies contract must catch semantic drift, not just presence/absence. (decision-question)

- **Retrofit of legacy ADR names deferred post-Trial-B.** 14 ADRs missing `name:` (10 with neither `name:` nor `title:`), baseline `LEGACY_LABEL_BASELINE = 10` captured in test. Single-instance drift doesn't trigger amendment; retrofit happens next /decision or when baseline pressure mounts. (Trial B spec, L-024)

- **6 slice-id violations predate identifier-scheme** (4 compression.yaml uppercase Y/Z, 1 housekeeping.yaml dots for CC version, 1 orchestrator-paths prefix mismatch). Advisory ceiling `LEGACY_SLICE_ID_BASELINE = 6` captured. Deeper reconciliation deferred. (Trial B audit)

## Constraints by branch

### RETROFIT
- Applies Trial B contract pattern to legacy artifacts violating identifier-scheme.
- **In scope:** 14 ADRs missing `name:`, 6 slice-id violations, Trial B audit drift.
- **Out:** TRIAL-C, TIGHTEN-FIRST.
- **Risk:** Defers "too strict" signal indefinitely. No test on slice intent; no contract-shape refinement before extension.

### TRIAL-C
- Advances to slice `intent.md` produced by Phase 1 (highest-friction test).
- **In scope:** Intent contract block, test suite, binding to Phase 1+ slices.
- **Precondition:** Plan-level contract must carve out enabling-work per a0e3fe6 (avoid "too strict" recurrence).
- **Risk:** Intent signature detection harder than file-state checks. Trial B's deterministic clauses (id shape, presence, cross-refs) may not transfer. Tests harder to make non-flaky. Tight intent contract may over-constrain Phase 1 output beyond pointer-format handoff.

### TIGHTEN-FIRST
- Refines contract-block shape before extending to slice intent.
- **In scope:** Amend identifier-scheme contract (relax mandatory keys, introduce versioning, separate must-satisfy/must-not-violate granularity, add enabling-work clause).
- **Risk:** Increases binding-state churn before second/third instance validates shape. Delays learning from TRIAL-C's higher-friction surface. In-place edit (frontmatter-only, reversibility-guard.sh allows) but requires subsequent supersession if definition changes.
- **Implication:** Blocks TRIAL-C until landed. RETROFIT independent (parallel-eligible).

## Cross-cutting risks surfaced

- **Contract-shape brittleness.** "Too strict" verdict signals artifact-scope/execution-scope conflation is structural, not one-off. Unless TIGHTEN-FIRST or TRIAL-C plan explicitly resolves, both branches inherit risk. (a0e3fe6, Trial B verdict section)

- **Slice-intent semantic drift detection.** Trial B template: deterministic checks (presence, shape, refs). Intents carry semantic content ("why needed, success criteria, decision bounds"). Detecting semantic drift is harder; high false-positive / false-negative risk. (00-question.md:8)

- **Enabling-work scope creep.** /decision arc (feature-schema-d5-reconciliation) legitimately needed extra artifacts but plan-level contract had no carve-out. If RETROFIT/TRIAL-C lack explicit enabling-work clause, same tension recurs. Boundary between "trial artifact scope" and "work to resolve surfaced issues" is informal unless escalation rules explicit. (a0e3fe6, memory note: setup_task_decision_weight)

- **Identifier-scheme locked via INV-005, context-discipline via INV-002, phase topology via INV-003.** Any branch amending underlying ADRs requires supersession. TIGHTEN-FIRST's contract amendment must supersede if changes D1+D2+D3+D5+D9. TRIAL-C must not contradict INV-002/INV-003. RETROFIT orthogonal (operational, no ADR changes). (ARCHITECTURE.md invariants, identifier-scheme status:accepted)
