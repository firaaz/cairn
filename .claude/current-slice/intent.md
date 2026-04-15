```yaml
slice: ruff-cleanup-v2
date: 2026-04-15
phase: 1-intent
invariants-touched: []
adrs-referenced: []
envelope:
  - "pyproject.toml"
  - "tests/unit/test_feature_cross_index.py"
  - "tests/unit/test_invariant_assertions.py"
out-of-scope:
  - "scripts/ — no validator changes"
  - "checks/ — no hook changes"
  - "commands/ — no slash command changes"
  - "docs/ — no ADR or architecture edits"
  - ".claude/d3-bypasses.log — append-only; cleared via clean gate pass"
  - "any non-lint behavior change in the two test files (no test additions, deletions, or assertion changes)"
  - "any pyproject.toml content beyond the pytest pythonpath config (no build-system, no ruff config, no project metadata)"
```

### What and Why

SLICE-013 failed because intent.md §3 prescribed placing `sys.path.insert(0, str(CAIRN_ROOT / "scripts"))` before the `from validate_architecture import ...` line at module top — a placement that still triggers ruff E402 (module-level import after a non-import statement). Any literal edit satisfying the "eliminate E402 without `# noqa`" criterion is unreachable via sys.path manipulation at module level.

SLICE-014 retries by moving the runtime path-wiring out of the test file entirely. Pytest's `pythonpath` config (`[tool.pytest.ini_options]` in `pyproject.toml`) puts `scripts/` on `sys.path` before test collection, which lets the validator import sit at the top of the file as an ordinary import — no sys.path statement, no E402. It also bundles the two `l → line` renames from SLICE-013 that were never reached (Phase 3 aborted on the contradiction before any edits landed).

This clears all three D3-bypassed ruff errors (1/10 window entry consumed by SLICE-012) in a single slice and establishes `pyproject.toml` as the home for pytest config going forward.

### Specification Detail

Three exact edits across three files.

**1. `pyproject.toml`** (new file — currently does not exist in the repo). Entire file contents:

```toml
[tool.pytest.ini_options]
pythonpath = ["scripts"]
```

No other sections. No `[build-system]`, no `[project]`, no `[tool.ruff]`. The file exists solely to configure pytest's module search path.

**2. `tests/unit/test_feature_cross_index.py`** — two renames, both list-comprehension loop variables:

- Line 88 before: `lines = [l for l in "".splitlines() if l.strip()]`
- Line 88 after:  `lines = [line for line in "".splitlines() if line.strip()]`
- Line 95 before: `l for l in section.splitlines() if l.strip() and not l.startswith("#")`
- Line 95 after:  `line for line in section.splitlines() if line.strip() and not line.startswith("#")`

No other lines change. `ruff E741` (ambiguous variable name `l`) is the target; renaming to `line` is the canonical fix.

**3. `tests/unit/test_invariant_assertions.py`** — relocate the validator import to the top of the file and delete the runtime sys.path.insert.

- Insertion: add the import to the top-of-file import block, immediately after `from pathlib import Path` (line 25), as a new line:
  ```python
  from validate_architecture import parse_assertion_blocks, parse_invariants
  ```
  Placement above the `CAIRN_ROOT` / `VALIDATOR` module-level assignments (lines 28–29) is required so that ruff E402 does not fire. The pytest `pythonpath = ["scripts"]` config makes `scripts/` available on `sys.path` before test collection, so the import resolves at top-of-file without any runtime sys.path manipulation.
- Deletion: remove lines 1112-1114 in their entirety:
  ```python
  # Import validator functions directly for parsing tests
  sys.path.insert(0, str(CAIRN_ROOT / "scripts"))
  from validate_architecture import parse_assertion_blocks, parse_invariants
  ```
  The preceding `# === SLICE-011: Assertion block coverage ...` section comment at line 1105 stays in place; only the three-line import block is removed.
- `import sys` at line 23 is retained (it is not the target of this slice and may be used elsewhere in the file).

The pytest `pythonpath = ["scripts"]` config makes the top-of-file import resolvable: when pytest loads the test module, `scripts/` is already on `sys.path`, so `from validate_architecture import ...` succeeds without any runtime sys.path manipulation inside the test file.

### Boundary

Out of scope for this slice:

- Adding, removing, or modifying any test case in either file. No assertion changes, no fixture edits, no parametrize tweaks.
- Changing imports beyond the literal edits above (no reordering other imports, no consolidating, no removing `import sys`).
- Touching `validate_architecture.py` or any production code under `scripts/`.
- Editing `.claude/d3-bypasses.log`. The 1/10 window entry ages out naturally when the gate passes cleanly on this and subsequent slices.
- Adding any `pyproject.toml` sections beyond `[tool.pytest.ini_options]` with the single `pythonpath` key. No ruff config migration, no project metadata.
- Refactoring the SLICE-011 section at line 1105+ beyond removing the three import lines.

### Verification (Definition of Done)

Phase 4 PASSES iff all of the following hold:

1. `python3 -m ruff check tests/unit/test_feature_cross_index.py tests/unit/test_invariant_assertions.py` exits 0 with zero errors. No `E402`, no `E741`, no suppressions.
2. `python3 -m pytest tests/unit/test_feature_cross_index.py tests/unit/test_invariant_assertions.py -v` exits 0 with all tests passing — same set of test outcomes as before the slice. The `parse_assertion_blocks` / `parse_invariants` imports resolve via pytest's `pythonpath` config.
3. `python3 scripts/integration_gate.py` exits 0. Step 3 (invariant check), Step 4a (ruff), and Step 4b (pytest) all PASS without bypass.
4. `python3 scripts/snapshot_diff.py --diff` reports changes confined to the three envelope files (`pyproject.toml`, the two test files) plus `.claude/current-slice/` artifacts.
5. `git diff` against the pre-slice baseline shows no changes outside the declared envelope.
6. No new entries are appended to `.claude/d3-bypasses.log` during slice-close — D3 gates pass cleanly.
7. `pyproject.toml` contains only the `[tool.pytest.ini_options]` section with the single `pythonpath = ["scripts"]` key.
