"""Phase 2 validation for efficiency-program/all-seven Item 6 — per-phase commit-message templates + prepare-commit-msg hook.

Verifies intent.md Item 6 acceptance:
  - Four .gitmessage-phase-<N> files exist at repo root, N in {1,2,3,4}.
  - Each contains a `phase-<N>:` subject-line template AND a `Next:` trailer.
  - Simulated prepare-commit-msg invocation with fixture slice.yaml
    status: 2-validation → buffer first non-empty line begins with `phase-2:`.
  - Simulated invocation with status: complete → buffer unchanged (no-op).

RED phase: neither the template files nor checks/prepare-commit-msg.sh
exist. Pytest + stdlib only.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
HOOK = PROJECT_ROOT / "checks" / "prepare-commit-msg.sh"
TEMPLATE_NAMES = tuple(f".gitmessage-phase-{n}" for n in (1, 2, 3, 4))


def _template_path(n: int) -> Path:
    return PROJECT_ROOT / f".gitmessage-phase-{n}"


def _write_slice_yaml(root: Path, status: str) -> Path:
    slice_dir = root / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True, exist_ok=True)
    path = slice_dir / "slice.yaml"
    path.write_text(
        "id: demo/slice\n"
        'name: "demo-slice"\n'
        f"status: {status}\n"
        "started: 2026-04-18\n"
        "completed: null\n",
        encoding="utf-8",
    )
    return path


def _invoke_hook(hook: Path, buf: Path, *, cwd: Path) -> subprocess.CompletedProcess:
    # prepare-commit-msg contract: git passes the msg-buffer path as $1.
    env = {
        "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
        "HOME": str(cwd),
        "CLAUDE_PROJECT_DIR": str(cwd),
    }
    return subprocess.run(
        ["bash", str(hook), str(buf)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(cwd),
        env=env,
    )


# --- Templates on disk -------------------------------------------------------


class TestTemplateFilesExist:
    @pytest.mark.parametrize("n", [1, 2, 3, 4])
    def test_template_file_exists(self, n: int):
        path = _template_path(n)
        assert path.is_file(), f"missing {path.name} at repo root (intent Item 6)"

    @pytest.mark.parametrize("n", [1, 2, 3, 4])
    def test_template_has_phase_subject_line(self, n: int):
        path = _template_path(n)
        text = path.read_text(encoding="utf-8")
        assert f"phase-{n}:" in text, (
            f"{path.name} must contain a `phase-{n}:` subject-line template"
        )

    @pytest.mark.parametrize("n", [1, 2, 3, 4])
    def test_template_has_next_trailer(self, n: int):
        path = _template_path(n)
        text = path.read_text(encoding="utf-8")
        assert "Next:" in text, (
            f"{path.name} must contain a `Next:` trailer (intent Item 6)"
        )


# --- prepare-commit-msg hook -------------------------------------------------


class TestPrepareCommitMsgHook:
    def test_hook_exists(self):
        assert HOOK.is_file(), (
            f"checks/prepare-commit-msg.sh missing (expected at {HOOK})"
        )

    def test_hook_has_shebang(self):
        if not HOOK.is_file():
            raise AssertionError("prepare-commit-msg hook not yet written")
        head = HOOK.read_text(encoding="utf-8").splitlines()
        assert head and head[0].startswith("#!"), (
            "prepare-commit-msg.sh must begin with a shebang"
        )

    def test_populates_buffer_for_status_2_validation(self, tmp_path: Path):
        if not HOOK.is_file():
            raise AssertionError("prepare-commit-msg hook not yet written")
        # Mirror a project dir in tmp_path with slice.yaml + a copy of the
        # templates so the hook can resolve them.
        _write_slice_yaml(tmp_path, "2-validation")
        # Symlink the templates so the hook can find them from $cwd.
        for name in TEMPLATE_NAMES:
            src = PROJECT_ROOT / name
            if src.exists():
                (tmp_path / name).symlink_to(src)
        buf = tmp_path / "COMMIT_EDITMSG"
        buf.write_text("", encoding="utf-8")
        result = _invoke_hook(HOOK, buf, cwd=tmp_path)
        assert result.returncode == 0, (
            f"hook exited non-zero: rc={result.returncode} stderr={result.stderr!r}"
        )
        body = buf.read_text(encoding="utf-8")
        first_nonempty = next((ln for ln in body.splitlines() if ln.strip()), "")
        assert first_nonempty.startswith("phase-2:"), (
            f"buffer first non-empty line must start with `phase-2:`; "
            f"got {first_nonempty!r}"
        )

    def test_noop_for_status_complete(self, tmp_path: Path):
        if not HOOK.is_file():
            raise AssertionError("prepare-commit-msg hook not yet written")
        _write_slice_yaml(tmp_path, "complete")
        for name in TEMPLATE_NAMES:
            src = PROJECT_ROOT / name
            if src.exists():
                (tmp_path / name).symlink_to(src)
        buf = tmp_path / "COMMIT_EDITMSG"
        original = "# user-typed body\nfix: something\n"
        buf.write_text(original, encoding="utf-8")
        result = _invoke_hook(HOOK, buf, cwd=tmp_path)
        assert result.returncode == 0
        body = buf.read_text(encoding="utf-8")
        assert body == original, (
            "hook must no-op when slice.yaml.status is `complete`; "
            f"buffer changed from {original!r} to {body!r}"
        )

    def test_noop_when_slice_yaml_missing(self, tmp_path: Path):
        if not HOOK.is_file():
            raise AssertionError("prepare-commit-msg hook not yet written")
        buf = tmp_path / "COMMIT_EDITMSG"
        original = "chore: regular commit\n"
        buf.write_text(original, encoding="utf-8")
        result = _invoke_hook(HOOK, buf, cwd=tmp_path)
        assert result.returncode == 0, (
            "hook must never block git commit on missing slice.yaml"
        )
        assert buf.read_text(encoding="utf-8") == original

    def test_noop_for_status_failed(self, tmp_path: Path):
        if not HOOK.is_file():
            raise AssertionError("prepare-commit-msg hook not yet written")
        _write_slice_yaml(tmp_path, "failed")
        buf = tmp_path / "COMMIT_EDITMSG"
        original = "slice: demo — failed\n"
        buf.write_text(original, encoding="utf-8")
        result = _invoke_hook(HOOK, buf, cwd=tmp_path)
        assert result.returncode == 0
        assert buf.read_text(encoding="utf-8") == original, (
            "status: failed is non-pipeline; hook must no-op"
        )
