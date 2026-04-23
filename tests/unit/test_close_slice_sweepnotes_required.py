"""Phase 2 RED — compression/phase-4-sweepnotes-required §D2 (INV-008 DC-4).

`close_slice` MUST verify `.claude/current-slice/integration/sweep-notes.md`
exists as a file on disk BEFORE issuing the sole `slice: <id> — complete`
commit. When the file is absent and the slice is NOT already closed:

  * close_slice aborts with a non-zero exit code (existing FAILED-terminal
    pattern, i.e. ``sys.exit`` / ``SystemExit`` with ``code != 0``).
  * No `slice: complete` commit is appended to HEAD.
  * `slice.yaml` is NOT advanced to ``status: complete`` — it remains
    ``in-progress`` (D4 resume-reconciliation precondition).
  * The current-slice tree is NOT wiped.
  * The terminal observability artifact (``<slug>-result.json``) records
    ``status == "FAILED"`` and a stable machine-readable reason token
    ``reason == "sweepnotes-missing-at-close"``.
  * stderr carries a single line referencing the absent sweep-notes path
    so operators can diagnose without tailing debug logs.

The check is gated on the `_is_slice_already_closed(state)` early-return:
if the slice is already closed (wipe already applied — sweep-notes has
correctly been removed), the presence check is bypassed. That path is
exercised by the existing `test_close_slice_twice_is_noop` in
`test_close_slice_hardened.py` and is NOT re-asserted here.

Expected at Phase 2: every test FAILS. `close_slice` today stages and
commits unconditionally; there is no sweep-notes presence gate.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest


# ---------- fixtures --------------------------------------------------------


REASON_TOKEN = "sweepnotes-missing-at-close"


def _init_project(tmp_path: Path) -> Path:
    """Build a tmp git repo with a fresh in-progress slice fixture.

    No integration/sweep-notes.md is created — that absence is the
    precondition for the RED path under test.
    """
    slice_dir = tmp_path / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True)
    (slice_dir / "slice.yaml").write_text(
        "id: demo/slice-x\n"
        'name: "demo/slice-x"\n'
        "status: in-progress\n"
        "current_phase: 4\n"
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
    # Repo-level git identity so subsequent `_git("commit", ...)` calls from
    # close_slice succeed without inheriting the caller's global config.
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    return slice_dir


def _patched_so(monkeypatch, tmp_path):
    slice_dir = _init_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    import slice_orchestrator as so

    monkeypatch.setattr(so, "SLICE_YAML", slice_dir / "slice.yaml", raising=False)
    monkeypatch.setattr(
        so, "DEBUG_DIR", tmp_path / ".claude" / "orchestrator-debug", raising=False
    )
    return so, slice_dir


def _git_log_subjects(cwd):
    return subprocess.run(
        ["git", "log", "--format=%s"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()


# ---------- presence check: abort path --------------------------------------


def test_missing_sweepnotes_raises_systemexit_with_nonzero_code(
    monkeypatch, tmp_path, capsys
):
    """close_slice must exit non-zero when sweep-notes.md is absent."""
    so, _slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    assert not (
        tmp_path / ".claude" / "current-slice" / "integration" / "sweep-notes.md"
    ).exists(), "fixture precondition: sweep-notes.md must be absent"

    with pytest.raises(SystemExit) as excinfo:
        so.close_slice(so._state)

    # SystemExit(None) → code is None → falsy (treated as 0). Require strictly
    # non-zero so the shell observes a failure.
    assert excinfo.value.code not in (0, None), (
        f"close_slice must exit non-zero on missing sweep-notes; "
        f"got code={excinfo.value.code!r}"
    )


def test_missing_sweepnotes_does_not_add_slice_complete_commit(monkeypatch, tmp_path):
    """HEAD must be unchanged — no `slice: complete` commit appears."""
    so, _slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    pre_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    pre_log = _git_log_subjects(tmp_path)

    try:
        so.close_slice(so._state)
    except SystemExit:
        pass

    post_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    post_log = _git_log_subjects(tmp_path)

    assert pre_head == post_head, (
        f"HEAD must not advance when sweep-notes is missing; "
        f"pre={pre_head!r} post={post_head!r}"
    )
    assert pre_log == post_log, (
        f"no new commits must be appended; pre={pre_log!r} post={post_log!r}"
    )
    complete_rx = re.compile(r"^slice: .+ — complete$")
    assert not any(complete_rx.match(s) for s in post_log), (
        f"no `slice: <id> — complete` commit may appear; log={post_log!r}"
    )


def test_missing_sweepnotes_leaves_slice_yaml_in_progress(monkeypatch, tmp_path):
    """slice.yaml status must remain `in-progress` (D4 precondition)."""
    so, slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    try:
        so.close_slice(so._state)
    except SystemExit:
        pass

    import yaml

    sy = yaml.safe_load((slice_dir / "slice.yaml").read_text())
    assert isinstance(sy, dict)
    assert sy.get("status") == "in-progress", (
        "slice.yaml must stay `in-progress` on FAILED-on-missing-sweepnotes; "
        f"got status={sy.get('status')!r}"
    )


def test_missing_sweepnotes_does_not_wipe_current_slice(monkeypatch, tmp_path):
    """The current-slice tree must survive an aborted close untouched."""
    so, slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    pre_files = sorted(
        p.relative_to(slice_dir).as_posix() for p in slice_dir.rglob("*") if p.is_file()
    )

    try:
        so.close_slice(so._state)
    except SystemExit:
        pass

    post_files = sorted(
        p.relative_to(slice_dir).as_posix() for p in slice_dir.rglob("*") if p.is_file()
    )

    assert post_files == pre_files, (
        "current-slice must not be wiped when close aborts; "
        f"pre={pre_files!r} post={post_files!r}"
    )


# ---------- terminal observability on the FAILED branch --------------------


def test_missing_sweepnotes_persists_failed_result_with_stable_reason(
    monkeypatch, tmp_path
):
    """orchestrator result json records status=FAILED + stable reason token."""
    so, _slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    try:
        so.close_slice(so._state)
    except SystemExit:
        pass

    result_json = (
        tmp_path / ".claude" / "orchestrator-debug" / "demo-slice-x-result.json"
    )
    assert result_json.exists(), (
        f"close_slice must persist orchestrator-result.json on FAILED branch; "
        f"missing at {result_json}"
    )
    payload = json.loads(result_json.read_text())
    assert payload.get("status") == "FAILED", (
        f"status must be FAILED; got {payload.get('status')!r}"
    )
    exit_code = payload.get("exit_code")
    assert exit_code not in (0, None), (
        f"exit_code must be non-zero on FAILED terminal; got {exit_code!r}"
    )
    assert payload.get("reason") == REASON_TOKEN, (
        f"reason token must be the stable literal {REASON_TOKEN!r}; "
        f"got {payload.get('reason')!r}"
    )


def test_missing_sweepnotes_emits_stderr_citing_path(monkeypatch, tmp_path, capsys):
    """stderr must carry a diagnostic line naming the absent path."""
    so, _slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    try:
        so.close_slice(so._state)
    except SystemExit:
        pass

    captured = capsys.readouterr()
    # The operator diagnostic must name the file; substring match keeps the
    # assertion resilient to wording changes beyond the path + status cue.
    assert "sweep-notes.md" in captured.err, (
        f"stderr must name the absent `sweep-notes.md`; got stderr={captured.err!r}"
    )


# ---------- ordering: presence check fires BEFORE slice.yaml mutation ------


def test_presence_check_runs_before_slice_yaml_is_rewritten(monkeypatch, tmp_path):
    """If the check ran AFTER slice.yaml had been advanced to `complete`, a
    failed close would leave slice.yaml in an inconsistent terminal state
    with no accompanying commit. The check must therefore run first."""
    so, slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    pre_yaml = (slice_dir / "slice.yaml").read_text()

    try:
        so.close_slice(so._state)
    except SystemExit:
        pass

    post_yaml = (slice_dir / "slice.yaml").read_text()
    assert pre_yaml == post_yaml, (
        "slice.yaml must be byte-identical after an aborted close "
        "(presence check must precede the status=complete write); "
        f"pre={pre_yaml!r} post={post_yaml!r}"
    )
