---
id: schema-amendment-threshold
name: "Schema amendment threshold — N≥3 trigger; D5 default-permit reading"
status: accepted
contract:
  must-satisfy:
    - "feature-file schema widening stays below the amendment threshold (carrier: scripts/validate_architecture.py INV-006)"
  evidence:
    - "uv run python scripts/validate_architecture.py"
firmness: firm
supersedes: null
supersedes-sections: []
superseded-by: null
topic: process
invariants-touched: [INV-006]
date: 2026-05-14
---

# schema-amendment-threshold: Schema amendment threshold — N≥3 trigger; D5 default-permit reading

## Status

Accepted, firm. Phase 5 independent verification required.

## Date

2026-05-14

## Context

Trial B of the cairn interaction-protocol reframe (`docs/plans/2026-05-14-cairn-adr-contract-trial-b.md`) bound a `contract:` block to `docs/adr/identifier-scheme.md` and shipped invariant tests for D1–D5, D9. T5 (`test_d5_feature_files_well_formed`) discovered that `.claude/features/orchestrator-paths.yaml` uses a richer schema than identifier-scheme/D5 prescribes:

- Replaces `intent:` with `charter:`
- Omits `shaped-from:`
- Adds 6 fields not enumerated in D5: `status`, `tracking`, `predecessor`, `lesson`, `audit-findings`, `out-of-scope`

9 of 10 active feature files conform to D5. orchestrator-paths.yaml is the lone outlier; its schema deviation arose in a single Phase-2 commit (`df8ba20`) with no documented rationale, suggesting drafting under context pressure.

The drift surfaced two questions:

1. **Interpretive:** Is identifier-scheme/D5 default-permit (extras are silently advisory) or default-deny (extras are forbidden)? D5's text lists required fields and names exactly one rejection (`epic:`); it does not say "and only these fields are permitted."
2. **Procedural:** When does single-file schema drift justify amending a firm ADR (WIDEN) versus migrating the file to conform (NARROW)?

A full /decision arc was conducted (records in `.claude/skill-runs/feature-schema-d5-reconciliation/`). Phase 0 confirmed no code in `checks/`, `scripts/`, hooks, or skills reads feature-file fields at runtime — D5 is purely advisory. Phase 1 surfaced six failure scenarios; risk asymmetry favored NARROW. Phase 2 enumerated three approaches: NARROW pure (drop extras), WIDEN via identifier-scheme-v2 supersession, HYBRID (NARROW + lesson with N≥3 trigger). Phase 3 stress-tested HYBRID and confirmed it survives.

## Decision

### D1 — D5 default-permit interpretation

identifier-scheme/D5 reads as default-permit: feature files MUST carry `id`, `name`, `intent`, `shaped-from`. Fields beyond this required set are advisory unless explicitly named-rejected (`epic:` is the sole current rejection).

This interpretation is documented here so the question is not litigated again per file. If a future /decision adopts default-deny, this ADR is superseded.

### D2 — Schema-amendment threshold (N≥3)

A firm schema ADR (e.g., identifier-scheme/D5) is NOT amended on the basis of a single feature file's drift. WIDEN via supersession is invoked when **N≥3 independent features each need the same non-schema field, AND each cannot satisfy the need via an adjacent artifact** (slice metadata, lessons.md, plan doc, ADR note).

"Independent" means different author contexts, different slice arcs — coincidental co-drift is not pattern.

"Need" means the field carries data with no canonical alternative home — not that the author found it convenient.

The protocol:

1. **First non-conforming feature** (N=1): migrate to schema; record the candidate non-schema fields in `docs/lessons.md` as a watching-mark with field names and counts.
2. **Second non-conforming feature** (N=2) using same non-schema fields: file a new /decision to reassess, but presumption remains NARROW.
3. **Third non-conforming feature** (N=3): WIDEN via supersession is the default; /decision evaluates whether to adopt.

The N=3 threshold mirrors cairn precedent (L-011 — recurrence count for mechanical-fix promotion).

### D3 — Application to orchestrator-paths.yaml

orchestrator-paths.yaml is N=1. Migration:

- Rename `charter:` → `intent:`
- Add `shaped-from:` (use `predecessor: substrate/root-resolver` value as provenance)
- Add `created:` (git-derived initial commit date)
- Remove slice-entry `status: phase-1` (independently violates `tests/unit/test_feature_file_schema.py:73-76`)
- **Retain** `tracking`, `predecessor`, `lesson`, `audit-findings`, `out-of-scope`, top-level `status` as unvalidated advisory fields per D1

