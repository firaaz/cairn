# Problem — the intent-contract cost model (when is a formal contract warranted, and who formalizes it)

status: problem-defined, `/decision`-ready (not yet decided)
date: 2026-05-31
origin: Trial-D m2 friction finding (`.claude/skill-runs/trial-d-measurement/README.md`)
framed-by: workflow `trial-d-problem-definition` (constraints / design-space / prior-decisions / adversarial framing-critic)

## One-sentence problem

Decide the intent contract's **cost model**: (a) for which class of intent a formal
EARS/atomicity `## Contract` is required at all vs. a thin prose intent, and (b) within the
band where it is required, how authoring splits between operator (the *intent* — what it should
do) and assistant (the *formalization* — EARS shape + atomicity + tags) — such that the
anti-rubber-stamp / intent-fidelity guard is preserved exactly where it carries weight.

## Trigger

Trial-D's m2 (LIGHT) measurement halted: the sole operator, first-ever exposure, found
hand-authoring the EARS `must-satisfy` contract painful/ritualistic even on the lightest,
trivially-atomic intent (8 behaviors; the gate flagged nothing). All three Trial-D pass
metrics (#1 authoring delta ≤30%, #2 rubber-stamp reduction ≥2/3, #3 false-positive <10%)
remain **unmeasured**. The operator elected to reconsider the authoring model.

## Why "who authors" is not (quite) the frame — the reframe

The operator's instinct was redistribution: assistant drafts, operator reviews. The adversarial
pass found a **prior** question that dissolves the dilemma on light intents:

- m2 was chosen *because* it is "all atomic by design, no payoff to see." The no-payoff was
  **structurally guaranteed** by the selection criterion. So "painful with nothing caught" is the
  expected reading of a **depth-selection error**, not evidence about authorship.
- intent-management-loop **D3** already commits to **graduated depth** — small work carries a
  thin one-line intent. By that rule, m2 arguably should never have carried 8 EARS clauses.
- Defining around "who authors" commits the project to building an **assistant-drafting pathway
  whose dominant effect on a light intent is to *manufacture* contract volume the operator must
  now review** — inflating the exact rubber-stamp surface metric #2 and the D7 identity exist to
  shrink. (This is the recorded reframing risk.)

So the problem is defined at two layers: **(1) requirement-by-size-band** (the prior question),
with **(2) the operator/assistant authoring split** as the local answer *inside* the band where
formalization has payoff (heavy / source-citing intents), not as the problem statement.

## Core tension (the single load-bearing tradeoff)

**Authoring cost vs. intent-fidelity.** The existing guards check *grounding*, not *fidelity*:
`premise_guard` diffs a clause's verbatim quote against live source; the front-challenge attacks
premises against code. **Neither verifies the intent is what the operator actually wanted.** A
flawlessly-grounded assistant-drafted intent can still be the wrong intent — the precise hole
metric #2 ("rubber-stamp reduction") and D7 ("keep AI-authored intent bound to verifiable
evidence") exist to close. Any move toward assistant-drafting must either preserve a human origin
for *what*, or build a new mechanical *intent-fidelity* check the current stack lacks.

## Hard constraints any solution must respect

| Constraint | Source | Binds the solution to… |
|---|---|---|
| INV-003 four-phase lock | phase-lock-and-role-declaration; thin-substrate D8 | keep the gate at the Phase-1→2 boundary; no new phase transitions |
| INV-004 token budget | intent-management-loop D4 | no costly new subagent/dispatch pathway without a budget justification |
| Premise-grounding keystone | thin-substrate D2.5/D7; `premise_guard.py` | grounding check stays at the approval gate; don't weaken evidence-binding |
| Atomicity single-source | `scripts/lib/atomicity.py` (shared by gate + validator) | one evaluator; the 4 tags; the shy heuristic is fixed (changing it = its own `/decision`) |
| ADR append-only | `reversibility-guard.sh` | any model change lands as a **new** ADR, not a body edit |
| Deps + hook portability | CLAUDE.md | pydantic/typer/pyyaml only; AI-driven analysis can't live in a provider-agnostic hook (must be a skill step / subagent) |
| Coexistence, not retirement | intent-management-loop D1/D7 | a change can ship in `cairn-intent`; four-phase stays until a separate firm supersession |
| Operator envelope / single-operator-per-branch | `role_guard.py`; D8 | new write paths must be envelope-declared; multi-operator is out of scope |

## Already decided — do NOT relitigate

EARS as the notation; the atomicity rule itself; the four exception tags; premise-grounding as
the identity keystone; the front-challenge & close-review mechanisms; same-family decorrelation
(cross-family EXPOSED); coexistence + Trial-E-gated retirement; no new deps/infra;
single-operator-per-branch. (Per prior `/decision` arc `thin-cairn-intent-management` + the two
ADRs.)

## The decision agenda (what is newly open)

1. **Requirement-by-size-band.** For which intents is a formal `## Contract` required vs. a thin
   prose intent? What is the right artifact at each band, and what threshold (and is any
   threshold non-gameable)?
2. **Who formalizes, in the band where a contract is required.** Operator-authors (status quo) /
   assistant-drafts-operator-approves / **intent–formalization split** / clause-by-clause
   assist-tooling / adversarial co-authoring (assistant drafts + fresh-context *fidelity*
   attacker).
3. **Does assistant-drafted formalization reopen rubber-stamping** — and if so, can a **mechanical
   intent-fidelity check** (something premise_guard + the grounding front-challenge do not
   provide) close it, or does the human origin of *what* have to stay?

## Design space (the axis, not the choice)

Primary axis — **who authors the formalized `must-satisfy`** — from fully-human → intent/
formalization split → clause-list split → clause-by-clause assist → adversarial co-authoring →
fully-assistant. Crossed with two orthogonal moves on **whether/when** a contract exists
(required-by-weight; lazy/just-in-time formalization at close-review) and one on **gate force**
(atomicity advisory-only). Every option trades on the one axis above (cost vs. fidelity). Full
nine-option enumeration with optimizes-for / sacrifices: workflow output `we6hctn0m`.

## Key unknowns (resolve early — they re-weight the space)

- **The disentangle (highest-leverage):** was the pain the **EARS formalization itself**, or the
  **measurement harness** (scratch file / two redos / mid-stream corrections)? If harness, "who
  authors" is a category error and the fix is a clean steady-state authoring loop. If
  formalization, the intent/formalization split is the targeted fix. (Probe A predicted
  "ritualistic on light intents" independently of any harness, so method friction is *at least
  partly* real — but n=1 first-exposure cannot separate the two.)
- **Unproven value:** #1/#2/#3 are unmeasured; we have **no** evidence the EARS+atomicity contract
  catches anything a thin prose intent wouldn't — at any size. A redistribution decision must not
  be ratified on n=1 light-intent first-exposure data with three live confounders.

## Success criteria (what a good resolution achieves)

1. Removes the felt **ceremony-without-payoff** on light intents.
2. **Preserves intent-fidelity** / does not reopen rubber-stamping in the band where it matters
   (heavy / source-citing intents).
3. Respects every hard constraint above (no INV-003/004 breach, no new deps, append-only ADR,
   coexistence).
4. Makes the eventual **Trial-E gate rest on validly-obtained evidence**, not the voided m2 run.

## Scope

**In:** the contract requirement-by-size rule; the operator/assistant authoring split; an
intent-fidelity check if assistant-drafting is adopted; the authoring harness.
**Out:** the notation (EARS stays); the atomicity rule and heuristic; four-phase retirement;
multi-operator reconciliation; richer formalisms (TLA+/Alloy); per-turn goal re-injection.

## Disposition

Routes to `/decision` (a focused new arc; adjacent to — and constraining — the open
`thin-cairn-intent-management` arc, whose 7 questions do not include this). Trial E stays gated.
Recommended first decision-step: settle the **disentangle** (EARS vs. harness) and the
**size-band** question before the authoring-split, because both can dissolve or re-shape it.
