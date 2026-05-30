---
id: identity-and-scope-deferral
name: "Cairn identity and scope — defer pivot; preserve option value"
status: superseded
firmness: provisional
supersedes: null
supersedes-sections: []
superseded-by: cairn-thin-substrate-direction
topic: scope
invariants-touched: []
date: 2026-05-20
---

# identity-and-scope-deferral: Cairn identity and scope — defer pivot; preserve option value

## Status

Accepted, provisional. Revisit triggers documented in D3.

## Date

2026-05-20

## Context

`docs/plans/2026-05-19-adaptive-reliability-direction.md` proposes pivoting Cairn from "a high-consequence four-phase methodology" to "an adaptive reliability layer for AI-assisted development" with four tiers (Tier 0 hygiene → Tier 3 formal flow), a deterministic risk scorer, and an amendment to `docs/spec-v1.md` §1's scope clause. The proposal cites Trial B's verdict (`a0e3fe6`, "contract correctly detected drift; trial bent rather than stopped") and five failing tests on `dev` as evidence of methodology strain.

A `/decision` arc was conducted; full record at `.claude/skill-runs/identity-and-scope-2026-05-20/outputs/`. Phase 0 harvested seven firm constraints. Phase 0.5 surfaced the structural finding that hooks (`checks/role_guard.py:43-45,137-167`), validators (`scripts/validate_architecture.py:443-445`), and tests (`tests/unit/test_handoff_contract.py`) are **orthogonal** to the four-phase machinery — they survive without the dispatch skill, agents, or `SKILL.md`. Phase 1 enumerated nine failure scenarios across technical/scale/integration dimensions. Phase 2 enumerated three approaches: A1 status-quo-hardened, A2 the direction-doc pivot, A3 infrastructure-identity-with-named-presets. Phase 3 mounted disconfirming search, runner-up steelman, and assumption audit. The steelman of A1 materially shifted the verdict by surfacing two arguments:

1. The pre-mortem's S1 ("bypass = de facto path") conflated *right-sizing* with *methodology rot*. Examining recent `dev` commits, all three execution paths (ad-hoc, `/decision`, `cairn-tdd-feature`) are active and matched to task shape — TDD outputs for code, `/decision` for arcs, ad-hoc for chores. The utilization pattern is appropriate, not failing.
2. Cairn has already pivoted once (substrate retirement at M4 per `cairn-substrate-and-fastmcp-superseded`). Likelihood of another pivot in 6-12 months is non-trivial. Every identity-level ADR landed now creates friction for that pivot.

The Phase-0 firm constraint that "primary user is one operator doing cairn-on-cairn; no external adoption pull demonstrated" reinforces deferring an identity commitment until external evidence accumulates.

## Decision

### D1 — Defer identity pivot

Cairn's identity claim remains as stated in `docs/spec-v1.md:25-29` ("genuinely complex software engineering; not for simple software") and `CLAUDE.md:2` ("methodology repo — TDD-by-construction dispatch skill, hooks, slash commands, validator"). The direction-doc proposal (Approach 2, adaptive tier model) and the infrastructure-identity reframe (Approach 3) are not adopted. The three de facto execution paths (ad-hoc under operator envelope, `/decision` for architectural arcs, `cairn-tdd-feature` for vertical TDD) are co-equal and documented as such in `docs/operational-reference.md`; no path is "the methodology." `phase-lock-and-role-declaration` (firm) is preserved.

### D2 — Orthogonality is a documented finding, not an identity claim

The orthogonality between governance infrastructure (hooks, validators, append-only ADRs, handoff contract, identifier scheme, role guards, plan-doc shape) and the four-phase TDD methodology is a verified structural fact (Phase 0.5 trace + Phase 3 disconfirming search). It is recorded as `docs/lessons.md` L-025, not as an identity ADR. The finding may inform future ADRs but is not itself a commitment.

### D3 — Revisit triggers

This decision is revisited when **any** of the following obtains:

