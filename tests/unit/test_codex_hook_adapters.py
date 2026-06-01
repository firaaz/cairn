"""Unit coverage for Cairn's Codex hook wrapper adapters."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRETOOL = REPO_ROOT / "plugins" / "cairn" / "checks" / "codex_pretool_guard.py"
POSTTOOL = REPO_ROOT / "plugins" / "cairn" / "checks" / "codex_posttool_reality.py"


def _env(project_root: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"AGENT_ROLE", "AGENT_ENVELOPE"}
    }
    env["CLAUDE_PROJECT_DIR"] = str(project_root)
    env["CODEX_PROJECT_DIR"] = str(project_root)
    if extra:
        env.update(extra)
    return env


def _run_hook(
    script: Path,
    payload: dict,
    project_root: Path,
    *,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=project_root,
        env=_env(project_root, env_extra),
        check=False,
    )


def _pretool(payload: dict, project_root: Path) -> subprocess.CompletedProcess[str]:
    return _run_hook(PRETOOL, payload, project_root)


def _patch_payload(patch: str) -> dict:
    return {"tool_name": "apply_patch", "tool_input": {"patch": patch}}


@pytest.mark.parametrize(
    ("command", "needle"),
    [
        ("rm -rf build", "rm -rf"),
        ("git reset --hard HEAD", "git reset --hard"),
        ("git push --force origin dev", "git push --force"),
    ],
)
def test_codex_pretool_denies_destructive_shell_commands(
    tmp_path: Path, command: str, needle: str
) -> None:
    proc = _pretool(
        {"tool_name": "exec_command", "tool_input": {"cmd": command}},
        tmp_path,
    )

    assert proc.returncode != 0
    assert needle in proc.stderr
    out = json.loads(proc.stdout)
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert reason


def test_codex_pretool_allows_force_with_lease(tmp_path: Path) -> None:
    proc = _pretool(
        {
            "tool_name": "exec_command",
            "tool_input": {"cmd": "git push --force-with-lease origin dev"},
        },
        tmp_path,
    )

    assert proc.returncode == 0, proc.stderr


def test_codex_pretool_denies_apply_patch_env_file(tmp_path: Path) -> None:
    patch = """*** Begin Patch
*** Add File: .env
+SECRET=value
*** End Patch
"""

    proc = _pretool(_patch_payload(patch), tmp_path)

    assert proc.returncode != 0
    assert "env file" in proc.stderr


def test_codex_pretool_denies_apply_patch_lock_file(tmp_path: Path) -> None:
    patch = """*** Begin Patch
*** Add File: uv.lock
+version = 1
*** End Patch
"""

    proc = _pretool(_patch_payload(patch), tmp_path)

    assert proc.returncode != 0
    assert "lock files" in proc.stderr


def test_codex_pretool_denies_existing_adr_body_edit(tmp_path: Path) -> None:
    adr = tmp_path / "docs" / "adr" / "existing.md"
    adr.parent.mkdir(parents=True)
    adr.write_text(
        "---\n"
        "id: existing\n"
        "status: accepted\n"
        "superseded-by: null\n"
        "firmness: provisional\n"
        "---\n\n"
        "## Decision\n\n"
        "Original body.\n",
        encoding="utf-8",
    )
    patch = """*** Begin Patch
*** Update File: docs/adr/existing.md
@@
-Original body.
+Changed body.
*** End Patch
"""

    proc = _pretool(_patch_payload(patch), tmp_path)

    assert proc.returncode != 0
    assert "ADR body is append-only" in proc.stderr


def test_codex_pretool_allows_existing_adr_frontmatter_supersession(
    tmp_path: Path,
) -> None:
    active = tmp_path / ".claude" / "active-envelope.yaml"
    active.parent.mkdir(parents=True)
    active.write_text("mode: operator\npaths:\n  - ^docs/adr/.*\n", encoding="utf-8")
    adr = tmp_path / "docs" / "adr" / "existing.md"
    adr.parent.mkdir(parents=True)
    adr.write_text(
        "---\n"
        "id: existing\n"
        "status: accepted\n"
        "superseded-by: null\n"
        "firmness: provisional\n"
        "---\n\n"
        "## Decision\n\n"
        "Original body.\n",
        encoding="utf-8",
    )
    patch = """*** Begin Patch
*** Update File: docs/adr/existing.md
@@
-status: accepted
+status: superseded
-superseded-by: null
+superseded-by: codex-hook-parity
*** End Patch
"""

    proc = _pretool(_patch_payload(patch), tmp_path)

    assert proc.returncode == 0, proc.stderr


def test_codex_pretool_denies_apply_patch_outside_operator_envelope(
    tmp_path: Path,
) -> None:
    active = tmp_path / ".claude" / "active-envelope.yaml"
    active.parent.mkdir(parents=True)
    active.write_text("mode: operator\npaths:\n  - ^allowed/.*\n", encoding="utf-8")
    patch = """*** Begin Patch
*** Add File: blocked/file.txt
+blocked
*** End Patch
"""

    proc = _pretool(_patch_payload(patch), tmp_path)

    assert proc.returncode != 0
    assert "operator envelope denied" in proc.stderr


def test_codex_pretool_denies_multifile_patch_if_any_file_violates(
    tmp_path: Path,
) -> None:
    patch = """*** Begin Patch
*** Add File: allowed.txt
+ok
*** Add File: .env.local
+SECRET=value
*** End Patch
"""

    proc = _pretool(_patch_payload(patch), tmp_path)

    assert proc.returncode != 0
    assert "env file" in proc.stderr


def test_codex_posttool_runs_ruff_for_python_files_touched_by_apply_patch(
    tmp_path: Path,
) -> None:
    source = tmp_path / "pkg" / "example.py"
    source.parent.mkdir()
    source.write_text("x=1\n", encoding="utf-8")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    ruff_log = tmp_path / "ruff.log"
    fake_ruff = bin_dir / "ruff"
    fake_ruff.write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$RUFF_LOG"\n',
        encoding="utf-8",
    )
    fake_ruff.chmod(0o755)

    patch = """*** Begin Patch
*** Update File: pkg/example.py
@@
-x=1
+x = 1
*** End Patch
"""

    proc = _run_hook(
        POSTTOOL,
        _patch_payload(patch),
        tmp_path,
        env_extra={
            "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            "RUFF_LOG": str(ruff_log),
        },
    )

    assert proc.returncode == 0, proc.stderr
    assert ruff_log.read_text(encoding="utf-8").splitlines() == [
        "format --quiet pkg/example.py",
        "check --fix --quiet pkg/example.py",
    ]
