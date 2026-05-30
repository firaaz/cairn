# Cairn Methodology Replacement — The Charter Cycle (Brainstorm #1)

**Date:** 2026-05-30
**Status:** Design spec from brainstorm #1 (subagent-orchestrated methodology). Phase-0 input to the identity-ADR `/decision` arc. Brainstorm #2 (intent-file shape) folded in — the charter *is* the intent-file primitive.
**Skill-run directory:** `.claude/skill-runs/cairn-identity-brainstorm-2026-05-22/`
**Consumes:** `landscape.md` (research arc A), `docs/plans/2026-05-22-cairn-identity-direction.md`.

---

## TL;DR

The 4-phase TDD machinery is replaced by a **charter cycle**: one committed *goal* per work-unit, formed through a focused brainstorming conversation, defended against per-message reactivity by an amendment protocol, executed by blind workers, and coupled to the ADR substrate at both ends with the validator as the mechanical hinge.

The reframe shifts the methodology's articulated center of gravity from *phase separation for complex codebases* toward **goal-commitment against agent reactivity** — a failure mode the old 4 phases defended only incidentally (via isolation). Whether that becomes cairn's headline identity, or a complement to the preserved cliff thesis, is for the identity `/decision` arc to adjudicate. Arc A confirmed the cliff (C1) and the cross-slice substrate (C5–C8) remain load-bearing; this design leaves the substrate internals untouched and rebuilds only the within-cycle machinery.

---

## §1 — The problem this solves

The named failure is **input-reactive over-steering**: the agent treats every user message as a new direction, so the working goal whipsaws instead of *accreting*. The desired property is a goal that is **built up through conversation but has inertia** — it changes only by deliberate amendment, never by default on each turn.

This is distinct from (but adjacent to) the drift/rot arc A documents. It is a control failure: the lead conversational agent is the entire locus of reactivity. Blind workers (subagents) cannot be hijacked — they never see the live chat. So goal-stability is a **lead-anchoring** problem.

Arc A grounding (see `landscape.md`):
- **C3 now-redundant** — subagents structurally cannot re-pollute the parent (only the final message returns). The old objection to subagent-based phases is gone.
- **C2 role-purity is the defensible core** — author≠critic survives as the one cheap mandatory invariant.
- **C6 the validator is a live, fail-closed coherence checker** — the mechanical hinge for substrate coupling.

---

## §2 — The unit: a goal-scoped work-cycle

A **session** is redefined as a *goal-scoped work-cycle*: one declared goal, an explicit start and end, spanning any number of subagent dispatches, surviving compaction/resume. Not "one chat window," not "one subagent." This is cairn's existing **slice** (one vertical change, one acceptance condition) — but discovered conversationally rather than pre-planned.

---

## §3 — The charter (this is the intent-file primitive)

One committed object per cycle. Four parts:

- `goal:` — the single committed objective, in the operator's words, refined through conversation.
- `done:` — **one testable acceptance condition.** This field *is* the operational definition of "one goal." One `done:` → one goal. A sub-task serves the `done:` (a worker dispatch); a second independent `done:` is a *second cycle*. Expressed cairn-natively as "what would a passing test look like" — the lineage of the Phase-2 Skeptic's failing test.
- `constraints:` — the binding invariants/ADRs this cycle must not violate (see §7). Curated, not the whole corpus.
- `amendments:` — an **append-only log**. Every deliberate direction-change is recorded here with its reason. This is how the goal accretes *visibly* instead of mutating silently.

**Singularity is declared, not derived.** There is no formula for "one goal"; the leverage is forcing the judgment to happen *once, explicitly* (at commit) instead of *constantly, implicitly* (every message). Genuinely fuzzy cases ("ship X + document X — one `done:` or two?") are surfaced and arbitrated by the operator, once, then recorded.

**Crystallization gate (SMART, trimmed).** The forming goal becomes committable when it passes a trimmed SMART check — **Specific + Measurable + achievable-enough-to-start**. (Relevant → already covered by `constraints:`; Time-bound → covered by the cycle boundary; both dropped as separate gates.) SMART answers *"ready to commit?"*; the single `done:` answers *"one goal?"* — complementary slots, not competing.

