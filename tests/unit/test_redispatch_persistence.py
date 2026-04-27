"""Phase 2 RED — compression/slice-2-state-machine §B14.

Before `phase = target; continue` in the RE_DISPATCH branch, the orchestrator
MUST persist `current_phase: target` to slice.yaml AND create a commit whose
message matches `slice: re-dispatch phase {N} → phase {target}`. This makes
`--resume` after a mid-redispatch crash land at `target`, not `N`.

Expected at Phase 2: FAILS — no persistence, no commit.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _init_project(tmp_path: Path) -> Path:
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    (slice_dir / "slice.yaml").write_text(
        'id: demo/rd\nname: "demo/rd"\nstatus: in-progress\n'
        'current_phase: 1\nbrief: "b"\n'
    )
    (slice_dir / "intent.md").write_text(
        "---\nslice: demo/rd\nphase: 1-intent\nenvelope: []\n---\n"
    )
    for n in (1, 2, 3, 4):
        (slice_dir / f"handoff-phase-{n}.md").write_text(f"phase-{n}\n")
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


def test_b14_redispatch_persists_target_phase_and_commits(monkeypatch, tmp_path):
    slice_dir = _init_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)
    monkeypatch.setattr(
        so, "DEBUG_DIR", tmp_path / ".claude" / "orchestrator-debug", raising=False
    )

    phase_call_counts: dict[int, int] = {}

    def dispatch_stub(role, inputs, envelope=None, timeout_hard=None):
        phase = inputs.get("phase")
        phase_call_counts[phase] = phase_call_counts.get(phase, 0) + 1
        # Phase 2 raises once, then succeeds.
        if phase == 2 and phase_call_counts[phase] == 1:
            return {
                "status": "RAISE_ISSUE",
                "commit_hash": "deadbee",
                "summary": "need phase 1 rework",
            }
        return {"status": "OK", "commit_hash": "feedbee", "summary": f"{role} ok"}

    def triager_stub(*args, **kwargs):
        return {"decision": "RE_DISPATCH", "target_phase": 1}

    monkeypatch.setattr(so, "dispatch_phase_agent", dispatch_stub)
    if hasattr(so, "dispatch_triager"):
        monkeypatch.setattr(so, "dispatch_triager", triager_stub)

    # The test observes the persisted state after run_phase_loop returns.
    # Because re-dispatch rewinds to phase 1 and then re-runs 2/3/4 with OK,
    # the loop should complete. But we only care that a commit was made
    # BEFORE the rewind.
    try:
        so.run_phase_loop()
    except SystemExit:
        pass

    log = subprocess.run(
        ["git", "log", "--format=%s"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    match = [
        ln
        for ln in log
        if ln.startswith("slice: re-dispatch phase 2") and "phase 1" in ln
    ]
    assert match, (
        f"expected `slice: re-dispatch phase 2 → phase 1` commit; git log={log!r}"
    )


def test_b14_redispatch_writes_target_phase_into_yaml(monkeypatch, tmp_path):
    slice_dir = _init_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)
    monkeypatch.setattr(
        so, "DEBUG_DIR", tmp_path / ".claude" / "orchestrator-debug", raising=False
    )

    seen_phases: list[int] = []

    def dispatch_stub(role, inputs, envelope=None, timeout_hard=None):
        phase = inputs.get("phase")
        seen_phases.append(phase)
        # At the moment Phase 1 is re-entered post-redispatch, slice.yaml
        # must already carry `current_phase: 1` (the target).
        if phase == 1 and seen_phases.count(1) == 2:
            body = (slice_dir / "slice.yaml").read_text()
            assert "current_phase: 1" in body, (
                f"slice.yaml must carry target phase before rewind; body={body!r}"
            )
        if phase == 2 and seen_phases.count(2) == 1:
            return {
                "status": "RAISE_ISSUE",
                "commit_hash": "d",
                "summary": "rewind",
            }
        return {"status": "OK", "commit_hash": "f", "summary": "ok"}

    monkeypatch.setattr(so, "dispatch_phase_agent", dispatch_stub)
    if hasattr(so, "dispatch_triager"):
        monkeypatch.setattr(
            so,
            "dispatch_triager",
            lambda *a, **k: {"decision": "RE_DISPATCH", "target_phase": 1},
        )
    try:
        so.run_phase_loop()
    except SystemExit:
        pass
    assert 1 in seen_phases and seen_phases.count(1) >= 2, (
        f"phase 1 must be re-entered after redispatch; seen={seen_phases!r}"
    )
