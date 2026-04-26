"""Phase 2 RED — compression/lever-Y-mcp-substrate V6.

`scripts.slice_orchestrator.dispatch._dispatch_once` MUST set
``AGENT_ENVELOPE`` for ``phase-1-writer`` dispatch to a JSON object with
a ``cairn_query_snapshot`` field equal to ``git rev-parse HEAD`` at
dispatch time. On simulated git failure, the field is the sentinel
``unknown-sha-<iso8601>`` per ADR D12.

Pre-existing phase-3-implementer envelope shape (JSON array) round-trips
through `role_guard._envelope_patterns` unchanged.

Expected at Phase 2: FAILS — current `_dispatch_once` only sets
AGENT_ENVELOPE when the caller passes one, and does not synthesize a
snapshot for phase-1-writer.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(CAIRN_ROOT / "scripts"))


_CAPTURED_ENV: dict = {}


def _fake_run_with_live_stderr_factory(rc=0, stdout_text=None):
    """Return a fake _run_with_live_stderr that captures `env` and returns OK."""
    if stdout_text is None:
        stdout_text = json.dumps(
            {"status": "OK", "commit_hash": "abc1234", "summary": "ok"}
        )

    def _fake(cmd, env, timeout, prefix=""):
        _CAPTURED_ENV.clear()
        _CAPTURED_ENV.update(env)
        return subprocess.CompletedProcess(
            args=cmd, returncode=rc, stdout=stdout_text, stderr=""
        )

    return _fake


@pytest.fixture(autouse=True)
def _reset_capture():
    _CAPTURED_ENV.clear()
    yield
    _CAPTURED_ENV.clear()


def _import_dispatch():
    from slice_orchestrator import dispatch  # type: ignore

    return dispatch


def test_v6_phase_1_writer_envelope_includes_cairn_query_snapshot(
    monkeypatch, tmp_path
):
    """intent.md §S3 — phase-1-writer dispatch MUST set
    `AGENT_ENVELOPE.cairn_query_snapshot` to current `git rev-parse HEAD`.
    """
    dispatch = _import_dispatch()
    monkeypatch.setattr(
        dispatch, "_run_with_live_stderr", _fake_run_with_live_stderr_factory()
    )
    monkeypatch.setattr(
        dispatch, "DEBUG_DIR", tmp_path / "orchestrator-debug", raising=False
    )

    dispatch._dispatch_once(
        "phase-1-writer",
        {"phase": 1, "slice_id": "compression/lever-Y-mcp-substrate"},
    )

    raw = _CAPTURED_ENV.get("AGENT_ENVELOPE")
    assert raw, (
        "intent §S3 — phase-1-writer dispatch must set AGENT_ENVELOPE; not present"
    )
    payload = json.loads(raw)
    assert isinstance(payload, dict), (
        f"intent §S3 — phase-1-writer envelope must be a JSON object; got {type(payload).__name__}"
    )
    assert "cairn_query_snapshot" in payload, (
        f"intent §S3 — envelope must carry cairn_query_snapshot; got keys={list(payload)!r}"
    )
    snap = payload["cairn_query_snapshot"]
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=CAIRN_ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    assert snap == head, (
        f"intent §S3 — snapshot must equal `git rev-parse HEAD`; got {snap!r}, head={head!r}"
    )


def test_v6_envelope_paths_array_present_for_phase_1_writer(monkeypatch, tmp_path):
    """intent.md §S3 — object envelope shape includes a `paths` array
    derived from slice.yaml's envelope; role_guard reads from it.
    """
    dispatch = _import_dispatch()
    monkeypatch.setattr(
        dispatch, "_run_with_live_stderr", _fake_run_with_live_stderr_factory()
    )
    monkeypatch.setattr(
        dispatch, "DEBUG_DIR", tmp_path / "orchestrator-debug", raising=False
    )

    dispatch._dispatch_once(
        "phase-1-writer",
        {"phase": 1, "slice_id": "compression/lever-Y-mcp-substrate"},
    )

    raw = _CAPTURED_ENV.get("AGENT_ENVELOPE")
    assert raw, "AGENT_ENVELOPE not set"
    payload = json.loads(raw)
    assert "paths" in payload, (
        f"intent §S3 — object envelope must carry `paths` array; got keys={list(payload)!r}"
    )
    assert isinstance(payload["paths"], list), "`paths` must be a list of regex strings"


def test_v6_sentinel_when_git_rev_parse_fails(monkeypatch, tmp_path):
    """ADR D12 — when `git rev-parse` fails, snapshot is `unknown-sha-<iso8601>`."""
    dispatch = _import_dispatch()
    monkeypatch.setattr(
        dispatch, "_run_with_live_stderr", _fake_run_with_live_stderr_factory()
    )
    monkeypatch.setattr(
        dispatch, "DEBUG_DIR", tmp_path / "orchestrator-debug", raising=False
    )

    # Force the snapshot resolver to fail. Implementation may use either
    # `_git_head_safe` (from .git module) or a local helper; patch both
    # surfaces conservatively.
    from slice_orchestrator import git as git_mod  # type: ignore

    def _explode(*_a, **_kw):
        raise subprocess.CalledProcessError(128, ["git", "rev-parse", "HEAD"])

    monkeypatch.setattr(git_mod, "_git_head_safe", lambda: None, raising=False)
    if hasattr(dispatch, "_resolve_snapshot"):
        monkeypatch.setattr(dispatch, "_resolve_snapshot", lambda: None, raising=False)
    monkeypatch.setattr(subprocess, "run", _explode)
    # Re-install our fake _run_with_live_stderr (subprocess.run was just patched out).
    monkeypatch.setattr(
        dispatch, "_run_with_live_stderr", _fake_run_with_live_stderr_factory()
    )

    dispatch._dispatch_once(
        "phase-1-writer",
        {"phase": 1, "slice_id": "compression/lever-Y-mcp-substrate"},
    )

    raw = _CAPTURED_ENV.get("AGENT_ENVELOPE")
    assert raw, "AGENT_ENVELOPE not set under git-failure path"
    payload = json.loads(raw)
    snap = payload.get("cairn_query_snapshot", "")
    assert snap.startswith("unknown-sha-"), (
        f"ADR D12 — sentinel must start with 'unknown-sha-'; got {snap!r}"
    )
    iso_tail = snap[len("unknown-sha-") :]
    # Loose ISO8601 check — at minimum YYYY-MM-DD prefix.
    assert re.match(r"^\d{4}-\d{2}-\d{2}", iso_tail), (
        f"ADR D12 — sentinel must include ISO8601 timestamp; got tail={iso_tail!r}"
    )


def test_v6_phase_3_array_envelope_round_trips_through_envelope_patterns():
    """intent.md §S3 — pre-existing phase-3-implementer JSON-array envelope
    shape MUST still produce the legacy pattern list when round-tripped
    through `role_guard._envelope_patterns`.
    """
    spec = importlib.util.spec_from_file_location(
        "role_guard", CAIRN_ROOT / "checks" / "role_guard.py"
    )
    rg = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(rg)

    array_env = json.dumps([r"^scripts/x\.py$", r"^tests/"])
    patterns = rg._envelope_patterns(array_env)
    assert patterns == [r"^scripts/x\.py$", r"^tests/"], (
        f"array-shape envelope must round-trip unchanged; got {patterns!r}"
    )


def test_v6_phase_3_dispatch_unaffected(monkeypatch, tmp_path):
    """Slice 3 territory — phase-3-implementer envelope behavior is NOT
    altered by this slice. If the caller passes an array-string envelope,
    it reaches the subprocess unchanged.
    """
    dispatch = _import_dispatch()
    monkeypatch.setattr(
        dispatch, "_run_with_live_stderr", _fake_run_with_live_stderr_factory()
    )
    monkeypatch.setattr(
        dispatch, "DEBUG_DIR", tmp_path / "orchestrator-debug", raising=False
    )

    array_env = json.dumps([r"^scripts/x\.py$"])
    dispatch._dispatch_once(
        "phase-3-implementer",
        {"phase": 3, "slice_id": "compression/lever-Y-mcp-substrate"},
        envelope=array_env,
    )
    raw = _CAPTURED_ENV.get("AGENT_ENVELOPE")
    assert raw == array_env, (
        f"phase-3 envelope must pass through unchanged; got {raw!r}"
    )
