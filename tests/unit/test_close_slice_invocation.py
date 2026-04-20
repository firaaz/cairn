"""Phase 2 RED — compression/slice-2-state-machine §B10.

`run_phase_loop` MUST call `close_slice(state)` exactly once when Phase 4
returns `status: OK`. Afterwards:

 - `slice.yaml` carries `status: complete` and `current_phase: 4`.
 - `.claude/handoff.md` is the concatenation of `handoff-phase-{1..4}.md`
   separated by `\\n---\\n`, followed by `integration/sweep-notes.md` if
   present.
 - A single git commit `slice: complete` stages both files.

Expected at Phase 2: FAILS because close_slice is not yet invoked from
run_phase_loop at the end of the Phase-4-OK exit path, or it does not
assemble handoff.md as specified.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _init_project(tmp_path: Path) -> Path:
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    (slice_dir / "slice.yaml").write_text(
        "id: demo/slice-x\n"
        'name: "demo/slice-x"\n'
        "status: in-progress\n"
        "current_phase: 1\n"
        'brief: "demo brief"\n'
    )
    (slice_dir / "intent.md").write_text(
        "---\nslice: demo/slice-x\nphase: 1-intent\nenvelope: []\n---\nbody\n"
    )
    for n in (1, 2, 3, 4):
        (slice_dir / f"handoff-phase-{n}.md").write_text(
            f"---\nphase: {n}\n---\nphase-{n}-body\n"
        )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-q",
            "-m",
            "init",
        ],
        cwd=tmp_path,
        check=True,
    )
    return slice_dir


def _stub_dispatch_ok(role, inputs, envelope=None, timeout_hard=None):
    return {"status": "OK", "commit_hash": "deadbee", "summary": f"{role} ok"}


def test_b10_close_slice_fires_and_produces_concatenated_handoff(monkeypatch, tmp_path):
    slice_dir = _init_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)
    monkeypatch.setattr(
        so, "DEBUG_DIR", tmp_path / ".claude" / "orchestrator-debug", raising=False
    )
    monkeypatch.setattr(so, "dispatch_phase_agent", _stub_dispatch_ok)

    rc = so.run_phase_loop()
    assert rc == 0, f"run_phase_loop returned {rc}; expected 0 on all-OK path"

    state_yaml = (slice_dir / "slice.yaml").read_text()
    assert "status: complete" in state_yaml
    assert "current_phase: 4" in state_yaml

    handoff = (tmp_path / ".claude" / "handoff.md").read_text()
    assert "phase-1-body" in handoff
    assert "phase-4-body" in handoff
    # exactly 3 separators between 4 phase files (+ optional trailing for sweep-notes)
    assert handoff.count("\n---\n") >= 3

    log = subprocess.run(
        ["git", "log", "--format=%s"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert "slice: complete" in log, f"no `slice: complete` commit; log={log!r}"
    assert log.count("slice: complete") == 1, "close_slice must commit exactly once"


def test_b10_handoff_includes_sweep_notes_when_present(monkeypatch, tmp_path):
    slice_dir = _init_project(tmp_path)
    integ = slice_dir / "integration"
    integ.mkdir()
    (integ / "sweep-notes.md").write_text("SWEEP-NOTES-BODY")
    monkeypatch.chdir(tmp_path)

    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)
    monkeypatch.setattr(
        so, "DEBUG_DIR", tmp_path / ".claude" / "orchestrator-debug", raising=False
    )
    monkeypatch.setattr(so, "dispatch_phase_agent", _stub_dispatch_ok)

    so.run_phase_loop()
    handoff = (tmp_path / ".claude" / "handoff.md").read_text()
    assert "SWEEP-NOTES-BODY" in handoff, (
        "handoff.md must include integration/sweep-notes.md when present"
    )