### D4 — Lesson capture

Append L-024 to `docs/lessons.md` recording the N≥3 protocol and the orchestrator-paths.yaml watching-mark (instance 1/3 for fields: `tracking`, `predecessor`, `lesson`, `audit-findings`, `out-of-scope`, `status`). Future authors encountering the impulse to add non-schema fields consult L-024 for protocol.

### D5 — Trial B test design

`test_d5_feature_files_well_formed` (Trial B T5) checks ONLY that the four required keys are present in `.claude/features/*.yaml` files. Extras are not enforced positively or negatively.

## Consequences

**Easier:**

- Future schema-drift surfacing: clear protocol (D2) replaces ad-hoc judgment.
- D5 firmness preserved — the methodology claim "firm ADRs are firm until ceremony" is intact (Trial B itself is dogfooding contract-as-protocol; this decision keeps that contract honest).
- orchestrator-paths.yaml's audit-findings cross-reference (F-039–F-050) survives migration at zero relocation cost.
- Trial B T5–T8 unblock and resume.

**Harder:**

- Operators must remember to file watching-marks when N=1 drift appears. Mechanism is prose-only, not enforced.
- The D5 default-permit reading depends on text interpretation; a future operator could reasonably read D5 as default-deny and challenge this ADR. Mitigated by recording the interpretation here as the canonical reading.
- "Adjacent artifact" criterion in D2 is a judgment call — what counts as a canonical home for displaced data is not enumerated.
- N=3 threshold is conventional (mirrors L-011), not derived. May be wrong direction for high-importance single instances; revisable.

## Alternatives Considered

**Alternative A — NARROW pure (drop extras).** Migrate orchestrator-paths.yaml fully to D5; drop the 6 non-schema fields outright. Rejected because audit-findings F-039–F-050 has no canonical relocation home and would be lost from live cross-reference (only preserved in git history). Pre-mortem Scenario 4 (`03-premortem.md:38-43`).

**Alternative B — WIDEN via identifier-scheme-v2 supersession.** Author a new ADR canonizing `charter:` and the 6 extra fields as enumerated optional. Rejected on three counts: (1) inverts D5's minimal-schema philosophy, expanding for one outlier; (2) opens long-term ad-hoc field proliferation (Scenario 3) by demonstrating that single-file drift triggers schema amendment; (3) introduces the `charter:`/`intent:` alias risk (Scenario 6). The supersession-form would mitigate the firmness-credibility concern (Scenario 5), but the cost-benefit doesn't justify a new ADR for a schema with zero mechanical consumers.

**Alternative D — Stop trial; defer reconciliation indefinitely.** Block Trial B without resolution. Rejected because Trial B is itself the methodology test that validates the contract-as-protocol claim; deferring its blocker undermines the dogfood arc and provides no mechanism for resumption.

## Risk Register

Per Phase 1 pre-mortem (`03-premortem.md`):

| Scenario | Severity | This ADR's handling |
|----------|----------|---------------------|
| S1: test extension breaks live files | Likely / small | Migration aligns orchestrator-paths.yaml to D5 BEFORE any live-test extension. Resolved. |
| S2: slice-entry `status: phase-1` violation | Likely / small | D3 explicitly removes the slice-entry status field. Resolved. |
| S3: ad-hoc field proliferation under WIDEN | Likely-at-scale / medium | D2 N≥3 threshold prevents single-instance amendment. Mitigated. |
| S4: audit-findings cross-ref loss | Possible / medium | D3 retains audit-findings as advisory per D1 default-permit. Mitigated. |
| S5: firmness claim undermined by in-place ADR edit | Possible / large | D5 unchanged; no firm ADR amended. Resolved. |
| S6: charter alias ambiguity | Possible / medium | charter: removed during migration; no alias introduced. Resolved. |

**Forward risks introduced by this ADR:**

- **R1:** Future strict-validation tooling could read D5 as default-deny, invalidating retained advisory fields. Mitigation: L-024 names this scenario; relocation to canonical homes occurs at that decision point.
- **R2:** N=3 threshold may be wrong direction (too high or too low). Mitigation: this ADR is firm but revisable via standard supersession; first counter-evidence triggers re-evaluation.
- **R3:** Watching-mark protocol is prose-enforced; an operator may not file the mark, defeating the counting mechanism. Mitigation: include "file watching-mark" as a step in any /decision template that touches schema drift.
