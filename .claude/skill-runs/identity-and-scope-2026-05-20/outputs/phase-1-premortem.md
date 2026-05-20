# Phase 1 — Pre-Mortem

Failure scenarios are enumerated **before** Phase 2 proposes any approach.
Each scenario names the failure, the mechanism, the pole(s) it hits, and
how it would be detected.

---

## Technical failures

### T1. Tier misclassification becomes a new high-consequence failure mode

**Mechanism.** The pivot reframes the question from "is this important enough
for Cairn?" to "what is the cost of being confidently wrong?" — but answering
that question correctly requires the operator to NOT be confidently wrong
about the cost. An operator misjudges a Tier-3 change as Tier-1 (no phase
isolation, no contract evidence), ships, and the methodology has no defense
because it deferred to the operator's own classification.

**Hits.** Pole B primarily (Pole C inherits this via hook-selection mistakes).

**Detected by.** First post-incident review where an architectural mistake
ships under a too-low tier. By construction, this is exactly the class of
failure cairn was built to prevent — `cliff-failure-mode-and-v1-defenses.md`
D0/D1/D2/D3.

**Hardening idea (not a decision yet).** Hard-override list (security,
irreversibility, architecture invariant change → forced Tier 3) is in the
direction doc but **classification of an ambiguous change is still the
operator's call**. The hard-override only catches the categorical cases.

---

### T2. Risk-scoring tool ships without calibration because there is no
calibration source

