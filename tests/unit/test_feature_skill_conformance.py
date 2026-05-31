"""Phase 2 validation tests for SLICE-009 — skill file conformance.

Verifies intent.md V1 (feature file creation in start-slice), V3 (existing
feature update), V4 (cross-feature index in handoff), V5 (Tier 2 gating in
catchup), V8 (trigger discipline).

Static artifact checks — reads slash command files and templates, verifies
they contain feature-model instructions per feature-slice-model D5 and context-tiers-integration D0/D1.

These tests FAIL until Phase 3 modifies the skill files.

Pytest + stdlib only.
"""

import re
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent


# --- Primitives (reused pattern from test_d1_gate.py) ------------------------


def slice_section(text: str, header: str) -> str | None:
    """Return the section starting at a line matching `header`.

    A line matches if it equals `header` exactly OR begins with `header`
    followed by a non-word boundary. The section runs from the matched line
    to the next line beginning with `## ` (same-level header) or EOF.
    Subheaders (`### ...`) stay inside. Returns None when no line matches.
    """
    pattern = re.compile(re.escape(header) + r"(?:$|\W)")
    lines = text.splitlines(keepends=True)
    start: int | None = None
    for i, line in enumerate(lines):
        if pattern.match(line.rstrip("\n")):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return "".join(lines[start:end])


def contains_any(
    text: str, phrases: list[str], *, case_insensitive: bool = False
) -> bool:
    """Return True if any phrase is present in text."""
    haystack = text.lower() if case_insensitive else text
    for phrase in phrases:
        needle = phrase.lower() if case_insensitive else phrase
        if needle in haystack:
            return True
    return False


# --- V4: handoff references feature context through pointer entries -----------


class TestHandoffPointerCompatibleFeatureGuidance:
    def test_handoff_template_has_contract_frontmatter(self):
        """templates/handoff.md carries the Trial-A frontmatter contract."""
        path = CAIRN_ROOT / "templates" / "handoff.md"
        assert path.is_file(), f"{path} does not exist"
        text = path.read_text()
        assert text.startswith("---\n"), "templates/handoff.md lacks frontmatter"
        frontmatter = text.split("\n---\n", 1)[0]
        assert "contract:" in frontmatter, (
            "templates/handoff.md frontmatter does not contain `contract:`"
        )

    def test_handoff_template_guides_feature_context_as_pointer_entry(self):
        """Feature/session context is represented as pointer-compatible entries."""
        path = CAIRN_ROOT / "templates" / "handoff.md"
        text = path.read_text()
        body = text.split("\n---\n", 1)[1]
        assert "## Features" not in text, (
            "templates/handoff.md should not require the retired ## Features section"
        )
        assert "<pointer> <state>" in body, (
            "templates/handoff.md body does not show the pointer/state entry shape"
        )
        assert "docs/plans/<filename>.md deferred <trigger-condition>" in body, (
            "templates/handoff.md does not show plan-doc context as a pointer entry"
        )
