---
id: hook-bare-python3-smoketest
name: Hook bare-python3 smoketest
firmness: provisional
status: spec — for cairn-tdd-feature dispatch
date: 2026-05-08
invariants-touched: []
envelope:
  - '^scripts/smoketest_hooks\.sh$'
---

# Hook bare-python3 smoketest

## What

A standalone shell script `scripts/smoketest_hooks.sh` that exercises every Python-based hook under `checks/` by invoking it with the system `python3` (i.e., `command -v python3` resolved outside the project's `uv` virtualenv) and confirms the hook's import phase does not raise. The pytest-side acceptance test at `tests/unit/test_hook_smoketest.py` runs the shell script as a subprocess and asserts a clean exit.

## Why

M4 cairn-shrink shipped a Critical bug caught only at code-review time: `checks/role_guard.py` imported `yaml` at module top, which crashed any consumer that invokes the hook via bare `python3` (no `uv`, no project venv). The cairn pytest suite did not catch it because tests run inside `uv run pytest`, where `pyyaml` is resolvable.

The fix (yaml lazy-import) landed in `a41bd44` along with a pytest regression test that uses `sys.modules['yaml'] = None` to simulate the missing dep. That regression test still runs under `uv` — it covers the symptom but not the consumer-realistic invocation path. A standalone shell smoketest closes the gap by invoking the hook the way a downstream consumer actually invokes it: `python3 checks/role_guard.py < <payload>`. CI integration (e.g., a separate workflow step) is a follow-up; this feature ships only the runnable artifact.

## Boundary

- **One new shell script** at `scripts/smoketest_hooks.sh`. Executable. POSIX `sh` or `bash` (decide in Phase 3).
- **One new pytest test file** at `tests/unit/test_hook_smoketest.py` (Phase 2 writes this).
- **No edits to existing hooks, settings.json, validator, or any documented surface.** The script is purely additive.
- The script must NOT depend on `uv`, `pyyaml`, or any non-stdlib Python package being available. Its whole reason to exist is to verify the hook works without them. The script itself is bash; the hook subprocess is bare `python3`.

## Specification

### `scripts/smoketest_hooks.sh`

Behavior:

1. Resolve `python3` from `PATH` (use `command -v python3`; fail with a non-zero exit and a clear message if not found).
2. For each Python hook under `checks/` (currently only `checks/role_guard.py`; the script must enumerate `checks/*.py` so future Python hooks are auto-covered), invoke it as `"$PYTHON3" "$hook"` with stdin set to a known-malformed payload (`<<< ""` or `< /dev/null`). The malformed-stdin path returns exit code 2 in the current `role_guard.py`; the smoketest accepts any exit code that is NOT a Python `ImportError`-style crash.
3. Detect import failure by stderr inspection: if stderr contains `ModuleNotFoundError`, `ImportError`, or `SyntaxError` after the invocation, the smoketest reports failure for that hook. Any other behavior (deny, allow, malformed-stdin error) is acceptable.
4. Print a one-line PASS/FAIL line per hook to stdout.
5. Exit 0 if all hooks pass; exit 1 if any hook fails.

Robustness:

- The script must not depend on the cwd. It resolves `checks/` relative to the script's own location (`dirname "$0"/..`).
- The script must not modify the working tree, the index, or any environment beyond its subprocess invocations.

### `tests/unit/test_hook_smoketest.py`

A single pytest test that:

1. Locates `scripts/smoketest_hooks.sh` from the repo root (use the same `Path(__file__).resolve()` walk pattern as the existing envelope tests).
2. Runs it with `subprocess.run([str(script)], capture_output=True, text=True, timeout=30)`.
3. Asserts `returncode == 0`.
4. Asserts stdout contains a `PASS` line for `role_guard.py` (so the test catches "smoketest accidentally skipped all hooks" silently passing).
5. Asserts stderr is free of the regression-class strings (`ModuleNotFoundError`, `ImportError`, `SyntaxError`).

The test does not need to invoke the hook directly — that's the script's job. The test verifies the script does its job.

## Verification

Phase 4 must confirm:

- Full pytest suite passes (`uv run pytest -q`) with the new test included; baseline passes were 359/0/2 at `034a59e`.
- `validate_architecture.py` runs green (10 invariants, 27 ADRs).
- `bash scripts/smoketest_hooks.sh` invoked directly (outside pytest) exits 0 and prints PASS for `role_guard.py`.
- `invariants-touched: []` — no invariant evidence section needed.

Phase 4 must NOT:

- Edit existing hook files or hook registrations.
- Add the smoketest to CI (out of scope; tracked as follow-up).
- Modify `pyproject.toml` or any dep manifest.

## Notes for the dispatch skill

- Feature id: `hook-bare-python3-smoketest`.
- Workspace: `.claude/skill-runs/hook-bare-python3-smoketest/`.
- Phase-3 source-write envelope is the regex array in this file's frontmatter (`envelope:` key).
- Snapshot SHA captured by the skill at dispatch time.
