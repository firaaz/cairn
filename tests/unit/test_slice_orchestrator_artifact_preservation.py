"""Phase 2 RED — ADR slice-artifact-preservation: pre-wipe snapshot of phase ephemerals.

Decisions covered (labels match docs/adr/slice-artifact-preservation.md and
the implementing plan docs/plans/2026-04-26-slice-artifact-preservation-plan.md):

  D1 — copy step ordering (between bundle and wipe in close_slice)
  D2 — snapshot scope (9 artifact paths + the pre-close slice.yaml text)
  D2.vii — pre-close slice.yaml captured BEFORE Step 1 mutates status
  D6a — idempotency on re-invocation
  D6b — F5-tolerance for missing source files (skip silently, no raise)
  D7 / (c) — operational copy failure (ENOSPC, EACCES) loud-fails

Imports use `slice_orchestrator` (not `scripts.slice_orchestrator`) because
pyproject.toml [tool.pytest.ini_options] declares `pythonpath = ["scripts"]`,
making `slice_orchestrator` the top-level package on sys.path. Patch targets
mirror that resolution.

Expected at Phase 2: ALL tests FAIL with
  `AttributeError: module 'slice_orchestrator.lifecycle' has no attribute
   '_copy_artifacts_to_sweep_results'`
or equivalent — the helper does not yet exist. Phase 3 implementation makes
them GREEN by adding the helper and wiring it into `close_slice`.
"""

from __future__ import annotations

import errno
from pathlib import Path
from unittest.mock import patch

import pytest

from slice_orchestrator import lifecycle


SLICE_ID = "compression/slice-artifact-preservation-test"
SLUG = "compression-slice-artifact-preservation-test"  # forward-slash → dash

# 9 source paths (relative to .claude/current-slice/) the helper must snapshot.
ARTIFACT_FILES = [
    "intent.md",
    "validation/approach.md",
    "implementation/notes.md",
    "integration/sweep-notes.md",
    "handoff-phase-1.md",
    "handoff-phase-2.md",
    "handoff-phase-3.md",
    "handoff-phase-4.md",
    "envelope-expansions.log",
]


@pytest.fixture
def populated_current_slice(tmp_path, monkeypatch):
    """Build a .claude/current-slice/ tree with all 9 artifact files populated."""
    monkeypatch.chdir(tmp_path)
    cs = tmp_path / ".claude" / "current-slice"
    cs.mkdir(parents=True)
    (cs / "validation").mkdir()
    (cs / "implementation").mkdir()
    (cs / "integration").mkdir()
    for rel in ARTIFACT_FILES:
        p = cs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"content of {rel}\n")
    yield cs


# --- D2: snapshot scope, byte-identity per artifact ----------------------------


def test_d2_handoff_phase_files_copied_byte_identical(populated_current_slice):
    """All four handoff-phase-{1..4}.md snapshots are byte-identical to source."""
    pre_close_yaml = "id: " + SLICE_ID + "\nstatus: in-progress\n"
    lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
    target = Path(".claude/sweep-results") / SLUG / "artifacts"
    for n in (1, 2, 3, 4):
        src = populated_current_slice / f"handoff-phase-{n}.md"
        dst = target / f"handoff-phase-{n}.md"
        assert dst.read_bytes() == src.read_bytes(), (
            f"mismatch for handoff-phase-{n}.md"
        )


def test_d2_phase_artifact_files_copied_byte_identical(populated_current_slice):
    """intent / approach / notes / sweep-notes / envelope-expansions.log are byte-identical."""
    pre_close_yaml = "id: " + SLICE_ID + "\n"
    lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
    target = Path(".claude/sweep-results") / SLUG / "artifacts"
    for rel in (
        "intent.md",
        "validation/approach.md",
        "implementation/notes.md",
        "integration/sweep-notes.md",
        "envelope-expansions.log",
    ):
        src = populated_current_slice / rel
        dst = target / rel
        assert dst.read_bytes() == src.read_bytes(), f"mismatch for {rel}"


def test_d2_pre_close_slice_yaml_captured_not_post_close(populated_current_slice):
    """slice.yaml in artifacts/ contains the pre-close text, not status=complete."""
    pre_close_yaml = "id: " + SLICE_ID + "\nstatus: in-progress\ncurrent_phase: 4\n"
    lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
    target = Path(".claude/sweep-results") / SLUG / "artifacts"
    snapshot = (target / "slice.yaml").read_text()
    assert snapshot == pre_close_yaml
    assert "status: in-progress" in snapshot
    assert "status: complete" not in snapshot


# --- D6b: F5-tolerance for missing source files --------------------------------


