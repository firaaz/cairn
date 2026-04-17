---
id: phase-pipeline-evaluation
status: accepted
firmness: firm
supersedes: []
supersedes-sections: []
superseded-by: null
topic: process
invariants-touched: [INV-003]
date: 2026-04-13
---

# phase-pipeline-evaluation: Phase Pipeline Evaluation — Confirmation of Four-Phase Structure

## Context

phase-lock-and-role-declaration locked the slice pipeline at four phases (Intent → Validation → Implementation → Integration) with named roles (Reader, Skeptic, Builder, Auditor) after two slices of experience. Since phase-lock-and-role-declaration's acceptance, three additional slices have shipped (SLICE-003 through SLICE-005), exercising the pipeline across both code-producing and non-code work. Before roadmap item 2 (protocol extraction to `protocols/phase-N-<role>.md`) bakes the current phase shape into standalone files, this evaluation assesses whether the abstraction level remains correct.

This ADR evaluates the phase count and names, role flexibility across work types, ceremony calibration, and protocol extraction readiness against observed evidence from five completed slices.

## Evaluation

### 1. Phase count and names

**Finding: The four phases remain correct. The phase names are load-bearing.**

The number of phases maps to four distinct cognitive modes that resist compression. Intent (what/why) must be separated from Validation (adversarial test design) to maintain the correlated-error defense — merging them would allow the intent author to unconsciously bias test coverage. Validation must be separated from Implementation because the Skeptic's independence from implementation reasoning is the core defense property (cliff-failure-mode-and-v1-defenses D1/D2). Integration exists as a terminal audit gate with different incentives than the Builder who wrote the code.

Evidence from non-code slices confirms the four phases carry their weight even when no source code is produced:

- SLICE-003 operationalized phase-lock-and-role-declaration's D2/D3/D4 decisions across three Markdown protocol files. All four phases executed with role-specific skill application. Phase 2 produced 7 tests (6 RED + 1 GREEN canary) against documentation changes, demonstrating that Validation works for non-code artifacts.
- SLICE-005 produced four new ADRs (semantic-identity through context-tiers-integration) with zero source code. Phase 2 generated an 18-test validation suite; Phase 4 verified 7 invariants across 8 ADRs with file:line evidence. The full ceremony completed without ceremony-reduction workarounds.

The phase names (Intent/Validation/Implementation/Integration) are occasionally awkward for non-code work — "Implementation" for writing an ADR sounds like a category error — but renaming carries a high migration cost (6 files reference phase names: `catchup.md`, `start-slice.md`, `scope-guard.sh`, `reality-check.sh`, `operational-reference.md`, `slice.yaml`) for marginal clarity gain. The names are understood by operators as role-boundary markers, not literal descriptions.

### 2. Role flexibility

**Finding: Reader, Skeptic, Builder, and Auditor map to all observed work types without becoming vacuous.**

The concern was that roles designed for code-producing slices might become vacuous for non-code categories. Evidence does not support this:

- SLICE-003 (non-code protocol documentation): The Reader produced intent constrained to protocol changes. The Skeptic wrote tests against Markdown structure and content. The Builder implemented the protocol edits. The Auditor verified invariant compliance with file:line citations.
- SLICE-004 (code-producing instrumentation): Standard role application — Reader scoped the dogfood harness, Skeptic wrote 18 tests, Builder implemented `dogfood_evaluate.py`, Auditor verified 4 invariants across 4 ADRs.
- SLICE-005 (non-code, 4 ADRs): All four roles carried substantive work. Phase 4 caught a pre-existing dirty file from SLICE-003, demonstrating the Auditor role catches cross-slice contamination even in non-code work.

The roles achieve flexibility not through different definitions per work type but through the Phase Skill Guide (phase-lock-and-role-declaration D4), which adapts the skill mapping while keeping role names and anti-behaviors stable. This separation of fixed roles from flexible skill assignments is the mechanism that makes the roles non-vacuous across all categories of work.

### 3. Ceremony calibration

**Finding: No phase should be skippable. Lightweight ceremony is achievable within the existing structure.**

The temptation is to allow skipping phases for "simple" work. The evidence argues against this:

- SLICE-003's Phase 2 escalated three ambiguities (ADR slug resolution, V6 plurality testing, dry-run fixture design) that would have been silent bugs without the Skeptic's adversarial pass. This was a "simple" protocol documentation slice where ceremony seemed heaviest relative to output size.
- SLICE-005's Phase 4 caught a pre-existing dirty measurement file that would have propagated as technical debt without the Auditor's integration sweep.
- SLICE-004's Phase 3 implementation notes record 3 minor decisions (verdict priority order, YAML parsing strategy, duplicate detection key) that were already implicit in Phase 2's test contracts — the ceremony forced these decisions to be recorded rather than silently made.

