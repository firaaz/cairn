"""Validation tests for slice housekeeping/post-slice-a-tidy.

Tests map 1:1 to intent.md verification items 1-5 and item 8. Items 6-7
(full suite + architecture validator) are Phase 4 whole-tree checks, not
Phase-2 fixtures.

RED/GREEN key at Phase 2 commit:
- Item A ruff F841 --- RED (line 147 still contains unused `calls` var)
- Item A pytest state-machine --- GREEN guard (no pre-existing failures in that file)
- Item B gitignore drift detector --- GREEN guard (untracked-after-close assertion retired; contradicts INV-008 D2)
- Item C platform-probe retired --- RED (file still tracked)
- Item D empty current-slice subdirs --- GREEN guard (pruned at a09e5e8)
- Item 8 dogfooding findings in sweep-notes.md --- RED (sweep-notes not yet written)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_MACHINE_TEST = REPO_ROOT / "tests/unit/test_slice_orchestrator_state_machine.py"
GITIGNORE = REPO_ROOT / ".gitignore"
HANDOFF = REPO_ROOT / ".claude/handoff.md"
PLATFORM_PROBE = REPO_ROOT / ".claude/platform-probe.md"
CURRENT_SLICE = REPO_ROOT / ".claude/current-slice"
SWEEP_NOTES = CURRENT_SLICE / "integration/sweep-notes.md"


def _run(cmd, cwd=None):
    return subprocess.run(
        cmd, cwd=cwd or REPO_ROOT, capture_output=True, text=True, check=False
    )


# --- Item A: F841 fix in state-machine test file -----------------------------


def test_item_a_ruff_no_f841_in_state_machine_test():
    result = _run(["uv", "run", "ruff", "check", str(STATE_MACHINE_TEST)])
    combined = (result.stdout or "") + (result.stderr or "")
    assert "F841" not in combined, (
        f"ruff reported F841 on {STATE_MACHINE_TEST.name}:\n{combined}"
    )


def test_item_a_state_machine_target_function_still_passes():
    """Successor to the prior-slice guard. The original target
    `test_v2_5_run_phase_loop_ok_advances_phase` was retired in
    compression/slice-1-foundation when the dispatch contract split
    (dispatch_phase_agent + dispatch_triager) replaced the dispatch_agent
    monkeypatch point. The equivalent state-machine assertion now lives in
    tests/integration/test_compressed_slice_end_to_end.py::test_v6_state_machine_runs_end_to_end.
    """
    target = "tests/integration/test_compressed_slice_end_to_end.py::test_v6_state_machine_runs_end_to_end"
    result = _run(["uv", "run", "python", "-m", "pytest", target])
    assert result.returncode == 0, (
        f"{target} must pass as the state-machine regression guard.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


# --- Item B: .claude/handoff.md gitignore drift guard ------------------------


def test_item_b_handoff_path_in_gitignore():
    text = GITIGNORE.read_text()
    assert ".claude/handoff.md" in text, (
        ".gitignore must continue to ignore .claude/handoff.md (intent item B)"
    )


# --- Item C: .claude/platform-probe.md retirement ----------------------------


def test_item_c_platform_probe_not_tracked():
    result = _run(["git", "ls-files", str(PLATFORM_PROBE.relative_to(REPO_ROOT))])
    assert result.stdout.strip() == "", (
        f".claude/platform-probe.md must be removed from the git index; "
        f"git ls-files returned:\n{result.stdout!r}"
    )


def test_item_c_platform_probe_not_in_working_tree():
    assert not PLATFORM_PROBE.exists(), (
        f"{PLATFORM_PROBE} must be removed from the working tree "
        "(slice-scoped artifact superseded by closed compression/infrastructure slice)"
    )


# --- Item D: no stray empty subdirs in .claude/current-slice/ ----------------


def test_item_d_no_empty_current_slice_subdirs():
    allowed_non_empty = {"validation", "implementation", "integration"}
    offenders = []
    for child in sorted(CURRENT_SLICE.iterdir()):
        if not child.is_dir():
            continue
        if child.name not in allowed_non_empty:
            offenders.append(f"unexpected dir: {child}")
            continue
        entries = list(child.iterdir())
        if not entries:
            offenders.append(f"empty dir: {child}")
    assert not offenders, (
        ".claude/current-slice/ must contain no stray/empty subdirs; found:\n"
        + "\n".join(offenders)
    )


# --- Item 8: dogfooding findings persisted in sweep-notes.md -----------------


def test_item_8_dogfooding_findings_section_in_sweep_notes():
    """Retired: slice close wipes .claude/current-slice/, so the prior
    slice's sweep-notes.md is not expected to persist in this working tree.
    Kept as a marker until the housekeeping/post-slice-a-tidy intent.md
    verification is re-anchored in a successor slice.
    """
    import pytest

    pytest.skip(
        "sweep-notes.md for housekeeping/post-slice-a-tidy was wiped at "
        "slice close per the pipeline's standard close sequence; this "
        "verification belonged to that closed slice and has no current-slice analogue."
    )