**Form** is the lightest open question (was brainstorm #2): default to a **committed file per cycle** — git-tracked, re-injectable, `amendments:` append-only like ADRs, consistent with "committed artifact is the contract." Final shape is for the `/decision` arc.

---

## §4 — Charter formation: a focused brainstorming conversation

Charter formation **is a focused, brainstorming-style dialogue** (lead + operator): explore intent one question at a time, converge, crystallize until SMART-enough, then **commit the charter**.

This contains the malleability you *want* early to a **bounded front-end**. The synthesis:

> **Brainstorming = the sanctioned malleable phase. Commit = the boundary. Amendment-protocol = post-commit stability.**

The agent stops whipsawing not because it is stubborn, but because free-ranging exploration has a *named place*, and once committed, direction-change costs a deliberate amendment.

This is where the old **Phase-1 (intent)** now lives — *co-formed with the operator*, not derived from ADRs in isolation. The isolation guarantee still holds at the downstream boundary: the brainstorming chat is messy and operator-coupled, but only the **committed charter** crosses to the blind workers — they never see the formation conversation. Co-formed intent **and** uncontaminated execution.

---

## §5 — The amendment protocol (the lead's contract)

Active *after* commit:

- **Default-advance.** Each turn the lead serves the committed `goal:`. Elaborating or ambiguous input is folded *into* the goal, not read as a pivot. The bar for "this is a new direction" is high.
- **Surface, don't switch.** When input genuinely proposes a change, the lead neither silently complies (the reactivity failure) nor silently ignores (the opposite failure). It **names** it: *"committed goal is X; this reads as a shift to Y — amend the charter, or fold into the current goal?"*
- **Record on confirm.** Confirmed changes append to `amendments:`. Direction-change becomes visible, deliberate, recorded — never automatic-per-message.
- **Resolutions, keyed on `done:`** — *fold in* (serves existing `done:`, no amendment) · *amend* (`done:` shifts/grows, recorded, same cycle) · *split* (a second independent `done:` → new cycle).

This **raises the bar for change; it does not refuse steering.** The operator stays in control — changes just stop being *free*.

This is **one shape, not graduated tiers** (respecting the rejected `adaptive-reliability` "not adaptive" signal). Fold/amend/split is scope-resolution, not complexity-tiering.

---

## §6 — Enforcement: mechanical vs disciplined vs deliberately-unbuilt

- **Mechanical (reliable):** a hook re-injects the committed `goal:` + open `amendments:` at the top of each turn, so the goal survives compaction and cannot fade. Arc A says re-injection is the one lever that actually holds (the `CLAUDE.md`-surviving-compaction mechanism).
- **Disciplined (prompt-level):** the classify→surface→record behavior lives in a skill the lead runs.
- **Deliberately NOT built:** a semantic "goal-lock" that hard-blocks off-goal actions. Arc A is explicit that "diverges from the goal" is semantic and cannot be made deterministic like a file-path regex. The bar is raised by *surfacing + recording*, not by blocking — that is the line between this and a rigid system that ignores the operator.

---

## §7 — Charter ↔ substrate coupling (with bounded context)

The charter touches the substrate at **both ends of the cycle**, with the validator as the mechanical hinge. Without this, the charter is an unmoored goal and the substrate is a museum; with it, both are mutually load-bearing.

- **(In) Formation reads the substrate — compactly.** `ARCHITECTURE.md` (the derived invariant list, one testable line each) is the only thing read by default. Full ADR bodies load **only for invariants the goal touches**. `constraints:` becomes the binding invariant set; `done:` must be compatible with it.
- **(Bounded context) Offload the bulk read to a disposable worker.** When a goal plausibly touches the substrate, the lead dispatches a **constraint-harvest worker** (blind, throwaway context) that reads the relevant ADRs in *its own* context and returns a **capped, curated `constraints:` set**. The useless context dies with the worker — it never enters the lead's persistent cycle context, which is exactly where drift accumulates. *Thin where it matters (the lead); thick where it is disposable (the worker).* This repurposes cairn's existing `/decision` "Constraint Harvest" sub-phase as a front-end worker.
- **(Route) Formation classifies the goal:**
  - *Lands within existing constraints* → straight to build → verify, bounded by `constraints:`.
  - *Makes an architectural decision* (touches invariants / boundaries / data-ownership / module structure) → it requires an ADR first: spin a `/decision` sub-arc, the ADR lands append-only, `ARCHITECTURE.md` + invariant update in the same commit, *then* the build cycle proceeds bounded by the new invariant. This is cairn's existing slice-vs-decision two-layer, now **routed by the charter** instead of by operator memory. The charter's `done:` for such a goal spans the whole arc — ADR recorded → implemented → validator green — so a decision and its implementation are **one cycle, not two**.
- **(Out) Decision-touching cycles grow the substrate.** "New ADR filed + invariant bound" is part of `done:` for such cycles — the stone that cycle adds. Cycle N+1's formation reads the constraints cycle N added; constraints compound (the across-cycle coherence arc A named as cairn's durable identity).
- **(Gate) The validator is the mechanical coupling.** Independent-verify runs `scripts/validate_architecture.py`: invariant↔ADR graph coherent, declared `constraints:` respected, any new invariant bound. **Validator-red ⇒ `done:` not met.**

