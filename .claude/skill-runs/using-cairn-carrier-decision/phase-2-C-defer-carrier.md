---
decision: using-cairn-carrier-contract
phase: 2-approach-C
approach: C-defer-carrier
date: 2026-06-01
---

# Phase 2 — Approach C: Defer the Carrier

**Thesis.** The carrier is an optimization (`intent-management-loop.md:80-81` D5: "carrier is
an optimization, not the only path"). Build *no* dedicated SessionStart carrier in slice #2.
Run Trial E on the `cairn-intent` skill alone. Build only (a) a documented "carrier-fired"
*contract stub* (frozen interface, zero emitter) and (b) a unit test asserting the skill's
`load-or-form-intent` step works with no carrier signal. Promote to a real carrier as a
follow-on once the loop is proven and D5's "fired"/budget/realization questions can be answered
against a working loop rather than against a hypothesis.

This is the minimum-premature-commitment answer. It is honestly weaker than the build-it
approaches on the friction D5/`delivery-mechanism-friction` D1 set out to remove. Below I flesh
all five sub-questions, then state where it is exposed and where it is not.

---

## What is already built (the load-bearing fact for this approach)

The `cairn-intent` skill and `workflows/cairn-intent.yaml` already ship the fallback as a
*built* node, not a prose promise:

- `workflows/cairn-intent.yaml:16-49` — node `load-or-form-intent` runs unconditionally
  (`execution.context: current`, no carrier precondition). Its required evidence
  `intent-pointer` is defined verbatim as "Active intent path or explicit no-intent signal"
  (`:40-42`) and `material-delta-classification` as "New, material-change, or resume"
  (`:43-45`). This is *exactly* D5's "emits the intent pointer or a no-intent signal"
  (`intent-management-loop.md:80`) — already realized inside the skill, off the SessionStart
  path.
- `plugins/cairn/skills/cairn-intent/SKILL.md:19` — Step 1 "Load or form the thinnest
  sufficient intent" is unconditional and lists `templates/intent.md` for new-intent forming.
- `.claude-plugin/hooks-template.json:1-35` — registers exactly the three guards
  (`reversibility-guard.sh`, `role_guard.py`, `reality-check.sh`); there is **no SessionStart
  entry today**. Deferring the carrier means this file is untouched, so D6 "no new hooks"
  (`intent-management-loop.md:83-85`) holds trivially.

C-defer-carrier's claim is therefore *not* "ship nothing" — the fallback path D5 names as the
reliable path is already in the payload. C declines to add the *optimization layer* on top of it.

---

## Sub-question (1) — Testable "fired" definition

**Answer: "fired" is defined as a frozen contract STUB, not an emitter.** No carrier exists, so
the runtime fired-signal is not produced in slice #2. Instead we write down the interface the
future carrier MUST satisfy and test the *negative*: the skill behaves correctly when nothing
fired.

- **Documented stub** (a markdown contract, e.g. `docs/carrier-contract.md`, no code): the
  future carrier, when built, emits to stdout `CAIRN_CARRIER_FIRED=1` plus one line
  `CAIRN_INTENT_POINTER=<path>` or `CAIRN_INTENT_POINTER=NO_INTENT`, within the ≤2k budget. This
  matches the Phase-0.5 testability surface (`phase-0.5-journey.md:266-268`) but is frozen as a
  *target*, not implemented.
- **The test that ships** (new `tests/unit/test_cairn_intent_skill_no_carrier.py`): asserts the
  `load-or-form-intent` node in `workflows/cairn-intent.yaml` (a) runs with no
  `CAIRN_CARRIER_FIRED` in the environment, (b) declares the `intent-pointer` evidence as
  required, (c) emits a no-intent classification path. This is a *render*/static-contract test
  against the YAML and skill prose — it asserts the skill's first step is carrier-independent.
  Note the existing `test_cairn_intent_workflow.py` (6 tests, `:16-80`) covers
  challenge/review/construct topology but does **not** assert the `load-or-form-intent`
  evidence contract — this approach closes exactly that gap.

**Honest weakness:** D5 (`intent-management-loop.md:79-82`) and D9 (`:100-104`) literally name
"the carrier's fired-detection + fallback" as a unit-test scope. C tests *only* the fallback
half. The fired-detection half is documented-but-untested-because-unbuilt. C must argue D9's
acceptance gate is satisfied by "fallback works + fired-contract frozen," which is a defensible
but contestable reading of "fired-detection + fallback."

---

## Sub-question (2) — ≤2k-token budget enforcement

**Answer: no enforcement needed in slice #2, because there is no SessionStart payload to clamp
or gate.** INV-004's ≤40k fresh-session budget (`ARCHITECTURE.md:39`,
`tests/unit/test_context_budget.py` live-measures `claude -p hi`) is unaffected — the carrier
would have been the *additive* ≤2k cost (`delivery-mechanism-friction.md:134`), and that cost
is simply not incurred. Neither an in-hook byte clamp nor `delivery-mechanism-friction` D6's CI
tokenizer gate (`:70-72`) is built.

