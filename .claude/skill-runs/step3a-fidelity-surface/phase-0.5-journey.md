# Phase 0.5 — User-Journey Trace: Step 3a operator gate

/decision arc `step3a-fidelity-surface`. Read-only trace of two end-to-end journeys through the
`cairn-intent` loop, focused on the Step 3a operator sign-off. Source files read live 2026-06-01:
`.claude/skills/cairn-intent/SKILL.md`, `workflows/cairn-intent.yaml`, `templates/intent.md`,
`.claude/agents/intent-challenge.md`, `.claude/agents/intent-review.md`, `checks/premise_guard.py`,
`docs/adr/intent-management-loop.md`.

---

## JOURNEY 1 — CURRENT (as the loop runs today)

Linear walk. Each step: actor, node (workflow id), artifact in→out, and session/state boundary.

### Step 1 — Load or form the intent
- **Actor / node:** main conversation, `load-or-form-intent` (workflow `:16`; `execution.context: current`,
  `human_signoff_after: false`, `:61-65`). SKILL `:49`.
- **Consumes:** current user request, `.claude/handoff.md` pointers, the carrier's SessionStart emission,
  `templates/intent.md`.
- **Produces:** `<workspace>/intent.md` (workspace = `.claude/skill-runs/<feature-id>/`, SKILL `:33`).
  The operator (or the LLM acting under the operator) authors the contract. Per `templates/intent.md`:
  the operator pins **`## Operator Prompt`** VERBATIM (`templates/intent.md:24-31`, derive-exempt,
  the gh#28 cold-read anchor) — this is the **only** operator-authored section; the eight body sections
  (`## What` … `## Explicit Scope-Out`, `:33-67`) plus the machine-readable `## Contract` block (`:87`)
  are LLM-derived. (Under cairn-tdd-feature these are Phase-1 Reader output; under cairn-intent they are
  authored in-conversation but are still derivation, not operator words.)
- **Output envelope (`status: ready-for-challenge`):** `intent_path`, `delta_kind` (new | material-change |
  resume), `contract_summary`, `material_change` (workflow `:49-55`).
- **State boundary:** none yet — same conversation, same context. intent.md is the first durable artifact.

### Step 2 — Decide whether the challenge fires (delta-trigger)
- **Actor:** main conversation (SKILL `:53`). No node — a routing decision.
- **Logic:** fire iff `delta_kind ∈ {new, material-change}` AND a **premise or `must-satisfy` clause** is
  new/edited (D2, ADR `:58-60`). A plain `resume` skips to Step 4 (construction) — **the gate never fires
  on a resume.** This is load-bearing for Journey 2 (below).

### Step 3 — Front-loaded intent-challenge (fresh context)
- **Actor / node:** `intent-challenge` agent (`.claude/agents/intent-challenge.md`), dispatched via the Agent
  tool with `subagent_type: intent-challenge` (SKILL `:55-58`). Workflow node `:67`;
  `execution.executor: fresh_agent`, `context: fresh`, `same_context_fallback: false` (`:112-116`).
- **SESSION/STATE BOUNDARY #1 (decorrelation):** fresh context. The challenger "has seen only the intent and
  the source it cites — not the reasoning that produced it" (agent `:7`). Same model **family** (ADR D4,
  SKILL `:76-78`) — ~60% co-miss accepted EXPOSED.
- **Pre-step gate:** `uv run python checks/premise_guard.py <workspace>/intent.md` runs first (SKILL `:55`):
  exit 0 proceed; exit 1 surfaces the verbatim-grounding diff and blocks (escape `CAIRN_PREMISE_FIX=1`);
  exit 2 = malformed-intent stop.
- **What it attacks:** each `## Premise Grounding` premise's `label:`/claim against live source — the
  slice-#25 semantic gap `premise_guard` cannot catch (agent `:13-19`). **Scope: premise-truth only.**
  `## Premise Grounding` is **OPTIONAL** (`templates/intent.md:69-77`); if absent, the challenger has almost
  nothing to attack. It does NOT attack intent-FIDELITY (does the derived contract match what the operator
  wanted) — that surface does not exist as challenger input.
- **Consumes:** intent path, cited `## Premise Grounding` source files, `docs/adr/intent-management-loop.md`,
  `checks/premise_guard.py`.
- **Produces:** report-only `<workspace>/intent-challenge.md` (write envelope `^…/intent-challenge\.md$`,
  workflow `:84-87`).
- **Output envelope:** `challenge-pass` → `verdict`, `challenged_premises`, `cited_evidence`,
  `blocked_counterfactuals`; `challenge-blocked` → `+ blocking_evidence`, `required_intent_revision`
  (workflow `:98-111`; agent `:29-43`).
