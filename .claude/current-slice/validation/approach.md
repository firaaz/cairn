# approach — substrate/orchestrator-paths

Phase 2 Skeptic notes. RED suite at `tests/unit/test_orchestrator_paths_migration.py` (42 cases, 22 currently RED). Existing predecessor xfails in `test_root_resolver_migration.py` and `test_path_discipline_lint.py` are also part of the RED surface — they turn XFAIL→PASS once Phase 3 unmarks them.

## Contract under test

Seven modules migrate uniformly per intent §Specification rules 1–4:

- `scripts/slice_orchestrator/{core,lifecycle,dispatch,telemetry}.py`
- `scripts/{integration_gate,validate_architecture,dogfood_evaluate}.py`

Each loses every `Path(".claude/...")` literal, every `Path.cwd()`, gains `cwd=` on every literal-list `subprocess.run(["git", ...])`, and imports `project_root` from `scripts._root`.

## Test surface

- 4 rules × 7 targets = 28 structural assertions (mirrors lint-gate visitors so a gate bug cannot mask incomplete migration).
- 1 real-tree lint-gate exit-0 invocation.
- 6 marker-removal assertions covering every strict-xfail that XPASSes post-migration; +1 negative control asserting the MCP-cluster xfail STAYS (issue #25).
- 1 L-017 symlink-trap regression: `project_root()` from inside a `.slice-system → .` symlink returns canonical toplevel (Verification 4).
- 1 scope-leak guardrail; 4 sanity checks for predecessor deliverables.

## Resolved ambiguities

1. **Brief says "4 markers"; intent lists 5; empirically 8 XPASS.** Enforce removal of every xfail that XPASSes post-migration (4 param + 4 module-level in migration file, 1 in lint file). Verification 3 (suite-green) forces this read. MCP-cluster xfail stays.
2. **`slice_orchestrator/git.py` not named but in scanned subtree.** `subprocess.run(cmd, **kwargs)` is a Name, not a literal list — AST gate does not flag. No test added.
3. **`_resolve_project_root` delete vs. alias.** Tests assert `project_root` import is present, leaving the alias choice to Phase 3.
4. **`Path.cwd()` "process-relative" exemption.** Phase-2 audit confirms none of the seven has a non-root use today. Blanket ban applied.

No unresolved ambiguity → not RAISE_ISSUE.
