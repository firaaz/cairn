"""Missing-dependency behavior for shell hooks.

These tests pin gh#2: hook dependencies must fail closed by default instead of
silently skipping the hook surface.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BASH = Path("/bin/bash")

REALITY_SCRIPTS = [
    REPO_ROOT / "checks" / "reality-check.sh",
    REPO_ROOT / "plugins" / "cairn" / "checks" / "reality-check.sh",
]
REVERSIBILITY_SCRIPTS = [
    REPO_ROOT / "checks" / "reversibility-guard.sh",
    REPO_ROOT / "plugins" / "cairn" / "checks" / "reversibility-guard.sh",
]


def _run_hook(script: Path, payload: str, *, path: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATH"] = path
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [str(BASH), str(script)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=10,
    )


def _write_fake_jq(bin_dir: Path) -> Path:
    jq = bin_dir / "jq"
    jq.write_text(
        "#!/bin/sh\n"
        "cat >/dev/null\n"
        "printf '%s\\n' \"$CAIRN_FAKE_JQ_RESULT\"\n"
    )
    jq.chmod(jq.stat().st_mode | stat.S_IXUSR)
    return jq


@pytest.mark.parametrize("script", REALITY_SCRIPTS, ids=lambda path: str(path.relative_to(REPO_ROOT)))
def test_reality_check_missing_jq_fails_closed(script: Path) -> None:
    result = _run_hook(script, "{}", path="")

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        "ERROR: reality-check hook dependency missing: jq not found in PATH; failing closed"
        in result.stderr
    )


@pytest.mark.parametrize("script", REALITY_SCRIPTS, ids=lambda path: str(path.relative_to(REPO_ROOT)))
def test_reality_check_missing_ruff_on_python_event_fails_closed(
    script: Path, tmp_path: Path
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_fake_jq(bin_dir)
    edited = tmp_path / "edited.py"
    edited.write_text("print('needs ruff')\n")

    result = _run_hook(
        script,
        json.dumps({"tool_input": {"file_path": str(edited)}}),
        path=f"{bin_dir}:/bin:/usr/bin",
        extra_env={"CAIRN_FAKE_JQ_RESULT": str(edited)},
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        "ERROR: reality-check hook dependency missing: ruff not found in PATH; failing closed"
        in result.stderr
    )


@pytest.mark.parametrize("script", REALITY_SCRIPTS, ids=lambda path: str(path.relative_to(REPO_ROOT)))
def test_reality_check_missing_ruff_on_non_python_event_still_allows(
    script: Path, tmp_path: Path
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_fake_jq(bin_dir)

    result = _run_hook(
        script,
        json.dumps({"tool_input": {"file_path": "README.md"}}),
        path=f"{bin_dir}:/bin:/usr/bin",
        extra_env={"CAIRN_FAKE_JQ_RESULT": "README.md"},
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


@pytest.mark.parametrize("script", REVERSIBILITY_SCRIPTS, ids=lambda path: str(path.relative_to(REPO_ROOT)))
def test_reversibility_guard_missing_jq_denies_with_json(script: Path) -> None:
    result = _run_hook(
        script,
        json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"}}),
        path="",
    )

    assert result.returncode == 2
    assert (
        "ERROR: reversibility-guard dependency missing: jq not found in PATH; failing closed"
        in result.stderr
    )
    data = json.loads(result.stdout)
    assert data == {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "REVERSIBILITY GUARD: required dependency jq not found in PATH; failing closed"
            ),
        }
    }


def test_plugin_hook_mirrors_match_canonical_scripts_byte_for_byte() -> None:
    pairs = [
        (
            REPO_ROOT / "checks" / "reality-check.sh",
            REPO_ROOT / "plugins" / "cairn" / "checks" / "reality-check.sh",
        ),
        (
            REPO_ROOT / "checks" / "reversibility-guard.sh",
            REPO_ROOT / "plugins" / "cairn" / "checks" / "reversibility-guard.sh",
        ),
    ]

    for canonical, mirror in pairs:
        assert mirror.read_bytes() == canonical.read_bytes(), (
            f"{mirror.relative_to(REPO_ROOT)} must match "
            f"{canonical.relative_to(REPO_ROOT)} byte-for-byte"
        )