- **State boundary back:** the challenger's report file + final JSON line cross back into the main
  conversation. Main parses the JSON (SKILL `:58`).

### Step 3a — Operator sign-off  ← THE GATE THIS DECISION REDESIGNS
- **SKILL `:60`** (the canonical line). Workflow: `intent-challenge` node `human_signoff_after: true`
  (`:115`); the claude_dynamic_workflows + codex_agents executors each model this as a **separate run**
  `cairn-intent-challenge` whose `after:` is "Operator reviews challenge output before construction starts"
  (`:281-292`, `:309-320`). The split exists because "Claude dynamic workflows cannot take mid-run user
  input, so … approval boundaries are separate workflow runs" (`:272-275`).
- **What the operator SEES:** "the committed `intent.md` AND the challenge verdict" surfaced as one object
  (SKILL `:60`). The full ~250–400-line LLM-authored contract + the challenge report, presented **all at
  once, all-or-nothing**. No decision-weight enumeration, no per-clause severity, no fidelity prompt. The
  verbatim `## Operator Prompt` is *inside* intent.md but is not separately foregrounded or diffed against
  anything.
- **What the operator TYPES:** an **explicit** approval ("Approval here is intent approval, not a glance",
  SKILL `:60`) — free-form confirmation in the conversation. There is no structured ballot, no
  per-criterion acknowledgment, no recorded approval artifact. The approval is conversational state only;
  nothing is written to disk.
- **THE RUBBER-STAMP SURFACE (the problem, brief `:9-13`):** VOLUME (whole contract) + LATENCY (the
  fresh-context round-trip in Step 3 made the operator lose the thread) → the operator approves to keep
  moving. The operator's *irreducible job* — intent-FIDELITY + VALUE/floor judgment — is never elicited as
  a discrete surface; it is buried in "read all 400 lines and say yes."

### Step 4 — Construct (fluid, test-first)
- **Actor / node:** main conversation, `construct` (workflow `:118`; `context: current`,
  `human_signoff_after: false`, `:161-165`). SKILL `:62`.
- **Consumes:** approved intent, `intent-challenge` pass output, conversation, repo files within the write
  envelope. `role_guard` enforces the `execution-scope` envelope ambiently (D6).
- **In-loop re-trigger:** if a **premise or `must-satisfy` clause** changes materially mid-construction,
  return to Step 3 and re-challenge (SKILL `:62`, D2). This is the **amendment path** — and it routes back
  through Step 3 → Step 3a, so a mid-construction edit triggers a fresh challenge + a fresh operator
  sign-off on the changed contract.
- **Produces (`status: ready-for-close-review`):** `intent_path`, `diff_summary`, `test_output`,
  `evidence_paths` (workflow `:148-154`).

### Step 5 — Fresh close-review
- **Actor / node:** `intent-review` agent (`.claude/agents/intent-review.md`), `subagent_type: intent-review`
  (SKILL `:65-68`). Workflow `close-review` node `:167`; `fresh_agent`, `context: fresh`,
  `same_context_fallback: false` (`:213-217`).
- **SESSION/STATE BOUNDARY #2 (decorrelation):** fresh context; "seen only the intent, the diff, and the
  verification output — not the conversation that produced them" (agent `:7`).
- **What it checks:** `contract-clause-check` (per-clause pass/fail vs diff), `evidence-adequacy-check`,
  `scope-check` (changed files ⊆ `execution-scope`) + the depth-vs-diff-size smell test (agent `:15-22`).
  **It checks diff-against-CONTRACT, not contract-against-operator-intent** — a faithful diff of a leaked /
  drifted clause passes clean (brief `:19`). It never sees the `## Operator Prompt` as a fidelity baseline.
- **Produces:** report-only `<workspace>/close-review.md`. Envelope `close-review-pass` →
  `clause_results`, `evidence_summary`, `residual_risk`; `close-review-blocked` → `findings`,
  `missing_evidence`, `required_rework` (workflow `:199-212`).

### Step 5a — Operator sign-off (close)
- **SKILL `:70`**; `close-review` node `human_signoff_after: true` (`:216`); executor run
  `cairn-intent-close-review` (`:287-292`, `:315-320`). Operator sees the close-review verdict; closes only
  on `close-review-pass` OR explicit acceptance of a documented `residual_risk`. Free-form approval, no
  structured ballot.

