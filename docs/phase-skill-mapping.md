# Phase Skill Guide

This doc is a **standalone-portable** artefact: a Superpowers user can adopt the phase → skill mapping below without committing to cairn's full four-phase pipeline. Cairn itself uses this table as the binding surface INV-003's `validate_phase_topology` regex-extracts from; preserving the four canonical agent slugs (`phase-1-tdd`, `phase-2-tdd`, `phase-3-tdd`, `phase-4-tdd`), the four role names (Reader, Skeptic, Builder, Auditor), and the literal `Superpowers` token is load-bearing.

This is a **living registry** of the role, anti-behaviors, and recommended skills for each of the four phases. Unlike phase-lock-and-role-declaration (which locks the phase count, the phase names, and the role names), updates to the skill mapping below do not require ADR supersession — they are ordinary documentation edits. phase-lock-and-role-declaration (`docs/adr/phase-lock-and-role-declaration.md`) remains authoritative for the phase/role lock; this doc is authoritative for the skill mapping.

The four canonical agent slugs — `phase-1-tdd`, `phase-2-tdd`, `phase-3-tdd`, `phase-4-tdd` — map 1:1 to the four phase rows below and to the role-slug set declared in `.claude/agents/role-topology.yaml` (the validator's authoritative source).

## Role and anti-behaviors (from phase-lock-and-role-declaration D2)

| Phase | Role | Primary anti-behavior | Secondary anti-behaviors |
|---|---|---|---|
| 1. Intent (`phase-1-tdd`) | **Reader** | Reader does not propose implementation | Does not read source code (greenfield features) or reads only public interfaces (modification features); does not write design-flavored content beyond `intent.md` Zone 2 "Specification Detail" |
| 2. Validation (`phase-2-tdd`) | **Skeptic** | Skeptic does not implement | Does not read Phase 3's implementation; enumerates ambiguities in `intent.md` and resolves them by reference to ARCHITECTURE.md/ADRs or escalates before writing any test |
| 3. Implementation (`phase-3-tdd`) | **Builder** | Builder does not re-litigate the spec or the tests | Does not expand the envelope beyond the plan doc's declared regex array; does not load Phase 2's `approach.md` or reasoning about why tests are shaped as they are |
| 4. Integration (`phase-4-tdd`) | **Auditor** | Auditor does not rewrite the implementation | Produces pass/fail verdict on declared invariants with `file:line` citation evidence; on implementation failure, RAISE_ISSUE per `docs/spec-v1.md` §13 item 8 rather than patching |

## Phase-to-skill mapping

Citations are to Superpowers plugin skill files. The mapping is a first-cut and evolves with experience — ADR supersession is not required to change it.

| Phase | Role | Primary skills | Supporting skills | Notes on adaptation |
|---|---|---|---|---|
| 1. Intent (`phase-1-tdd`) | Reader | — (no primary fit; `.claude/skills/cairn-tdd-feature/SKILL.md` Step 4 is the dispatch protocol guide) | — | No Superpowers skill is a primary fit for Phase 1 because `intent.md`'s Zone 1/2/3 schema is cairn-specific. `superpowers:brainstorming` runs *upstream* of Phase 1 per L-002 (framing step), not inline within the Reader session. |
| 2. Validation (`phase-2-tdd`) | Skeptic | `superpowers:test-driven-development` — the **RED + Verify RED** half of the red-green cycle | `superpowers:brainstorming` for ambiguity enumeration (one-question-at-a-time style aligns with the Skeptic protocol) | TDD's red-green cycle is structurally bisected by cairn's session boundary: the Skeptic commits the failing tests (RED + Verify RED) without ever touching production code, and hands off to Phase 3 via commit. Non-obvious adaptation of the skill. |
| 3. Implementation (`phase-3-tdd`) | Builder | `superpowers:test-driven-development` (GREEN + Verify GREEN + REFACTOR half), `superpowers:verification-before-completion` | `superpowers:subagent-driven-development` when the envelope has multiple independent files; `superpowers:dispatching-parallel-agents` when the envelope has multiple independent files or tasks (within-feature parallel dispatch is v1-legal; cliff-failure-mode-and-v1-defenses D4's v2+ time-box applies to cross-feature parallelism only); `superpowers:receiving-code-review` when review feedback arrives; `superpowers:using-git-worktrees` when subagent-driven tasks require workspace isolation or cross-feature parallel work (parallelism-v1 D3) | Builder completes the TDD cycle that Phase 2 started. `verification-before-completion` is mandatory before ending Phase 3: tests must be run fresh, output cited, no "should pass" claims. |
| 4. Integration (`phase-4-tdd`) | Auditor | `superpowers:verification-before-completion` (applied to full-suite + validator + invariant checks), `superpowers:requesting-code-review` (mandatory before merge) | `superpowers:systematic-debugging` as escape route if an invariant check fails — its "question architecture after 3+ failed fixes" rule maps directly to `docs/spec-v1.md` §13 item 8's Phase 4 death-spiral discipline and to phase-lock-and-role-declaration D2's "Auditor does not rewrite" anti-behavior | Auditor is the terminal phase — pass/fail judgment with evidence. Code-reviewer subagent dispatched via `requesting-code-review` is the external check for invariant verification. If invariants fail, `systematic-debugging` governs the response path (investigate, do not patch; RAISE_ISSUE after 3 failed fixes). |

## Explicit exclusions — skills deliberately NOT mapped

These Superpowers skills are not in the primary mapping above, each for a specific reason:

- `superpowers:executing-plans` — the parallel-session variant of `superpowers:subagent-driven-development`; inside a Phase 3 session, same-session subagent dispatch is the right choice.
- `superpowers:finishing-a-development-branch` — cairn's per-feature commit discipline (Phase 4 commits sweep notes; merge is operator-driven) supersedes it for feature work; applies to non-feature development only.
- `superpowers:writing-skills`, `superpowers:writing-plans` — meta-skills that sit outside any phase.
