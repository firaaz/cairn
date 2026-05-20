# Cairn Adaptive Reliability Direction Plan

**Date:** 2026-05-19
**Status:** Direction draft for Claude-side review
**Audience:** next Claude/Codex maintainer session

---

## TL;DR

Cairn should pivot from "a high-consequence four-phase methodology" to an
**adaptive reliability layer for AI-assisted development**.

The durable core is not the workflow ceremony. The durable core is mechanical
reliability: hooks, validators, contracts, and short guidance that make agent
failure modes observable or blocked. The four-phase TDD flow remains available
as the strictest preset, but it should no longer be the product identity.

This plan is a direction-setting artifact, not an implementation plan. The next
session should review the thesis, decide whether to accept it, and then write a
proper ADR/implementation plan.

---

## Problem Statement

The current Cairn framing is too narrow and too heavy:

- "High-consequence only" misses the way projects evolve. Low-stakes prototypes
  often become production tools after habits and architecture are already set.
- Claude Code and Codex now provide native workflow primitives: hooks, skills,
  slash commands, subagents, plugins, MCP, worktrees, cloud tasks, and project
  instructions. Cairn should not compete with those runtimes.
- Recent Trial A and Trial B showed that contracts help, but also that literal
  strictness can become counterproductive when a task legitimately needs enabling
  work outside an artifact's narrow scope.
- Current `dev` is split-brained: handoff template and `/catchup` use the new
  contract-shaped model, while some tests/docs still encode the old sectioned
  handoff model.

The central question for the next session:

> Should Cairn become a graduated reliability system that scales from basic
> hygiene to formal architectural control?

---

## Proposed Thesis

Cairn exists to convert engineering discipline into mechanical guardrails for
AI-assisted development.

It should be useful from day one in ordinary repositories, then scale up when
risk increases. The system should ask:

> What is the cost of the agent being confidently wrong on this change?

Not:

> Is this project important enough for Cairn?

---

## Tier Model

### Tier 0 — Hygiene

Default for almost every repository.

Purpose: prevent common damage with minimal ceremony.

Guardrails:

- block destructive commands
- protect `.env*` and lock files
- block `git push --force`; allow `--force-with-lease`
- run format/lint hooks where configured
- fail loudly when hook dependencies are missing
- maintain a tiny handoff/current-state pointer

Use when:

- docs, formatting, isolated edits, experiments
- no user-facing/data/security impact
- rollback is easy

### Tier 1 — Scoped Work

Default for normal feature/bug work.

Purpose: keep agents from sprawling beyond the intended change.

Guardrails:

- file/path envelope
- required verification command
- short task summary or task contract
- explicit envelope expansion trail

Use when:

- behavior changes
- multiple files are touched
- tests/config/build files are edited
- rollback is possible but non-trivial

### Tier 2 — Contracted Work

Default when correctness depends on intent, not just code.

Purpose: make review attach to falsifiable clauses rather than prose.

Guardrails:

- `must-satisfy`
- `must-not-violate`
- `wrong-if`
- `evidence`
- deterministic contract tests where possible
- ADR-lite or decision note when needed

Use when:

- requirements are ambiguous
- user-facing workflow changes
- public API/schema/data model changes
- tests could pass while intent is still wrong
- future maintainers need to understand why

### Tier 3 — Formal Flow

Strict mode for changes whose mistakes compound.

Purpose: protect architectural, security, data, and irreversible boundaries.

Guardrails:

- append-only ADR or supersession
- architecture invariant update
- strict envelope
- independent review or phase separation
- full validator/test evidence
- optional four-phase TDD flow

Use when:

- architecture/invariant changes
- irreversible migrations
- security/privacy/auth/billing boundaries
- cross-service integration
- long-lived decisions future work depends on
- multiple agents/sessions/branches coordinate on the change

---

## Tier Selection Heuristic

Start every task at Tier 0, then add one point for each trigger:

- touches production behavior
- touches data/security/auth
- changes public API/schema/config/deploy
- spans 3+ files or 2+ subsystems
- hard to rollback
- requirements are ambiguous
- creates a precedent future work depends on
- multiple agents or sessions will work on it
- tests could pass while intent is still wrong

