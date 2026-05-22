# Rejected exploration — adaptive-reliability-pivot ADR draft

**Status:** Archaeology only. This ADR was drafted on 2026-05-22 as a candidate supersession of `[[identity-and-scope-deferral]]` + `[[slice-intent-contract]]`. Operator rejected the framing the same day with the signals "not adaptive" + "thinner" + "identity question still open." The file was never committed to `docs/adr/` and was deleted from the working tree before the session cut. Preserved here as one explored framing the brainstorm may consult, attack, modify, or discard.

**Why it was drafted:** earlier in the same session, the operator asked me to look at recent commits and the workflow-subagents branch under the framing "make cairn actually usable." The dev arc plus the 2026-05-19 direction doc plus identity-and-scope-deferral's D3.4 escape together pointed toward partial adoption of the direction doc's adaptive-reliability tier model. The ADR below committed to the *framing* (Cairn as adaptive reliability layer; four-phase methodology as optional Tier 3) without committing to the direction doc's "Future Implementation Shape" (spec amendment, risk-scorer, task-contract template, per-tier hook config).

**Why it was rejected:** the operator's response after seeing the draft surfaced that committing to ANY framing (adaptive, deferred, or otherwise) is premature — the identity question itself needs to be brainstormed first. The thinning direction was the load-bearing signal: lean toward less of cairn, not more conceptual scaffolding. Adaptive-reliability adds a tier model; the operator wants to know what's load-bearing before adding any model.

**Useful inputs the brainstorm should engage with from this exploration:**

1. The bounded-scope reasoning (framing without spec amendment) is a valid pattern; the brainstorm may want to apply it differently — e.g., commit to "infrastructure-as-identity" without committing to "delete the methodology."
2. The contract block (must-satisfy/must-not-violate/wrong-if/evidence + execution-scope) demonstrates the contract grammar in use at decision-level; the brainstorm can use this shape if it produces an ADR.
3. The risk register inherited risks from identity-and-scope-deferral's pre-mortem; if the brainstorm produces a supersession, it should similarly engage with the deferral's I2/S2/T1 analysis rather than ignoring it.
4. The honest "Consequences > Harder" section names split-brain risk (spec vs. ops-ref) — same risk applies to any partial-adoption pivot; brainstorm should consider whether full-or-nothing is cleaner.

**Cross-references the draft cited (useful for brainstorm context):**

