# D-xfam — Phase 2: candidate resolutions

Three coherent resolutions of "commit cross-family enforcement (B), or record not-triggered?"
Each is stated so the operator can pick; the recommendation + main tradeoff are at the end.

---

## Approach 1 — Record "not triggered; B **deferred, not refuted**" on W1 as-is

Accept the Codex-reconstructed provenance for a *defer* close. Record:
- trigger **not met** — cross-family front arm 0/3 = measured same-family front arm 0/3
  (dp3); no material delta below the operative (measured) baseline;
- B **remains deferred** under D4 — **not falsified** (n=3 cannot refute it);
- D2's cross-family co-miss instrumentation **stays live** for production dogfood (the
  conjunct-2/3 vehicle dp3 names), so the trigger can re-fire on real-usage data.

**Pros**
- Honors measure-before-enforce: data shows no delta → ship no new enforcement.
- Cheapest close; no rerun, no new committed surface, no critical-path Codex dependency.
- Provenance caveat is **conservative for a defer**: Codex-authored cases can only
  *inflate* Codex's catch rate, and an inflated Codex still showed zero improvement — so
  the caveat cannot manufacture a false "not triggered" (see attack §C1).
- Keeps the door open exactly as the ADR intended (defer-until-measured, now
  defer-until-measured-in-production).

**Cons**
- Leaves the trigger formally unmeasured at *production* provenance (Claude-authored,
  primed agents).
- Rests on accepting an n=3 baseline as "enough not to act" — defensible for a defer, but
  someone could later argue the trigger should have been read literally (0% vs the 60%
  prior → met). The close must explicitly state which reading it adopts and why (constraint
  §2).

---

## Approach 2 — Require a Claude-authored-provenance rerun before closing

Hold D-xfam open until the five cases are rerun from a **Claude-authored case pack**
(Claude drafts intents → Codex challenges), restoring true author/challenger family
separation, then adjudicate.

**Pros**
- Closes the provenance gap; the only path to a *positive* cross-family claim ("cross-family
  is at least as good as same-family on production-shaped, family-separated cases").
- Methodologically cleanest read of the trigger.

**Cons**
- **The rerun cannot change the "not triggered" conclusion at n=3.** Even a clean rerun
  lands at "0/3, no delta, underpowered" — you spend a full harness run and still cannot
  adjudicate the trigger as *met* or *falsified*. This is measurement-for-its-own-sake
  unless the operator wants a *positive* claim (operator memory: "measure over more
  decisions" cuts the other way here — the gating datum was already run).
- Cost + a second blind-grader cycle for a decision whose current conclusion is robust to
  the caveat's direction.
- Only worth it as **enabling work for a future commit**, not for a defer close.

---

## Approach 3 — Commit B (cross-family enforcement) now

Read the trigger literally — cross-family 0% is materially below the recorded ~60%
same-family prior — treat W1 as sufficient, and ship cross-family (Claude drafts / Codex
challenges) as the committed front challenger (skill-step, D6-compliant).

**Pros (steelman — see attack §S for the full version)**
- Cross-family is the **one decorrelation mechanism the trilemma leaves standing** (S1/S5/S10
  kill operator-as-source; S3 kills same-family). Its only objection was "unmeasured" — and
  W1 measured it at 5/5, zero misses, zero false positives, with the Codex path *already
  rendering* through the canonical workflow.
- If you trust the Kim ~60% prior over an n=3 sample, same-family *will* co-miss eventually;
  waiting for that is waiting for a silent, slow, six-month-cliff failure (the S6 trap).
  Committing now is defense-in-depth before a rare-but-catastrophic co-miss.
- Honors the pre-recorded trigger literally rather than re-reading "~60%" after the fact.

**Cons**
- **Enforcement without validation — the exact S4/S6 trap measure-before-enforce rejects.**
  D4 says defer until data justifies; the data (no delta) justifies *continued deferral*, not
  commitment.
- Reads the imported Kim prior as the baseline when the ADR's own S3/D5 say cairn **measures**
  its class rather than trusting the prior (constraint §2). Under the ADR's own discipline the
  trigger is not met.
- n=3 cannot justify a *commit*; and a commit makes the provenance caveat load-bearing
  (possibly-inflated Codex catch) and unresolved.
- Adds a runtime Codex dependency to the critical construction path.

---

## Recommendation

**Approach 1**, with the conclusion reshaped to **"trigger not met; B deferred, not
refuted; cross-family co-miss instrumentation stays live for production dogfood."** The
attack on commit-B is strong enough to *reshape* the record (defer ≠ refute; the baseline is
underpowered both ways) but not to flip the call to commit.

Escalate to **Approach 2 only if** the operator wants a *positive* cross-family claim or to
begin moving toward a future commit — in which case the Claude-authored rerun is the gating
measurement for *that* claim. It is not a prerequisite for a defer close.

## Single main tradeoff

**Epistemic honesty vs. closure.** Accepting W1 as-is (Approach 1) closes D-xfam cheaply and
correctly *for a defer*, but bakes in an n=3, Codex-reconstructed datum the close must
explicitly mark as "not refuted, not powered." Demanding production provenance (Approach 2)
removes that caveat but cannot change the verdict — so the cost buys cleanliness, not a
different decision.
