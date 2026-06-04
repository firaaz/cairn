---
id: trial-e-w1-cross-family-probe
snapshot-sha: c371d72
---

# Trial-E W1 Cross-Family Probe Runbook

## Purpose

Measure whether a Codex challenger changes the miss/co-miss outcome on the
same fidelity-leap class used by dp3. This harness reuses five neutral
case-intent files:

- `.claude/skill-runs/trial-e-w1-case-01/intent.md`
- `.claude/skill-runs/trial-e-w1-case-02/intent.md`
- `.claude/skill-runs/trial-e-w1-case-03/intent.md`
- `.claude/skill-runs/trial-e-w1-case-04/intent.md`
- `.claude/skill-runs/trial-e-w1-case-05/intent.md`

The challenger should see only one case intent plus its cited source at a time.
Do not provide dp3 notes, this runbook, the closure spec, or any answer key to
the challenger.

## Mechanical Preconditions

Run with `CAIRN_PREMISE_FIX` unset:

```bash
uv run python checks/premise_guard.py .claude/skill-runs/trial-e-w1-case-01/intent.md
uv run python checks/premise_guard.py .claude/skill-runs/trial-e-w1-case-02/intent.md
uv run python checks/premise_guard.py .claude/skill-runs/trial-e-w1-case-03/intent.md
uv run python checks/premise_guard.py .claude/skill-runs/trial-e-w1-case-04/intent.md
uv run python checks/premise_guard.py .claude/skill-runs/trial-e-w1-case-05/intent.md
```

Each grounded case must exit 0. A bogus-source variant must exit 1 with
`cited source not found`.

## Codex Dispatch Path

The canonical dispatch brief is rendered with:

```bash
uv run python -c "from pathlib import Path; from lib.workflow_registry import load_workflow; from lib.codex_workflow_executor import render_codex_dispatch_brief; w=load_workflow(Path('workflows/cairn-intent.yaml')); print(render_codex_dispatch_brief(w, 'cairn-intent-challenge'))"
```

For each case, dispatch a fresh Codex worker with no context fork. The worker's
message should include the rendered `cairn-intent-challenge` brief and a single
case path, replacing the generic `<feature>` placeholder with that case id.

## Recording

Record the case-by-case Codex verdicts and the blind-grader comparison in
`docs/operator-field-notes-YYYY-MM-DD.md`. Carry dp3's caveats: small n,
existence-not-rate, de-primed capability floor, and not production-prompt
behavior.
