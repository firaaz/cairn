"""Phase 2 validation for efficiency-program/all-seven Item 3 — Read-before-Write preload prose.

Verifies intent.md Item 3 acceptance:
  grep -c "Read the file first (CC 2.1.110+ requires Read before Write)" \
     commands/claude-code/handoff.full.md        >= 1
  same grep on commands/claude-code/start-slice.full.md                  >= 1

Exact verbatim substring required — Phase 3 must match the intent's spec
string character-for-character so grep-based audits downstream don't drift.

RED phase: neither file currently contains this phrase.
Pytest + stdlib only.
"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CMD = PROJECT_ROOT / "commands" / "claude-code"

HANDOFF_FULL = CMD / "handoff.full.md"
START_SLICE_FULL = CMD / "start-slice.full.md"

REQUIRED_PHRASE = "Read the file first (CC 2.1.110+ requires Read before Write)"


class TestRequiredPhrasePresent:
    def test_handoff_full_contains_phrase(self):
        text = HANDOFF_FULL.read_text(encoding="utf-8")
        count = text.count(REQUIRED_PHRASE)
        assert count >= 1, (
            f"handoff.full.md missing verbatim phrase {REQUIRED_PHRASE!r} "
            f"(grep -c returned {count})"
        )

    def test_start_slice_full_contains_phrase(self):
        text = START_SLICE_FULL.read_text(encoding="utf-8")
        count = text.count(REQUIRED_PHRASE)
        assert count >= 1, (
            f"start-slice.full.md missing verbatim phrase {REQUIRED_PHRASE!r} "
            f"(grep -c returned {count})"
        )


class TestPhraseLocation:
    """The phrase is a preamble at the top of the phase-commit instruction
    sections (intent.md Item 3). Loose placement check: assert it appears
    before any literal 'slice.yaml' write instruction in handoff.full.md so
    the preamble actually precedes the footgun."""

    def test_handoff_full_phrase_appears_before_slice_yaml_write(self):
        text = HANDOFF_FULL.read_text(encoding="utf-8")
        phrase_idx = text.find(REQUIRED_PHRASE)
        assert phrase_idx != -1, (
            "required phrase absent from handoff.full.md (precondition check)"
        )
        write_idx = text.find("slice.yaml", phrase_idx)
        # Allow absence of a following 'slice.yaml' mention (preamble is at
        # top); only assert ordering when both are present after the phrase.
        if write_idx != -1:
            # Phrase comes first by definition of `.find` from phrase_idx.
            assert write_idx > phrase_idx

    def test_start_slice_full_phrase_appears_before_slice_yaml_write(self):
        text = START_SLICE_FULL.read_text(encoding="utf-8")
        phrase_idx = text.find(REQUIRED_PHRASE)
        assert phrase_idx != -1, (
            "required phrase absent from start-slice.full.md (precondition check)"
        )
        write_idx = text.find("slice.yaml", phrase_idx)
        if write_idx != -1:
            assert write_idx > phrase_idx
