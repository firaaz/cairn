# Trial-D — 3-intent atomicity measurement (record)

Status: **m2 run halted by an operator-friction finding (2026-05-31); measurement not
completed as designed.** See "## m2 run — result & finding" below. The friction is itself
a recorded Trial-D finding (the plan mandates recording, not papering over). Pass on all
three metrics would have unblocked Trial E.

- Plan: `docs/plans/2026-05-30-cairn-trial-d-scope-split.md` § "Next session — the 3-intent measurement"
- Trials umbrella: `docs/plans/2026-05-20-cairn-thin-substrate-trials.md` § "Trial 2" (= Trial D)
- Frozen mechanism: `scripts/lib/atomicity.py` `is_atomic()` post-F1 (`43850f7`); gate `checks/atomicity_guard.py`

## Integrity boundary (why this is non-headless)

Metrics #1 and #2 measure the **operator's** authoring experience. If the assistant authors
any `## Contract` → `must-satisfy` clause, those numbers are void. Roles:
- **Operator** — authors `must-satisfy` in EARS, makes the tag/split calls, stopwatches #1, flags #2, adjudicates #3.
- **Assistant** — instrument only: scaffolded the scratch files (done), runs the gate, proposes FP labels.

## The three intents (size range; do in order — LIGHT first)

| Size   | Scratch                   | Source intent (read-only)                            | Behaviors            |
|--------|---------------------------|------------------------------------------------------|----------------------|
| LIGHT  | `light-m2-scratch.md`     | `m2-dogfood-extract-invariant-ids/intent.md`         | 8 (b1–b8)            |
| MEDIUM | `medium-m7-scratch.md`    | `cairn-m7-plugin-deployment-pattern/intent.md`       | S1–S6 + FLI-1..7     |
| HEAVY  | `heavy-m5-f1-scratch.md`  | `cairn-m5-f1-packaging/intent.md`                    | A1–A12               |

The source intents are completed-run records — **never mutated**; each scratch holds a verbatim
copy for derivation plus an empty `## Contract` skeleton.

## Metrics & targets (§2 Trial 2 of the trials plan)

| # | Metric                     | Target          | Instrument |
|---|----------------------------|-----------------|------------|
| 1 | Authoring-time delta       | ≤30%            | operator stopwatch (EARS+tag authoring) vs felt-prose baseline; small-N self-report |
| 2 | Rubber-stamp reduction     | ≥2 of 3 intents | binary/intent: did the gate surface a split/tag call you'd have waved through? |
| 3 | Atomicity false-positive   | <10%            | of clauses the gate FLAGS, the fraction the operator judges genuinely atomic |

**4th observation** (carried from Probe A; not a pass/fail gate): did the *prose-leakage* failure
mode recur — a clause that passes the gate (grammatically-fine EARS, atomic-looking) but that
atomicity *should* have rejected? Record any instances.

## Proposed scoring interpretation — assistant's call, **confirm or correct before we score**

The plan leaves three things underspecified; my defaults:
- **#3 denominator** — report per-intent AND pooled across all three. m2 is the controlled anchor:
  all 8 behaviors should be atomic, so any flag on m2 is a false positive. Pass test applied to the pooled rate.
