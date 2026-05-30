"""CLI approval gate — blocks Phase-2 dispatch on a stale/fabricated/missing premise.

Reads an intent's optional `## Premise Grounding` block (verbatim source-quotes)
and diffs each quote against live source via the shared lib.premise_match.grounded
matcher (FLI-1: same tolerance as the validator assertion). Invocation:
`uv run python checks/premise_guard.py <path-to-intent.md>`.

Exit codes (mirror role_guard.py): 0 = all premises grounded, or no section /
empty premises; 1 = one+ premises not grounded / source missing / unreadable;
2 = intent file missing/unreadable, malformed YAML block, or bad args.

FLI-2: fail-open on ABSENCE (no block → 0), fail-closed on MALFORMATION (→ 2).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
# Premise `source` paths resolve against PROJECT_ROOT (the consumer cwd); the
# shared matcher ships beside this script, so import it from cairn's own root —
# the two roots diverge when cairn is consumed downstream.
_CAIRN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(_CAIRN_ROOT / "scripts"))

from lib.premise_match import grounded  # noqa: E402


_FENCE_OPEN = re.compile(r"^(\s*)```([A-Za-z0-9_-]*)\s*$")


def _extract_premise_block(text: str) -> str | None:
    """Return the first top-level ```yaml block under '## Premise Grounding', or None."""
    # Fence state machine: a fence closes only on a bare ``` at the SAME indent as its
    # open, so inner ``` lines (a quoted markdown heading, or a fenced code block inside
    # an indented `quote: |` scalar) are body, not a close — neither a `## ` heading nor
    # an inner fence may truncate the block into a fail-open None.
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "## Premise Grounding":
            start = i + 1
            break
    if start is None:
        return None

    i = start
    while i < len(lines):
        line = lines[i]
        m = _FENCE_OPEN.match(line)
        if m is None:
            # A top-level `## ` heading outside any fence ends the section.
            if line.startswith("## "):
                return None
            i += 1
            continue
        indent, info = m.group(1), m.group(2)
        close = re.compile(rf"^{re.escape(indent)}```\s*$")
        body_start = i + 1
        j = body_start
        while j < len(lines) and not close.match(lines[j]):
            j += 1
        if info in ("yaml", "yml"):
            return "\n".join(lines[body_start:j])
        # Non-yaml fence (e.g. a ```text example): consume it and keep scanning.
        i = j + 1
    return None


_PREMISES_KEY = re.compile(r"^\s*premises\s*:", re.MULTILINE)


def _section_has_premises(text: str) -> bool:
    """True if the '## Premise Grounding' section text carries a `premises:` key."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "## Premise Grounding":
            start = i + 1
            break
    if start is None:
        return False
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    return bool(_PREMISES_KEY.search("\n".join(lines[start:end])))


def _check_premises(premises: list[dict]) -> list[str]:
    failures = []
    for premise in premises:
        source = premise.get("source")
        quote = premise.get("quote")
        resolved = PROJECT_ROOT / source
        if not resolved.exists():
            failures.append(f"cited source not found: {source}")
            continue
        try:
            text = resolved.read_text()
        except (OSError, UnicodeDecodeError):
            failures.append(f"cited source unreadable: {source}")
            continue
        if not grounded(text, quote, Path(source).suffix):
            failures.append(
                f"premise no longer grounded in {source} "
                f"(quoted text absent — stale or fabricated): {quote}"
            )
    return failures


def main() -> int:
    if os.environ.get("CAIRN_PREMISE_FIX") == "1":
        print(
            "premise_guard: CAIRN_PREMISE_FIX=1 — bypassing premise grounding check",
            file=sys.stderr,
        )
        return 0

    if len(sys.argv) != 2:
        print(
            "premise_guard: usage: premise_guard.py <path-to-intent.md>",
            file=sys.stderr,
        )
        return 2

    intent_path = Path(sys.argv[1])
    try:
        text = intent_path.read_text()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"premise_guard: cannot read intent file: {exc}", file=sys.stderr)
        return 2

    block = _extract_premise_block(text)
    if block is None:
        # Fail-closed backstop (FLI-2): genuine absence → exit 0, but a section
        # that authored a `premises:` key yet yielded no extractable yaml block
        # (e.g. a stray/unbalanced fence swallowing the real one) must not pass.
        if _section_has_premises(text):
            print(
                "premise_guard: '## Premise Grounding' section contains premise "
                "content but no parseable yaml block could be extracted "
                "(check fence formatting)",
                file=sys.stderr,
            )
            return 2
        return 0

    import yaml

    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        print(f"premise_guard: malformed premise YAML block: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict) or "premises" not in data:
        print(
            "premise_guard: premise block must be a mapping with a 'premises' key",
            file=sys.stderr,
        )
        return 2
    premises = data["premises"]
    if premises is None:
        return 0
    if not isinstance(premises, list):
        print("premise_guard: 'premises' must be a list", file=sys.stderr)
        return 2
    if not premises:
        return 0
    for premise in premises:
        if (
            not isinstance(premise, dict)
            or not isinstance(premise.get("source"), str)
            or not isinstance(premise.get("quote"), str)
        ):
            print(
                "premise_guard: each premise must be a mapping with string "
                "'source' and 'quote'",
                file=sys.stderr,
            )
            return 2

    failures = _check_premises(premises)
    if failures:
        for failure in failures:
            print(f"premise_guard: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
