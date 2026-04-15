```yaml
slice: ruff-cleanup
date: 2026-04-15
phase: 1-intent
invariants-touched: []
adrs-referenced: []
envelope:
  - "tests/unit/test_feature_cross_index.py"
  - "tests/unit/test_invariant_assertions.py"
out-of-scope:
  - "scripts/ — no validator changes"
  - "checks/ — no hook changes"
  - "commands/ — no slash command changes"
  - "docs/ — no ADR or architecture edits"
  - ".claude/d3-bypasses.log — append-only log, not edited by this slice"
  - "any non-lint behavior change in the two test files (no test additions, deletions, or assertion changes)"
```

### What and Why

Three pre-existing ruff lint errors in `tests/unit/test_feature_cross_index.py` and `tests/unit/test_invariant_assertions.py` were bypassed during SLICE-012 via `ADR_D3_BYPASS=1` to land the D3 design slice. The bypass is logged in `.claude/d3-bypasses.log` (currently 1 of 3 within the rolling 10-slice window before D3 design review fires).

This slice clears all three errors so that `python3 scripts/integration_gate.py` Step 4a passes without a bypass on every subsequent slice. Doing it now prevents the rolling-window mechanism from being consumed by known-stale debt and removes the bypass tax from all downstream slices.

This is also the first explicit cleanup-shaped slice in cairn; it sets the precedent for how D3 bypass debt is cleared.

### Specification Detail

Three exact edits, no behavior changes:

1. **`tests/unit/test_feature_cross_index.py:88`** — rename `l` → `line` in the list comprehension. After the edit, the line reads:
   ```python
   lines = [line for line in "".splitlines() if line.strip()]
   ```

2. **`tests/unit/test_feature_cross_index.py:95`** — rename `l` → `line` in the list comprehension. After the edit, the line reads:
   ```python
   line for line in section.splitlines() if line.strip() and not line.startswith("#")
   ```

3. **`tests/unit/test_invariant_assertions.py`** — relocate the import block from the bottom of the file to the top. Specifically:
   - Delete the existing block at lines 1112-1114:
     ```python
     # Import validator functions directly for parsing tests
     sys.path.insert(0, str(CAIRN_ROOT / "scripts"))
     from validate_architecture import parse_assertion_blocks, parse_invariants
     ```
   - Insert the same block (without the comment) after line 29 (`VALIDATOR = ...`), before the `# --- Fixtures ---` separator at line 32. Place a blank line above and below the inserted block. The result is that `sys.path.insert` and the validator import live with the other top-of-file imports, eliminating E402 without `# noqa` suppression.
   - The `# === SLICE-011: Assertion block coverage ...` section comment at line 1105 stays in place. Only the import lines move.

### Boundary

Out of scope for this slice:

- Adding, removing, or modifying any test case in either file.
- Changing assertion semantics, fixtures, or imports beyond the literal three edits above.
- Touching `validate_architecture.py` or any production code.
- Editing `.claude/d3-bypasses.log` (it's append-only; the rolling-window count naturally falls off as slices age out).
- Refactoring the SLICE-011 section structure beyond moving the two import lines.

### Verification (Definition of Done)

Phase 4 PASSES iff all of the following hold:

1. `python3 -m ruff check tests/unit/test_feature_cross_index.py tests/unit/test_invariant_assertions.py` exits 0 with zero errors.
2. `python3 -m pytest tests/unit/test_feature_cross_index.py tests/unit/test_invariant_assertions.py -v` exits 0 with all tests passing — same set of test outcomes as before the slice.
3. `python3 scripts/integration_gate.py` exits 0. Step 3 (invariant check), Step 4a (ruff), and Step 4b (pytest) all PASS.
4. `python3 scripts/snapshot_diff.py --diff` reports no out-of-envelope changes (the two test files are the only changed source files).
5. `git diff` against the pre-slice baseline shows changes confined to the two files in the envelope and to `.claude/current-slice/` artifacts.
6. No new entries are appended to `.claude/d3-bypasses.log` during slice-close — the D3 gates pass cleanly without bypass.
