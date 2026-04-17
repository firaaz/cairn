"""Phase 2 validation tests for SLICE-009 — cross-feature index format & budget.

Verifies intent.md V4 (cross-feature index format) and V9 (token budget —
5 features under 125 tokens).

Format and budget validation with synthetic data. These tests define the
spec and PASS immediately.

Pytest + stdlib only.
"""

import re


# --- Index line format -------------------------------------------------------

# context-tiers-integration D0: one line per active feature in handoff.md ## Features section.
# Format: "- <feature-id>: <status-summary>"
# Each line ~15–25 tokens.

INDEX_LINE_PATTERN = re.compile(r"^- [a-z][a-z0-9-]+: .+$")


def validate_index_line(line: str) -> bool:
    """Return True if the line matches the cross-feature index format."""
    return bool(INDEX_LINE_PATTERN.match(line.strip()))


def approximate_tokens(text: str) -> float:
    """Approximate token count at ~5 chars per token (context-tiers-integration convention)."""
    return len(text) / 5


# --- Sample data -------------------------------------------------------------

SAMPLE_LINES = [
    "- feature-slice-model: SLICE-009 active, phase validation",
    "- context-discipline: SLICE-003 complete",
    "- d1-automated-refresh: SLICE-008 complete",
    "- parallelism-native: SLICE-010 planned",
    "- unknown-backstop: SLICE-011 planned",
]

SAMPLE_INDEX = "\n".join(SAMPLE_LINES)


# --- V4: Cross-feature index line format -------------------------------------


class TestIndexLineFormat:
    def test_valid_active_feature_line(self):
        assert validate_index_line(
            "- feature-slice-model: SLICE-009 active, phase validation"
        )

    def test_valid_complete_feature_line(self):
        assert validate_index_line("- context-discipline: SLICE-003 complete")

    def test_valid_planned_feature_line(self):
        assert validate_index_line("- parallelism-native: SLICE-010 planned")

    def test_rejects_missing_dash_prefix(self):
        assert not validate_index_line("feature-slice-model: SLICE-009 active")

    def test_rejects_missing_colon_separator(self):
        assert not validate_index_line("- feature-slice-model SLICE-009 active")

    def test_rejects_empty_status(self):
        assert not validate_index_line("- feature-slice-model:")

    def test_rejects_uppercase_id(self):
        """Feature IDs are semantic kebab-case (semantic-identity) — lowercase."""
        assert not validate_index_line("- Feature-Slice-Model: SLICE-009 active")

    def test_all_sample_lines_valid(self):
        for line in SAMPLE_LINES:
            assert validate_index_line(line), f"Invalid sample line: {line}"


# --- V4: Empty index is valid ------------------------------------------------


class TestEmptyIndex:
    def test_empty_string_is_valid(self):
        """When no features are active, the ## Features section is absent
        or empty (intent.md V4)."""
        # An empty index has zero lines — nothing to validate
        lines = [line for line in "".splitlines() if line.strip()]
        assert len(lines) == 0

    def test_section_with_no_entries_is_valid(self):
        """A ## Features header with no entries beneath it is valid."""
        section = "## Features\n"
        content_lines = [
            line
            for line in section.splitlines()
            if line.strip() and not line.startswith("#")
        ]
        assert len(content_lines) == 0


# --- V9: Token budget — 5 features under 125 tokens -------------------------


class TestTokenBudget:
    def test_single_line_within_per_line_budget(self):
        """Each feature line should be ~15–25 tokens (context-tiers-integration D0)."""
        for line in SAMPLE_LINES:
            tokens = approximate_tokens(line)
            assert tokens <= 30, (
                f"Line exceeds per-line budget (~30 tokens): "
                f"{tokens:.0f} tokens for '{line}'"
            )

    def test_five_feature_index_under_125_tokens(self):
        """Cross-feature index with 5 features must stay under 125 tokens
        (intent.md V9, context-tiers-integration D0)."""
        tokens = approximate_tokens(SAMPLE_INDEX)
        assert tokens <= 125, (
            f"5-feature index ≈{tokens:.0f} tokens, exceeds 125-token ceiling"
        )

    def test_five_feature_index_under_625_chars(self):
        """Equivalent char-based check: 125 tokens × 5 chars/token = 625 chars."""
        assert len(SAMPLE_INDEX) <= 625, (
            f"5-feature index is {len(SAMPLE_INDEX)} chars, "
            f"exceeds 625-char ceiling (125 tokens × 5 chars/token)"
        )

    def test_index_fits_within_handoff_400_token_budget(self):
        """The index must leave room in handoff.md's 400-token ceiling.
        With ~275 tokens for other handoff sections (State, Next, Blocked,
        Pointers), 125 tokens for the index = 400 total (context-tiers-integration D3)."""
        index_tokens = approximate_tokens(SAMPLE_INDEX)
        remaining_budget = 400 - index_tokens
        assert remaining_budget >= 200, (
            f"Index uses ≈{index_tokens:.0f} tokens, leaving only "
            f"≈{remaining_budget:.0f} for other handoff sections (need ≥200)"
        )
