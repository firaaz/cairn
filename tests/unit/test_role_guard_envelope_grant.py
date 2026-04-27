"""Phase 2 RED — compression/lever-Y-mcp-substrate V5.

`checks/role_guard.py` MUST allow Read on a locked-down path when
``AGENT_ENVELOPE`` (object shape: ``{"paths":[…], "cairn_query_snapshot":…}``)
grants the path via its ``paths`` array — AND must append exactly one line
to ``.claude/envelope-grants.log`` recording the grant.

Per intent.md §S4 step 2 + ADR D9.

Expected at Phase 2: FAILS — current `_envelope_patterns` reads only the
JSON-array shape and there is no Read-deny path nor grant-log emission.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = CAIRN_ROOT / "checks" / "role_guard.py"
GRANT_LOG = CAIRN_ROOT / ".claude" / "envelope-grants.log"


def _backup_grant_log():
    if GRANT_LOG.exists():
        return GRANT_LOG.read_text()
    return None


def _restore_grant_log(snapshot):
    if snapshot is None:
        if GRANT_LOG.exists():
            GRANT_LOG.unlink()
    else:
        GRANT_LOG.write_text(snapshot)


def _run_hook(tool_input, role, envelope):
    env = {
        k: v for k, v in os.environ.items() if k not in {"AGENT_ROLE", "AGENT_ENVELOPE"}
    }
    env["AGENT_ROLE"] = role
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


def test_v5_object_envelope_grants_read_on_canonical_path():
    """intent.md §S4 — object-shape envelope with matching `paths` regex
    allows Read on a normally-denied canonical path.
    """
    snapshot = _backup_grant_log()
    try:
        envelope = json.dumps(
            {
                "paths": [r"^docs/ARCHITECTURE\.md$"],
                "cairn_query_snapshot": "deadbeef",
            }
        )
        code, stderr = _run_hook(
            {"tool_name": "Read", "tool_input": {"file_path": "docs/ARCHITECTURE.md"}},
            role="phase-1-writer",
            envelope=envelope,
        )
        assert code == 0, (
            f"envelope grant must allow Read; got rc={code} stderr={stderr!r}"
        )
    finally:
        _restore_grant_log(snapshot)


def test_v5_grant_appends_one_line_to_envelope_grants_log():
    """intent.md §S4 — every grant appends ONE line to envelope-grants.log."""
    snapshot = _backup_grant_log()
    try:
        if GRANT_LOG.exists():
            GRANT_LOG.unlink()

        envelope = json.dumps(
            {
                "paths": [r"^docs/lessons\.md$"],
                "cairn_query_snapshot": "deadbeef",
            }
        )
        code, _ = _run_hook(
            {"tool_name": "Read", "tool_input": {"file_path": "docs/lessons.md"}},
            role="phase-1-writer",
            envelope=envelope,
        )
        assert code == 0
        assert GRANT_LOG.exists(), (
            "intent.md §S4 — grant must append to .claude/envelope-grants.log"
        )
        lines = [ln for ln in GRANT_LOG.read_text().splitlines() if ln.strip()]
        assert len(lines) == 1, f"expected exactly one grant line; got {lines!r}"
        # Format spec: <slice-id> <YYYY-MM-DD> <granted-path> <granting-phase>
        line = lines[0]
        assert "docs/lessons.md" in line, f"line missing granted path: {line!r}"
        assert "phase-1" in line or "phase-1-writer" in line, (
            f"line missing granting phase: {line!r}"
        )
    finally:
        _restore_grant_log(snapshot)


def test_v5_object_envelope_non_matching_still_denies():
    """intent.md §S4 — object envelope with no matching path leaves the
    deny in place.
    """
    snapshot = _backup_grant_log()
    try:
        envelope = json.dumps(
            {
                "paths": [r"^docs/operational-reference\.md$"],
                "cairn_query_snapshot": "deadbeef",
            }
        )
        code, _ = _run_hook(
            {"tool_name": "Read", "tool_input": {"file_path": "docs/ARCHITECTURE.md"}},
            role="phase-1-writer",
            envelope=envelope,
        )
        assert code == 1
    finally:
        _restore_grant_log(snapshot)


def test_v5_legacy_array_envelope_still_round_trips():
    """intent.md §S4 — pre-existing JSON-array envelope shape (phase-3-impl)
    is preserved through `_envelope_patterns` for write-path consumers.
    """
    # Direct module call — the contract is that array-shape envelopes still
    # produce the same pattern list (back-compat).
    sys.path.insert(0, str(CAIRN_ROOT / "checks"))
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("role_guard", HOOK)
        rg = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(rg)
        patterns = rg._envelope_patterns(json.dumps([r"^scripts/a\.py$", r"^tests/"]))
        assert patterns == [r"^scripts/a\.py$", r"^tests/"], (
            f"array-shape envelope must round-trip unchanged; got {patterns!r}"
        )
    finally:
        if str(CAIRN_ROOT / "checks") in sys.path:
            sys.path.remove(str(CAIRN_ROOT / "checks"))
