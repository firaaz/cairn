# D-cost — Phase 0.5: journey trace

How the heavy-band bundle got deferred to Trial E, and what binds the call now.

## 1. The cost finding (Trial D, m2)

Trial D's m2 measurement **halted** when the operator found hand-authoring the
EARS contract painful even on the lightest intent
(`.claude/skill-runs/trial-d-measurement/README.md`). The operator confirmed
heavy-band authoring cost is a **recurring driver, not an n=1 artifact**. This is
the *cost* leg — and per operator memory, **"cost confirmed ≠ enforcement value
confirmed."** That gap is the entire story below.

## 2. The over-commit and the trim (`intent-contract-model` /decision, 2026-05-31)

A subagent-driven `/decision` explored a **full band-dependent promise model** —
band rule + `traceability_guard` + `severity` + a fidelity challenge. On operator
review the draft **over-committed**: it shipped *enforcement machinery whose
catching-value is unmeasured* to justify a *cost-model* decision, defaulted users
into ceremony, and buried the elegant idea. The ADR was trimmed to keep only what
evidence supports:

- **D1** — the invariant (user approves promise, agent owns proof).
- **D2** — cost-*removal*: agent drafts EARS; light work = thin prose only. Bets
  nothing on the formal layer's value.
- **D3** — the enforcement bundle **deferred**, "gated on Trial E showing the
  formal proof adds value under the agent-owned model."
- **D5** — Trial E measures exactly that. **This is the gate D-cost adjudicates.**

The bundle's mechanisms were preserved as **deferred design constraints**, not
discarded — so the follow-on would not re-derive them.

## 3. The measurement program (`measure-before-enforce`, 2026-06-01)

Opened on the Step-3a rubber-stamp. A steelman panel + adversarial pass **reversed
the obvious redesign** and committed **measure-only**: D1 (populate the fidelity
baseline), D2 (instrument same- AND cross-family co-miss), D3 (decoy + active-recall
pilot). Crucially it states it **feeds `intent-contract-cost-model` D5, does not
supersede the deferral** (`:47`, `:92`). It is the instrument that was supposed to
generate D5's pass/fail data.

## 4. Trial E ran (dp1–5 + W1)

| datum | what it exercised | result | what it actually measured |
|---|---|---|---|
| dp1 | front intent-challenge | caught a semantic over-read `premise_guard` couldn't | front-challenge value; **n=1, self-referential vehicle** |
| dp2 | de-primed front-challenge | blocked slice-#25 class, generalized, discriminated | front-challenge capability floor; constructed harness |
| dp3 | both checkpoints, n=3 defects | front 5/5, close 4/5, **0/3 co-miss** | **fidelity is front-loaded**; close-review = conditional backstop |
| dp4/dp5 | **live cairn-intent dogfood** | no co-miss; front-challenge + close-process catches | the loop on **thin prose intents** — heavy contract never present |
| W1 | cross-family Codex front-challenger | 5/5, **parity**, no improvement | front-challenge cross-family; corpus reconstructed in-session |

## 5. The binding observation for D-cost

Every Trial-E datum exercised the **front intent-challenge** (an *existing* gate)
over **thin / prose** intents. The dogfood runs (dp4/dp5) explicitly used thin
prose — **the heavy-band formal contract was never in the loop in any datapoint.**
So the program built to generate D5's data measured the *baseline*, not the
*treatment*. The journey's central irony: Trial D proved the heavy layer is
*costly*; Trial E measured a *different* layer (the front-challenge) and found *it*
strong — leaving the heavy layer's marginal value exactly where D3 left it:
deferred and now **unmeasured, not failed** (see attack.md).

D3 revisit also engages `identity-and-scope-deferral` (trigger #4 binds the sibling
D-retire arc); D-cost's own trigger is D5's pass/fail, which `measure-before-enforce`
`:92` restates as "pass = commit the bundle; fail = retire the ambition."