- The ≤2k sub-budget (D1 `delivery-mechanism-friction.md:39`) becomes a *documented target* in
  the carrier-contract stub, to be enforced by the follow-on slice that actually builds the
  emitter — at which point the CAIRN_<KNOB> env-override (`CAIRN_SESSIONSTART_BUDGET`,
  CLAUDE.md no-hardcoded-sizes) and the CI gate are designed against a real payload, not a
  guessed one.
- This *eliminates* the Phase-1 Scenario-3 budget-drift class entirely for the trial window:
  there is no payload, so it cannot drift past 2k, so there is no silent INV-004 creep on
  consumers (`phase-1-premortem.md:52-66`).

**Honest weakness:** `delivery-mechanism-friction` D6 (`:70-72`) said the CI token-budget check
"is included as in-slice work … If the check cannot land in-slice, … demote S9 … to EXPOSED."
C-defer-carrier does not land it. Strictly, choosing C means S9 / L-005 drift exposure is the
*standing* posture — but it is standing against a non-existent payload, so the exposure is
vacuous for the trial and becomes live only when the follow-on builds the carrier. That is the
honest framing; it is not "we dodged D6," it is "D6's subject doesn't exist yet."

---

## Sub-question (3) — Fallback contract

**Answer: the fallback IS the whole contract; there is nothing for the skill to branch on.** D5
says the carrier "is an optimization, not the only path" (`intent-management-loop.md:80-81`).
With no carrier, the skill's `load-or-form-intent` runs unconditionally every session
(`cairn-intent/SKILL.md:19`; `workflows/cairn-intent.yaml:16-65`).

- **Detection of non-firing:** trivially "always non-firing." The skill does **not** probe for
  `CAIRN_CARRIER_FIRED`, does not read a carrier-emitted pointer file, does not branch. It reads
  `.claude/handoff.md` + `.claude/skill-runs/<feature>/intent.md` directly and classifies
  new/material-change/resume (`workflows/cairn-intent.yaml:22-27, 43-45`). This is the
  `phase-0.5-journey.md:317-322` "skill does NOT branch on carrier state" design, taken to its
  limit: there is no carrier state to branch on.
- This directly satisfies L-005's warning (`phase-0-constraints.md:148-152`): a prose-specified
  "if carrier doesn't fire, do X" side-effect is fragile under context pressure. C removes the
  conditional entirely — the load-or-form step is the *only* path, so there is no
  protocol-declared branch that can silently fail to execute.

**Honest weakness:** none on correctness; the cost is that *every* session pays the load-or-form
read (two file reads, no API calls per `phase-0.5-journey.md:321`). On a warm Claude Code host
the carrier would have skipped this for resumes. C accepts that per-session cost for the trial.

---

## Sub-question (4) — Realization (bash hook vs SessionStart SKILL)

**Answer: neither. No SessionStart artifact is realized.** The #2 draft's bash-script-vs-SKILL
tension (`phase-0-constraints.md:163-167`) and `delivery-mechanism-friction` D1's literal
"`dist/skills/using-cairn/SKILL.md` registered via `dist/hooks/hooks.json`" wording
(`delivery-mechanism-friction.md:39`) are both deferred, not reconciled. The reconciliation
question is handed to the follow-on slice.

- The existing `plugins/cairn/skills/using-cairn/SKILL.md` stays a **manually-invoked skill
  chooser** (its current role — `using-cairn/SKILL.md:1-23`), NOT a SessionStart-registered
  carrier. `hooks-template.json` gains no SessionStart entry. D6 "no new hooks beyond the three
  shipped" (`intent-management-loop.md:83-85`) is satisfied by construction.
- The carrier-contract stub records the *open* realization question so the follow-on slice
  re-decides it with a working loop in hand — exactly the `delivery-mechanism-friction` R4
  posture ("If shipped SessionStart does not collapse J1 friction … open a follow-up /decision",
  `delivery-mechanism-friction.md:128`), applied *before* shipping rather than after.

