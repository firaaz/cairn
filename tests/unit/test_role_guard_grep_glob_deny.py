"""Phase 2 RED — compression/lever-Y-mcp-substrate-fixup §S3.

Asserts ``checks/role_guard.py`` extends the read-class deny surface from
{Read} to {Read, Grep, Glob} for ``phase-1-writer``, and that the
phase-1-writer agent's ``tools:`` frontmatter no longer lists Grep/Glob
(defense-in-depth outer gate). Per intent.md §S3, ADR
``cairn-substrate-and-fastmcp`` D8 (structural deny) and D9 (envelope-grant
parity for new read-class tools).

G1-G7 cover:
  G1 — Grep on a ROLE_DENY_READ path is denied for phase-1-writer (rc=1).
  G2 — Glob on a ROLE_DENY_READ path is denied for phase-1-writer (rc=1).
  G3 — Grep with envelope `paths` matching is granted (rc=0, log appended).
  G4 — Glob with envelope `paths` matching is granted (rc=0, log appended).
  G5 — Grep on a non-locked-down path is allowed (rc=0).
  G6 — Grep without `path` argument is allowed (rc=0).
  G7 — Non-phase-1-writer roles are unaffected (rc=0).

Plus frontmatter coverage:
  F1 — phase-1-writer.md `tools:` line drops Grep + Glob.

Expected at Phase 2: FAILS — current ``READ_CLASS_TOOLS = {"Read"}`` and
``phase-1-writer.md`` still lists ``tools: Write, Edit, Grep, Glob``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = CAIRN_ROOT / "checks" / "role_guard.py"
GRANT_LOG = CAIRN_ROOT / ".claude" / "envelope-grants.log"
PHASE_1_WRITER_MD = CAIRN_ROOT / ".claude" / "agents" / "phase-1-writer.md"


# ---------------------------------------------------------------------------
# Hook subprocess helpers (pattern lifted from test_role_guard_envelope_grant)
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
# G1-G2 — Grep/Glob on locked-down path → deny
# ---------------------------------------------------------------------------


def test_g1_grep_on_locked_down_path_denied_for_phase_1_writer():
    """intent §S3 G1 — Grep on docs/ARCHITECTURE.md denied for phase-1-writer.

    The deny check applies to `tool_input.path` (Grep's search root); the
    `pattern` argument is not a path.
    """
    snapshot = _backup_grant_log()
    try:
        code, stderr = _run_hook(
            {
                "tool_name": "Grep",
                "tool_input": {
                    "pattern": "INV-010",
                    "path": "docs/ARCHITECTURE.md",
                },
            },
            role="phase-1-writer",
        )
        assert code == 1, (
            f"intent §S3 G1 — Grep on canonical knowledge must deny; "
            f"got rc={code} stderr={stderr!r}. "
            f"READ_CLASS_TOOLS must include 'Grep'."
        )
        # Diagnostic must name the role and the path (operator-debuggable).
        assert "phase-1-writer" in stderr, (
            f"deny diagnostic must name role; stderr={stderr!r}"
        )
        assert "docs/ARCHITECTURE.md" in stderr, (
            f"deny diagnostic must name path; stderr={stderr!r}"
        )
    finally:
        _restore_grant_log(snapshot)


def test_g2_glob_on_locked_down_path_denied_for_phase_1_writer():
    """intent §S3 G2 — Glob with `path` rooted in deny-list denied."""
    snapshot = _backup_grant_log()
    try:
        code, stderr = _run_hook(
            {
                "tool_name": "Glob",
                "tool_input": {
                    "pattern": "**/*.md",
                    "path": "docs/adr",
                },
            },
            role="phase-1-writer",
        )
        assert code == 1, (
            f"intent §S3 G2 — Glob rooted at docs/adr/ must deny; "
            f"got rc={code} stderr={stderr!r}. "
            f"READ_CLASS_TOOLS must include 'Glob'."
        )
        assert "phase-1-writer" in stderr, stderr
        assert "docs/adr" in stderr, stderr
    finally:
        _restore_grant_log(snapshot)


def test_g1_grep_on_cairn_query_internals_denied():
    """intent §S3 — `^scripts/cairn_query/` deny pattern covers Grep too."""
    snapshot = _backup_grant_log()
    try:
        code, _ = _run_hook(
            {
                "tool_name": "Grep",
                "tool_input": {
                    "pattern": "lookup",
                    "path": "scripts/cairn_query/storage.py",
                },
            },
            role="phase-1-writer",
        )
        assert code == 1, (
            "intent §S3 — Grep on scripts/cairn_query/* must deny "
            "(ADR D8 structural lockdown extends to read-class tools)."
        )
    finally:
        _restore_grant_log(snapshot)


# ---------------------------------------------------------------------------
# G3-G4 — envelope-grant parity for Grep/Glob
# ---------------------------------------------------------------------------


def test_g3_grep_with_envelope_grant_allowed_and_logged():
    """intent §S3 G3 / ADR D9 — envelope `paths` match grants Grep, logs once."""
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
                "tool_name": "Grep",
                "tool_input": {"pattern": "INV-010", "path": "docs/ARCHITECTURE.md"},
            },
            role="phase-1-writer",
            envelope=envelope,
        )
        assert code == 0, (
            f"intent §S3 G3 / D9 — envelope grant must allow Grep on locked-down "
            f"path; got rc={code} stderr={stderr!r}"
        )
        assert GRANT_LOG.exists(), (
            "intent §S3 G3 — grant must append to .claude/envelope-grants.log"
        )
        lines = [ln for ln in GRANT_LOG.read_text().splitlines() if ln.strip()]
        assert len(lines) == 1, f"expected exactly one grant line; got {lines!r}"
        line = lines[0]
        assert "docs/ARCHITECTURE.md" in line, line
        assert "phase-1" in line or "phase-1-writer" in line, line
    finally:
        _restore_grant_log(snapshot)


def test_g4_glob_with_envelope_grant_allowed_and_logged():
    """intent §S3 G4 — same as G3 but tool_name=Glob."""
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
        code, stderr = _run_hook(
            {
                "tool_name": "Glob",
                "tool_input": {"pattern": "*.md", "path": "docs/lessons.md"},
            },
            role="phase-1-writer",
            envelope=envelope,
        )
        assert code == 0, (
            f"intent §S3 G4 / D9 — envelope grant must allow Glob; "
            f"got rc={code} stderr={stderr!r}"
        )
        assert GRANT_LOG.exists()
        lines = [ln for ln in GRANT_LOG.read_text().splitlines() if ln.strip()]
        assert len(lines) == 1, f"expected exactly one grant line; got {lines!r}"
    finally:
        _restore_grant_log(snapshot)


# ---------------------------------------------------------------------------
# G5-G6 — non-locked path / missing path argument → allow
# ---------------------------------------------------------------------------


def test_g5_grep_on_non_locked_path_allowed():
    """intent §S3 G5 — Grep on a path outside ROLE_DENY_READ is allowed."""
    snapshot = _backup_grant_log()
    try:
        if GRANT_LOG.exists():
            GRANT_LOG.unlink()
        code, stderr = _run_hook(
            {
                "tool_name": "Grep",
                "tool_input": {"pattern": "anything", "path": "tests/"},
            },
            role="phase-1-writer",
        )
        assert code == 0, (
            f"intent §S3 G5 — Grep on tests/ must NOT deny "
            f"(not in ROLE_DENY_READ); got rc={code} stderr={stderr!r}"
        )
        # No diagnostic, no grant-log line (pure allow).
        assert not GRANT_LOG.exists() or GRANT_LOG.read_text() == "", (
            "intent §S3 G5 — non-deny-list path must NOT touch grant log"
        )
    finally:
        _restore_grant_log(snapshot)


def test_g6_grep_without_path_argument_allowed():
    """intent §S3 G6 — Grep that omits `path` (search-from-CWD) is not denied.

    The deny check is against an explicit path argument; absent path is
    treated as not matching the deny patterns (intent §S3 explicitly).
    """
    snapshot = _backup_grant_log()
    try:
        code, stderr = _run_hook(
            {"tool_name": "Grep", "tool_input": {"pattern": "INV-010"}},
            role="phase-1-writer",
        )
        assert code == 0, (
            f"intent §S3 G6 — Grep without `path` must NOT deny; "
            f"got rc={code} stderr={stderr!r}"
        )
    finally:
        _restore_grant_log(snapshot)


def test_g6b_glob_without_path_argument_allowed():
    """intent §S3 G6 (Glob analogue) — Glob with only `pattern` is not denied.

    Glob pattern is not a path on its own (a glob matching a deny-list file
    surfaces filenames; the subsequent Read of the matched file is what
    triggers deny via Read).
    """
    snapshot = _backup_grant_log()
    try:
        code, stderr = _run_hook(
            {"tool_name": "Glob", "tool_input": {"pattern": "**/*.md"}},
            role="phase-1-writer",
        )
        assert code == 0, (
            f"intent §S3 — Glob without `path` (pattern-only) must NOT deny; "
            f"got rc={code} stderr={stderr!r}"
        )
    finally:
        _restore_grant_log(snapshot)


# ---------------------------------------------------------------------------
# G7 — non-phase-1-writer roles unaffected
# ---------------------------------------------------------------------------


def test_g7_phase_3_implementer_grep_on_deny_list_path_allowed():
    """intent §S3 G7 — phase-3-implementer is NOT in ROLE_DENY_READ this slice.

    Slice 3 (`compression/lever-Z-substrate-full-pipeline`) extends the
    lockdown to phases 2/3/4. This slice keeps it phase-1-writer-only.
    """
    snapshot = _backup_grant_log()
    try:
        code, stderr = _run_hook(
            {
                "tool_name": "Grep",
                "tool_input": {"pattern": "INV-010", "path": "docs/ARCHITECTURE.md"},
            },
            role="phase-3-implementer",
        )
        assert code == 0, (
            f"intent §S3 G7 boundary — phase-3-implementer Grep must NOT deny "
            f"(lockdown is per-role; phases 2/3/4 are Slice 3 scope); "
            f"got rc={code} stderr={stderr!r}"
        )
    finally:
        _restore_grant_log(snapshot)


def test_g7_unset_role_grep_on_deny_list_path_allowed():
    """ADR D8 scope clause — AGENT_ROLE unset is the no-op path."""
    snapshot = _backup_grant_log()
    try:
        code, _ = _run_hook(
            {
                "tool_name": "Grep",
                "tool_input": {"pattern": "INV-010", "path": "docs/ARCHITECTURE.md"},
            },
            role=None,
        )
        assert code == 0, (
            "ADR D8 scope clause — AGENT_ROLE unset must be a no-op even on "
            "deny-listed paths (orchestrator-bypass / operator session)."
        )
    finally:
        _restore_grant_log(snapshot)


# ---------------------------------------------------------------------------
# READ_CLASS_TOOLS source-text contract (defense-in-depth: catches the case
# where a Phase 3 refactor accidentally re-narrows the constant elsewhere)
# ---------------------------------------------------------------------------


def test_read_class_tools_constant_widened_to_three():
    """intent §S3 — READ_CLASS_TOOLS = {"Read", "Grep", "Glob"} in role_guard.py."""
    sys.path.insert(0, str(CAIRN_ROOT / "checks"))
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("role_guard_under_test", HOOK)
        assert spec and spec.loader
        rg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rg)
        assert rg.READ_CLASS_TOOLS == {"Read", "Grep", "Glob"}, (
            f"intent §S3 — READ_CLASS_TOOLS must equal "
            f"{{'Read', 'Grep', 'Glob'}}; got {rg.READ_CLASS_TOOLS!r}"
        )
    finally:
        if str(CAIRN_ROOT / "checks") in sys.path:
            sys.path.remove(str(CAIRN_ROOT / "checks"))


# ---------------------------------------------------------------------------
# F1 — phase-1-writer.md frontmatter drops Grep + Glob
# ---------------------------------------------------------------------------


def _phase_1_writer_tools_line() -> str:
    """Extract the YAML `tools:` line from phase-1-writer.md frontmatter."""
    text = PHASE_1_WRITER_MD.read_text()
    m = re.search(r"^tools:\s*(.+)$", text, re.MULTILINE)
    assert m, f"no `tools:` line in {PHASE_1_WRITER_MD}"
    return m.group(1).strip()


def test_f1_phase_1_writer_frontmatter_drops_grep():
    """intent §S3 — phase-1-writer.md `tools:` no longer contains Grep
    (defense-in-depth outer gate; Slice 2 stated discipline).
    """
    tools_line = _phase_1_writer_tools_line()
    tokens = {t.strip() for t in tools_line.split(",")}
    assert "Grep" not in tokens, (
        f"intent §S3 — phase-1-writer frontmatter must drop Grep; "
        f"got tools: {tools_line!r}"
    )


def test_f1_phase_1_writer_frontmatter_drops_glob():
    """intent §S3 — phase-1-writer.md `tools:` no longer contains Glob."""
    tools_line = _phase_1_writer_tools_line()
    tokens = {t.strip() for t in tools_line.split(",")}
    assert "Glob" not in tokens, (
        f"intent §S3 — phase-1-writer frontmatter must drop Glob; "
        f"got tools: {tools_line!r}"
    )


def test_f1_phase_1_writer_frontmatter_keeps_write_and_edit():
    """intent §S3 — phase-1-writer remains able to Write/Edit intent.md."""
    tools_line = _phase_1_writer_tools_line()
    tokens = {t.strip() for t in tools_line.split(",")}
    assert "Write" in tokens, (
        f"phase-1-writer must retain Write to author intent.md; got {tools_line!r}"
    )
    assert "Edit" in tokens, (
        f"phase-1-writer must retain Edit to refine intent.md; got {tools_line!r}"
    )
