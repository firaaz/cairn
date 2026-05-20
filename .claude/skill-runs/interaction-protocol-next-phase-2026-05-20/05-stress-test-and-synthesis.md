# Phase 3 — Adversarial Stress Test and Synthesis

## Pre-elimination

Two of four approaches collapse under honest reading of their own steelmen:

### TIGHTEN-FIRST — eliminate

`04c-approach-tighten-first.md:58` self-states: *"Forced-enumeration honest verdict: TIGHTEN-FIRST is the weakest of the three branches when calendar-time and learning-velocity dominate, and the strongest only if the operator's actual constraint is 'stop accreting implicit grammar variants before the count passes three.'"*

The reframed motivation (consolidating grammar) survives Phase 1's premise contestation but reduces TIGHTEN-FIRST to documentation-optimization. With one operator on cairn (`identity-and-scope-deferral.md:33`), reader-disambiguation is speculative; `adr-contract-execution-scope-clause.md:116` explicitly defers consolidation until "post-enough-instances," and Trial C *is* the natural third instance. TIGHTEN-FIRST today is solution looking for a problem.

### RETROFIT — eliminate as primary; viable as sub-task

`04a-approach-retrofit.md:61` self-states the killer attack: *"easy work is the wrong selection criterion when the operator is trying to validate a methodology."*

The approach is mechanically sound — title-collision policy is explicit, baseline-decrement is atomic, `substrate/orchestrator-paths` is honestly surfaced as watching-mark 1/3. But RETROFIT produces zero protocol-shape learning. If the operator's framing "do C" presumes the /decision picks among trial-iteration options, RETROFIT is not in that frame; it's deferral dressed as productivity. Viable as a within-session sub-task during a larger arc, not as the primary answer.

## Real choice: TRIAL-C vs. FREEZE+DISTRIBUTE

These two are not interchangeable — they answer different questions:

- **TRIAL-C** answers: *"What's the next trial that pressure-tests the contract pattern?"*
- **FREEZE+DISTRIBUTE** answers: *"Is more in-repo trial-iteration still the highest-value activity?"*

The first question accepts the operator's framing. The second challenges it. Both deserve honest stress-testing.

## Stress test — TRIAL-C

### Disconfirming search

- **Verified gap #2 (semantic-drift validator class) is owned but residual remains.** The Layer-2 mechanism — Phase 2 cites `clause-id` in test docstrings; Phase 4 grep-binds clause→test — is form-binding, not semantic. Phase 2 can cite the wrong clause; coverage map says "covered," underlying assertion doesn't enforce the cited clause. The agent's Trial-B analogy (`04b-approach-trial-c.md:54`) holds for filesystem clauses but degrades for aspirational ones like *"Specification names observable behavior."* A test docstring `"# clause: spec-observable"` paired with `assert intent['Specification']` is form-bound but semantically vacuous.
- **Operator-gate (Step 5.5) is real new surface.** SKILL.md amendment + 20-line marker-file pause primitive + new policy ("append-effective-once") + new operator review point. Each is reasonable; the aggregate is "TRIAL-C is a protocol expansion masquerading as a trial." The agent calls this "enabling work" and cites `feedback_plan_contract_scope_separation.md` — defensible, but the trial's stated value (validate contract on intent) and its enabling work (add a synchronous operator gate to cairn-tdd-feature) are not obviously co-priced.
- **The bet may lose.** Honest acknowledgment at `04b-approach-trial-c.md:97`: *"If the verdict is 'contract added no clarity Phase 2 didn't get from prose,' 2-3 sessions buy a negative result on whether the pattern generalises to LLM-consumer artifacts."* A negative result is still informative — but only if the operator is prepared to accept it.

### Steelman of TRIAL-C's runner-up (FREEZE+DISTRIBUTE attack on TRIAL-C)

FREEZE+DISTRIBUTE argues TRIAL-C's signal class is misaligned: cairn has one operator; all "external" use is operator dogfooding. Trial B's "too strict" verdict came from operator dogfooding (`03-premortem.md:36-37`). A third internal trial yields more of the same signal class. The categorical gap to *external-consumer* signal (the audience the contract pattern was designed for) cannot be closed by TRIAL-C.