- `docs/plans/2026-05-19-adaptive-reliability-direction.md`
- `[[identity-and-scope-deferral]]` (D3.4 trigger)
- `[[slice-intent-contract]]` (yesterday's TRIAL-C ADR)
- `[[phase-lock-and-role-declaration]]` (firm; four-phase methodology lock)
- `[[context-discipline-protocol]]` (firm; handoff substrate)
- `[[feature-slice-model]]` (firm; slice ceremony)
- `[[adr-contract-execution-scope-clause]]` (provisional; contract grammar)
- `[[schema-amendment-threshold]]` (firm; N≥3 trigger)
- `[[context-tiers-integration]]` (INV-007 context-budget tiers; orthogonal to reliability tiers)
- `docs/lessons.md` L-025 (orthogonality), L-026 (default-with-pivot)
- `feature/workflow-subagents` branch (6 Tier 0/1-equivalent utilities)

---

# adaptive-reliability-pivot: Cairn as adaptive reliability layer — tier framing committed, scope bounded

## Frontmatter (as drafted)

```yaml
id: adaptive-reliability-pivot
name: "Cairn as adaptive reliability layer — tier framing committed, scope bounded"
status: accepted
firmness: provisional
contract:
  must-satisfy:
    - D1 Cairn's identity claim is "adaptive reliability layer for AI-assisted development" with four tiers (0 hygiene, 1 scoped work, 2 contracted work, 3 formal flow)
    - D2 the existing four-phase TDD methodology is preserved as Tier 3 — optional, not the default
    - D3 workflow-subagents under agents/ land as the immediate Tier 0/1 surface in this slice
    - D4 the 5 stale tests named in docs/plans/2026-05-19-adaptive-reliability-direction.md (lines 200–208) rebaseline as part of this slice
    - D5 slice-intent-contract is retracted — TRIAL-C as ceremony-extension is incompatible with this framing
  must-not-violate:
    - this ADR is read as full adoption of docs/plans/2026-05-19-adaptive-reliability-direction.md when it is scope-bounded to that doc's "Proposed Next Slice" only
    - the four-phase methodology becomes vestigial through erosion rather than explicit retirement
    - tier-doc infrastructure (per-tier hook configuration, risk-scorer script, task-contract.yaml template) is built before tier framing produces external-use signal
  wrong-if:
    - 90 days after merge, no Tier 0/1 utility (slice-status, handoff-closer, pytest-triage, root-cause-hunter, worktree-map, adr-context) is invoked outside cairn-on-cairn work
    - the rebaseline (5 stale tests + INV-011/INV-012 coverage) does not land in the same slice as this ADR
    - spec-v1 §1 scope clause is amended in a follow-up slice without re-running /decision against identity-and-scope-deferral I2 ("spec amendment one-way door")
  evidence:
    - this ADR is committed; docs/adr/index.md registers it; identity-and-scope-deferral and slice-intent-contract carry status:superseded + superseded-by: adaptive-reliability-pivot
    - feature/workflow-subagents is merged into dev (HEAD reachable from origin/dev)
    - all 5 stale tests pass under contract-shaped handoff + dynamic invariant-id derivation
    - docs/lessons.md L-027 captures the D3.4 trigger pattern
  execution-scope:
    - docs/adr/identity-and-scope-deferral.md (frontmatter-only: status/superseded-by)
    - docs/adr/slice-intent-contract.md (frontmatter-only: status/superseded-by)
    - docs/adr/index.md (this ADR registered; superseded statuses updated)
    - docs/operational-reference.md (graduated-guardrails as primary mental model; not a spec amendment)
    - docs/lessons.md (L-027 D3.4 trigger pattern)
    - .claude/handoff.md (drop slice-intent-contract thread; add rebaseline + workflow-subagents threads)
    - tests/unit/test_context_discipline_protocol.py + tests/unit/test_feature_skill_conformance.py + tests/unit/test_invariant_assertions.py (5 stale tests rebaselined)
    - merge of feature/workflow-subagents into dev
supersedes: [identity-and-scope-deferral, slice-intent-contract]
supersedes-sections: []
superseded-by: null
topic: scope
invariants-touched: []
date: 2026-05-21
```

## Status (as drafted)

Accepted, provisional. Provisional firmness reflects that this ADR commits to the *framing* (Cairn as adaptive reliability layer; Tier 3 = current methodology) but explicitly defers the broader direction-doc adoption (spec-v1 §1 amendment, per-tier hook reconfiguration, risk-scorer infrastructure, task-contract template, adapter guidance). Supersession is the standard remedy if the tier framing produces no usage signal within the 90-day window named in `wrong-if`.

## Date

2026-05-21 (the draft was dated 2026-05-21; the operator's session crossed midnight to 2026-05-22 before the rejection signal).

## Context (as drafted)

### The chain

- **2026-05-19** — `docs/plans/2026-05-19-adaptive-reliability-direction.md` (290 lines) proposes pivoting Cairn from "high-consequence four-phase methodology" → "adaptive reliability layer," with four tiers (0 hygiene default → 3 formal flow optional). The framing question changes from "is this project important enough for Cairn?" to "what is the cost of the agent being confidently wrong on this change?"
- **2026-05-20** — `[[identity-and-scope-deferral]]` runs a full `/decision` arc and **defers** the pivot. Phase 0 firm constraint: "primary user is one operator doing cairn-on-cairn; no external adoption pull demonstrated." Phase 3 disconfirming search reframes the deferral's S1 ("bypass = de facto path") as right-sizing rather than rot. The ADR commits to deferral but writes four revisit triggers; D3.4 names "the operator's own design directive (a new direction doc or `/decision` invocation) explicitly invokes this ADR for supersession" as the operator-override path.
- **2026-05-20** — Same day, post-deferral, `[[slice-intent-contract]]` (TRIAL-C) lands. The ADR extends the Trial-A/Trial-B contract pattern to slice `intent.md` and adds a Step 5.5 operator gate to the dispatch skill. Direction: net new ceremony at the highest-friction surface.
- **2026-05-21** — Operator invokes D3.4. The framing: "make cairn actually usable; nothing uses cairn right now because of its issues" + "the usage model is realistically usable, and there is value of using cairn." Plus an explicit directive to "look at the commits and other branches" — surfacing `feature/workflow-subagents` (six Tier 0/1 utilities, sitting unmerged for 10 days) as the concrete adoption surface.

### Why the deferral was correct on its own evidence

Re-reading `[[identity-and-scope-deferral]]`'s rejection of Approach 2 (adaptive tier model): the three counts were I2 (spec amendment one-way door), T1 (tier misclassification risk), S2 (doc surface multiplies). On 2026-05-20's evidence — no external pull, fresh substrate-pivot precedent, single-operator constraint — deferral with option-value preservation was the rational move.

### Why D3.4 firing today is a real signal, not noise

The deferral framed D3.4 as a catch-all override the operator could invoke. But D3.4 is more than rubber-stamp: it exists to capture cases the empirical triggers (D3.1 external pull; D3.2 90-day utilization data; D3.3 Trial C structural insight) can't see at a 1-day window. Three observations support D3.4 being genuinely informative here:

1. **The deferral didn't redirect work.** The next day produced `slice-intent-contract`, which is *more* ceremony on the most-LLM-authored artifact — the direct opposite of the direction doc. Deferral preserved option value but not direction.
2. **Workflow-subagents existed all along.** The `feature/workflow-subagents` branch (commit `8b680cb`, 2026-05-11) carries six concrete Tier 0/1 utilities (slice-status, handoff-closer, pytest-triage, root-cause-hunter, worktree-map, adr-context) plus `docs/PREREQS.md` documenting the consumer code-intelligence stack. The branch sat unmerged for 10 days while dev accumulated meta-work. Non-merge is itself the "non-use" signal the deferral's D3.2 trigger would have caught only at 90 days.
3. **Re-reading the dev arc.** Trial A pointer-only handoff, schema-amendment-threshold N≥3, execution-scope clause, identity-and-scope-deferral itself — all reduce ceremony / codify implicit / prevent premature commitment. The dev direction is tier-compatible. Only `slice-intent-contract` breaks the pattern.

### What this ADR does NOT do

It does not adopt the full direction doc. The deferral's I2 and S2 risk analyses are still partially load-bearing:

- **I2 (spec amendment one-way door).** `docs/spec-v1.md:25-29`'s "genuinely complex software engineering; not for simple software" clause is reputationally expensive to revert. This ADR adopts the tier framing in cairn's internal mental model (`docs/operational-reference.md`) without amending the spec. The spec amendment is a separate decision and remains gated on the deferral's I2 reasoning.
- **S2 (doc surface multiplies).** Per-tier hook configuration, risk-scorer script, task-contract.yaml template, adapter guidance — all from the direction doc's "Future Implementation Shape" (lines 241–264) — are NOT in this slice's scope. They become candidate work after the tier framing produces usage signal.

The bet: the framing commitment without the spec/infra commitments is enough to unblock the workflow-subagents merge and the rebaseline, produce signal, and preserve option to walk back if the tier framing turns out to be wrong.

## Decision (as drafted)

### D1 — Cairn's identity claim: adaptive reliability layer

Cairn is an adaptive reliability layer for AI-assisted development. Its purpose is to convert engineering discipline into mechanical guardrails that scale from basic hygiene (Tier 0) to formal architectural control (Tier 3). The four tiers are:

- **Tier 0 — Hygiene.** Default for ordinary repositories. Block destructive commands, protect `.env*` and lock files, block `git push --force` (allow `--force-with-lease`), run format/lint where configured, fail loudly when hook dependencies are missing, maintain a tiny handoff pointer.
- **Tier 1 — Scoped Work.** Default for normal feature/bug work. File/path envelope, required verification command, task summary or task contract, explicit envelope-expansion trail.
- **Tier 2 — Contracted Work.** When correctness depends on intent (not just code). `must-satisfy`/`must-not-violate`/`wrong-if`/`evidence` clauses, deterministic contract tests where possible, ADR-lite or decision note.
- **Tier 3 — Formal Flow.** Architecture/invariant/security/irreversible boundaries. Append-only ADR or supersession, architecture invariant update, strict envelope, independent review or phase separation, full validator/test evidence, **optional four-phase TDD flow**.

This supersedes `[[identity-and-scope-deferral]]` D1 (which preserved "high-consequence-only" framing via `docs/spec-v1.md:25-29`). Per `[[adr-contract-execution-scope-clause]]` D2, the tier framing applies to *cairn's mental model and ops-reference*; it does not amend `docs/spec-v1.md` in this slice — see D5.

This contrasts with `[[context-tiers-integration]]`'s context-tiers (Tier 1 handoff index, Tier 2 feature on-demand, Tier 3 slice working) which govern context-budget partitioning. The two tier systems are orthogonal and use the same word for different things. Disambiguation: when an adaptive-reliability tier is meant, the term is "reliability tier"; the existing `INV-007` context tiers retain their name.

### D2 — Four-phase methodology preserved as Tier 3 (optional)

`[[phase-lock-and-role-declaration]]` (firm) remains firm; the four-phase pipeline (Intent → Validation → Implementation → Integration) is preserved unchanged. Its role under this ADR is **Tier 3 optional machinery** — invoked for changes whose mistakes compound (architecture, invariant, security, irreversibility, cross-service integration, multi-agent coordination). It is no longer the default execution path for ordinary work.

The three de facto execution paths identified in `[[identity-and-scope-deferral]]` D1 (ad-hoc under operator envelope, `/decision` for architectural arcs, `cairn-tdd-feature` for vertical TDD) remain co-equal — but now they map to tiers: ad-hoc → Tier 0/1; `/decision` → Tier 2/3; `cairn-tdd-feature` → Tier 3.

### D3 — Workflow-subagents are the Tier 0/1 mechanical surface

`feature/workflow-subagents` (commit `8b680cb`, 1 commit ahead of dev, no conflict per `git merge-tree`) is merged into dev as part of this slice. The branch adds:

- `agents/slice-status.md` — auto-fires on "status?", reports orchestrator/slice state (Tier 0)
- `agents/handoff-closer.md` — auto-fires on "wrap up", writes handoff + conventional-commit (Tier 0/1)
- `agents/pytest-triage.md` — auto-fires on pytest failure, root-cause via systematic-debugging (Tier 0/1 diagnostic)
- `agents/root-cause-hunter.md` — auto-fires on "find every place that does X", LSP + ast-grep backward trace (Tier 0/1 diagnostic)
- `agents/worktree-map.md` — auto-fires on "status across worktrees", compact table (Tier 0)
- `agents/adr-context.md` — auto-fires on "what invariants apply to X", constraint envelope as `/decision` prelude (Tier 2)
- `docs/PREREQS.md` — consumer code-intelligence stack (Claude Code ≥2.0.74 native LSP, ast-grep, Pyright, Ruff, superpowers)

These six agents are the immediate observable change a Tier 0/1 consumer experiences. They are read-only or diagnostic; their blast radius is bounded; they do not require the four-phase dispatch skill to invoke.

### D4 — Stale-test rebaseline lands in this slice

Per `docs/plans/2026-05-19-adaptive-reliability-direction.md` lines 200–208, five tests on `dev` enforce the retired sectioned-narrative handoff model and a hard-coded INV-001..010 invariant set. They are rebaselined to the contract-shaped handoff model and dynamic invariant-id derivation as part of this slice:

- `tests/unit/test_context_discipline_protocol.py::test_v1_handoff_template_exists_and_is_tight` — update to assert the contract-shaped frontmatter from `[[invariant-binding-strategy]]` and `tests/unit/test_handoff_contract.py`
- `tests/unit/test_feature_skill_conformance.py::TestHandoffCrossFeatureIndex::test_handoff_template_has_features_section` — retire the `## Features` section assertion (the Tier-0/1 handoff is pointer-only per Trial A)
- `tests/unit/test_feature_skill_conformance.py::TestHandoffCrossFeatureIndex::test_handoff_features_section_describes_per_feature_line` — retire
- `tests/unit/test_invariant_assertions.py::TestSlice011AssertionCoverage::test_no_extra_assertion_blocks` — update to derive invariant-id range from `ARCHITECTURE.md` parse rather than hard-code
- `tests/unit/test_invariant_assertions.py::TestSlice011AssertionCoverage::test_invariant_count_unchanged` — update to derive expected count from `ARCHITECTURE.md`

The rebaseline retires the dev split-brain (direction-doc-language vs. test-enforced-shape mismatch) without amending `docs/spec-v1.md`.

### D5 — Scope bounded; spec-v1 §1 amendment deferred

This ADR does NOT amend `docs/spec-v1.md` §1 (the "genuinely complex software engineering; not for simple software" scope clause). Per `[[identity-and-scope-deferral]]` I2, that amendment is a reputational one-way door whose cost is paid for an external-adoption claim that still lacks demonstrated pull. Deferral of the spec amendment is preserved.

This ADR does NOT introduce:

- `scripts/assess_risk_tier.py` (direction doc lines 245–248)
- `templates/task-contract.yaml` (direction doc lines 250–252)
- Per-tier hook integration (direction doc lines 254–258)
- Adapter guidance for Claude Code vs. Codex (direction doc lines 260–264)

These are direction-doc "Future Implementation Shape" items. They become candidate work *after* the framing in D1–D4 produces usage signal — the test is whether the Tier 0/1 workflow-subagents get invoked outside cairn-on-cairn work (see `wrong-if` clause in this ADR's contract).

### D6 — TRIAL-C agenda retired; slice-intent-contract superseded

`[[slice-intent-contract]]` is superseded by this ADR. TRIAL-C as scoped (Step 5.5 operator gate, append-effective-once amendment policy, intent-contract Layer-1 + Layer-2 validator) is incompatible with the reliability-tier framing: it added Tier-3-class ceremony to the most-LLM-authored artifact at a moment when the direction was lowering the floor, not raising it.

The substantive work product of yesterday's `/decision` (the Phase 0–5 record at `.claude/skill-runs/interaction-protocol-next-phase-2026-05-20/`) is preserved. L-026 (default-with-explicit-pivot pattern) stands; the supersession of `slice-intent-contract` is itself an instance of L-026 firing — the active alternative (FREEZE+DISTRIBUTE, broadened to "adaptive reliability") was operator-priority-elevated, and supersession was the cheap pivot path L-026 named.

### D7 — Lessons capture: D3.4 trigger pattern

A new `docs/lessons.md` entry (L-027) captures the structural lesson: when a deferral ADR writes an operator-override revisit trigger (e.g., D3.4 in `[[identity-and-scope-deferral]]`), the override firing is not a methodology failure — it is the trigger functioning as designed. The deferral's analysis is preserved as durable refusal vocabulary; the override invokes it cleanly without destroying the prior reasoning. This pattern is candidate for `/decision` skill promotion at N≥3 instances per `[[schema-amendment-threshold]]`/D2.

## Consequences (as drafted)

**Easier:**

- A consumer installing cairn into an ordinary repository (the explicit Tier 0 audience) has six immediately-useful workflow agents and a documented prereq stack — concrete value per session, not waiting on slice completion.
- The dev split-brain (5 stale tests enforcing the retired model) is closed; future sessions can extend without re-litigating the handoff shape.
- The deferral's analysis is preserved as Alternatives Considered, not destroyed; future identity-level proposals must engage with both this ADR and `[[identity-and-scope-deferral]]`'s rejection grounds.
- The TRIAL-C retraction is clean: yesterday's `/decision` arc's substantive work product (the four-approach enumeration, the FREEZE+DISTRIBUTE active-alternative pattern that informed today's pivot) is intact at `.claude/skill-runs/interaction-protocol-next-phase-2026-05-20/`; only the ADR's substantive commitments are reversed.
- L-026 (default-with-explicit-pivot) is validated by its first real firing within 24 hours — the supersession path was actually cheap because the prior ADR was written to be flippable.

**Harder:**

- `docs/spec-v1.md` §1 now reads "not for simple software" while `docs/operational-reference.md` reads "Tier 0 default for ordinary repositories." The two surfaces will be inconsistent until the spec amendment is re-litigated. Accepted as the price of preserving I2's one-way-door risk analysis.
- Future readers may interpret this ADR as full direction-doc adoption (the framing matches). The `must-not-violate` clause in this ADR's contract explicitly forbids that reading, but enforcement is by convention, not by hook. The bounded scope must be re-stated in `docs/operational-reference.md`.
- Future tier-infrastructure work (assess_risk_tier.py, task-contract.yaml, per-tier hook config) carries the obligation to re-engage with the deferral's analysis when proposed; this is procedural overhead that pure-deferral would have avoided.
- The four-phase methodology becoming "optional Tier 3" risks atrophy through under-use. `wrong-if` clause names the 90-day non-use trigger; if the methodology is used only for cairn-on-cairn work, the framing's claim of cross-tier value is unverified.

## Alternatives Considered (as drafted)

**Alternative A — Continue deferral (status quo on identity-and-scope-deferral).** Leave the deferral in place; do not invoke D3.4 today; let one of the empirical triggers (D3.1 external pull, D3.2 90-day utilization, D3.3 Trial C) accumulate signal instead. **Rejected** because the deferral didn't redirect work: yesterday's `slice-intent-contract` ADR is direct evidence that preserving option value did not prevent ceremony accretion. D3.4 exists specifically for the case where empirical triggers can't catch direction-misalignment at a short window; this is that case.

**Alternative B — Full direction-doc adoption (amend spec-v1 §1; ship risk-scorer + task-contract template + per-tier hook configuration in this slice).** Adopt the framing AND the infrastructure together. **Rejected** because the deferral's I2 (spec one-way door) and S2 (doc surface multiplies) concerns are still load-bearing. The framing commitment without the spec amendment costs nothing reputationally; the spec amendment without external pull is the cost the deferral identified. Land the framing; defer the spec; gate the infrastructure on signal.

**Alternative C — Workflow-subagents merge only; no framing commitment.** Merge `feature/workflow-subagents` and supersede `slice-intent-contract`, but do NOT commit to the tier framing. **Rejected** because the workflow-subagents *are* the tier framing's first concrete instance — refusing to name the framing while shipping the surface is the worst of both worlds: it commits to the work product without the conceptual scaffold future authors need to extend it. L-025's orthogonality finding is structural; this ADR is what converts it into a framing claim.

**Alternative D — Re-run the full `/decision` arc from Phase 0.** The deferral's `/decision` arc happened 1 day ago; the constraint envelope, journey trace, pre-mortem, and enumeration are all current. Re-running them would duplicate work the operator's D3.4 invocation explicitly authorizes skipping. The deferral's record is preserved at `.claude/skill-runs/identity-and-scope-2026-05-20/outputs/` as input to *this* ADR; re-running it would either reach the same conclusion or surface evidence that would force a third pivot. Either case is wasteful at 1-day cadence. **Rejected on procedural grounds.**

## Risk Register (as drafted)

Inheriting from `[[identity-and-scope-deferral]]`'s pre-mortem (some risks the deferral avoided are now active under partial adoption):

| # | Scenario | Severity | This ADR's handling |
|---|----------|----------|---------------------|
| R1 (was T1) | Tier misclassification | Medium — was latent under A2, now active | No risk-scorer ships; tier selection is operator-judgment-driven. Hard overrides (security/irreversible/architecture) are recorded in D1 prose. If misclassification compounds, the risk-scorer becomes load-bearing follow-up work. |
| R2 (was S2) | Doc surface multiplies | Low — preserved by bounded scope | D5 explicitly defers per-tier doc infrastructure. The `must-not-violate` clause in this ADR's contract names "tier-doc infrastructure built before signal" as a contract breach. |
| R3 (was I2) | Spec amendment one-way door | High — but avoided | D5 explicitly does NOT amend `docs/spec-v1.md`. The cost reasoning from `[[identity-and-scope-deferral]]` I2 is preserved as gating for any future amendment. |
| R4 (new) | Dev split-brain between spec and ops-ref | Medium / accepted | Spec says "not for simple software"; ops-ref will say "Tier 0 default for ordinary." Documented in Consequences "Harder"; ops-ref update explicitly notes the bounded scope. |
| R5 (new) | TRIAL-C retraction surfaces as inconsistency | Low | `[[slice-intent-contract]]` becomes superseded; its substantive content (Phase 0–5 record) stays as decision-arc archaeology. L-026's first firing validates the cheap-pivot path. |
| R6 (new) | Four-phase methodology atrophy through under-use | Medium / latent | `wrong-if` clause's 90-day non-use trigger catches this. If Tier 3 work doesn't happen in 90 days, the methodology's preserved status needs re-evaluation. |
| R7 (was S1, reframed) | "Bypass = de facto path" — adaptive tier framing legitimizes existing bypass patterns rather than producing new value | Medium / latent | `wrong-if` 90-day non-use of Tier 0/1 utilities outside cairn-on-cairn IS the test. If utilities are invoked only by the operator on cairn-internal work, the framing is window-dressing on existing patterns. |
| R8 (new) | Operator priority shifts again before signal accumulates | Possible / low | Provisional firmness; supersession path is well-scoped per L-026. The pattern has now fired once within 24 hours of its lesson being written — operationally validated. |

## Cross-references (as drafted)

- Direction doc: `docs/plans/2026-05-19-adaptive-reliability-direction.md`
- Superseded ADRs (proposed): `[[identity-and-scope-deferral]]`, `[[slice-intent-contract]]`
- Decision-arc archives preserved as input: `.claude/skill-runs/identity-and-scope-2026-05-20/outputs/`, `.claude/skill-runs/interaction-protocol-next-phase-2026-05-20/`
- Companion ADRs preserved: `[[phase-lock-and-role-declaration]]` (firm; Tier 3 machinery), `[[context-discipline-protocol]]` (firm; Tier 0/1 handoff substrate), `[[feature-slice-model]]` (firm; Tier 3 unit of work), `[[adr-contract-execution-scope-clause]]` (provisional; Tier 2 grammar), `[[schema-amendment-threshold]]` (firm; tier-doc infra gating)
- Relevant lessons: L-025 (orthogonality — governance vs methodology), L-026 (default-with-explicit-pivot — first firing today)
- Branch landing as part of this slice: `feature/workflow-subagents` (commit `8b680cb`, 6 agents + PREREQS.md)
- Disambiguation: `[[context-tiers-integration]]` (INV-007 context-budget tiers — orthogonal to reliability tiers)
