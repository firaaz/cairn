# Approach — substrate/root-resolver (Phase 2 Skeptic)

## Tests

Three files cover the intent's three layers:

1. **`tests/unit/test_root.py`** — `scripts/_root.project_root()` contract.
   Precedence chain (`CLAUDE_PROJECT_DIR` → `git rev-parse --show-toplevel`
   → loud `RuntimeError`), empty-env fall-through, relative-path resolution,
   subdirectory git-climbing, and the `.slice-system → .` symlink-trap
   regression for L-017. Source-text check bans `__file__` inside `_root.py`.

2. **`tests/unit/test_root_resolver_migration.py`** — call-site audit.
   AST scans of `scripts/` and `mcp_servers/` reject residual
   `Path(".claude/...")` literals (outside `scripts/_root.py`), `Path.cwd()`
   in production code, and `subprocess.run(["git", ...])` without `cwd=`.
   Each brief-named target (orchestrator quartet, `cairn_query` package,
   `snapshot_diff.py`, MCP server) gets a parametrized assertion so a
   half-migration produces a precise file:line failure. Doc check requires a
   "Project-root resolution" subsection in `docs/operational-reference.md`.

3. **`tests/unit/test_path_discipline_lint.py`** — lint-gate behaviour.
   Invokes `python -m lint_paths` against synthetic trees. Asserts: clean
   exit on the post-migration cairn checkout; non-zero with file:line and a
   `scripts/_root.py:project_root` remediation pointer for each banned
   construct; `tests/` and `scripts/_root.py` exempt.

## Resolved ambiguities

* **Lint-gate home** (intent §Risks open) — committed to
  `scripts/lint_paths.py`, callable as `python -m lint_paths`. Phase 3 may
  still re-export it from `validate_architecture.py`.
* **Extractor signature** — tests assert only the observable: no
  `Path(".claude/...")` literal and a `project_root` reference. Either
  explicit `root` param or internal call passes.
* **MCP `__file__` chain** — server.py's
  `Path(__file__).resolve().parent.parent.parent` is forbidden outright;
  every use of it (sys.path, DB root) is project-root inference.

## Out of scope

Issues #14, #20, #21; upgrade-doc headers. Existing orchestrator/cairn_query
behavioural suites are not duplicated — they remain a Phase-3 obligation per
§Verification 3.
