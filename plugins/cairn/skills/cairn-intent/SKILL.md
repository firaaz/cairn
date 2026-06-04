---
name: cairn-intent
description: Operate Cairn's thin intent-management workflow in Codex using `workflows/cairn-intent.yaml` and the Codex workflow executor helpers.
---

# Cairn Intent

Use this for Cairn's thin intent-management mode: durable intent, current-conversation construction, and fresh-context challenge/review boundaries.

## Inputs

- `workflows/cairn-intent.yaml`
- `scripts/lib/workflow_registry.py`
- `scripts/lib/codex_workflow_executor.py`
- `references/guards.md`

## Operating Loop

1. Load or form the thinnest sufficient intent. Use `templates/intent.md` when creating a new `.claude/skill-runs/<feature>/intent.md`.
2. For a new or materially changed intent, render the `cairn-intent-challenge` Codex dispatch brief. Codex hook-backed enforcement runs automatically where the host has loaded the plugin hooks; use the explicit guard commands from `references/guards.md` as fallback/manual evidence and for non-hooked premise/atomicity checks.
3. Construct in the current conversation under the approved intent. Use test-first discipline for feature or bugfix behavior.
4. When construction has diff, tests, and evidence, render the `cairn-intent-close-review` dispatch brief.
5. Close only after fresh review passes or the operator explicitly accepts documented residual risk, then update `.claude/handoff.md` and record the Trial-E observation in `docs/operator-field-notes-YYYY-MM-DD.md`.

## Rendering Dispatch Briefs

Inside this repo, this Python snippet renders a reviewable packet:

```bash
uv run python -c "from pathlib import Path; from lib.workflow_registry import load_workflow; from lib.codex_workflow_executor import render_codex_dispatch_brief; w=load_workflow(Path('workflows/cairn-intent.yaml')); print(render_codex_dispatch_brief(w, 'cairn-intent-challenge'))"
```

Change the run id to `cairn-intent-close-review` for the close boundary.

Each Codex dispatch uses `spawn_agent` with `agent_type: worker` and `fork_context: false`. The human sign-off boundaries in the workflow are mandatory.
