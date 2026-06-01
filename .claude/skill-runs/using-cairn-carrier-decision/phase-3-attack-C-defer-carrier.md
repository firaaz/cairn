---
decision: using-cairn-carrier-contract
phase: 3-attack
approach: C-defer-carrier
date: 2026-06-01
verdict: SURVIVES-AS-FALLBACK-ONLY (does not satisfy the slice's accepted decision; survives only if the adjudicator reframes D5 as discretionary)
---

# Phase 3 — Adversarial stress test of Approach C (defer the carrier)

Method: disconfirming search against live source. Each load-bearing claim tagged
VERIFIED (matches source) or BELIEVED (asserted, source says otherwise / silent).
Default-to-refute: a standing fatal flaw → survives=false.

## Process note — Phase 0/1 artifacts for THIS decision do not exist

The brief and Phase-2-C cite `phase-0-constraints.md`, `phase-1-premortem.md`,
`phase-0.5-journey.md` under `using-cairn-carrier-decision/`. Only the three
`phase-2-*.md` files exist there (`ls`). Phase-2-C's line-cites to
`phase-0-constraints.md:118-167`, `phase-0.5-journey.md:149-322`,
`phase-1-premortem.md:21-118` are **uncheckable** — they point at files that were
never written for this run. I audited C's claims against LIVE SOURCE (ADRs, YAML,
hooks, tests, lessons) instead, which is the stronger check anyway. Where C's only
support is a non-existent phase-0/1 file, I mark the claim BELIEVED.

## The decisive refutation (read this first)

C's thesis is "build *no* dedicated SessionStart carrier in slice #2." But **D5 is a
Decision, not an option**: `intent-management-loop.md:77-78` reads "**D5 — SessionStart
carrier.** Build the `using-cairn` SessionStart carrier" — imperative. The
"optimization, not the only path" clause (`:80-81`) describes the carrier↔fallback
*relationship* (the carrier may not fire, so the skill must self-load); it does not
license skipping the build. C's own constraint table concedes this:
"`delivery-mechanism-friction` D1 SKILL-at-SessionStart → **NOT ACTIONED**"
(`phase-2-C-defer-carrier.md:190`) and "declines `delivery-mechanism-friction` D1's
named, accepted deliverable" (`:267-270`).

