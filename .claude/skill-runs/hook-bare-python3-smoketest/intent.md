---
id: hook-bare-python3-smoketest
name: Hook bare-python3 smoketest
snapshot-sha: 034a59e1ab2ffeaa21195e2eb850d9065791f0c0
invariants-touched: []
---

# Intent — Hook bare-python3 smoketest

## What

Add `scripts/smoketest_hooks.sh`: a stdlib-only shell script that invokes every `checks/*.py` hook with the system `python3` (the one resolved by `command -v python3`, deliberately *outside* cairn's `uv` venv) on a malformed-stdin payload, and reports per-hook PASS/FAIL based purely on whether the hook's import phase raises. A pytest acceptance test at `tests/unit/test_hook_smoketest.py` runs the script as a subprocess and asserts a clean exit, that role_guard.py emits a PASS line, and that stderr is free of import-failure substrings.

## Why

M4 cairn-shrink shipped a Critical regression: `checks/role_guard.py` had a top-level `import yaml`, which crashed any consumer invoking the hook via bare `python3` (no `uv`, no venv). The cairn pytest suite missed it because tests run inside `uv run pytest`. The follow-up regression test (commit `a41bd44`) used `sys.modules['yaml'] = None` — symptomatically correct, but still inside `uv`. The smoketest shells out exactly the way a downstream consumer does, closing the gap with a consumer-realistic invocation path. CI integration is explicitly deferred.

## Boundary

In scope: one new executable shell script (`scripts/smoketest_hooks.sh`) and one new pytest file (`tests/unit/test_hook_smoketest.py`, written in Phase 2). Out of scope: edits to existing hooks, `settings.json`, validator, ADRs, dep manifests, CI workflow files. The script must not require `uv`, `pyyaml`, or any non-stdlib Python package; that requirement is the artifact's reason to exist.

## Specification

### Acceptance contract Phase 2 must encode

`tests/unit/test_hook_smoketest.py` contains a single pytest test that:

1. Resolves the script path via the canonical `CAIRN_ROOT = Path(__file__).resolve().parents[2]` walk used by every other test in `tests/unit/` (see `test_role_guard_envelope.py:32`, `test_inv_002_structural_parser.py:40`, `test_active_envelope.py:20`).
2. Asserts `scripts/smoketest_hooks.sh` exists and is executable (`os.access(path, os.X_OK)`).
3. Runs `subprocess.run([str(script)], capture_output=True, text=True, timeout=30)`.
4. Asserts `result.returncode == 0`.
5. Asserts `"PASS" in result.stdout` AND `"role_guard.py" in result.stdout` on the same line — guards against the silent-skip failure mode where the script enumerates zero hooks and trivially exits 0.
6. Asserts none of `ModuleNotFoundError`, `ImportError`, `SyntaxError` appear in `result.stderr`.

The test does NOT invoke the hook directly; it verifies the script does its job.

### Behavioral contract for `scripts/smoketest_hooks.sh` (Phase 3)

- Resolves `python3` via `command -v python3`; non-zero exit + clear error if absent.
- Resolves `checks/` relative to its own location (`dirname "$0"/..`), not cwd.
- Enumerates `checks/*.py` (currently only `role_guard.py`; future Python hooks auto-covered).
- Per hook: invokes `"$PYTHON3" "$hook"` with `< /dev/null` (or `<<< ""`), captures stderr, ignores exit code semantics.
- Failure criterion: stderr contains `ModuleNotFoundError`, `ImportError`, or `SyntaxError`. Any other behavior — deny, allow, malformed-stdin error, exit 2 — is acceptable.
- Emits one PASS/FAIL line per hook to stdout, including the hook basename.
- Exits 0 iff every hook passes; exits 1 if any hook fails.
- Read-only: must not modify working tree, index, or environment beyond its subprocess invocations.

## Verification

Phase 4 must confirm:

- `uv run pytest -q` is green; baseline at `034a59e` was 359 passed / 2 xfailed / 0 failed.
- `validate_architecture.py` runs green (10 invariants, 27 ADRs).
- Direct invocation `bash scripts/smoketest_hooks.sh` outside pytest exits 0 and prints a PASS line for `role_guard.py`.
- `invariants-touched: []` — no invariant evidence section needed.

Phase 4 must NOT edit existing hooks/registrations, add the smoketest to CI, or modify `pyproject.toml`.

## Reference points for Phase 2/3

- **Repo-root walk pattern**: `tests/unit/test_role_guard_envelope.py:32` uses `CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent`; `test_inv_002_structural_parser.py:40` uses the equivalent `parents[2]`. Phase 2 should match the prevailing style of nearby tests.
- **Hook to smoke**: `checks/role_guard.py` is the only `checks/*.py` at snapshot SHA. `checks/reality-check.sh` and `checks/reversibility-guard.sh` are bash and out of scope.
- **Phase 3 source-write envelope** (from plan frontmatter): `^scripts/smoketest_hooks\.sh$`. Phase 2 writes only to `tests/unit/test_hook_smoketest.py` per its own phase envelope.
- **Existing regression precedent**: commit `a41bd44` (yaml lazy-import + `sys.modules['yaml'] = None` regression test). The smoketest is additive to, not a replacement for, that test.

## Non-obvious invariants implied

- **Silent-skip is a real failure mode.** A naive `for f in checks/*.py; do …; done` that finds zero matches exits 0 with no output. The "PASS line for role_guard.py" assertion is the load-bearing guard against this; Phase 3 must emit per-hook output even when the loop runs, and Phase 2's assertion must be specific enough that an empty stdout fails.
- **Exit-code semantics are not equivalent to import-failure semantics.** `role_guard.py` legitimately exits non-zero (e.g., 2) on malformed stdin; the smoketest must NOT treat non-zero exit as failure. Only stderr substring detection is reliable.
- **The script must work without the project venv.** This means no `#!/usr/bin/env -S uv run …` shebang, no `python` (which may resolve to venv or be absent), only `command -v python3`. The script's own shebang is `#!/usr/bin/env bash` (or `sh`).
- **No symlink recursion risk** here since `scripts/` and `checks/` are not under `.slice-system/`, but the script should not `find` from the repo root either — it scopes enumeration to `checks/` directly.
