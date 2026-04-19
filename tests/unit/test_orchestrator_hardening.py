"""Phase 2 RED tests for compression/orchestrator-hardening — F1 + F2.

F1 — `dispatch_agent` plumbs `--permission-mode acceptEdits` so role_guard.py
remains the effective inner write-path gate per compression-infrastructure-
bootstrap. The literal value lives behind a module-level UPPERCASE constant
(name not pinned) so future audits can locate it without grep.

F2 — `init_new_slice(brief)` persists the user's brief into a new
`brief:` key on `.claude/current-slice/slice.yaml`; `read_slice_state`
round-trips it; `run_phase_loop` includes it in every Phase 1 dispatch
payload so the writer no longer loses it after init.

F3 lives in `test_slice_orchestrator_state_machine.py` — a test-isolation
fix that makes existing assertions independent of the real repo's
slice.yaml state. Not duplicated here.

Module is imported as `slice_orchestrator` (pyproject.toml wires pythonpath
to scripts/). At Phase 2 these tests should be RED — Builder's Phase 3 work
in `scripts/slice_orchestrator.py` makes them GREEN.
"""

from __future__ import annotations

import subprocess


# --- F1 — --permission-mode plumbing ---------------------------------------


def _fake_run_capturing_cmd(captured: dict):
    """Returns a subprocess.run replacement that records cmd and returns a
    CompletedProcess with a valid JSON-tail stdout so dispatch_agent's
    _parse_structured_tail does not raise."""

    def _run(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout='{"status": "OK"}', stderr=""
        )

    return _run


def test_f1_dispatch_agent_cmd_includes_permission_mode_flag(monkeypatch):
    """The cmd list constructed by dispatch_agent MUST contain --permission-mode."""
    import slice_orchestrator as so

    captured: dict = {}
    monkeypatch.setattr(so.subprocess, "run", _fake_run_capturing_cmd(captured))

    so.dispatch_agent("phase-1-writer", {"phase": 1, "slice_id": "x/y"})

    assert "cmd" in captured, "dispatch_agent did not invoke subprocess.run"
    assert "--permission-mode" in captured["cmd"], (
        f"dispatch_agent cmd missing --permission-mode flag; got {captured['cmd']!r}"
    )


def test_f1_dispatch_agent_permission_mode_value_is_acceptedits(monkeypatch):
    """The value following --permission-mode MUST be 'acceptEdits' so
    role_guard.py runs as the inner write-path gate per
    compression-infrastructure-bootstrap Decision 2."""
    import slice_orchestrator as so

    captured: dict = {}
    monkeypatch.setattr(so.subprocess, "run", _fake_run_capturing_cmd(captured))

    so.dispatch_agent("phase-1-writer", {"phase": 1, "slice_id": "x/y"})

    cmd = captured["cmd"]
    idx = cmd.index("--permission-mode")
    assert idx + 1 < len(cmd), (
        f"--permission-mode appears at end of cmd with no value; cmd={cmd!r}"
    )
    assert cmd[idx + 1] == "acceptEdits", (
        f"--permission-mode value is {cmd[idx + 1]!r}; expected 'acceptEdits'."
        " If Builder selects a different value, ADR-cite it in implementation/notes.md"
        " AND update this test."
    )


def test_f1_permission_mode_value_lives_in_module_level_constant():
    """The permission-mode value MUST be reachable via a module-level
    UPPERCASE attribute on slice_orchestrator (the constant's *name* is
    Builder's choice; only the structural commitment is enforced here)."""
    import slice_orchestrator as so

    matches = [
        name
        for name in dir(so)
        if name.isupper()
        and not name.startswith("_")
        and getattr(so, name, None) == "acceptEdits"
    ]
    assert matches, (
        "expected at least one module-level UPPERCASE constant on"
        " slice_orchestrator equal to 'acceptEdits'; found none. Builder must"
        " bind the value to a named constant (intent.md F1: 'so future audits"
        " can locate it without grep')."
    )


def test_f1_phase_3_dispatcher_inherits_permission_mode(monkeypatch):
    """The Phase 3 cluster dispatcher (dispatch_phase_3) builds cmds via the
    same dispatch_agent path, so it MUST also carry --permission-mode. This
    guards against a future refactor that bypasses dispatch_agent for Phase 3.

    Implemented by counting --permission-mode occurrences across all cmds
    captured during a stubbed run_phase_loop(max_phase=1) run — Phase 1 is
    enough to prove the flag flows through dispatch_agent uniformly. The
    cluster-fanout path (Phase 3) is checked in V2.5/V2.6 already; this test
    locks the flag-presence invariant for *every* dispatch_agent caller."""
    import slice_orchestrator as so

    captured_cmds: list = []

    def _run(cmd, *args, **kwargs):
        captured_cmds.append(list(cmd))
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout='{"status": "OK"}', stderr=""
        )

    monkeypatch.setattr(so.subprocess, "run", _run)

    so.dispatch_agent("phase-2-skeptic", {"phase": 2, "slice_id": "x/y"})
    so.dispatch_agent("phase-4-integrator", {"phase": 4, "slice_id": "x/y"})

    assert captured_cmds, "no subprocess.run calls captured"
    for cmd in captured_cmds:
        assert "--permission-mode" in cmd, (
            f"cmd missing --permission-mode flag; got {cmd!r}"
        )


