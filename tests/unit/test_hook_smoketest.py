"""Acceptance test for scripts/smoketest_hooks.sh.

The smoketest shells out to every checks/*.py hook with the system python3
(deliberately outside cairn's uv venv) and reports per-hook PASS/FAIL based
on whether the import phase raises. This test verifies the script does its
job: a clean exit, an explicit PASS line for role_guard.py, and stderr free
of import-failure substrings.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = CAIRN_ROOT / "scripts" / "smoketest_hooks.sh"


def test_smoketest_hooks_script_runs_clean_and_reports_role_guard_pass() -> None:
    assert SCRIPT.exists(), f"missing script: {SCRIPT}"
    assert os.access(SCRIPT, os.X_OK), f"script not executable: {SCRIPT}"

    result = subprocess.run(
        [str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, (
        f"smoketest exited {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )

    role_guard_pass_lines = [
        line
        for line in result.stdout.splitlines()
        if "PASS" in line and "role_guard.py" in line
    ]
    assert role_guard_pass_lines, (
        "expected a stdout line containing both 'PASS' and 'role_guard.py' "
        "(guards against silent-skip where the script enumerates zero hooks "
        "and trivially exits 0).\n"
        f"stdout:\n{result.stdout}"
    )

    for needle in ("ModuleNotFoundError", "ImportError", "SyntaxError"):
        assert needle not in result.stderr, (
            f"smoketest stderr contains forbidden substring {needle!r}\n"
            f"stderr:\n{result.stderr}"
        )


def _run_smoketest() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_liveness_role_guard_blocks_and_allows() -> None:
    """INV-013 D8: role_guard provably blocks a known-bad write (exit 2) and
    allows a known-good absolute in-envelope write (exit 0)."""
    result = _run_smoketest()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS liveness role_guard.py deny" in result.stdout, result.stdout
    assert "PASS liveness role_guard.py allow-absolute" in result.stdout, result.stdout


def test_liveness_reversibility_guard_blocks() -> None:
    """reversibility-guard denies a force-push payload with a deny decision."""
    result = _run_smoketest()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS liveness reversibility-guard.sh deny" in result.stdout, result.stdout


def test_liveness_reality_check_reformats() -> None:
    """reality-check acts on a known-bad (unformatted) Python file."""
    result = _run_smoketest()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS liveness reality-check.sh reformat" in result.stdout, result.stdout


def test_liveness_carrier_fires() -> None:
    """using-cairn-carrier emits its marker and never gates (exit 0)."""
    result = _run_smoketest()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS liveness using-cairn-carrier.sh fired" in result.stdout, result.stdout
