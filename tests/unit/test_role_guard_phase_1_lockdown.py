"""Phase 2 RED — compression/lever-Y-mcp-substrate V4.

`checks/role_guard.py` MUST deny ``Read`` and ``Bash`` tool calls on
canonical-knowledge paths when ``AGENT_ROLE=phase-1-writer`` and no
envelope grant covers the path. Default-allow when ``AGENT_ROLE`` is unset
(pipeline-substrate carve-out per ADR D8 scope clause).

Expected at Phase 2: FAILS — current `role_guard.py` only gates writes
(WRITE_TOOLS) and has no `ROLE_DENY_READ` table.
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


DENIED_PATHS = [
    "scripts/cairn_query/__init__.py",
    "scripts/cairn_query/storage.py",
    "docs/ARCHITECTURE.md",
    "docs/adr/cairn-substrate-and-fastmcp.md",
    "docs/adr/phase-lock-and-role-declaration.md",
    "docs/lessons.md",
    "docs/spec-v1.md",
    "docs/operational-reference.md",
]


def _run_hook(tool_input, role=None, envelope=None):
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


@pytest.mark.parametrize("path", DENIED_PATHS)
def test_v4_phase_1_writer_read_denied_on_canonical_path(path):
    """intent.md §S4 — Read on canonical knowledge paths is denied."""
    code, stderr = _run_hook(
        {"tool_name": "Read", "tool_input": {"file_path": path}},
        role="phase-1-writer",
    )
    assert code == 1, (
        f"phase-1-writer Read of {path!r} must be denied; got rc={code} stderr={stderr!r}"
    )
    assert "phase-1-writer" in stderr or "denied" in stderr.lower()


@pytest.mark.parametrize(
    "command",
    [
        "cat docs/ARCHITECTURE.md",
        "head -n 50 docs/lessons.md",
        "grep INV-008 docs/ARCHITECTURE.md",
        "cat docs/adr/cairn-substrate-and-fastmcp.md",
        "less scripts/cairn_query/storage.py",
    ],
)
def test_v4_phase_1_writer_bash_denied_on_canonical_paths(command):
    """intent.md §S4 — Bash equivalents (cat/head/grep/less) on canonical
    paths are denied. Bash is treated as a Read-class tool per ADR D8.
    """
    code, stderr = _run_hook(
        {"tool_name": "Bash", "tool_input": {"command": command}},
        role="phase-1-writer",
    )
    assert code == 1, (
        f"phase-1-writer Bash {command!r} must be denied; got rc={code} stderr={stderr!r}"
    )


def test_v4_phase_1_writer_read_allowed_on_uncovered_path():
    """intent.md §S4 step 1 — paths not on the deny list pass through."""
    code, _ = _run_hook(
        {
            "tool_name": "Read",
            "tool_input": {"file_path": ".claude/current-slice/intent.md"},
        },
        role="phase-1-writer",
    )
    assert code == 0


def test_v4_default_allow_when_agent_role_unset():
    """ADR D8 scope clause — pipeline-substrate sessions (no AGENT_ROLE)
    are unaffected. Read on canonical paths must allow.
    """
    code, _ = _run_hook(
        {"tool_name": "Read", "tool_input": {"file_path": "docs/ARCHITECTURE.md"}},
        role=None,
    )
    assert code == 0


def test_v4_other_roles_now_in_read_denylist_post_slice_3():
    """compression/lever-Z-substrate-full-pipeline §S1 — Slice 3 generalizes
    ROLE_DENY_READ from `phase-1-writer` only to all four phase roles
    (`phase-2-skeptic`, `phase-3-implementer`, `phase-4-integrator` added).
    Predecessor Slice-2 docstring anticipated this inversion ("Slice 3
    generalizes"); Cluster D (envelope-expansions.log 2026-04-26T19:05Z)
    rewrites the assertion to the post-Slice-3 truth: Read on
    docs/ARCHITECTURE.md is now DENIED for all three additional roles.
    """
    for role in ("phase-2-skeptic", "phase-3-implementer", "phase-4-integrator"):
        code, stderr = _run_hook(
            {"tool_name": "Read", "tool_input": {"file_path": "docs/ARCHITECTURE.md"}},
            role=role,
        )
        assert code == 1, (
            f"{role} Read on canonical path must now be denied post-Slice-3; "
            f"got rc={code} stderr={stderr!r}"
        )
        assert role in stderr or "denied" in stderr.lower(), (
            f"stderr must name role or 'denied'; got stderr={stderr!r}"
        )
