#!/usr/bin/env python3
"""Codex PostToolUse adapter for Cairn's Python reality check."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from codex_pretool_guard import (
    _extract_patch,
    _is_apply_patch_call,
    _parse_apply_patch,
    _project_root,
    _repo_relative,
)


def _touched_python_files(payload: dict) -> list[Path]:
    patch = _extract_patch(payload)
    if not patch:
        return []
    project_root = _project_root()
    out: list[Path] = []
    seen: set[Path] = set()
    for file_patch in _parse_apply_patch(patch):
        for raw_path in file_patch.touched_paths:
            rel_path = _repo_relative(raw_path, project_root)
            if not rel_path.endswith(".py"):
                continue
            path = project_root / rel_path
            if path in seen:
                continue
            seen.add(path)
            out.append(path)
    return out


def _run_ruff(path: Path, project_root: Path, ruff: str) -> None:
    if not path.is_file():
        return
    rel_path = path.relative_to(project_root).as_posix()
    subprocess.run(
        [ruff, "format", "--quiet", rel_path],
        cwd=project_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    subprocess.run(
        [ruff, "check", "--fix", "--quiet", rel_path],
        cwd=project_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except (TypeError, ValueError) as exc:
        print(f"codex_posttool_reality: malformed stdin: {exc}", file=sys.stderr)
        return 0
    if not isinstance(payload, dict) or not _is_apply_patch_call(payload):
        return 0

    ruff = shutil.which("ruff")
    if not ruff:
        print(
            "WARNING: codex_posttool_reality skipped - ruff not found in PATH. "
            "Install with: uv tool install ruff",
            file=sys.stderr,
        )
        return 0

    project_root = _project_root()
    for path in _touched_python_files(payload):
        _run_ruff(path, project_root, ruff)
    return 0


if __name__ == "__main__":
    sys.exit(main())