So C is not "approach C of the carrier-contract decision." C is a *motion to vacate the
decision* — to re-litigate D5 of an already-accepted ADR and D1 of a second already-accepted
ADR. The adjudication question for this slice is *how to realize the carrier*, not *whether*.
Choosing C means the slice does not produce the artifact two accepted ADRs commit it to
produce, and does so **without a superseding ADR** (`phase-2-C:148` admits "C does not
supersede D1 — it leaves D1 un-actioned"). Un-actioning an accepted decision-point without
supersession is the gap. That is the fatal flaw; everything else is secondary.

This does not mean C's engineering is wrong — its premortem-elimination is real and its
honest-minimal fit is genuine. It means C answers a different question than the one under
adjudication, and answering it requires re-opening a closed decision through the wrong door.

---

## Sub-question audits (disconfirming)

### (1) Does C's "fired" test prove anything real?

C's answer: "fired" is a frozen contract STUB; the shipped test asserts only the *negative*
(skill works with no carrier signal) (`phase-2-C:50-67`).

- VERIFIED: the existing `tests/unit/test_cairn_intent_workflow.py` does **not** cover
  `load-or-form-intent` (grep: no match for `load-or-form` / `intent-pointer` /
  `material-delta` / `contract-floor`). C's "closes exactly that gap" claim (`:66-67`) is true.
- VERIFIED: `workflows/cairn-intent.yaml:16-65` runs `load-or-form-intent` with
  `execution.context: current`, no carrier precondition; evidence `intent-pointer`
  (`:39-42`), `material-delta-classification` (`:43-45`). The fallback path D5 names is
  already built in the workflow. C's load-bearing fact is real.
- **REFUTATION**: C's "fired" test proves *nothing about firing* — by construction. It tests
  that the skill is carrier-independent (good), but D9 (`:100-102`) names "the carrier's
  **fired-detection** + fallback" as the unit-test scope. C tests the fallback half and
  *documents* the fired half as prose in a `docs/carrier-contract.md` that has zero executable
  binding. Compare the build-it test
  (`proposed/test_using_cairn_carrier.py:59-63`):
  `assert out.splitlines()[0] == "CAIRN_CARRIER_FIRED"` — a real subprocess assertion that
  the emitter ran and emitted the marker. C's draft replaces an executable fired-detection
  test with a markdown paragraph. So the honest reading is: C does not half-satisfy D9's
  carrier test; it **removes** the carrier test and substitutes documentation. The slice ships
  with the fired-detection acceptance gate untested-because-the-subject-is-unbuilt
  (C concedes this, `:69-73`).
  - Note C's own caveat is correct that EVEN the build-it test (option A/B) only proves "a
    script runs and renders a marker," not "real SessionStart injection on a consumer host"
    (this is the brief's sub-q (1) caveat, and `proposed/test_using_cairn_carrier.py` header
    line 14-15 admits "no module under test"). So the fired-test ceiling is low for everyone.
    But C is strictly *below* that low ceiling: it proves the script runs by not having a
    script.

### (2) Does C satisfy INV-004 and the ≤2k budget?

C's answer: vacuously — no payload to clamp (`phase-2-C:79-93`).

- VERIFIED: INV-004 is ≤40k fresh-session, machine-checked by `test_context_budget.py`
  which live-runs `claude -p hi` (`ARCHITECTURE.md:39-44`; `test_context_budget.py:48,65`,
  `BUDGET_HARD = 40_000` at `:18`). The ≤2k is the *additive* carrier sub-budget
  (`delivery-mechanism-friction.md:39,134`). No carrier ⇒ no additive cost. C is technically
  correct: it cannot breach a budget for a payload it does not emit.
- **PARTIAL REFUTATION (not fatal)**: this is the weakest of C's claims to attack — it holds.
  But it holds *by not delivering the thing the budget governs*. "I satisfy the speed limit by
  not driving" is true and useless. The budget question (sub-q 2: in-hook clamp vs CI gate vs
  both) is one the slice was convened to *answer*; C answers it by deferring it
  (`:88-90` hands `CAIRN_SESSIONSTART_BUDGET` + the D6 CI gate to a follow-on). The
  build-it draft already answers it concretely: in-hook byte clamp
  (`using-cairn-carrier.sh:18,29` `BUDGET_BYTES=${CAIRN_CARRIER_BUDGET_BYTES:-8000}`, head -c)
  — CLAUDE.md no-hardcoded-sizes compliant. So on sub-q 2 C is not refuted on correctness; it
  is refuted on *responsiveness* — it declines to decide.
- L-005 MISATTRIBUTION (inherited, flag only): C cites "L-005 drift exposure"
  (`phase-2-C:96-100,213-214`) for budget drift. `lessons.md:92` L-005 is "Parallelism
  substrate works; skill-level coordination is the actual tax" — nothing to do with token
  budget. BUT `delivery-mechanism-friction.md:72` D6 *itself* says "L-005 drift exposure," so
  C faithfully repeats the ADR's own error. Not C's flaw to own; it is a latent bug in the
  source ADR the adjudicator should note. The intended lesson is almost certainly a
  SessionStart/INV-004 drift lesson, not L-005.

### (3) Fallback contract — does C's "no branch" hold?

C's answer: the fallback IS the whole contract; the skill never branches on carrier state
(`phase-2-C:106-124`).

- VERIFIED: `cairn-intent/SKILL.md:19` Step 1 "Load or form the thinnest sufficient intent"
  is unconditional; `workflows/cairn-intent.yaml:61-64` `load-or-form-intent` is
  `executor: conversation, context: current` with no carrier precondition. The skill genuinely
  does not probe `CAIRN_CARRIER_FIRED`. C's "no branch to silently fail" is correct and is
  L-005's *actual* lesson applied correctly (prose-specified side-effects execute
  inconsistently under context pressure, `lessons.md:96` — ironically the right cite for this
  point, the wrong cite for sub-q 2).
- **NO REFUTATION HERE**: this is C's genuinely strong point and it is identical to what the
  build-it approaches must also do (the carrier never gates either way). C does not *win* the
  decision on (3); it ties — because every approach makes the skill self-load. C's marginal
  claim — "there is no carrier state to branch on" — is a difference that makes no behavioral
  difference, since no approach branches on carrier state.

### (4) Realization — does C reconcile the bash-vs-SKILL tension?

C's answer: neither; no SessionStart artifact realized; tension deferred (`phase-2-C:128-151`).

