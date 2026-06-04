# D-retire — attack before synthesis

Per operator memory ("Attack before synthesis", "Steelman before recommending deferral"):
mount adversarial attacks on every load-bearing claim, and steelman **"do NOT retire / keep
the four-phase pipeline"** as hard as possible before any retirement recommendation. A weak
steelman validates retirement; a strong one should **reshape** it.

---

## Steelman of KEEP (the position the data is being marshalled against)

**S-1 — Retirement rests the whole methodology on a single checkpoint whose production
behavior is unmeasured.** dp3 is explicit: for non-propagating fidelity defects the bracket
is "effectively single-checkpoint" (front only). And *every* measurement that shows the front
is strong — dp2, dp3 Arm A, W1 — used a **de-primed `general-purpose` agent**, never the
shipped `intent-challenge`, which is **primed** (slice-#25 hard-coded at
`.claude/agents/intent-challenge.md:19`). dp2 states the consequence flatly: the production
gate's blocks are "recall-confounded… near-unfalsifiable." So retirement would remove the
redundant pipeline to lean on a single production checkpoint **we have never measured in
production**. The four-phase pipeline is the thing currently covering that unmeasured risk.

**S-2 — n=3, one defect class. Retiring a safety mechanism needs more than an existence
result.** Closure-spec §7 and dp3 both warn: 0/3 co-miss "rules out 'co-miss is the common
case' only weakly; it does not establish 'co-miss is rare.'" One defect class (slice-#25
grounded-quote/false-label) is tested; others are not. Retirement is a firm, Phase-5,
machine-bound-invariant one-way door. Asymmetric stakes: keeping costs maintenance; retiring
wrongly costs a firm reversal. Under that asymmetry, n=3 on one class does not clear the bar.

**S-3 — option value / pivot precedent.** `identity-and-scope-deferral` records that cairn
**already pivoted once** (substrate retirement at M4) and that "likelihood of another pivot
in 6–12 months is non-trivial; every identity-level ADR landed now creates friction for that
pivot." Retiring `cairn-tdd-feature` *firmly* (superseding INV-003 + three firm ADRs +
reversing `cairn-thin-substrate-direction` D8's retention) is the maximal-friction move
against a future pivot. Coexistence costs almost nothing; the firm supersession spends option
value the operator deliberately preserved.

**S-4 — D1 co-equality and genuine use-case difference.** `identity-and-scope-deferral` D1:
the three paths are co-equal, "no path is 'the methodology.'" The two skills serve **different
shapes** — `cairn-intent` for fluid single-conversation work, `cairn-tdd-feature` for strict
per-phase isolation against a `docs/plans/<feature>.md` plan doc (large/multi-session). The
felt-cost dogfoods (dp1, dp4, dp5) were all **small** changes — template tweak, hook bugfix,
sink fix — exactly where the loop *should* win. None exercised the large-plan-doc case the
four-phase exists for. So the felt-cost evidence is drawn from the wrong end of the size span
to justify retiring the path that serves the *other* end.

**S-5 — `intent-management-loop` itself retained A2 as the fallback "if Trial E fails."** The
ADR is provisional; the retirement ADR was always meant to be the *firm* one. The operator
has consistently chosen to keep the off-ramp. KEEP is the path of least regret.

---

## Attacks on the load-bearing claims

### Attack on the RETIRE case

**A-1 — "Trial-E criteria met ⇒ retire" is a category error.** The criteria (C4) are the
**gate to open** the `/decision`, not the decision. C4 forbids the conflation explicitly. Any
retirement framing that leans on "the criteria are met" is attackable on its face.

