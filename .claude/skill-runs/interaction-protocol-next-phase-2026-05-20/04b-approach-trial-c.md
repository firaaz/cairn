# Approach TRIAL-C — Steelman

## Core idea

Bind a `contract:` block to slice `intent.md` produced by Phase 1 in `cairn-tdd-feature`. Trial A bound a contract to `handoff.md` (agent-to-agent). Trial B bound one to `docs/adr/identifier-scheme.md:6-22` (validator-to-filesystem). Both surfaces were structurally amenable. TRIAL-C runs the pattern at the surface that most threatens the methodology: an LLM-authored, free-prose-with-frontmatter artifact (`phase-1-tdd.md:13`) whose sole consumer is another LLM agent (`phase-2-tdd.md:7-10`). Success: Phase-2 tests cite contract clauses (not prose) as their obligation, and Phase 4 reports the contract caught semantic wrongness Phase 2 would have rubber-stamped. Failure: contract restates prose; Phase 2 ignores it; or the operator gate degrades to theatre.

## Mechanism

Files changed:

- `phase-1-tdd.md:13` — require a frontmatter `contract:` block (`must-satisfy`, `must-not-violate`, `wrong-if`, `evidence`; Trial-A/B shape). Each `must-satisfy` carries a `clause-id`. Clauses derive from Risk Surface + Feature-Local Invariants (already required at `phase-1-tdd.md:17-19`); non-derivable → RAISE_ISSUE.
- `phase-2-tdd.md:17` — require explicit `clause-id` citation in test docstrings and `approach.md`.
- `SKILL.md` — insert Step 5.5 (operator gate) between Step 5 (line 64) and Step 6 (line 66).
- `tests/unit/test_intent_contract.py` (new) — deterministic structural checks: frontmatter parses; four clause keys present; clause-ids unique; each `must-satisfy` ≤120 chars (Trial B's are 60-120 per `docs/adr/identifier-scheme.md:7-22`); `evidence:` paths resolve.

**Validator class — owned answer.** Verified categorical gap (03-premortem.md:19): clauses like "Specification names observable behavior" require judgement. I pick **deterministic structural + non-LLM binding**, not LLM-judge:

- *Layer 1 (`test_intent_contract.py`):* well-formedness, clause-id uniqueness, evidence resolution. Zero non-determinism. Stays inside `invariant-binding-strategy/D1`'s reserved `structural-parser` envelope (`docs/adr/invariant-binding-strategy.md:38`).
- *Layer 2 (citation binding):* Phase 2 cites clause-ids in test docstrings; Phase 4 sweeps and emits `clause-id → test-function` coverage map. Grep, not semantic.

Non-determinism budget: zero on both layers. Semantic judgement is bounded human attention at two checkpoints (Step 5.5; Phase-4 spot-check). Rejected: LLM-judge (violates D1) and regex blacklist (high false-positive, 03-premortem.md:19).

## Constraint fit

- **Honors:** INV-002 (intent.md is per-skill-run, not handoff), INV-003 (phase topology unchanged — Step 5.5 is a gate inside Phase 1→2 transition, not a new phase), INV-005 (no amendment to identifier-scheme contract; TRIAL-C is N=1 of a *new* contract surface, not D1-D9 supersession). Honors `schema-amendment-threshold/D2` (`01-constraints.md:19`) — N≥3 trigger is for widening, not for landing a first instance on a new surface.
- **Risks violating:** `invariant-binding-strategy/D1` *only if* the validator is LLM-judge; I rejected that. Also `phase-1-tdd.md:21` ("No same-session restate gate") if Step 5.5 is implemented as in-session Phase-1 restate — it must not be; it's operator review on the *committed* artifact between agent dispatches (asynchronous, harness-native).

## Engagement with pre-mortem attacks

### 1. No operator gate in skill (VERIFIED, 03-premortem.md:17)

Verified: `SKILL.md:64-66` chains Step 5 → Step 6 with `git show --stat` as the only intermediate; `phase-1-tdd.md:21` disavows a structural gate; memory note `feedback_intent_is_the_contract` corroborates.

**Scope it in.** Trial plan enumerates the skill amendment as *permitted enabling work* (lesson from `feedback_plan_contract_scope_separation.md` and commit `a0e3fe6`):

(a) *Step 5.5* — after Phase-1 commit verification, skill writes `<workspace>/step-5-5.gate` marker, prints banner with rendered contract block, exits. Operator inspects committed `intent.md`, then either re-invokes (resumes Step 6, deletes marker) or hand-edits first (scenario 4).

(b) *Pause primitive* — not a harness feature. The harness already returns control between Agent calls; the primitive is ~20 lines of checkpoint-on-marker logic in the skill. No infrastructure work.

(c) *Pre-applied lesson* — trial plan's contract enumerates `(SKILL.md, phase-{1,2}-tdd.md, intent contract policy)` as enabling-work artifact-scope.

The framing "that's protocol-pipeline-shape work, not a trial" is rejected. Trial A added a new artifact; Trial B added a new validator surface. Both expanded mechanism. TRIAL-C's expansion is the operator gate — same shape.

### 2. Semantic-drift validator class gap (VERIFIED, 03-premortem.md:19)

Verified via `tests/unit/test_identifier_scheme_contract.py:1-223` — all six tests are filesystem scans. The categorical gap is real.

**Owned answer:** Layer-1 / Layer-2 above. Semantic clauses are not directly machine-checkable; they become *bindable* via citation: Phase 2 cites clause-id; Phase 4 grep-confirms; operator spot-checks meaning at Step 5.5 and Phase 4 close. The "validator" is the composition (test_intent_contract.py + citation grep + bounded human attention). No new validator *type* — Layer 1 inside `structural-parser`, Layer 2 a Phase-4 audit. Consistent with D1.

### 3. Phase isolation breaks if Phase 2 cites contract clauses (03-premortem.md:21)

The doctrine at `SKILL.md:13` is *forward-blind*, not backward-blind. Phase 2 already consumes Phase 1's full intent.md (`phase-2-tdd.md:7-10`). Citing clauses is strictly *less* leakage than consuming prose; doctrine preserved.

Real risk: does contract-authoring leak Phase 2 *test design* into Phase 1? No. Phase 1 writes obligation-shaped clauses derived from Risk Surface + Feature-Local Invariants (`phase-1-tdd.md:17-19`); it does not write tests. Analogy: Trial-B clause "every ADR has a flat-slug id" (`docs/adr/identifier-scheme.md:9`) does not prescribe `test_d2_strict_id_shape`'s implementation (`tests/unit/test_identifier_scheme_contract.py:102-113`) — it states the obligation. Phase 2 retains assertion-design freedom.

### 4. Amendment authority for non-ADR contracts undefined (VERIFIED, 03-premortem.md:23)

Verified: only `phase-1-tdd` writes intent.md per `phase-1-tdd.md:11` and `role_guard.py` ROLE_POLICIES; no role re-edits post-commit.

**Scope the policy into the trial.** Minimum-viable rule:

- Intent contracts are *append-effective-once*: Phase 1 writes; once committed, frozen for the slice.
- Step 5.5 finds contract wrong → operator hand-edits intent.md (unset `AGENT_ROLE` → no role_guard block on `.claude/skill-runs/`), re-invokes skill.
- Phase 2/3/4 mid-slice ambiguity → RAISE_ISSUE (`SKILL.md:78-83`) → triager-tdd → ESCALATE_TO_USER → operator amends. No mid-slice agent re-edits.

Deliberately conservative; sufficient for TRIAL-C. Permissive schemes (triager-tdd re-dispatches Phase 1 with pre-amended contract) are future work. Framing "supposed to use the policy, not write it" rejected — writing the minimum policy needed to run TRIAL-C is properly-scoped enabling-work.

## Why TRIAL-C *now* (not after TIGHTEN-FIRST)

The strongest cross-branch attack (03-premortem.md:53): TIGHTEN-FIRST without a second contract instance is solution-without-problem; TRIAL-C surfaces actual shape-stresses.

TIGHTEN-FIRST's candidate tightenings (versioning, audience tags, must-satisfy-optional, `escalate-when` separation) are drawn from intuition about Trial-B's "too strict" verdict. But that verdict applied to Trial-B's *plan-level* execution-scope clause (`01-constraints.md:17`), not the ADR contract block shape. The block shape is N=2 (Trial-A, Trial-B); both held. Tightening N=2 without a third instance pulling against it is over-fitting to an adjacent failure.

TRIAL-C is that third instance. It will reveal whether the shape needs audience tagging (intent contracts are operator-review-facing, unlike Trial-B's validator-facing surface), explicit non-derivation clauses, or must-satisfy-optional (intent contracts may be purely-negative — "this slice does NOT touch X"). These stresses cannot be predicted; they must be found.

**Honest concession:** TIGHTEN-FIRST first is defensible if priority is minimum churn in contract-shape ADRs and rework is absorbable. TRIAL-C-first dominates if priority is *learning velocity per session* and *evidence-based tightening*. The shape held across two unlike artifact types without amendment — it has earned a third instance without preemptive refinement.

## Downstream impact

**Makes easier:**

- Working intent-contract becomes the template for every future slice. Phase-1 artifact quality becomes structural, not pure operator discipline. Floor rises corpus-wide.
- Step-5.5 gate is reusable by any future skill needing "operator confirms artifact before next dispatch." Closes the gap `feedback_intent_is_the_contract` flagged.
- Phase-4 clause-id coverage map gives the audit machine-readable scope (today's audits arbitrary invariants from prose).

**Makes harder:**

- Two new policies (append-effective-once contracts; operator-only mid-slice amendments) enter the methodology — new surface tested by use.
- Phase-1 latency grows by one checkpoint (~5-15 min/slice). Trial-B contracts are 16 lines (`docs/adr/identifier-scheme.md:6-22`), so review is bounded.
- Future TIGHTEN-FIRST work coexists with shipped clause-id field. Migration per-new-slice, not corpus-wide.

## Honest costs

- **Calendar:** 2-3 sessions. S1: trial plan + SKILL.md + agent updates + `test_intent_contract.py`. S2: P1-P4 run on a simple slice; Step-5.5 review; Phase-4 map. S3: close-out + verdict.
- **Operator attention:** highest in this arc. Trial A and B added zero attention points per slice; TRIAL-C adds two (Step 5.5, Phase-4 coverage spot-check). Strongest *operational* argument against TRIAL-C now.
- **Semi-result risk:** "shape works but adjacent infrastructure (Step 5.5 UX, amendment edge cases, coverage-map polish) is incomplete." Mitigation: trial plan scopes the gate as minimum-viable banner + marker file; UX polish declared out-of-scope (lesson from `01-constraints.md:27`).
- **Strongest argument against (forced):** Trial A and B bound contracts whose downstream consumers were *deterministic* (handoff parsers; pytest). Intent's consumer is Phase 2 — an LLM agent. A contract whose primary consumer is non-deterministic risks becoming one *only the operator verifies*, collapsing TRIAL-C to "operator reviews intent.md as before, in YAML." If the verdict is "contract added no clarity Phase 2 didn't get from prose," 2-3 sessions buy a negative result on whether the pattern generalises to LLM-consumer artifacts. The bet is that the operator gate + clause-id citation force enough structure that the contract earns its keep with an LLM downstream. The bet may lose.
