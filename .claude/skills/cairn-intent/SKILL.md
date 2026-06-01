---
name: cairn-intent
description: Use for intent-management mode — a durable intent contract anchors fluid, test-first construction in the current conversation, bracketed by two fresh-context decorrelation checkpoints (front-loaded intent-challenge before construction; fresh close-review before close). Coexists with cairn-tdd-feature; use cairn-tdd-feature when the operator wants strict per-phase isolation against a docs/plans/<feature>.md plan doc.
---

# cairn-intent

Cairn's intent-management operating mode (`intent-management-loop` D1). The intent contract is the durable anchor; construction is one continuous, test-first conversation; two fresh-context subagents provide the decorrelation the four-phase pipeline got from per-phase isolation. This skill is the Claude-Code-native surface over `workflows/cairn-intent.yaml` — it dispatches the `.claude/agents/` personas via the Agent tool. It does NOT render Codex dispatch briefs; the Codex plugin's `cairn-intent` skill owns that. Both drive the same workflow nodes and must agree on node ids, verdict statuses, and evidence ids.

## When to use

- Repo-writing work that wants a live intent anchor and fluid construction, not per-phase resets.
- Resuming work that already has an active intent (the carrier or Step 1 loads it).

Do NOT use for: strict phase-isolated TDD against a `docs/plans/<feature>.md` plan doc (use `cairn-tdd-feature`, the retained fallback — `intent-management-loop` D1/D7); read-only / Q&A sessions (no write → nothing to govern, D8).

## The loop (intent-management-loop D2)

```
load-or-form-intent ──▶ [new or material change?] ──▶ intent-challenge (fresh) ──▶ operator sign-off
                              │ no (plain resume)                                          │
                              └──────────────────────────────────────────────────────────▶ construct (fluid, test-first)
                                                                                                  │
                                                                       close-review (fresh) ◀─────┘
                                                                                  │
                                                                          operator sign-off ──▶ close
```

Approval is **delta-triggered**: the fresh intent-challenge re-fires only when a **premise or `must-satisfy` clause** changes materially — never on code diff size (D2). A plain resume skips the challenge.

## Workspace conventions

- Workspace root: `.claude/skill-runs/<feature-id>/`
- Intent contract: `<workspace>/intent.md` (shape: `templates/intent.md`)
- Challenge report (report-only, written by the `intent-challenge` agent): `<workspace>/intent-challenge.md`
- Close-review report (report-only, written by the `intent-review` agent): `<workspace>/close-review.md`
- Close record + handoff: `<workspace>/close.md`, `.claude/handoff.md`

The feature id is the intent's frontmatter `id:`.

## Pre-flight

1. **Agent definitions are session-pre-existing.** The two fresh-context agents this skill dispatches live at `.claude/agents/intent-challenge.md` and `.claude/agents/intent-review.md`; Claude Code's registry loads them at session start. Confirm with `ls .claude/agents/intent-challenge.md .claude/agents/intent-review.md` before any dispatch. If either is missing or the session predates its commit, abort and instruct the operator to start a fresh session.

2. **Project import convention.** Cairn's `pyproject.toml` sets `pythonpath = ["scripts"]`; tests under `tests/` import as `from <subpackage>.<module> import ...`. State this verbatim in any test the construct step writes.

## Steps

1. **Load or form the intent (`load-or-form-intent` node).** In the current conversation: locate the active intent from `.claude/handoff.md` pointers, the carrier's session-start emission, or the conversation. If none exists, form the thinnest sufficient contract from `templates/intent.md` — at least a one-line scope statement, one `must-satisfy` clause, an evidence expectation, and a write envelope (D3 completeness floor). Classify the intent as **new**, **material-change**, or **resume** (`delta_kind`). This step is the carrier's fallback: if the SessionStart carrier did not fire, load/form here explicitly — the carrier is an optimization, not the only path (D5).
   - Pass output (`status: ready-for-challenge`): `intent_path`, `delta_kind`, `contract_summary`, `material_change`.
   - If you cannot determine intent (`status: needs-operator-intent`): surface the `question` and `missing_inputs` and stop.

2. **Decide whether the challenge fires.** Fire the intent-challenge iff `delta_kind` is `new` or `material-change` AND a **premise or `must-satisfy` clause** is new or edited (D2). A plain `resume` skips to Step 4.

