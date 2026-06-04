# D-retire — Phase 2: candidate resolutions

All three respect the constraints: framed on the **front-challenge's strength** (not bracket
redundancy / not the falsified grammar thesis), no new hooks, distinct from D-cost/D-xfam.
Each notes its `identity-and-scope-deferral` D3.4 posture.

---

## Approach A — Retire now (clean firm supersession)

Write the firm ADR: retire `cairn-tdd-feature`, supersede `INV-003` + the three firm phase
ADRs + reverse `cairn-thin-substrate-direction` D8's retention, define a coexistence sunset
window, carry Phase-5 verification. Justify on: Trial-E criteria met (C4); front-challenge
strength (dp2/dp3/W1); felt-cost wins (dp1/dp4/dp5). `cairn-intent` becomes the methodology;
four-phase exits at sunset.

- **For:** Realizes the actual driver (daily-usability; "move *to* intent management"). Ends
  R6 zombie-default and the standing dual-maintenance of INV-003 + three firm ADRs. Cleanest
  end-state. The front-challenge's source-reading capability is the best-measured thing in the
  whole trial (dp2 de-primed + novel, dp3 3/3, W1 cross-family parity).
- **Against:** Rests the fidelity defense on a **single** checkpoint whose **production**
  behavior is **unmeasured** (shipped agent is primed → recall-confounded; C5) at **n=3**.
  Ignores dp3 rec #2 (close-review structurally can't catch the non-propagating D2 class) and
  dp2 rec #3 (de-prime the production gate). A **firm one-way door** on a machine-bound
  invariant taken while the load-bearing checkpoint is only floor-measured. Removes the A2
  off-ramp. **D3.4 risk:** looks closest to the *rejected* A3 ("retire immediately") unless
  the trial-gating is foregrounded.
- **Honest weakness:** "criteria met ⇒ retire" treats the gate-to-open as the call (C4 forbids).

---

## Approach B — Keep four-phase as `cairn-tdd-feature` fallback only (no firm retirement)

Do **not** write the supersession. Document `cairn-intent` as the **default** and
`cairn-tdd-feature` as the **strict-isolation fallback** for plan-doc / multi-session
features. INV-003 + the firm phase ADRs stand. This is `intent-management-loop` A2-as-
fallback made explicit (status-quo-plus-docs).

- **For:** **Zero one-way-door cost.** Preserves option value — `identity-and-scope-deferral`
  notes cairn already pivoted once (substrate retirement at M4); a firm retirement now creates
  friction for the next pivot. Honors D1 co-equality. The **under-powered co-miss (n=3)**
  doesn't force a firm call the data can't yet support (closure-spec §7). Matches the operator's
  revealed-preference pattern that the identity steelman read as **right-sizing, not rot**.
  The two skills genuinely serve different shapes (fluid single-conversation vs. strict
  per-phase isolation against `docs/plans/<feature>.md`).
- **Against:** **R6 zombie-default** — four-phase lingers; the "move *to* intent management"
  goal is never realized; standing dual-maintenance persists. And the headline "keep it for the
  safety net" rationale is **partly illusory** (see attack.md): four-phase's Phase-2 Skeptic
  reads `intent.md` and has the **same** premise-fidelity exposure as the front-challenge, and
  its Phase-4 Auditor shares the close-review's diff-vs-contract charter — so keeping it does
  **not** demonstrably cover the dp3 D2 (non-propagating) gap.
- **D3.4 posture:** safest — changes no identity claim, retires nothing.

---

## Approach C — Retire-with-conditions (recommended)

Commit to retirement **as the firm supersession**, but **gate the firm ADR on first closing
the dp3 single-checkpoint gap**, and retain four-phase through the sunset window rather than
hard-deleting. Concretely, sequence two enabling sub-decisions before/with the supersession:

1. **De-prime the shipped `intent-challenge` prompt** (dp2 rec #3) — drop the hard-coded
   slice-#25 example, keep the generic charter — so the **production** gate rests on
   demonstrated capability, not a memorized fixture. (Decision-weight: changes loop behavior.)
2. **Add a fidelity-aware close-review obligation** (dp3 rec #2) — `intent-review.md` gets an
   explicit "re-verify the contract's premises against source when the diff is faithful-but-
   suspect" charter, so the loop is **not structurally single-checkpoint** on the
   non-propagating fidelity class (D2). (Decision-weight: changes a checkpoint charter.)
3. **Retain `cairn-tdd-feature` as a documented fallback through the coexistence sunset
   window** (already in D7), so the off-ramp survives the measurement-thin period.

Frame the supersession strictly on the front-challenge's demonstrated strength (C2), and
**explicitly do not** rest it on "co-miss is rare" (n=3, C5).

- **For:** Addresses the **actual gap** — non-propagating fidelity + an unmeasured production
  gate — that **neither A nor B closes** (A ignores it; B's redundancy is illusory). Honors
  the dp3 front-loaded constraint and the closure-spec anti-over-read. Satisfies the trials-plan
  §5 "do not delete Phase-2 Skeptic without an equivalent mechanism" *and* makes the equivalent
  mechanism (the front-challenge + a hardened close-review) actually robust. Preserves the
  off-ramp cheaply during sunset. **D3.4-clean:** demonstrably the trial-gated execution of an
  already-decided direction with the named gap closed first — not a re-opening of A2/A3.
- **Against:** **Most work** — two charter/skill changes plus the firm ADR. The two conditions
  are themselves decision-weight (dp2/dp3 flag them for `/decision`), so C is really "retire,
  but run two enabling sub-arcs first" — it does **not** end dual-tooling immediately, and it
  adds `/decision` surface (weigh against operator memory "Measure over more decisions": these
  are concrete charter changes the data already motivates, not deferrals-to-an-unmeasured-datum).
- **Sequencing note:** the conditions are **enabling work**, not scope creep (operator memory
  "Plan-level contracts split artifact-scope from execution-scope"). Condition 2 in particular
  could be its own short `/decision` sub-arc; condition 1 is a prompt edit + a re-run of the
  dp2/dp3 probes against the *de-primed production* agent to confirm the floor holds in prod.

---

## Decision-shape summary

| | A — retire now | B — keep as fallback | C — retire-with-conditions |
|---|---|---|---|
| Firm supersession of INV-003 | yes, now | no | yes, after conditions |
| Closes dp3 non-propagating gap | no | no (illusory) | **yes** |
| Production gate measured before resting on it | no | n/a | **yes (de-prime + re-probe)** |
| One-way-door cost paid while gate unmeasured | **yes** | no | no |
| Ends R6 zombie dual-tooling | yes | no | yes (at sunset) |
| D3.4 / identity risk | highest (≈ rejected A3) | lowest | low (gated execution) |
| Work | low | lowest | highest |
