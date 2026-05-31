# Decision context — intent-contract cost model (consolidated inputs)

Companion to `framing.md` (the problem). This consolidates the design space and the adversarial
stress-test of the leading candidate so phase agents have short prompts. Read `framing.md` first.

## Design space (9 options; full detail in workflow output `we6hctn0m`)

Primary axis = **who authors the formalized `must-satisfy`**, fully-human → fully-assistant;
crossed with orthogonal moves on **whether/when** a contract exists and **gate force**.

1. **Operator-authors-everything** (status quo / Trial-D-as-designed) — max intent-fidelity, the measured pain.
2. **Assistant-drafts / operator-approves** — lowest cost, reopens rubber-stamping (the named tension).
3. **Intent / formalization split** — human owns the *what*, assistant formalizes; review for fidelity.
4. **Contract-required-only-by-intent-weight** (graduated mandate) — light intents skip the formal contract.
5. **Atomicity-as-advisory-only** — gate never blocks, prints findings; keeps authorship human.
6. **Tooling-to-cut-authoring-cost** (snippets / clause-by-clause LLM assist) — authorship stays human.
7. **Lazy / just-in-time authoring** — prose up front, formalize at close / on delta-trigger.
8. **Adversarial co-authoring** — assistant drafts, fresh-context agent attacks *fidelity*.
9. **Operator-authors-must-satisfy / assistant-fills-the-other-five-lists** — split by clause-list.

## Leading candidate: the "promise" model (band-dependent)

- The user approves ONE plain-language **promise** (not a contract/card/taxonomy). Larger work:
  promise + `Includes:` / `Excludes:`. **User owns the promise** (is this the work I want?);
  **agent owns the proof** (EARS, tags, tests, evidence, traceability).
- Flow: agent proposes promise → user OKs/edits → agent formalizes internally → at close, agent
  reports proof against the *same* promise. Approval and verification share one object.
- Stated invariant: "Nothing formal may exceed the promise. Nothing important may disappear from the proof."

## Adversarial stress of the promise model (workflow output `wsi6y2nr3`)

- **Structural flaw — the invariant bounds the CEILING, never the FLOOR.** "Nothing exceeds the
  promise" is an upper bound on *scope*; it is silent on severity/polarity/must-fail *within* scope.
  **Counterexample (real heavy intent):** m5 A10 wants a validator that *fails loud and declares the
  install unsafe*. Encoded as "the validator shall exercise enforcement and **report a result**" it is
  grounded ✓, atomic ✓, consistent-with-promise ✓ — then implemented as log-and-exit-0. Green on every
  gate; D5's whole reason silently evaporates. **This is slice-#25 (the wrong-premise miss that birthed
  premise-grounding) relocated to the promise→clause gap.**
- **Mechanizable, deterministic, INV-clean** — the invariant's two *cardinality* halves reduce to
  set-membership over an explicit edge: a `## Promise` block with `pid:`-keyed lines (agent adds ids,
  user approves prose) + a per-clause `traces-to:` edge. **Orphan clause = smuggled scope; unrealized
  pid = dropped behavior.** Ship as `checks/traceability_guard.py` + `scripts/lib/traceability.py`,
  sibling of atomicity_guard, at the existing Phase-1→2 gate (no new phase, no session-start token).
  **Plus a mandatory per-clause `severity`/floor field** → turns *silent* floor-erosion into *declared*
  floor-erosion (a visible `severity: advisory` next to A10's clause that a reviewer can object to).
- **Not mechanizable — needs a fresh-context fidelity attacker.** "Is each edge honest / is a pid
  under-realized in substance" is semantic → a front-loaded promise-expansion challenge (widen the
  existing intent-management-loop D2(a) front-challenge slot; verdicts: SCOPE-EXCEEDED /
  PROMISE-UNDERREALIZED / EDGE-MISDIRECTED). Raises the floor; ~60% same-family co-miss residual remains
  (same honest limit as premise-grounding). Order: premise_guard → traceability_guard → fidelity challenge → Phase-2.
- **Stays human by design (correctly):** *is the promise the work you want.* No mechanism can or should check this.
- **Band-dependence (the convergence — all four stress angles land here):**
  - LIGHT (≤10 trivially-atomic behaviors): **promise-only; cut the formal/atomicity layer** (it catches structurally nothing).
  - MEDIUM (10–30, some tags, light open questions): promise + a visible abbreviated contract at approval.
  - HEAVY (30+ criteria, enforcement-positive tests, open-Q gates): promise + **full formal contract / floor visible at approval** + traceability hook + front-loaded fidelity challenge; **keep atomicity** — it uniquely catches *obligation-set collapse* (A4 "no path under any of 10 excluded prefixes" tested 3/10, suite still green; tests and grounding can't catch this).

## Hard constraints (full table in `framing.md`)

INV-003 four-phase lock (gate stays at Phase-1→2; no new phase transitions); INV-004 token budget
(no new session-start cost; reuse the front-challenge dispatch slot); premise_guard + atomicity_guard
**reused unchanged**; deps **pydantic/typer/pyyaml only**; hooks **provider-agnostic** (semantic checks
must be a subagent, never a hook); **ADRs append-only** (lands as a new ADR); coexistence with
`cairn-tdd-feature` (no retirement here); single-operator-per-branch.

## Already decided — do NOT relitigate (full list in `framing.md`)

EARS notation; the atomicity rule itself; the four exception tags; premise-grounding as identity
keystone; front-challenge & close-review mechanisms; same-family decorrelation (cross-family EXPOSED);
coexistence + Trial-E-gated retirement; no new deps/infra; single-operator-per-branch.

## Open hinge (still unresolved)

The disentangle — was the m2 pain the EARS *formalization* or the *harness* — is now largely answered
by the band analysis: formalization was the cost, paid in the band where it has no payoff. But the
contract grammar's *value* (Trial-D #1/#2/#3) remains **unmeasured** at any size.
