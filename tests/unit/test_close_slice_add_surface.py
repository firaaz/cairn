"""Phase 2 RED — compression/phase-4-sweepnotes-required §Add-surface.

`close_slice` MUST stage every path that the Phase-4 agent is contracted
to write (`.claude/agents/phase-4-integrator.md:9`). Specifically the
sole `slice: <id> — complete` commit tree must contain:

  * ``.claude/handoff.md`` — already produced by ``_bundle_handoff_md``
    and covered by the existing ``-f`` add; re-asserted here as a
    regression guard for the add-surface extension.
  * ``.claude/sweep.yaml`` — currently orphaned (outside the add list).
    RED today.
  * any newly-created file under ``.claude/sweep-results/`` — currently
    orphaned; must be staged wholesale via ``git add -A`` semantics so
    close_slice need not enumerate filenames. RED today.

This is the concrete fix for the orphan-artifact pattern observed in
commit a8d8f23 (intent.md §What/Why). No new commit site is introduced
— the extension grows the existing staging block in close_slice, which
remains the sole producer of `slice: <id> — complete` (INV-008 DC-4).

Each test stages its inputs on disk (simulating a real phase-4 agent
write), then runs ``close_slice`` with a valid ``integration/sweep-notes.md``
so the primary presence check passes. After close, the tests inspect
``git show HEAD:<path>`` on the resulting `slice: complete` commit to
assert the content is reachable from the commit tree.

Expected at Phase 2: the handoff.md regression test passes today; the
sweep.yaml and sweep-results tests FAIL because close_slice's current
add list (``scripts/slice_orchestrator.py:1766-1770``) does not cover
those paths.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


# ---------- fixtures --------------------------------------------------------


def _init_project(tmp_path: Path) -> Path:
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
    # sweep-notes.md present → the D2 presence check passes and the close
    # proceeds into the staging block under test.
    integ = slice_dir / "integration"
    integ.mkdir()
    (integ / "sweep-notes.md").write_text("SWEEP-NOTES-BODY\nINV-008 DC-4 PASS\n")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
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


def _assert_head_is_slice_complete(cwd):
    subject = subprocess.run(
        ["git", "log", "-1", "--format=%s"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert re.match(r"^slice: .+ — complete$", subject), (
        f"HEAD subject must match `slice: <id> — complete`; got {subject!r}"
    )


def _git_show(cwd, rev_path):
    """Return (returncode, stdout) for `git show <rev_path>`.

    Non-zero return code means the path is NOT in the commit tree.
    """
    proc = subprocess.run(
        ["git", "show", rev_path],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout


# ---------- handoff.md regression (anti-regression; should stay GREEN) -----


def test_handoff_md_appears_in_slice_complete_commit_tree(monkeypatch, tmp_path):
    """Regression guard: the add-surface extension must not drop handoff.md."""
    so, _slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    so.close_slice(so._state)

    _assert_head_is_slice_complete(tmp_path)
    rc, body = _git_show(tmp_path, "HEAD:.claude/handoff.md")
    assert rc == 0, (
        f"`.claude/handoff.md` must be in the slice: complete commit tree; "
        f"`git show` returned rc={rc}"
    )
    # Bundle is the concatenation of the four handoff-phase-*.md files.
    assert "phase-1-body" in body and "phase-4-body" in body, (
        f"handoff.md bundle content unexpected; body={body!r}"
    )


# ---------- sweep.yaml (RED — not staged today) -----------------------------


def test_sweep_yaml_content_appears_in_slice_complete_commit_tree(
    monkeypatch, tmp_path
):
    """`.claude/sweep.yaml` written by phase-4 must land in the commit tree."""
    so, _slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    # Simulate phase-4-integrator having written .claude/sweep.yaml prior to
    # close_slice running.
    sweep_yaml = tmp_path / ".claude" / "sweep.yaml"
    sweep_yaml.write_text(
        "schema_version: 1\ninvariants:\n  - id: INV-008\n    status: PASS\n"
    )

    so.close_slice(so._state)

    _assert_head_is_slice_complete(tmp_path)
    rc, body = _git_show(tmp_path, "HEAD:.claude/sweep.yaml")
    assert rc == 0, (
        "`.claude/sweep.yaml` must appear in the slice: complete commit tree; "
        f"`git show HEAD:.claude/sweep.yaml` returned rc={rc} "
        "(likely orphaned outside the add list)"
    )
    assert "INV-008" in body, (
        f"staged sweep.yaml content missing expected token; body={body!r}"
    )


def test_modified_sweep_yaml_reaches_commit_tree_even_when_preexisting(
    monkeypatch, tmp_path
):
    """Second case: sweep.yaml already tracked but modified in working tree.

    Reproduces the orphan-artifact pattern where a pre-existing tracked
    ``.claude/sweep.yaml`` is re-written by phase-4 but the update never
    reaches the slice-complete commit because the staging block does not
    re-add it.
    """
    so, _slice_dir = _patched_so(monkeypatch, tmp_path)

    # Seed a tracked sweep.yaml (staged by the fixture's `git add -A`).
    sweep_yaml = tmp_path / ".claude" / "sweep.yaml"
    sweep_yaml.write_text("schema_version: 1\nold: true\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "seed sweep.yaml"],
        cwd=tmp_path,
        check=True,
    )

    so._init_state_dict(slice_id="demo/slice-x")

    # Phase-4 rewrites sweep.yaml with new content.
    sweep_yaml.write_text(
        "schema_version: 1\nold: false\nrefresh_token: PHASE-4-UPDATE\n"
    )

    so.close_slice(so._state)

    _assert_head_is_slice_complete(tmp_path)
    rc, body = _git_show(tmp_path, "HEAD:.claude/sweep.yaml")
    assert rc == 0, f"`.claude/sweep.yaml` must be addressable at HEAD; rc={rc}"
    assert "PHASE-4-UPDATE" in body, (
        "updated sweep.yaml content must be present in the slice: complete "
        f"commit tree (orphan-artifact pattern); body={body!r}"
    )


# ---------- sweep-results/ (RED — new files under subdir not staged today) -


def test_new_sweep_result_file_appears_in_slice_complete_commit_tree(
    monkeypatch, tmp_path
):
    """New files under ``.claude/sweep-results/`` must be staged wholesale.

    The spec calls for ``git add -A .claude/sweep-results/`` semantics so
    close_slice does not need to enumerate filenames.
    """
    so, _slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    results_dir = tmp_path / ".claude" / "sweep-results"
    results_dir.mkdir()
    (results_dir / "invariant-INV-008.md").write_text(
        "# INV-008 sweep result\nstatus: PASS\n"
    )
    (results_dir / "validator.txt").write_text("validate_architecture: OK\n")

    so.close_slice(so._state)

    _assert_head_is_slice_complete(tmp_path)

    rc1, body1 = _git_show(tmp_path, "HEAD:.claude/sweep-results/invariant-INV-008.md")
    assert rc1 == 0, (
        "new file `.claude/sweep-results/invariant-INV-008.md` must be in "
        f"the slice: complete commit tree; `git show` returned rc={rc1}"
    )
    assert "INV-008 sweep result" in body1

    rc2, body2 = _git_show(tmp_path, "HEAD:.claude/sweep-results/validator.txt")
    assert rc2 == 0, (
        "new file `.claude/sweep-results/validator.txt` must be in the "
        f"slice: complete commit tree; `git show` returned rc={rc2}"
    )
    assert "validate_architecture: OK" in body2


def test_absent_sweep_results_dir_does_not_block_close(monkeypatch, tmp_path):
    """If ``.claude/sweep-results/`` does not exist, close must still
    succeed — the directory is optional (intent §2 tolerance clause)."""
    so, _slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    assert not (tmp_path / ".claude" / "sweep-results").exists(), (
        "fixture precondition: sweep-results/ must be absent"
    )

    # Must not raise; the staging block is tolerant of the missing dir.
    so.close_slice(so._state)

    _assert_head_is_slice_complete(tmp_path)


# ---------- DC-4 invariant: single commit site preserved -------------------


def test_add_surface_extension_does_not_introduce_second_commit_site(
    monkeypatch, tmp_path
):
    """INV-008 DC-4: exactly one `slice: <id> — complete` commit is emitted,
    regardless of how many extra paths the add-surface extension covers."""
    so, _slice_dir = _patched_so(monkeypatch, tmp_path)
    so._init_state_dict(slice_id="demo/slice-x")

    # Populate every path the extended add surface is contracted to cover.
    (tmp_path / ".claude" / "sweep.yaml").write_text("schema_version: 1\n")
    results_dir = tmp_path / ".claude" / "sweep-results"
    results_dir.mkdir()
    (results_dir / "r1.md").write_text("r1\n")
    (results_dir / "r2.md").write_text("r2\n")

    so.close_slice(so._state)

    log = subprocess.run(
        ["git", "log", "--format=%s"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    complete_rx = re.compile(r"^slice: .+ — complete$")
    matches = [s for s in log if complete_rx.match(s)]
    assert len(matches) == 1, (
        "exactly one `slice: <id> — complete` commit must be produced "
        f"(DC-4 sole commit source); got {matches!r} in log={log!r}"
    )