- **#1 HEAVY breach** — a named failure: if the HEAVY (m5) delta > 30%, that's a real finding even if LIGHT/MEDIUM pass.
- **Gate mode** — default (Contract block present, so fail-open-on-absence doesn't apply; `CAIRN_CONTRACT_REQUIRED` unset).
- **Authoring scope** — one EARS clause per behavior (m2: all 8; m7: S+FLI set; m5: A1–A12), matching a real Phase-1→2 contract authoring. Subset is fine if you'd rather; say so and I'll note it.

## Per-intent record (fill during the run)

### LIGHT (m2)
- #1 elapsed: ___   felt-prose baseline: ___   delta: ___
- #2 rubber-stamp surfaced (Y/N): ___   note: ___
- #3 gate flags: ___   operator-judged-atomic (FPs): ___   FP rate: ___
- post-F1 sanity — b2 ("…no INV-NNN patterns") + b8 ("…no word boundaries") pass BARE? ___
- prose-leakage recurrence: ___

### MEDIUM (m7)
- #1 elapsed: ___   felt-prose baseline: ___   delta: ___
- #2 rubber-stamp surfaced (Y/N): ___   note: ___
- #3 gate flags: ___   operator-judged-atomic (FPs): ___   FP rate: ___
- prose-leakage recurrence: ___

### HEAVY (m5)
- #1 elapsed: ___   felt-prose baseline: ___   delta: ___ (>30% = named breach)
- #2 rubber-stamp surfaced (Y/N): ___   note: ___
- #3 gate flags: ___   operator-judged-atomic (FPs): ___   FP rate: ___
- prose-leakage recurrence: ___

## Verdict (after all three)
- #1 ≤30%? ___   #2 ≥2/3? ___   #3 <10% (pooled)? ___
- → PASS unblocks Trial E  /  FAIL = recorded finding (narrow the heuristic further, or accept as advisory-only)

## m2 run — result & finding (2026-05-31)

**What happened.** Operator (sole operator; first-ever exposure to EARS/structured contracts)
authored the m2 `## Contract`. First pass: 2 invented clauses unrelated to m2. Second pass:
4 of 8 behaviors, terse/non-EARS shorthand (e.g. "Match strictly to 3 digit numbers",
"Only caps allowed"). Gate read all clauses as atomic, 0 flags. Operator then reported the
authoring itself was painful, and elected to halt and reconsider the authoring model.

**Mechanical metrics — not validly obtained:**
- #1 authoring-time delta — void (confounded by first-exposure learning ramp + two redos + my corrections; m2 also can't isolate steady-state ceremony).
- #2 rubber-stamp reduction — m2 surfaced no split/tag decision (expected: m2 is all trivially atomic by design), so no signal either way.
- #3 false-positive rate — not exercised: shorthand undercovered (4/8) and avoided the exact "no …" wording (b2/b8) the F1 fix targets. (Post-F1 sanity that b2/b8 pass **bare** is independently green in `tests/unit/test_atomicity.py::test_no_negation_clauses_stay_atomic`, so the mechanism is confirmed there, not here.)

**Primary finding (qualitative).** Operator hand-authoring of the EARS `must-satisfy` contract
is experienced as painful/ritualistic **even on the lightest, most trivially-atomic intent**,
after a full ground-up explanation. This matches Probe A's prediction ("ritualistic on light
intents"), and lands it harder: the ceremony felt like pure tax because a light intent gives
the gate nothing to catch — no payoff is visible where every behavior is already atomic.

**Operator's reframe (the chosen disposition).** Reconsider *who authors*: assistant drafts
the contract, operator reviews/approves — rather than operator authoring EARS from scratch.

**The load-bearing counterargument (recorded so /decision must answer it).** Operator-authoring
is not ceremony for its own sake — it is *the mechanism by which the human's actual goal enters
the system*. Assistant-drafting risks the operator only rubber-stamping **what** the feature
should do, and the existing guards do **not** catch that: `premise_guard` checks that quotes are
grounded in source, and the front-challenge (intent-management-loop ADR) attacks premises — both
verify *grounding*, not *intent-fidelity to the operator's goal*. A perfectly-grounded
assistant-drafted intent can still be the wrong intent. This is the exact failure metric #2
("rubber-stamp reduction") and the thin-substrate identity D7 ("keep AI-authored intent bound to
verifiable evidence") exist to prevent.

**Candidate synthesis (for /decision, not settled here).** Separate **intent** (what it should do
— stays human, as a brief/prose) from **formalization** (EARS shape + atomicity + tags — the
painful part — done by the assistant), with the operator reviewing the formalization for
*fidelity*, and `premise_guard` + the atomicity gate + the front-challenge keeping the
formalization honest. This targets the pain (formalization, not intent) while preserving the
anti-rubber-stamp guard for *what*. Hinges on the disentangle question still open: was the pain
the EARS *formalization* specifically, or the harness (scratch file / redo / corrections)?

**Confounders / weight.** n=1 operator, lightest intent only, first exposure, clunky measurement
harness. Real but limited; not "operator-authoring is dead."

**Disposition.** Authoring-model question is decision-weight and reshapes the
`intent-management-loop` ADR's authoring model → routes to `/decision`. Trial-D's #1/#3 remain
unmeasured-as-designed; that is the finding, and Trial E stays gated.