- **REFUTATION**: sub-q (4) literally asks "reconcile [the bash script] with D1's wording"
  (`delivery-mechanism-friction.md:39` specifies a SKILL at `dist/skills/using-cairn/SKILL.md`
  registered via hooks.json). C does not reconcile — it declines. That is a non-answer to a
  direct question. The draft's bash realization (`proposed/using-cairn-carrier.sh`,
  `proposed/hooks-template.json` SessionStart entry) is at least *an* answer that the slice can
  adjudicate; C removes the question from the table. An adjudicator cannot select C as "the
  realization decision" because C's realization is "do not realize."
- VERIFIED detail-error in C (minor): C says hooks-template.json "registers exactly the three
  guards (reversibility-guard.sh, role_guard.py, reality-check.sh)" (`phase-2-C:39-41`).
  Actual `.claude-plugin/hooks-template.json:3-33` registers reversibility-guard (PreToolUse),
  role_guard (PreToolUse), reality-check (PostToolUse) — three hook *entries*, correct count,
  but D6's three *guards* are premise_guard/role_guard/atomicity_guard
  (`intent-management-loop.md:83-84`), and premise_guard + atomicity_guard are **not** wired
  into hooks-template.json at all (they appear only as `guards:` labels in
  `cairn-intent.yaml:9-13`). So C's "D6 no-new-hooks holds trivially" (`:41`) is true but its
  parenthetical naming of the three is muddled. Not load-bearing for C's thesis; flagged for
  accuracy.

### (5) Distribution — does C's choice contradict ADR R1 / provisional firmness?

C's answer: ship nothing carrier-shaped; R1/R3 neutralized for the carrier (`phase-2-C:155-176`).

