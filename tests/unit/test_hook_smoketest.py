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
