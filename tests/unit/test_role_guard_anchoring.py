"""RED tests for cairn-m5-f1-packaging A7 — role_guard runtime anchoring (D5).

Pins:
- A7 — `CAIRN_ROOT` resolves from `CLAUDE_PROJECT_DIR` (env), falls back to
  `os.getcwd()` when unset; `OPERATOR_ENVELOPE_PATH` and `_log_grant()`
  inherit the anchoring; `Path(__file__).resolve().parent.parent` is gone.

A8 (regression guard) is verified by Phase 4 re-running the existing
`tests/unit/test_role_guard_envelope.py` and `tests/unit/test_role_guard_post_m4.py`
suites; not duplicated here.

Module loaded via importlib.util.spec_from_file_location (same convention as
test_role_guard_envelope.py / test_role_guard_post_m4.py — `checks/` is
NOT on the project pythonpath; only `scripts/` is).

Tests must FAIL at HEAD because role_guard.py:28 currently uses
`Path(__file__).resolve().parent.parent`, which is anchored on the file's
on-disk location, not on CLAUDE_PROJECT_DIR.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / "checks" / "role_guard.py"


def _import_role_guard():
    """(Re)load role_guard.py fresh — its module-level constants capture env
    state at import time, so each test must reload after mutating env/cwd.
    """
    spec = importlib.util.spec_from_file_location(
        "role_guard_under_test_anchoring", HOOK
    )
    assert spec and spec.loader, f"failed to load spec for {HOOK}"
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    return rg


# ---------------------------------------------------------------------------
# A7.1 — CAIRN_ROOT honours CLAUDE_PROJECT_DIR
# ---------------------------------------------------------------------------


def test_a7_cairn_root_uses_claude_project_dir(tmp_path, monkeypatch):
    """With CLAUDE_PROJECT_DIR set, CAIRN_ROOT == that path."""
    consumer = tmp_path / "some-consumer"
    consumer.mkdir()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(consumer))
    rg = _import_role_guard()
    assert rg.CAIRN_ROOT == Path(str(consumer)), (
        f"A7: CAIRN_ROOT must equal $CLAUDE_PROJECT_DIR; got {rg.CAIRN_ROOT!r}"
    )


def test_a7_operator_envelope_path_under_claude_project_dir(tmp_path, monkeypatch):
    """OPERATOR_ENVELOPE_PATH resolves under CLAUDE_PROJECT_DIR/.claude/."""
    consumer = tmp_path / "consumer-x"
    consumer.mkdir()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(consumer))
    rg = _import_role_guard()
    expected = Path(str(consumer)) / ".claude" / "active-envelope.yaml"
    assert rg.OPERATOR_ENVELOPE_PATH == expected, (
        f"A7: OPERATOR_ENVELOPE_PATH must resolve at "
        f"$CLAUDE_PROJECT_DIR/.claude/active-envelope.yaml; got "
        f"{rg.OPERATOR_ENVELOPE_PATH!r}"
    )


# ---------------------------------------------------------------------------
# A7.2 — Fallback to os.getcwd() when CLAUDE_PROJECT_DIR unset
# ---------------------------------------------------------------------------


def test_a7_cairn_root_falls_back_to_cwd_when_unset(tmp_path, monkeypatch):
    """With CLAUDE_PROJECT_DIR unset, CAIRN_ROOT == os.getcwd()."""
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    rg = _import_role_guard()
    # Resolve symlinks on macOS (/tmp -> /private/tmp).
    assert rg.CAIRN_ROOT.resolve() == tmp_path.resolve(), (
        f"A7: CAIRN_ROOT must fall back to cwd when env unset; "
        f"got {rg.CAIRN_ROOT!r} expected {tmp_path!r}"
    )


# ---------------------------------------------------------------------------
# A7.3 — _log_grant inherits anchoring
# ---------------------------------------------------------------------------


def test_a7_log_grant_writes_under_claude_project_dir(tmp_path, monkeypatch):
    """_log_grant() writes to $CLAUDE_PROJECT_DIR/.claude/envelope-grants.log."""
    consumer = tmp_path / "consumer-log"
    consumer.mkdir()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(consumer))
    rg = _import_role_guard()
    rg._log_grant("foo/bar.py", "phase-3-tdd")
    log = consumer / ".claude" / "envelope-grants.log"
    assert log.is_file(), (
        f"A7: _log_grant must write under $CLAUDE_PROJECT_DIR/.claude/; "
        f"expected {log}, not found"
    )
    line = log.read_text().strip()
    assert "foo/bar.py" in line, f"A7: log line missing path; got {line!r}"
    assert "phase-3-tdd" in line, f"A7: log line missing role; got {line!r}"


# ---------------------------------------------------------------------------
# A7.4 — `Path(__file__).resolve().parent.parent` removed from source
# ---------------------------------------------------------------------------


def test_a7_no_file_anchored_cairn_root_in_source():
    """Static check: `Path(__file__).resolve().parent.parent` is gone from
    role_guard.py source. (Defensive — catches accidental re-introduction
    that an env-based test might miss.)"""
    text = HOOK.read_text()
    assert "Path(__file__).resolve().parent.parent" not in text, (
        "A7: role_guard.py must not anchor CAIRN_ROOT on __file__; "
        "use $CLAUDE_PROJECT_DIR (with cwd fallback)"
    )


def test_a7_source_references_claude_project_dir_env():
    """Static check: the new anchoring uses CLAUDE_PROJECT_DIR env var."""
    text = HOOK.read_text()
    assert "CLAUDE_PROJECT_DIR" in text, (
        "A7: role_guard.py must reference CLAUDE_PROJECT_DIR for anchoring"
    )
