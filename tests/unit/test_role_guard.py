"""Phase 2 RED tests for compression/infrastructure — checks/role_guard.py.

Verifies intent.md V1 (role_guard correctness) plus Phase 2 ambiguity
resolutions A4 (AGENT_ENVELOPE empty vs unset) and the ADR-scoped write-path-
only constraint from compression-infrastructure-bootstrap.

Invokes role_guard.py as a subprocess with tool-call JSON on stdin and env
vars (AGENT_ROLE, AGENT_ENVELOPE). Asserts on returncode + stderr substring.
Expected state at Phase 2: all tests FAIL because checks/role_guard.py does
not exist yet.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = CAIRN_ROOT / "checks" / "role_guard.py"


def run_hook(
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


# --- V1 — intent.md:134-146 -------------------------------------------------


def test_v1_1_agent_role_unset_is_noop():
    """AGENT_ROLE unset → exit 0 (non-compressed slices unaffected)."""
    code, _ = run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "src/main.py"}},
        role=None,
    )
    assert code == 0


def test_v1_2_phase_1_writer_allowed_on_intent():
    code, _ = run_hook(
        {
            "tool_name": "Write",
            "tool_input": {"file_path": ".claude/current-slice/intent.md"},
        },
        role="phase-1-writer",
    )
    assert code == 0


def test_v1_3_phase_1_writer_denied_on_source():
    code, stderr = run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "src/main.py"}},
        role="phase-1-writer",
    )
    assert code == 1
    assert "phase-1-writer" in stderr


def test_v1_4_phase_2_skeptic_allowed_on_tests():
    code, _ = run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "tests/unit/test_foo.py"}},
        role="phase-2-skeptic",
    )
    assert code == 0


def test_v1_5_phase_2_skeptic_denied_on_intent():
    """F1 prevention — Skeptic may not edit intent.md after Phase 1."""
    code, _ = run_hook(
        {
            "tool_name": "Edit",
            "tool_input": {"file_path": ".claude/current-slice/intent.md"},
        },
        role="phase-2-skeptic",
    )
    assert code == 1


def test_v1_6_phase_3_implementer_denied_on_intent():
    """Primary F1 prevention — Implementer may not edit intent.md."""
    code, stderr = run_hook(
        {
            "tool_name": "Edit",
            "tool_input": {"file_path": ".claude/current-slice/intent.md"},
        },
        role="phase-3-implementer",
        envelope="^src/",
    )
    assert code == 1
    assert "intent" in stderr


def test_v1_7_phase_4_integrator_allowed_on_sweep_notes():
    """F3 support — Integrator must write sweep-notes.md."""
    code, _ = run_hook(
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": ".claude/current-slice/integration/sweep-notes.md"
            },
        },
        role="phase-4-integrator",
    )
    assert code == 0


def test_v1_8_unknown_role_denied():
    code, stderr = run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "tests/unit/test_x.py"}},
        role="phase-99-mystery",
    )
    assert code == 1
    assert "unknown role" in stderr


# --- A4 — envelope empty-vs-unset for phase-3-implementer ------------------


def test_a4_phase_3_implementer_empty_envelope_denies():
    """intent.md:50 — empty AGENT_ENVELOPE denies all writes."""
    code, _ = run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "src/main.py"}},
        role="phase-3-implementer",
        envelope="",
    )
    assert code == 1


def test_a4_phase_3_implementer_unset_envelope_denies():
    """A4 resolution — unset envelope treated as empty → deny."""
    code, _ = run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "src/main.py"}},
        role="phase-3-implementer",
        envelope=None,
    )
    assert code == 1


def test_a4_phase_3_implementer_envelope_match_allows():
    code, _ = run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "src/main.py"}},
        role="phase-3-implementer",
        envelope=r"^src/main\.py$",
    )
    assert code == 0


def test_a4_phase_3_implementer_multiple_envelope_patterns_colon_separated():
    """Colon-separated regex list — intent.md:50."""
    code, _ = run_hook(
        {"tool_name": "Edit", "tool_input": {"file_path": "scripts/helper.py"}},
        role="phase-3-implementer",
        envelope=r"^src/:^scripts/",
    )
    assert code == 0


# --- compression-infrastructure-bootstrap — write-path-only scope -----------


def test_bootstrap_scope_read_tool_ignored():
    """Tool not in {Write,Edit,MultiEdit,NotebookEdit} → exit 0 regardless of role,
    provided the path is outside ROLE_DENY_READ. Path argument substituted from
    `docs/adr/any.md` to `tests/some_test_file.py` per
    compression/lever-Z-substrate-full-pipeline Cluster D
    (envelope-expansions.log 2026-04-26T19:05Z): Slice 3 §S1 added
    `^docs/adr/` to phase-2-skeptic's read-deny set, which would otherwise
    collide with this test's bootstrap-scope-ignores-Read intent. The
    substitute path preserves the original purpose (the bootstrap-scope
    write-path-only check ignores Read) without depending on the previous
    phase-2-skeptic-has-no-read-deny-set side condition.
    """
    code, _ = run_hook(
        {"tool_name": "Read", "tool_input": {"file_path": "tests/some_test_file.py"}},
        role="phase-2-skeptic",
    )
    assert code == 0


def test_bootstrap_scope_bash_tool_ignored():
    code, _ = run_hook(
        {"tool_name": "Bash", "tool_input": {"command": "ls"}},
        role="phase-1-writer",
    )
    assert code == 0


def test_bootstrap_scope_empty_file_path_ignored():
    """intent.md:49 — empty file_path → exit 0."""
    code, _ = run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": ""}},
        role="phase-1-writer",
    )
    assert code == 0


# --- Malformed stdin contract (intent.md:63 — exit code 2) ------------------


def test_malformed_stdin_exits_2():
    """intent.md:63 — exit codes 0 allow, 1 deny, 2 malformed stdin."""
    assert HOOK.exists(), "role_guard.py must exist; Phase 3 writes it"
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not-json-at-all",
        text=True,
        capture_output=True,
        env={**os.environ, "AGENT_ROLE": "phase-1-writer"},
        cwd=CAIRN_ROOT,
    )
    assert proc.returncode == 2
    assert "No such file" not in proc.stderr
