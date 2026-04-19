"""Phase 2 RED tests for compression/infrastructure — scripts/slice_orchestrator.py.

Verifies intent.md V2 (orchestrator state-machine correctness) plus Phase 2
ambiguity resolutions A1 (structured-return JSON parser rules), A5 (unknown-
status non-zero exit), A6 (target_phase strict validation), A7 (read_slice_state
extras tolerated), A8 (retry-once same args).

Imports slice_orchestrator as a module (pyproject.toml wires pythonpath to
scripts/). Monkeypatches module-level dispatch_agent to stub agent returns.
Expected at Phase 2: all tests FAIL — scripts/slice_orchestrator.py does not
exist, so `import slice_orchestrator` raises ModuleNotFoundError.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
ORCHESTRATOR = CAIRN_ROOT / "scripts" / "slice_orchestrator.py"


# --- V2.1 — CLI surface ----------------------------------------------------


def test_v2_1_help_mentions_brief_and_resume():
    proc = subprocess.run(
        [sys.executable, str(ORCHESTRATOR), "--help"],
        capture_output=True,
        text=True,
        cwd=CAIRN_ROOT,
    )
    assert proc.returncode == 0
    assert "--brief" in proc.stdout
    assert "--resume" in proc.stdout


# --- V2.2 — read_slice_state ------------------------------------------------


def test_v2_2_read_slice_state_parses_minimal_fields(tmp_path: Path):
    import slice_orchestrator as so

    yaml_path = tmp_path / "slice.yaml"
    yaml_path.write_text(
        "id: compression/infrastructure\n"
        'name: "Compression infra"\n'
        "status: 2-validation\n"
        "current_phase: 2\n"
    )
    state = so.read_slice_state(yaml_path)
    assert state["id"] == "compression/infrastructure"
    assert state["status"] == "2-validation"
    assert state["current_phase"] == 2  # A7 — coerced to int


def test_a7_read_slice_state_tolerates_extra_fields(tmp_path: Path):
    """A7 resolution — intent.md:71 'at least' these keys; extras pass through."""
    import slice_orchestrator as so

    yaml_path = tmp_path / "slice.yaml"
    yaml_path.write_text(
        "id: foo/bar\n"
        'name: "Foo"\n'
        "status: 1-intent\n"
        "current_phase: 1\n"
        "invariants-touched: [INV-003]\n"
        "adrs-referenced: [some-adr]\n"
    )
    state = so.read_slice_state(yaml_path)
    assert state["id"] == "foo/bar"
    assert state["current_phase"] == 1


# --- V2.3 / A1 — dispatch_agent structured-return parser --------------------


def test_v2_3_dispatch_agent_parses_structured_return(monkeypatch):
    import slice_orchestrator as so

    stdout = (
        "some preamble\n"
        "chatter about what happened\n"
        '{"status": "OK", "commit_hash": "abc123", "summary": "did the thing"}\n'
    )
    monkeypatch.setattr(
        so.subprocess,
        "run",
        lambda *a, **kw: _fake_completed(stdout=stdout),
    )
    result = so.dispatch_agent("phase-1-writer", {"brief": "x"})
    assert result["status"] == "OK"
    assert result["commit_hash"] == "abc123"


def test_a1_dispatch_agent_takes_last_json_object_line(monkeypatch):
    """A1 — multiple JSON lines in stdout; parser picks the last object."""
    import slice_orchestrator as so

    stdout = (
        '{"status": "OK", "commit_hash": "old", "summary": "stale"}\n'
        "interstitial chatter\n"
        '{"status": "OK", "commit_hash": "new", "summary": "final"}\n'
    )
    monkeypatch.setattr(
        so.subprocess, "run", lambda *a, **kw: _fake_completed(stdout=stdout)
    )
    result = so.dispatch_agent("phase-1-writer", {"brief": "x"})
    assert result["commit_hash"] == "new"


def test_a1_dispatch_agent_strips_trailing_whitespace(monkeypatch):
    """A1 — trailing whitespace on the JSON line does not break parsing."""
    import slice_orchestrator as so

    stdout = '{"status": "OK", "commit_hash": "h", "summary": "s"}   \n'
    monkeypatch.setattr(
        so.subprocess, "run", lambda *a, **kw: _fake_completed(stdout=stdout)
    )
    result = so.dispatch_agent("phase-1-writer", {"brief": "x"})
    assert result["status"] == "OK"


def test_v2_4_dispatch_agent_malformed_stdout_returns_failed(monkeypatch):
    """V2.4 + A1 — no JSON-object line → status FAILED with diagnostic summary."""
    import slice_orchestrator as so

    stdout = "no json anywhere\njust prose\n"
    monkeypatch.setattr(
        so.subprocess, "run", lambda *a, **kw: _fake_completed(stdout=stdout)
    )
    result = so.dispatch_agent("phase-1-writer", {"brief": "x"})
    assert result["status"] == "FAILED"
    assert "malformed" in result["summary"].lower()


# --- V2.5 / V2.6 — run_phase_loop routing -----------------------------------


def test_v2_5_run_phase_loop_ok_advances_phase(monkeypatch, tmp_path: Path):
    import slice_orchestrator as so

    def stub_dispatch(role, inputs, envelope=None, timeout_hard=None):
        return {
            "status": "OK",
            "commit_hash": f"sha-{role}",
            "summary": f"{role} done",
        }

    committed: list[tuple[int, str, str]] = []

    def stub_commit(phase, summary, commit_hash):
        committed.append((phase, summary, commit_hash))

    monkeypatch.setattr(so, "dispatch_agent", stub_dispatch)
    monkeypatch.setattr(so, "commit_phase_handoff", stub_commit)
    monkeypatch.setattr(
        so,
        "dispatch_phase_3",
        lambda slice_id: stub_dispatch("phase-3-implementer", {}),
    )

    def mock_read_state():
        return {"id": "x/y", "status": "in-progress", "current_phase": 1}

    monkeypatch.setattr(so, "_current_phase", lambda: 1, raising=False)

    rc = so.run_phase_loop(max_phase=4)
    assert rc == 0
    phases = [c[0] for c in committed]
    assert phases == [1, 2, 3, 4]


def test_v2_6_run_phase_loop_failed_retries_once(monkeypatch):
    import slice_orchestrator as so

    call_log: list[str] = []

    def stub_dispatch(role, inputs, envelope=None, timeout_hard=None):
        call_log.append(role)
        return {"status": "FAILED", "summary": "boom", "commit_hash": ""}

    monkeypatch.setattr(so, "dispatch_agent", stub_dispatch)
    monkeypatch.setattr(so, "dispatch_phase_3", stub_dispatch)
    monkeypatch.setattr(so, "commit_phase_handoff", lambda *a, **k: None)
    # F3 (compression/orchestrator-hardening): pin _current_phase so this
    # test passes irrespective of the real repo's slice.yaml state. Without
    # this monkeypatch, _current_phase reads .claude/current-slice/slice.yaml
    # and may return any phase — defeating the phase-1 retry assertion.
    monkeypatch.setattr(so, "_current_phase", lambda: 1, raising=False)

    rc = so.run_phase_loop(max_phase=4)
    assert rc != 0  # escalated after second FAILED
    assert call_log.count("phase-1-writer") == 2  # A8 — retry-once same role


def test_a8_retry_uses_same_inputs_and_envelope(monkeypatch):
    """A8 — retry reuses identical role + inputs + envelope + timeout_hard."""
    import slice_orchestrator as so

    call_log: list[tuple[Any, ...]] = []

    def stub_dispatch(role, inputs, envelope=None, timeout_hard=None):
        call_log.append(
            (role, json.dumps(inputs, sort_keys=True), envelope, timeout_hard)
        )
        return {"status": "FAILED", "summary": "boom", "commit_hash": ""}

    monkeypatch.setattr(so, "dispatch_agent", stub_dispatch)
    monkeypatch.setattr(so, "dispatch_phase_3", stub_dispatch)
    monkeypatch.setattr(so, "commit_phase_handoff", lambda *a, **k: None)
    # F3 (compression/orchestrator-hardening): pin _current_phase — without
    # this monkeypatch, the real slice.yaml decides which phase the loop
    # starts in, and the phase-1 retry-once assertion below becomes flaky.
    monkeypatch.setattr(so, "_current_phase", lambda: 1, raising=False)

    so.run_phase_loop(max_phase=4)
    first_two = [c for c in call_log if c[0] == "phase-1-writer"]
    assert len(first_two) == 2
    assert first_two[0] == first_two[1]  # identical args across retry


# --- V2.7 — RAISE_ISSUE routing + A6 target_phase validation ----------------


def test_v2_7_raise_issue_dispatches_triager_and_escalates(monkeypatch):
    import slice_orchestrator as so

    triager_calls: list[dict] = []

    def stub_dispatch(role, inputs, envelope=None, timeout_hard=None):
        if role == "issue-triager":
            triager_calls.append(inputs)
            return {
                "action": "ESCALATE_TO_USER",
                "target_phase": 1,
                "amendment": "",
                "rationale": "needs user",
            }
        return {"status": "RAISE_ISSUE", "commit_hash": "iss1", "summary": "blocked"}

    monkeypatch.setattr(so, "dispatch_agent", stub_dispatch)
    monkeypatch.setattr(so, "dispatch_phase_3", stub_dispatch)
    monkeypatch.setattr(so, "commit_phase_handoff", lambda *a, **k: None)

    rc = so.run_phase_loop(max_phase=4)
    assert rc != 0
    assert len(triager_calls) == 1


def test_a6_target_phase_out_of_bounds_returns_nonzero(monkeypatch):
    """A6 — triager returns target_phase > max_phase → non-zero, no clamp."""
    import slice_orchestrator as so

    def stub_dispatch(role, inputs, envelope=None, timeout_hard=None):
        if role == "issue-triager":
            return {
                "action": "RE_DISPATCH",
                "target_phase": 7,  # out of bounds for max_phase=4
                "amendment": "",
                "rationale": "go to phase 7",
            }
        return {"status": "RAISE_ISSUE", "commit_hash": "iss", "summary": "x"}

    monkeypatch.setattr(so, "dispatch_agent", stub_dispatch)
    monkeypatch.setattr(so, "dispatch_phase_3", stub_dispatch)
    monkeypatch.setattr(so, "commit_phase_handoff", lambda *a, **k: None)

    rc = so.run_phase_loop(max_phase=4)
    assert rc != 0  # loud failure, no silent clamp


def test_a6_target_phase_zero_returns_nonzero(monkeypatch):
    """A6 — target_phase below 1 is equally invalid; no floor clamp."""
    import slice_orchestrator as so

    def stub_dispatch(role, inputs, envelope=None, timeout_hard=None):
        if role == "issue-triager":
            return {
                "action": "RE_DISPATCH",
                "target_phase": 0,
                "amendment": "",
                "rationale": "go to 0",
            }
        return {"status": "RAISE_ISSUE", "commit_hash": "iss", "summary": "x"}

    monkeypatch.setattr(so, "dispatch_agent", stub_dispatch)
    monkeypatch.setattr(so, "dispatch_phase_3", stub_dispatch)
    monkeypatch.setattr(so, "commit_phase_handoff", lambda *a, **k: None)

    rc = so.run_phase_loop(max_phase=4)
    assert rc != 0


# --- A5 — unknown status returns non-zero -----------------------------------


def test_a5_unknown_status_returns_nonzero(monkeypatch):
    """A5 — agent returns unrecognised status → diagnostic + non-zero exit."""
    import slice_orchestrator as so

    def stub_dispatch(role, inputs, envelope=None, timeout_hard=None):
        return {"status": "MYSTERIOUS", "commit_hash": "x", "summary": "y"}

    monkeypatch.setattr(so, "dispatch_agent", stub_dispatch)
    monkeypatch.setattr(so, "dispatch_phase_3", stub_dispatch)
    monkeypatch.setattr(so, "commit_phase_handoff", lambda *a, **k: None)

    rc = so.run_phase_loop(max_phase=4)
    assert rc != 0


# --- V2.8 / A2 — dispatch_phase_3 cluster fan-out ---------------------------


def test_v2_8_dispatch_phase_3_fans_out_three_clusters(monkeypatch, tmp_path: Path):
    import slice_orchestrator as so

    (tmp_path / ".claude" / "current-slice" / "validation").mkdir(parents=True)
    (
        tmp_path / ".claude" / "current-slice" / "validation" / "coupling-clusters.yaml"
    ).write_text(
        "clusters:\n"
        "  - name: core\n"
        '    files: ["^src/core/"]\n'
        "  - name: worker\n"
        '    files: ["^src/worker/"]\n'
        "  - name: api\n"
        '    files: ["^src/api/"]\n'
    )
    monkeypatch.chdir(tmp_path)

    calls: list[str] = []

    def stub_dispatch(role, inputs, envelope=None, timeout_hard=None):
        calls.append(role)
        return {"status": "OK", "commit_hash": f"sha-{len(calls)}", "summary": "ok"}

    monkeypatch.setattr(so, "dispatch_agent", stub_dispatch)

    result = so.dispatch_phase_3("x/y")
    assert result["status"] == "OK"
    assert calls.count("phase-3-implementer") == 3


def test_a2_dispatch_phase_3_absent_clusters_single_implicit(
    monkeypatch, tmp_path: Path
):
    """A2 — absent coupling-clusters.yaml → one implicit-cluster dispatch."""
    import slice_orchestrator as so

    (tmp_path / ".claude" / "current-slice" / "validation").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    calls: list[tuple[str, str | None]] = []

    def stub_dispatch(role, inputs, envelope=None, timeout_hard=None):
        calls.append((role, envelope))
        return {"status": "OK", "commit_hash": "h", "summary": "s"}

    monkeypatch.setattr(so, "dispatch_agent", stub_dispatch)

    result = so.dispatch_phase_3("x/y")
    assert result["status"] == "OK"
    assert len(calls) == 1
    assert calls[0][0] == "phase-3-implementer"


# --- helpers ----------------------------------------------------------------


def _fake_completed(stdout: str = "", stderr: str = "", returncode: int = 0):
    class _Result:
        pass

    r = _Result()
    r.stdout = stdout
    r.stderr = stderr
    r.returncode = returncode
    return r
