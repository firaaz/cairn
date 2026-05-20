---
id: slice-intent-contract
name: "Slice intent contract — TRIAL-C frontmatter shape, operator gate, append-effective-once amendment policy"
status: accepted
firmness: provisional
contract:
  must-satisfy:
    - D1 Trial C scope is a frontmatter contract block on slice intent.md produced by Phase 1
    - D2 the contract validator is deterministic structural (Layer 1) plus clause-id citation binding (Layer 2); no LLM-judge
    - D3 the cairn-tdd-feature skill grows Step 5.5 — an asynchronous operator gate between Phase 1 commit and Phase 2 dispatch
    - D4 intent contracts are append-effective-once — only the operator may amend a committed contract mid-slice, via RAISE_ISSUE escalation
    - D5 the trial commitment is one trial slice running Phase 1 through Phase 4 under the new contract shape, producing an operator verdict recorded in skill-runs close-out
  must-not-violate:
    - an LLM-judge validator is introduced for intent-contract semantic checks
    - Step 5.5 is implemented as an in-session Phase-1 restate (violates phase-1-tdd.md "no same-session restate gate")
    - mid-slice agents (Phase 2/3/4 or triager-tdd) re-edit a committed intent.md without operator escalation
    - the trial's enabling work expands beyond the artifact-scope enumerated in execution-scope below
  wrong-if:
    - Phase 4 sweep-notes clause-id coverage map shows any must-satisfy clause uncited by at least one test
    - operator review at Step 5.5 takes more than 15 minutes per slice on average (contract is too dense to scan; defeats rubber-stamping defeat)
    - trial close-out verdict is "contract added no clarity Phase 2 didn't get from prose"
  evidence:
    - tests/unit/test_intent_contract.py exists and passes (Layer 1 well-formedness)
    - .claude/agents/phase-1-tdd.md and .claude/agents/phase-2-tdd.md carry the contract-shape and clause-citation amendments
    - .claude/skills/cairn-tdd-feature/SKILL.md carries Step 5.5
    - a trial slice's intent.md carries a populated contract block and Phase 4 sweep-notes record clause-id coverage
  execution-scope:
    - docs/plans/2026-05-20-cairn-trial-c-slice-intent-contract.md (trial plan)
    - .claude/skills/cairn-tdd-feature/SKILL.md (Step 5.5 amendment)
    - .claude/agents/phase-1-tdd.md and .claude/agents/phase-2-tdd.md (prompt amendments)
    - tests/unit/test_intent_contract.py (new test file)
    - docs/adr/index.md (registration of this ADR)
    - docs/lessons.md (L-NNN entry capturing the next-phase decision and the FREEZE+DISTRIBUTE alternative axis)
    - .claude/handoff.md (TRIAL-C in-flight thread; FREEZE+DISTRIBUTE deferred thread)
supersedes: null
supersedes-sections: []
superseded-by: null
topic: process
invariants-touched: []
date: 2026-05-20
---

# slice-intent-contract: Slice intent contract — TRIAL-C frontmatter shape, operator gate, append-effective-once amendment policy

## Status

Accepted, provisional. Provisional firmness reflects this ADR's nature as a *trial commitment* — the architectural shape is locked enough to execute, but the trial's close-out verdict may invalidate or refine specific clauses. Supersession after trial close is the expected re-evaluation point.

## Date

2026-05-20

## Context

Trial A (`docs/plans/2026-05-13-cairn-as-interaction-protocol.md`, landed at commit `53a7c58`, INV-002 closed at commit `d35ded5`) bound a frontmatter `contract:` block to `.claude/handoff.md`. Trial B (`docs/plans/2026-05-14-cairn-adr-contract-trial-b.md`, closed at commit `45c31a8`, verdict at commit `a0e3fe6`) bound a contract block to `docs/adr/identifier-scheme.md`. Both shipped; both are firm-bound. The contract pattern has been demonstrated on two unlike surfaces (agent-to-agent handoff; validator-to-filesystem identifier scheme).

