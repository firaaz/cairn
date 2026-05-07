"""Utilities for extracting invariant identifiers from text."""

import re


def extract_invariant_ids(text: str) -> list[str]:
    """Return sorted, deduplicated INV-NNN identifiers from `text`.

    NNN is exactly three digits. Matches are case-sensitive on `INV-`.
    """
    # Negative lookahead prevents matching a 3-digit prefix inside a 4+-digit run.
    return sorted(set(re.findall(r"INV-\d{3}(?!\d)", text)))
