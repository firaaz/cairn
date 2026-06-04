# D-cost — attack-before-synthesis

Two independent adversarial agents (a commit-steelman and an evidence-interrogator,
neither seeing the other) were run on the load-bearing claims before any
recommendation. They converged. Operator memory: default-to-acceptance is the named
failure mode; "cost confirmed ≠ enforcement value confirmed" is the gap to interrogate.

## The load-bearing finding (both agents, independently)

**D5 is UNMEASURED, not measured-and-failed.** Every Trial-E datum — dp1, dp2, dp3,
dp4, dp5, W1 — exercised the **front intent-challenge** (an *existing* gate) operating
over **thin / prose** intents. dp4/dp5 (the only live dogfood) ran on thin prose
explicitly; dp1–3 and W1 used constructed de-primed harnesses. **The heavy-band formal
contract — derived banding, promise↔clause traceability, declared/attacked severity —
was never instantiated in any datapoint.** The marginal artifact under adjudication has
**zero** data touching it.

Consequence: you **cannot** conclude the formal layer lacks value (no test of it), and
you **cannot** conclude it has value (no test of it). The D5 gate, read literally
("does the formal proof catch what thin-prose + existing gates miss"), is unsatisfiable
from this corpus — the treatment arm was never run. This cuts against **both** a naive
"commit (pass)" and a naive "retire (fail)."

## Attack on the RETIRE lean (the side this packet leans toward → steelmanned hardest)

The retire case leans on **"the cheap layer already covers the catch surface."** Attacks:

- **Over-read.** The catch surface was probed on **one defect class** (slice-#25
  grounded-quote/false-label) with **one layer** (the front-challenge). The formal
  layer's plausible value-prop — promise↔clause coverage gaps, severity miscalibration,
  floor-erosion — is **exactly the class never tested**. The evidence is silent precisely
  where the heavy layer would earn its cost.
- **Ceiling-not-floor is structural, not empirical.** The front-challenge re-reads
  *source*; a floor-drafting clause (`validator shall report a result` → `log-and-exit-0`)
  has **no source to contradict** — it's grounded, atomic, within-promise. The
  front-challenge cannot see it *by construction*, regardless of how many dp's it aced.
  Zero floor-defects were *observed* in dp1–5, but the mode is slow/silent/sample-starved
  (S6) — at n≈8 / one operator it would read absent even if present. **"Unobserved ≠ absent."**
- **W1 parity is a ceiling artifact, not a null result.** Codex matched same-family at
  5/5 because the baseline already had **0 misses** — there was no headroom to detect any
  improvement. "Parity" licenses nothing about the formal layer.

**Steelman of COMMIT (the side leaned against), strongest form:** *The front-challenge is
a scope-ceiling, not a severity-floor; dp1–5 only ever exercised the ceiling. The one
defect class the floor layer targets was never planted. "Unobserved" is the predicted
signature of a silent failure, so its absence is not evidence. And the sibling
`measure-before-enforce` ADR already built the instruments (decoy pilot, cross-family
log) to convert that null into signal — committing the floor defense is the structurally
honest move, retiring it before those instruments report is premature.* The steelman's
own concession: it rests entirely on **structural argument, not field data**, and on the
tested class the baseline saturates.

## Attack on the COMMIT lean

- **Zero direct evidence** the formal layer catches anything — every catch is attributable
  to the front-challenge, which ships today without the bundle.
- **Confirmed cost, unmeasured benefit** — spends m2-confirmed EARS authoring cost + the
  unsolved O(pids×clauses) traceability + distribution-staleness against a benefit no
  datum demonstrates. This is the exact inversion the cost-model ADR rejected for shipping
  ("enforcement machinery against unmeasured value").
- **dp3's front-loaded finding is about gate *placement*, not contract *formality*.**
  Reusing "the front gate is load-bearing" to argue *for* a formal layer conflates two
  things: a front-challenge over *prose* catches the same defects with or without a formal
  contract. dp3 licenses "front gate carries the load," nothing about banding/traceability/severity.

## Confound ranking (most → least discounting) — from the evidence interrogator

1. **Formal-layer-never-in-loop** (all live runs) — total discount on any value claim; the machinery wasn't present.
2. **Constructed/de-primed harness ≠ shipped primed agent** (dp2/dp3/W1) — production generalization unestablished.
3. **W1 cases reconstructed in the Codex session** — cross-family independence partly compromised; "parity" is on recycled corpus.
4. **n=3 existence-not-rate + one defect class + same-family grader** (dp3).
5. **Self-referential vehicle + motivation-to-look-good** (dp1) — most confounded; near-uninformative for value.

## Cleanest (least-confounded) finding

**dp2.** A de-primed front-challenge blocked the slice-#25 class, generalized within it,
and discriminated (didn't fire on controls). Even discounted for the constructed harness,
it licenses one claim: *a front intent-challenge over a thin prose intent has real,
discriminating catch on the grounded-quote class.* Note this result requires **no formal
contract** — the cleanest datum is itself evidence **for the thin path**, not the heavy one.

## Claims that survive the attack intact

1. The **front intent-challenge** (existing gate) over **thin prose** has demonstrated,
   discriminating catch on the slice-#25 class (dp2 clean; dp3/W1 corroborate at ceiling).
2. Fidelity in the loop is **front-loaded** — close-review is near-redundant to the front
   gate (dp3, within n=3 / one-class bounds).

Neither touches the formal layer. **Verdict the evidence licenses:** retire-or-defer the
heavy band as *unproven-at-confirmed-cost* — **not** "valueless." If anyone wants "commit,"
the honest gating step is a run that actually puts the formal contract in the loop against
a structural/floor defect class — not another adjudication over this corpus. This is the
seam **Approach C** (retire the build, keep the watch) is built on.
