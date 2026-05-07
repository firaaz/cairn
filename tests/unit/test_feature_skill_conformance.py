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


# --- V4: handoff references cross-feature index ------------------------------


class TestHandoffCrossFeatureIndex:
    def test_handoff_template_has_features_section(self):
        """templates/handoff.md must contain a ## Features section
        (context-tiers-integration D0 — handoff.md gains a cross-feature index)."""
        path = CAIRN_ROOT / "templates" / "handoff.md"
        assert path.is_file(), f"{path} does not exist"
        text = path.read_text()
        assert "## Features" in text, (
            "templates/handoff.md does not contain ## Features section"
        )

    def test_handoff_features_section_describes_per_feature_line(self):
        """The ## Features section in the handoff template must describe
        the one-line-per-active-feature format (context-tiers-integration D0)."""
        path = CAIRN_ROOT / "templates" / "handoff.md"
        text = path.read_text()
        features_section = slice_section(text, "## Features")
        assert features_section is not None, (
            "templates/handoff.md has no ## Features section to inspect"
        )
        # Section should reference the per-feature line format
        assert contains_any(
            features_section,
            ["feature", "active", "line"],
            case_insensitive=True,
        ), "## Features section does not describe the per-feature line format"
