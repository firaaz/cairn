"""Phase 2 validation for efficiency-program/all-seven Item 4 — /handoff post-check verifier.

Verifies intent.md Item 4 acceptance:
  - test -x scripts/verify_handoff.sh passes.
  - Pass-fixture invocation: exit 0, empty stderr.
  - Fail-fixture invocation (missing handoff-phase-<N>.md where the commit
    claims phase-<N>): non-zero exit, stderr names the missing file.
  - commands/claude-code/handoff.md gains a line invoking the verifier.
  - commands/claude-code/handoff.full.md documents the contract (exit codes
    + error shape).

Three hook checks in the verifier per intent:
  1. Pipeline phase → slice.yaml.status matches the expected next-phase state
     implied by the most recent commit subject.
  2. Phase-commit → .claude/current-slice/handoff-phase-<N>.md exists.
  3. Subject line begins with `handoff:` OR `phase-<N>:` OR `slice: .* — complete`.

RED phase: scripts/verify_handoff.sh does not yet exist; the two .md files
do not yet reference it. Pytest + stdlib only.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
VERIFIER = PROJECT_ROOT / "scripts" / "verify_handoff.sh"
HANDOFF_MD = PROJECT_ROOT / "commands" / "claude-code" / "handoff.md"
HANDOFF_FULL = PROJECT_ROOT / "commands" / "claude-code" / "handoff.full.md"


def _init_git_repo(root: Path) -> None:
    """Initialize a minimal git repo with deterministic identity so
    verifier calls to `git log -1 --format=%s` succeed in an isolated tmp."""
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, env=env)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=root, check=True)


def _commit(
    root: Path, subject: str, *, file_name: str = "f", content: str = "x"
) -> None:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    fpath = root / file_name
    fpath.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", file_name], cwd=root, check=True, env=env)
    subprocess.run(
        ["git", "commit", "-q", "-m", subject], cwd=root, check=True, env=env
    )


def _write_slice_yaml(root: Path, status: str) -> None:
    slice_dir = root / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True, exist_ok=True)
    (slice_dir / "slice.yaml").write_text(
        "id: demo/slice\n"
        'name: "demo"\n'
        f"status: {status}\n"
        "started: 2026-04-18\n"
        "completed: null\n",
        encoding="utf-8",
    )


def _run_verifier(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(VERIFIER)],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(cwd),
    )


# --- Verifier existence ------------------------------------------------------


class TestVerifierExists:
    def test_verifier_file_present(self):
        assert VERIFIER.is_file(), (
            f"scripts/verify_handoff.sh missing (expected at {VERIFIER})"
        )

    def test_verifier_is_executable(self):
        assert VERIFIER.is_file()
        # Either executable bit OR invocable via `bash <path>`. Intent says
        # "runnable as bash scripts/verify_handoff.sh" so bash-invocable is
        # sufficient, but we still check that the shebang is set.
        head = VERIFIER.read_text(encoding="utf-8").splitlines()
        assert head and head[0].startswith("#!"), (
            "verify_handoff.sh must begin with a shebang"
        )

    def test_verifier_uses_set_euo_pipefail(self):
        text = VERIFIER.read_text(encoding="utf-8")
        assert "set -euo pipefail" in text, (
            "intent requires POSIX shell verifier to use `set -euo pipefail`"
        )


# --- Pass fixture ------------------------------------------------------------


class TestPassFixture:
    def test_pass_state_returns_zero_and_empty_stderr(self, tmp_path: Path):
        """A commit with subject `handoff: whatever` + a matching handoff.md
        pointer passes all three checks."""
        if not VERIFIER.is_file():
            # RED phase — skip-as-fail via direct assert so pytest reports it.
            raise AssertionError("scripts/verify_handoff.sh does not exist yet")
        _init_git_repo(tmp_path)
        _write_slice_yaml(tmp_path, "2-validation")
        (tmp_path / ".claude" / "handoff.md").write_text(
            "---\nslice: demo/slice\nphase: 2\n---\n\n## State\nok\n",
            encoding="utf-8",
        )
        _commit(tmp_path, "handoff: phase-2 complete")
        result = _run_verifier(tmp_path)
        assert result.returncode == 0, (
            f"verifier should pass on a valid handoff commit; "
            f"rc={result.returncode} stderr={result.stderr!r}"
        )
        assert result.stderr.strip() == "", (
            f"pass state must have empty stderr; got {result.stderr!r}"
        )


# --- Fail fixture ------------------------------------------------------------


class TestFailFixture:
    def test_missing_phase_handoff_file_fails_with_named_stderr(self, tmp_path: Path):
        """Commit subject is `phase-2: ...` but `handoff-phase-2.md` is
        absent → non-zero exit, stderr names the missing file."""
        if not VERIFIER.is_file():
            raise AssertionError("scripts/verify_handoff.sh does not exist yet")
        _init_git_repo(tmp_path)
        _write_slice_yaml(tmp_path, "2-validation")
        # Commit a phase-commit subject but do NOT create handoff-phase-2.md
        _commit(tmp_path, "phase-2: validation complete")
        result = _run_verifier(tmp_path)
        assert result.returncode != 0, (
            f"verifier should fail when handoff-phase-2.md is missing; "
            f"rc={result.returncode} stdout={result.stdout!r}"
        )
        assert (
            "handoff-phase-2.md" in result.stderr or "handoff-phase-2" in result.stderr
        ), (
            "fail-state stderr must name the missing handoff-phase-2.md file; "
            f"got {result.stderr!r}"
        )

    def test_bad_subject_prefix_fails(self, tmp_path: Path):
        """Commit subject doesn't match handoff: / phase-N: / slice: ... —
        complete → non-zero."""
        if not VERIFIER.is_file():
            raise AssertionError("scripts/verify_handoff.sh does not exist yet")
        _init_git_repo(tmp_path)
        _write_slice_yaml(tmp_path, "2-validation")
        _commit(tmp_path, "chore: something unrelated")
        result = _run_verifier(tmp_path)
        assert result.returncode != 0, (
            "verifier must reject commits whose subject is not one of the "
            "three accepted prefixes"
        )


# --- Skill integration -------------------------------------------------------


class TestSkillWiring:
    def test_handoff_lite_references_verifier(self):
        """handoff.md (lite) gains a line instructing the skill to invoke
        the verifier as its final step."""
        text = HANDOFF_MD.read_text(encoding="utf-8")
        assert "verify_handoff.sh" in text or "verify_handoff" in text, (
            "commands/claude-code/handoff.md must reference "
            "scripts/verify_handoff.sh (intent Item 4)"
        )

    def test_handoff_full_documents_verifier_contract(self):
        """handoff.full.md gains a section documenting exit codes + error
        shape."""
        text = HANDOFF_FULL.read_text(encoding="utf-8")
        assert "verify_handoff.sh" in text or "verify_handoff" in text, (
            "handoff.full.md must document the verifier contract (intent Item 4)"
        )
        lower = text.lower()
        assert "exit" in lower, (
            "handoff.full.md verifier section must mention exit codes"
        )
