# /status

One-stop pipeline dashboard. Six lines, ≤1500 chars (INV-004).

Usage: `/status` (lite) · `/status full` loads the expanded view.

## Dashboard output

```
Slice: <id> · Phase: <N> <phase-name> · HEAD: <short-sha>
Last test run: <YYYY-MM-DD HH:MM> <pass|fail|—>
Sweep: <due|up-to-date> (<N> slice-complete since last)
Features: <id:name, id:name, …>
Cost: <N> tokens · $<X.XX> USD (this slice)
Next: <first non-empty line of handoff.md ## Next>
```

## Source contract

1. **Slice** — `slice.yaml` `id:` + `status:`. Phase = status digit. HEAD = `git rev-parse --short` or `—`.
2. **Last test run** — newest mtime under `current-slice/validation/` or `integration/`. Verdict from filename substring.
3. **Sweep** — read `.claude/sweep.yaml`; count `^slice: .* — complete$` since `last-sweep-at-slice-id:`. `due` if count ≥ `sweep-interval`.
4. **Features** — iterate `.claude/features/*.yaml`; emit `id:name`.
5. **Cost** — read `tokens_total` + `cost_total_usd` from the current slice's `<slug>-result.json` (in-progress) or the last-closed slice's result if none active. Per-slice only — this line never totals prior slices. `—` when the result file is absent. INV-009 governs the threshold (provisional / advisory-only at introduction).
6. **Next** — first non-empty line under `## Next` in `.claude/handoff.md`.

Missing state degrades to `—` per field.

## Rendering

Invoke `scripts/render_status.sh` with `CLAUDE_PROJECT_DIR` pointing at the repo root. Bash, stdlib only.

## Load full

Read status.full.md only when the user asks for the full registry view, debug dump, or expanded status. The lite dashboard above satisfies INV-004's progressive-disclosure budget.