The handoff thread tracking what comes next (`.claude/handoff.md` open pointer to the interaction-protocol plan) was the open question entering this /decision. The full Phase 0–Phase 3 record lives in `.claude/skill-runs/interaction-protocol-next-phase-2026-05-20/`. Four approaches were enumerated:

- RETROFIT — apply the Trial B contract to the deferred legacy artifacts (14 ADRs missing `name:`, 6 slice-id violations)
- TRIAL-C — bind a contract to slice `intent.md`, the most-LLM-authored artifact in the methodology
- TIGHTEN-FIRST — refine the contract-block shape itself via a consolidating grammar ADR before extending to a third surface
- FREEZE+DISTRIBUTE — pause the trial sequence; resume M5/M7 distribution work (Node-20 deadline `#32` at 2026-06-02; `delivery-mechanism-friction` impl slice `#33`)

Phase 3 stress-tested the survivors. TIGHTEN-FIRST self-eliminated under honest reading (premise contestation: the "too strict" verdict applied to *plan-level* contract execution-scope, already fixed by `[[adr-contract-execution-scope-clause]]`, not to the contract-block shape). RETROFIT eliminated as primary (produces no protocol-shape learning; the operator's stated framing presumes trial-iteration value, which RETROFIT does not serve). The real choice was TRIAL-C vs. FREEZE+DISTRIBUTE; both owned their critiques honestly, neither has a disqualifying flaw. The choice axis is operator priority — *"learning velocity per session"* favours TRIAL-C; *"calendar pressure + external signal as next-needed evidence class"* favours FREEZE+DISTRIBUTE.

This ADR records TRIAL-C as the default per the synthesis recommendation. The FREEZE+DISTRIBUTE alternative is recorded in `## Alternatives Considered` and `## Risk Register` so that flipping the decision on operator-priority signal is cheap.

### Why TRIAL-C specifically targets slice intent.md

Slice `intent.md` is the most LLM-authored, most-prone-to-rubber-stamping artifact in the cairn methodology. Phase 1 (Reader) authors it from plan + ADR context; Phase 2 (Skeptic) consumes it as its sole input for RED-test design (per `commands/claude-code/.claude/skills/cairn-tdd-feature/SKILL.md` line 13 — forward-blind isolation). If a contract pattern can survive at this rubber-stamping target, it earns evidence the pattern generalizes from deterministic-consumer surfaces (Trial A handoff; Trial B identifier-scheme) to LLM-consumer surfaces.

### Why not after TIGHTEN-FIRST

TIGHTEN-FIRST's candidate refinements (audience tags, must-satisfy-optional, versioning) are intuitive but un-evidenced. The shape held at N=2 across unlike artifact types without amendment. Trial C is the third instance whose stress (operator-review-facing semantic clauses) will surface the *actual* refinements needed. Tightening N=2 ahead of the third instance over-fits.

## Decision

### D1 — Trial C scope: slice intent.md contract

Phase 1 (Reader) writes `intent.md` with a YAML frontmatter `contract:` block carrying the Trial-A/Trial-B four-clause shape (`must-satisfy`, `must-not-violate`, `wrong-if`, `evidence`) plus optional `execution-scope` per `[[adr-contract-execution-scope-clause]]`. Each `must-satisfy` clause carries a `clause-id`. Clauses derive from the intent's Risk Surface and Feature-Local Invariants sections (already required by `.claude/agents/phase-1-tdd.md:17-19`). Non-derivable clauses trigger RAISE_ISSUE.

### D2 — Validator class: deterministic structural + citation binding (no LLM-judge)

The contract validator is two-layer, both deterministic:

- **Layer 1 — `tests/unit/test_intent_contract.py`**: well-formedness checks. Frontmatter parses; all four clause keys present; clause-ids unique; each must-satisfy clause length-bounded (≤120 chars per Trial B precedent); evidence paths resolvable on filesystem.
- **Layer 2 — clause-id citation binding**: Phase 2 cites `clause-id` in test docstrings; Phase 4 sweep grep-binds clause→test and emits coverage map. No semantic judgement in the binding mechanism itself.

Semantic judgement is bounded human attention at two checkpoints: Step 5.5 (operator review of committed intent + contract) and Phase 4 close (operator spot-checks coverage map). Layer 1 stays inside `[[invariant-binding-strategy]]/D1`'s reserved `structural-parser` envelope; Layer 2 is a Phase 4 audit, not a new validator type.

**LLM-judge validators are explicitly rejected.** They introduce non-determinism into the validator layer, contradict `[[invariant-binding-strategy]]/D1`'s validator-type whitelist, and recreate the rubber-stamping risk the contract pattern was designed to defeat.

### D3 — Step 5.5: asynchronous operator gate

The `cairn-tdd-feature` skill grows a Step 5.5 between Step 5 (Phase 1 commit verification) and Step 6 (Phase 2 dispatch). Step 5.5 writes a marker file to the skill-run workspace, prints a banner with the rendered contract block, and exits. Control returns to the operator. The operator inspects the committed `intent.md`, then either re-invokes the skill (resumes Step 6; the skill deletes the marker on re-entry) or hand-edits the intent first per D4 and then re-invokes.

The gate is **asynchronous and harness-native** — the existing Claude Code harness already returns control between Agent calls. The pause primitive is ~20 lines of checkpoint-on-marker logic in the skill, not a new harness feature.

The gate is NOT an in-session Phase-1 restate; that would violate `.claude/agents/phase-1-tdd.md:21` ("No same-session restate gate"). It is operator review of the *committed* artifact between agent dispatches.

### D4 — Append-effective-once amendment policy for non-ADR contracts

Intent contracts are append-effective-once for the lifetime of a slice. Once Phase 1 commits the intent.md, the contract block is frozen for that slice. Amendments require operator action — either before Phase 2 dispatch via Step 5.5 (hand-edit + skill re-invoke; allowed because `AGENT_ROLE` is unset for the operator, so `role_guard.py` does not block writes to `.claude/skill-runs/`), or mid-slice via the existing RAISE_ISSUE → triager-tdd → ESCALATE_TO_USER chain (`SKILL.md:78-83`). Phase 2/3/4 agents and triager-tdd never re-edit a committed intent.md autonomously.

Permissive amendment schemes (e.g., triager-tdd re-dispatching Phase 1 with a pre-amended contract) are explicit future work, not in TRIAL-C scope.

### D5 — Trial commitment

TRIAL-C is one trial slice running Phase 1 → Phase 2 → Phase 3 → Phase 4 under the new contract shape, with operator verdict recorded in the close-out file at `.claude/skill-runs/slice-intent-contract-trial-c/close-out.md`. The verdict answers:

- **Works:** contract surfaced an ambiguity Phase 2 would have rubber-stamped from prose
- **Too strict:** contract clauses over-constrained Phase 1 output or Phase 2 test design
- **No-signal:** contract restated what prose already said; no new clarity

A "Works" verdict promotes the shape from trial-scope to default for future slices; future SKILL.md amendments make the contract block required. "Too strict" or "No-signal" feeds the next-phase /decision.

### D6 — Sequencing carve-out

The `#32` Node-20 deprecation deadline (2026-06-02, 13 calendar days from this ADR's date) is committed to be executed inline before TRIAL-C session 1 begins. This is a separate maintenance task and explicitly NOT enabling work for the intent contract (it does not appear in `execution-scope:` above per `[[adr-contract-execution-scope-clause]]/D2` — listed targets must serve the arc that owns the contract, and the Node-20 bump does not). The carve-out is recorded here to make the calendar commitment explicit, not to bundle the two arcs.

## Consequences

**Easier:**

- A working intent-contract becomes the template for future slices. Phase-1 artifact quality becomes structural, not pure operator discipline. Floor rises corpus-wide.
- Step 5.5 is reusable by any future skill needing "operator confirms artifact before next dispatch." Closes the gap captured in operator memory `feedback_intent_is_the_contract`.
- Phase 4 clause-id coverage map gives audits a machine-readable scope. Today, Phase 4 audits arbitrary invariants from prose; with TRIAL-C, the audit has a structured target.
- The contract pattern's validator-class design (Layer 1 deterministic + Layer 2 citation binding) gives future LLM-consumer surfaces a template that avoids LLM-judge non-determinism.

**Harder:**

- Two new policies enter the methodology: append-effective-once intent contracts (D4) and the Step 5.5 operator gate (D3). Both are tested by use; if either proves friction, supersession is the remedy.
- Phase 1 latency grows by one checkpoint per slice (~5–15 minutes operator review time). Trial-B contracts are 16 lines; intent contracts will likely be similar bounded.
- A future TIGHTEN-FIRST consolidating-grammar ADR (post-Trial-C) coexists with the shipped clause-id field. Migration is per-new-slice, not corpus-wide.
- The Layer-2 binding is *form*, not *semantics*: Phase 2 can cite the wrong clause-id and the coverage map still says "covered." This is the strongest residual risk; see Risk R2.

## Alternatives Considered

**Alternative A — RETROFIT (apply Trial-B contract to legacy artifacts).** Steelman at `.claude/skill-runs/interaction-protocol-next-phase-2026-05-20/04a-approach-retrofit.md`. **Eliminated** because RETROFIT produces no protocol-shape learning — the contract is already proven at the validator-facing surface; applying it to 14 stale ADRs validates nothing new. RETROFIT remains viable as an in-arc sub-task during a future session if the operator wants to drain the deferred audit; this ADR does not gate that.

**Alternative B — TIGHTEN-FIRST (consolidating contract-grammar ADR).** Steelman at `.claude/skill-runs/interaction-protocol-next-phase-2026-05-20/04c-approach-tighten-first.md`. **Eliminated** because the motivating premise (Trial B's "too strict" verdict signals structural brittleness in the contract block shape) was contested in Phase 1 and the contestation held: the "too strict" verdict applied to plan-level execution-scope, already fixed by `[[adr-contract-execution-scope-clause]]`. The reframed motivation (consolidating grammar for reader-disambiguation) is documentation-optimization, not protocol-optimization, and with one operator on cairn (`[[identity-and-scope-deferral]]`) reader confusion is speculative. `[[adr-contract-execution-scope-clause]]:116` explicitly defers consolidation until "post-enough-instances" — Trial C is the natural third instance.

**Alternative C — FREEZE+DISTRIBUTE (pause trial sequence; resume M5/M7 distribution).** Steelman at `.claude/skill-runs/interaction-protocol-next-phase-2026-05-20/04d-approach-freeze-distribute.md`. **Recorded as the active alternative**, not eliminated. The motivating claim — that the operator's actual priority is external-distribution-first — is BELIEVED, not VERIFIED. If operator priority signal shifts to "ship what's stable; let external use produce the next signal class," this ADR is the right candidate for supersession. The pivot is cheap: this ADR is provisional; superseding it requires a new ADR plus updated frontmatter (`status: superseded`, `superseded-by:`). The carve-out for `#32` Node-20 in D6 preserves the most calendar-pressured piece of FREEZE+DISTRIBUTE inside TRIAL-C, so deferring the rest of distribution does not strand the deadline.

**Alternative D — Full forced-pause (do neither TRIAL-C nor distribute; request external feedback first).** Not enumerated in Phase 2 because the operator memory notes (`feedback_use_superpowers`, `feedback_steelman_before_deferring`) and the synthesis itself converge on "default to action with explicit pivot point." Recorded here for completeness.

## Risk Register

| # | Scenario | Severity | Handling in this ADR |
|---|----------|----------|----------------------|
| R1 | Layer-2 clause-id citation binding is form, not semantics: Phase 2 cites the wrong clause-id, coverage map says "covered," underlying assertion enforces something else | Possible / medium | D2 acknowledges; mitigation is bounded human attention at Phase 4 close (operator spot-checks coverage map for at least one clause/test pair). If R1 recurs, Phase 4 prompt amendment to require clause-text quotation in test docstrings becomes a supersession-class fix. |
| R2 | Trial close-out verdict is "no signal" — the contract block restates prose intent without surfacing ambiguity Phase 2 would have rubber-stamped | Possible / medium | A "no signal" verdict is itself informative (the pattern does not generalize to LLM-consumer artifacts). Feeds the next /decision toward TIGHTEN-FIRST or FREEZE+DISTRIBUTE. Not a defect of this ADR; a designed-in falsifiability. |
| R3 | Step 5.5 operator review at >15 min/slice — contract too dense, operator can't scan it | Possible / low | `wrong-if` clause in this ADR's own contract makes this a falsification trigger. Mitigation: Trial-B contracts are 16 lines; intent contracts target similar bound. If exceeded, Phase 1 prompt tightens. |
| R4 | Operator priority shifts mid-trial to FREEZE+DISTRIBUTE | Possible / medium | Provisional firmness; supersession is inexpensive. This ADR's `## Alternatives Considered` records FREEZE+DISTRIBUTE as the active alternative so the pivot is well-scoped. |
| R5 | `#32` Node-20 bump (D6 carve-out) drifts past 2026-06-02 because TRIAL-C session 1 starts before the bump lands | High if missed / low likelihood | D6 explicitly commits to inline execution *before* TRIAL-C session 1. Operator memory `feedback_use_superpowers` reminds calendar-pressed tasks get hook priority. Mitigation: handoff thread `#32 open Node-20-deadline-2026-06-02` stays open until the bump commits. |
| R6 | TRIAL-C produces a fourth de-facto contract grammar variant (operator-facing) that later consolidation cannot absorb cleanly | Possible / low | D1 explicitly reuses the Trial-A/Trial-B four-clause shape; no new clause types are introduced. The only new structural element is `clause-id` on must-satisfy entries, which is additive. Future consolidating-grammar ADR can absorb cleanly. |
| R7 | Mid-slice agent (Phase 2/3/4 or triager-tdd) hand-edits intent.md and bypasses operator escalation | Possible / low | D4 explicitly forbids; `role_guard.py` already enforces phase-1-tdd as the only role writing intent.md. Defense-in-depth via the existing role lock. |

## Cross-references

- Decision arc record: `.claude/skill-runs/interaction-protocol-next-phase-2026-05-20/` (00–05)
- Trial A: `docs/plans/2026-05-13-cairn-as-interaction-protocol.md`, commits `53a7c58` (Trial A landed) and `d35ded5` (INV-002 closed against Trial A shape)
- Trial B: `docs/plans/2026-05-14-cairn-adr-contract-trial-b.md`, commit `45c31a8` (closed), commit `a0e3fe6` (verdict)
- Related ADRs: `[[identifier-scheme]]` (Trial B target; contract-block shape source), `[[adr-contract-execution-scope-clause]]` (execution-scope grammar adopted by this ADR), `[[schema-amendment-threshold]]` (N≥3 trigger; not invoked here since this is a first-instance landing on a new surface, not a schema widening), `[[invariant-binding-strategy]]` (validator-type reservation), `[[phase-lock-and-role-declaration]]` (phase topology preserved — Step 5.5 is a gate, not a phase), `[[identity-and-scope-deferral]]` (companion ADR; FREEZE+DISTRIBUTE alternative motivated partly by deferred-pivot framing)
- Operator memory: `feedback_intent_is_the_contract` (Phase 1 review gate gap), `feedback_plan_contract_scope_separation` (execution-scope enumeration), `feedback_steelman_before_deferring` (Phase 2 dispatched a steelman of FREEZE+DISTRIBUTE before this ADR settled on TRIAL-C)
- Trial plan (to be authored as enabling work per D1 execution-scope): `docs/plans/2026-05-20-cairn-trial-c-slice-intent-contract.md`
