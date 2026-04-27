"""Phase 2 RED — V2 of compression/slice-1-foundation intent.md.

Asserts `.claude/settings.json` registers `checks/role_guard.py` as a
PreToolUse hook with matcher `Write|Edit|MultiEdit|NotebookEdit`, and
that the hook itself no-ops when AGENT_ROLE is unset (compat preserved
per intent.md:54 and compression-infrastructure-bootstrap D1).

At Phase 2 this test is RED because `.claude/settings.json` does not
yet register the hook. Phase 3 makes it GREEN.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
SETTINGS = CAIRN_ROOT / ".claude" / "settings.json"
HOOK = CAIRN_ROOT / "checks" / "role_guard.py"


def _load_settings():
    return json.loads(SETTINGS.read_text())


def _role_guard_pretooluse_entries(settings):
    """Return PreToolUse entries whose command path points at role_guard.py."""
    out = []
    for entry in settings.get("hooks", {}).get("PreToolUse", []):
        for hook in entry.get("hooks", []):
            cmd = hook.get("command", "") or ""
            if "role_guard.py" in cmd:
                out.append((entry, hook))
    return out


# --- V2a — hook registered with correct matcher ---------------------------


def test_v2_role_guard_registered_as_pretooluse():
    settings = _load_settings()
    entries = _role_guard_pretooluse_entries(settings)
    assert entries, (
        "intent.md:54/V2 — .claude/settings.json must register role_guard.py as a "
        "PreToolUse hook; no entry with 'role_guard.py' in command found."
    )


def test_v2_role_guard_matcher_covers_all_write_tools():
    settings = _load_settings()
    entries = _role_guard_pretooluse_entries(settings)
    assert entries, "role_guard.py hook not registered (see sibling test)"
    entry, _hook = entries[0]
    matcher = entry.get("matcher", "") or ""
    required = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
    present = set(re.split(r"\s*\|\s*", matcher)) if matcher else set()
    missing = required - present
    assert not missing, (
        f"intent.md:54/V2 — PreToolUse matcher must cover {sorted(required)}; "
        f"missing {sorted(missing)} (got matcher={matcher!r})"
    )


def test_v2_role_guard_command_resolves_via_slice_system():
    """Per compression-infrastructure-bootstrap and CLAUDE.md (canonical paths),
    hook command must resolve through `$CLAUDE_PROJECT_DIR/.slice-system/checks/role_guard.py`.
    """
    settings = _load_settings()
    entries = _role_guard_pretooluse_entries(settings)
    assert entries
    _entry, hook = entries[0]
    cmd = hook.get("command", "") or ""
    assert "$CLAUDE_PROJECT_DIR" in cmd, (
        f"Hook command must reference $CLAUDE_PROJECT_DIR for symlink resolution; got {cmd!r}"
    )
    assert ".slice-system/checks/role_guard.py" in cmd, (
        f"Hook command must invoke .slice-system/checks/role_guard.py; got {cmd!r}"
    )


# --- V2b — sample tool-call JSON no-ops when AGENT_ROLE unset ------------


def test_v2_hook_noops_when_agent_role_unset():
    """intent.md:54 — hook MUST no-op when AGENT_ROLE is unset so non-
    compressed slices are unaffected (role_guard.py:60-62 contract)."""
    assert HOOK.exists(), "checks/role_guard.py must exist"
    payload = json.dumps(
        {"tool_name": "Write", "tool_input": {"file_path": "src/main.py"}}
    )
    env = {k: v for k, v in os.environ.items() if k != "AGENT_ROLE"}
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        text=True,
        capture_output=True,
        env=env,
        cwd=CAIRN_ROOT,
    )
    assert proc.returncode == 0, (
        f"Hook must exit 0 when AGENT_ROLE unset; got rc={proc.returncode} "
        f"stderr={proc.stderr!r}"
    )