3. **Dispatch the front-loaded intent-challenge (`intent-challenge` node, fresh context).** If the intent makes claims about existing source behaviour, the operator adds a `## Premise Grounding` block (see `templates/intent.md`); run `uv run python checks/premise_guard.py <workspace>/intent.md` first (exit 0 to proceed; exit 1 surfaces the verbatim-grounding diff and blocks until corrected or `CAIRN_PREMISE_FIX=1`; exit 2 is a malformed-intent stop). Then call the Agent tool:
   - `subagent_type: intent-challenge`
   - `prompt:` a self-contained brief naming: the intent path, the cited `## Premise Grounding` source files, `docs/adr/intent-management-loop.md`, and `checks/premise_guard.py`. The agent attacks each premise's `label`/claim against live source — the slice-#25 semantic gap `premise_guard` cannot catch — and writes one report-only file at `<workspace>/intent-challenge.md`.
   - Parse the agent's final JSON line. `status: challenge-pass` → `challenged_premises`, `cited_evidence`, `blocked_counterfactuals`. `status: challenge-blocked` → surface `blocking_evidence` + `required_intent_revision`; revise the intent and re-dispatch. A sustained block is a real finding, not a hurdle.

3a. **Operator sign-off (mandatory, `human_signoff_after: true`).** Surface the committed `intent.md` AND the challenge verdict to the operator for **explicit** confirmation. Approval here is intent approval, not a glance — the operator approves the contract and the challenge result before any construction. Do not begin Step 4 without it.

4. **Construct (`construct` node, current conversation, fluid).** Implement the approved intent in this conversation. Use **test-first** discipline for every feature/bugfix behaviour: write the test, run `uv run pytest <test> -v` and observe RED, implement, observe GREEN. Keep the intent live; if a **premise or `must-satisfy` clause** changes materially mid-construction, return to Step 3 and re-challenge before continuing (D2 delta-trigger). Writes stay inside the intent's `## Contract` `execution-scope` / write envelope (`role_guard` enforces it ambiently, D6).
   - Pass output (`status: ready-for-close-review`): `intent_path`, `diff_summary`, `test_output`, `evidence_paths`.

5. **Dispatch the fresh close-review (`close-review` node, fresh context).** Call the Agent tool:
   - `subagent_type: intent-review`
   - `prompt:` a self-contained brief naming: the intent path, the construction `git diff`, the full focused test output, architecture-validation output when relevant, and the close evidence from Step 4. The agent checks each clause against the diff, the evidence adequacy against contract depth, and that changed files match `execution-scope`; it writes one report-only file at `<workspace>/close-review.md`. No same-context self-review fallback.
   - Parse the final JSON line. `status: close-review-pass` → `clause_results`, `evidence_summary`, `residual_risk`. `status: close-review-blocked` → surface `findings`, `missing_evidence`, `required_rework`; rework in Step 4 and re-review.

5a. **Operator sign-off (mandatory, `human_signoff_after: true`).** Surface the close-review verdict to the operator. Close only after a `close-review-pass` OR an explicit operator acceptance of a documented `residual_risk`.

6. **Close (`close` node, current conversation).** Record the close: write `<workspace>/close.md` (intent pointer, final verification, residual risk if accepted), append a handoff pointer to `.claude/handoff.md`, and record the Trial-E observation (felt cost vs four-phase; any correlated-miss signal) to `docs/dogfood-log.md`. Run the final verification command and confirm GREEN before recording.
   - Pass output (`status: closed`): `intent_path`, `verification`, `handoff_entry`, `trial_e_observation`.
   - Keep `cairn-tdd-feature` as the fallback until a future firm retirement ADR supersedes it (D7).

## Decorrelation note (intent-management-loop D4)

Both checkpoints run as fresh-context **same-family** subagents (fits the INV-004 budget). The Kim-et-al ~60% same-family error-agreement risk is accepted EXPOSED for this provisional trial. A correlated miss observed in Trial E opens a cross-family `/decision` — record any such signal in the Step 6 Trial-E observation.

## Output

On success, print a short summary: intent path, challenge verdict (or "resume — skipped"), close-review verdict, and the handoff pointer. The handoff + close.md are the durable record; no slice.yaml.
