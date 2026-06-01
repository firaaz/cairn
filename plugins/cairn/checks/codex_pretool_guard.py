#!/usr/bin/env python3
"""Codex PreToolUse adapter for Cairn enforcement hooks.

Codex edit payloads are not Claude Write/Edit payloads. This adapter keeps that
normalization boundary here and leaves the existing Claude hook scripts stable.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HOOK_EVENT = "PreToolUse"
SHELL_TOOLS = {
    "bash",
    "exec_command",
    "functions.exec_command",
    "shell",
    "shell_command",
}
APPLY_PATCH_TOOLS = {"apply_patch", "functions.apply_patch"}
ADR_FRONTMATTER_KEYS = (
    "status:",
    "superseded-by:",
    "superseded_by:",
    "firmness:",
)
LOCK_FILE_SUFFIXES = ("uv.lock", "package-lock.json", "poetry.lock")
GIT_FORCE_PUSH_REASON = (
    "REVERSIBILITY GUARD: git push --force: use --force-with-lease instead"
)
GIT_SHORT_FORCE_PUSH_REASON = (
    "REVERSIBILITY GUARD: git push -f: use --force-with-lease instead"
)
GIT_OPTIONS_WITH_VALUES = {
    "-C",
    "-c",
    "--config-env",
    "--exec-path",
    "--git-dir",
    "--namespace",
    "--work-tree",
}


@dataclass
class FilePatch:
    path: str
    op: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    context: list[str] = field(default_factory=list)
    move_to: str | None = None

    @property
    def touched_paths(self) -> list[str]:
        paths = [self.path]
        if self.move_to:
            paths.append(self.move_to)
        return paths


def _project_root() -> Path:
    for key in ("CODEX_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        raw = os.environ.get(key)
        if raw:
            return Path(raw).resolve()
    return Path.cwd().resolve()


def _repo_relative(path: str, project_root: Path) -> str:
    normalized = path.strip()
    if normalized.startswith('"') and normalized.endswith('"'):
        normalized = normalized[1:-1]
    candidate = Path(normalized)
    if candidate.is_absolute():
        try:
            normalized = candidate.resolve().relative_to(project_root).as_posix()
        except ValueError:
            normalized = candidate.as_posix()
    normalized = normalized.removeprefix("./")
    normalized = normalized.removeprefix(".slice-system/")
    return normalized


def _input_mappings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    mappings: list[dict[str, Any]] = []
    for key in ("tool_input", "input", "arguments", "parameters", "params"):
        value = payload.get(key)
        if isinstance(value, dict):
            mappings.append(value)
    mappings.append(payload)
    return mappings


def _tool_name(payload: dict[str, Any]) -> str:
    for key in ("tool_name", "toolName", "tool", "name"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _extract_string(payload: dict[str, Any], keys: tuple[str, ...]) -> str:
    for mapping in _input_mappings(payload):
        for key in keys:
            value = mapping.get(key)
            if isinstance(value, str):
                return value
    for key in ("tool_input", "input", "arguments"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return ""


def _extract_command(payload: dict[str, Any]) -> str:
    return _extract_string(payload, ("command", "cmd"))


def _extract_patch(payload: dict[str, Any]) -> str:
    return _extract_string(payload, ("patch", "input"))


def _is_shell_call(payload: dict[str, Any]) -> bool:
    name = _tool_name(payload).lower()
    return name in SHELL_TOOLS or bool(_extract_command(payload))


def _is_apply_patch_call(payload: dict[str, Any]) -> bool:
    name = _tool_name(payload).lower()
    return name in APPLY_PATCH_TOOLS or bool(_extract_patch(payload))


def _deny(reason: str) -> int:
    print(reason, file=sys.stderr)
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": HOOK_EVENT,
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return 2


def _split_shell_segments(command: str) -> list[str]:
    segments: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    index = 0

    def flush() -> None:
        segment = "".join(current).strip()
        if segment:
            segments.append(segment)
        current.clear()

    while index < len(command):
        char = command[index]
        if escaped:
            current.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\" and quote != "'":
            current.append(char)
            escaped = True
            index += 1
            continue
        if quote:
            if char == quote:
                quote = None
            current.append(char)
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
            index += 1
            continue
        if command.startswith(("&&", "||"), index):
            flush()
            index += 2
            continue
        if char in {";", "|"}:
            flush()
            index += 1
            continue
        current.append(char)
        index += 1

    flush()
    return segments


def _is_env_assignment(token: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", token))


def _is_git_token(token: str) -> bool:
    return token == "git" or token.endswith("/git")


def _git_command_index(tokens: list[str]) -> int | None:
    index = 0
    while index < len(tokens) and _is_env_assignment(tokens[index]):
        index += 1
    if index < len(tokens) and tokens[index] == "env":
        index += 1
        while index < len(tokens) and (
            tokens[index].startswith("-") or _is_env_assignment(tokens[index])
        ):
            index += 1
    while index < len(tokens) and tokens[index] in {"command", "exec", "time"}:
        index += 1
    if index < len(tokens) and tokens[index] == "sudo":
        index += 1
        while index < len(tokens) and tokens[index].startswith("-"):
            flag = tokens[index]
            index += 1
            if flag in {"-C", "-g", "-h", "-p", "-T", "-u"} and index < len(tokens):
                index += 1
        while index < len(tokens) and _is_env_assignment(tokens[index]):
            index += 1
    if index < len(tokens) and _is_git_token(tokens[index]):
        return index
    return None


def _git_push_index(tokens: list[str], git_index: int) -> int | None:
    index = git_index + 1
    while index < len(tokens):
        token = tokens[index]
        if token == "push":
            return index
        if token == "--":
            return None
        if token in GIT_OPTIONS_WITH_VALUES:
            index += 2
            continue
        if any(
            token.startswith(f"{option}=")
            for option in GIT_OPTIONS_WITH_VALUES
            if option.startswith("--")
        ):
            index += 1
            continue
        if token.startswith(("-C", "-c")) and token not in {"-C", "-c"}:
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return None
    return None


def _is_short_force_token(token: str) -> bool:
    return token.startswith("-") and not token.startswith("--") and "f" in token[1:]


def _git_push_force_reason_from_tokens(tokens: list[str]) -> str | None:
    git_index = _git_command_index(tokens)
    if git_index is None:
        return None
    push_index = _git_push_index(tokens, git_index)
    if push_index is None:
        return None
    for token in tokens[push_index + 1 :]:
        if token == "--":
            return None
        if token == "--force" or token.startswith("--force="):
            return GIT_FORCE_PUSH_REASON
        if _is_short_force_token(token):
            return GIT_SHORT_FORCE_PUSH_REASON
    return None


def _git_push_force_reason_from_unparsed(segment: str) -> str | None:
    if re.search(r"\bgit\s+push\b.*(?<!\S)--force(?:=|\s|$)", segment):
        return GIT_FORCE_PUSH_REASON
    if re.search(r"\bgit\s+push\b.*(?<!\S)-[A-Za-z]*f[A-Za-z]*(?:\s|$)", segment):
        return GIT_SHORT_FORCE_PUSH_REASON
    return None


def _git_push_force_reason(command: str) -> str | None:
    for segment in _split_shell_segments(command):
        try:
            tokens = shlex.split(segment)
        except ValueError:
            reason = _git_push_force_reason_from_unparsed(segment)
        else:
            reason = _git_push_force_reason_from_tokens(tokens)
        if reason:
            return reason
    return None


def _destructive_command_reason(command: str) -> str | None:
    if "rm -rf" in command:
        return "REVERSIBILITY GUARD: rm -rf: use rm with explicit paths instead"
    if "rm -fr" in command:
        return "REVERSIBILITY GUARD: rm -fr: use rm with explicit paths instead"
    git_push_reason = _git_push_force_reason(command)
    if git_push_reason:
        return git_push_reason
    if "git reset --hard" in command:
        return "REVERSIBILITY GUARD: git reset --hard: use git stash or a backup branch"
    if "git clean -fd" in command:
        return "REVERSIBILITY GUARD: git clean -fd: destructive - enumerate files first"
    if re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE):
        return "REVERSIBILITY GUARD: DROP TABLE: export data first"
    if re.search(r"\bdrop\s+database\b", command, flags=re.IGNORECASE):
        return "REVERSIBILITY GUARD: DROP DATABASE: export data first"
    return None


def _parse_apply_patch(patch: str) -> list[FilePatch]:
    patches: list[FilePatch] = []
    current: FilePatch | None = None
    for raw_line in patch.splitlines():
        if raw_line.startswith("*** Update File: "):
            current = FilePatch(
                raw_line.removeprefix("*** Update File: ").strip(), "update"
            )
            patches.append(current)
            continue
        if raw_line.startswith("*** Add File: "):
            current = FilePatch(raw_line.removeprefix("*** Add File: ").strip(), "add")
            patches.append(current)
            continue
        if raw_line.startswith("*** Delete File: "):
            current = FilePatch(
                raw_line.removeprefix("*** Delete File: ").strip(), "delete"
            )
            patches.append(current)
            continue
        if raw_line.startswith("*** Move to: ") and current is not None:
            current.move_to = raw_line.removeprefix("*** Move to: ").strip()
            continue
        if current is None:
            continue
        if raw_line.startswith("***") or raw_line.startswith("@@"):
            continue
        if raw_line.startswith("+"):
            current.added.append(raw_line[1:])
        elif raw_line.startswith("-"):
            current.removed.append(raw_line[1:])
        elif raw_line.startswith(" "):
            current.context.append(raw_line[1:])
    return patches


def _is_env_path(path: str) -> bool:
    return path.endswith(".env") or ".env." in path


def _is_lock_path(path: str) -> bool:
    return path.endswith(LOCK_FILE_SUFFIXES)


def _is_adr_path(path: str) -> bool:
    return path.startswith("docs/adr/") and path.endswith(".md")


def _matches_any(path: str, patterns: list[str]) -> bool:
    return any(pattern and re.search(pattern, path) for pattern in patterns)


def _strip_yaml_comment(value: str) -> str:
    return value.split(" #", 1)[0].strip()


def _load_operator_envelope(project_root: Path) -> tuple[str, list[str]] | None:
    envelope = project_root / ".claude" / "active-envelope.yaml"
    if not envelope.is_file():
        return None

    mode: str | None = None
    paths: list[str] = []
    in_paths = False
    for line in envelope.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("mode:"):
            raw_mode = _strip_yaml_comment(stripped.split(":", 1)[1])
            mode = raw_mode.strip("'\"")
            in_paths = False
            continue
        if stripped.startswith("paths:"):
            in_paths = True
            continue
        if in_paths and stripped.startswith("-"):
            raw_path = _strip_yaml_comment(stripped[1:])
            path = raw_path.strip("'\"")
            if path:
                paths.append(path)
            continue
        if re.match(r"^[A-Za-z_][\w-]*:", stripped):
            in_paths = False

    if mode is None:
        raise ValueError("active-envelope.yaml mode is missing")
    if mode not in {"operator", "off"}:
        raise ValueError(
            f"active-envelope.yaml mode must be 'operator' or 'off', got {mode!r}"
        )
    if mode == "operator" and not paths:
        raise ValueError(
            "active-envelope.yaml paths must be non-empty when mode: operator"
        )
    return mode, paths


def _operator_envelope_reason(rel_path: str, project_root: Path) -> str | None:
    try:
        envelope = _load_operator_envelope(project_root)
    except ValueError as exc:
        return f"role_guard: {exc}"
    if envelope is None:
        return None
    mode, paths = envelope
    if mode == "off" or _matches_any(rel_path, paths):
        return None
    return f"role_guard: operator envelope denied write outside paths: {rel_path}"


def _frontmatter_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return []
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            return lines[: index + 1]
    return []


def _is_allowed_adr_frontmatter_edit(file_patch: FilePatch, path: Path) -> bool:
    changed = [
        line for line in [*file_patch.removed, *file_patch.added] if line.strip()
    ]
    if not changed:
        return True
    if not all(line.lstrip().startswith(ADR_FRONTMATTER_KEYS) for line in changed):
        return False

    frontmatter = _frontmatter_lines(path)
    if not frontmatter:
        return False

    removed = [line for line in file_patch.removed if line.strip()]
    if removed:
        return all(line in frontmatter for line in removed)

    context = [line for line in file_patch.context if line.strip()]
    return any(line in frontmatter for line in context)


def _adr_reason(file_patch: FilePatch, rel_path: str, project_root: Path) -> str | None:
    if rel_path == "docs/adr/index.md" or not _is_adr_path(rel_path):
        return None
    absolute = project_root / rel_path
    if file_patch.op == "add" and not absolute.exists():
        return None
    if _is_allowed_adr_frontmatter_edit(file_patch, absolute):
        return None
    return (
        "REVERSIBILITY GUARD: ADR body is append-only. Only frontmatter "
        "status, superseded-by, and firmness updates are permitted; use a "
        "superseding ADR for body changes."
    )


def _role_guard_reason(rel_path: str, project_root: Path) -> str | None:
    if not os.environ.get("AGENT_ROLE"):
        return _operator_envelope_reason(rel_path, project_root)

    role_guard = Path(__file__).with_name("role_guard.py")
    if not role_guard.is_file():
        return f"role_guard missing at {role_guard}"
    payload = {"tool_name": "Edit", "tool_input": {"file_path": rel_path}}
    env = os.environ.copy()
    env.setdefault("CLAUDE_PROJECT_DIR", str(project_root))
    proc = subprocess.run(
        [sys.executable, str(role_guard)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
        check=False,
    )
    if proc.returncode == 0:
        return None
    diagnostic = proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}"
    return f"role_guard denied {rel_path}: {diagnostic}"


def _apply_patch_reason(payload: dict[str, Any]) -> str | None:
    patch = _extract_patch(payload)
    if not patch:
        return None

    project_root = _project_root()
    file_patches = _parse_apply_patch(patch)
    if not file_patches:
        return "codex_pretool_guard: could not parse apply_patch touched files"

    for file_patch in file_patches:
        for raw_path in file_patch.touched_paths:
            rel_path = _repo_relative(raw_path, project_root)
            if _is_env_path(rel_path):
                return (
                    "REVERSIBILITY GUARD: blocked write to env file - "
                    "update .env.example instead"
                )
            if _is_lock_path(rel_path):
                return (
                    "REVERSIBILITY GUARD: lock files are auto-generated - "
                    "use the package manager"
                )

        primary_path = _repo_relative(file_patch.path, project_root)
        reason = _adr_reason(file_patch, primary_path, project_root)
        if reason:
            return reason

    for file_patch in file_patches:
        for raw_path in file_patch.touched_paths:
            rel_path = _repo_relative(raw_path, project_root)
            reason = _role_guard_reason(rel_path, project_root)
            if reason:
                return reason

    return None


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except (TypeError, ValueError) as exc:
        return _deny(f"codex_pretool_guard: malformed stdin: {exc}")
    if not isinstance(payload, dict):
        return _deny("codex_pretool_guard: hook payload must be a JSON object")

    if _is_shell_call(payload):
        reason = _destructive_command_reason(_extract_command(payload))
        if reason:
            return _deny(reason)
        return 0

    if _is_apply_patch_call(payload):
        reason = _apply_patch_reason(payload)
        if reason:
            return _deny(reason)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
