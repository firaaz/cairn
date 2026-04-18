# Integration Sweep — Full Reference

Run a cross-slice integration check against the merged codebase to catch failures that no individual slice could see.

Usage: `/integration-sweep`

## Why This Exists

Two slices that each pass Phase 4 independently can produce a system that is broken in ways neither slice could see. A schema change in slice A that breaks queries written in slice B, a tool signature change that orphans a client added in another slice. Cross-slice failures are silent by definition — that's what makes them dangerous and why periodic sweeps catch what per-slice checks cannot.

The sweep runs in a fresh context against the merged codebase. Its job is to find breakage, not confirm correctness. It is structurally adversarial.

## Step 1: Load Invariants

Read `docs/ARCHITECTURE.md` and extract every invariant from the `## Invariants` section. Each has the form:
**INV-NNN** <statement> (ADR-NNN)

If ARCHITECTURE.md doesn't exist or looks stale (check `git log -1 -- docs/ARCHITECTURE.md` vs latest ADR dates), suggest running `/refresh-architecture` first.

## Step 2: Enumerate Failure Modes

Before checking anything, think adversarially. Enumerate possible cross-slice failure modes specific to this codebase:

- **Import conflicts**: circular dependencies between `src/` modules
- **Schema drift**: DuckDB schema changes that break existing views or queries
- **Tool contract breaks**: MCP tool signatures or return shapes changed
- **Config conflicts**: changes to `.mcp.json`, `pyproject.toml`, or settings
- **Boundary violations**: modules reaching into other modules' data (e.g., `src/agent/` importing from `src/db/` directly)
- **Invariant interactions**: two invariants that cannot both be satisfied simultaneously

List these as a table with potential impact and where to look. This enumeration step exists because looking for specific things finds more than looking generally.

## Steps 3–4: Integration Gate + Snapshot Diff (D3 Automated)

Steps 3 and 4 are mechanized by D3 backstop scripts. Run them instead of manual checks:

### Integration Gate (Steps 3–4 combined)

```bash
python3 scripts/integration_gate.py
```

Runs three sub-checks without short-circuiting:
- **Step 3 (invariant check):** delegates to `validate_architecture.py` Check D — executes invariant-check assertion blocks from ARCHITECTURE.md.
- **Step 4a (ruff check):** `ruff check .` on all Python files.
- **Step 4b (pytest):** `python3 -m pytest tests/ -x --tb=short`.

Exit codes: 0 = all pass, 1 = one or more fail, 2 = missing prerequisites (e.g. ruff).

Each sub-check logs pass/fail status. All checks run even if early ones fail.

### Snapshot Diff (out-of-envelope detection)

```bash
python3 scripts/snapshot_diff.py --diff
```

Compares the current file tree against `.claude/structural-snapshot.json`. Reports files that are new, deleted, or changed outside the current slice's `intent.md` envelope globs.

Exit codes: 0 = no out-of-envelope changes, 1 = out-of-envelope changes found (listed on stdout), 2 = no prior snapshot (creates one).

After a clean sweep, update the baseline:
```bash
python3 scripts/snapshot_diff.py --snapshot
```

### Manual supplementary checks (still recommended)

- **Type check**: `ty check src/` (skip if ty is not available or too slow)
- **Schema check**: If `data/rag.duckdb` exists, verify expected tables/views are present

## Step 5: Review Recent History

Run `git log --oneline -20` and scan for:
- Commits that changed multiple modules simultaneously (potential coupling)
- Commit messages suggesting workarounds or temporary fixes
- Files outside any slice's declared envelope that were modified (check recent slice intents)

Also check if any ADRs have `firmness: provisional` and are being treated as firm in the code — these are candidates for promotion or revision.

## Step 6: Report

Produce a structured summary:

```
## Integration Sweep Results — <date>

**Invariants**: N checked, N passed, N failed
**Cross-module**: N checks run, N passed, N failed
**History review**: <key observations>

### Failures (if any)
1. INV-NNN: <what failed, where, and how to fix it>

### Recommendations
- <patterns to record in docs/lessons.md>
- <ADRs that need updating or promoting from provisional to firm>
- <new slices needed to fix integration issues>

### Verdict: PASS / FIX REQUIRED
```

If failures exist, recommend creating new slices through the normal 4-phase pipeline. Do not retroactively edit completed slices — that breaks the audit trail.

## Step 6.5: Persist Results

Write the sweep report to a file so it survives beyond the current session:

- If an active slice exists (`.claude/current-slice/slice.yaml`), write to `.claude/current-slice/integration/sweep-notes.md`
- Otherwise, create `.claude/sweep-results/` if it doesn't exist, and write to `.claude/sweep-results/<YYYY-MM-DD>-sweep.md`

Commit the results:
```
git add .claude/sweep-results/ .claude/current-slice/integration/ && git commit -m "sweep: integration sweep results — <date>"
```

## Step 7: Update Sweep Tracking

Read `.claude/sweep.yaml` and update `last-sweep-at-slice-id:` to the id of the slice whose completion triggered this sweep (the slice named in the most recent `^slice: .* — complete$` commit on the current branch).
