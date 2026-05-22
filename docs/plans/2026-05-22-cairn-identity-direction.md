# Cairn Identity Direction — Infrastructure + Intent-File Primitive + Smarter-Subagent Methodology

**Date:** 2026-05-22
**Status:** Direction draft from brainstorming session; input to a follow-up identity-ADR /decision arc.
**Audience:** next Claude/Codex maintainer session; /decision Phase 0 reader.
**Skill-run directory:** `.claude/skill-runs/cairn-identity-brainstorm-2026-05-22/`

---

## TL;DR

Cairn's scope claim is preserved at **the medium-scale AI-managed cliff** (per `why-cairn.md`, `spec-v1.md` §1). What changes:

- **Cairn IS infrastructure + intent-file primitive + a methodology preset.** Infrastructure = hooks, validators, append-only ADR contract, pointer-only handoff contract, identifier scheme, operator envelope, and (new) the intent-file primitive. The methodology is one preset using this infrastructure, not what cairn IS.
- **The current 4-phase TDD machinery is too heavy** and will be replaced by **smarter subagent orchestration** (specific shape TBD via a research + brainstorm arc).
- **Intent file is the unit of work.** It references constraining ADRs. Mechanism for intent-ADR alignment is deliberately NOT shipped — the absence is the empirical test for whether mechanism is needed.
- **Two contested ADRs are superseded:** `[[slice-intent-contract]]` retires (more-ceremony direction contradicted); `[[identity-and-scope-deferral]]` superseded via its own D3.4 operator-override trigger.
- **Four follow-up arcs declared.**

---

## Context — what triggered this brainstorm

- **2026-05-19** — `docs/plans/2026-05-19-adaptive-reliability-direction.md` proposed pivoting cairn to "adaptive reliability tiers" (Tier 0–3).
- **2026-05-20** — `[[identity-and-scope-deferral]]` ran a /decision arc and **deferred** the pivot, citing no external pull, post-substrate-pivot fatigue, and single-operator constraint. Surfaced L-025 (structural orthogonality: infrastructure ⊥ methodology).
- **2026-05-20** — Same-day, `[[slice-intent-contract]]` (TRIAL-C) added Step 5.5 operator gate + Phase 4 clause-id coverage map to the dispatch skill. Net direction: more ceremony on the most-LLM-authored artifact.
- **2026-05-21** — Operator drafted an `adaptive-reliability-pivot` ADR (preserved at `.claude/skill-runs/cairn-identity-brainstorm-2026-05-22/00-rejected-adaptive-pivot-exploration.md`); rejected with signals "not adaptive" + "thinner" + "identity still open".
- **2026-05-22** — This brainstorm.

### Operator signals threaded through

- **Cliff scope preserved** — `why-cairn.md`'s medium-scale claim stays.
- **Thinner methodology footprint** — infrastructure is the candidate identity; the current 4-phase machinery doesn't justify its weight.
- **Intent-driven methodology** — extract the essence of the 4-phase machinery and centre it on an intent file.
- **Intent aligns with ADRs** — and the ADR corpus itself may not be fit-for-purpose as a constraint surface.
- **No mechanism is the test** — ship intent-ADR alignment as a discipline; let failure surface where mechanism is needed.
- **Smarter subagents replace phases** — not pre-built tiers, not more ceremony.
- **Both subagent design AND current-state-of-AI-assisted-development need research before brainstorm #1 converges.**

---

## §1 — Identity claim

Cairn addresses the **medium-scale AI-managed cliff** (`why-cairn.md`, `spec-v1.md` §1 — PRESERVED). Cairn IS:

- **Infrastructure**: hooks (`reversibility-guard`, `role_guard`, `reality-check`), validators (`scripts/validate_architecture.py`), append-only ADR contract, pointer-only handoff contract, identifier scheme, operator envelope.
- **Intent-file primitive** (new): a named artifact shape that holds work intent and binds to constraining ADRs.
- **A methodology preset**: one preset replacing the current 4-phase TDD machinery via **smarter subagent orchestration** (shape TBD per follow-up brainstorm #1).

The current 4-phase machinery (`cairn-tdd-feature` SKILL.md, four phase agent prompts, dispatch flow, `AGENT_ROLE` wiring, per-phase commit gates) is over-engineered for the value it produces and will be replaced.

The dual-inseparable mechanism (context engineering + role reset) from `why-cairn.md` is preserved as a **goal** the new methodology must satisfy. Standing tensions brainstorm #1 must address:

- Subagents dispatched from a parent session weaken context isolation — orchestrator accumulates subagent outputs and feeds them into next dispatches.
- Role reset depended on session boundaries; subagent ≠ session.
- Today's per-phase `AGENT_MODEL_CONFIG` doesn't map directly to subagent dispatch.

**Brainstorm #1 authority:** refines HOW subagents are used. If research surfaces that subagent orchestration is structurally unworkable for the cliff failure mode, brainstorm #1 may propose an alternative replacement — the identity arc commits to "phases-out," not exclusively to "subagents-in."

---

## §2 — Intent-file primitive

Intent file is the unit of work. Every slice or work-unit produces and works against an intent file.

What the intent file carries — frontmatter vs prose, validator vs no validator, what fields are required, how ADR references are declared — is **deferred to brainstorm #2 (intent-file shape)**. This direction commits only to:

- Intent file exists as a named primitive in cairn's infrastructure layer.
- It references constraining ADRs (shape TBD).
- It is consumed by the methodology preset (current preset: subagent orchestration; specific shape TBD per brainstorm #1).

---

## §3 — Mechanism deferral as the empirical test

The identity ADR (when authored) ships **no mechanism** for intent-ADR semantic alignment. The absence is the test:

- If operator/agent discipline keeps intent aligned with ADRs, mechanism was over-engineering and the absence is the durable choice.
- If alignment fails, the failure mode signals what mechanism to build.

### Misalignment instance criteria

Any of the following counts toward the N≥3 trigger:

1. Intent ships against a `status: superseded` ADR.
2. Intent contradicts an active ADR clause.
3. Intent omits an ADR that should have constrained the work.
4. Operator self-reports drift during or after a session.

### N≥3 trigger

Per `[[schema-amendment-threshold]]` D2 pattern: when N≥3 misalignment instances accumulate, a mechanism-design /decision arc fires. Instances accumulate in `docs/lessons.md` or equivalent tracking surface (decision of tracking-surface is mechanical, not load-bearing here).

### Acknowledged tension

`why-cairn.md`'s thesis says cairn ships mechanism where discipline fails. This direction bets intent-ADR alignment is a layer where discipline-first is appropriate until proven otherwise. The bet is falsifiable via the trigger; if N≥3 fires, the bet is partially or fully wrong and mechanism design becomes load-bearing.

---

## §4 — ADR-sufficiency audit declared as immediate-next /decision arc

The intent-ADR alignment direction depends on the ADR corpus being fit-for-purpose as a constraint surface. Three audit axes (operator-selected):

- **Machine-readability** — ADRs are mostly prose; intent files referencing them can't programmatically align without structured constraints. Whether to make new ADRs structured (frontmatter clauses, `invariants-touched`, etc.) is a decision the audit /decision must make.
- **Coverage gaps** — some decisions live as implicit conventions, `CLAUDE.md` prose, or lessons-not-ADRs. Intent files would have nothing to reference where decisions aren't formalized.
- **Content quality / staleness** — ADRs accumulate stale references, narrative drift, internal contradictions, or commitments the code no longer honors.

The audit is declared as the **immediate-next /decision arc** after the identity ADR lands. It does NOT gate the identity ADR. Likely outputs: supersession of some ADRs, retrofit of others, new ADRs filling coverage gaps, possibly a structured-ADR-shape grammar amendment.

The **shape-inconsistency** axis (Trial-B retrofit incomplete: 14 ADRs missing `name:`, 6 slice-id violations deferred) was explicitly de-selected as a worry. It may be folded into the audit if convenient but is not a load-bearing concern.

---

## §5 — Supersession map

- **`[[slice-intent-contract]]`** (2026-05-20) — superseded. Its premise (add ceremony to slice intent.md via Step 5.5 gate + Phase 4 clause-id coverage map) is contradicted by the thinner-identity direction. Its substantive work product survives:
  - FREEZE+DISTRIBUTE active-alternative pattern → L-026 default-with-pivot
  - clause-id citation concept may resurface in brainstorm #2
  - decision-arc archive at `.claude/skill-runs/interaction-protocol-next-phase-2026-05-20/` is preserved

- **`[[identity-and-scope-deferral]]`** (2026-05-20) — superseded via its own D3.4 trigger (operator design directive). Its Alternatives Considered, pre-mortem (S1/I2/S2), and L-025 finding survive as decision archaeology informing the new ADR.

The identity ADR (when authored) will carry `supersedes: [slice-intent-contract, identity-and-scope-deferral]` and update both prior ADRs' frontmatter with `status: superseded` + `superseded-by: <new-adr-id>`.

---

## §6 — Follow-up arcs declared

### Research arc A — AI-assisted development landscape (research-only)

- **Scope:** what failure modes does cairn's medium-scale cliff still target that native runtimes have not addressed since cairn's conception?
- **Targets:** Claude Code, Codex, Cursor, Aider; native primitives that have shipped/evolved (hooks, skills, subagents, MCP, plugins, worktrees, plan mode, agent SDKs); failure modes visible in published reports / repos / community.
- **Output:** a landscape document grounding which of cairn's load-bearing claims are still load-bearing vs. now-redundant with native runtime features.
- **Feeds:** brainstorm #1, brainstorm #2, ADR-sufficiency /decision arc.
- **No design output** — pure investigation.

### Brainstorm #1 — subagent-orchestrated methodology (research + brainstorm)

- **Consumes** research arc A output + its own research on Claude Code Agent-tool semantics, context isolation guarantees, model-tier dispatch via Agent tool, harness behavior re `AGENT_ROLE` on subagent dispatch.
- **Determines** what replaces the 4-phase machinery: SKILL.md disposition, per-phase agent prompts (4 of them), `AGENT_ROLE` wiring, INV-002 binding, per-phase commit gates.
- **Tension axes from §1** must be addressed: context isolation weakening vs friction reduction; role reset via subagent dispatch vs fresh-session-per-phase; model-tier reconfiguration.
- **Authority** to propose an alternative replacement if subagent orchestration is unworkable. Identity arc commits to "phases-out," not exclusively to "subagents-in."

### Brainstorm #2 — intent-file shape

- **What the intent file carries:** prose vs frontmatter, what fields, how ADR references are declared, what mechanism (if any — see §3) backs the file.
- May be runtime-specific; consumes research arc A.
- The reference-shape question ("pure prose vs frontmatter list vs frontmatter + validator") was deliberately deferred to this brainstorm.

### /decision arc — ADR-sufficiency audit

- **Three axes:** machine-readability, coverage gaps, content quality / staleness (per §4).
- **Informed by** research arc A on what runtimes already cover.
- **Likely outputs:** supersession map, retrofit list, new ADRs filling gaps, possibly a structured-ADR-shape grammar amendment.

---

## §7 — Explicitly out of scope

- **`feature/workflow-subagents` disposition** — separate slice; not gated on this direction. Under infrastructure-first identity, the workflow-subagents have a clean home (one consumer pattern using cairn infrastructure) but its merge/refactor/extract is a slice-level call to be made after the identity ADR.
- **`docs/spec-v1.md` §1 scope-clause amendment** — preserved deferral from `[[identity-and-scope-deferral]]` I2 (reputational one-way door risk). If brainstorm #1 reframes the methodology in a way that materially changes the scope claim, that's a separate /decision arc.
- **Distribution / packaging work (M5/M7)** — orthogonal to identity arc. Calendar-pressured pieces (`gh:firaaz/cairn#32` Node-20 by 2026-06-02; `gh:firaaz/cairn#33` `delivery-mechanism-friction` impl slice) are tracked in `.claude/handoff.md`.

---

## Sequencing recommendation for the next session

1. **Read this direction doc + the rejected adaptive-pivot exploration** at `.claude/skill-runs/cairn-identity-brainstorm-2026-05-22/00-rejected-adaptive-pivot-exploration.md`.
2. **Launch research arc A** as a research subagent (general-purpose or Explore) with the bounded brief from §6.1. Output: landscape document in the same skill-run directory.
3. **Convene brainstorm #1** consuming research arc A's output. Output: design spec for the new methodology shape.
4. **Convene brainstorm #2** in parallel or sequence (intent-file shape).
5. **Author the identity ADR** via /decision arc with the brainstorm outputs as Phase 0 input. Per `feedback_decision_with_agent_teams` — parallelize Phase 0/0.5 + Phase 2 (3 approaches) via TeamCreate.
6. **Author the ADR-sufficiency /decision arc** as the immediate-next /decision after the identity ADR lands.

---

## Cross-references

- `docs/plans/2026-05-19-adaptive-reliability-direction.md` — prior direction; subsumed but its empirical anchors (5 stale tests on dev, INV-011/INV-012 coverage gap) carry forward as concrete bugs the new methodology will need to clean up
- `[[identity-and-scope-deferral]]` — to be superseded
- `[[slice-intent-contract]]` — to be superseded
- `[[adr-contract-execution-scope-clause]]` — contract grammar; carries forward
- `[[schema-amendment-threshold]]` — N≥3 pattern; reused for the §3 misalignment trigger
- `[[phase-lock-and-role-declaration]]` — under threat from §1; brainstorm #1 decides its fate
- `[[context-discipline-protocol]]` — Trial-A handoff contract; survives as Tier-0/1-equivalent primitive
- `[[invariant-binding-strategy]]` — validator-type whitelist; constrains §3 if mechanism is ever built
- `[[context-tiers-integration]]` — INV-007 context-budget tiers; orthogonal
- L-025 (orthogonality), L-026 (default-with-pivot) — both carry forward as load-bearing
- `.claude/skill-runs/cairn-identity-brainstorm-2026-05-22/00-rejected-adaptive-pivot-exploration.md` — input archaeology
- `.claude/handoff.md` — pointer to this direction; threads to be updated on commit (drop the open `cairn-identity-brainstorm-pending` pointer; replace with pointer to this doc plus the follow-up arc threads)