- VERIFIED: no `dist/` exists today (`ls dist/` → ENOENT); `build_dist.py` ALLOW_LIST (`:18-33`)
  has no carrier row. C leaves it untouched, so no carrier goes stale in a consumer
  `.slice-system` (R1, `intent-management-loop.md:146`) and none fails to fire on a non-CC host
  (R3, `:148`). C's neutralization claim is real and is the honest mirror image of the build-it
  blast-radius the brief flags ("ADR R1 stale-.slice-system / non-CC-host blast radius on every
  consumer session").
- **NO REFUTATION on safety**; this is C's second genuinely strong point. It is *consistent*
  with provisional firmness — provisional means cheap to reverse, and shipping nothing is the
  cheapest reversal. But note the asymmetry: provisional firmness is an argument for *shipping
  cautiously*, not for *not shipping*. `delivery-mechanism-friction.md:91,128` R4 already
  prescribes the cautious-ship posture ("If shipped SessionStart does not collapse J1 friction
  … open a follow-up /decision; do NOT accrete payload as a workaround"). C inverts R4: R4 says
  ship-then-revisit-if-it-fails; C says do-not-ship-until-proven. R4 is the ADR's settled
  answer to exactly C's risk, and C silently overrides it.

---

## Premortem-elimination claims (C's headline strength) — audited

- VERIFIED: L-012 (`lessons.md:225-231`) is real and exactly as C describes — a SessionStart
  cheatsheet (`role-cheatsheet.sh`) emitting a stale "/start-slice" line caused a Phase-4
  opus-low integrator to refuse 4× quoting the hook text (`:231`). A carrier is a SessionStart
  emitter; every build-it approach inherits this surface. C builds no emitter ⇒ **zero L-012
  exposure**. This is C's single strongest, fully-verified point (`phase-2-C:214-220`).
  - Counter: L-012's mechanism is *schema drift between hook and a consumer that reads it
    literally*. The build-it draft's carrier emits a pointer + "run the cairn-intent skill"
    (`using-cairn-carrier.sh:41-46`) — it carries no slice-status schema to drift. L-012's
    specific failure (status-field mismatch) is not structurally reachable by a pointer-only
    carrier. So C over-claims slightly: it eliminates L-012's *class* (any SessionStart text a
    tier-sensitive consumer can misread), but the build-it design already mitigates L-012's
    *instance* by being pointer-only and intent-neutral. The delta between C and build-it on
    L-012 is "zero exposure" vs "low, structurally-bounded exposure," not "zero vs high."
- VERIFIED-as-orthogonal: Scenario 4 (premise_guard `.slice-system` traversal, R4
  `intent-management-loop.md:149`) is carrier-independent; C does nothing, neither does any
  carrier approach (`phase-2-C:224-227`). Fair.
- **SHARPEST RESIDUAL (C's own admission, verified)**: Scenario 5 — C makes the un-versioned
  fallback the *only* path and the fallback does not freshness-check what it loads
  (`phase-2-C:228-232`). `load-or-form-intent` (`cairn-intent.yaml:28-48`) reads handoff +
  skill-runs intent with no schema/staleness gate. C removes the carrier-misfire vector but
  leans harder on the un-versioned loader, and now has no second path. This is real and C is
  honest about it — but it weakens C's "lowest-risk" framing: it trades a *bounded, testable*
  carrier-misfire risk for an *unbounded, untested* stale-load risk on the sole path.

---

## Fatal vs serious

### Fatal

1. **C does not produce the slice's accepted deliverable.** D5 (`intent-management-loop.md:77-78`,
   imperative "Build … carrier") and D1 (`delivery-mechanism-friction.md:37-39`, names the
   SKILL-at-SessionStart artifact) both commit slice #2 to build the carrier. C builds none and
   does not supersede either ADR (`phase-2-C:148,190,267-270` self-admits "NOT ACTIONED" /
   "does not supersede D1"). Un-actioning two accepted decision-points without a superseding ADR
   is outside this slice's authority — it is a `/decision` to re-open D5/D1, not a realization
   choice. As an answer to "the using-cairn SessionStart carrier contract," C is non-responsive.

2. **C removes, rather than partially satisfies, the D9 fired-detection acceptance gate.**
   D9 (`:100-102`) names "the carrier's fired-detection + fallback" as unit-test scope. C ships
   a fallback-only test and a non-executable markdown stub for fired-detection
   (`phase-2-C:50-73`). The carrier acceptance gate is not half-met; its subject is deleted, so
   the gate is vacuous. The slice would close with an accepted ADR's named test scope unbuilt.

### Serious

1. **Non-answer to sub-q (4).** The brief asks C to *reconcile* bash-vs-SKILL with D1's wording;
   C defers the question (`phase-2-C:128-151`). An adjudicator cannot pick C as the realization
   decision because C declines to realize.

2. **Non-answer to sub-q (2) and silent override of R4.** C defers the byte-clamp-vs-CI-gate
   choice (`:88-90`) and inverts `delivery-mechanism-friction.md:91,128` R4 (ship-then-revisit)
   into do-not-ship-until-proven, without naming that it is overriding R4.

3. **Sole reliance on the un-versioned fallback (Scenario 5).** C's own sharpest residual
   (`:228-232`): the load-or-form path has no freshness/schema check (`cairn-intent.yaml:28-48`)
   and is now the only path. Trades bounded carrier-misfire for unbounded stale-load.

4. **Measurement-validity hit to Trial E / D7.** C leaves per-session load-or-form un-amortized,
   biasing the felt-cost-vs-four-phase comparison upward — exactly the variable D7's pass-condition
   weighs (`intent-management-loop.md:88-91`; `phase-2-C:249-256`). C could make the loop look
   more expensive than the carrier-enabled design it is meant to replace.

5. **Citation hygiene:** (a) C's phase-0/0.5/1 cites point at files that do not exist for this
   run; (b) C repeats the source ADR's L-005 misattribution for budget drift
   (correct lesson is not L-005; `lessons.md:92`); (c) C's "three guards" parenthetical
   (`:39-41`) conflates hook entries with D6 guards (premise_guard/atomicity_guard are not in
   hooks-template.json). None load-bearing for the thesis, but they erode the artifact's
   reliability.

## Verdict

survives = **false** as an answer to *this* decision. C is a well-reasoned argument for
*deferring* the carrier, and its safety case (zero L-012, R1/R3 neutralized, honest-minimal) is
the strongest of any approach — but it answers "should we build the carrier now?" with "no,"
when the slice's job is "how do we build it?", and it reaches that "no" by un-actioning two
accepted ADR decision-points without supersession. It survives ONLY if the adjudicator first
rules that D5/D1 are discretionary for this slice (reframing the carrier as not-yet-committed) —
which is itself a `/decision`, not a finding this Phase can grant. Absent that reframing, the
fatal flaw stands: C does not deliver, and does not test, the carrier the slice exists to
deliver. Its genuine merits (L-012 avoidance, blast-radius avoidance, the verified
load-or-form-coverage gap it would close) should be **harvested into the chosen build-it
approach** — ship a pointer-only carrier that cannot drift schema (mitigating L-012's instance)
and add C's fallback-only test *alongside* the executable fired-detection test, not instead of it.