def test_d6b_missing_source_skips_silently(tmp_path, monkeypatch):
    """Operator-rebase corner: source file gone → skip-and-proceed, no raise."""
    monkeypatch.chdir(tmp_path)
    cs = tmp_path / ".claude" / "current-slice"
    cs.mkdir(parents=True)
    # Only intent.md exists; the other artifacts are absent.
    (cs / "intent.md").write_text("only intent\n")
    pre_close_yaml = "id: " + SLICE_ID + "\n"
    # MUST NOT raise.
    lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
    target = Path(".claude/sweep-results") / SLUG / "artifacts"
    assert (target / "intent.md").read_text() == "only intent\n"
    assert not (target / "handoff-phase-1.md").exists()
    assert not (target / "validation" / "approach.md").exists()
    # Pre-close yaml is always written (D2.vii caller-supplied).
    assert (target / "slice.yaml").read_text() == pre_close_yaml


# --- D7 / (c): operational copy failure loud-fails -----------------------------


def test_c_operational_copy_failure_raises(populated_current_slice):
    """Disk-full during copyfile → propagate OSError, do not silently skip."""
    pre_close_yaml = "id: " + SLICE_ID + "\n"

    def _disk_full(*args, **kwargs):
        raise OSError(errno.ENOSPC, "No space left on device")

    with patch("slice_orchestrator.lifecycle.shutil.copyfile", side_effect=_disk_full):
        with pytest.raises(OSError) as excinfo:
            lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
    assert excinfo.value.errno == errno.ENOSPC


def test_c_target_dir_creation_failure_raises(populated_current_slice):
    """Permission-denied on target dir creation → propagate OSError."""
    pre_close_yaml = "id: " + SLICE_ID + "\n"

    def _perm_denied(*args, **kwargs):
        raise OSError(errno.EACCES, "Permission denied")

    with patch("slice_orchestrator.lifecycle.os.makedirs", side_effect=_perm_denied):
        with pytest.raises(OSError) as excinfo:
            lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
    assert excinfo.value.errno == errno.EACCES


# --- D6a: idempotency on re-invocation -----------------------------------------


def test_d6a_helper_idempotent_on_repeat_invocation(populated_current_slice):
    """Second invocation with same slice_id over identical sources is a no-op
    in observable effect: target file content unchanged, no raise."""
    pre_close_yaml = "id: " + SLICE_ID + "\n"
    lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
    target = Path(".claude/sweep-results") / SLUG / "artifacts"
    first = (target / "intent.md").read_bytes()
    # Second call over identical sources — must not raise; content stable.
    # (Idempotency at helper level = no-error-on-rerun, not freeze-on-first-run;
    # DC-3 short-circuit at close_slice level prevents real re-runs in prod.)
    lifecycle._copy_artifacts_to_sweep_results(SLICE_ID, pre_close_yaml)
    second = (target / "intent.md").read_bytes()
    assert first == second  # source unchanged → target unchanged


# --- D1 ordering: copy populates target BEFORE wipe destroys sources -----------


class _FakeProc:
    stdout = ""
    returncode = 0


def test_d1_close_slice_copies_before_wipe(populated_current_slice, monkeypatch):
    """Integration: close_slice end-to-end populates artifacts/ AND wipes
    current-slice/. The artifacts dir must contain intent.md and a slice.yaml
    with `status: in-progress` (proof: copy ran before the wipe and used the
    pre-close yaml capture, not the post-mutation form)."""
    # Stub git invocations so commit step is inert.
    monkeypatch.setattr(lifecycle, "_git", lambda *a, **kw: _FakeProc())
    monkeypatch.setattr(lifecycle, "_git_head_safe", lambda: "deadbeef")
    # Write a real slice.yaml so close_slice can read pre-close text from it.
    sy_path = populated_current_slice / "slice.yaml"
    sy_path.write_text("id: " + SLICE_ID + "\nstatus: in-progress\ncurrent_phase: 4\n")
    monkeypatch.setattr(lifecycle, "SLICE_YAML", sy_path)

    lifecycle.close_slice()

    target = Path(".claude/sweep-results") / SLUG / "artifacts"
    # Copy step ran before wipe: artifacts populated.
    assert (target / "intent.md").exists()
    snap = (target / "slice.yaml").read_text()
    assert snap.startswith("id: " + SLICE_ID)
    # D2.vii: capture happened BEFORE Step 1 mutated status.
    assert "status: in-progress" in snap
    assert "status: complete" not in snap
    # Wipe ran (DC-5): only slice.yaml survives in current-slice/.
    survivors = sorted(
        p.relative_to(populated_current_slice).as_posix()
        for p in populated_current_slice.rglob("*")
        if p.is_file()
    )
    assert survivors == ["slice.yaml"], f"unexpected survivors: {survivors}"