### Step 6 — Close
- **Actor / node:** main conversation, `close` (`:219`; `context: current`, `:264-268`). SKILL `:72`.
- **Produces:** `<workspace>/close.md`, appends a pointer to `.claude/handoff.md`, records a Trial-E
  observation to `docs/dogfood-log.md`. Runs final verification, confirms GREEN. Envelope `closed` →
  `intent_path`, `verification`, `handoff_entry`, `trial_e_observation` (`:251-257`).

**Current-journey summary of operator touch-points:** two free-form sign-offs (Step 3a `:60`, Step 5a `:70`),
both all-or-nothing over LLM-derived artifacts, neither eliciting the operator's fidelity/floor criteria as a
discrete surface, neither producing a durable approval artifact. The operator's verbatim words live only in
`## Operator Prompt`, which **no challenger, reviewer, or gate consumes** — it is a cold-read anchor with zero
downstream wiring.

---

## JOURNEY 2 — PREDICT-BEFORE-SEE (Approach A)

Goal: the operator pins fidelity + floor criteria at **peak context** — when/right after authoring
`## Operator Prompt`, BEFORE the LLM-derived `## Contract` is revealed — those criteria are **frozen**, and
the gate checks the committed contract against the **frozen operator criteria** (not against a fresh read of
all 400 lines). This sidesteps the ~60% co-miss because the **human supplies the floor** (brief `:13`, `:31`).

Walked end-to-end. **Bold = mechanism that does not exist yet**; each names the file that would carry it.

### Step 1′ — Author intent + PIN CRITERIA at peak context
- The operator authors `## Operator Prompt` verbatim as today (`templates/intent.md:24`). **NEW: immediately
  after — before any LLM derivation of `## Contract` is shown — the operator pins their fidelity + floor
  criteria.** "Peak context" = the moment the operator's own framing is freshest, before the 400-line
  contract has displaced it.
  - **MISSING MECHANISM #1 — the pinned-criteria artifact + its schema.** A new structured section the
    operator authors: e.g. `## Operator Floor` (working name) carrying (a) **fidelity criteria** — "this is
    faithful iff it does X / preserves Y / targets Z" in the operator's words, and (b) **floor / must-fail
    criteria** — the severity declaration L-028 mandates ("declare the floor", brief `:16`). Per L-028 the
    *severity field is the challenger's input, NEVER user review* — so this is the operator declaring the
    floor *as a prediction*, distinct from re-reading severity off a finished contract.
    **Carrier file:** `templates/intent.md` (new section + its derive-EXEMPT authoring note, parallel to the
    `## Operator Prompt` exemption at `:19-22`).
  - **Ordering constraint:** this MUST be authored before `## Contract` is derived/revealed. Today
    `load-or-form-intent` produces the whole intent.md in one pass (SKILL `:49`); predict-before-see
    **splits authoring into two ordered sub-steps** within Step 1 — operator-pin first, LLM-derive-contract
    second. **Carrier file:** `.claude/skills/cairn-intent/SKILL.md` Step 1 (`:49`) + the
    `load-or-form-intent` node prompt (`workflows/cairn-intent.yaml:22-27`).

### Freeze boundary — make the pinned criteria IMMUTABLE
- **MISSING MECHANISM #2 — the freeze/immutability enforcement.** The pinned criteria must be frozen the
  moment the contract is revealed, so the operator cannot retro-edit their "prediction" to match what the LLM
  produced (that would re-collapse predict-before-see into post-hoc rubber-stamp). The natural precedent is
  **`premise_guard.py`**: it already does "operator pins an immutable verbatim thing, a check enforces it,
  fail-open on absence / fail-closed on malformation, env-var escape" (`checks/premise_guard.py:11-13`,
  exit-code contract `:9-13`). A floor-freeze guard would be a sibling.
  - Freeze could be enforced by (a) a snapshot mechanism — hash/copy the criteria block at reveal time and
    block edits that diverge (cf. `snapshot-sha` frontmatter, `templates/intent.md:3`), or (b) an
    append-only discipline on the section.
  - **Carrier file:** a new `checks/floor_guard.py` (sibling to `premise_guard.py` / `atomicity_guard.py`),
    invoked from SKILL Step 1.5/3 the way `premise_guard` is invoked at SKILL `:55`. Plus its registration
    in `workflows/cairn-intent.yaml` `guards:` list (`:9-13`) and the executor guard wiring.