**Honest weakness:** This is the bluntest deferral of the five. `delivery-mechanism-friction` D1
is an accepted (provisional) ADR that *names* the SKILL-at-SessionStart realization
(`:37-39`); C declines to build it. C does not supersede D1 — it leaves D1 un-actioned. That is
legitimate only because D1 is provisional and `intent-management-loop` D5 reframes the carrier
as an optimization; but an adjudicator could reasonably read "the issue called `using-cairn`
SessionStart the highest-leverage friction-reduction" (`delivery-mechanism-friction.md:25,29`)
and judge C as declining the slice's primary value.

---

## Sub-question (5) — Distribution scope

**Answer: nothing carrier-shaped ships to consumers; the `cairn-intent` skill + workflow ship
as today.** `scripts/build_dist.py`'s ALLOW_LIST (`:18-33`) is untouched re the carrier — no
`using-cairn` SessionStart registration is added to `hooks/hooks.json`. The carrier stays
cairn-internal-and-nonexistent until the follow-on slice / the D7 retirement ADR.

- This *neutralizes* ADR R1 (`intent-management-loop.md:146`, stale-`.slice-system`) and R3
  (`:148`, carrier doesn't fire on non-Claude-Code hosts) **for the carrier specifically**:
  there is no carrier to go stale in a consumer's `.slice-system`, and no carrier to fail-to-fire
  on a non-CC host. Every consumer host — CC, Codex, external — gets the *same* path: invoke
  `/cairn-intent`, run load-or-form (`phase-0.5-journey.md:149-187` case iv is now the *only*
  case, not the degraded case).
- INV-012 (`ARCHITECTURE.md:87`) release-branch distribution is unaffected; the skill/workflow
  already ride the existing payload curation.

**Honest weakness:** the friction `delivery-mechanism-friction` D1 set out to kill (J1
~20min→~3min cold-start via SessionStart auto-injection, `:78-79`) is **not** delivered to
consumers in this slice. C's bet is that the loop's *correctness* (Trial E) must be proven
before its *ergonomics* (the carrier) are worth shipping — but that bet leaves the measured J1
friction standing for the duration of the trial.

---

## Constraint fit (cite the envelope)

| Constraint | Source | C-defer-carrier |
|---|---|---|
| ≤2k carrier sub-budget | D1 `delivery-mechanism-friction.md:39` | Vacuously met — no payload |
| ≤40k fresh-session | INV-004 `ARCHITECTURE.md:39` | No additive cost incurred |
| No new hooks | D6 `intent-management-loop.md:83`; CLAUDE.md | Met by construction — `hooks-template.json` untouched |
| Standing deps pydantic/typer/pyyaml | CLAUDE.md | Met — only YAML/markdown + one pytest added |
| Honest-minimal (no module w/o caller) | CLAUDE.md | **Strongest fit** — builds no emitter that nothing yet consumes |
| Carrier is optimization, not gate | D5 `intent-management-loop.md:80-81` | Taken to its limit — fallback is the only path |
| Testable fired + fallback (D9 gate) | D9 `intent-management-loop.md:100-104` | **PARTIAL** — fallback tested; fired frozen-as-contract, untested |
| `delivery-mechanism-friction` D1 SKILL-at-SessionStart | `:37-39` | **NOT ACTIONED** (deferred; D1 is provisional) |
| Premise-grounding keystone | `cairn-thin-substrate-direction` D7; `phase-0-constraints.md:118-122` | Fewer premises to ground — no carrier whose assumptions about intent-location need binding |
| Trial-E gating | D7 `intent-management-loop.md:87-93` | Trial E runs on the skill alone, which is what D7's pass-condition actually measures (≥1 increment through `cairn-intent`, felt cost < four-phase) — the carrier is not in D7's pass-condition |

The sharpest fit: **honest-minimal** (CLAUDE.md: "no module without a real caller") and the fact
that **D7's Trial-E pass-condition never mentions the carrier** (`:88-91`) — it measures the
skill loop. C aligns the build to exactly what the trial gates.

---

## Premortem exposure (Phase-1 scenarios)

**NOT vulnerable to (eliminated by deferral):**

- **Scenario 1 — non-firing on non-CC host** (`phase-1-premortem.md:21-29`): no carrier, so
  "non-firing" is the universal, designed state; the fallback that S1 names as the safe path is
  the *only* path. Fully eliminated.
- **Scenario 2 — carrier emits stale intent, poisoning context** (`:34-47`): no emitter, no
  emission, no poisoning. Eliminated.
- **Scenario 3 — carrier payload blows ≤2k / drifts silently** (`:52-66`): no payload.
  Eliminated for the trial window.
- **Scenario 6 — carrier emits pointer to a deleted file** (`:107-118`): no carrier-emitted
  pointer. The deleted-intent.md *audit* concern (`:113-116`) still exists at the skill layer,
  but the carrier-specific misfire is gone.
- **L-012 SessionStart-hook-poisons-a-compliant-tier** (`lessons.md:225-237`): **this is the
  decisive exposure C uniquely avoids.** L-012 is direct in-repo evidence that a SessionStart
  hook emitting stale/contradictory text caused a Phase-4 opus-low integrator to hard-refuse
  four times (`lessons.md:231`). A carrier is precisely a SessionStart context emitter; every
  build-it approach inherits L-012's "the bill comes due at the most compliant consumer"
  failure surface (`:233`). C builds no such emitter and is the only approach with **zero**
  L-012 exposure.

**STILL vulnerable to / does not address:**

- **Scenario 4 — `premise_guard` `.slice-system`-path traversal escape** (`:70-82`, ADR R4
  `intent-management-loop.md:149`): wholly orthogonal to the carrier. `premise_guard.py` runs at
  intent approval regardless of carrier presence; C does nothing about it. (Neither does any
  carrier approach — this is a separate fix.)
- **Scenario 5 — fallback runs on stale `.slice-system`, loads stale-schema intent** (`:86-104`):
  C *increases reliance* on the fallback (it is now the only path), and the fallback's
  load-or-form does **not** version-check or freshness-check what it loads. The stale-load
  blast radius (`:94`) is unchanged or marginally worse — C removes the carrier-misfire vector
  but leans harder on the un-versioned fallback. This is C's sharpest residual exposure.
- **R2 same-family decorrelation 60%** (`intent-management-loop.md:147`): unaffected by carrier
  scope; inherited as EXPOSED either way.

---

## Downstream impact

- **Consumers:** get the `cairn-intent` skill + workflow, no SessionStart auto-injection. Every
  session is `/cairn-intent` → load-or-form, identical across CC/Codex/external hosts. The
  measured J1 cold-start friction (`delivery-mechanism-friction.md:78`) is **not** reduced for
  them this slice. No new blast-radius surface on every consumer session (the ADR R1 concern
  the brief flags is avoided).
- **Codex plugin:** unaffected and arguably *cleaner* — Codex has no SessionStart hook parity
  anyway (`workflows/cairn-intent.yaml:298-300`: "hook registration is not available in
  plugin.json for this slice"). C's skill-only path is the path Codex would take regardless, so
  C makes CC and Codex behave identically rather than CC getting a carrier Codex can't have.
- **Trial E:** runs on the skill alone. This is *consistent* with D7's pass-condition
  (`intent-management-loop.md:88-91`), which measures the loop (counterfactual blocks at
  front-challenge, ≥1 real increment ships, felt-cost < four-phase) and never the carrier. The
  risk: if part of the loop's *felt cost* is the per-session load-or-form that a carrier would
  have amortized, Trial E measures a slightly higher felt cost than the carrier-enabled design
  would — i.e., C could make the loop look marginally *more* expensive than it needs to, biasing
  the felt-cost-vs-four-phase comparison against the loop. That is a real measurement-validity
  concern for D7.
- **D7 retirement ADR:** C cleanly separates concerns — the retirement ADR decides four-phase
  sunset on loop evidence; a *separate* follow-on slice (or the retirement ADR itself) decides
  whether to build the carrier, now informed by real Trial-E session traces showing whether
  cold-start friction actually bit. C trades "ship the carrier on a hypothesis" for "build it on
  evidence," at the cost of one more slice and a slower friction win.

---

## Where this approach is weakest (no advocacy)

1. **It declines `delivery-mechanism-friction` D1's named, accepted deliverable** — the
   SessionStart `using-cairn` carrier the issue called highest-leverage. Defensible only because
   D1 is provisional and D5 reframes the carrier as optional, but an adjudicator can read C as
   not-doing-the-slice's-headline-job.
2. **D9's "fired-detection + fallback" unit-test scope is only half-met** — fired is frozen as a
   contract, not tested, because it is not built.
3. **It leans entirely on the un-versioned fallback** (Scenario 5), removing the carrier-misfire
   vector but doing nothing about stale-`.slice-system` + stale-schema intent loads — and now
   there is no second path.
4. **It can bias Trial E's felt-cost measurement upward** by leaving per-session load-or-form
   un-amortized, which is exactly the variable D7's pass-condition weighs.

C's honest summary: it is the **lowest-risk, lowest-value** option — it eliminates four of six
Phase-1 carrier failure scenarios and the L-012 tier-poisoning surface outright, at the cost of
the friction reduction that motivated the carrier and a partial-coverage reading of the D9 gate.
