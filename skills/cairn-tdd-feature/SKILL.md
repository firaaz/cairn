---
name: cairn-tdd-feature
description: Use when implementing a feature that has a per-feature plan doc at docs/plans/<feature>.md and the operator wants TDD-by-construction phase isolation. Sequences Phase 1 (intent) → Phase 2 (RED tests) → Phase 3 (GREEN impl) → Phase 4 (audit) using fresh subagents per phase.
---

# cairn-tdd-feature

Sequences four phase subagents to deliver a feature with TDD discipline and phase isolation. Each phase runs in a fresh context window via the Agent tool. This is cairn's protocol-layer dispatch primitive, post-orchestrator.

## When to use

- The operator has written a per-feature plan at `docs/plans/<feature>.md` describing the work, the touched invariants, and the source-write envelope.
- The operator wants strict TDD-by-construction (Phase 1 cannot see Phase 2's tests; Phase 2 cannot see Phase 3's impl; Phase 3 cannot see Phase 2's reasoning).
- The work fits in one Phase-3 agent (multi-file fan-out is M3+).

Do NOT use for: ad-hoc bugfixes (use the standard tools), exploratory refactors (brainstorm first), or work that has no clear failing-test shape.

## Inputs

A single argument: path to the per-feature plan doc, e.g., `docs/plans/2026-05-06-some-feature.md`.

## Pre-flight conventions

Before dispatching Phase 1, verify and prepare the following — these prevent the four issues observed during the M2 dogfood (see `.claude/skill-runs/m2-dogfood-extract-invariant-ids/integration/sweep-notes.md` for the original incidents):

1. **Agent definitions are session-pre-existing.** Claude Code's agent registry loads at session start; agent definitions added mid-session aren't `subagent_type`-discoverable. The five agents this skill dispatches (`phase-{1..4}-tdd`, `triager-tdd`) live at `.claude/agents/`. Confirm with `ls .claude/agents/phase-{1..4}-tdd.md .claude/agents/triager-tdd.md` before Step 4. If any are missing or the session predates their commit, abort and instruct the operator to start a fresh session.

2. **Project import convention is in every Phase brief.** Cairn's `pyproject.toml` sets `[tool.pytest.ini_options] pythonpath = ["scripts"]`, which means Python imports inside `tests/` use the form `from <subpackage>.<module> import ...` where `<subpackage>` is a directory under `scripts/` (e.g., `from lib.invariant_id_extractor import extract_invariant_ids`). The Phase-2 brief MUST include this exact convention verbatim — Phase 2's M2 dogfood wrote a bare-module import (`from invariant_id_extractor import ...`) which required a fixup. Inline the `pythonpath` rule in the Phase-2 prompt; do not assume the agent can infer it.

3. **Baseline capture uses the full FAILED list, not the summary line.** Before Phase 1, run `uv run pytest -q --tb=no -rf` and capture the full output (typically 20-50 lines: a `FAILED` block followed by the summary). This file is the comparison anchor for Phase 4. The M2 dogfood captured only the summary line and Phase 4 had to investigate two flagged "new failures" by file-identity comparison instead of a list diff.

## Verification language (Phase 3 / Phase 4)

Phase 3 and Phase 4 briefs MUST contain the following exact language about regression attribution:

> Any test failure observed beyond the baseline failure list (file pinned in `/tmp/<feature-id>-baseline-failures.txt`) requires either (a) a `file:line` citation showing the failure was already present at the snapshot SHA, or (b) `RAISE_ISSUE` with the failure id in the summary. Self-attribution without evidence — "those failures are caused by Phase 2 commits not by my work" — is not acceptable. The baseline file is the only authority.

## Workspace conventions

- Workspace root: `.claude/skill-runs/<feature-id>/`
- Phase 1 writes: `<workspace>/intent.md`
- Phase 2 writes: `<workspace>/validation/approach.md` plus test files under `tests/`
- Phase 3 writes: source files matching the envelope from the plan doc
- Phase 4 writes: `<workspace>/integration/sweep-notes.md`, optionally appends to `.claude/handoff.md`

The feature id is derived from the plan doc's frontmatter `id:` field, or from the filename stem (`2026-05-06-some-feature` → `m2-dogfood-extract-invariant-ids` style).

### intent.md required shape

`phase-1-tdd.md` is authoritative; this is the operational summary. Phase 1 commits an `intent.md` containing YAML frontmatter (`id`, `name`, `snapshot-sha`, `invariants-touched`) followed by sections, in order: What, Why, Boundary, Specification, Verification, **Risk Surface**, **Feature-Local Invariants**, **Explicit Scope-Out**. The three trailing sections are required and must be derived from the plan-doc + cited ADRs + ARCHITECTURE.md — Phase 1 RAISE_ISSUEs rather than fabricating any of them when the inputs don't support derivation. Phase 2 reads Risk Surface and renders it as a named test category in `approach.md`; that traceability is part of the Phase 2 contract.

## Steps

1. **Read the plan doc.** `Read` the path passed as the argument. Extract: feature id, source-write envelope (a list of regex strings under an `envelope:` key in the plan's frontmatter), and the touched invariant ids.

2. **Capture the snapshot SHA.** Run `git rev-parse HEAD`. Save as `SNAPSHOT_SHA`.

3. **Create the workspace.** `mkdir -p .claude/skill-runs/<feature-id>/{validation,integration}`.

4. **Dispatch Phase 1.** Call the Agent tool:
   - `subagent_type: phase-1-tdd`
   - `prompt:` a brief that includes: feature id, plan doc path, workspace path (`.claude/skill-runs/<feature-id>/intent.md`), `SNAPSHOT_SHA`, and a verbatim copy of the plan doc's "What/Why/Boundary" section.

5. **Verify Phase 1 commit.** Parse the JSON tail line for `status` and `commit_hash`. If `status != "OK"`, dispatch `triager-tdd`; act on its decision (escalate, re-dispatch, or abort). Verify the commit exists with `git show <commit_hash> --stat`.

6. **Dispatch Phase 2.** Agent tool with `subagent_type: phase-2-tdd`, prompt including: feature id, intent.md path, plan doc path, workspace path, `SNAPSHOT_SHA`, and the touched invariant ids.

7. **Verify Phase 2 commit and that tests are RED at HEAD~0.** Parse the JSON. Then run `uv run pytest <new-test-files> -v` directly (skill code, not subagent) and confirm tests fail. If green, the intent was already satisfied — escalate.

8. **Dispatch Phase 3.** Agent tool with `subagent_type: phase-3-tdd`, prompt including: feature id, intent.md path, workspace path, `SNAPSHOT_SHA`, the source-write envelope (JSON array of regex strings), and the test paths committed in Phase 2.

9. **Verify Phase 3 commit and GREEN.** Parse the JSON. Run `uv run pytest <new-test-files> -v` and confirm pass. Run `uv run pytest -q` and confirm no new failures vs. the snapshot SHA's baseline.

10. **Dispatch Phase 4.** Agent tool with `subagent_type: phase-4-tdd`, prompt including: feature id, workspace path, plan doc path, `SNAPSHOT_SHA`, and the touched invariant ids.

11. **Verify Phase 4 commit and final state.** Parse the JSON. Confirm `<workspace>/integration/sweep-notes.md` exists. Confirm `git log --oneline | head -4` shows four commits matching the per-phase convention.

## RAISE_ISSUE handling

On any phase RAISE_ISSUE, dispatch `triager-tdd` with: issue commit hash, current phase, feature id, workspace path. Act on its action:
- `ESCALATE_TO_USER`: stop the skill, surface the rationale to the operator, exit.
- `RE_DISPATCH`: re-run the named target phase with the amendment included in the brief. Cap at one re-dispatch per phase per skill run; second RAISE_ISSUE → ESCALATE_TO_USER.
- `ABORT`: stop the skill, surface to operator, exit.

## Output

On success, print a four-line summary listing each phase's commit hash and a one-sentence status. The git log is the durable record; no slice.yaml.

## Coexistence with the orchestrator

This skill creates files only under `.claude/skill-runs/`, `tests/`, and the source paths in the envelope — never under `.claude/current-slice/` or `.claude/features/`. Slice machinery is unaffected; running this skill while a slice is open is a smell but not blocked.
