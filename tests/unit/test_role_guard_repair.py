"""gh#35 repair contract: deny is blocking (exit 2) and paths are normalized.

Two paired defects (ADR carrier-hierarchy-and-process-diet D4):
- deny exited 1, which Claude Code does not treat as blocking — fail-open;
- envelope regexes are repo-root-relative but the hook matched the raw
  (absolute) tool path, so every absolute-path write was denied — masked by
  the first defect, and a deny-everything gate the moment exit codes flip.

Both directions are asserted: known-bad input BLOCKED (exit 2) and
known-good ABSOLUTE in-envelope path ALLOWED (exit 0). `.slice-system/`
paths are deliberately NOT normalized away (edit-canonical-paths-only rule).
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

ENVELOPE = """\
mode: operator
paths:
  - ^docs/
  - ^\\.claude/skill-runs/.*
"""


def _run_hook(
    tool_input: dict,
    project_dir: Path,
    role: str | None = None,
) -> tuple[int, str]:
    env = {
        k: v for k, v in os.environ.items() if k not in {"AGENT_ROLE", "AGENT_ENVELOPE"}
    }
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    if role is not None:
        env["AGENT_ROLE"] = role
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(tool_input),
        text=True,
        capture_output=True,
        env=env,
        cwd=CAIRN_ROOT,
    )
    return proc.returncode, proc.stderr


@pytest.fixture
def operator_project(tmp_path: Path) -> Path:
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "active-envelope.yaml").write_text(ENVELOPE)
    return tmp_path


def _write(path: str) -> dict:
    return {"tool_name": "Write", "tool_input": {"file_path": path}}


def test_operator_deny_is_blocking_exit_2(operator_project):
    code, stderr = _run_hook(_write("secrets/evil.txt"), operator_project)
    assert code == 2, (
        f"deny must exit 2 (Claude Code blocks only on 2); got rc={code} "
        f"stderr={stderr!r}"
    )
    assert "denied" in stderr


def test_operator_absolute_in_envelope_path_allowed(operator_project):
    abs_path = str(operator_project / "docs" / "roadmap.md")
    code, stderr = _run_hook(_write(abs_path), operator_project)
    assert code == 0, (
        f"absolute path to in-envelope file must be allowed (normalization "
        f"against CLAUDE_PROJECT_DIR); got rc={code} stderr={stderr!r}"
    )


def test_operator_absolute_out_of_envelope_path_denied(operator_project):
    abs_path = str(operator_project / "secrets" / "evil.txt")
    code, stderr = _run_hook(_write(abs_path), operator_project)
    assert code == 2, f"got rc={code} stderr={stderr!r}"


def test_operator_path_outside_project_root_denied(operator_project):
    code, stderr = _run_hook(_write("/etc/passwd"), operator_project)
    assert code == 2, f"got rc={code} stderr={stderr!r}"


def test_slice_system_prefix_is_not_stripped(operator_project):
    """`.slice-system/docs/...` must NOT normalize to `docs/...` — the
    edit-canonical-paths-only rule depends on the symlinked shape matching
    no envelope pattern."""
    rel = ".slice-system/docs/roadmap.md"
    code, _ = _run_hook(_write(rel), operator_project)
    assert code == 2, "relative .slice-system path must stay denied"
    abs_path = str(operator_project / ".slice-system" / "docs" / "roadmap.md")
    code, _ = _run_hook(_write(abs_path), operator_project)
    assert code == 2, "absolute .slice-system path must stay denied"


def test_malformed_envelope_fails_closed_blocking(operator_project):
    (operator_project / ".claude" / "active-envelope.yaml").write_text(
        "mode: [unclosed\n"
    )
    code, stderr = _run_hook(_write("docs/x.md"), operator_project)
    assert code == 2, (
        f"malformed envelope must fail closed AND blocking; got rc={code} "
        f"stderr={stderr!r}"
    )


def test_role_deny_is_blocking_exit_2(tmp_path):
    code, stderr = _run_hook(_write("src/outside.py"), tmp_path, role="phase-1-tdd")
    assert code == 2, f"role-path deny must exit 2; got rc={code} stderr={stderr!r}"


def test_role_absolute_in_allowlist_path_allowed(tmp_path):
    abs_path = str(tmp_path / ".claude" / "skill-runs" / "feat" / "intent.md")
    code, stderr = _run_hook(_write(abs_path), tmp_path, role="phase-1-tdd")
    assert code == 0, (
        f"absolute path inside phase-1-tdd allowlist must be allowed; "
        f"got rc={code} stderr={stderr!r}"
    )


def test_unknown_role_is_blocking_exit_2(tmp_path):
    code, stderr = _run_hook(_write("docs/x.md"), tmp_path, role="not-a-role")
    assert code == 2, f"unknown role must exit 2; got rc={code} stderr={stderr!r}"
