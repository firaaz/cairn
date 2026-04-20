"""Phase 2 RED — compression/slice-2-state-machine §B15.

`run_phase_loop` MUST maintain `redispatch_count: dict[int, int]` keyed by
source phase. On the second RE_DISPATCH whose source phase is already in
the dict, the orchestrator MUST escalate with stderr matching
`orchestrator: phase {N} re-dispatched twice; escalating per design §6.1`
and return exit code 1 WITHOUT invoking the triager a second time.

Expected at Phase 2: FAILS — no cap, triager re-invoked.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _init_project(tmp_path: Path) -> Path:
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    (slice_dir / "slice.yaml").write_text(
        'id: demo/cap\nname: "demo/cap"\nstatus: in-progress\n'
        'current_phase: 1\nbrief: "b"\n'
    )
    (slice_dir / "intent.md").write_text(
        "---\nslice: demo/cap\nphase: 1-intent\nenvelope: []\n---\n"
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


def test_b15_second_redispatch_from_same_phase_escalates(monkeypatch, tmp_path, capsys):
    slice_dir = _init_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)
    monkeypatch.setattr(
        so, "DEBUG_DIR", tmp_path / ".claude" / "orchestrator-debug", raising=False
    )

    def dispatch_stub(role, inputs, envelope=None, timeout_hard=None):
        # Phase 2 always raises — triager always says re-dispatch to 1.
        if inputs.get("phase") == 2:
            return {
                "status": "RAISE_ISSUE",
                "commit_hash": "d",
                "summary": "raise",
            }
        return {"status": "OK", "commit_hash": "f", "summary": "ok"}

    triager_calls: list[tuple] = []

    def triager_stub(*args, **kwargs):
        triager_calls.append((args, kwargs))
        return {"decision": "RE_DISPATCH", "target_phase": 1}

    monkeypatch.setattr(so, "dispatch_phase_agent", dispatch_stub)
    assert hasattr(so, "dispatch_triager"), "dispatch_triager must exist"
    monkeypatch.setattr(so, "dispatch_triager", triager_stub)

    rc = None
    try:
        rc = so.run_phase_loop()
    except SystemExit as e:
        rc = e.code

    assert rc == 1, f"second redispatch must force exit 1; got {rc}"
    assert len(triager_calls) == 1, (
        f"triager must be invoked exactly once (first RE_DISPATCH only); "
        f"got {len(triager_calls)} calls: {triager_calls!r}"
    )
    err = capsys.readouterr().err
    assert "re-dispatched twice" in err, (
        f"stderr must mention cap violation; got {err!r}"
    )
    assert "phase 2" in err, f"stderr must name the offending source phase; got {err!r}"
