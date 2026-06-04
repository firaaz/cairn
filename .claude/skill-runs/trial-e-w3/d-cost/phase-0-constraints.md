# D-cost — Phase 0: constraint envelope

Decision: `intent-contract-cost-model` **D3** — commit vs retire the heavy-band
enforcement bundle. Gate is **D5**. This is decision-prep only; the call and any
ADR write are operator-bound.

## What the decision IS (scope)

Adjudicate the **D3 deferred bundle only**:
- derived banding (infer heavy-vs-light from the work, not user-declared)
- promise↔clause traceability (O(pids×clauses))
- agent-declared / challenger-attacked **severity** (the "floor" defense)
- the front-loaded fidelity challenge *carrying that severity machinery*
- the heavy formal `## Contract` layer those fields live in

Ships as **one bundle** via the plugin-release path (constraint 4 below) — the
fields never precede the workflow that drafts them.

## What is FIXED / out of bounds (do not reopen)

1. **D1 + D2 are shipped, not in question.** D1 (user approves the *promise*,
   agent owns the *proof*) and D2 (agent drafts EARS from the promise; **light
   work carries thin prose intent only — no formal contract**) are committed and
   value-independent. The realized form in the loop = **agent-judges-band +
   operator-veto at Step 5a**. The m2 authoring-cost pain is already removed by D2.
   D-cost decides *only* whether to add the enforcement layer on top.

2. **The D5 gate is the adjudication criterion.** "Does the formal proof catch
   anything a **thin prose intent + the existing gates** would not, now that the
   *agent* (not the operator) drafts the formal contract?" Pass → commit; fail →
   retire the ambition (`measure-before-enforce` `:92`). **Read literally, this
   gate requires the formal layer to have been *exercised* against the thin-prose
   baseline.** (attack.md shows it was not — see "unmeasured-not-failed.")

3. **No new hooks.** `intent-management-loop` D6 binds. Any "commit" must ship as
   a skill-step / plugin-release artifact, never a new PreToolUse hook.

4. **The deferred design constraints are unsolved and MUST be answered by any
   "commit"** (`intent-contract-cost-model:75-98`), not by D-cost:
   - **ceiling-not-floor** — a promise bounds *scope*, never the *floor*; a clause
     can be grounded+atomic+within-promise yet ship as `log-and-exit-0` (L-028).
     This is the bundle's whole reason to exist and the risk the data is silent on.
   - **band-must-be-derived** — "whoever picks the band picks whether the floor exists."
   - **quadratic-at-scale** — traceability is O(pids×clauses); a single-pass challenge
     skims at 30+ clauses.
   - **distribution-staleness** — inert on stale `.slice-system` wiring; no global `*_FIX` bypass (L-018).
   - **approval-timing**; **same-family ~60% co-miss residual** (Kim, EXPOSED).

5. **`measure-before-enforce` owns the measurement path and FEEDS this gate — it
   does not supersede it.** Its D1 (baseline capture), D2 (same+cross-family
   instrument), D3 (decoy/recall pilot) generate D5's data. That instrumentation
   build is **downstream, explicitly out of scope for this team** (closure-spec).
   D-cost may *re-bind a revival trigger* to those instruments but must not order
   their build.

6. **W1 feeds, does not settle.** Cross-family Codex front-challenger = 5/5,
   **parity** with same-family, **no measured improvement** (baseline had 0 misses).
   Provenance caveat: cases reconstructed from the dp3 corpus inside the Codex
   session, not freshly Claude-authored. The cross-family *enforcement* trigger
   (`measure-before-enforce` B) is a separate decision (D-xfam) and is **not met**;
   D-cost only borrows W1 as a data point on front-challenge strength.

7. **Firmness ceiling.** The cost-model ADR is **provisional**, supersedes nothing,
   touches no invariant. Committing or retiring D3 does **not** cascade into the
   firm-decision web and needs no Phase-5 independent verification — but it is still
   operator-bound (operator-veto 5a posture).

## Forbidden moves

- Do **not** declare D5 "passed" or "failed" on data that never instantiated the
  formal layer (see attack.md). The honest state is *unmeasured*.
- Do **not** frame any retire on "two independent decorrelation catches" — dp3
  shows fidelity is **front-loaded** (close-review is a conditional backstop).
- Do **not** treat "no floor-defect observed in dp1–5" as "floor risk absent" —
  the failure mode is slow/silent/sample-starved by construction (S6).
