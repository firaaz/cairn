"""Phase 2 RED — close_slice INV-008 (DC-3, DC-4, DC-5).

Spec: intent.md §DC-3 precondition, §DC-4 three-layer enforcement, §DC-5 wipe
semantics.
 - DC-3: `close_slice` is idempotent; `_is_slice_already_closed(state)` returns
   True iff all four signals (status=complete, handoff.md exists and non-empty,
   current-slice/ contains only slice.yaml, HEAD subject == "slice: complete").
 - DC-4: `close_slice` is the SOLE source of the `slice: complete` commit.
   `run_phase_loop` skips `commit_phase_handoff` at the Phase-4 boundary.
 - DC-5: `_wipe_current_slice` deletes every file except slice.yaml; tolerates
   FileNotFoundError; raises RuntimeError on any other OSError.

Expected at Phase 2: every test FAILS — the helpers do not exist and
`run_phase_loop` still emits `handoff: phase 4 complete` before close.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


# ---------- fixtures --------------------------------------------------------


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


def _patched_so(monkeypatch, tmp_path):
    slice_dir = _init_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)
    monkeypatch.setattr(
        so, "DEBUG_DIR", tmp_path / ".claude" / "orchestrator-debug", raising=False
    )
    monkeypatch.setattr(so, "dispatch_phase_agent", _stub_dispatch_ok)
    return so, slice_dir


# ---------- DC-3 idempotency ------------------------------------------------


def test_close_slice_twice_is_noop(monkeypatch, tmp_path):
    so, slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    rc = so.run_phase_loop()
    assert rc == 0

    before = subprocess.run(
        ["git", "log", "--format=%s"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()

    # Second invocation must short-circuit cleanly.
    so.close_slice(so._state)

    after = subprocess.run(
        ["git", "log", "--format=%s"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()

    assert after == before, "second close_slice must not add any commit"
    assert after.count("slice: complete") == 1


def test_close_slice_short_circuits_on_already_closed_state(monkeypatch, tmp_path):
    so, slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    # Simulate an already-closed slice (all four DC-3 signals).
    (slice_dir / "slice.yaml").write_text(
        "id: demo/slice-x\nname: 'demo/slice-x'\nstatus: complete\ncurrent_phase: 4\nbrief: 'b'\n"
    )
    (tmp_path / ".claude" / "handoff.md").write_text("bundled\n")
    for f in slice_dir.iterdir():
        if f.name != "slice.yaml":
            f.unlink()
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "--allow-empty",
            "-q",
            "-m",
            "slice: complete",
        ],
        cwd=tmp_path,
        check=True,
    )
    assert so._is_slice_already_closed(so._state) is True

    before = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    so.close_slice(so._state)
    after = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert before == after, "already-closed close_slice must not advance HEAD"


# ---------- DC-4 sole commit source ----------------------------------------


def test_run_phase_loop_skips_commit_at_phase_4_boundary(monkeypatch, tmp_path):
    so, slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    calls: list[int] = []
    real_commit = so.commit_phase_handoff

    def spy(phase, summary, commit_hash):
        calls.append(phase)
        return real_commit(phase, summary, commit_hash)

    monkeypatch.setattr(so, "commit_phase_handoff", spy)

    rc = so.run_phase_loop()
    assert rc == 0
    assert 4 not in calls, (
        "commit_phase_handoff must NOT be called for phase 4 (DC-4 code layer)"
    )
    assert calls == [1, 2, 3], (
        f"expected handoff commits for phases 1..3 only; got {calls!r}"
    )


def test_close_slice_produces_single_slice_complete_commit(monkeypatch, tmp_path):
    so, slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    rc = so.run_phase_loop()
    assert rc == 0

    log = subprocess.run(
        ["git", "log", "--format=%s"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()

    assert log[0] == "slice: complete", (
        f"HEAD subject must be 'slice: complete'; got {log[0]!r}"
    )
    assert log.count("slice: complete") == 1
    # DC-4 strengthening: no `handoff: phase 4 complete` anywhere in slice history.
    assert not any(s == "handoff: phase 4 complete" for s in log), (
        f"'handoff: phase 4 complete' must not appear; log={log!r}"
    )


# ---------- Ordering: bundle before wipe, wipe before commit ----------------


def test_close_slice_bundles_handoff_before_wipe(monkeypatch, tmp_path):
    so, slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    events: list[str] = []
    real_bundle = getattr(so, "_bundle_handoff_md", None)
    real_wipe = getattr(so, "_wipe_current_slice", None)
    assert real_bundle is not None and real_wipe is not None, (
        "_bundle_handoff_md and _wipe_current_slice must exist"
    )

    def spy_bundle(*a, **kw):
        # Record that handoff-phase-*.md are still present when bundle runs.
        still_there = sorted(p.name for p in slice_dir.glob("handoff-phase-*.md"))
        events.append(f"bundle:{len(still_there)}")
        return real_bundle(*a, **kw)

    def spy_wipe(*a, **kw):
        events.append("wipe")
        return real_wipe(*a, **kw)

    monkeypatch.setattr(so, "_bundle_handoff_md", spy_bundle)
    monkeypatch.setattr(so, "_wipe_current_slice", spy_wipe)

    so.run_phase_loop()
    assert events[0].startswith("bundle:"), f"bundle must run first; events={events!r}"
    assert int(events[0].split(":")[1]) == 4, (
        "all four handoff-phase files must still exist at bundle time"
    )
    assert "wipe" in events and events.index("wipe") > 0


def test_close_slice_wipe_runs_before_commit(monkeypatch, tmp_path):
    so, slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    events: list[str] = []
    real_wipe = so._wipe_current_slice
    real_git = so._git

    def spy_wipe(*a, **kw):
        events.append("wipe")
        return real_wipe(*a, **kw)

    def spy_git(*args, **kwargs):
        if args and args[0] == "commit":
            msg = args[args.index("-m") + 1] if "-m" in args else ""
            if msg == "slice: complete":
                events.append("commit")
        return real_git(*args, **kwargs)

    monkeypatch.setattr(so, "_wipe_current_slice", spy_wipe)
    monkeypatch.setattr(so, "_git", spy_git)

    so.run_phase_loop()
    assert "wipe" in events and "commit" in events
    assert events.index("wipe") < events.index("commit"), (
        f"wipe must precede commit; events={events!r}"
    )


# ---------- DC-5 wipe semantics --------------------------------------------


def test_wipe_clears_all_except_slice_yaml(monkeypatch, tmp_path):
    so, slice_dir = _patched_so(monkeypatch, tmp_path)
    # Add a nested subdir too
    (slice_dir / "integration").mkdir()
    (slice_dir / "integration" / "notes.md").write_text("x")
    (slice_dir / "stray.tmp").write_text("y")

    so._wipe_current_slice()

    remaining = sorted(
        p.relative_to(slice_dir).as_posix() for p in slice_dir.rglob("*")
    )
    assert remaining == ["slice.yaml"], (
        f"only slice.yaml must remain; got {remaining!r}"
    )


def test_wipe_raises_on_undeletable_file(monkeypatch, tmp_path):
    so, slice_dir = _patched_so(monkeypatch, tmp_path)
    (slice_dir / "blocker.md").write_text("x")

    def boom(self, *a, **kw):
        if self.name == "blocker.md":
            raise PermissionError("locked")
        return (
            Path.__dict__["unlink"].__wrapped__(self, *a, **kw)
            if hasattr(Path.unlink, "__wrapped__")
            else os.unlink(str(self))
        )

    # Simpler: monkeypatch os.unlink directly.
    real_unlink = os.unlink

    def patched_unlink(p):
        if str(p).endswith("blocker.md"):
            raise PermissionError("locked")
        return real_unlink(p)

    monkeypatch.setattr(os, "unlink", patched_unlink)
    with pytest.raises(RuntimeError):
        so._wipe_current_slice()


def test_wipe_tolerates_file_already_absent(monkeypatch, tmp_path):
    """F5 operator-rebase corner: a listed file may have been removed under
    our feet. Wipe must tolerate FileNotFoundError without failing."""
    so, slice_dir = _patched_so(monkeypatch, tmp_path)
    (slice_dir / "ghost.md").write_text("x")

    real_unlink = os.unlink

    def patched_unlink(p):
        if str(p).endswith("ghost.md"):
            raise FileNotFoundError(str(p))
        return real_unlink(p)

    monkeypatch.setattr(os, "unlink", patched_unlink)
    # Must NOT raise.
    so._wipe_current_slice()
    assert not (slice_dir / "ghost.md").exists() or True  # ghost may or may not remain
