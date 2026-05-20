# Phase 0.5 — User-Journey Trace

## Current journey (today on `dev`)

**Session start → orientation:**
Operator runs `/catchup` (commands/claude-code/catchup.md). Reads `.claude/handoff.md` (pointer-based state machine: gh:#, docs/adr/*.md, docs/plans/*.md entries with state ∈ {open, blocked, deferred}). Tests verify contract at tests/unit/test_handoff_contract.py:166–173 (coverage; resolution).

**Scoping a feature:**

- **Ad-hoc edit:** Operator sets `.claude/active-envelope.yaml` to `mode: operator` + a `paths:` regex list (docs/operational-reference.md:19–23). Edits directly. Hooks: `reversibility-guard.sh` (checks/reversibility-guard.sh:48,76) gates Bash|Edit|Write; `role_guard.py` (checks/role_guard.py) gates Write|Edit when `AGENT_ROLE` unset. `reality-check.sh` (checks/reality-check.sh) runs post-edit.

- **Architectural decision:** Operator invokes `/decision <question>`. Surfaces context to Decision-skill agent-teams. Operator writes ADR via `/new-adr`. `reversibility-guard.sh` blocks overwrites; Edit allowed only for frontmatter (status:, superseded-by:, firmness:). ADRs stored in `docs/adr/*.md`.

- **Feature with TDD:** Operator writes per-feature plan at `docs/plans/<date>-<feature-id>.md` with frontmatter `id:` + `envelope:` regex array. Invokes `cairn-tdd-feature` skill (Skill tool). Plan doc = session-spanning context.

**Dispatch: Four-phase protocol (cairn-tdd-feature, .claude/skills/cairn-tdd-feature/SKILL.md):**

1. **Phase 1 (Intent).** Fresh subagent. Input: plan doc + docs/ARCHITECTURE.md + ADRs. Output: `.claude/skill-runs/<feature-id>/intent.md` (YAML frontmatter + What/Why/Boundary/Specification/Verification/Risk Surface/Feature-Local Invariants/Explicit Scope-Out). **Commit gates Phase 2.** Agent: `.claude/agents/phase-1-tdd.md`.

2. **Phase 2 (Validation).** Fresh subagent. Input: intent.md only. Output: tests under `tests/` + `.claude/skill-runs/<feature-id>/validation/approach.md`. Writes RED tests. **Commit gates Phase 3.** Agent: `.claude/agents/phase-2-tdd.md`.

3. **Phase 3 (Implementation).** Fresh subagent. Input: intent.md + test files. Output: source under envelope regex set (from plan doc). Hook enforcement: `AGENT_ROLE=phase-3-tdd` passed to role_guard.py; Write paths matched against envelope. Commits. **Commit gates Phase 4.** Agent: `.claude/agents/phase-3-tdd.md`.

4. **Phase 4 (Integration).** Fresh subagent. Input: implementation + intent.md + ARCHITECTURE.md. Output: `.claude/skill-runs/<feature-id>/integration/sweep-notes.md`. Runs full test suite + `scripts/validate_architecture.py` + invariant grep-checks. Optional: append to `.claude/handoff.md`. **Commits.** Agent: `.claude/agents/phase-4-tdd.md`.

**RAISE_ISSUE flow:** Any phase escalates → `triager-tdd` agent adjudicates → ESCALATE_TO_USER | RE_DISPATCH | ABORT (docs/operational-reference.md:69–75).

**Session close:**
Phase 4 commits sweep notes. Handoff entries added (optional). Operator reviews `.claude/skill-runs/<feature-id>/` artifacts (intent + approach + sweep-notes). Workspace cleans up or persists per operator discretion.

---

## Journey under Pole A (status quo: four-phase only)

Identical to current journey. Four-phase methodology is the explicit contract. Ad-hoc edits exist outside it (operator envelope gate). Decision-skill usage is orthogonal (doesn't require four-phase dispatch). No tier selection needed. All tasks map to one of: ad-hoc | /decision | cairn-tdd-feature.

---

## Journey under Pole B (4-tier adaptive reliability)

**Tier selection point:** New decision before Phase 1: Operator or scoring function (TBD) selects Tier ∈ {0, 1, 2, 3}.

**Per-tier journey deltas:**

- **Tier 0 (hygiene).** Runs `reversibility-guard.sh` + `role_guard.py` + `reality-check.sh` only. No dispatch skill. Operator edits directly; `.claude/active-envelope.yaml` can be `mode: off` (unrestricted). No intent.md, no test suite, no four-phase ceremony. Commit messages must pass validator.

- **Tier 1 (tested ad-hoc).** Like Tier 0, but operator must run `uv run pytest` before committing. `reality-check.sh` still enforces format/lint. No intent.md, no formalized test ownership. Tests exist but are not written-first.

- **Tier 2 (planned TDD, no phase isolation).** Operator writes plan doc (like four-phase), writes tests, writes code, commits together. No subagent dispatch. All three artifacts (intent-sketch, tests, code) in one session. Operator envelope still gates writes.

- **Tier 3 (four-phase TDD).** Identical to current journey. Full four-phase dispatch, phase isolation, RAISE_ISSUE flow, sweep-notes.

**Boundary gaps under Pole B:**

- **Tier selection mechanism:** Deterministic scoring (source complexity, invariants touched, test coverage), user declaration, or both? Where does the scoring live? Does it block Phase 1 dispatch or is it advisory?
- **Tier upgrade path:** Can Tier 0 work be re-cast to Tier 2 or Tier 3 later? What artifact migration happens?
- **Handoff representation:** If Tier 0–2 work runs outside the dispatch skill, how does it appear in `.claude/handoff.md`? New pointer format? Open question.
- **Hook configuration per tier:** Tier 0 may want `reversibility-guard.sh` disabled for bootstrap work. Who controls that? Per-session `.claude/settings.json` override? Environment variable gating?

---

## Journey under Pole C (à la carte hooks/validators, no tier hierarchy)

**Hook selection point:** New affordance: operator (or a new "hook registry" diagnostic tool) declares which hooks to run before Phase 1.

**Journey changes:**

- **Scoping:** Before editing, operator runs a hypothetical `/hooks-for-this-task` command (or manually reads a decision doc `docs/hook-selection-rationale.md`). Selects from:
  - Linter + formatter only (`ruff`)
  - Reversibility guards (`reversibility-guard.sh`)
  - Role guards (`role_guard.py`)
  - Handoff contract checks (`test_handoff_contract.py`)
  - Invariant validator (`scripts/validate_architecture.py`)

- **Configuration:** Selected hooks are registered in `.claude/settings.json` or a new `.claude/hook-selection.yaml` per-task.

- **No tier logic:** Operator picks tools à la carte based on:
  - Type of change (ADR vs code vs test vs doc)
  - Blast radius (single file vs cross-cutting)
  - Downstream dependencies (consumer-facing breaking change vs internal refactor)
  - External compliance (handoff must be synchronized)

**Boundary gaps under Pole C:**

- **Hook discoverability:** How does operator know which hooks exist and what each enforces? New `docs/hooks-registry.md` required, with per-hook threat model.
- **Preset configurations:** Do common patterns (e.g., "safe bugfix", "ADR write", "test-only") ship as bundled `.claude/settings.json` presets?
- **Validation on mismatch:** If operator selects no hooks but writes to an ADR, who catches it? Is the mistake just "no enforcement happened"? Or should a meta-hook check for likely mismatches and warn?
- **Handoff synchronization:** Handoff contract test assumes all open issues/provisional ADRs appear in `.claude/handoff.md`. But if hooks are à la carte and handoff checks aren't selected, entries can drift silently.

---

## Boundary gaps detected

| Gap | Surfaces under which pole(s) | Category |
|-----|-----|----------|
| Tier selection mechanism (deterministic scoring, user declaration, or hybrid?) | Pole B | Decision-weight; no spec exists. |
| Tier upgrade / artifact migration (Tier 0 → Tier 3) | Pole B | Session/state boundary; unclear handoff. |
| Handoff representation for non-dispatch-skill work (Tier 0–2 under Pole B) | Pole B | Artifact format; pointer types undefined. |
| Per-tier hook configuration (which hooks run per tier?) | Pole B | Configuration scope; per-tier `.claude/settings.json` override strategy? |
| Hook discovery & selection UI (how does operator know which to pick?) | Pole C | No affordance; requires new doc or CLI command. |
| Preset configurations (bundled hook patterns) | Pole C | Optional but would reduce friction; design TBD. |
| Validation on hook/content mismatch (ADR written without reversibility guard?) | Pole C | Silent failure mode; may need meta-hook. |
| Handoff drift if handoff-contract test not selected | Pole C | Coverage risk; handoff becomes eventual-consistent. |

---

## Reusable primitives already shipped

All three poles can reuse:

- **Git-based phase gating** (Phase 2 waits for Phase 1 commit; verified in dispatch skill steps 5/7/9/11).
- **Hook architecture** (PreToolUse / PostToolUse matcher-based dispatch in `.claude/settings.json:3–35`).
- **Invariant validation** (scripts/validate_architecture.py; currently runs post-Phase-4; survives all poles).
- **Handoff contract** (pointer schema + state keywords + tests/unit/test_handoff_contract.py; Pole A/B use directly; Pole C must decide if it's à la carte or mandatory).
- **Agent framework** (subagent dispatch via Skill tool; Pole A/B uses directly; Pole C doesn't use agents unless operator explicitly selects four-phase).
- **Role guards** (AGENT_ROLE + role_guard.py enforcement of envelope regex; Pole B/C can reuse at any tier/level).
- **Identifier scheme** (ADR id + name separation; survives all poles).
- **Plan-doc shape** (frontmatter id + envelope + What/Why/Boundary/Specification/Verification; reusable even if dispatch happens within one session instead of four-phase).

All three poles can drop the four-phase infrastructure (agents, SKILL.md) without breaking hooks, invariants, or handoff — they are orthogonal.
