"""Envelope-grant coverage for the post-M4 role_guard.py.

Restores coverage that test_role_guard_envelope_grant.py and
test_role_guard_envelope_json.py provided pre-D2. Per M3 bathwater audit §8,
the envelope-grant mechanism (`_envelope_patterns` three input shapes +
`_log_grant` audit trail) is required carry-forward; only the dying
read-class lockdown was supposed to be deleted.

Slug fixtures ported from legacy phase-1-writer / phase-3-implementer to the
canonical phase-1-tdd / phase-3-tdd; paths ported from .claude/current-slice/
to .claude/skill-runs/<feature>/.

Surface tested:
- _envelope_patterns: JSON-array, JSON-object-with-paths, legacy colon-split
  (with stderr deprecation warning).
- Empty / unset envelope returns no patterns.
- Phase-3-tdd envelope-driven grant + deny (already covered in
  test_role_guard_post_m4.py — not duplicated here).
- Static-policy roles (phase-1-tdd) get envelope-grant escape via D9 with
  audit-log line written exactly once.
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
GRANT_LOG = CAIRN_ROOT / ".claude" / "envelope-grants.log"


def _backup_grant_log() -> str | None:
    return GRANT_LOG.read_text() if GRANT_LOG.exists() else None


def _restore_grant_log(snapshot: str | None) -> None:
    if snapshot is None:
        if GRANT_LOG.exists():
            GRANT_LOG.unlink()
    else:
        GRANT_LOG.write_text(snapshot)


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


def _import_role_guard():
    spec = importlib.util.spec_from_file_location("role_guard_under_test", HOOK)
    assert spec and spec.loader
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    return rg


# ---------------------------------------------------------------------------
# _envelope_patterns shape parsing — direct module call (no subprocess)
# ---------------------------------------------------------------------------


def test_envelope_patterns_json_array_shape():
    """JSON-array envelope round-trips unchanged through _envelope_patterns."""
    rg = _import_role_guard()
    patterns = rg._envelope_patterns(json.dumps([r"^scripts/a\.py$", r"^tests/"]))
    assert patterns == [r"^scripts/a\.py$", r"^tests/"], (
        f"array-shape envelope must round-trip unchanged; got {patterns!r}"
    )


def test_envelope_patterns_json_object_with_paths_shape():
    """JSON-object-with-paths envelope returns the paths array."""
    rg = _import_role_guard()
    raw = json.dumps(
        {
            "paths": [r"^src/foo\.py$", r"^src/bar\.py$"],
            "cairn_query_snapshot": "deadbeef",
        }
    )
    patterns = rg._envelope_patterns(raw)
    assert patterns == [r"^src/foo\.py$", r"^src/bar\.py$"], (
        f"object-shape envelope must return paths array; got {patterns!r}"
    )


def test_envelope_patterns_legacy_colon_split_shape():
    """Non-JSON colon-separated envelope falls back to legacy split."""
    rg = _import_role_guard()
    legacy = r"^scripts/a\.py$:^tests/b\.py$"
    patterns = rg._envelope_patterns(legacy)
    assert patterns == [r"^scripts/a\.py$", r"^tests/b\.py$"], (
        f"legacy colon-split must yield two patterns; got {patterns!r}"
    )


def test_envelope_patterns_empty_returns_empty_list():
    """Unset (None) envelope yields an empty pattern list."""
    rg = _import_role_guard()
    assert rg._envelope_patterns(None) == []
    assert rg._envelope_patterns("") == []


# ---------------------------------------------------------------------------
# JSON-array envelope shape — write-path grant + audit log (subprocess)
# ---------------------------------------------------------------------------


def test_json_array_envelope_grants_write_on_static_role_and_logs():
    """phase-1-tdd writing outside its static allowlist but matching the
    envelope (D9 escape) is granted and produces exactly one grant-log line.
    """
    snapshot = _backup_grant_log()
    try:
        if GRANT_LOG.exists():
            GRANT_LOG.unlink()
        envelope = json.dumps([r"^src/foo\.py$"])
        code, stderr = _run_hook(
            {"tool_name": "Write", "tool_input": {"file_path": "src/foo.py"}},
            role="phase-1-tdd",
            envelope=envelope,
        )
        assert code == 0, (
            f"D9 envelope escape must allow phase-1-tdd write outside static "
            f"allowlist; got rc={code} stderr={stderr!r}"
        )
        assert GRANT_LOG.exists(), (
            "envelope grant must append to .claude/envelope-grants.log"
        )
        lines = [ln for ln in GRANT_LOG.read_text().splitlines() if ln.strip()]
        assert len(lines) == 1, f"expected exactly one grant line; got {lines!r}"
        line = lines[0]
        assert "src/foo.py" in line, f"line missing granted path: {line!r}"
        assert "phase-1-tdd" in line, f"line missing granting role: {line!r}"
    finally:
        _restore_grant_log(snapshot)


def test_json_array_envelope_with_colon_in_path():
    """JSON-array envelope handles paths containing `:` (regression vs legacy
    colon-split format).
    """
    snapshot = _backup_grant_log()
    try:
        envelope = json.dumps(["scripts/a:b.py", "tests/c.py"])
        code, stderr = _run_hook(
            {"tool_name": "Write", "tool_input": {"file_path": "scripts/a:b.py"}},
            role="phase-3-tdd",
            envelope=envelope,
        )
        assert code == 0, (
            f"JSON envelope with colon path must allow write for phase-3-tdd; "
            f"stderr={stderr!r}"
        )
    finally:
        _restore_grant_log(snapshot)


# ---------------------------------------------------------------------------
# JSON-object envelope shape — write-path grant via paths key
# ---------------------------------------------------------------------------


def test_json_object_envelope_grants_write_on_static_role():
    """Object-shape envelope's `paths` array drives the D9 grant escape for
    phase-2-tdd writing outside its static allowlist.
    """
    snapshot = _backup_grant_log()
    try:
        if GRANT_LOG.exists():
            GRANT_LOG.unlink()
        envelope = json.dumps(
            {
                "paths": [r"^src/bar\.py$"],
                "cairn_query_snapshot": "deadbeef",
            }
        )
        code, stderr = _run_hook(
            {"tool_name": "Write", "tool_input": {"file_path": "src/bar.py"}},
            role="phase-2-tdd",
            envelope=envelope,
        )
        assert code == 0, (
            f"object-shape envelope must allow phase-2-tdd write outside "
            f"allowlist; got rc={code} stderr={stderr!r}"
        )
        assert GRANT_LOG.exists()
        lines = [ln for ln in GRANT_LOG.read_text().splitlines() if ln.strip()]
        assert len(lines) == 1, f"expected exactly one grant line; got {lines!r}"
        assert "src/bar.py" in lines[0]
        assert "phase-2-tdd" in lines[0]
    finally:
        _restore_grant_log(snapshot)


def test_json_object_envelope_non_matching_denies():
    """Object envelope with no matching path leaves the static-allowlist deny
    in place (no D9 escape fires).
    """
    snapshot = _backup_grant_log()
    try:
        envelope = json.dumps(
            {
                "paths": [r"^src/foo\.py$"],
                "cairn_query_snapshot": "deadbeef",
            }
        )
        code, stderr = _run_hook(
            {"tool_name": "Write", "tool_input": {"file_path": "src/baz.py"}},
            role="phase-1-tdd",
            envelope=envelope,
        )
        assert code == 2, (
            f"object envelope without matching path must deny (blocking); "
            f"got rc={code} stderr={stderr!r}"
        )
    finally:
        _restore_grant_log(snapshot)


# ---------------------------------------------------------------------------
# Legacy colon-separated envelope shape — back-compat + deprecation warning
# ---------------------------------------------------------------------------


def test_legacy_colon_split_envelope_grants_with_warning():
    """Legacy colon-separated envelope still grants matching writes AND emits
    exactly one stderr deprecation warning.
    """
    snapshot = _backup_grant_log()
    try:
        legacy = r"^src/foo\.py$:^src/bar\.py$"
        code, stderr = _run_hook(
            {"tool_name": "Write", "tool_input": {"file_path": "src/foo.py"}},
            role="phase-3-tdd",
            envelope=legacy,
        )
        assert code == 0, (
            f"legacy colon-separated envelope must still allow matching writes "
            f"on phase-3-tdd; stderr={stderr!r}"
        )
        warning_lines = [ln for ln in stderr.splitlines() if "legacy" in ln.lower()]
        assert len(warning_lines) == 1, (
            f"expected exactly one legacy-format warning; got {warning_lines!r}"
        )
        assert "migrate to JSON array" in warning_lines[0], (
            f"deprecation warning must point to JSON-array format; "
            f"got {warning_lines[0]!r}"
        )
    finally:
        _restore_grant_log(snapshot)


# ---------------------------------------------------------------------------
# Empty / unset envelope — no grant
# ---------------------------------------------------------------------------


def test_unset_envelope_does_not_grant_static_role():
    """phase-1-tdd writing outside its static allowlist with no envelope at
    all is denied (no D9 escape, no grant log entry).
    """
    snapshot = _backup_grant_log()
    try:
        if GRANT_LOG.exists():
            GRANT_LOG.unlink()
        code, stderr = _run_hook(
            {"tool_name": "Write", "tool_input": {"file_path": "src/foo.py"}},
            role="phase-1-tdd",
            envelope=None,
        )
        assert code == 2, (
            f"phase-1-tdd outside allowlist with no envelope must deny (blocking); "
            f"got rc={code} stderr={stderr!r}"
        )
        assert not GRANT_LOG.exists() or GRANT_LOG.read_text() == "", (
            "no envelope → no grant log entry"
        )
    finally:
        _restore_grant_log(snapshot)


def test_empty_envelope_does_not_grant_static_role():
    """phase-1-tdd writing outside its static allowlist with empty envelope
    string is denied (envelope-patterns yields []).
    """
    snapshot = _backup_grant_log()
    try:
        if GRANT_LOG.exists():
            GRANT_LOG.unlink()
        code, stderr = _run_hook(
            {"tool_name": "Write", "tool_input": {"file_path": "src/foo.py"}},
            role="phase-1-tdd",
            envelope="",
        )
        assert code == 2, (
            f"phase-1-tdd outside allowlist with empty envelope must deny (blocking); "
            f"got rc={code} stderr={stderr!r}"
        )
    finally:
        _restore_grant_log(snapshot)


# ---------------------------------------------------------------------------
# Phase-3-tdd envelope-driven (already covered in test_role_guard_post_m4.py;
# one extra colon-handling case here to round out the matrix).
# ---------------------------------------------------------------------------


def test_phase_3_tdd_with_object_envelope_grants():
    """phase-3-tdd write gate accepts the object-shape envelope (parity with
    JSON-array shape covered in test_role_guard_post_m4.py).
    """
    envelope = json.dumps({"paths": [r"^src/quux\.py$"]})
    code, stderr = _run_hook(
        {"tool_name": "Write", "tool_input": {"file_path": "src/quux.py"}},
        role="phase-3-tdd",
        envelope=envelope,
    )
    assert code == 0, (
        f"phase-3-tdd object envelope must grant matching path; "
        f"got rc={code} stderr={stderr!r}"
    )
