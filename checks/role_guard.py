"""PreToolUse hook — denies writes outside a role's allow-list when AGENT_ROLE is set.
Also denies Read and Bash read-class access to canonical knowledge paths for
phase-1-writer unless AGENT_ENVELOPE grants the path (ADR D8).

Inner gate paired with each agent's `tools:` frontmatter (the outer gate). Reads
tool-call JSON from stdin. AGENT_ROLE unset is the no-op path, so non-compressed
slices are unaffected.

Exit codes: 0 = allow, 1 = deny (with stderr diagnostic), 2 = malformed stdin.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
from pathlib import Path

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
READ_CLASS_TOOLS = {"Read"}
BASH_TOOL = "Bash"

CAIRN_ROOT = Path(__file__).resolve().parent.parent

# Canonical knowledge paths locked down for phase-1-writer (ADR D8).
# Agents must query these via MCP (cairn_query) instead of direct Read/Bash.
ROLE_DENY_READ = {
    "phase-1-writer": [
        r"^scripts/cairn_query/",
        r"^docs/ARCHITECTURE\.md$",
        r"^docs/adr/",
        r"^docs/lessons\.md$",
        r"^docs/spec-v1\.md$",
        r"^docs/operational-reference\.md$",
    ],
}

ROLE_POLICIES = {
    "phase-1-writer": [
        r"^\.claude/current-slice/intent\.md$",
        r"^\.claude/current-slice/slice\.yaml$",
        r"^\.claude/features/[^/]+\.yaml$",
    ],
    "phase-2-skeptic": [
        r"^tests/",
        r"^\.claude/current-slice/validation/",
    ],
    "phase-4-integrator": [
        r"^\.claude/current-slice/integration/",
        r"^\.claude/current-slice/handoff-phase-\d+\.md$",
        r"^\.claude/handoff\.md$",
        r"^\.claude/current-slice/slice\.yaml$",
        r"^\.claude/sweep\.yaml$",
    ],
}


def _matches_any(path: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if pat and re.search(pat, path):
            return True
    return False


def _envelope_patterns(raw: str | None) -> list[str]:
    """Return regex patterns from AGENT_ENVELOPE.

    Handles three shapes:
    - JSON array of strings (canonical write-gate format, back-compat)
    - JSON object with ``paths`` key (new object shape per ADR D9)
    - Colon-separated legacy string (deprecated)
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
        "migrate to JSON array (see compression/slice-2 §B7)",
        file=sys.stderr,
    )
    return [p for p in raw.split(":") if p]


def _log_grant(path: str, role: str) -> None:
    """Append one line to .claude/envelope-grants.log recording the envelope grant."""
    grant_log = CAIRN_ROOT / ".claude" / "envelope-grants.log"
    grant_log.parent.mkdir(parents=True, exist_ok=True)
    date_str = datetime.date.today().isoformat()
    slice_id = "compression/lever-Y-mcp-substrate"
    line = f"{slice_id} {date_str} {path} {role}\n"
    with open(grant_log, "a") as fh:
        fh.write(line)


def _bash_path_tokens(command: str) -> list[str]:
    """Extract potential file-path tokens from a shell command string.

    Skips the command name (first token) and flag arguments (starting with ``-``).
    """
    tokens = (command or "").split()
    if len(tokens) <= 1:
        return []
    return [t for t in tokens[1:] if not t.startswith("-")]


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError) as exc:
        print(f"role_guard: malformed stdin: {exc}", file=sys.stderr)
        return 2

    role = os.environ.get("AGENT_ROLE")
    if not role:
        return 0

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}

    # ------------------------------------------------------------------
    # Read-class lockdown (ADR D8) — phase-1-writer only this slice.
    # ------------------------------------------------------------------
    if tool_name in READ_CLASS_TOOLS and role in ROLE_DENY_READ:
        file_path = re.sub(r"^\./", "", tool_input.get("file_path") or "")
        deny_patterns = ROLE_DENY_READ[role]
        if _matches_any(file_path, deny_patterns):
            env_patterns = _envelope_patterns(os.environ.get("AGENT_ENVELOPE"))
            if _matches_any(file_path, env_patterns):
                _log_grant(file_path, role)
                return 0
            print(
                f"role_guard: {role} denied Read of canonical knowledge path: {file_path}",
                file=sys.stderr,
            )
            return 1

    # ------------------------------------------------------------------
    # Bash read-class lockdown (ADR D8) — treat cat/head/grep/less etc.
    # as equivalent to Read for path-access purposes.
    # ------------------------------------------------------------------
    if tool_name == BASH_TOOL and role in ROLE_DENY_READ:
        command = tool_input.get("command") or ""
        deny_patterns = ROLE_DENY_READ[role]
        for token in _bash_path_tokens(command):
            if _matches_any(token, deny_patterns):
                print(
                    f"role_guard: {role} denied Bash read-class access to "
                    f"canonical knowledge path: {token}",
                    file=sys.stderr,
                )
                return 1

    # ------------------------------------------------------------------
    # Write lockdown — existing behaviour unchanged.
    # ------------------------------------------------------------------
    if tool_name not in WRITE_TOOLS:
        return 0

    file_path = tool_input.get("file_path", "") or ""
    if not file_path:
        return 0

    if role == "phase-3-implementer":
        envelope = os.environ.get("AGENT_ENVELOPE")
        patterns = _envelope_patterns(envelope)
        if _matches_any(file_path, patterns):
            return 0
        print(
            f"role_guard: phase-3-implementer denied write outside envelope: {file_path}",
            file=sys.stderr,
        )
        return 1

    if role in ROLE_POLICIES:
        if _matches_any(file_path, ROLE_POLICIES[role]):
            return 0
        print(
            f"role_guard: {role} denied write outside allow-list: {file_path}",
            file=sys.stderr,
        )
        return 1

    print(f"role_guard: unknown role '{role}'", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