### Step 3″ — Challenger consumes the frozen criteria
- **MISSING MECHANISM #3 — the challenger reads + attacks against the frozen criteria.** Today
  `intent-challenge` is scoped to `## Premise Grounding` premise-truth only (agent `:13-19`); it does not
  read `## Operator Prompt` and there is no fidelity surface in its inputs (`:9`). Approach A requires the
  challenger to take the **frozen operator criteria** as a first-class input and attack the **committed
  `## Contract` against those criteria**: does the derived contract realize each fidelity criterion? does it
  honor each declared floor item, or has scope-internal erosion dropped a must-fail (the L-028 floor hole,
  brief `:16`)? Severity-as-challenger-input is exactly L-028's prescription.
  - **Carrier files:** `.claude/agents/intent-challenge.md` (add the frozen-criteria input to "Inputs" `:9`
    and a new "fidelity-against-frozen-floor" check alongside the slice-#25 obligation `:13-19`; extend the
    verdict evidence `:23-27` and envelopes `:31-41` with a fidelity/floor result). `workflows/cairn-intent.yaml`
    `intent-challenge` node: add the criteria artifact to `allowed_inputs` (`:79-83`), add an evidence id
    (`:88-97`), extend `pass_output`/`fail_output` (`:98-111`). Also the **Codex plugin's** `cairn-intent`
    skill which renders Codex dispatch briefs (named at SKILL `:8`) — both surfaces must agree on node ids /
    verdict statuses / evidence ids (SKILL `:8`), so the Codex skill file needs the parallel edit.

### Step 3a″ — Gate surface assembled FROM the frozen criteria
- **MISSING MECHANISM #4 — the derived gate surface.** Today Step 3a surfaces the *whole* intent.md + verdict
  (SKILL `:60`). Approach A's whole point: the operator does **not** re-read 400 lines. The gate surface is
  **assembled from the frozen criteria** — for each pinned fidelity/floor criterion, show {the criterion (the
  operator's own words) → how the committed contract realizes it → the challenger's pass/attack on that
  pairing}. The operator's job collapses to confirming each *criterion* is met, not auditing the artifact.
  This is the "surface = job" derivation (brief `:7`, `:13`).
  - This needs a **deterministic criterion↔clause traceability** rendering — L-028's "mechanize the
    structural edge": every floor criterion must map to a realizing contract clause (an unrealized criterion
    = dropped operator intent; an orphan clause carrying weight no criterion covers = smuggled scope, brief
    `:16`). **Caveat from L-028 (brief `:16`):** "Never narrate the structural check as if it caught
    semantics" — the structural map is necessary but the fidelity judgment stays the operator's + the
    challenger's.
  - **Carrier files:** `.claude/skills/cairn-intent/SKILL.md` Step 3a (`:60`) — rewrite what the operator
    sees + what they type (per-criterion acknowledgment, not free-form glance). The traceability map is
    deterministic → a new helper (e.g. `scripts/lib/` + a `checks/` invocation, function-based per the new-code
    rule) that pairs criteria to clauses. The criterion-rendering shape may also belong in
    `templates/intent.md`.

