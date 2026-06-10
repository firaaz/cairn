---
id: context-tiers-integration
title: Context Tiers Integration for Feature-Slice Model
status: accepted
contract:
  must-satisfy:
    - "feature artifacts respect the three-tier context model (carrier: scripts/validate_architecture.py INV-007)"
  evidence:
    - "uv run python scripts/validate_architecture.py"
firmness: firm
supersedes: []
supersedes-sections: []
superseded-by: null
topic: process
invariants-touched: []
date: 2026-04-12
---

# context-tiers-integration: Context Tiers Integration for Feature-Slice Model

## Status
Accepted

## Date
2026-04-12

## Context

context-discipline-protocol established a three-tier context discipline protocol governing session-to-session context transfer. The protocol was designed for single-slice, single-feature work:

- **Tier 1** (always loaded): `handoff.md`, `slice.yaml`, `sweep.yaml`, `git log --oneline -5`, `git status --short`. Target: 150–400 token budget for handoff.
- **Tier 2** (on-demand via subagent): Files named in handoff pointers, loaded only when admission criteria are met.
- **Tier 3** (working context): Normal file reading once the user gives a direct work imperative.

The feature-slice model (feature-slice-model) introduces new artifacts — feature files at `.claude/features/<id>.yaml` — and new state relationships — multiple active features, multiple slices per feature, cross-feature dependencies. These must integrate into context-discipline-protocol's tier model without regressing the context budget or collapsing the admission criteria.

The key question is whether INV-002 (the invariant pairing context-discipline-protocol's protocol commitments) needs amendment to accommodate the feature-slice model's new artifacts.

## Decision

### D0 — Feature-slice artifacts map to existing tiers

The feature-slice model's artifacts integrate into context-discipline-protocol's three tiers without creating a new tier:

**Tier 1 — handoff.md gains a cross-feature index.** `handoff.md` on the dev branch includes a cross-feature index: one line per active feature with the feature ID and current status. This stays within context-discipline-protocol's 150–400 token budget because each feature entry is a single line (~15–25 tokens). At the expected v1 scale (2–5 concurrent features), the cross-feature index adds 30–125 tokens — well within the existing budget ceiling.

**Tier 2 — feature file loaded on-demand.** When entering a feature's branch, the feature file (`.claude/features/<id>.yaml`) is loaded as a Tier 2 read. The admission criteria from context-discipline-protocol Layer 2 apply: the feature file is loaded only when the user directs entry into a specific feature's work (admission criterion 2: "User directed entry into a specific pipeline phase and the handoff pointers explicitly list files for that phase") or when verifying decomposition state before acting (admission criterion 3). The feature file is NOT loaded during Tier 1 orientation — its detail is decomposition context, not session-state context.

**Tier 3 — slice.yaml on active branch (unchanged).** `slice.yaml` remains the working-context artifact. When a user issues a direct work imperative on a slice, normal file reading resumes — including the feature file if needed for dependency context. This is unchanged from context-discipline-protocol.

### D1 — Feature inventory for Tier 1 derived from handoff

The cross-feature index in `handoff.md` is the source of truth for Tier 1 feature inventory. `/catchup` Tier 1 reads the index to report active features without loading any feature files. Feature files are Tier 2 depth — they are never loaded in Tier 1 regardless of how many features are active.

This preserves context-discipline-protocol's Tier 1 invariant: a bounded, predictable context load at session start that does not scale with the number of active features or slices.

### D2 — INV-002 accommodates this without amendment

INV-002 (paired with context-discipline-protocol) commits to: handoff token budget of 150–400 tokens, tiered catchup with admission-gated reads, and slice closure wipe. The feature-slice model's integration does not violate any of these commitments:

- The cross-feature index in handoff stays within the 150–400 token budget at expected scale.
- Feature files are gated by existing Tier 2 admission criteria — no new admission path is introduced.
- Slice closure wipe (context-discipline-protocol Layer 3) is unaffected — feature files live on the feature branch, not in `.claude/current-slice/`.

INV-002 does not require amendment. The feature-slice model operates within the protocol's existing commitments.

### D3 — Token budget monitoring

If the cross-feature index grows beyond 5 features and threatens the 400-token ceiling, the index entries are condensed (shorter descriptions, abbreviations) before considering a budget amendment. A budget amendment — raising the ceiling — requires a superseding ADR because it would modify context-discipline-protocol's firm commitment. The expected v1 scale (2–5 features) does not require this.

## Consequences

- **context-discipline-protocol's token budget is preserved.** The 150–400 token budget for `handoff.md` accommodates the cross-feature index at v1 scale without amendment.

- **No new tier is introduced.** Feature files map cleanly to Tier 2 (on-demand depth), avoiding the complexity of a four-tier model.

- **`/catchup` gains feature-awareness.** Tier 1 orientation reports active features from the handoff index. Tier 2 dispatch loads feature file detail when entering a feature's work. The implementation slice updates `/catchup` to read the cross-feature index.

- **`/handoff` gains a cross-feature index section.** The implementation slice updates `/handoff` to write a cross-feature index line per active feature. The handoff template is extended with the index section.

- **INV-002 remains stable.** Downstream work that depends on INV-002's commitments (including integration-sweep checks for handoff token budget compliance) is unaffected.

- **Scalability ceiling is explicit.** Beyond ~5 concurrent features, the token budget may bind. This is named as a known limit, not a defect — v1 targets small-team / solo-developer scale where 2–5 concurrent features is the expected operating range.

- **context-discipline-protocol reference preserved.** This ADR references context-discipline-protocol's three-tier model and token budget (150–400 tokens) as the integration target. Future changes to context-discipline-protocol's tier model or budget require reviewing this ADR for compatibility.
