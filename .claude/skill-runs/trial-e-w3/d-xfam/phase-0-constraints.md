# D-xfam — Phase 0: constraint envelope

Decision: commit `measure-before-enforce` **B** (cross-family fidelity challenger as
*committed* enforcement) — or record the pre-set trigger as **not met** and keep B deferred.
This packet is decision-prep only: **no call, no ADR.**

## Fixed (binds the decision)

1. **The pre-recorded trigger — verbatim** (`intent-fidelity-measure-before-enforce.md:90`):
   > "Cross-family co-miss delta (D2) materially below same-family ~60% on the
   > fidelity-leap class → open a `/decision` to commit B (cross-family enforcement)."
   The decision must adjudicate against *this* condition. It is the gate; nothing else
   authorizes committing B early.

2. **How "~60%" must be read.** The "~60%" is the Kim-et-al same-family error-agreement
   prior (`intent-contract-cost-model/D3:97`, EXPOSED) — a *literature* number, not a cairn
   measurement. The ADR's own metric discipline forbids trusting it for cairn's class:
   - S3 (`:79`): "the same-family challenger stays as-is; D2 *measures* its miss rate
     **rather than trusting it**."
   - D5 (`:49`): success judged on the **generated signals** (cross-family co-miss delta,
     operator-miss-vs-challenger-catch), never an imported prior or a time target.
   Constraint: the operative comparator is the **measured** same-family baseline (dp3 front
   arm = **0/3 miss**), not the imported 60%. (The attack file stresses this — it is the
   single highest-leverage interpretive choice in the decision.)

3. **D5 metric discipline** (`:49`). Forbidden to adopt review-time-under-15-min or any
   disengagement-rewarding target as the success metric. The cross-family co-miss delta is
   the metric of record; post-close defect-escape is the slow backstop.

4. **D4 — committed enforcement is deferred by default** (`:47`): "no committed cross-family
   enforcement (B) … revisited when D2/D3 produce data." Committing B *overturns* this
   standing posture; recording "not triggered" *maintains* it. The burden of proof sits on
   the commit, not the defer.

5. **D6 — no new hooks** (`intent-management-loop`, cited `:35`). Constrains the *mechanism*,
   not the *verdict*: cross-family enforcement, if ever committed, must ship as a skill-step
   challenger swap (Claude drafts / Codex challenges), **not** a PreToolUse hook. D6 does not
   by itself forbid committing B.

6. **This ADR is provisional, supersedes nothing, touches no invariant** (`:17`). So:
   recording "not triggered" is a follow-on note / status confirmation — no Phase 5
   independent verification, no invariant edit. Committing B is the heavier change (new
   committed enforcement + a runtime Codex dependency on the critical path) and must be
   weighed as such.

## Forbidden (claims the close may not make)

- **"Cross-family parity proven"** or **"B falsified."** dp3's front-loaded finding +
  n=3 across both arms forbid any strong positive *or* negative claim. The most the data
  supports is "no measured delta at n=3."
- **"Two independent decorrelation catches."** dp3 shows fidelity is front-loaded; this is a
  D-retire constraint that also bounds how W1 may be cited here.
- **Committed enforcement on an n=3 existence result** without naming the S4/S6 validation
  gap (fast approval ≈ disengagement; defect-escape silent + sample-starved).
- New hooks (D6); time-based success metric (D5).

## Out of scope (brief)

- The D1 baseline-capture + D3 decoy/recall **instrumentation build** — downstream, not a
  Trial-E blocker.
- Writing the final ADR or making the call without the operator (operator-bound by design).