**Three cleanly separated mechanism tiers** (so this respects "no mechanism is the test", direction doc §3):
1. *Selection* (which ADRs are relevant) — simple: compact index + touch-based loading via the harvest worker. Ships now.
2. *Smart retrieval* (semantic index / MCP knowledge server over the corpus) — **deferred**; built only if "omitted an ADR that should have constrained the work" recurs (§3 misalignment criterion #3; N≥3 trigger). Arc A's C6 names native indexing/MCP as the sanctioned path for *recall*.
3. *Semantic alignment* (does the goal's meaning contradict an ADR's meaning) — **never mechanized**; the permanent discipline-only test. The brainstorming front-end *surfaces* the relevant ADRs; the operator judges.

Escalation valve if even the compact index outgrows its budget: cairn's existing `INV-007` context-budget tiers / `[[context-tiers-integration]]`.

---

## §8 — Execution: blind workers

Real work runs in subagents handed only the charter (`goal:` + `done:` + curated `constraints:`), blind to the live chat. The cycle replaces the 4 fixed phases with:

> **charter-commit (conversational, lead + operator) → build (blind worker) → independent verify (blind worker)**

with **one mandatory invariant** — the cairn-defensible core (arc A C2): **the worker that builds is not the worker that checks**, and the verifier is blind to the builder's reasoning (it sees only the committed result + the `done:` acceptance condition).

For substrate-touching goals, the §7 `/decision` sub-arc runs *between* charter-commit and build, producing the constraining ADR the build then respects.

- **Test-first default-on.** A skeptic worker turns `done:` into an executable acceptance test *before* build — cairn's TDD DNA, and `done:` is already a testable condition. Default-on, not an optional tier. (The one place the `/decision` arc may revisit default-on vs droppable.)
- **Arc A's four provisos are hard requirements:** (a) inter-step channel = committed git artifacts, never return strings; (b) returns hard-capped (status + commit_hash + ≤100-word summary); (c) foreground + named subagents only; (d) `CLAUDE_CODE_FORK_SUBAGENT` treated as hostile.

The first two provisos are already met by today's `cairn-tdd-feature` SKILL.md — so the execution layer is **formalization + modernization**, not a rebuild.

---

## §9 — Disposition of the current machinery

- **Superseded:** `.claude/skills/cairn-tdd-feature/SKILL.md` + the four `.claude/agents/phase-{1,2,3,4}-tdd.md` defs → replaced by [charter + amendment-protocol skill + build/verify worker pattern + charter-formation brainstorming skill].
- **`AGENT_ROLE` wiring:** today it is **unwired** — `role_guard.py:137` reads `AGENT_ROLE`, but dispatch never injects it, so per-phase write-gating is dead code and only the operator envelope enforces (documented at `active-envelope.yaml`). Under the new design, workers get scope from **native per-subagent `tools`/`permissionMode`/`disallowedTools` frontmatter** rather than env-var `role_guard` — OR the wiring is fixed via a `SubagentStart` hook. Sub-decision for the `/decision` arc.
- **Untouched:** the substrate internals — ADR corpus, append-only guard, derived `ARCHITECTURE.md`, invariant validator, `/decision` protocol, pointer-handoff (`/catchup`). Arc A: C5–C8 still load-bearing. The pointer-handoff remains the *cross-cycle* resume; the charter is the *within-cycle* goal-state.

---

## §10 — Open questions for the `/decision` arc

1. **Charter form** — file vs frontmatter vs native-memory; exact field grammar; how `constraints:` cite ADRs (id list, invariant ids). (Brainstorm #2 territory; default = committed file per cycle.)
2. **`AGENT_ROLE` disposition** — native per-subagent scoping vs fix the env-var wiring vs both.
3. **Test-first** — confirm default-on vs droppable.
4. **Re-injection hook mechanics** — which event (`UserPromptSubmit` / `SessionStart`), what it injects, interaction with compaction.
5. **Multiple concurrent cycles** — relationship to `[[parallelism-v1]]` (worktree-per-slice → worktree-per-charter).
6. **Charter ↔ handoff overlap** — does the charter subsume part of the pointer-handoff for an in-flight cycle?
7. **Identity claim** — does "goal-commitment against reactivity" become cairn's headline value, a complement to the cliff thesis, or a scoped sub-claim? This is the identity ADR's call; arc A keeps the cliff (C1) load-bearing, so this is additive, not a replacement.

---

## Cross-references

- `docs/plans/2026-05-22-cairn-identity-direction.md` — parent direction; this is brainstorm #1's output (with #2 folded in).
- `.claude/skill-runs/cairn-identity-brainstorm-2026-05-22/landscape.md` — research arc A; the C1–C8 verdicts this design rests on.
- `[[slice-intent-contract]]` — to be superseded; its clause-id/contract concept resurfaces here as `done:` + `constraints:`.
- `[[identity-and-scope-deferral]]` — to be superseded.
- `[[schema-amendment-threshold]]` — N≥3 pattern, reused for the §7 retrieval-mechanism trigger.
- `[[phase-lock-and-role-declaration]]` — its fate is decided here: the 4-role lock collapses to one mandatory build≠check cleave.
- `[[context-discipline-protocol]]` — pointer-handoff contract; survives as the cross-cycle resume.
- `[[context-tiers-integration]]` — `INV-007` context-budget tiers; the escalation valve for §7.
- `why-cairn.md`, `spec-v1.md` §1–§2 — the preserved cliff thesis the charter cycle operates within.
