# handoff — phase 4 → triager (RAISE_ISSUE)

slice: substrate/orchestrator-paths
phase-3 commit: cf6b31f
auditor verdict: RAISE_ISSUE

## Why

Phase 3 migration is technically correct against the lint gate (lint_paths.py exits 0) and the in-scope migration tests pass. However the full unit-test sweep shows **70 new failures across 12 test modules** introduced between slice init (1ca90d7) and Phase 3 (cf6b31f). All trace to a single shape: `project_root()` invoked at module-import / class-attribute time in production modules raises when test fixtures `monkeypatch.chdir(tmp_path)` outside a git tree.

The intent contract (§Verification 3) explicitly requires full `pytest tests/unit/` green. It also calls out that "any new fixture pressure signals a Phase-2 review" — but the rules in intent are sound; the implementation chose the wrong invocation site. Phase-3 fix: defer `project_root()` to call-time, or thread `root: Path` through the regressed entrypoints.

## What the auditor did

- Ran `scripts/lint_paths.py` → exit 0.
- Ran `scripts/validate_architecture.py` → all checks passed.
- Ran in-scope migration tests → 34 passed, 1 xfailed (MCP, out of scope).
- Ran full `pytest tests/unit/` → 70 failed, 1075 passed.
- Verified failures are slice-introduced (40-test pre-Phase-3 baseline at 1ca90d7 was green).
- Wrote `integration/sweep-notes.md` with full evidence.
- Did **not** edit any source/test/ADR file. Did not commit.

## What Phase 3 needs to fix

For each of the 12 failing modules, identify the production module-level / class-default invocation of `project_root()` and either:

1. Move it inside the function body (lazy resolution), or
2. Promote `root: Path` to a constructor / function arg with `root or project_root()` resolution at call time.

Re-run `uv run pytest tests/unit/` to green. Lint gate must remain at exit 0.

## Out of scope (do not touch)

- `mcp_servers/`, `scripts/cairn_query/`, `scripts/snapshot_diff.py` (issue #25).
- `scripts/_root.py`, `scripts/lint_paths.py` beyond what migration forces.
- xfail fixture edits beyond the five already removed.
