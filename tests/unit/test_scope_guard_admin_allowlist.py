"""Phase 2 validation for substrate/papercut-bundle paper-cut #1.

Asserts that ``checks/scope-guard.sh``'s admin-allowlist accepts
``.claude/d1-bypasses.log`` and ``.claude/d3-bypasses.log`` regardless of
the active slice envelope — i.e. Write/Edit hook events on those
append-only bypass logs exit 0 without ``EXPAND_ENVELOPE=1`` and without
a Bash-heredoc bypass.

Two layers per existing precedent (``test_feature_scope_guard.py``):
  1. Source inspection — the always-allowed ``case`` arm enumerates both
     log paths.
  2. Subprocess — synthetic Write hook input under a tight slice
     envelope that explicitly excludes the bypass logs returns exit 0.

RED until Phase 3 widens the ``case`` statement at scope-guard.sh:60.

Pytest + stdlib only.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
SCOPE_GUARD = CAIRN_ROOT / "checks" / "scope-guard.sh"

BYPASS_LOG_PATHS = [".claude/d1-bypasses.log", ".claude/d3-bypasses.log"]


# --- Source inspection -------------------------------------------------------


class TestScopeGuardSource:
    def test_scope_guard_exists(self) -> None:
        assert SCOPE_GUARD.is_file(), f"{SCOPE_GUARD} does not exist"

    @pytest.mark.parametrize("log_path", BYPASS_LOG_PATHS)
    def test_admin_allowlist_lists_bypass_log(self, log_path: str) -> None:
        """The admin-allowlist case statement must enumerate both bypass
        log paths so they are exempt from envelope enforcement."""
        text = SCOPE_GUARD.read_text(encoding="utf-8")
        assert log_path in text, (
            f"scope-guard.sh admin-allowlist must reference {log_path!r} "
            f"(intent paper-cut #1)"
        )


# --- Subprocess: synthetic envelope EXCLUDES the bypass logs -----------------


def _write_synthetic_slice(root: Path) -> None:
    """Create a `.claude/current-slice/` whose envelope deliberately
    excludes the bypass logs. This forces scope-guard to fall through
    envelope-pattern matching and rely solely on the admin-allowlist."""
    slice_dir = root / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True, exist_ok=True)
    (slice_dir / "intent.md").write_text(
        "---\n"
        "slice: synthetic/papercut-fixture\n"
        "envelope:\n"
        '  - "src/unrelated/module.py"\n'
        "---\n\n"
        "# fixture\n",
        encoding="utf-8",
    )
    (slice_dir / "slice.yaml").write_text(
        "id: synthetic/papercut-fixture\n"
        "name: synthetic\n"
        "status: in-progress\n"
        "current_phase: 3\n",
        encoding="utf-8",
    )


def _run_scope_guard(
    project_root: Path, tool_name: str, tool_input: dict
) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    env = {
        "PATH": __import__("os").environ.get("PATH", ""),
        "CLAUDE_PROJECT_DIR": str(project_root),
    }
    return subprocess.run(
        ["bash", str(SCOPE_GUARD)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(project_root),
        env=env,
    )


class TestScopeGuardSubprocess:
    @pytest.mark.parametrize("log_path", BYPASS_LOG_PATHS)
    def test_write_bypass_log_exits_zero_under_excluding_envelope(
        self, tmp_path: Path, log_path: str
    ) -> None:
        """Write to .claude/d{1,3}-bypasses.log must be admin-allowed
        even when the active slice envelope excludes it. No
        EXPAND_ENVELOPE override is set in this fixture."""
        _write_synthetic_slice(tmp_path)
        result = _run_scope_guard(
            tmp_path,
            "Write",
            {
                "file_path": str(tmp_path / log_path),
                "content": "2026-05-02T00:00:00Z bypass entry\n",
            },
        )
        assert result.returncode == 0, (
            f"scope-guard blocked Write to {log_path}: "
            f"exit={result.returncode} stderr={result.stderr!r}"
        )

    @pytest.mark.parametrize("log_path", BYPASS_LOG_PATHS)
    def test_edit_bypass_log_exits_zero_under_excluding_envelope(
        self, tmp_path: Path, log_path: str
    ) -> None:
        """Edit on the bypass logs must be admin-allowed for the same
        reason (append-only audit logs are operator-managed)."""
        _write_synthetic_slice(tmp_path)
        result = _run_scope_guard(
            tmp_path,
            "Edit",
            {
                "file_path": str(tmp_path / log_path),
                "old_string": "old",
                "new_string": "new",
            },
        )
        assert result.returncode == 0, (
            f"scope-guard blocked Edit to {log_path}: "
            f"exit={result.returncode} stderr={result.stderr!r}"
        )