Recommendation:

- 0-1 points: Tier 0
- 2-3 points: Tier 1
- 4-5 points: Tier 2
- 6+ points: Tier 3

Hard override to Tier 3:

- security/privacy boundary
- destructive or irreversible migration
- architecture invariant change
- production incident remediation

The human may override the recommendation, but the tool should display the
reasons and required guardrails before work proceeds.

---

## Relationship To Current Work

This direction should absorb the current interaction-protocol work:

- Trial A handoff contract becomes a Tier 0/Tier 1 current-state primitive.
- Trial B ADR contract becomes a Tier 2/Tier 3 artifact-contract primitive.
- The "works, but might be too strict" verdict becomes evidence for separating
  artifact-level scope from execution-level enabling work.
- The current stale tests should be updated toward the new contract-shaped model,
  not used as evidence to revert to the old sectioned handoff.

Current `dev` failures observed on 2026-05-19:

- `test_context_discipline_protocol.py::test_v1_handoff_template_exists_and_is_tight`
  still expects old `slice/phase/branch/as-of` frontmatter and four body sections.
- `test_feature_skill_conformance.py::TestHandoffCrossFeatureIndex` still expects
  a `## Features` section.
- `test_invariant_assertions.py` still expects invariants only through INV-010,
  while `ARCHITECTURE.md` has INV-011 and INV-012.

These are migration failures, not evidence that the new direction is wrong.

---

## Proposed Next Slice

Name: `adaptive-reliability-rebaseline`

Goal: make the tiered reliability thesis explicit and get `dev` internally
consistent again.

Scope:

1. Write an ADR or design decision establishing adaptive risk tiers.
2. Update `docs/operational-reference.md` so Cairn's primary mental model is
   graduated guardrails, not high-consequence-only workflow.
3. Rebaseline `docs/ARCHITECTURE.md` INV-002 around contract-shaped handoff.
4. Update stale tests that still enforce the old sectioned handoff.
5. Update invariant assertion coverage to include INV-011 and INV-012, or derive
   expected ids from `ARCHITECTURE.md` rather than hardcoding the old range.
6. Keep the four-phase workflow as Tier 3 optional machinery.

Non-goals:

- no new orchestrator
- no AI risk classifier
- no broad plugin-distribution rewrite
- no attempt to support all Claude/Codex adapter details in this slice
- no retrofitting all historical ADRs/features beyond what tests require

---

## Future Implementation Shape

After the rebaseline, implement the tier system in small pieces:

1. `scripts/assess_risk_tier.py`
   - deterministic preflight tool
   - reads changed paths and optional task text
   - outputs recommended tier, reasons, and required guardrails

2. `templates/task-contract.yaml`
   - tiny Tier 1/Tier 2 contract shape
   - distinct from full ADR contract

3. Hook integration
   - Tier 0 always-on safety
   - Tier 1 envelope enforcement
   - Tier 2 contract evidence checks
   - Tier 3 ADR/invariant validation

4. Adapter guidance
   - Claude Code: plugin/skills/hooks first
   - Codex: `AGENTS.md`, scripts, tests, hooks where available
   - shared core remains plain files and deterministic validators

---

## Questions For Claude Review

1. Does the tier model solve the adoption problem without diluting Cairn's
   reliability promise?
2. Are Tier 0 and Tier 1 valuable enough for ordinary repositories?
3. Is Tier 3 still meaningfully different from "just use Claude/Codex carefully"?
4. Should tiers be selected by deterministic scoring, user declaration, or both?
5. What is the smallest slice that proves this direction without re-opening the
   full methodology design?
6. Which current docs/tests must be rebaselined first so `dev` is coherent?

---

## Recommended Claude Session Prompt

Use this as the opening instruction in the Claude instance:

> Review `docs/plans/2026-05-19-adaptive-reliability-direction.md` as a product
> direction change for Cairn. Evaluate whether Cairn should pivot from a
> high-consequence four-phase methodology to adaptive reliability tiers. Compare
> this against current Claude Code and Codex primitives. Produce a decision:
> accept, amend, or reject. If accepted, propose the next slice scope that makes
> `dev` internally consistent without building new machinery.

