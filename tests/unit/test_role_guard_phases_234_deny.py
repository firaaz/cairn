"""Phase 2 RED — compression/lever-Z-substrate-full-pipeline §S6.

Asserts ``checks/role_guard.py`` extends ``ROLE_DENY_READ`` from
``{phase-1-writer}`` to ``{phase-1-writer, phase-2-skeptic,
phase-3-implementer, phase-4-integrator}`` — each mapped to the same six
canonical-knowledge path patterns. Per intent §S1 / ADR
``cairn-substrate-and-fastmcp`` D8 (second-stage rollout).

D1-D7 mirror the test-driving pattern of
``tests/unit/test_role_guard_grep_glob_deny.py`` (Slice-2-fixup):
subprocess invocation of ``checks/role_guard.py`` with JSON ``tool_input``
on stdin, exit-code + stderr-substring assertions. The three new role keys
are exercised parametrically.

  D1 — Read on locked-down path is denied (rc=1, role+path in stderr).
  D2 — Grep on locked-down path is denied (rc=1).
  D3 — Glob on locked-down path is denied (rc=1).
  D4 — Bash with deny-path token denied (rc=1, _bash_path_tokens propagation).
  D5 — Envelope-grant escape allows (rc=0, one log line appended).
  D6 — Non-locked path is allowed (rc=0, no diagnostic, no log entry).
  D7 — Cross-role isolation: phase-1-writer still in ROLE_DENY_READ after
       this slice (smoke; G1-G7 of test_role_guard_grep_glob_deny.py own
       the full phase-1-writer behavior surface).

Expected at Phase 2: D1-D6 FAIL for all three new roles (the role keys are
not in ``ROLE_DENY_READ`` yet, so role_guard takes the ``unknown role``
branch on writes and the no-op branch on reads). D7 PASSES already
(phase-1-writer is in the table today).
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = CAIRN_ROOT / "checks" / "role_guard.py"
GRANT_LOG = CAIRN_ROOT / ".claude" / "envelope-grants.log"

NEW_ROLES = ["phase-2-skeptic", "phase-3-implementer", "phase-4-integrator"]

# A path that MUST be in ROLE_DENY_READ for every role under test.
DENY_PATH = "docs/ARCHITECTURE.md"
# A path outside any deny pattern.
ALLOW_PATH = "tests/unit/test_role_guard_phases_234_deny.py"


# ---------------------------------------------------------------------------
# Subprocess helpers (lifted from test_role_guard_grep_glob_deny.py)
# ---------------------------------------------------------------------------


def _backup_grant_log() -> str | None:
    return GRANT_LOG.read_text() if GRANT_LOG.exists() else None


def _restore_grant_log(snapshot: str | None) -> None:
    if snapshot is None:
        if GRANT_LOG.exists():
            GRANT_LOG.unlink()
    else:
        GRANT_LOG.write_text(snapshot)


def _run_hook(payload: dict, role: str | None, envelope: str | None = None):
    env = {
        k: v for k, v in os.environ.items() if k not in {"AGENT_ROLE", "AGENT_ENVELOPE"}
    }
    if role is not None:
        env["AGENT_ROLE"] = role
    if envelope is not None:
        env["AGENT_ENVELOPE"] = envelope
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        cwd=CAIRN_ROOT,
    )
    return proc.returncode, proc.stderr


# ---------------------------------------------------------------------------
# D1 — Read on locked-down path → deny
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("role", NEW_ROLES)
def test_d1_read_on_locked_down_path_denied(role):
    """intent §S6 D1 — Read on docs/ARCHITECTURE.md denied for new roles."""
    snapshot = _backup_grant_log()
    try:
        code, stderr = _run_hook(
            {
                "tool_name": "Read",
                "tool_input": {"file_path": DENY_PATH},
            },
            role=role,
        )
        assert code == 1, (
            f"intent §S6 D1 — Read on {DENY_PATH} must deny for {role}; "
            f"got rc={code} stderr={stderr!r}. "
            f"ROLE_DENY_READ must include '{role}'."
        )
        assert role in stderr, (
            f"deny diagnostic must name role '{role}'; stderr={stderr!r}"
        )
        assert DENY_PATH in stderr, f"deny diagnostic must name path; stderr={stderr!r}"
    finally:
        _restore_grant_log(snapshot)


# ---------------------------------------------------------------------------
# D2 — Grep on locked-down path → deny
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("role", NEW_ROLES)
def test_d2_grep_on_locked_down_path_denied(role):
    """intent §S6 D2 — Grep on canonical knowledge denied for new roles."""
    snapshot = _backup_grant_log()
    try:
        code, stderr = _run_hook(
            {
                "tool_name": "Grep",
                "tool_input": {"pattern": "INV-010", "path": DENY_PATH},
            },
            role=role,
        )
        assert code == 1, (
            f"intent §S6 D2 — Grep on {DENY_PATH} must deny for {role}; "
            f"got rc={code} stderr={stderr!r}"
        )
        assert role in stderr, stderr
        assert DENY_PATH in stderr, stderr
    finally:
        _restore_grant_log(snapshot)


# ---------------------------------------------------------------------------
# D3 — Glob on locked-down path → deny
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("role", NEW_ROLES)
def test_d3_glob_on_locked_down_path_denied(role):
    """intent §S6 D3 — Glob rooted at docs/adr/ denied for new roles."""
    snapshot = _backup_grant_log()
    try:
        code, stderr = _run_hook(
            {
                "tool_name": "Glob",
                "tool_input": {"pattern": "**/*.md", "path": "docs/adr"},
            },
            role=role,
        )
        assert code == 1, (
            f"intent §S6 D3 — Glob on docs/adr must deny for {role}; "
            f"got rc={code} stderr={stderr!r}"
        )
        assert role in stderr, stderr
        assert "docs/adr" in stderr, stderr
    finally:
        _restore_grant_log(snapshot)


# ---------------------------------------------------------------------------
# D4 — Bash with deny-path token → deny
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("role", NEW_ROLES)
def test_d4_bash_with_deny_path_token_denied(role):
    """intent §S6 D4 — `cat docs/ARCHITECTURE.md` denied via _bash_path_tokens."""
    snapshot = _backup_grant_log()
    try:
        code, stderr = _run_hook(
            {
                "tool_name": "Bash",
                "tool_input": {"command": f"cat {DENY_PATH}"},
            },
            role=role,
        )
        assert code == 1, (
            f"intent §S6 D4 — Bash `cat {DENY_PATH}` must deny for {role}; "
            f"got rc={code} stderr={stderr!r}. "
            f"_bash_path_tokens already extracts the path; the deny gate "
            f"keys on `role in ROLE_DENY_READ`."
        )
        assert role in stderr, stderr
        assert DENY_PATH in stderr, stderr
    finally:
        _restore_grant_log(snapshot)


# ---------------------------------------------------------------------------
# D5 — envelope-grant escape allows + logs
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("role", NEW_ROLES)
def test_d5_envelope_grant_allows_and_logs(role):
    """intent §S6 D5 / ADR D9 — object-shape envelope grants Read on locked
    path, appends one line to .claude/envelope-grants.log.
    """
    snapshot = _backup_grant_log()
    try:
        if GRANT_LOG.exists():
            GRANT_LOG.unlink()
        envelope = json.dumps(
            {
                "paths": [r"^docs/ARCHITECTURE\.md$"],
                "cairn_query_snapshot": "deadbeef",
            }
        )
        code, stderr = _run_hook(
            {
                "tool_name": "Read",
                "tool_input": {"file_path": DENY_PATH},
            },
            role=role,
            envelope=envelope,
        )
        assert code == 0, (
            f"intent §S6 D5 — envelope grant must allow Read on {DENY_PATH} "
            f"for {role}; got rc={code} stderr={stderr!r}"
        )
        assert GRANT_LOG.exists(), (
            "intent §S6 D5 — envelope grant must append to envelope-grants.log"
        )
        lines = [ln for ln in GRANT_LOG.read_text().splitlines() if ln.strip()]
        assert len(lines) == 1, f"expected exactly one grant line; got {lines!r}"
        line = lines[0]
        assert DENY_PATH in line, line
        assert role in line, f"grant log line must record role '{role}'; got {line!r}"
    finally:
        _restore_grant_log(snapshot)


# ---------------------------------------------------------------------------
# D6 — non-locked path → allow (no diagnostic, no log entry)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("role", NEW_ROLES)
def test_d6_non_locked_path_allowed(role):
    """intent §S6 D6 — Read of a non-deny path is allowed; no log mutation.

    Note: phase-2-skeptic and phase-4-integrator have explicit ROLE_POLICIES
    entries in role_guard.py. phase-3-implementer goes through the
    envelope-write branch. None of these gate Read-class operations on
    non-deny paths — those return rc=0 from the read-class branch with no
    side effects.
    """
    snapshot = _backup_grant_log()
    try:
        if GRANT_LOG.exists():
            GRANT_LOG.unlink()
        code, stderr = _run_hook(
            {
                "tool_name": "Read",
                "tool_input": {"file_path": ALLOW_PATH},
            },
            role=role,
        )
        assert code == 0, (
            f"intent §S6 D6 — Read of non-deny path {ALLOW_PATH} must allow "
            f"for {role}; got rc={code} stderr={stderr!r}"
        )
        assert stderr == "", (
            f"intent §S6 D6 — non-deny Read must emit no diagnostic; "
            f"got stderr={stderr!r}"
        )
        assert not GRANT_LOG.exists() or GRANT_LOG.read_text() == "", (
            "intent §S6 D6 — non-deny Read must not touch grant log"
        )
    finally:
        _restore_grant_log(snapshot)


# ---------------------------------------------------------------------------
# D7 — cross-role isolation: phase-1-writer still in ROLE_DENY_READ
# ---------------------------------------------------------------------------


def test_d7_phase_1_writer_still_in_role_deny_read():
    """intent §S6 D7 — Slice 3 widens the ROLE_DENY_READ key set; it must
    NOT remove or alter phase-1-writer.

    Smoke-level cross-role isolation: full phase-1-writer behavior coverage
    lives in tests/unit/test_role_guard_grep_glob_deny.py (G1-G7); this
    test asserts only that the key is still present and still maps to the
    six canonical-knowledge patterns. (Pattern-set equality across all four
    roles is implicit in S1's "byte-identical pattern lists" requirement
    and is asserted here.)
    """
    spec = importlib.util.spec_from_file_location("role_guard_under_test", HOOK)
    assert spec and spec.loader
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)

    assert "phase-1-writer" in rg.ROLE_DENY_READ, (
        "intent §S6 D7 — phase-1-writer must remain in ROLE_DENY_READ "
        "after Slice 3's widening; got keys="
        f"{sorted(rg.ROLE_DENY_READ.keys())!r}"
    )
    # All four roles must map to the same six patterns (intent §S1).
    expected_keys = {
        "phase-1-writer",
        "phase-2-skeptic",
        "phase-3-implementer",
        "phase-4-integrator",
    }
    assert set(rg.ROLE_DENY_READ.keys()) >= expected_keys, (
        f"intent §S1 — ROLE_DENY_READ must contain all four phase roles; "
        f"got {sorted(rg.ROLE_DENY_READ.keys())!r}"
    )
    p1_patterns = list(rg.ROLE_DENY_READ["phase-1-writer"])
    for role in expected_keys:
        assert list(rg.ROLE_DENY_READ[role]) == p1_patterns, (
            f"intent §S1 — {role} must map to the same six patterns as "
            f"phase-1-writer; got {rg.ROLE_DENY_READ[role]!r}"
        )
