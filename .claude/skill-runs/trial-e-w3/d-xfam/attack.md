# D-xfam — attack-before-synthesis

Default-to-acceptance is the named failure mode (operator memory). Every load-bearing claim
below is attacked before the recommendation rests on it. Verdicts are stated, not implied.

---

## C1 — "W1's 0/3 cross-family parity is sound." (provenance + n)

**Attack A (provenance).** Cross-family's entire value is *author↔challenger family
separation*: Claude drafts, a *different* family (Codex) challenges, so their blind spots
differ. But the W1 cases were **reconstructed inside the Codex session**, not Claude-authored
(field note `:83`, brief §W1 caveat). That collapses the separation on the *authoring* side —
Codex is partly grading cases Codex shaped. Plausible effect: Codex catches lies it would
itself construct → **inflated** catch rate.

**Verdict A.** The inflation is *directional*, and the direction is **conservative for a
defer close.** An inflated Codex still scored 5/5 — i.e. showed **zero improvement** over the
same-family 5/5. Provenance can only mask a *real* cross-family advantage; it cannot
manufacture a false "no delta." The only way provenance threatens "not triggered" is if
reconstruction made the cases *harder* for Codex (anti-correlated), which is implausible.
→ **Sound enough for "not triggered." Insufficient for any positive claim or a commit.**

**Attack B (n).** "0/3 parity" is an **existence result, not a rate** (field note `:76`).
It establishes "neither family co-missed *these three*," not "cross-family ≈ same-family."
→ **"Parity proven" is over-read; "no measured delta at n=3" is the honest statement.**
The Phase-2 record and any ADR text must use the latter.

---

## C2 — "No material delta below the ~60% baseline" is the right reading. (the crux)

**Attack.** The trigger (`:90`) says "materially below same-family **~60%**." That ~60% is
the **Kim literature prior** (`intent-contract-cost-model/D3:97`), but the *observed*
same-family baseline (dp3 front arm) was **0/3 = 0%**. Two readings collide:
- **(a) literal:** cross-family 0% vs prior 60% → materially below → **TRIGGER MET → commit B.**
- **(b) measured:** cross-family 0/3 vs measured same-family 0/3 → no delta → **NOT MET.**

The field note + brief adopt (b). Is (b) defensible, or is it goalpost-moving after a
literal trigger fired?

**Verdict.** (b) is correct **by the ADR's own discipline**: S3 (`:79`) — "the same-family
challenger stays as-is; D2 *measures* its miss rate **rather than trusting it**"; D5 (`:49`)
— success = generated signals, not imported priors. cairn explicitly refuses to treat the
Kim 60% as its own class's rate; it measured it (0/3). So the operative comparator is the
measured baseline, and there is no delta. Reading (a) would require trusting exactly the
prior the ADR says not to trust. **Not goalpost-moving — it is the metric discipline the ADR
pre-committed to.**

**But the deeper attack:** the measured baseline is *itself n=3*. So **neither reading is
powered.** 0/3 does not establish same-family reliability (it failed to *sample* a co-miss —
field note `:91`, dp3 `:92`); it only rules out "co-miss is the common case." Therefore:
→ **The trigger is not adjudicable as "met" OR "falsified" at n=3.** "Not triggered" is a
defensible *decision* (no evidence of a material delta → don't ship unvalidated enforcement,
per D4) but **must not be recorded as "B refuted" or "cross-family parity."** The honest
close is **"trigger not met on available evidence; B deferred, not refuted; instrumentation
stays live."**

---

## S — Steelman "commit B now," then rebut. (a strong steelman reshapes; a weak one validates)

**Steelman (strongest case for committing).**
1. **Cross-family is the trilemma's sole survivor.** S1/S5/S10 kill operator-as-source; S3
   kills same-family; cross-family's *only* objection was "unmeasured" (S7) — a measurement
   gap, not a structural flaw. Of all decorrelation mechanisms, it is the one the arc said
   could actually work pending data.