1. External adoption pull is demonstrated — a non-operator consumer (or operator-of-another-project) actively using cairn produces a documented need the current three paths do not satisfy.
2. Revealed-preference data over 90+ continuous days on `dev` shows `cairn-tdd-feature` utilization below a threshold that distinguishes right-sizing from rot. (Threshold not specified here; the empirical claim is what matters, not the cutoff.)
3. A third independent contract trial (Trial C) surfaces a structural insight not absorbed by `[[adr-contract-execution-scope-clause]]`.
4. The operator's own design directive (a new direction doc or `/decision` invocation) explicitly invokes this ADR for supersession.

Until one of these obtains, identity-level proposals are referred to this ADR's Alternatives Considered section before being re-litigated.

### D4 — Mechanical follow-ups (not part of this ADR's commitment, recorded for traceability)

These are Trial-A-completion work, executed independently of this decision:

- Close `docs/ARCHITECTURE.md` INV-002 `binding-effective-from: <pending-slice-close-sha>` with Trial-A landing SHA.
- Rebaseline the five failing tests on `dev` (`test_context_discipline_protocol::test_v1_handoff_template_exists_and_is_tight`, `test_feature_skill_conformance::TestHandoffCrossFeatureIndex::{test_handoff_template_has_features_section,test_handoff_features_section_describes_per_feature_line}`, `test_invariant_assertions::TestSlice011AssertionCoverage::{test_no_extra_assertion_blocks,test_invariant_count_unchanged}`).
- Add the three-paths section to `docs/operational-reference.md` per D1.
- Add L-025 to `docs/lessons.md` per D2.

## Consequences

**Easier:**

- Re-litigation cost on future tier proposals drops: any direction-doc-style proposal must engage with the Alternatives Considered section before re-proposing. The `.claude/skill-runs/identity-and-scope-2026-05-20/outputs/` artifacts are the durable refusal vocabulary.
- Trial A's handoff-contract landing unblocks; INV-002 binding can close.
- The orthogonality lesson (L-025) is available as input to future contract trials and design moves without committing to an identity claim built on it.
- spec-v1 §1 remains the scope clause; consumer-facing framing is unchanged.
- `phase-lock-and-role-declaration` firmness is unaffected.

**Harder:**

- The structural insight from Phase 0.5 is *not* canonized at the ADR level. Future Claude sessions or consumers must read `docs/lessons.md` (L-025) or the skill-run files to find it; it is not in `docs/adr/index.md` as a discoverable claim. This is a deliberate choice (option value), not an oversight.
- The direction-doc's "ordinary repositories" framing is not adopted; if external adoption pull does materialize, retrofitting tier infrastructure later costs more than landing it now would have. Accepted as the price of option value.
- The pre-mortem's S1 scenario (bypass = de facto path) is reframed as right-sizing but not formally falsified. If sustained low utilization of `cairn-tdd-feature` proves to be rot rather than right-sizing, this decision will need supersession.

## Alternatives Considered

**Approach 2 — Adaptive tier model (the direction-doc proposal).** Pivot Cairn to "adaptive reliability layer." Four tiers, deterministic risk scorer, `templates/task-contract.yaml`, per-tier hook configuration, spec-v1 §1 amendment, `docs/operational-reference.md` rewrite. **Rejected** on three counts:

1. *I2 (spec amendment one-way door).* Amending `docs/spec-v1.md:25-29` from "not for simple software" to graduated framing is reputationally and consumer-mental-model expensive to revert. The amendment pays this cost for an external-adoption claim that has no demonstrated pull (Phase 0 firm constraint).
2. *T1 (tier misclassification).* The pivot reframes "is this important enough for Cairn?" to "what is the cost of being confidently wrong?" — but answering the new question correctly requires the operator to not be confidently wrong about the cost. Hard-overrides catch categorical cases (security, irreversibility, architecture, incident); ambiguous changes still leak.
3. *S2 (doc surface multiplies).* Four tiers × five doc dimensions (spec, ops-ref, hook config, test shape, contract template) is real maintenance debt. The direction doc's "Future Implementation Shape" section is post-slice, but the rebaseline alone is four-slices-in-a-trench-coat.