The right calibration is not fewer phases but lighter ceremony within phases. Phase 2 for a documentation slice produces fewer tests than Phase 2 for a complex feature — the ceremony adapts naturally through the Skeptic's judgment about what needs adversarial coverage. phase-lock-and-role-declaration's structure already permits this: nothing mandates a minimum test count or a minimum Phase 3 implementation size.

### 4. Protocol extraction readiness

**Finding: The phase shape is stable enough for protocol extraction to `protocols/phase-N-<role>.md` (roadmap item 2).**

The evaluation across five slices shows:

- Zero phase-count or phase-name changes needed
- Zero role redefinitions needed
- The Phase Skill Guide (D4) is the only component that has evolved, and it is explicitly documented as a living registry independent of ADR supersession

Protocol extraction can proceed with confidence that the extracted protocols will not require immediate revision. The extraction readiness is confirmed: the phase shape has survived both code-producing (SLICE-004) and non-code (SLICE-003, SLICE-005) slices without structural modification.

## A2 Tripwire Evaluation

**A2 tripwire status: NOT FIRED.**

The A2 tripwire (phase-lock-and-role-declaration Risk Register) monitors whether the Phase 1→Phase 2 session boundary provides sufficient isolation to prevent smuggled implementation reasoning. The mechanical test: if more than 1 slice in any rolling 10-slice window has novel design tokens in `approach.md` absent from `intent.md`, the tripwire fires.

**Evidence evaluated**: SLICE-003 through SLICE-005 (the slices with Phase 2 `approach.md` artifacts under phase-lock-and-role-declaration's regime).

- SLICE-003: Phase 2's approach.md resolved ambiguities by reference to phase-lock-and-role-declaration and ARCHITECTURE.md. Design tokens (ADR slug glob pattern, plurality rule phrasing) originated in intent.md's specification items, not in smuggled implementation reasoning.
- SLICE-004: Phase 2's 18 tests target the dogfood harness interface declared in intent.md. Implementation notes show 3 minor decisions (verdict priority, YAML parsing, duplicate key) that were implicit in Phase 2's test contracts — indicating the Skeptic worked from the intent, not from leaked design.
- SLICE-005: Phase 2's 18-test suite covered 4 ADRs' structural requirements. No design token leakage detected; Phase 4's integration sweep confirmed clean phase boundaries.

**Finding**: 0 of 5 slices in the current window show design token leakage from intent to approach. The A2 canary has not fired. The Phase 1→Phase 2 session boundary is providing the isolation phase-lock-and-role-declaration assumed.

## Confirmation Justification

This ADR confirms phase-lock-and-role-declaration rather than superseding it. What has changed since phase-lock-and-role-declaration to justify re-confirmation rather than mere acceptance:

**New evidence from three additional slices shipped since phase-lock-and-role-declaration**: At the time of phase-lock-and-role-declaration's acceptance, only SLICE-001 and SLICE-002 had exercised the pipeline — both code-oriented, both from the initial dogfood period. The concern was that the four-phase structure might not survive contact with non-code work. Since phase-lock-and-role-declaration:

- SLICE-003 demonstrated the pipeline works for protocol documentation (non-code, Markdown-only output)
- SLICE-004 demonstrated it works for instrumentation tooling (code-producing, Python script)
- SLICE-005 demonstrated it works for multi-ADR design work (non-code, four ADRs as output)

This diversity of work types — none of which existed as evidence when phase-lock-and-role-declaration was written — is the new evidence that transforms phase-lock-and-role-declaration from a reasonable bet into an empirically supported decision. The confirmation is warranted because the five slices shipped collectively demonstrate that the four-phase structure, role definitions, and ceremony expectations are not merely self-consistent but actually function across the work types that prompted the evaluation.

## Consequences

- phase-lock-and-role-declaration's D1 (four phases), D2 (named roles), D3 (pre-decision immutability gate), and D4 (Phase Skill Guide) remain in force without modification
- Roadmap item 2 (protocol extraction) may proceed against the current phase shape
- The Phase Skill Guide in `docs/operational-reference.md` remains the correct location for work-type-specific ceremony guidance; no new ceremony-calibration mechanism is needed
- The A2 tripwire remains active; next evaluation due at SLICE-010 or upon any observed design token leakage
- INV-003 (phase count/names/surfacing lock) is reaffirmed by this evaluation