### Amendment / re-challenge interaction
- **MISSING MECHANISM #5 — how a mid-construction amendment re-interacts with frozen criteria.** Today a
  material premise/`must-satisfy` edit during Step 4 routes back to Step 3 → Step 3a (SKILL `:62`, D2
  delta-trigger). Under Approach A, the **frozen criteria** must travel with that re-challenge: a mid-flight
  contract amendment is re-checked against the *original* frozen criteria (did the amendment break a pinned
  floor item?). The hard question: **can the operator ever amend the frozen criteria themselves?** If never,
  a genuinely-changed intent is stuck. If freely, the freeze is meaningless. Likely resolution: amending the
  frozen criteria is itself a **delta-trigger that re-opens a full predict-before-see cycle** (new pin → new
  freeze → new challenge → new sign-off), recorded as a distinct, append-only revision — never an in-place
  edit of the original prediction.
  - **Carrier files:** `.claude/skills/cairn-intent/SKILL.md` Step 4 (`:62`, the delta-trigger prose) +
    Step 2 (`:53`, the fire-decision logic must add "criteria amended" as a trigger). The append-only
    revision discipline → `checks/floor_guard.py` (mechanism #2) + possibly `templates/intent.md`.

### Mismatch handling
- **MISSING MECHANISM #6 — what happens on a criterion↔contract mismatch.** Today the only blocking verdict
  is `challenge-blocked` on premise-truth (agent `:39-41`). Approach A introduces a new failure class: the
  committed contract **fails to realize a frozen fidelity criterion** or **violates a declared floor item**.
  This needs its own verdict envelope + downstream routing: does it block at the challenger (a new
  `challenge-blocked` reason code), or does it surface as a flagged item the operator must explicitly
  resolve at Step 3a (revise contract, or — append-only — revise the criteria via mechanism #5)? L-028 says
  an orphan clause = smuggled scope and an unrealized criterion = dropped behavior, so a structural mismatch
  is a hard finding, not a soft warning.
  - **Carrier files:** `.claude/agents/intent-challenge.md` (new blocked reason + envelope field, `:39-41`),
    `workflows/cairn-intent.yaml` `intent-challenge` `fail_output` (`:105-111`), and SKILL Step 3a/Step 3
    routing (`:58`, `:60`).

---

## Boundaries where Journey 2 breaks an existing invariant / contract / protocol

1. **`load-or-form-intent` single-pass authoring → split into ordered sub-steps.** The node today emits the
   whole intent.md at once (`workflows/cairn-intent.yaml:22-27`, SKILL `:49`). Predict-before-see **requires
   the operator-criteria pin to precede contract derivation** — an ordering constraint the current node/step
   does not encode. This is a contract change to the `load-or-form-intent` node, not just additive surface.

2. **The delta-trigger invariant (D2) gains a new trigger.** "Approval is delta-triggered — re-fires only on
   a premise or `must-satisfy` clause edit" (ADR `:58-60`, SKILL `:29`, `:53`). Adding "criteria amended" as
   a trigger (mechanism #5) **edits the D2 invariant's trigger set** — and D2 is the load-bearing
   anti-ceremony decision from the pre-mortem ("approve every session" was found *fatal*, ADR `:38-41`).
   Touching it risks reintroducing per-session ceremony. Likely needs a superseding/extending ADR over
   `intent-management-loop` D2.

3. **Resume path bypasses the gate entirely.** A plain `resume` skips Step 3 → Step 3a (SKILL `:29`, `:53`).
   If a resume can pick up an intent whose criteria were frozen in a prior session, **the frozen criteria
   cross a session boundary unre-confirmed** — predict-before-see's "peak context" guarantee does not survive
   a resume. Needs an explicit decision: re-surface frozen criteria on resume, or accept the gap.

4. **Append-once / amendment protocol vs. an editable prediction.** The freeze (mechanism #2) imposes
   append-only/immutable semantics on a *new* artifact. This is consistent with the repo's append-only ethos
   (ADRs append-only; `premise_guard` immutable quotes) but is a **new protocol** the loop does not have for
   intent-internal sections — `## Operator Prompt` is verbatim-pinned but not *enforced* immutable by any
   guard. Journey 2 is the first time an intent.md section would be machine-frozen mid-life.

5. **Two-surface agreement (Claude Code skill ↔ Codex plugin skill).** SKILL `:8` mandates both surfaces
   "agree on node ids, verdict statuses, and evidence ids." Every envelope/evidence/node change in
   mechanisms #3 and #6 **must be mirrored in the Codex plugin's `cairn-intent` skill** or the two diverge —
   a parity contract Journey 2 stresses at multiple points.

6. **Trial-E acceptance gate semantics.** The loop is provisional and gated on Trial E (ADR `:88-93`,
   D7/D9), whose pass condition is defined around the slice-#25 counterfactual blocking at the
   front-challenge. Adding a fidelity/floor gate **changes what "the front-challenge" is** mid-trial — the
   decision arc must reconcile this with the in-flight Trial-E acceptance contract (and the deferral the
   SUPERSESSION question targets, brief `:6`, `:17`).

7. **INV-004 context budget.** A per-criterion assembled surface + a new template section + challenger inputs
   add session/dispatch context. INV-004 (`docs/ARCHITECTURE.md:39`, brief `:26`) caps session-start /
   command context; the assembled gate surface should be *smaller* than today's whole-contract dump (that's
   the point), but the new authoring section + guard wiring must stay within budget — verify in Phase 0/2.

---

## Precedent assets that lower Journey-2 cost (cut-before-adding)

- **`premise_guard.py`** is a near-complete template for the freeze guard (#2): operator pins an immutable
  thing, a function-based check diffs it, exit-code contract, fail-open-absence / fail-closed-malformation,
  env-var escape (`checks/premise_guard.py:9-13`). A `floor_guard.py` sibling reuses the whole shape.
- **`## Operator Prompt`** (`templates/intent.md:24`) already establishes the "operator pins verbatim,
  derive-exempt, peak-context anchor" pattern — the criteria pin (#1) is the same move, one section over, and
  finally gives `## Operator Prompt` a downstream consumer it currently lacks.
- **L-028 + D3 completeness-floor + atomicity tags** already supply the floor vocabulary; the criteria pin
  formalizes the operator side of a mechanism the repo already reasoned about (brief `:16-17`).
