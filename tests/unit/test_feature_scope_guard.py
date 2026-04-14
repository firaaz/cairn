"""Phase 2 validation tests for SLICE-009 — scope-guard feature file access.

Verifies intent.md V6: writes to .claude/features/*.yaml are allowed by
checks/scope-guard.sh regardless of slice phase.

Two layers:
  1. Source inspection — the always-allowed path list includes the pattern.
  2. Subprocess — piping a Write tool-input for a feature file path returns
     exit 0 (allowed).

FAILS until Phase 3 modifies scope-guard.sh.

Pytest + stdlib only.
"""

import json
import subprocess
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
SCOPE_GUARD = CAIRN_ROOT / "checks" / "scope-guard.sh"


# --- V6: Source contains .claude/features/ in always-allowed paths -----------


class TestScopeGuardSource:
    def test_scope_guard_exists(self):
        assert SCOPE_GUARD.is_file(), f"{SCOPE_GUARD} does not exist"

    def test_always_allowed_includes_features_path(self):
        """scope-guard.sh must include .claude/features/ in its always-allowed
        write paths, same category as .claude/current-slice/, .claude/handoff.md,
        .claude/sweep.yaml (intent.md scope-guard update)."""
        text = SCOPE_GUARD.read_text()
        # The pattern should appear in the source — could be a glob, regex,
        # or string match. We check for the path fragment.
        assert ".claude/features/" in text or "features/" in text, (
            "scope-guard.sh does not contain .claude/features/ in always-allowed paths"
        )


# --- V6: Subprocess — scope-guard allows Write to feature file ---------------


class TestScopeGuardSubprocess:
    def _run_scope_guard(
        self, tool_name: str, tool_input: dict
    ) -> subprocess.CompletedProcess:
        """Run scope-guard.sh with the given tool invocation JSON on stdin."""
        payload = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
        return subprocess.run(
            ["bash", str(SCOPE_GUARD)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(CAIRN_ROOT),
        )

    def test_write_feature_file_allowed(self):
        """scope-guard.sh must allow Write to .claude/features/<id>.yaml."""
        result = self._run_scope_guard(
            "Write",
            {
                "file_path": ".claude/features/test-feature.yaml",
                "content": "id: test-feature\nintent: test\ncreated: 2026-04-14\n",
            },
        )
        assert result.returncode == 0, (
            f"scope-guard blocked Write to .claude/features/test-feature.yaml: "
            f"exit={result.returncode}, stderr={result.stderr}"
        )

    def test_edit_feature_file_allowed(self):
        """scope-guard.sh must allow Edit to .claude/features/<id>.yaml."""
        result = self._run_scope_guard(
            "Edit",
            {
                "file_path": ".claude/features/test-feature.yaml",
                "old_string": "intent: old",
                "new_string": "intent: new",
            },
        )
        assert result.returncode == 0, (
            f"scope-guard blocked Edit to .claude/features/test-feature.yaml: "
            f"exit={result.returncode}, stderr={result.stderr}"
        )
