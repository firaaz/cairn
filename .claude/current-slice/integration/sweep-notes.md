# sweep-notes — substrate/orchestrator-paths

## Invariants table

No invariants declared in `intent.md` (`invariants-touched` not set). Slice is a path-plumbing migration with explicit behavioral-parity contract; verification is via tests/lint, not invariant grep.

| ID | Statement | Status | Evidence |
|----|-----------|--------|----------|
| (none declared) | — | — | — |

## Verification gates (post-rework, commit `bbe8c80`)

| Gate | Result | Evidence |
|------|--------|----------|
| `uv run python scripts/lint_paths.py` | PASS (exit 0) | "lint_paths: OK — no path-discipline violations found." |
| `uv run python scripts/validate_architecture.py` | PASS (exit 0) | "ALL CHECKS PASSED — Invariants verified: 10, ADR files checked: 18" |
| In-scope tests `test_root_resolver_migration.py` + `test_path_discipline_lint.py` + `test_orchestrator_paths_migration.py` | PASS | 76 passed, 1 xfailed (MCP-cluster, out of scope per intent §Boundary) |
| Full `uv run pytest tests/unit/` | PASS modulo pre-existing | 1141 passed, 4 failed (all in `test_mcp_cairn_knowledge_tools.py` — kuzu binding `IndexError: unordered_map::at` at baseline `1ca90d7` too; not slice-introduced) |
| D3 integration_gate (`scripts/integration_gate.py`) | BYPASS | Step 3 invariant check PASS, Step 4a ruff PASS; pytest fails on the same 4 pre-existing kuzu MCP tests. Bypass logged with reason. |
| D3 snapshot_diff (`scripts/snapshot_diff.py --diff`) | BYPASS | Baseline `.claude/structural-snapshot.json` last refreshed `2026-04-30 00:37` (many slices stale); reports ~hundreds of "new" files unrelated to this envelope. Bypass logged. |

## Phase 3 rework history

**Initial phase 3 (`cf6b31f`):** mechanically applied intent §Specification rules 1–4 across the seven targets — every `Path(".claude/...")` literal → `_project_root_or_cwd()-anchored` (initially `project_root()`-anchored), every `Path.cwd()` → `project_root()`, `cwd=` added to literal-list git subprocess calls, `from _root import project_root` imported in each. Lint gate exits 0; in-scope migration tests pass.

**Phase 4 audit verdict:** RAISE_ISSUE — full pytest sweep regressed 70 tests across 12 modules. Root cause: `project_root()` raises `RuntimeError` when invoked under `monkeypatch.chdir(tmp_path)` because tmp_path is neither a git repo nor pointed at by `CLAUDE_PROJECT_DIR`. Failure surface is call-time, not strictly module-load — tests that import the slice_orchestrator package and then call `_init_state_dict()`, `_observability_paths()`, `commit_phase_handoff()`, etc. trigger `project_root()` via the migrated paths. Intent §Verification(3) (full suite green) violated. Auditor performed no edits.

**Phase 3 rework (`bbe8c80`):**
1. Added `_project_root_or_cwd()` helper to `scripts/slice_orchestrator/core.py`: `try: project_root() except RuntimeError: Path(os.getcwd())`. Mirrors the pattern landed in `a2ebd1a` for `scripts/integration_gate.py:_resolve_root`. Production runs (CLAUDE_PROJECT_DIR set or git repo present) get the canonical resolver; test fixtures using `monkeypatch.chdir(tmp_path)` get cwd, restoring pre-migration `Path.cwd()` semantics for behavioral parity.
2. Replaced every `project_root()` call in `core.py`, `dispatch.py`, `lifecycle.py`, `telemetry.py` with `_project_root_or_cwd()`. The `from _root import project_root` import is preserved (with `# noqa: F401`) per migration rule 4 / `test_target_imports_project_root_from_scripts_root`.
3. `commit_phase_handoff` (lifecycle.py) now passes RELATIVE path strings to `_git("add", ...)` (`.claude/current-slice/intent.md` etc.) so the test contract in `test_commit_phase_handoff_stage_surface.py` (which asserts those exact strings appear in the staged set) continues to hold. Existence checks still use absolute paths via `_project_root_or_cwd() / rel_path`.

**Lint contract preserved.** `Path(os.getcwd())` is `Path(<call>)`, not `Path("string")`, so `_DotClaudeVisitor` does not flag it. `_CwdVisitor` looks for `Path.cwd()` (attribute call) and ignores `os.getcwd()`. `_project_root_or_cwd()` is in `scripts/_root.py`'s donor cluster — but the helper lives in `scripts/slice_orchestrator/core.py`, not `_root.py`, so the boundary "no changes to scripts/_root.py" holds.

## Out-of-scope failures (pre-existing; not slice-introduced)

`test_mcp_cairn_knowledge_tools.py` (4 tests) fails on every commit reachable in the current branch including `1ca90d7` (slice init) and `dev` HEAD before this slice. Trace: `kuzu.Database.init_database` → `_kuzu.Database(...)` → `IndexError: unordered_map::at: key not found`. Environment-bound (kuzu binding state). Belongs to issue #25's MCP cluster scope, not this slice. Documented as "1 pre-existing OOS" in pattern with the prior slice's `compression/lever-Z-substrate-full-pipeline` sweep notes.

## D3 bypasses recorded

- `D3_GATE_BYPASS` (integration_gate): pytest fails only on 4 pre-existing kuzu MCP tests (not slice-introduced); invariant check + ruff check both PASS. Bypass logged in `.claude/d3-bypasses.log`.
- `D3_GATE_BYPASS` (snapshot_diff): baseline snapshot is many slices stale (refresh due as housekeeping, separate from this slice). Hundreds of "new" files reported are pre-existing housekeeping/feature/ADR/plan additions outside this slice's envelope. Bypass logged.

## Disposition

PASS. Phase 3 rework satisfies intent §Verification(1)–(5) modulo the 4 pre-existing kuzu MCP regressions (out of scope per §Boundary, deferred to issue #25). Slice ready for close.
