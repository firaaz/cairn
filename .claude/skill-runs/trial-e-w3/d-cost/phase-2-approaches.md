# D-cost — Phase 2: candidate resolutions

Three resolutions for `intent-contract-cost-model` D3. All are operator-bound; this
is prep, not a call. Read attack.md first — it establishes the load-bearing finding
(**D5 is unmeasured, not measured-and-failed**) that all three must reckon with.

---

## Approach A — Commit the heavy-band bundle now

Ship derived banding + promise↔clause traceability + agent-declared/challenger-
attacked severity + the front-loaded fidelity challenge, as one plugin-release bundle.

**Best affirmative case (steelman):**
- The front-challenge is a **scope-ceiling, not a severity-floor**. Every dp1–5
  catch was a grounding/scope defect — the work said something the source didn't
  support. L-028 / ceiling-not-floor names a defect the front-challenge *structurally
  cannot see*: a grounded, atomic, within-promise clause that drafts the floor away
  (`validator shall report a result` → `log-and-exit-0`). Only declared+attacked
  *severity* makes the floor an attackable object.
- **"Unobserved" is the predicted signature, not absence.** The distinguishing
  signal (post-close defect-escape) is silent, slow, sample-starved by construction
  (S6). n≈8 over weeks on one operator will *always* read as "no floor-defect" — citing
  that as license to not-build is the S4 self-deception.
- **Scale value has no signal in dp1–5.** Derived banding + traceability are *scale*
  properties; every dp ran on small, repo-writing intents. The bundle's payoff is on
  heavy multi-clause downstream-consumer work (complex-rag-analysis class) never touched.

**Cost / honest weakness:** spends m2-**confirmed** authoring cost + unsolved O(n²)
traceability + distribution-staleness against a benefit **no datapoint demonstrates**.
The affirmative rests entirely on *structural* argument, not field data — and on the
one class tested (slice-#25) the cheap baseline already saturates (W1: 0 misses, no
headroom). This is "commit because the front-challenge provably can't see the floor
class," **not** "commit because we saw it fail." Inverts the cost-model ADR's own
discipline ("don't ship enforcement machinery against unmeasured value").

---

## Approach B — Retire the ambition outright

Supersede D3: drop the deferred bundle, let the cost-model ADR's cheap layer (D1 + D2)
stand as the terminal design. The graduated-mandate alternative
(`intent-contract-cost-model:107`) is the recorded supersession candidate if needed.

**Case for:**
- The cheap layer the data *did* validate — thin prose intent (D2, shipped) + front
  intent-challenge (existing gate) — carried the load on the tested class: dp2 clean
  + discriminating, dp3 front 5/5, W1 cross-family 5/5. dp3's **front-loaded** finding
  says even the *second* checkpoint is a conditional backstop, so the bracket is
  effectively single-strong-checkpoint — which performed.
- Honors "commit only what evidence supports" + "cut before adding": don't carry a
  deferred ambition the trial gave no positive signal for; close the loop cleanly.

**Cost / honest weakness:** **over-claims.** "Retire the ambition" reads as "the value
question was settled negative." It wasn't — attack.md shows the formal layer was never
exercised, so the floor/structural-defect class the bundle targets was **never tested**.
B risks declaring victory on a question the data didn't answer (the same S4 self-deception
one level up that `measure-before-enforce` named). Leaves the ceiling-not-floor mode with
**no** named defense and **no** revival hook.

---

## Approach C — Retire the build, keep the watch (recommended)

Adjudicate D5 honestly as **unmeasured-not-failed**. Do **not** commit the speculative
bundle (no value signal at confirmed cost → A is unjustified today). Do **not** declare
the ambition dead (B over-claims). Instead:

1. **Decline to commit** the heavy machinery (banding + traceability + severity grammar
   + heavy `## Contract`) — unproven value, unsolved O(n²)/distribution cost.
2. **Keep the cheap layer** that the data validated: thin prose intent (D2, shipped) +
   front intent-challenge (existing). Affirm the **front-loaded** model from dp3 as the
   loop's terminal fidelity posture for now.
3. **Re-bind the residual floor risk** (ceiling-not-floor, same-family ~60% residual) to
   `measure-before-enforce`'s already-committed instruments — its D3 decoy/recall pilot
   and D2 cross-family log — with a **pre-registered revival trigger**: *reopen D3 via
   `/decision` iff a real floor-defect-escape is observed in dogfood OR a genuinely
   heavy multi-clause downstream intent demonstrably under-covers under the front gate.*
   That reopen must put the **formal layer actually in the loop** against a structural/
   floor defect class — the measurement D5 nominally required and Trial E never ran.

**Case for:** matches the evidence exactly — commits nothing on unmeasured value, retires
nothing on unmeasured absence, and keeps the floor concern alive against the *correct*
instruments instead of building O(n²) machinery speculatively. Disciplined posture per
operator memory ("commit only what evidence supports"; "measure over more decisions" —
but here Trial E already *was* the measurement and it pointed at the cheap layer).

**Cost / honest weakness:** not a clean binary close — leaves D3 in a third "deferred-
again-but-narrowly" state, which can read as indecision. Mitigated by the **sharp,
pre-registered** trigger (not an open-ended "revisit later"). Also accepts the same
slow/silent detection risk B does — if the floor mode is real, the decoy pilot may be the
only thing that surfaces it, and it could surface late.

---

## Comparison

| | A — Commit | B — Retire outright | C — Retire build, keep watch |
|---|---|---|---|
| Honors "unmeasured-not-failed" | no (claims pass) | no (claims fail) | **yes** |
| Spends confirmed cost on unmeasured value | **yes** | no | no |
| Leaves floor risk with a named defense | yes (built) | **no** | yes (decoy pilot + trigger) |
| Closes the loop cleanly | yes | yes | partial |
| Reversible if wrong | costly (built+distributed) | needs new ADR | **cheap (trigger fires)** |
