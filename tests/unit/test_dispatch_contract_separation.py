"""Phase 2 RED — V3 of compression/slice-1-foundation intent.md.

Asserts the B1/B17 contract split:

    dispatch_phase_agent(role, inputs, ...) -> {status, commit_hash, summary}
    dispatch_triager(issue_hash, phase, slice_id) -> {action, target_phase, ...}

Triager returns with action RE_DISPATCH and NO `status` key must NOT
write a noise failure log (the regression this split prevents —
intent.md:60). dispatch_phase_agent must reject a stdout tail missing
the `status` key with a clear error surface.

RED at Phase 2: both functions do not exist in scripts/slice_orchestrator.py.
"""

from __future__ import annotations

import json
import subprocess



def _fake_run_with_stdout(stdout_text: str, rc: int = 0):
    def _run(cmd, *args, **kwargs):
        return subprocess.CompletedProcess(
            args=cmd, returncode=rc, stdout=stdout_text, stderr=""
        )

    return _run


def _fake_popen_with_stdout(stdout_text: str, rc: int = 0):
    """Fake Popen returning the given stdout and a clean stderr, in case the
    implementation replaces run() with Popen() (D3 live-stderr)."""

    class _FakeProc:
        def __init__(self, *_a, **_kw):
            self._out = stdout_text
            self.returncode = rc

        def communicate(self, *_a, **_kw):
            return (self._out, "")

        def wait(self, *_a, **_kw):
            return rc

        def poll(self):
            return rc

        @property
        def stdout(self):
            import io

            return io.StringIO(self._out)

        @property
        def stderr(self):
            import io

            return io.StringIO("")

        def kill(self):
            pass

        def terminate(self):
            pass

    return _FakeProc


# --- V3a — dispatch_triager exists with the right signature ---------------


def test_v3_dispatch_triager_symbol_exported():
    import slice_orchestrator as so

    assert hasattr(so, "dispatch_triager"), (
        "intent.md:58/V3 — dispatch_triager must be exported from slice_orchestrator"
    )


def test_v3_dispatch_phase_agent_symbol_exported():
    import slice_orchestrator as so

    assert hasattr(so, "dispatch_phase_agent"), (
        "intent.md:57/V3 — dispatch_phase_agent must be exported from slice_orchestrator"
    )


# --- V3b — triager return parses and writes no noise failure log ----------


def test_v3_triager_re_dispatch_returns_typed_result_no_noise_log(
    monkeypatch, tmp_path
):
    """intent.md:58-60 — triager tail {action: RE_DISPATCH, target_phase: 2}
    must validate and produce NO failure log (the B1 regression)."""
    import slice_orchestrator as so

    triager_tail = json.dumps(
        {"action": "RE_DISPATCH", "target_phase": 2, "rationale": "retry-after-flake"}
    )
    monkeypatch.setattr(so.subprocess, "run", _fake_run_with_stdout(triager_tail, rc=0))
    # Cover Popen path too (D3).
    monkeypatch.setattr(
        so.subprocess, "Popen", _fake_popen_with_stdout(triager_tail, rc=0)
    )

    debug_dir = tmp_path / "orchestrator-debug"
    monkeypatch.setattr(so, "DEBUG_DIR", debug_dir, raising=False)

    result = so.dispatch_triager(
        issue_hash="deadbeef",
        phase=2,
        slice_id="compression/slice-1-foundation",
    )

    assert isinstance(result, dict) or hasattr(result, "action"), (
        "dispatch_triager must return a dict-like / dataclass with `action`"
    )
    action = result["action"] if isinstance(result, dict) else result.action
    assert action == "RE_DISPATCH", f"action must round-trip; got {action!r}"
    target = result["target_phase"] if isinstance(result, dict) else result.target_phase
    assert target == 2, f"target_phase must round-trip; got {target!r}"

    if debug_dir.exists():
        logs = list(debug_dir.glob("*.log"))
        assert not logs, (
            f"intent.md:60 — triager RE_DISPATCH must NOT write failure log; "
            f"found {[p.name for p in logs]!r}"
        )