2. **W1 closed the only open objection.** 5/5, 0 misses, 0 false positives; and the Codex
   path **already renders through the canonical workflow** (`render_codex_dispatch_brief`,
   field note `:20`). Integration is in-flight (`codex-hook-parity`) anyway → low marginal
   commit cost.
3. **The "no delta" reading leans on an underpowered baseline.** If you weight the Kim ~60%
   prior over an n=3 sample, same-family *will* co-miss; waiting to observe it means waiting
   for a silent, slow, sample-starved cliff failure (S6) — you may never get the signal.
   Commit cross-family now as defense-in-depth before the rare co-miss.
4. **D6 doesn't block it** — cross-family is a skill-step challenger swap, not a hook.
5. **Honor your own pre-recorded trigger** (the literal 0% < 60% reading) rather than
   re-interpreting "~60%" after the result is in.

**Rebuttal.**
- Points 3+5 hinge on reading "~60%" as the trusted prior — exactly what S3/D5 forbid
  (see C2). Under the ADR's own discipline the trigger is not met.
- Point 3 is *enforcement without validation* — the S4/S6 trap measure-before-enforce was
  written to reject. D4: defer until data justifies; the data (no delta) justifies continued
  deferral, not commitment. "Defense-in-depth before a rare co-miss" is precisely the
  unvalidated-commit move the ADR refuses.
- n=3 cannot justify a *commit* (it can't even adjudicate the trigger). A commit also makes
  the provenance caveat load-bearing and unresolved (C1), and puts a runtime Codex dependency
  on the construction critical path.

**How the steelman reshapes the recommendation.** Point 3 is *correct* that 0/3 is
underpowered — and that cuts **both ways**: it cannot justify a commit, but it also forbids
recording B as *falsified*. So the steelman does not validate the bare default ("not
triggered, move on"); it **reshapes** the close into "**deferred, not refuted; cross-family
co-miss instrumentation stays live in production dogfood**" so the trigger can genuinely
re-fire on a powered, production-provenance sample. That is the difference between dismissing
B and keeping the pre-recorded escalation alive — which is what the ADR (`:68`) actually
promised.

---

## C3 — Is the dp3 baseline a fair comparator for W1?

**Attack.** dp3's same-family front arm was *de-primed general-purpose agents*; W1's Codex
was also *de-primed/no-context*. Neither reflects the **shipped, primed** `intent-challenge`
(slice-#25 hard-coded → recall-confounded). And W1's corpus is a *reconstruction* of dp3's,
not the identical artifacts.

**Verdict.** The *delta* read is fair because **both arms are de-primed** — it is an
apples-to-apples capability-floor comparison (field note `:78`, dp3 `:94`). Absolute rates
don't reflect production, but the trigger asks about a *delta*, and the delta comparison is
internally consistent. The reconstruction risk (different difficulty) folds into C1's
provenance caveat and does not separately threaten "not triggered." → **Comparator is fair
for the delta; does not undermine the verdict.**

---

## C4 — Does deferring again violate "measure over more decisions"?

**Attack.** Operator memory warns against stacking `/decision` arcs that defer to the same
unmeasured datum instead of running the measurement.

**Verdict.** Inverted here: the gating datum **was** run (W1). So a *defer* close does not
stack-and-defer — it acts on measurement. The risk runs the *other* way: **Approach 2's
rerun** is the move that would "measure for its own sake," because it cannot change the n=3
verdict. → Recording "not triggered" is consistent with the memory lesson; a rerun is only
warranted for a *positive* claim, not a defer.

---

## Net

- "Not triggered" is sound **as a defer decision**, robust to the provenance caveat's
  direction (C1) and to the comparator critique (C3).
- It is **not** sound as "B refuted" or "parity proven" — n=3 forbids both (C2, C1-B).
- The strong steelman (S) reshapes the close to **deferred-not-refuted + live
  instrumentation**, not bare dismissal.
- A Claude-authored rerun (Approach 2) is enabling work for a *future commit*, not a
  prerequisite for this close (C1, C4).
