---
id: trial-e-closure-adjudication
name: "Trial-E closure — adjudicate the three deferred points (cross-family defer, heavy-band retire-build, four-phase retire-with-conditions)"
status: accepted
firmness: provisional
supersedes: null
superseded-by: null
topic: architecture
invariants-touched: []
date: 2026-06-04
---

# Trial-E closure — adjudicating the three deferred decision points

## Status

Accepted, provisional. Records the operator's adjudication (2026-06-04) of the three
decisions Trial E was gating, after the W1 cross-family probe supplied the last missing
datum. **Supersedes nothing** — the parent ADRs remain valid; their Trial-E-gated points
are now resolved by this record. Resolves: `intent-fidelity-measure-before-enforce` (alt B),
`intent-contract-cost-model` (D3/D5), `intent-management-loop` (D7/R2).

## Date

2026-06-04

## Context

Trial E measured whether the formal intent contract + the four-phase pipeline buy
fidelity/value the thin intent loop would not. Closure spec:
`docs/plans/2026-06-02-cairn-trial-e-closure.md`. Decision-prep + adversarial passes (two
independent attackers per arc, attack-before-synthesis): `.claude/skill-runs/trial-e-w3/{d-xfam,d-cost,d-retire}/`.
Empirical record: dp1–5 (`docs/operator-field-notes-2026-06-01.md`, `-2026-06-02.md`) + W1
(`-2026-06-04.md`).

**The load-bearing fact that reshaped all three calls:** every Trial-E datapoint (dp1–5 + W1)
exercised the **front intent-challenge over thin/prose intents**. The **heavy-band formal
contract** (derived banding + promise↔clause traceability + declared/attacked severity) was
**never instantiated in any datapoint**. And the *shipped* `intent-challenge` is primed
(slice-#25 hard-coded at `.claude/agents/intent-challenge.md:19`), so its **production**
behaviour is unmeasured — every "front is strong" datum used a de-primed agent. Consequence:
the measured value sits in one already-shipped gate, at n=3, on one defect class; everything
else under adjudication was never tested.

## Decision

### D-xfam — `measure-before-enforce` alt B: **deferred, not refuted**

Cross-family fidelity enforcement is **not committed**. W1's cross-family front-challenger
scored 0/3 co-miss against the *measured* same-family baseline of 0/3 (dp3 Arm A) — **no
delta**. Per the parent ADR's own S3/D5 discipline (measure the class; do not import the Kim
~60% prior), the `:90` trigger is **not met**.

- Recorded as **"trigger not met on available evidence; B deferred, not refuted"** — never as
  "B refuted" or "cross-family parity proven" (both baselines are n=3; existence, not rate).
- The W1 Codex-reconstructed-provenance caveat is accepted for a *defer* close (it is
  conservative for a defer: inflated Codex still showed zero delta). A Claude-authored-provenance
  rerun is enabling work for a future *commit*, not a prerequisite for this close.
- The `:90` realization trigger stays **armed**; cross-family co-miss instrumentation stays live
  for production dogfood.

### D-cost — `intent-contract-cost-model` D3: **Approach C — retire the build, keep the watch**

- **Decline to commit** the heavy-band bundle: no value signal at the m2-confirmed authoring
  cost (the formal layer was never in the loop in any datum → "cost confirmed ≠ value confirmed").