def test_v3_triager_rejects_invalid_action(monkeypatch, tmp_path):
    """An action outside {ESCALATE_TO_USER, RE_DISPATCH, ABORT} must be rejected."""
    import slice_orchestrator as so

    bad_tail = json.dumps({"action": "TELEPORT", "target_phase": 2})
    monkeypatch.setattr(so.subprocess, "run", _fake_run_with_stdout(bad_tail, rc=0))
    monkeypatch.setattr(so.subprocess, "Popen", _fake_popen_with_stdout(bad_tail, rc=0))
    monkeypatch.setattr(so, "DEBUG_DIR", tmp_path / "orchestrator-debug", raising=False)

    result = so.dispatch_triager(
        issue_hash="deadbeef",
        phase=2,
        slice_id="compression/slice-1-foundation",
    )
    action = result["action"] if isinstance(result, dict) else result.action
    # Implementation may return action="FAILED" sentinel, or map unknown to ESCALATE.
    assert action != "TELEPORT", (
        "dispatch_triager must not pass an unknown action through verbatim"
    )


# --- V3c — dispatch_phase_agent rejects tail missing `status` -------------


def test_v3_dispatch_phase_agent_missing_status_surfaces_clear_error(
    monkeypatch, tmp_path
):
    """intent.md:72 — a tail missing `status` must produce a clear error surface
    (either raise or return FAILED with a message naming `status`)."""
    import slice_orchestrator as so

    no_status_tail = json.dumps({"commit_hash": "abc1234", "summary": "ok"})
    monkeypatch.setattr(
        so.subprocess, "run", _fake_run_with_stdout(no_status_tail, rc=0)
    )
    monkeypatch.setattr(
        so.subprocess, "Popen", _fake_popen_with_stdout(no_status_tail, rc=0)
    )
    monkeypatch.setattr(so, "DEBUG_DIR", tmp_path / "orchestrator-debug", raising=False)

    try:
        result = so.dispatch_phase_agent(
            "phase-1-writer",
            {"phase": 1, "slice_id": "compression/slice-1-foundation"},
        )
    except (ValueError, KeyError, TypeError) as exc:  # raise is acceptable
        assert "status" in str(exc).lower(), (
            f"error message must name the missing field; got {exc!r}"
        )
        return

    # Otherwise must return a FAILED result that mentions the missing status.
    status = result["status"] if isinstance(result, dict) else result.status
    assert status == "FAILED", (
        f"Missing-status tail must surface FAILED (or raise); got status={status!r}"
    )
    summary = (result["summary"] if isinstance(result, dict) else result.summary) or ""
    assert "status" in summary.lower(), (
        f"FAILED summary must mention the missing `status` field; got {summary!r}"
    )


# --- V3d — dispatch_phase_agent accepts a well-formed OK tail ---------------


def test_v3_dispatch_phase_agent_happy_path(monkeypatch, tmp_path):
    import slice_orchestrator as so

    ok_tail = json.dumps(
        {"status": "OK", "commit_hash": "abc1234", "summary": "phase 1 done"}
    )
    monkeypatch.setattr(so.subprocess, "run", _fake_run_with_stdout(ok_tail, rc=0))
    monkeypatch.setattr(so.subprocess, "Popen", _fake_popen_with_stdout(ok_tail, rc=0))
    monkeypatch.setattr(so, "DEBUG_DIR", tmp_path / "orchestrator-debug", raising=False)

    result = so.dispatch_phase_agent(
        "phase-1-writer", {"phase": 1, "slice_id": "compression/slice-1-foundation"}
    )
    status = result["status"] if isinstance(result, dict) else result.status
    assert status == "OK"
    commit = result["commit_hash"] if isinstance(result, dict) else result.commit_hash
    assert commit == "abc1234"