**A-2 — the strongest felt-cost data point is confounded.** dp1 (the clearest "front-challenge
caught a real semantic error the mechanical gate couldn't") was **self-referential** — the loop
improving its own intent template — a confound the field note flags itself. dp4/dp5 are honest
but report "higher ceremony than a straight bugfix"; the win is *decision-forcing*, not speed.
And per `measure-before-enforce` D5 / closure-spec §7, **fast approval must be rejected as a
success metric** (indistinguishable from disengagement). So the felt-cost case for retirement
is thinner than it first reads.

**A-3 — W1 adds nothing to the retirement case.** It is **parity, not improvement** (0/3 vs the
same 0/3 baseline) and carries a provenance caveat (Codex-reconstructed cases). It confirms the
front-challenge holds cross-family; it does **not** strengthen "retire."

### Attacks on the KEEP steelman (does it survive?)

**A-4 — S-1/S-4's premise is partly illusory: four-phase does NOT demonstrably cover the gap
it's invoked to cover.** This is the decisive counter. The dp3 D2 case (non-propagating,
no-tell) was missed by the **close-review** because its charter is diff-vs-contract and the
diff *faithfully implements the false contract*. The four-phase pipeline's **Phase-4 Auditor**
shares that charter (audits diff vs tests/contract) → same blind spot. And the four-phase
**Phase-2 Skeptic** reads `intent.md` to write RED tests → it has the **same premise-fidelity
exposure** as the front-challenge (a false premise in the intent flows into the Skeptic's tests
too). **No one has measured four-phase against the dp3 corpus.** So "keep four-phase for the
redundancy" assumes a redundancy that is **unproven** — and structurally, four-phase's two
extra source-reading passes (Skeptic, Auditor) look like they'd miss D2 for the *same* reasons
the loop's close-review did. KEEP buys ceremony, not demonstrably more fidelity coverage.

**A-5 — S-2's asymmetry cuts toward conditions, not toward keep.** Yes, n=3 is thin and the
production gate is unmeasured (S-1) — but the remedy for "the load-bearing checkpoint is only
floor-measured" is to **measure/harden that checkpoint** (de-prime the production prompt; re-run
the probe against the de-primed *production* agent; add the fidelity-aware close-review
obligation), **not** to indefinitely retain a parallel pipeline that A-4 shows doesn't cover the
gap either. KEEP leaves the gap open *and* unmeasured; it just hides it behind dual-tooling.

**A-6 — S-3/S-5's option value is real but cheap to honor without blocking retirement.** A
coexistence **sunset window** (already in D7) preserves the off-ramp through the measurement-thin
period without paying the zombie-default cost (R6) forever. Option value argues for *sequencing
and a sunset*, not for *never retiring*.

---

## Where the attack lands (reshaped recommendation)

The KEEP steelman is **strong on S-1/S-2/S-3** (single unmeasured production checkpoint; n=3
one-class; option value) and these genuinely **defeat Approach A (retire now)** — retiring
firmly while the load-bearing gate is only floor-measured, on a one-way door, is not supported.

But the steelman is **defeated on its own headline (S-4/A-4):** keeping four-phase does **not**
demonstrably close the dp3 non-propagating gap — four-phase's Skeptic and Auditor share the
exposures that produced the D2 miss, and no measurement shows otherwise. So "keep for the safety
net" is partly illusory, and **Approach B does not actually buy the protection it's invoked to
buy.**

Both poles fail for the same root reason: **the real problem is the single, unmeasured,
production fidelity checkpoint — and neither retire-now nor keep-as-fallback fixes it.** That is
exactly what reshapes the recommendation toward **Approach C (retire-with-conditions)**: de-prime
the production challenger and re-probe it (closes S-1's "unmeasured" attack), add the
fidelity-aware close-review obligation (closes A-4's structural gap), retain four-phase only
through a sunset window (honors S-3/S-5 option value cheaply), and frame the eventual firm
supersession strictly on the front-challenge's *demonstrated* strength — never on bracket
redundancy or "co-miss is rare" (n=3).

**Residual risk the operator should weigh:** C's conditions are themselves decision-weight and
add `/decision` surface; if the operator judges the front-challenge's de-primed strength
sufficient and the dual-maintenance cost high, the honest fallback is **B with a committed
sunset date**, not A. A (clean retire now) is the one option the attack does **not** support.
