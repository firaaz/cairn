# Phase 2 approach — hook-bare-python3-smoketest

## Tests written

Single pytest in `tests/unit/test_hook_smoketest.py`:
`test_smoketest_hooks_script_runs_clean_and_reports_role_guard_pass`.

Assertions (mirror intent.md §"Acceptance contract Phase 2 must encode"):

1. `CAIRN_ROOT = Path(__file__).resolve().parents[2]` — matches the
   `parents[2]` form cited at `test_inv_002_structural_parser.py:40`. (The
   sibling `test_role_guard_envelope.py:32` uses the equivalent
   `parent.parent.parent`; intent permits either.)
2. `SCRIPT.exists()` and `os.access(SCRIPT, os.X_OK)`.
3. `subprocess.run([str(SCRIPT)], capture_output=True, text=True, timeout=30)`.
4. `result.returncode == 0`.
5. Some stdout line contains BOTH `"PASS"` and `"role_guard.py"`. Implemented
   as a per-line scan rather than naive `"PASS" in stdout and "role_guard.py"
   in stdout` to honour the intent's "on the same line" clause and defeat the
   silent-skip failure mode where two unrelated lines could fool a global
   `in`.
6. None of `ModuleNotFoundError`, `ImportError`, `SyntaxError` appears in
   `result.stderr`.

## Spec ambiguities resolved

- **"same line" interpretation** (intent §Acceptance #5): chose strict
  per-line scan. The non-obvious-invariant "Silent-skip is a real failure
  mode" makes line-level granularity load-bearing; a substring-anywhere
  check would let an empty-loop script that happens to print a banner
  passing both substrings on different lines silently pass.
- **`parents[2]` vs `parent.parent.parent`**: both appear in the cited
  reference tests; picked `parents[2]` per intent's §1 wording and
  `test_inv_002_structural_parser.py:40` precedent.
- **No imports from `scripts/`**: smoketest is invoked via subprocess, so
  the project's `pythonpath = ["scripts"]` convention is unused here.

## Flagged for human

None — intent.md is unambiguous on the contract.

## RED confirmation

`uv run pytest tests/unit/test_hook_smoketest.py -v` fails at
`AssertionError: missing script: …/scripts/smoketest_hooks.sh` (expected;
Phase 3 creates the script). No other tests touched.
