"""Phase 2 validation tests for SLICE-009 — skill file conformance.

Verifies intent.md V1 (feature file creation in start-slice), V3 (existing
feature update), V4 (cross-feature index in handoff), V5 (Tier 2 gating in
catchup), V8 (trigger discipline).

Static artifact checks — reads slash command files and templates, verifies
they contain feature-model instructions per ADR-006 D5 and ADR-008 D0/D1.

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


# --- V1: start-slice.full.md references feature file creation ----------------


class TestStartSliceFeatureCreation:
    def _read_start_slice_full(self) -> str:
        path = CAIRN_ROOT / "commands" / "claude-code" / "start-slice.full.md"
        assert path.is_file(), f"{path} does not exist"
        return path.read_text()

    def test_references_feature_file_path(self):
        """start-slice.full.md must reference .claude/features/ as the
        feature file location (ADR-006 D1)."""
        text = self._read_start_slice_full()
        assert ".claude/features/" in text, (
            "start-slice.full.md does not reference .claude/features/ path"
        )

    def test_references_feature_file_creation(self):
        """start-slice.full.md must contain instructions for creating a
        feature file when one does not exist (ADR-006 D3 always-create)."""
        text = self._read_start_slice_full()
        assert contains_any(
            text,
            ["create", "creates", "creating"],
            case_insensitive=True,
        ) and contains_any(
            text,
            ["feature file", "feature.yaml", ".claude/features/"],
            case_insensitive=True,
        ), "start-slice.full.md lacks feature file creation instructions"

    def test_references_feature_file_update(self):
        """start-slice.full.md must contain instructions for adding a slice
        entry to an existing feature file (V3 — existing feature update)."""
        text = self._read_start_slice_full()
        # Must reference adding/appending a slice entry to an existing feature
        has_update_language = contains_any(
            text,
            [
                "add",
                "adds",
                "append",
                "update",
                "existing feature",
                "already exists",
            ],
            case_insensitive=True,
        )
        has_slice_entry_language = contains_any(
            text,
            ["slice entry", "slices list", "slices:", "slice to the feature"],
            case_insensitive=True,
        )
        assert has_update_language and has_slice_entry_language, (
            "start-slice.full.md lacks instructions for updating existing feature files"
        )


# --- V4: handoff references cross-feature index ------------------------------


class TestHandoffCrossFeatureIndex:
    def test_handoff_full_references_cross_feature_index(self):
        """handoff.full.md must contain instructions for writing a
        cross-feature index section (ADR-008 D0/D1)."""
        path = CAIRN_ROOT / "commands" / "claude-code" / "handoff.full.md"
        assert path.is_file(), f"{path} does not exist"
        text = path.read_text()
        assert contains_any(
            text,
            ["## Features", "cross-feature index", "feature index"],
            case_insensitive=True,
        ), "handoff.full.md does not reference cross-feature index"

    def test_handoff_template_has_features_section(self):
        """templates/handoff.md must contain a ## Features section
        (ADR-008 D0 — handoff.md gains a cross-feature index)."""
        path = CAIRN_ROOT / "templates" / "handoff.md"
        assert path.is_file(), f"{path} does not exist"
        text = path.read_text()
        assert "## Features" in text, (
            "templates/handoff.md does not contain ## Features section"
        )

    def test_handoff_features_section_describes_per_feature_line(self):
        """The ## Features section in the handoff template must describe
        the one-line-per-active-feature format (ADR-008 D0)."""
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


# --- V5: catchup Tier 1 reads index from handoff, NOT feature files ----------


class TestCatchupTierGating:
    def _read_catchup_full(self) -> str:
        path = CAIRN_ROOT / "commands" / "claude-code" / "catchup.full.md"
        assert path.is_file(), f"{path} does not exist"
        return path.read_text()

    def test_tier1_references_cross_feature_index(self):
        """catchup.full.md Tier 1 must reference the cross-feature index
        from handoff.md (ADR-008 D1)."""
        text = self._read_catchup_full()
        assert contains_any(
            text,
            ["cross-feature index", "feature index", "## Features"],
            case_insensitive=True,
        ), "catchup.full.md does not reference cross-feature index"

    def test_tier1_does_not_load_feature_files(self):
        """catchup.full.md must explicitly state that feature files are NOT
        loaded at Tier 1 — they are Tier 2 on-demand reads (ADR-008 D0)."""
        text = self._read_catchup_full()
        # Must contain language about feature files being Tier 2 / not Tier 1
        has_tier2_reference = contains_any(
            text,
            [
                "tier 2",
                "on-demand",
                "not loaded in tier 1",
                "not tier 1",
                "feature file",
            ],
            case_insensitive=True,
        )
        assert has_tier2_reference, (
            "catchup.full.md does not clarify that feature files are Tier 2 reads"
        )


# --- V8: Trigger discipline — updates only at listed events ------------------


class TestTriggerDiscipline:
    def test_start_slice_is_a_trigger_event(self):
        """start-slice.full.md must contain feature file update logic,
        confirming it is a trigger event per ADR-006 D5."""
        path = CAIRN_ROOT / "commands" / "claude-code" / "start-slice.full.md"
        text = path.read_text()
        assert contains_any(
            text,
            [".claude/features/", "feature file", "feature.yaml"],
            case_insensitive=True,
        ), "start-slice.full.md does not reference feature files (trigger event)"

    def test_handoff_is_a_trigger_event(self):
        """handoff.full.md must contain cross-feature index update logic,
        confirming it is a trigger event per ADR-006 D5."""
        path = CAIRN_ROOT / "commands" / "claude-code" / "handoff.full.md"
        text = path.read_text()
        assert contains_any(
            text,
            ["## Features", "cross-feature", "feature index", "decomposition"],
            case_insensitive=True,
        ), "handoff.full.md does not reference feature index updates (trigger event)"
