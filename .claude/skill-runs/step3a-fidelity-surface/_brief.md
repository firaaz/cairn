# Decision brief — Step 3a operator gate: defeat rubber-stamping

/ decision arc, opened 2026-06-01. Shared context; phase agents read this so their prompts stay short.

## The decision (two coupled questions)
1. **SUPERSESSION** — Should we act NOW, given this bundle was deliberately deferred?
2. **DESIGN** — If we act, what mechanism redesigns the `cairn-intent` **Step 3a** operator approval so the review *surface* is derived from the operator's *irreducible job*?

## The problem
Operators rubber-stamp the Step 3a human approval: the gate surfaces the full ~250–400-line LLM-authored `intent.md` + the challenge verdict as one all-or-nothing approval, no decision-weight enumeration (`.claude/skills/cairn-intent/SKILL.md:60`). Driver (operator's own words): information **VOLUME** + **LATENCY** — the fresh-context challenge round-trip makes the operator lose the thread, so they approve to keep moving.

## The operator's chosen frame (steelman this)
**Surface = JOB = TIMING.** The operator's irreducible contribution is intent-**FIDELITY** ("does this match what I actually wanted") + **VALUE/scope** judgment ("is this deferral/priority right") — NOT correctness (the human can't validate it; an AI wrote the code — `docs/adr/cliff-failure-mode-and-v1-defenses.md:48`). Derive the surface from that job. Because of the ~60% co-miss (below), the only decorrelation-preserving compression is to elicit the operator's fidelity/floor criteria **before** revealing the committed contract (predict-before-see): the operator pins the floor at peak context; challenger + a structural check enforce it.

