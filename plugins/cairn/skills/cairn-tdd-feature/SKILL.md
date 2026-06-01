---
name: cairn-tdd-feature
description: Run Cairn's phase-isolated TDD feature workflow in Codex from a per-feature plan document.
---

# Cairn TDD Feature

Codex port of Cairn's `cairn-tdd-feature`. Use when a feature has a plan at `docs/plans/<feature>.md` and needs TDD-by-construction with phase isolation.

Codex does not use Claude custom agent registrations. This skill dispatches generic Codex workers with the bundled phase prompts from `references/`.
Guard boundary semantics and explicit guard commands are documented in `references/guards.md`.

## Inputs

One argument: the plan document path, for example `docs/plans/2026-05-06-some-feature.md`.

## Preflight

1. Read the plan doc. Extract feature id, source-write envelope, and touched invariants.
2. Capture `SNAPSHOT_SHA` with `git rev-parse HEAD`.
3. Capture baseline failures with `uv run pytest -q --tb=no -rf` and save the full output to `/tmp/<feature-id>-baseline-failures.txt`.
4. Create `.claude/skill-runs/<feature-id>/{validation,integration}`.

## Dispatch Pattern

For each phase, call `spawn_agent` with:

```json
{
  "agent_type": "worker",
  "fork_context": false,
  "message": "<phase prompt plus the bounded feature context>"
}
```

Load the phase prompt from:

- `references/phase-1-tdd.md`
- `references/phase-2-tdd.md`
- `references/phase-3-tdd.md`
- `references/phase-4-tdd.md`

Use `references/triager-tdd.md` only when a phase returns `RAISE_ISSUE`.

## Phase Flow

1. Phase 1 reads the plan and writes `.claude/skill-runs/<feature-id>/intent.md`.
2. Human/operator gate: surface the intent promise and band call. Then run:
   - `uv run python checks/premise_guard.py .claude/skill-runs/<feature-id>/intent.md`
   - `uv run python checks/atomicity_guard.py .claude/skill-runs/<feature-id>/intent.md`
   See `references/guards.md` for the full guard-command boundary contract.
3. Phase 2 writes `.claude/skill-runs/<feature-id>/validation/approach.md` and RED tests under `tests/`.
4. Verify RED directly with `uv run pytest <new-test-files> -v`.
5. Phase 3 writes source files inside the plan envelope and makes the tests GREEN.
6. Verify GREEN with `uv run pytest <new-test-files> -v`, then run the relevant broader suite and compare against the baseline failure file.
7. Phase 4 writes `.claude/skill-runs/<feature-id>/integration/sweep-notes.md` and may append `.claude/handoff.md`.

## Regression Attribution

Any test failure observed beyond the baseline failure list requires either a `file:line` citation showing the failure was already present at `SNAPSHOT_SHA`, or `RAISE_ISSUE` with the failure id in the summary. Self-attribution without evidence is not acceptable. The baseline file is the authority.

## Branch Lifecycle

This skill is branch-agnostic. Cairn's phase-commit audit trail assumes feature branches merge back to `dev` with `--no-ff`, not squash or fast-forward.
