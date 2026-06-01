#!/usr/bin/env python3
"""Phase-1→Phase-2 scope-split (atomicity) gate (cairn-trial-d).

Reads an intent's ``## Contract`` block and runs the atomicity check on its
``must-satisfy`` clauses, blocking the boundary when a clause is non-atomic and
untagged (or carries a bad tag/empty declaration). Mirrors ``premise_guard.py``.

Exit codes (mirror premise_guard.py): 0 = no ``## Contract`` block (fail-open
with a visible stderr notice) or all clauses atomic-or-validly-tagged; 1 = one+
offences, or absence under CAIRN_CONTRACT_REQUIRED; 2 = intent unreadable,
malformed YAML, or ``## Contract`` heading present but no parseable block.

Invocation: ``python3 checks/atomicity_guard.py <path-to-intent.md>``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Dual-root sys.path: CLAUDE_PROJECT_DIR (or cwd) for the intent path resolution;
# the cairn root (two parents up) for ``from lib.atomicity import``.
_CAIRN_ROOT = Path(__file__).resolve().parent.parent
if str(_CAIRN_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_CAIRN_ROOT / "scripts"))

from lib.atomicity import check_clauses  # noqa: E402


def _indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def _extract_contract_block(text: str) -> str | None:
    """Return the YAML body inside the ``## Contract`` fenced block.

    State machine: find the heading, then the first ``` fence whose info-string
    is yaml or bare; capture until its closing bare ``` at the SAME indent (so an
    inner deeper-indented fence inside a literal scalar cannot truncate the
    block). A non-yaml fence (```text, ```python) before the yaml one is an
    illustrative block and is skipped. Returns None if no usable block.
    """
    lines = text.splitlines()
    in_section = False
    in_fence = False
    fence_indent = ""
    fence_is_yaml = False
    captured: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not in_section:
            if stripped == "## Contract":
                in_section = True
            continue
        if not in_fence:
            if stripped.startswith("## ") and stripped != "## Contract":
                break
            if stripped.startswith("```"):
                info = stripped[3:].strip().lower()
                fence_is_yaml = info in ("", "yaml", "yml")
                in_fence = True
                fence_indent = _indent(line)
                captured = []
            continue
        # In a fence: close only on a bare ``` at the fence's open indent.
        if stripped == "```" and _indent(line) == fence_indent:
            in_fence = False
            if fence_is_yaml:
                return "\n".join(captured)
            # Illustrative non-yaml block: discard and keep scanning for yaml.
            continue
        captured.append(line)
    return None


def _section_has_contract(text: str) -> bool:
    """True if a ``## Contract`` heading is present at all (fail-closed backstop)."""
    for line in text.splitlines():
        if line.strip() == "## Contract":
            return True
    return False


def _parse_must_satisfy(block: str) -> list:
    """Parse the YAML block, returning its ``must-satisfy`` list. Raises on bad YAML."""
    import yaml

    data = yaml.safe_load(block)
    if not isinstance(data, dict) or "must-satisfy" not in data:
        raise ValueError("no 'must-satisfy' key in block")
    clauses = data["must-satisfy"]
    if not isinstance(clauses, list):
        raise ValueError("'must-satisfy' is not a list")
    return clauses


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: atomicity_guard.py <intent.md>", file=sys.stderr)
        return 2
    if os.environ.get("CAIRN_ATOMICITY_FIX") == "1":
        print(
            "atomicity_guard: CAIRN_ATOMICITY_FIX=1 set — bypassing atomicity check.",
            file=sys.stderr,
        )
        return 0
    intent_path = Path(argv[1])
    if not intent_path.is_file():
        print(f"atomicity_guard: intent not readable: {intent_path}", file=sys.stderr)
        return 2
    try:
        text = intent_path.read_text()
    except OSError as exc:
        print(f"atomicity_guard: cannot read intent: {exc}", file=sys.stderr)
        return 2

    block = _extract_contract_block(text)
    if block is None or not block.strip():
        if _section_has_contract(text):
            print(
                "atomicity_guard: '## Contract' heading present but no parseable "
                "fenced yaml block — malformed intent.",
                file=sys.stderr,
            )
            return 2
        if os.environ.get("CAIRN_CONTRACT_REQUIRED") == "1":
            print(
                "atomicity_guard: no '## Contract' block but "
                "CAIRN_CONTRACT_REQUIRED=1 — blocking.",
                file=sys.stderr,
            )
            return 1
        print(
            "atomicity_guard: no '## Contract' block — atomicity unchecked "
            "(no contract block).",
            file=sys.stderr,
        )
        return 0
    try:
        clauses = _parse_must_satisfy(block)
    except Exception as exc:
        print(f"atomicity_guard: malformed contract block: {exc}", file=sys.stderr)
        return 2
    offences = check_clauses(clauses)
    if offences:
        print("atomicity_guard: atomicity offences detected:", file=sys.stderr)
        for off in offences:
            print(f"  - {off}", file=sys.stderr)
        return 1
    print(
        f"atomicity_guard: all {len(clauses)} clause(s) atomic-or-validly-tagged.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
