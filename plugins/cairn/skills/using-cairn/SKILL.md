---
name: using-cairn
description: Use as the entry point for Cairn in Codex; choose the right Cairn skill for catchup, handoff, decisions, ADRs, TDD dispatch, or intent workflow operation.
---

# Using Cairn

Cairn is a protocol layer for complex AI-assisted engineering. Use this skill first when the user asks to "use Cairn" or when they need help choosing a Cairn workflow.

## Skill Chooser

- Use `cairn-catchup` to orient a fresh Codex thread from `.claude/handoff.md`, recent git history, working-tree state, and the active envelope.
- Use `cairn-handoff` to write or refresh `.claude/handoff.md` from `templates/handoff.md`.
- Use `cairn-decision` for decisions that affect architecture, invariants, ownership, or downstream assumptions.
- Use `cairn-new-adr` to create or supersede ADRs with the Cairn frontmatter and append-only discipline.
- Use `cairn-tdd-feature` when a feature has a plan at `docs/plans/<feature>.md` and needs phase-isolated TDD dispatch.
- Use `cairn-intent` to operate the thin intent-management workflow from `workflows/cairn-intent.yaml`.

## Bundled References

Canonical command references live in `references/`. Guard command boundaries are documented in `references/guards.md`. Templates live in `templates/`. Guard scripts live in `checks/`. The Codex workflow renderer lives in `scripts/lib/codex_workflow_executor.py`.

When in doubt, start with `cairn-catchup`, then choose the narrowest workflow that matches the current task.
