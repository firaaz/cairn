# D-retire — Phase 0.5: journey trace (how this decision got here)

## The driver: the operator stopped using the four-phase pipeline

`intent-management-loop` Context (`:28`): the operator stopped using `cairn-tdd-feature`
for daily work — per-feature ceremony cost more than it returned (`spec-v2.md` §2). The
accepted `cairn-thin-substrate-direction` set the direction ("the layer that keeps
AI-authored intent bound to verifiable evidence"); 5.5/6 primitives shipped. What remained
was the migration: **Trial E — drop phase-1 derivation, manage intents directly.**

## The binding chain (what constrains this call)

```
identity-and-scope-deferral (2026-05-20, now SUPERSEDED)
   D1: ad-hoc / /decision / cairn-tdd-feature are CO-EQUAL; "no path is the methodology"
   D3.4: an explicit /decision invoking this ADR for supersession is a revisit trigger ◄── THIS arc
        │  (must engage its Alternatives A2/A3 before re-litigating identity)
        ▼
cairn-thin-substrate-direction (accepted — the direction)
   D8: EXPLICITLY RETAINS INV-003 + the firm phase ADRs ◄── retirement must reverse this
        ▼
intent-management-loop (2026-05-31, accepted, PROVISIONAL)
   A1 selected over A2 (augment four-phase in place — retained as the FALLBACK if Trial E fails)
   and rejected A3 (retire four-phase immediately — "violates firm INV-003 + D8")
   D1: build cairn-intent COEXISTING; retire NOTHING here
   D7: retirement = a SEPARATE FIRM supersession, gated on Trial-E pass ◄── THIS arc executes D7
        ▼
Trial-E closure spec (2026-06-02) → W3 → D-retire  ◄── you are here
```

Two facts from the chain shape the call: (a) **A3 — "retire immediately" — was already
rejected once** on firm-INV-003 grounds; this arc is the *gated* path A3 was rejected in
favor of, now that the gate is reached. (b) **A2 — "augment four-phase in place" — was
retained as the explicit fallback if Trial E fails.** Trial E did **not** fail, so A2-as-
fallback is not auto-triggered — but "keep four-phase as a fallback" lives on as a distinct
option from the retirement question (see approaches B/C).

## The thesis that was falsified (Probe C, 2026-05-20)

The original Trial-3 thesis — **"contract grammar alone defeats wrong-model propagation"**
— was **falsified** by the slice-#25 counterfactual (`2026-05-20-…:109-141`). A faithfully-
authored EARS contract built from a *false* premise (slice-#25's docstring claimed
`_REPO_ROOT` fed DB/corpus paths; it only fed `sys.path`) sails through **every** mechanical
layer. Verdict: "Arguably worse than today's pipeline: Phase 2 Skeptic at least exists as a
role where the check could be added; cairn-simplified deletes the role and adds no
replacement." This is **why Trial 3 was gated** and why the smallest-fix `premise_guard.py`
was built. It is the reason retirement cannot be framed on the mechanical layers (constraint
C2).

## What the live + sandboxed dogfoods then showed (dp1–5, W1)

**Front-challenge is real and source-reading, not theater:**
- **dp1** (gh#28, live): front-challenge caught a **semantic over-read** the mechanical
  `premise_guard` (exit 0) structurally could not — "exactly the decorrelation value
  proposition." But self-referential (loop improving its own template) → confound.
- **dp2** (slice-#25 crash test, sandboxed, de-primed): the de-primed front-challenge
  **blocks the canonical case AND a novel un-shown counterfactual** by genuine source-
  reading, and **discriminates** (both truthful controls pass). Crucial reframe: the gate is
  **not** `premise_guard` (the lie lives in the label, which the hook never reads) — it is
  the **front intent-challenge agent reading source**. And the shipped agent is **primed**
  (slice-#25 hard-coded) → its blocks are recall-confounded → the literal D7 wording is
  near-unfalsifiable against the production agent. dp2 rec: de-prime the shipped prompt.

**The asymmetry finding (dp3, 2026-06-02 — load-bearing for THIS arc):**
- Two-checkpoint co-miss probe, n=3 planted slice-#25-class defects + 2 controls,
  de-primed both arms. Result: **co-miss 0/3** — every defect caught by ≥1 checkpoint.
- **But not symmetric.** Arm A (front) **5/5**. Arm B (close-review) **4/5 — missed D2**,
  the *no-friendly-tell* case: the diff *faithfully implements its (false) contract*, so the
  close-review (charter = diff-vs-contract) has no purchase. D1/D3 were caught by *both* arms
  only because they left a **contradicted in-file tell** (a now-false comment; a violated
  fail-closed docstring). **Strip the tell → close-review misses.**
- Implication: fidelity protection is **front-loaded, not two independent shots**. The
  close-review is a **conditional backstop** (reliable only when the defect propagates into a
  visible regression). dp3's own recs: (1) don't claim two-independent-checkpoint coverage;
  (2) the close-review may warrant a **fidelity-aware obligation** to re-verify premises when
  the diff is faithful-but-suspect; (3) co-miss is **under-powered at n=3**.

**Felt cost (the daily-usability driver), live:**
- **dp4** (gh#2 fail-closed, real repo-write): front-challenge "forced the compatibility-risk
  question before construction"; net "higher ceremony than a straight hook bugfix, but it
  produced a real pre-construction decision." The dp3 D2 gap **did not surface** (front
  rechecked premises; impl was a direct change to the same grounded branches).
- **dp5** (sink fix, real repo-write): close-review **blocked** on a missing observation
  record — a close-*process* catch, not a premise-fidelity catch. Useful friction.

**Cross-family (W1, 2026-06-04):**
- A fresh **Codex** front-challenger scored **5/5** on the dp3 corpus. But this is **parity**
  with the same-family 0/3 baseline (which already had no misses), **not** a measured
  improvement — and the cases were **Codex-reconstructed from the dp3 corpus**, not Claude-
  authored (provenance caveat). For D-retire: a cross-family arm does **not** move the
  front-loaded conclusion; it confirms the front-challenge holds across families on this
  corpus.

## Where that leaves the call

The pass criteria are **met** (C4), so the door is open. The central, recurring input is
the **dp3 asymmetry**: the loop's fidelity defense rests substantially on a **single**
checkpoint (front), whose **production** behavior is **unmeasured** (only the de-primed floor
is), at **n=3**. Retirement framing must therefore stand on the front-challenge's
demonstrated *strength* — and the open question the data hands the operator is whether to
**harden that single checkpoint first** (dp2 rec #3 de-prime; dp3 rec #2 fidelity-aware
close-review) before resting the methodology on it, or to retire on the strength already
shown. That is the fork the three approaches lay out.
