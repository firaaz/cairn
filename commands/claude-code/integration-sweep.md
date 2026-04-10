# Integration Sweep — Cross-Slice Invariant Check

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

## Step 3: Check Each Invariant

For each invariant from ARCHITECTURE.md, verify it against the current codebase:

1. Read the relevant source files that the invariant constrains
2. Determine if the code honors the invariant — cite specific file:line evidence
3. Record PASS or FAIL

Format:
| INV | Statement | Status | Evidence |
|-----|-----------|--------|----------|
| 001 | Text-to-SQL only... | PASS | No vector/graph imports in src/ (grep verified) |

Use `grep` and file reads for evidence — assertions should be backed by what you actually found, not memory.

## Step 4: Cross-Module Checks

Run concrete verification. Discover the current module structure dynamically rather than assuming specific imports:

1. **Import integrity**: Find all `__init__.py` files in `src/` and attempt to import each top-level package:
   ```bash
   uv run python -c "import importlib, pathlib; [importlib.import_module(f'src.{p.parent.name}') for p in pathlib.Path('src').rglob('__init__.py') if p.parent != pathlib.Path('src')]; print('All imports OK')"
   ```
2. **Lint check**: `ruff check src/ scripts/`
3. **Type check**: `ty check src/` (skip if ty is not available or too slow)
4. **Test suite**: `uv run python -m pytest tests/ -x --tb=short` (if tests/ exists)
5. **Schema check**: If `data/rag.duckdb` exists, verify expected tables/views are present

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

Read `.claude/sweep.yaml` and update `last-sweep-at-slice` to the current `current-slice-number`.
