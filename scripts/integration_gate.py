#!/usr/bin/env python3
"""D3 integration gate — mechanizes integration-sweep Steps 3-4.

Runs all checks without short-circuiting:
  Step 3: Delegates to validate_architecture.py (Check D invariant assertions)
  Step 4a: ruff check on all Python files
  Step 4b: pytest test suite

Exit codes:
    0 — all gates pass
    1 — one or more gates failed (details on stderr)
    2 — missing prerequisites (e.g. ruff not installed)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _resolve_root() -> Path:
    """Use CWD as the repo root."""
    return Path.cwd()


def _find_validator(root: Path) -> Path:
    """Locate validate_architecture.py.

    Checks root/scripts/ first, then falls back to the same directory as
    this script (for when integration_gate.py is run from a consumer repo
    that symlinks .slice-system).
    """
    candidate = root / "scripts" / "validate_architecture.py"
    if candidate.exists():
        return candidate
    # Fallback: same directory as this script
    here = Path(__file__).resolve().parent
    candidate = here / "validate_architecture.py"
    if candidate.exists():
        return candidate
    return root / "scripts" / "validate_architecture.py"  # let it fail naturally


def _check_prerequisites() -> list[str]:
    """Check that required tools are available. Returns list of missing tools."""
    missing = []
    if not shutil.which("ruff"):
        missing.append("ruff")
    return missing


def _run_step3(root: Path) -> tuple[bool, str]:
    """Step 3: run validate_architecture.py for invariant checking."""
    validator = _find_validator(root)
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(root)
    try:
        result = subprocess.run(
            [sys.executable, str(validator)],
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        return (
            False,
            "Step 3 (invariant check): FAIL — validate_architecture.py not found",
        )
    except subprocess.TimeoutExpired:
        return False, "Step 3 (invariant check): FAIL — timed out"

    if result.returncode == 0:
        return True, "Step 3 (invariant check): PASS"
    else:
        detail = result.stdout.strip() or result.stderr.strip()
        return False, f"Step 3 (invariant check): FAIL\n{detail}"


def _positive_int_env(name: str, default: int) -> int:
    """Return env var as a positive int, else default. Silent on invalid."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _run_step4a(root: Path) -> tuple[bool, str]:
    """Step 4a: run ruff check on all Python files."""
    timeout = _positive_int_env("CAIRN_RUFF_TIMEOUT", 60)
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return False, "Step 4a (ruff check): FAIL — ruff not found"
    except subprocess.TimeoutExpired:
        return False, "Step 4a (ruff check): FAIL — timed out"

    if result.returncode == 0:
        return True, "Step 4a (ruff check): PASS"
    else:
        detail = result.stdout.strip() or result.stderr.strip()
        return False, f"Step 4a (ruff check): FAIL\n{detail}"


def _run_step4b(root: Path) -> tuple[bool, str]:
    """Step 4b: run pytest test suite."""
    timeout = _positive_int_env("CAIRN_PYTEST_TIMEOUT", 120)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-x", "--tb=short"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, "Step 4b (pytest): FAIL — timed out"

    if result.returncode == 0:
        return True, "Step 4b (pytest): PASS"
    else:
        detail = result.stdout.strip() or result.stderr.strip()
        return False, f"Step 4b (pytest): FAIL\n{detail}"


def main() -> int:
    root = _resolve_root()

    # Prerequisite check
    missing = _check_prerequisites()
    if missing:
        print(
            f"Missing prerequisites: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    # Run all checks — no short-circuit (A2)
    results: list[tuple[bool, str]] = []
    results.append(_run_step3(root))
    results.append(_run_step4a(root))
    results.append(_run_step4b(root))

    # Report
    any_failed = False
    for passed, message in results:
        if passed:
            print(message)
        else:
            any_failed = True
            print(message, file=sys.stderr)

    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
