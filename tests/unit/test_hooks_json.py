"""RED tests for cairn-m5-f1-packaging A6 — hooks manifest (D4).

Pins:
- A6 — Canonical `.claude-plugin/hooks-template.json` exists; `build_dist`
  copies it to `dist/hooks/hooks.json`. Both must register PreToolUse +
  PostToolUse entries with `${CLAUDE_PLUGIN_ROOT}` substitution and must
  NOT contain the legacy `$CLAUDE_PROJECT_DIR/.slice-system/` literal.

Both surfaces (canonical source AND post-build artefact) are asserted per
the operator-confirmed envelope amendment landed at SHA e18dfd7.

Tests must FAIL at HEAD because:
- `.claude-plugin/hooks-template.json` does not exist.
- `scripts/build_dist.py` does not exist.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOKS_TEMPLATE_PATH = REPO_ROOT / ".claude-plugin" / "hooks-template.json"
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_dist.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_entries(data: dict, event_key: str, matcher_substr: str) -> list[dict]:
    """Return entries under `data[event_key]` whose `matcher` string contains
    `matcher_substr` as a substring (handles the `Bash|Edit|Write`-style alt).
    """
    entries = data.get(event_key) or []
    return [e for e in entries if matcher_substr in (e.get("matcher") or "")]


def _all_command_strings(data: dict) -> list[str]:
    """Return every `command` string across PreToolUse + PostToolUse hooks."""
    out: list[str] = []
    for evt in ("PreToolUse", "PostToolUse"):
        for entry in data.get(evt) or []:
            for hook in entry.get("hooks") or []:
                cmd = hook.get("command")
                if isinstance(cmd, str):
                    out.append(cmd)
    return out


def _assert_hooks_manifest_shape(data: dict, label: str) -> None:
    """Shared shape assertions for both canonical and built hooks.json."""
    # PreToolUse: Bash|Edit|Write -> reversibility-guard.sh
    rev_entries = _find_entries(data, "PreToolUse", "Bash")
    assert rev_entries, (
        f"A6 [{label}]: PreToolUse must contain a matcher with 'Bash' "
        f"(for reversibility-guard.sh)"
    )
    rev_cmd = " ".join(
        h.get("command", "")
        for entry in rev_entries
        for h in (entry.get("hooks") or [])
    )
    assert "reversibility-guard.sh" in rev_cmd, (
        f"A6 [{label}]: Bash matcher must route to reversibility-guard.sh; "
        f"got command={rev_cmd!r}"
    )
    assert "${CLAUDE_PLUGIN_ROOT}" in rev_cmd, (
        f"A6 [{label}]: reversibility-guard.sh path must be prefixed by "
        f"${{CLAUDE_PLUGIN_ROOT}}; got {rev_cmd!r}"
    )

    # PreToolUse: Write|Edit|MultiEdit|NotebookEdit -> role_guard.py
    role_entries = _find_entries(data, "PreToolUse", "MultiEdit")
    assert role_entries, (
        f"A6 [{label}]: PreToolUse must contain a matcher with 'MultiEdit' "
        f"(for role_guard.py)"
    )
    role_cmd = " ".join(
        h.get("command", "")
        for entry in role_entries
        for h in (entry.get("hooks") or [])
    )
    assert "role_guard.py" in role_cmd, (
        f"A6 [{label}]: MultiEdit matcher must route to role_guard.py; got {role_cmd!r}"
    )
    assert "${CLAUDE_PLUGIN_ROOT}" in role_cmd, (
        f"A6 [{label}]: role_guard.py path must be prefixed by "
        f"${{CLAUDE_PLUGIN_ROOT}}; got {role_cmd!r}"
    )

    # PostToolUse: Edit|Write -> reality-check.sh
    real_entries = data.get("PostToolUse") or []
    assert real_entries, f"A6 [{label}]: PostToolUse must declare at least one entry"
    edit_entries = [
        e
        for e in real_entries
        if "Edit" in (e.get("matcher") or "") or "Write" in (e.get("matcher") or "")
    ]
    assert edit_entries, (
        f"A6 [{label}]: PostToolUse must contain a matcher routing Edit|Write"
    )
    real_cmd = " ".join(
        h.get("command", "")
        for entry in edit_entries
        for h in (entry.get("hooks") or [])
    )
    assert "reality-check.sh" in real_cmd, (
        f"A6 [{label}]: Edit|Write PostToolUse matcher must route to "
        f"reality-check.sh; got {real_cmd!r}"
    )
    assert "${CLAUDE_PLUGIN_ROOT}" in real_cmd, (
        f"A6 [{label}]: reality-check.sh must be prefixed by "
        f"${{CLAUDE_PLUGIN_ROOT}}; got {real_cmd!r}"
    )


def _assert_no_legacy_slice_system_paths(data: dict, label: str) -> None:
    """No hook command may contain `$CLAUDE_PROJECT_DIR/.slice-system/`."""
    for cmd in _all_command_strings(data):
        assert "$CLAUDE_PROJECT_DIR/.slice-system/" not in cmd, (
            f"A6 [{label}]: legacy $CLAUDE_PROJECT_DIR/.slice-system/ literal "
            f"must not appear in any hook command; got {cmd!r}"
        )


# ---------------------------------------------------------------------------
# A6 — Canonical source `.claude-plugin/hooks-template.json`
# ---------------------------------------------------------------------------


def test_a6_canonical_hooks_template_exists_and_parses():
    assert HOOKS_TEMPLATE_PATH.is_file(), (
        f"A6: canonical hooks template missing at {HOOKS_TEMPLATE_PATH}"
    )
    data = json.loads(HOOKS_TEMPLATE_PATH.read_text())
    assert isinstance(data, dict), "A6: hooks-template.json top-level must be an object"


def test_a6_canonical_hooks_template_full_shape():
    data = json.loads(HOOKS_TEMPLATE_PATH.read_text())
    _assert_hooks_manifest_shape(data, "canonical")


def test_a6_canonical_hooks_template_no_legacy_slice_system():
    data = json.loads(HOOKS_TEMPLATE_PATH.read_text())
    _assert_no_legacy_slice_system_paths(data, "canonical")


# ---------------------------------------------------------------------------
# A6 — Built artefact `dist/hooks/hooks.json` (post-build)
# ---------------------------------------------------------------------------


def _run_build_into(tmp_path: Path) -> None:
    if not BUILD_SCRIPT.is_file():
        pytest.fail(f"A6: build_dist.py not found at {BUILD_SCRIPT}")
    dist_root = tmp_path / "dist"
    proc = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "--repo-root",
            str(REPO_ROOT),
            "--dist-root",
            str(dist_root),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, (
        f"A6: build_dist.py failed rc={proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )


def test_a6_built_hooks_json_exists(tmp_path):
    _run_build_into(tmp_path)
    built = tmp_path / "dist" / "hooks" / "hooks.json"
    assert built.is_file(), f"A6: built hooks.json not found at {built}"


def test_a6_built_hooks_json_full_shape(tmp_path):
    _run_build_into(tmp_path)
    built = tmp_path / "dist" / "hooks" / "hooks.json"
    data = json.loads(built.read_text())
    _assert_hooks_manifest_shape(data, "built")


def test_a6_built_hooks_json_no_legacy_slice_system(tmp_path):
    _run_build_into(tmp_path)
    built = tmp_path / "dist" / "hooks" / "hooks.json"
    data = json.loads(built.read_text())
    _assert_no_legacy_slice_system_paths(data, "built")


def test_a6_built_hooks_json_equals_canonical_template(tmp_path):
    """The built artefact is a byte-for-byte copy of the canonical template."""
    _run_build_into(tmp_path)
    built = tmp_path / "dist" / "hooks" / "hooks.json"
    canonical = json.loads(HOOKS_TEMPLATE_PATH.read_text())
    assert json.loads(built.read_text()) == canonical, (
        "A6: built dist/hooks/hooks.json must equal canonical "
        ".claude-plugin/hooks-template.json"
    )
