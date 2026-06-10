"""RED tests for the post-M4 simplified role_guard shape (D2 target).

TDD red-phase commit. These tests pin the behavior that Task D2 will deliver:
  - ROLE_POLICIES keyed on TDD slugs (phase-{1..4}-tdd)
  - Write paths under .claude/skill-runs/ instead of .claude/current-slice/
  - No canonical read-class lockdown (READ_CLASS_TOOLS gate removed for all roles)
  - READ_CLASS_TOOLS constant preserved (regression check)
  - _envelope_patterns three-shape contract preserved

Expected at HEAD 59889ce: tests #1-9 FAIL (legacy slugs + read lockdown active);
test #10 PASSES (READ_CLASS_TOOLS constant already exists).
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = CAIRN_ROOT / "checks" / "role_guard.py"


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
# phase-1-tdd write-path tests
# ---------------------------------------------------------------------------


def test_phase_1_tdd_writes_intent_md_within_skill_runs():
    """phase-1-tdd may write intent.md under .claude/skill-runs/<feature>/."""
    code, _ = _run_hook(
        {
            "tool_name": "Write",
            "tool_input": {"file_path": ".claude/skill-runs/some-feature/intent.md"},
        },
        role="phase-1-tdd",
    )
    assert code == 0


def test_phase_1_tdd_denied_outside_skill_runs():
    """phase-1-tdd must not write to arbitrary paths outside skill-runs."""
    code, stderr = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "docs/foo.md"}},
        role="phase-1-tdd",
    )
    assert code == 2
    assert "phase-1-tdd" in stderr or "denied" in stderr


# ---------------------------------------------------------------------------
# phase-2-tdd write-path tests
# ---------------------------------------------------------------------------


def test_phase_2_tdd_writes_tests():
    """phase-2-tdd may write test files under tests/."""
    code, _ = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "tests/unit/test_foo.py"}},
        role="phase-2-tdd",
    )
    assert code == 0


def test_phase_2_tdd_writes_validation():
    """phase-2-tdd may write validation files under .claude/skill-runs/<feature>/validation/."""
    code, _ = _run_hook(
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".claude/skill-runs/foo/validation/approach.md"
            },
        },
        role="phase-2-tdd",
    )
    assert code == 0


# ---------------------------------------------------------------------------
# phase-3-tdd envelope-driven write tests
# ---------------------------------------------------------------------------


def test_phase_3_tdd_envelope_grants():
    """phase-3-tdd with matching AGENT_ENVELOPE allows write."""
    code, _ = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "src/foo.py"}},
        role="phase-3-tdd",
        envelope=json.dumps([r"^src/foo\.py$"]),
    )
    assert code == 0


def test_phase_3_tdd_envelope_denies_outside():
    """phase-3-tdd with AGENT_ENVELOPE denies writes outside the envelope."""
    code, stderr = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "src/bar.py"}},
        role="phase-3-tdd",
        envelope=json.dumps([r"^src/foo\.py$"]),
    )
    assert code == 2
    assert "denied" in stderr or "phase-3-tdd" in stderr


# ---------------------------------------------------------------------------
# phase-4-tdd write-path tests
# ---------------------------------------------------------------------------


def test_phase_4_tdd_writes_integration():
    """phase-4-tdd may write integration notes under .claude/skill-runs/<feature>/integration/."""
    code, _ = _run_hook(
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".claude/skill-runs/foo/integration/sweep-notes.md"
            },
        },
        role="phase-4-tdd",
    )
    assert code == 0


def test_phase_4_tdd_writes_handoff():
    """phase-4-tdd may write .claude/handoff.md."""
    code, _ = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": ".claude/handoff.md"}},
        role="phase-4-tdd",
    )
    assert code == 0


# ---------------------------------------------------------------------------
# No canonical read-class lockdown after M4
# ---------------------------------------------------------------------------


def test_no_canonical_deny_read_lockdown():
    """After M4, no phase role should be blocked from reading canonical docs.

    The ROLE_DENY_READ / _CANONICAL_DENY_PATTERNS lockdown is removed in D2.
    At HEAD, phase-1-writer IS locked down (exit 1). After D2, the lockdown
    is gone and the same call must exit 0 — no envelope needed.

    Uses phase-1-writer (a legacy slug that IS in ROLE_DENY_READ at HEAD) so
    this test fails RED at HEAD and turns GREEN when D2 drops the lockdown.
    """
    code, stderr = _run_hook(
        {
            "tool_name": "Read",
            "tool_input": {"file_path": "docs/ARCHITECTURE.md"},
        },
        role="phase-1-writer",
    )
    assert code == 0, (
        f"expected no read lockdown post-D2; got rc={code} stderr={stderr!r}"
    )


# ---------------------------------------------------------------------------
# READ_CLASS_TOOLS constant preserved (regression check — passes at HEAD)
# ---------------------------------------------------------------------------


def test_read_class_tools_constant_preserved():
    """READ_CLASS_TOOLS == {"Read", "Grep", "Glob"} must survive D2."""
    spec = importlib.util.spec_from_file_location("role_guard", HOOK)
    assert spec and spec.loader
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    assert rg.READ_CLASS_TOOLS == {"Read", "Grep", "Glob"}, (
        f"READ_CLASS_TOOLS changed; got {rg.READ_CLASS_TOOLS!r}"
    )
