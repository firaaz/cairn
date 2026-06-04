---
id: intent-management-loop
name: "Intent-management loop — coexisting thin-cairn path, retirement gated on Trial E"
status: accepted
firmness: provisional
supersedes: null
superseded-by: null
resolved-by: trial-e-closure-adjudication
topic: architecture
invariants-touched: []
date: 2026-05-31
---

# Intent-management loop — coexisting thin-cairn path, retirement gated on Trial E

## Status

Accepted (post-`/decision` arc `thin-cairn-intent-management`, 2026-05-31; operator-selected
Approach A1 over runner-up A2 and rejected A3, after Phases 0–3). **Provisional** — this ADR
supersedes nothing and modifies no invariant, so Phase 5 independent verification is not
required for it. The *future retirement* ADR (D7) is the firm one that will get Phase 5.

## Date

2026-05-31

## Context

The operator stopped using cairn's four-phase pipeline (`cairn-tdd-feature`) for daily work:
the per-feature ceremony cost more than it returned (`spec-v2.md` §2). The accepted
`cairn-thin-substrate-direction` ADR resolves this at the substrate level — its identity (D7)
is *"the layer that keeps AI-authored intent bound to verifiable evidence,"* and five-and-a-half
of its six primitives are shipped (premise-grounding keystone + scope-split included). What
remains is the migration: **Trial E — drop phase-1 derivation in favour of managing intents
directly.** "New cairn" = **intent management**: the intent (contract) is the durable anchor;
the predefined four-phase sequence is retired *in time*, not now.

This decision was shaped by a brainstorm (`docs/plans/2026-05-31-thin-cairn-intent-management.md`)
and a 6-refuter adversarial pre-mortem that reshaped the design (it found "approve every
session" **fatal** — ceremony recreation + stale-load — fixed by anchor≠approval; and the
semantic-misread gap **serious** — fixed by a front-loaded challenge). The `/decision` arc
(Phases 0–3 record: `.claude/skill-runs/thin-cairn-intent-management-decision/phases-0-3.md`)
then established the **decisive constraint**:

> `INV-003` is firm and machine-bound (`validate_phase_topology`), and
> `cairn-thin-substrate-direction` **D8 explicitly retains** INV-003 + the firm phase ADRs.
> Therefore this decision **cannot retire** the four-phase pipeline — retirement is a
> *separate, firm supersession*. This decision **builds the coexisting path and gates
> retirement on Trial E.**

## Decision

**D1 — Coexisting skill, no retirement here.** Build a new `cairn-intent` dispatch skill that
**coexists** with `cairn-tdd-feature` (unchanged). The four-phase pipeline, INV-003, and the
firm phase ADRs (`phase-lock-and-role-declaration`, `phase-pipeline-evaluation`,
`feature-slice-model`) are **retained unmodified** by this ADR.

**D2 — The loop.** Intent is an **always-on anchor**, loaded or formed at session start and
edited live. **Approval is delta-triggered** — re-fires only on a **premise or `must-satisfy`
clause edit** (not on code diff-size). Construction is **fluid** (one continuous conversation,
tests test-first, no phase resets), bracketed by **two decorrelation checkpoints**:
(a) a **front-loaded intent-challenge** — a fresh-context agent attacks the intent's premises
against live source *before* construction; (b) a **fresh close-review** — given contract +
diff + test output. (a) is the Skeptic's value front-loaded — the ADR D8 "equivalent
mechanism" requirement.

**D3 — Contract mandatory, graduated, with a completeness floor.** Every repo-writing session
carries at least a thin (one-liner) intent; depth graduates by size via the D3 exception tags.
The **completeness floor** = a one-line scope-statement in the contract (attackable by the
front-challenge) + the close-review smell-testing contract-depth against diff size. No hard
cardinality gate.

**D4 — Decorrelation: same-family now, cross-family EXPOSED.** Both checkpoints run as
fresh-context **same-family** subagents (fits the INV-004 budget; Song et al. backs
cross-*context*). The Kim-et-al ~60% same-family error-agreement risk is recorded EXPOSED,
with a revisit trigger: a correlated miss observed in Trial E opens a cross-family `/decision`.

**D5 — SessionStart carrier.** Build the `using-cairn` SessionStart carrier
(`delivery-mechanism-friction` D1) with a **testable "fired" definition** (emits the intent
pointer or a no-intent signal within the ≤2k-token INV-004 budget) and a **fallback**: if it
doesn't fire, the skill's first step does load/form explicitly (carrier is an optimization,
not the only path).