**Mechanism.** Steelman's "ship to generate calibration data" argument
assumes a varied corpus of tasks across many projects. Cairn's primary user
is one operator doing cairn-on-cairn (Phase 0 firm constraint). The risk
scorer's break points (`0-1 → Tier 0, 2-3 → Tier 1, 4-5 → Tier 2, 6+ → Tier
3`) accumulate no signal beyond what one operator's intuition already
provides. The tool ships, sits, becomes dead code; its presence implies
empirical grounding it never earns.

**Hits.** Pole B.

**Detected by.** 6-month retrospective: how many times did the risk-scorer's
recommendation differ from the operator's intuition? If <5 differences, the
tool produced no signal worth its maintenance burden.

---

### T3. Hook-discoverability failure under Pole C

**Mechanism.** À la carte tooling requires the operator to know which hooks
to enable. Phase 0.5 surfaced this gap explicitly: no affordance exists. The
operator forgets reversibility-guard.sh on an ADR-write session; an ADR is
overwritten by mistake; cairn's whole append-only invariant is silently
violated. Same class of failure cairn was built to prevent.

**Hits.** Pole C.

**Mitigation.** Mandatory-on safety hooks (Tier 0 in pole B language) plus
operator-declarable extensions. But once you require mandatory-on safety
hooks, you've reinvented Tier 0 — Pole C without Tier 0 doesn't work; Pole C
with Tier 0 is Pole B without the upper tiers.

---

## Scale failures

### S1. Bypass path becomes the de facto path (Pole A)

**Mechanism.** Status quo identity is "high-consequence four-phase
methodology." But the operational reality on `dev` today is three execution
paths: ad-hoc edit (operator envelope), /decision arc, cairn-tdd-feature
dispatch (Phase 0.5). The four-phase dispatch is the most expensive path; for
small fixes, ad-hoc edit is what gets used. This is already happening — the
operator is making cairn-on-cairn changes via /decision and ad-hoc edits
**right now**, not via cairn-tdd-feature. The four-phase becomes a Sunday-
best ceremony invoked rarely; its mechanical reliability erodes.

**Hits.** Pole A (status quo).

**Detected by.** Counting cairn-tdd-feature invocations on `dev` over the
last 90 days vs. ad-hoc + /decision invocations. Already observable.

---

### S2. Documentation surface area multiplies under Pole B

**Mechanism.** Four tiers × (spec, operational-reference, hook config, test
shape, contract template) = 20+ documented combinations. spec-v1 §1's scope
clause ("not for simple software") requires amendment for tier 0/1 to make
sense. operational-reference's "primary mental model" rewrites for graduated
guardrails. Each tier wants its own contract template. The methodology repo
becomes a methodology *suite* repo; doc drift becomes the primary failure.

**Hits.** Pole B.

**Detected by.** Three months after pivot: number of open issues tagged
`doc-drift` or `tier-confusion`. Compare to baseline drift rate.

---

### S3. Vestigial Tier 3 (Pole B late-stage)

**Mechanism.** With Tier 1/2 available, the operator's revealed preference
will be "I'm doing Tier 1 today" for almost everything. Tier 3 becomes a
preset nobody uses; the four-phase machinery + agents + dispatch skill rot.
A future "simplification" pass deletes them. By then the original
orthogonality (Phase 0.5: "all three poles can drop the four-phase without
breaking hooks") may have decayed because something has crept across the
boundary — and the rollback path is gone.

**Hits.** Pole B (long-term).

**Detected by.** Year-2 audit: percentage of changes invoking Tier 3
machinery. Below 10% = vestigial; consider explicit retirement instead of
silent rot.

---

## Integration failures

### I1. Handoff contract collides with non-dispatch tier work (Pole B)

**Mechanism.** Trial A's handoff contract assumes every open thread has a
resolvable pointer. Tier 0/1 work that doesn't go through cairn-tdd-feature
dispatch has no `.claude/skill-runs/<feature-id>/` directory to point to.
Phase 0.5 explicitly flagged this gap. Tier-0 changes become invisible to
/catchup; drift accumulates between what `dev` actually contains and what
the handoff says is in flight.

**Hits.** Pole B. Pole C inherits if handoff-contract test is à la carte.

**Detected by.** A `/catchup` that misses load-bearing in-flight work.

---

### I2. spec-v1 scope clause amendment is a one-way door

**Mechanism.** spec-v1 §1 explicitly scopes Cairn to complex AI-assisted
engineering only ("not for simple software"). Pole B's "Tier 0 default for
ordinary repositories" framing requires amending this. Once Cairn officially
says "graduated reliability for all projects, scaled to risk," walking back
to "only complex high-consequence work" is far more expensive — consumers
will have built mental models, downstream plugin installs will assume
Tier-0 hygiene works for any repo. The amendment is high-firmness even if
provisional.

**Hits.** Pole B.

**Detected by.** First post-pivot consumer who tries to install cairn into a
prototype repo and finds Tier 0/1 doesn't deliver on promises (because they
were designed for a different threat model).

---

### I3. Direction-doc framing exports a market motion as a reliability claim

**Mechanism.** "Cairn should not compete with [Claude/Codex] runtimes" and
"useful from day one in ordinary repositories" are adoption-motion claims.
But the direction doc justifies them with reliability arguments. If Pole B
ships and no external adoption follows (Phase 0 firm constraint: no external
pull demonstrated), the cost — doc rewrite, tier infrastructure, spec
amendment — was paid for an unrealized claim. The reliability tooling still
works; the framing investment is the loss.

**Hits.** Pole B.

**Detected by.** 12-month retrospective: external consumer count. If still
1 (the operator), the framing was a sunk cost.

---

## Failure-mode classification

| ID | Pole(s) | Detectability | Cost-to-fix if it fires |
|----|---------|---------------|--------------------------|
| T1 | B (C) | Post-incident, high latency | High — cliff-failure-mode is firm |
| T2 | B | Self-detecting at retrospective | Low — delete the script |
| T3 | C | Immediate at first hook gap | Medium — re-add mandatory hooks (= reinvent Tier 0) |
| S1 | A | Observable now on `dev` | High — methodology rot is hard to reverse |
| S2 | B | Visible in 3 months | Medium — doc consolidation |
| S3 | B | Visible in 12-24 months | Medium — explicit retirement |
| I1 | B (C) | Visible at /catchup miss | Low — handoff-contract amendment |
| I2 | B | Visible at first consumer | High — spec amendment is one-way |
| I3 | B | Visible in 12 months | Medium — framing revert |

---

## What Phase 2 must defend against

The strongest failure cluster is **Pole B integration failures**: I1 (handoff
collision), I2 (spec amendment one-way door), I3 (market motion mistaken for
reliability claim). Any tier-model approach must address these explicitly, or
it inherits all three.

The strongest **Pole A failure** is S1 (bypass path is already the de facto
path). Status quo is not a stable position — it is already silently eroding.

The strongest **Pole C failure** is T3 (hook discoverability), which folds
Pole C back into Pole B once mandatory-on safety hooks are added.

This suggests Phase 2's approaches will cluster around: "address S1 (the
status quo is already broken) without inheriting I1/I2/I3 (Pole B's
integration costs)." The space between Pole A and Pole B is where the
genuine design move lives.
