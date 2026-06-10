"""Tests for the F3 operator-envelope feature in role_guard.py.

AGENT_ROLE unset + .claude/active-envelope.yaml controls write-path enforcement.
All subprocess tests run with cwd=CAIRN_ROOT so the hook resolves the envelope
file via CAIRN_ROOT / ".claude" / "active-envelope.yaml".  Each test that needs
a specific envelope state backs up and restores the real file via the
`envelope_file` fixture.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = CAIRN_ROOT / "checks" / "role_guard.py"
ENVELOPE_PATH = CAIRN_ROOT / ".claude" / "active-envelope.yaml"


# ---------------------------------------------------------------------------
# Fixture: temporarily replace the envelope file for the duration of a test
# ---------------------------------------------------------------------------


@pytest.fixture()
def envelope_file():
    """Yield a setter callable; restores original envelope on teardown."""
    original = ENVELOPE_PATH.read_text() if ENVELOPE_PATH.exists() else None

    def _set(content: str | None) -> None:
        if content is None:
            if ENVELOPE_PATH.exists():
                ENVELOPE_PATH.unlink()
        else:
            ENVELOPE_PATH.parent.mkdir(parents=True, exist_ok=True)
            ENVELOPE_PATH.write_text(content)

    yield _set

    # teardown — restore
    if original is None:
        if ENVELOPE_PATH.exists():
            ENVELOPE_PATH.unlink()
    else:
        ENVELOPE_PATH.write_text(original)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _run_hook(
    tool_input: dict,
    role: str | None = None,
    envelope: str | None = None,
) -> tuple[int, str]:
    env = {
        k: v for k, v in os.environ.items() if k not in {"AGENT_ROLE", "AGENT_ENVELOPE"}
    }
    if role is not None:
        env["AGENT_ROLE"] = role
    if envelope is not None:
        env["AGENT_ENVELOPE"] = envelope
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(tool_input),
        text=True,
        capture_output=True,
        env=env,
        cwd=CAIRN_ROOT,
    )
    return proc.returncode, proc.stderr


# ---------------------------------------------------------------------------
# 1. No envelope file → no-op
# ---------------------------------------------------------------------------


def test_no_envelope_file_noop(envelope_file):
    """AGENT_ROLE unset, no active-envelope.yaml — all writes allowed."""
    envelope_file(None)
    code, _ = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "anything/foo.py"}}
    )
    assert code == 0


# ---------------------------------------------------------------------------
# 2. mode: off → no-op
# ---------------------------------------------------------------------------


def test_mode_off_noop(envelope_file):
    """mode: off disables enforcement regardless of paths."""
    envelope_file("mode: off\n")
    code, _ = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "anything/foo.py"}}
    )
    assert code == 0


# ---------------------------------------------------------------------------
# 3. mode: operator — allowed path
# ---------------------------------------------------------------------------


def test_operator_allows_matching_path(envelope_file):
    """mode: operator allows writes that match the paths list."""
    envelope_file("mode: operator\npaths:\n  - ^src/foo\\.py$\n")
    code, _ = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "src/foo.py"}}
    )
    assert code == 0


# ---------------------------------------------------------------------------
# 4. mode: operator — denied path
# ---------------------------------------------------------------------------


def test_operator_denies_non_matching_path(envelope_file):
    """mode: operator denies writes outside the paths list."""
    envelope_file("mode: operator\npaths:\n  - ^src/foo\\.py$\n")
    code, stderr = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "src/bar.py"}}
    )
    assert code == 2
    assert "operator envelope denied" in stderr
    assert "src/bar.py" in stderr


# ---------------------------------------------------------------------------
# 5. Malformed YAML → fail closed
# ---------------------------------------------------------------------------


def test_malformed_yaml_fails_closed(envelope_file):
    """Broken YAML in active-envelope.yaml causes exit 2 (fail-closed, blocking)."""
    envelope_file("mode: operator\npaths: [\nbad yaml")
    code, stderr = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "src/foo.py"}}
    )
    assert code == 2
    assert "role_guard" in stderr


# ---------------------------------------------------------------------------
# 6. Unknown mode → fail closed
# ---------------------------------------------------------------------------


def test_unknown_mode_fails_closed(envelope_file):
    """Unrecognised mode value causes exit 2 (fail-closed, blocking)."""
    envelope_file("mode: foo\npaths:\n  - ^src/.*\n")
    code, stderr = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "src/foo.py"}}
    )
    assert code == 2
    assert "mode" in stderr


# ---------------------------------------------------------------------------
# 7. mode: operator with paths missing → fail closed
# ---------------------------------------------------------------------------


def test_operator_without_paths_fails_closed(envelope_file):
    """mode: operator with no paths key causes exit 2."""
    envelope_file("mode: operator\n")
    code, stderr = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "src/foo.py"}}
    )
    assert code == 2
    assert "paths" in stderr


# ---------------------------------------------------------------------------
# 8. Operator envelope ignored when AGENT_ROLE is set
# ---------------------------------------------------------------------------


def test_operator_envelope_ignored_when_agent_role_set(envelope_file):
    """When AGENT_ROLE is set, active-envelope.yaml is not consulted."""
    # envelope would deny "src/foo.py" but AGENT_ENVELOPE grants it
    envelope_file("mode: operator\npaths:\n  - ^denied/.*\n")
    code, _ = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "src/foo.py"}},
        role="phase-3-tdd",
        envelope=json.dumps([r"^src/foo\.py$"]),
    )
    assert code == 0


# ---------------------------------------------------------------------------
# 9. Read tools not gated by operator envelope
# ---------------------------------------------------------------------------


def test_read_tools_not_gated(envelope_file):
    """Operator envelope only applies to WRITE_TOOLS; Read is always allowed."""
    envelope_file("mode: operator\npaths:\n  - ^src/foo\\.py$\n")
    code, _ = _run_hook(
        {"tool_name": "Read", "tool_input": {"file_path": "anything/secret.py"}}
    )
    assert code == 0


# ---------------------------------------------------------------------------
# 10. Edit tool also gated (WRITE_TOOLS completeness)
# ---------------------------------------------------------------------------


def test_edit_tool_is_gated(envelope_file):
    """Edit is in WRITE_TOOLS — denied when path not in operator envelope."""
    envelope_file("mode: operator\npaths:\n  - ^src/foo\\.py$\n")
    code, stderr = _run_hook(
        {"tool_name": "Edit", "tool_input": {"file_path": "src/bar.py"}}
    )
    assert code == 2
    assert "operator envelope denied" in stderr


# ---------------------------------------------------------------------------
# 11. Empty file_path in payload — operator envelope allows (no-op)
# ---------------------------------------------------------------------------


def test_empty_file_path_allowed(envelope_file):
    """Empty file_path with operator envelope active → exit 0 (no-op)."""
    envelope_file("mode: operator\npaths:\n  - ^src/.*\n")
    code, _ = _run_hook({"tool_name": "Write", "tool_input": {"file_path": ""}})
    assert code == 0


# ---------------------------------------------------------------------------
# 12. No-envelope happy path must not require pyyaml — consumer hooks invoke
#     role_guard via bare `python3` (commands/claude-code/settings.json) and
#     may not have pyyaml available. Regression for the M4 yaml-at-module-top
#     bug that broke every consumer.
# ---------------------------------------------------------------------------


def test_no_envelope_path_does_not_require_pyyaml(envelope_file):
    """With no envelope file, role_guard must run without importing pyyaml."""
    envelope_file(None)
    env = {
        k: v for k, v in os.environ.items() if k not in {"AGENT_ROLE", "AGENT_ENVELOPE"}
    }
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.modules['yaml'] = None; "
            "import runpy; runpy.run_path('checks/role_guard.py', run_name='__main__')",
        ],
        input=json.dumps(
            {"tool_name": "Write", "tool_input": {"file_path": "anything/foo.py"}}
        ),
        text=True,
        capture_output=True,
        env=env,
        cwd=CAIRN_ROOT,
    )
    assert proc.returncode == 0, f"hook failed without pyyaml: stderr={proc.stderr!r}"
    assert "yaml" not in proc.stderr.lower(), (
        f"hook touched yaml on the no-envelope path: stderr={proc.stderr!r}"
    )
