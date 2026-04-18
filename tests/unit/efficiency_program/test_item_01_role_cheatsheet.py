"""Phase 2 validation for efficiency-program/all-seven Item 1 — session-start role cheatsheet.

Verifies intent.md Item 1 acceptance assertions:
  - SessionStart hook reads `.claude/current-slice/slice.yaml`'s `status:` field.
  - Looks up the matching row in docs/operational-reference.md § Phase Skill Guide.
  - Prints a single line:
        Slice: <slice-name>. Phase: <N> <phase-name>. Role: <role>.
        Anti-behavior: <primary anti-behavior>.
  - No active slice / status complete|failed  → prints "No active slice ..." hint.
  - Missing / malformed slice.yaml              → exit 0 silently (never a blocker).
  - Hook is registered in `.claude/settings.json` under `hooks.SessionStart`.

RED phase — the hook does not yet exist; every assertion below must fail
today. Pytest + stdlib only.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CHECKS_DIR = PROJECT_ROOT / "checks"
SETTINGS_JSON = PROJECT_ROOT / ".claude" / "settings.json"
# Phase 3 may pick any filename under checks/; the verified candidate set is
# narrow — "session-start.sh" / "role-cheatsheet.sh" / "session_start.sh".
CANDIDATE_HOOK_NAMES = (
    "session-start.sh",
    "role-cheatsheet.sh",
    "session_start.sh",
    "cheatsheet.sh",
)


def _find_hook() -> Path:
    for name in CANDIDATE_HOOK_NAMES:
        candidate = CHECKS_DIR / name
        if candidate.is_file():
            return candidate
    pytest.fail(
        "SessionStart role-cheatsheet hook not found under checks/ — "
        f"tried: {', '.join(CANDIDATE_HOOK_NAMES)}"
    )


def _write_slice_yaml(root: Path, status: str, *, name: str = "demo-slice") -> Path:
    slice_dir = root / ".claude" / "current-slice"
    slice_dir.mkdir(parents=True, exist_ok=True)
    path = slice_dir / "slice.yaml"
    path.write_text(
        "id: demo/slice\n"
        f'name: "{name}"\n'
        f"status: {status}\n"
        "started: 2026-04-18\n"
        "completed: null\n"
        "invariants-touched: []\n"
        "adrs-referenced: []\n"
        "adrs-created: []\n",
        encoding="utf-8",
    )
    return path


def _run_hook(
    hook: Path,
    cwd: Path,
    *,
    stdin: str = "{}",
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    env = {
        "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
        "HOME": str(cwd),
        "CLAUDE_PROJECT_DIR": str(cwd),
    }
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(hook)],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(cwd),
        env=env,
    )


@pytest.fixture
def mirrored_root(tmp_path: Path) -> Path:
    """Create a tmp root that mirrors the repo structure the hook needs.

    Symlinks docs/ and checks/ into tmp_path so the hook (once written)
    can resolve the Phase Skill Guide table without copying it.
    """
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "current-slice").mkdir()
    (tmp_path / "docs").symlink_to(PROJECT_ROOT / "docs")
    (tmp_path / "checks").symlink_to(PROJECT_ROOT / "checks")
    return tmp_path


# --- Hook existence ----------------------------------------------------------


class TestHookExists:
    def test_hook_file_present(self):
        _find_hook()

    def test_hook_is_executable_or_runnable_via_bash(self):
        hook = _find_hook()
        assert hook.read_text(encoding="utf-8").startswith("#!"), (
            f"{hook.relative_to(PROJECT_ROOT)} must begin with a shebang "
            "(hook is invoked as a SessionStart command)"
        )


# --- Output format -----------------------------------------------------------


class TestHookOutput:
    def test_prints_cheatsheet_for_status_3_implementation(self, mirrored_root: Path):
        hook = _find_hook()
        _write_slice_yaml(mirrored_root, "3-implementation", name="demo-slice")
        result = _run_hook(hook, mirrored_root)
        assert result.returncode == 0, (
            f"hook exited non-zero: rc={result.returncode} stderr={result.stderr!r}"
        )
        out = result.stdout
        assert "Phase: 3" in out, f"missing `Phase: 3` token in output: {out!r}"
        assert "Role: Builder" in out, f"missing `Role: Builder` in output: {out!r}"
        assert "Anti-behavior:" in out, f"missing anti-behavior line in output: {out!r}"
        # Primary anti-behavior from docs/operational-reference.md table
        # (Phase 3 Builder): "Builder does not re-litigate the spec or the tests".
        assert "re-litigate" in out or "does not re-litigate" in out.lower(), (
            f"Phase 3 Builder anti-behavior substring not surfaced: {out!r}"
        )

    def test_prints_cheatsheet_for_status_1_intent(self, mirrored_root: Path):
        hook = _find_hook()
        _write_slice_yaml(mirrored_root, "1-intent", name="demo-slice")
        result = _run_hook(hook, mirrored_root)
        assert result.returncode == 0
        out = result.stdout
        assert "Phase: 1" in out
        assert "Role: Reader" in out
        assert "Anti-behavior:" in out

    def test_prints_cheatsheet_for_status_2_validation(self, mirrored_root: Path):
        hook = _find_hook()
        _write_slice_yaml(mirrored_root, "2-validation", name="demo-slice")
        result = _run_hook(hook, mirrored_root)
        assert result.returncode == 0
        assert "Phase: 2" in result.stdout
        assert "Role: Skeptic" in result.stdout

    def test_prints_cheatsheet_for_status_4_integration(self, mirrored_root: Path):
        hook = _find_hook()
        _write_slice_yaml(mirrored_root, "4-integration", name="demo-slice")
        result = _run_hook(hook, mirrored_root)
        assert result.returncode == 0
        assert "Phase: 4" in result.stdout
        assert "Role: Auditor" in result.stdout


# --- Generic / fallback paths ------------------------------------------------


class TestHookFallbacks:
    def test_status_complete_prints_no_active_slice_hint(self, mirrored_root: Path):
        hook = _find_hook()
        _write_slice_yaml(mirrored_root, "complete")
        result = _run_hook(hook, mirrored_root)
        assert result.returncode == 0
        assert "No active slice" in result.stdout, (
            f"status: complete should print the generic hint, got {result.stdout!r}"
        )
        assert "/start-slice" in result.stdout, (
            "generic hint should point at /start-slice"
        )

    def test_status_failed_prints_no_active_slice_hint(self, mirrored_root: Path):
        hook = _find_hook()
        _write_slice_yaml(mirrored_root, "failed")
        result = _run_hook(hook, mirrored_root)
        assert result.returncode == 0
        assert "No active slice" in result.stdout

    def test_missing_slice_yaml_silent_exit_zero(self, mirrored_root: Path):
        hook = _find_hook()
        # No slice.yaml written
        result = _run_hook(hook, mirrored_root)
        assert result.returncode == 0, (
            f"hook must exit 0 when slice.yaml is missing; got rc={result.returncode}"
        )

    def test_malformed_slice_yaml_silent_exit_zero(self, mirrored_root: Path):
        hook = _find_hook()
        slice_dir = mirrored_root / ".claude" / "current-slice"
        slice_dir.mkdir(parents=True, exist_ok=True)
        (slice_dir / "slice.yaml").write_text(
            ":::: not yaml ::::\n\tthis is broken\n",
            encoding="utf-8",
        )
        result = _run_hook(hook, mirrored_root)
        assert result.returncode == 0, (
            "hook must never block a session on malformed slice.yaml; "
            f"got rc={result.returncode} stderr={result.stderr!r}"
        )


# --- settings.json registration ---------------------------------------------


class TestSettingsRegistration:
    def test_settings_has_sessionstart_array(self):
        data = json.loads(SETTINGS_JSON.read_text(encoding="utf-8"))
        hooks = data.get("hooks", {})
        assert "SessionStart" in hooks, (
            ".claude/settings.json must register a SessionStart hook (intent.md Item 1)"
        )
        assert isinstance(hooks["SessionStart"], list), (
            "hooks.SessionStart must be an array of hook descriptors"
        )
        assert len(hooks["SessionStart"]) >= 1

    def test_sessionstart_entry_points_at_our_hook(self):
        data = json.loads(SETTINGS_JSON.read_text(encoding="utf-8"))
        entries = data.get("hooks", {}).get("SessionStart", [])
        flat = json.dumps(entries)
        assert any(name in flat for name in CANDIDATE_HOOK_NAMES), (
            "hooks.SessionStart does not reference any recognized hook filename; "
            f"expected one of {CANDIDATE_HOOK_NAMES} to appear in {flat!r}"
        )