# --- F2 — brief persistence -------------------------------------------------


def _stub_dispatch_returning_slice_id(slice_id: str = "test/seed"):
    """Returns a dispatch_agent stub that emulates the slice-id-proposer
    response init_new_slice expects."""

    def _stub(role, inputs, envelope=None, timeout_hard=None):
        return {"proposed_slice_id": slice_id}

    return _stub


def test_f2_init_new_slice_writes_brief_key_to_slice_yaml(tmp_path, monkeypatch):
    """init_new_slice(brief=...) MUST write a `brief:` line into slice.yaml
    containing the user's brief verbatim."""
    import slice_orchestrator as so

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(so, "dispatch_agent", _stub_dispatch_returning_slice_id())

    brief_text = "fix the orchestrator dispatch path"
    so.init_new_slice(brief=brief_text)

    yaml_path = tmp_path / ".claude" / "current-slice" / "slice.yaml"
    assert yaml_path.exists(), "slice.yaml was not created"
    yaml_text = yaml_path.read_text()
    assert "brief:" in yaml_text, (
        f"slice.yaml missing `brief:` key after init_new_slice; got:\n{yaml_text}"
    )
    assert brief_text in yaml_text, (
        f"slice.yaml does not contain brief text verbatim; got:\n{yaml_text}"
    )


def test_f2_brief_round_trips_through_read_slice_state(tmp_path, monkeypatch):
    """init_new_slice writes brief; read_slice_state retrieves it. Covers
    intent.md F2: 'preserving whitespace and quoting'."""
    import slice_orchestrator as so

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(so, "dispatch_agent", _stub_dispatch_returning_slice_id())

    brief_text = "make dispatcher honour permission-mode"
    so.init_new_slice(brief=brief_text)

    yaml_path = tmp_path / ".claude" / "current-slice" / "slice.yaml"
    state = so.read_slice_state(yaml_path)
    assert state.get("brief") == brief_text, (
        f"round-trip mismatch: wrote {brief_text!r}, read {state.get('brief')!r}"
    )


def test_f2_brief_with_embedded_colon_round_trips(tmp_path, monkeypatch):
    """A brief containing a YAML-significant colon MUST still round-trip.
    read_slice_state uses partition(':') which only splits the first colon,
    so any sane Builder serialisation should preserve the value."""
    import slice_orchestrator as so

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(so, "dispatch_agent", _stub_dispatch_returning_slice_id())

    brief_text = "fix: dispatcher loses --permission-mode under -p"
    so.init_new_slice(brief=brief_text)

    yaml_path = tmp_path / ".claude" / "current-slice" / "slice.yaml"
    state = so.read_slice_state(yaml_path)
    assert state.get("brief") == brief_text, (
        f"colon round-trip mismatch: wrote {brief_text!r}, read {state.get('brief')!r}"
    )


def test_f2_run_phase_loop_propagates_brief_into_phase_1_dispatch(
    tmp_path, monkeypatch
):
    """A seeded slice.yaml with `brief: <value>` MUST cause run_phase_loop's
    Phase 1 dispatch to carry inputs['brief'] == <value>. This is the
    end-to-end verification of F2."""
    import slice_orchestrator as so

    monkeypatch.chdir(tmp_path)
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    seed_brief = "the seed brief value"
    (slice_dir / "slice.yaml").write_text(
        "id: test/seed\n"
        'name: "test/seed"\n'
        "status: in-progress\n"
        "current_phase: 1\n"
        f'brief: "{seed_brief}"\n'
    )

    captured: list = []

    def stub_dispatch(role, inputs, envelope=None, timeout_hard=None):
        captured.append((role, dict(inputs)))
        return {"status": "OK", "summary": "stub", "commit_hash": ""}

    monkeypatch.setattr(so, "dispatch_agent", stub_dispatch)
    monkeypatch.setattr(so, "dispatch_phase_3", stub_dispatch)
    monkeypatch.setattr(so, "commit_phase_handoff", lambda *a, **k: None)

    rc = so.run_phase_loop(max_phase=1)
    assert rc == 0, f"run_phase_loop returned non-zero: {rc}"

    phase_1_calls = [c for c in captured if c[0] == "phase-1-writer"]
    assert phase_1_calls, (
        f"no phase-1-writer dispatch observed; captured roles="
        f"{[c[0] for c in captured]}"
    )
    inputs = phase_1_calls[0][1]
    assert inputs.get("brief") == seed_brief, (
        f"phase-1-writer dispatch missing brief; inputs={inputs!r}"
    )