The pivot's strongest argument — that S1 (bypass = de facto path) is *avoided* under Pole B because the bypass becomes the spec — is undercut by the steelman's reframing of S1 as right-sizing.

**Approach 3 — Infrastructure identity, methodology as named preset.** Land one ADR declaring Cairn's identity as governance infrastructure; name the three execution paths as `ad-hoc | contracted | formal` presets; preserve `phase-lock-and-role-declaration`. **Rejected** on two counts:

1. The mechanical state of the repo after A3 lands is identical to after A1 lands plus one paragraph. A3's own honest weakness section admits: "rebranding, not redesign... If documentation alone solves the identity question, Approach 1 (doc-only, no ADR) does it cheaper."
2. The append-only commitment cost of A3's ADR is paid for a framing benefit that may not survive a future Cairn pivot. Option value, given the substrate-retirement precedent and the single-operator constraint, dominates the framing benefit.

The disconfirming search verified A3 is internally consistent (orthogonality holds, no naming collisions, no spec dependencies, three small amendments would suffice). The rejection is not on A3's design coherence but on the timing — committing identity claims while the identity question is unsettled is premature.

## Risk Register

Per Phase 1 pre-mortem (`.claude/skill-runs/identity-and-scope-2026-05-20/outputs/phase-1-premortem.md`):

| Scenario | Severity | This ADR's handling |
|----------|----------|---------------------|
| T1: tier misclassification | High / latent under A2 | Avoided — no tiers introduced. |
| T2: uncalibrated risk-scorer | Medium / latent under A2 | Avoided — no scorer introduced. |
| T3: hook discoverability | Medium / latent under Pole C | Avoided — hooks remain mandatory-on. |
| S1: bypass becomes de facto path | Reframed as right-sizing | Documented in D1; revisit trigger D3.2 catches the rot case if it obtains. |
| S2: doc surface multiplies | Low under deferral | Avoided — no spec amendment, no tier docs. |
| S3: vestigial Tier 3 | N/A under deferral | Avoided. |
| I1: handoff collision with non-dispatch work | Low | Mitigated by D4 INV-002 closure (Trial-A landing). |
| I2: spec amendment one-way door | High under A2 | Avoided — no spec change. |
| I3: market motion masked as reliability claim | Medium under A2 | Avoided — no adoption framing change. |

**Forward risks introduced by this ADR:**

- **R1:** Re-litigation of the identity question may recur (a fourth direction doc, another `/decision` invocation). Mitigation: the Alternatives Considered section is structured so future proposals must engage with it. If a proposal does not address why A2 or A3 was rejected, it can be answered "see this ADR."
- **R2:** The orthogonality finding (L-025) sitting outside the ADR tier may be missed by future contributors. Mitigation: D2 explicitly cross-references the lesson; the skill-run files persist; CLAUDE.md may eventually cite L-025 if it proves load-bearing.
- **R3:** D3's revisit triggers are operator-judgment-bound (no automated detector). Mitigation: the triggers name concrete observable conditions (external adoption, 90-day utilization data, Trial C, explicit invocation); a future review can audit against them.
- **R4:** "Right-sizing vs rot" distinction in S1 is not formally falsifiable in this ADR. If `cairn-tdd-feature` utilization is genuinely rotting, the deferral compounds. Mitigation: D3.2 trigger explicitly names this as a revisit condition.

## Cross-references

- Decision arc artifacts: `.claude/skill-runs/identity-and-scope-2026-05-20/outputs/`
- Trial B verdict: commit `a0e3fe6`, `docs/plans/2026-05-14-cairn-adr-contract-trial-b.md`
- Direction doc: `docs/plans/2026-05-19-adaptive-reliability-direction.md`
- Companion ADR: [[adr-contract-execution-scope-clause]]
- Orthogonality lesson: `docs/lessons.md` L-025
- Related firm ADRs preserved: `phase-lock-and-role-declaration`, `context-discipline-protocol`, `feature-slice-model`
