"""Phase 2 validation for efficiency-program/all-seven Item 2 — measurements-drift hook idempotency.

Verifies intent.md Item 2 acceptance:
  - Run the session-start hook TWICE on a clean worktree.
  - After the second run, `git status --porcelain` for the measurements artifact
    path must be empty (no chronic `M`).

Two acceptable implementation forms are allowed by the intent:
  - Form A: diff-then-write (hook writes only when contents would change).
  - Form B: relocate the artifact out of the tracked path; old tracked path
    gone, new path exists outside `git ls-files`.

This test accepts EITHER form and fails if neither is observed.

RED phase: the hook currently rewrites the measurement file on every session,
so running it twice leaves the tracked path dirty. Pytest + stdlib only.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MEASUREMENT_REL = "docs/plans/measurements/2026-04-12-slice-003.txt"
MEASUREMENT_ABS = PROJECT_ROOT / MEASUREMENT_REL
NEW_PATH_CANDIDATES_REL = (
    ".claude/measurements/2026-04-12-slice-003.txt",
    ".claude/plans/measurements/2026-04-12-slice-003.txt",
)

# Same candidate set as Item 1 — Phase 3 picks a name; the hook is the same
# SessionStart entry point.
CANDIDATE_HOOK_NAMES = (
    "session-start.sh",
    "role-cheatsheet.sh",
    "session_start.sh",
    "cheatsheet.sh",
    "measurements-refresh.sh",
)


def _find_any_sessionstart_hook() -> Path:
    checks = PROJECT_ROOT / "checks"
    for name in CANDIDATE_HOOK_NAMES:
        candidate = checks / name
        if candidate.is_file():
            return candidate
    pytest.fail(
        "No SessionStart hook found under checks/ — Item 1 or a dedicated "
        f"measurements refresh hook must exist. Tried: {CANDIDATE_HOOK_NAMES}"
    )


def _run_hook_twice(hook: Path) -> tuple[subprocess.CompletedProcess, ...]:
    env = {
        "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
        "HOME": str(PROJECT_ROOT),
        "CLAUDE_PROJECT_DIR": str(PROJECT_ROOT),
    }
    first = subprocess.run(
        ["bash", str(hook)],
        input="{}",
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(PROJECT_ROOT),
        env=env,
    )
    second = subprocess.run(
        ["bash", str(hook)],
        input="{}",
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(PROJECT_ROOT),
        env=env,
    )
    return first, second


def _git_porcelain(path_rel: str) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", path_rel],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(PROJECT_ROOT),
    )
    return result.stdout


def _git_tracked(path_rel: str) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", path_rel],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(PROJECT_ROOT),
    )
    return result.returncode == 0


class TestMeasurementsIdempotency:
    def test_double_invocation_leaves_measurement_path_clean(self):
        """Form A or B — after two invocations the measurement artifact must
        not appear in `git status --porcelain` as modified."""
        hook = _find_any_sessionstart_hook()
        _run_hook_twice(hook)

        porcelain = _git_porcelain(MEASUREMENT_REL)

        # Form B also accepted: the tracked path no longer exists and was
        # removed from git (status will show `D ...` which is also a form of
        # divergence, so we additionally allow the file being gone AND a
        # candidate relocated path existing untracked).
        if porcelain.strip() == "":
            return

        if "D " in porcelain and not MEASUREMENT_ABS.exists():
            relocated = [(PROJECT_ROOT / rel) for rel in NEW_PATH_CANDIDATES_REL]
            if any(p.exists() for p in relocated):
                tracked_anywhere = any(
                    _git_tracked(rel) for rel in NEW_PATH_CANDIDATES_REL
                )
                assert not tracked_anywhere, (
                    "Form B selected but relocated path is tracked by git; "
                    "it must live outside git ls-files (add to .gitignore)"
                )
                return

        pytest.fail(
            "Item 2 FAIL: measurements artifact is dirty after two SessionStart "
            f"invocations. git status --porcelain:\n{porcelain}"
        )

    def test_form_b_tracked_path_absent_when_relocated(self):
        """If Phase 3 chose Form B, the old tracked path must be removed AND a
        relocated path must exist. Skip cleanly if Form A was chosen."""
        if MEASUREMENT_ABS.exists():
            # Form A path — tracked artifact still exists. Not our assertion.
            return
        relocated_exists = any(
            (PROJECT_ROOT / rel).exists() for rel in NEW_PATH_CANDIDATES_REL
        )
        assert relocated_exists, (
            "Old measurement path is gone but no relocated artifact was found "
            f"in any of: {NEW_PATH_CANDIDATES_REL}"
        )

    def test_form_a_preserves_tracked_path_with_clean_status(self):
        """If Phase 3 chose Form A, the tracked path still exists AND is clean
        in `git status` after double invocation."""
        hook = _find_any_sessionstart_hook()
        if not MEASUREMENT_ABS.exists():
            # Form B path — nothing to assert here.
            return
        _run_hook_twice(hook)
        porcelain = _git_porcelain(MEASUREMENT_REL)
        assert porcelain.strip() == "", (
            "Form A: measurements path exists but is dirty after two hook "
            f"runs; porcelain={porcelain!r}"
        )
