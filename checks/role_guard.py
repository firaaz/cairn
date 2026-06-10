"""PreToolUse hook — denies writes outside a role's allow-list when AGENT_ROLE is set.

Inner gate paired with each agent's `tools:` frontmatter. Reads tool-call JSON
from stdin. AGENT_ROLE unset is the no-op path unless .claude/active-envelope.yaml
is present with mode: operator, in which case it enforces the declared paths.
Post-M4-shrink:
- Read-class lockdown removed (cairn-substrate-and-fastmcp superseded).
- Bash-token deny block removed (no canonical-knowledge target).
- Write paths target dispatch-skill workspace (.claude/skill-runs/) and tests/.
- Phase-3 write gate is envelope-driven; mechanism unchanged.
- Operator envelope gate added (F3): active when AGENT_ROLE unset + file present.

Exit codes: 0 = allow, 2 = deny or malformed input (blocking — Claude Code
treats only exit 2 as a blocking hook error; gh#35).
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
from pathlib import Path

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
READ_CLASS_TOOLS = {"Read", "Grep", "Glob"}  # preserved per M3 §5; future-proof

CAIRN_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
OPERATOR_ENVELOPE_PATH = CAIRN_ROOT / ".claude" / "active-envelope.yaml"

ROLE_POLICIES = {
    "phase-1-tdd": [
        r"^\.claude/skill-runs/[^/]+/intent\.md$",
    ],
    "phase-2-tdd": [
        r"^tests/",
        r"^\.claude/skill-runs/[^/]+/validation/",
    ],
    "phase-4-tdd": [
        r"^\.claude/skill-runs/[^/]+/integration/",
        r"^\.claude/handoff\.md$",
    ],
    # phase-3-tdd: no static entry; envelope-driven (preserves the asymmetry
    # that phase-3-implementer established under compression-infrastructure-bootstrap;
    # intentional by design — AGENT_ENVELOPE is the write-path contract).
}


def _matches_any(path: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if pat and re.search(pat, path):
            return True
    return False


def _normalize_path(file_path: str) -> str:
    """Repo-root-relative form of an absolute tool path.

    Tools report absolute paths; allow-list regexes are anchored repo-root-
    relative (gh#35's masked second defect). Lexical strip only — no
    resolve(), so `.slice-system/...` keeps its symlinked shape and stays
    deny-able (edit-canonical-paths-only rule).
    """
    root = str(CAIRN_ROOT)
    if file_path.startswith(root + os.sep):
        return file_path[len(root) + 1 :]
    return file_path


def _envelope_patterns(raw: str | None) -> list[str]:
    """Return regex patterns from AGENT_ENVELOPE.

    Handles three shapes:
    - JSON array of strings (canonical write-gate format, back-compat)
    - JSON object with ``paths`` key (per ADR D9)
    - Colon-separated legacy string (deprecated; warns on stderr)
    """
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        parsed = None
    if isinstance(parsed, list) and all(isinstance(p, str) for p in parsed):
        return [p for p in parsed if p]
    if isinstance(parsed, dict) and isinstance(parsed.get("paths"), list):
        return [p for p in parsed["paths"] if isinstance(p, str) and p]
    print(
        "role_guard: legacy colon-separated AGENT_ENVELOPE format detected; "
        "migrate to JSON array",
        file=sys.stderr,
    )
    return [p for p in raw.split(":") if p]


def _load_operator_envelope() -> tuple[str, list[str]] | None:
    """Read .claude/active-envelope.yaml if present.

    Returns (mode, paths) or None if the file is absent.
    Raises ValueError on malformed content so the caller can fail closed.
    """
    if not OPERATOR_ENVELOPE_PATH.exists():
        return None
    # yaml is imported lazily so the no-envelope happy path stays stdlib-only —
    # consumer hooks invoke this script via bare `python3` and may not have pyyaml.
    import yaml

    raw = OPERATOR_ENVELOPE_PATH.read_text()
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ValueError(f"active-envelope.yaml is not valid YAML: {exc}")
    if not isinstance(data, dict):
        raise ValueError("active-envelope.yaml must be a mapping")
    mode = data.get("mode")
    # PyYAML 1.1 parses bare `off` as False; normalise to the expected string.
    if mode is False:
        mode = "off"
    if mode not in ("operator", "off"):
        raise ValueError(
            f"active-envelope.yaml mode must be 'operator' or 'off', got {mode!r}"
        )
    if mode == "operator":
        paths = data.get("paths")
        if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
            raise ValueError(
                "active-envelope.yaml paths must be a list of strings when mode: operator"
            )
        return (mode, list(paths))
    return (mode, [])


def _log_grant(path: str, role: str) -> None:
    """Append one line to .claude/envelope-grants.log recording the envelope grant."""
    grant_log = CAIRN_ROOT / ".claude" / "envelope-grants.log"
    grant_log.parent.mkdir(parents=True, exist_ok=True)
    date_str = datetime.date.today().isoformat()
    line = f"cairn-tdd-feature {date_str} {path} {role}\n"
    with open(grant_log, "a") as fh:
        fh.write(line)


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError) as exc:
        print(f"role_guard: malformed stdin: {exc}", file=sys.stderr)
        return 2

    role = os.environ.get("AGENT_ROLE")
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}

    # ────────── Operator envelope path (AGENT_ROLE unset) ──────────
    if not role:
        if tool_name not in WRITE_TOOLS:
            return 0
        try:
            env = _load_operator_envelope()
        except ValueError as exc:
            print(f"role_guard: {exc}", file=sys.stderr)
            return 2
        if env is None:
            return 0  # no envelope file = no-op (default)
        mode, paths = env
        if mode == "off":
            return 0
        # mode == "operator" — enforce
        file_path = _normalize_path(tool_input.get("file_path", "") or "")
        if not file_path:
            return 0
        if _matches_any(file_path, paths):
            return 0
        print(
            f"role_guard: operator envelope denied write outside paths: {file_path}",
            file=sys.stderr,
        )
        return 2

    # ────────── Existing per-phase logic (AGENT_ROLE set) ──────────
    if tool_name not in WRITE_TOOLS:
        return 0

    file_path = _normalize_path(tool_input.get("file_path", "") or "")
    if not file_path:
        return 0

    if role == "phase-3-tdd":
        envelope = os.environ.get("AGENT_ENVELOPE")
        patterns = _envelope_patterns(envelope)
        if _matches_any(file_path, patterns):
            return 0
        print(
            f"role_guard: phase-3-tdd denied write outside envelope: {file_path}",
            file=sys.stderr,
        )
        return 2

    if role in ROLE_POLICIES:
        if _matches_any(file_path, ROLE_POLICIES[role]):
            return 0
        # Envelope-grant escape (D9): wider grant via AGENT_ENVELOPE applies to
        # static-policy roles too.
        envelope = os.environ.get("AGENT_ENVELOPE")
        env_patterns = _envelope_patterns(envelope)
        if _matches_any(file_path, env_patterns):
            _log_grant(file_path, role)
            return 0
        print(
            f"role_guard: {role} denied write outside allow-list: {file_path}",
            file=sys.stderr,
        )
        return 2

    print(f"role_guard: unknown role '{role}'", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