## Load-bearing evidence (verified 2026-06-01)
- **L-028 (`docs/lessons.md:557`, watching-mark 1/3) — THE governing lesson.** A compressed human-approval object bounds the *ceiling* (scope), never the *floor* (severity/must-fail) — declare the floor or intent silently erodes within scope. Corrective: (1) **mechanize the structural edge** — deterministic anchor↔clause traceability (orphan clause = smuggled scope; unrealized anchor line = dropped behavior); (2) **declare the floor** — mandatory per-clause severity field, as the **challenger's input, NEVER user review**; (3) **attack semantics** with a fresh-context fidelity challenger; (4) **record the honest limit** — same-family review **~60% co-misses**: raises the floor, does not close the hole. "Never narrate the structural check as if it caught semantics." → Any compressed ballot/surface MUST declare the floor; severity must NOT be re-loaded onto the user.
- **The deferral (`docs/adr/intent-contract-cost-model.md`, 2026-05-31).** D3 (`:49-52`) defers the whole heavy-band bundle — "promise↔clause traceability, agent-declared/challenger-attacked severity, and the front-loaded fidelity challenge" — as a measured follow-on **gated on Trial E**. D4 (`:56`): introduces NONE of it now. `:72`: "no *new automated* intent-fidelity backstop until D3 lands … floor concern … explicitly unaddressed by new machinery until then." Floor mechanisms recorded as **deferred design constraints, NOT accepted for implementation**. → Acting now = superseding this deferral on n=1 Trial-E data ("commit only what evidence supports").
- **~60% co-miss (`intent-contract-cost-model.md:97`).** "A fresh-context fidelity challenger raises the floor but ~60% co-misses (intent-management-loop/D4, EXPOSED); cross-family escalation is the named fallback." → A single same-family fresh-context agent cannot be the sole floor/fidelity guard.
- **Back-gate is charter-blind to fidelity (`.claude/agents/intent-review.md:15-22`).** Checks diff-against-CONTRACT (contract-clause-check / evidence-adequacy / scope-check + depth-vs-diff-size smell test). A faithful diff of a leaked clause passes clean — cannot recover an intent-fidelity leap.
- **Front-challenger is scoped to premise-truth, not fidelity (`.claude/agents/intent-challenge.md:13-19`).** Attacks `## Premise Grounding` claims vs cited source ("grounded quote, false label", slice-#25). That section is OPTIONAL. A fidelity leap that isn't a source-citing premise is out of scope.
- **>15min metric (`docs/adr/slice-intent-contract.md:20`).** Review >15min/slice declared a failure ("contract too dense to scan; defeats rubber-stamping defeat"). ATTACK: a failure-ceiling possibly mislabeled as a success target — fast approval is observationally identical to disengagement. Prefer correlating against post-close defect-escape.
- **gh#27** already names "parallelism produces rubber-stamping … operator has lost framing"; proposes a six-field decision object (recommendation/reversibility/blocking).

## Constraints (verify in Phase 0)
- **INV-003** (`docs/ARCHITECTURE.md:30`) locks the FOUR-PHASE `cairn-tdd-feature` topology. **Open question:** does it bind the *cairn-intent* loop (a different skill) and its Step 3a? Find cairn-intent's governing structure (likely `docs/adr/intent-management-loop.md`); determine whether a Step-3a change needs a superseding ADR.
- **INV-004** (`docs/ARCHITECTURE.md:39`) is the CONTEXT-BUDGET invariant (≤40k session-start; slash-command progressive disclosure, lite ≤500 tokens + `.full.md`). Relevant only if the redesign adds session-start/command context.
- Ethos: "cut before adding" — prefer widening the existing front-challenge slot over new phases/dispatch/machinery. New code = Python, function-based, pydantic/typer/pyyaml only, no decorators/metaprogramming.
- ADRs are append-only; this likely lands as a superseding/related ADR (supersedes or extends `intent-contract-cost-model` D3/D4).

## Approaches to enumerate (Phase 2 — ≥3 viable)
- **A. Predict-before-see (operator-elicited floor/criteria).** Operator pins fidelity + floor criteria at peak context BEFORE the contract is revealed; challenger + structural traceability enforce contract-against-operator's-frozen-criteria. Sidesteps ~60% co-miss (human supplies the floor). Combines L-028 declare-floor + mechanize-edge with the timing move.
- **B. Cross-family fidelity challenger + declared-floor surface.** The repo's named fallback for ~60% co-miss: a different-model-family challenger assembles/attacks a severity-tagged surface (severity = challenger's input per L-028). Keeps agent-assembled compression, decorrelates by family. Adds cross-family machinery.
- **C. Forcing-function on the existing monolithic gate (minimal / cut-before-adding).** Don't compress at all (avoids co-miss). Add an engagement-forcing function: per-clause active recall ("what would make this wrong?"), planted-decoy clause the operator must reject to proceed, or mandatory per-clause severity acknowledgment (declare-floor without compression).
- **D. Do-nothing-structural / measure-first (deferral-honoring baseline; runner-up to steel-man).** Instrument the gap (operator pre-verdict vs gate/challenger catches) to GET the Trial-E data the deferral is gated on; redesign only when data justifies. Honors the deferral + "commit only what evidence supports."

## Key attacks (every approach must survive)
1. **Relocation, not elimination** — does a smaller surface just move the rubber-stamp? What FORCES engagement vs merely reducing volume?
2. **Floor erosion (L-028)** — does the surface declare the floor, or only bound the ceiling? Is severity kept off the user's plate?
3. **Challenger co-miss (~60%)** — is any single same-family agent a single point of failure for the class the gate exists to catch?
4. **Wrong-target metric** — does optimizing review-time-under-15min reward disengagement? Use defect-escape instead.
5. **Job mis-scoping** — premise-truth ≠ correctness; operator holds externalities (domain/regulatory facts) a context-blind challenger never saw. Does the design wrongly strip these?

## Canonical files
- `.claude/skills/cairn-intent/SKILL.md` (Step 3a ~:60); `workflows/cairn-intent.yaml` (`human_signoff_after: true` ~:115); `templates/intent.md`
- `.claude/agents/intent-challenge.md`, `.claude/agents/intent-review.md`
- `docs/adr/intent-contract-cost-model.md`, `intent-management-loop.md`, `slice-intent-contract.md`, `cliff-failure-mode-and-v1-defenses.md`
- `docs/lessons.md` (L-028 `:557`); `docs/ARCHITECTURE.md` (INV registry)
- prior arc: `.claude/skill-runs/intent-contract-model-decision/`
