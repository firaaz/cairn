"""PreToolUse hook — denies writes outside a role's allow-list when AGENT_ROLE is set.

Inner gate paired with each agent's `tools:` frontmatter (the outer gate). Reads
tool-call JSON from stdin. AGENT_ROLE unset is the no-op path, so non-compressed
slices are unaffected.

Exit codes: 0 = allow, 1 = deny (with stderr diagnostic), 2 = malformed stdin.
"""

from __future__ import annotations

import json
import os
import re
import sys

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}

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


def _matches_any(path, patterns):
    for pat in patterns:
        if pat and re.search(pat, path):
            return True
    return False


def _envelope_patterns(raw):
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        parsed = None
    if isinstance(parsed, list) and all(isinstance(p, str) for p in parsed):
        return [p for p in parsed if p]
    print(
        "role_guard: legacy colon-separated AGENT_ENVELOPE format detected; "
        "migrate to JSON array (see compression/slice-2 §B7)",
        file=sys.stderr,
    )
    return [p for p in raw.split(":") if p]


def main():
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
    if tool_name not in WRITE_TOOLS:
        return 0

    tool_input = payload.get("tool_input") or {}
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
