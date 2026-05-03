"""Phase 2 validation for substrate/papercut-bundle paper-cut #4.

Asserts that ``scripts/verify_handoff.sh`` check (c) accepts ``sweep: ``
as a fourth subject prefix alongside ``handoff:``, ``phase-<N>:``, and
``slice: <anything> — complete``. Also asserts the ``expected one of:``
error message enumerates the new ``sweep:`` form so a future operator
seeing a mismatched subject knows the accepted set.

RED until Phase 3 extends the regex chain at verify_handoff.sh:34-41
and the matching error-message enumeration at line 45.

Pytest + stdlib only. Mirrors the git-fixture style of
``tests/unit/efficiency_program/test_item_04_handoff_verifier.py``.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VERIFIER = PROJECT_ROOT / "scripts" / "verify_handoff.sh"


def _git_env() -> dict[str, str]:
    return {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }


def _init_git_repo(root: Path) -> None:
    env = _git_env()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, env=env)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=root, check=True)


def _commit(root: Path, subject: str) -> None:
    env = _git_env()
    fpath = root / "f"
    fpath.write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "f"], cwd=root, check=True, env=env)
    subprocess.run(
        ["git", "commit", "-q", "-m", subject], cwd=root, check=True, env=env
    )


def _run_verifier(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(VERIFIER)],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(cwd),
    )


# --- Source inspection ------------------------------------------------------


class TestVerifierSource:
    def test_verifier_exists(self) -> None:
        assert VERIFIER.is_file(), f"{VERIFIER} does not exist"

    def test_check_c_regex_chain_accepts_sweep_prefix(self) -> None:
        """The check (c) regex chain must include a ``^sweep:`` arm.
        Match is loose: any line containing both ``grep`` invocation and
        the ``^sweep:`` pattern is acceptable."""
        text = VERIFIER.read_text(encoding="utf-8")
        assert "^sweep:" in text, (
            "verify_handoff.sh check (c) must add a regex arm matching "
            "'^sweep:' (paper-cut #4)"
        )

    def test_error_message_enumerates_sweep_form(self) -> None:
        """The ``expected one of:`` enumeration printed on rejection must
        list the new ``sweep:`` form so operators know it is accepted."""
        text = VERIFIER.read_text(encoding="utf-8")
        assert "expected one of" in text, (
            "verify_handoff.sh must still print an 'expected one of' error "
            "(regression guard against accidental message rewording)"
        )
        assert "sweep:" in text, (
            "the rejection error string must enumerate 'sweep:' as one of "
            "the accepted subject prefixes (paper-cut #4)"
        )


# --- Behavioural: synthetic git repo with a sweep-subject HEAD --------------


class TestSweepSubjectAccepted:
    def test_sweep_subject_passes_check_c(self, tmp_path: Path) -> None:
        """HEAD subject ``sweep: post-demo — PASS`` exercises only check
        (c) (not phase-N: ⇒ checks (a)/(b) skipped). Must exit 0."""
        _init_git_repo(tmp_path)
        _commit(tmp_path, "sweep: post-demo — PASS")
        result = _run_verifier(tmp_path)
        assert result.returncode == 0, (
            "verify_handoff.sh must accept a 'sweep: ...' subject under "
            f"check (c); rc={result.returncode} stderr={result.stderr!r}"
        )
        assert result.stderr.strip() == "", (
            f"sweep-subject pass must have empty stderr; got {result.stderr!r}"
        )

    def test_sweep_subject_with_trailing_label_passes(self, tmp_path: Path) -> None:
        """Real sweep commits carry varied trailing labels (PASS,
        PASS-with-known-debt, FAIL). All must pass check (c) — the
        accepted set widens by prefix only."""
        _init_git_repo(tmp_path)
        _commit(tmp_path, "sweep: 2026-05-02 post-demo — PASS-with-known-debt")
        result = _run_verifier(tmp_path)
        assert result.returncode == 0, (
            "verify_handoff.sh must accept any 'sweep: ...' prefix regardless "
            f"of trailing text; rc={result.returncode} stderr={result.stderr!r}"
        )


# --- Negative regression: non-sweep, non-accepted subjects still rejected ---


class TestRejectionStillEnforced:
    def test_chore_subject_still_rejected(self, tmp_path: Path) -> None:
        """The widened accepted set must NOT degrade rejection of
        unrelated prefixes (e.g. 'chore:'). Stderr should enumerate
        accepted forms including 'sweep:'."""
        _init_git_repo(tmp_path)
        _commit(tmp_path, "chore: unrelated change")
        result = _run_verifier(tmp_path)
        assert result.returncode != 0, (
            "verify_handoff.sh must still reject 'chore:' subjects after "
            f"the widening; rc={result.returncode}"
        )
        assert "sweep:" in result.stderr, (
            "rejection stderr must list 'sweep:' among the accepted forms; "
            f"got {result.stderr!r}"
        )
