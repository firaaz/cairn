# Status — Development System Dashboard

Show the current state of the development system at a glance.

Usage: `/status`

## What to Report

Gather and display all of the following:

### Active Slice

Read `.claude/current-slice/slice.yaml`. If it exists, report:
- Slice ID, title, and current phase (status field)
- Started date
- Invariants touched
- ADRs referenced or created

If no slice is active, say so.

### Phase Artifacts

Check which phase artifacts exist and whether they're committed:

| Phase | Artifact | Exists? | Committed? |
|-------|----------|---------|------------|
| 1 - Intent | `.claude/current-slice/intent.md` | Check file | `git log --oneline -1 -- .claude/current-slice/intent.md` |
| 2 - Validation | `.claude/current-slice/validation/` | Check dir has files | `git log --oneline -1 -- .claude/current-slice/validation/` |
| 3 - Implementation | Source files in envelope | Check intent.md envelope | `git status --short` for uncommitted changes |
| 4 - Integration | All tests pass | Run `uv run python -m pytest tests/ -x --tb=line -q 2>/dev/null` | Report result |

### Integration Sweep

Read `.claude/sweep.yaml` and report:
- Current slice number
- Last sweep at slice N
- Sweep interval
- **Sweep due?** (current - last >= interval)

### ADR Health

Run `uv run python .slice-system/scripts/validate_architecture.py` and report pass/fail.

Also check for:
- Any ADRs with `status: proposed` (not yet accepted — need review)
- Any ADRs with `firmness: provisional` that are being treated as firm boundaries

### Git State

- Current branch
- Uncommitted changes count
- Last commit message and date

### Format

```
## Development System Status — <date>

**Slice**: SLICE-NNN "<title>" — Phase N (<status>)
**Artifacts**: Intent ✓/✗ [committed/uncommitted] | Validation ✓/✗ | Implementation ✓/✗ | Tests ✓/✗
**Sweep**: Due in N slices (last at SLICE-NNN, interval: N)
**Validator**: PASS/FAIL
**ADRs**: N accepted (N firm, N provisional), N proposed
**Git**: branch <name>, N uncommitted files, last commit: "<msg>" (<date>)
```

Keep the output concise — this is a dashboard, not a report.
