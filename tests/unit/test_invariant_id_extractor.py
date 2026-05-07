"""Tests for scripts.lib.invariant_id_extractor.extract_invariant_ids.

All eight behaviors from the M2 dogfood spec (intent.md / plan doc):
  https://github.com/…/docs/plans/2026-05-06-m2-dogfood-extract-invariant-ids.md
"""

from lib.invariant_id_extractor import extract_invariant_ids


def test_empty_string_returns_empty_list():
    """Behavior 1: empty string returns []."""
    assert extract_invariant_ids("") == []


def test_no_matching_pattern_returns_empty_list():
    """Behavior 2: text with no INV-NNN patterns returns []."""
    assert extract_invariant_ids("nothing to see here") == []


def test_single_occurrence_returns_list_with_one_entry():
    """Behavior 3: single occurrence INV-001 returns ['INV-001']."""
    assert extract_invariant_ids("INV-001") == ["INV-001"]


def test_multiple_distinct_ids_returned_sorted():
    """Behavior 4: multiple distinct ids are returned sorted."""
    assert extract_invariant_ids("INV-008 see also INV-001") == ["INV-001", "INV-008"]


def test_duplicate_occurrences_collapsed_to_one():
    """Behavior 5: duplicate occurrences collapse to one entry."""
    assert extract_invariant_ids("INV-001 and INV-001") == ["INV-001"]


def test_two_digit_and_four_digit_forms_do_not_match():
    """Behavior 6: two-digit (INV-99) and four-digit (INV-9999) forms do NOT match."""
    assert extract_invariant_ids("INV-99 INV-9999") == []


def test_lowercase_prefix_does_not_match():
    """Behavior 7: lowercase prefix inv-001 does NOT match (case-sensitive)."""
    assert extract_invariant_ids("inv-001") == []


def test_embedded_in_word_does_match():
    """Behavior 8: regex INV-\\d{3} carries no word boundaries.

    'xINV-001y' DOES match and returns ['INV-001']. The spec explicitly states
    no \\b anchors are used, so partial-word embeddings are intentional.
    """
    assert extract_invariant_ids("xINV-001y") == ["INV-001"]