**D6 — Ambient enforcement, no new hooks.** Reuse the three shipped hooks unchanged —
`premise_guard` (grounding at approval), `role_guard` (envelope on writes), `atomicity_guard`
(scope-split). Deps stay pydantic/typer/pyyaml.

**D7 — Retirement is a future firm supersession.** The four-phase pipeline is **not** retired
here. **Trial-E pass** = the slice-#25 counterfactual **blocks at the front-challenge** AND
≥1 real cairn increment ships through `cairn-intent` with the operator confirming no
semantic-grounding leak AND the loop's felt cost < the four-phase cost. On pass → a **separate
firm ADR** retires `cairn-tdd-feature` and supersedes INV-003 + the phase ADRs, with a defined
coexistence sunset window and Phase-5 verification. On fail → the pipeline stays; the failure
is a real Trial-D/E finding, not a bug to paper over.

**D8 — Scope.** Single-operator-per-branch (intent lives in git; branches own their intent);
multi-operator/multi-branch reconciliation is EXPOSED + deferred to a future decision when a
real multi-operator consumer appears. Read-only / Q&A sessions are exempt (no write → nothing
to govern).

**D9 — Acceptance.** Unit-test the graduated-contract + completeness-floor rules, the
intent-challenge and close-review input/verdict contracts, and the carrier's fired-detection +
fallback (the three gates are already tested, unchanged). Trial-E dogfood is the integration
test; the slice-#25 counterfactual re-run blocking at the front-challenge is the decorrelation
acceptance gate.

## Consequences

### Easier

- **Daily-usability** is recovered: fluid construction, no per-session approval ceremony
  (approval is delta-triggered), thin intents on small work.
- **Semantic-misread defense** that the four-phase Skeptic provided is preserved *and*
  front-loaded — the front-challenge attacks premises before construction.
- **Coexistence is a safe off-ramp**: `cairn-tdd-feature` remains the fallback; no forced
  migration; retirement waits for evidence.
- Reuses the entire shipped substrate (three hooks + validator + templates); no new deps/infra.

### Harder

- **Four new components to build** (the skill + two subagents + the carrier), all currently
  unbuilt — a real implementation surface.
- **Same-family decorrelation residual** (Kim 60%) is accepted EXPOSED for the provisional
  trial; if Trial E shows a correlated miss, cross-family becomes a cost-bearing follow-on.
- **Three Phase-1 failure modes** need mitigation in build/migration: stale-`.slice-system`
  hook gaps downstream, the carrier not firing on non-Claude-Code hosts (intent divergence),
  and the premise_guard `.slice-system`-path traversal escape.
- **Temporary dual-tooling** during coexistence; if Trial E drags, the four-phase risks
  lingering as a zombie default — D7's sunset window mitigates.

## Alternatives Considered

- **A2 — Augment the four-phase in place** (intent gates inside the existing phases; no new
  skill, no retirement). *Runner-up.* Honors every firm ADR and is zero-migration, and its
  gates are genuine decorrelation — but it keeps the per-phase ceremony, so it **fails the
  daily-usability driver and the stated goal** (move *to* intent management). Retained as the
  **fallback if A1's Trial E fails**.
- **A3 — Promote spec-v2 wholesale now** (retire the four-phase immediately). **Rejected:**
  violates firm INV-003 + D8 (needs the firm supersession first), bypasses trial-gating, and
  carries severe cross-repo blast radius. It is where A1 *leads* if Trial E passes (D7), not a
  starting point.

## Risk Register

| ID | Risk | Prob | Impact | Mitigation |
|----|------|------|--------|------------|
| R1 | Stale `.slice-system` in a consumer → decorrelation hooks missing, silent grounding failure | Med | High | Plugin distribution ships the hooks; operational-reference safety note; migration doc surfaces the check |
| R2 | Same-family decorrelation lets a correlated misread through (Kim 60%) | Med | High | EXPOSED + Trial-E slice-#25 counterfactual is the acceptance gate; correlated miss → cross-family `/decision` (D4) |
| R3 | Carrier doesn't fire on a non-Claude-Code host → intent divergence | Med | Med | D5 skill-step fallback (carrier is an optimization); single-operator-per-branch scope (D8) |
| R4 | `premise_guard` `.slice-system`-path traversal reads cairn's source not consumer's → false-green | Low | High | Template guidance: repo-root-relative premise paths, not `.slice-system/…`; unit-test symlink resolution |
| R5 | Q1/Q4 resolve loose in practice → ceremony returns (A1 degrades to A2-plus-risk) | Low | Med | Delta-trigger on premise/clause edits only (D2); Trial E measures felt cost vs four-phase |
| R6 | Trial E never converges → four-phase lingers as zombie default | Low | Med | D7 retirement trigger + coexistence sunset window |
