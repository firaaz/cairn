# D-retire — Phase 0: constraint envelope (what's fixed / forbidden)

Decision: `intent-management-loop` **D7/R2** — retire the four-phase pipeline
(`cairn-tdd-feature`) now that Trial-E data is in? This packet is **prep only**;
the call and any ADR are operator-bound.

## C1 — This is a FIRM supersession, not a light close (one-way door)

Retirement is not a status flip on a provisional ADR. Per `intent-management-loop`
D7, retirement is a **separate firm ADR** that must:

- **Supersede `INV-003`** — firm and **machine-bound** via `validate_phase_topology`
  (the decisive constraint recorded in the source `/decision`, `intent-management-loop:44`).
- **Supersede three firm phase ADRs:** `phase-lock-and-role-declaration`,
  `phase-pipeline-evaluation`, `feature-slice-model`.
- **Reverse a retention commitment in an *accepted* ADR.** `cairn-thin-substrate-direction`
  **D8 explicitly retains** INV-003 + the firm phase ADRs. The retirement ADR does not
  merely supersede the phase ADRs — it overturns a live retention clause in the accepted
  direction ADR. That clause must be addressed head-on, not silently.
- **Carry Phase-5 independent verification** (it is the firm ADR; `intent-management-loop`
  itself is provisional and skipped Phase 5 — D7's successor does not get to).
- **Define a coexistence sunset window** (D7 wording; mitigates R6 zombie-default).

Forbidden: retiring via a provisional ADR, an `Edit` to `intent-management-loop`, or any
path that skips Phase-5 verification of the firm supersession.

## C2 — The dp3 framing constraint (load-bearing; brief + closure-spec §3.W3.2, §7)

**Do NOT frame retirement on "two independent decorrelation catches."** Two distinct
reasons, both on record:

1. The **original Trial-3 thesis is falsified.** Probe C (`2026-05-20-…:109-141`):
   "contract grammar alone defeats wrong-model propagation" is **not** supported — the
   slice-#25 wrong-premise propagates through *every* mechanical layer (EARS, scope-split,
   `role_guard`, `reversibility-guard`, `premise_guard`) unchallenged. Retirement therefore
   **cannot** rest on the mechanical/grammar layers.
2. **Fidelity is front-loaded, not symmetric** (dp3, `2026-06-02`). The two checkpoints
   guard *different objects* (front = premise-vs-source; close = diff-vs-contract). For a
   fidelity defect that does **not** propagate into a diff-visible regression, the
   close-review has little purchase (it missed **D2**, the no-friendly-tell case). The
   bracket is therefore **effectively single-checkpoint** on the non-propagating fidelity
   class. Any retirement framing must rest on the **front-challenge's demonstrated
   strength**, not bracket redundancy.

Corollary forbidden move: justifying retirement on "co-miss is rare." Co-miss is **0/3
but under-powered at n=3** (dp3, closure-spec §7). 0/3 rules out "co-miss is the common
case" only weakly; it does **not** establish "co-miss is rare."

## C3 — `identity-and-scope-deferral` D3.4 obligation (binds this arc)

This `/decision` **is** D3 revisit **trigger #4** ("the operator's own … `/decision`
invocation explicitly invokes this ADR for supersession", `identity-and-scope-deferral:52`).
The obligation D3 imposes: identity-level proposals **must engage that ADR's Alternatives
Considered section before being re-litigated** — i.e. the retirement decision must show it
is **not** a back-door re-opening of A2 (adaptive tier model) or A3 (infrastructure-identity
rebrand), both of which were rejected on option-value/timing grounds.

Two facts make this engageable rather than blocking:
- That ADR is **already superseded** by `cairn-thin-substrate-direction`; its *direction*
  is spent. The surviving obligation is procedural (engage A2/A3), not a veto.
- Retiring `cairn-tdd-feature` is **narrower** than A2 or A3: it drops **one** of the three
  co-equal execution paths (`identity-and-scope-deferral` D1), it is **trial-gated execution
  of an already-decided direction** (`cairn-thin-substrate-direction` + `intent-management-loop`),
  not a fresh identity pivot. The decision packet must say this explicitly.

But note the live tension D3.4 surfaces: D1 names the three paths (ad-hoc / `/decision` /
`cairn-tdd-feature`) **co-equal, "no path is 'the methodology.'"** Retirement removes one
co-equal path. That is a real identity-touching move and must be argued, not assumed.

## C4 — Trial-E / Trial-3 pass criteria are the *gate to open* this arc — not the call

The criteria (`2026-05-20-…:213`; `intent-management-loop` D7) are **met**, which is what
*authorizes* the retirement `/decision` — it does not pre-decide it:

| Conjunct | Criterion | Status |
|---|---|---|
| 1 | slice-#25 counterfactual **blocks at the front-challenge** | **Met** — dp2 (de-primed + novel), dp3 (Arm A 3/3), W1 (Codex 5/5). *Refinement:* trials-plan said "blocks under `premise_guard`"; dp2 corrected this — `premise_guard` exits 0 (lie lives in the *label*, not the quote); the real gate is the **front intent-challenge agent**. |
| 2 | ≥1 real increment ships clean, operator confirms no semantic-grounding leak | **Met** — dp4 (gh#2 fail-closed, real repo-write) + dp5 (sink); both clean, no leak. |
| 3 | loop felt cost **< four-phase cost** | **Met** — dp1 ("Lighter"), dp4/dp5 (higher than a bare bugfix, but a real pre-construction decision at ~half the four-phase dispatch ceremony). |

Forbidden: treating "criteria met" as equivalent to "retire." The criteria open the door;
the `/decision` still weighs retire vs. keep-as-fallback vs. retire-with-conditions.

## C5 — Anti-over-read constraints carried into the call (closure-spec §7, dp1–5)

- All fidelity measurements (dp2/dp3/W1) are **de-primed `general-purpose` capability-floor**,
  **not** the shipped (primed) `intent-challenge`. The shipped agent hard-codes the slice-#25
  example (`.claude/agents/intent-challenge.md:19`), so its blocks are **recall-confounded**.
  The **production** gate's real behavior is **unmeasured**.
- **One defect class** (slice-#25 grounded-quote/false-label). Other fidelity classes untested.
- **Reject review-time-under-15-min as success** (`measure-before-enforce` D5): fast approval
  is observationally identical to disengagement. Do not read dp4/dp5 speed as value.
- W1 cross-family is **parity, not improvement** (0/3 vs the same 0/3 baseline) and carries a
  **provenance caveat** (cases Codex-reconstructed from the dp3 corpus, not Claude-authored).

## C6 — Scope guards (closure-spec §5, brief)

- **No new hooks** (`intent-management-loop` D6 stands). Any new obligation is a skill-step /
  charter change, not a PreToolUse hook.
- Do not collapse this into D-cost or D-xfam — distinct commitments, distinct gates.
- Out of scope: writing the firm ADR, making the call, building `measure-before-enforce`
  D1/D3 instrumentation.