This is a real attack. TRIAL-C's response is that semantic-drift detection is a *different stress* from external-consumer mismatch — slice intent is the hardest in-repo rubber-stamp target, and the gate UX is its own deliverable. That defense holds: TRIAL-C tests a stress no external consumer would generate (intent.md is internal to the dispatch skill). But the cost-evidence ratio narrows.

### Assumption audit

| Assumption | Status | Failure mode |
|---|---|---|
| Layer-1 + Layer-2 validator preserves D1 | **VERIFIED** by reading `invariant-binding-strategy.md:38` reserved-types list | If LLM-judge slips in later via "small judgement helper," D1 silently bends |
| Phase 2 will cite contract clauses faithfully | **BELIEVED** | Phase 2 may cite wrong clause; coverage-map binding is form not semantics |
| Trial-B's contract-shape generalises to LLM-consumer artifacts | **BELIEVED** | The bet TRIAL-C explicitly makes; honest acknowledgment of possible negative result |
| Operator has 2-3 sessions of attention for the trial | **BELIEVED** (no calendar signal in handoff or memory) | Calendar pressure (#32 Node-20 deadline 2026-06-02) competes |
| Step 5.5 marker-file pause primitive is ~20 lines, not a harness change | **VERIFIED** by reading SKILL.md flow — harness already returns control between Agent calls | If operator expects a UX-polished pause, scope expands |

## Stress test — FREEZE+DISTRIBUTE

### Disconfirming search

- **Cross-branch failure #1 — the motivating attack — is BELIEVED, not VERIFIED.** Phase 1 named the meta-constraint as "may be." There is no signal in `.claude/handoff.md`, recent commits, or memory that the operator's actual priority is external-distribution-first. The /decision protocol is meant to surface such meta-questions, but a strong steelman of "the operator's stated framing is wrong" needs a strong evidentiary base, and that base is at best inferential here.
- **Self-admitted symmetric risk holds.** `04d-approach-freeze-distribute.md:69`: distribution is *also* "many small editorial decisions" — D6 token-budget enforcement scope, which nav agents land in v0.2.0 vs. defer, whether the manual-update procedure is surfaced loudly enough. The RETROFIT-mechanical critique transfers. Distribution is not low-decision-weight just because it's downstream-facing.
- **Re-emergence failure scenario (self-admitted #3) is real.** Freeze + 3 months of distribution shifts ground state. The TRIAL-C / TIGHTEN-FIRST / RETROFIT branches as designed against 2026-05-20 codebase become Chesterton's-fence material: present in handoff but no longer trustworthy.
- **Separability assumption is weak.** `04d:71`: *"Honest reading: trial sequence and distribution track are not as separable as the FREEZE framing claims."* If the impl slice for `delivery-mechanism-friction` (#33) hits a contract-pattern-shape problem mid-execution, FREEZE either crosses its own freeze line or ships with a known gap. The freeze is operator-discipline, not mechanical.

### Steelman of FREEZE+DISTRIBUTE's runner-up (TRIAL-C attack on FREEZE+DISTRIBUTE)

TRIAL-C argues distribution can wait but the trial sequence has internal momentum: Trial A + Trial B + the execution-scope ADR have built a pattern; the third instance is the natural next step. Letting that momentum dissipate (3 months frozen) means re-derivation cost later. Furthermore, Node-20 deadline (#32) is a *single small task*, not a substitute for trial-iteration — the agent's claim that #32 "sets the calendar" overweights one CI bump into a strategic pivot.

This is a real attack. FREEZE+DISTRIBUTE's response is that the trial sequence has produced what it can produce on one operator's dogfooding; external use is the next-needed evidence class. Defense partially holds — but the "what it can produce" claim is itself contestable (TRIAL-C explicitly identifies stresses Trial A/B didn't surface).

### Assumption audit

| Assumption | Status | Failure mode |
|---|---|---|
| Operator's actual constraint is "ship what's stable," not "validate the methodology further" | **BELIEVED** (Phase 1 named as "may be") | If wrong, FREEZE refuses an operator-stated goal without authorization |
| External use will produce contract-shape signal within 30 days | **BELIEVED** (`delivery-mechanism-friction/R4`) | If no consumers, freeze produces no signal — unfalsifiable claim |
| #32 Node-20 deadline (2026-06-02) is a hard external constraint | **VERIFIED** (calendar fact) | Mitigated by being a single small task; not load-bearing for the whole approach |
| Trial sequence and distribution track are independently advanceable | **BELIEVED** (self-contradicted at 04d:71) | If a distribution slice surfaces contract-shape issue, freeze breaks |
| The deferred retrofit + un-tested intent contract are acceptable carrying costs | **BELIEVED** | If a regression surfaces during distribution that an un-run trial would have caught, freeze is regretted |

## Synthesis

Two viable approaches, each strongest under different operator priorities:

| Operator priority | Strongest approach |
|---|---|
| Learning velocity per session; methodology validation as the active project | **TRIAL-C** |
| Calendar pressure (Node-20 + delivery-mechanism shipping); external signal as next-needed evidence class | **FREEZE+DISTRIBUTE** |
| Equally weighted but bandwidth-constrained | TRIAL-C as primary, with #32 Node-20 bumped as a small in-arc task before the deadline |

**Neither approach has a serious flaw that disqualifies it.** Both own their critiques honestly. The choice is over what the next-needed evidence class is.

### Recommendation

Default to **TRIAL-C as the primary answer**, with two carve-outs:

1. **#32 Node-20 bump executed inline.** 13 days to 2026-06-02; treating it as TRIAL-C's first session-zero task (small, time-pressured, non-conflicting) honors the deadline without abandoning the trial.
2. **Pre-trial operator decision point:** before TRIAL-C session 1 begins, the operator confirms (or pivots to) FREEZE+DISTRIBUTE on the priority axis above. If the priority is "ship what's stable now, validate via external use later," this entire /decision's verdict should flip to FREEZE+DISTRIBUTE, and the unused trial branches get a "deferred" entry in `.claude/handoff.md`.

The reason for this shape rather than a clean pick: the load-bearing claim in FREEZE+DISTRIBUTE (operator priority is external-distribution-first) is BELIEVED not VERIFIED, and the /decision protocol's job is to surface that to the operator, not preempt it. Defaulting to TRIAL-C respects the stated "do C" framing; the pre-trial pivot point gives the operator one explicit chance to reframe before commitment.

### What the ADR should record

- **Decision:** next phase of the cairn-as-interaction-protocol reframe is TRIAL-C — bind a `contract:` block to slice `intent.md`, scoped as a single trial with permitted enabling work (Step 5.5 operator gate; append-effective-once amendment policy; `test_intent_contract.py` deterministic Layer-1 validator).
- **Firmness:** provisional. This is a sequencing/trial decision, not an invariant amendment. Provisional firmness keeps the door open for a Phase-5-style re-evaluation after the trial closes.
- **Alternatives considered:** RETROFIT (eliminated — no protocol learning), TIGHTEN-FIRST (eliminated — self-admitted weakest, motivating premise contested), FREEZE+DISTRIBUTE (the active alternative; surface the priority axis explicitly so re-opening the decision is cheap).
- **Risk register:** the four pre-mortem failures TRIAL-C engaged with (operator-gate scope, semantic-drift validator class, phase isolation, amendment authority) plus the assumption-audit residuals (clause-citation form vs. semantics; possible negative result on LLM-consumer artifacts).
- **Carve-out:** #32 Node-20 deadline is in-arc maintenance, not a separate trial.

## Skip Phase 5?

The decision is sequencing + scoping a trial, not amending an invariant. Firmness should be `provisional` per `identifier-scheme.md` firmness vocabulary — provisional decisions are expected to be revisited as the project learns more (decision.full Phase 5 rule: skip independent verification for provisional decisions). The trial close-out is itself a natural re-evaluation point.
