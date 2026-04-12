# /status

Show the current state of the development system at a glance.

Usage: `/status`

## Rules

1. Read `.claude/current-slice/slice.yaml` — report slice ID, title, phase, started date, invariants, ADRs. If none, say so.
2. Check phase artifacts: intent.md (exists + committed?), validation/ (has files + committed?), implementation (envelope source + uncommitted changes?), tests (`uv run python -m pytest tests/ -x --tb=line -q 2>/dev/null`).
3. Read `.claude/sweep.yaml` — report current slice number, last sweep, interval, whether sweep is due.
4. Run `uv run python .slice-system/scripts/validate_architecture.py` — report pass/fail. Note proposed or provisional-treated-as-firm ADRs.
5. Report git: branch, uncommitted count, last commit message and date.
6. Format as compact dashboard, not a report.

## Load full

No full form.