- **Do not declare the ambition dead.** D5 read literally ("does the formal proof catch what
  thin-prose + existing gates miss") is **unsatisfiable from this corpus** — the treatment arm
  was never run. This is *unmeasured*, not *measured-and-failed*.
- **Re-bind** the residual ceiling-not-floor risk (a floor-drafting lie — e.g. `validator shall
  report a result` → `log-and-exit-0` — is grounded/atomic/within-promise, so the source-reading
  front-challenge cannot see it by construction) to `measure-before-enforce`'s already-committed
  instruments, with a **pre-registered revival trigger**: a real floor-defect-escape OR a
  genuinely heavy multi-clause intent that under-covers → reopen D3 with the formal layer
  actually instantiated in the loop.

### D-retire — `intent-management-loop` D7/R2: **Approach C — retire-with-conditions (sequenced)**

The four-phase pipeline is **not retired now.** Trial-E criteria being met *opens* the
retirement `/decision`; it does not settle it. Clean-retire-now is **rejected** (firm one-way
door while the load-bearing checkpoint's production behaviour is unmeasured at n=3); keep-as-is
is **rejected** as partly illusory (four-phase's Phase-2 Skeptic shares the front-challenge's
premise-fidelity exposure; its Phase-4 Auditor shares the close-review's diff-vs-contract blind
spot — so it does not demonstrably cover the dp3 D2 non-propagating gap either). Both poles fail
for one root reason: **the single, unmeasured, production fidelity checkpoint.**

Conditions before any firm supersession, in order:

1. **Keystone — de-prime + re-probe the shipped `intent-challenge`** against the production agent
   (closes the "unmeasured production gate" attack; this is dp2 rec#3). This de-risks all three
   arcs.
2. **Add a fidelity-aware close-review obligation** to `.claude/agents/intent-review.md` /
   `intent-review` ("re-verify the contract's premises against source when the diff is
   faithful-but-suspect") — closes the dp3 D2 structural gap (dp3 rec#2).
3. **Retain four-phase through a sunset window** (honours the option-value concern recorded in
   `cairn-thin-substrate-direction`, which superseded `identity-and-scope-deferral`'s D3.4
   option-value clause; this `/decision` is that ADR's supersession-trigger #4 invocation).

The eventual firm supersession ADR — when the conditions are met — must be framed strictly on
the front-challenge's **demonstrated** strength, **never** on bracket redundancy or "co-miss is
rare" (n=3). Honest fallback if dual-maintenance cost is judged too high to run the conditions
first: **keep-with-a-committed-sunset-date**, not clean-retire-now.

## Consequences

**Easier:**
- Trial E closes; three long-deferred points have a recorded outcome instead of an open gate.
- The follow-on work is now concrete and small: one keystone probe + one close-review obligation
  + two pre-registered triggers — not an open-ended "keep measuring."
- No firm, hard-to-reverse machinery ships against unmeasured value (no heavy-band build, no
  cross-family enforcement, no four-phase deletion).

**Harder:**
- The ceiling-not-floor risk (a wrong-but-grounded intent ships green as log-and-exit-0) is
  **named but unobserved**, and its detection is slow/silent/sample-starved — we may learn we
  were wrong late. Mitigated only by the pre-registered revival trigger + the keystone re-probe,
  not closed.
- Trial-E evidence is n=3, one defect class, de-primed harness. Every "front is strong" claim
  carries that bound; the production re-probe (condition 1) is what converts it.
- Dual-tooling (`cairn-intent` + `cairn-tdd-feature`) persists through the sunset window — the
  zombie-default cost is paid until the firm supersession lands.

## Alternatives Considered

- **D-xfam — commit cross-family enforcement (literal trigger):** rejected. Reads "~60%" as the
  trusted Kim prior the parent ADR's S3/D5 explicitly refuse to import; n=3 cannot justify a
  commit and would put a runtime Codex dependency on the construction critical path.
- **D-cost — commit the heavy-band bundle:** rejected — confirmed cost vs zero measured benefit,
  the exact inversion the cost-model ADR was written to avoid. **Retire-the-ambition (declare
  dead):** rejected — over-claims a "fail" the corpus cannot support (treatment arm never run).
- **D-retire — clean retire now (A):** rejected — firm one-way door (touches
  `phase-lock-and-role-declaration`/`phase-pipeline-evaluation` firmness + INV-003) while the
  load-bearing gate is only floor-measured. **Keep-as-fallback indefinitely (B):** rejected —
  buys ceremony, not demonstrably more fidelity coverage; leaves the gap open *and* unmeasured
  behind dual-tooling.
