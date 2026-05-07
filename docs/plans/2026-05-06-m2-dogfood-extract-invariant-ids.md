---
id: m2-dogfood-extract-invariant-ids
name: M2 dogfood — extract invariant ids
firmness: provisional
status: spec — for cairn-tdd-feature dispatch
date: 2026-05-06
invariants-touched: []
envelope:
  - '^scripts/lib/invariant_id_extractor\.py$'
  - '^scripts/lib/__init__\.py$'
---

# M2 Dogfood — extract_invariant_ids

## What

A pure Python function `extract_invariant_ids(text: str) -> list[str]` that returns the sorted, deduplicated list of `INV-NNN` identifiers occurring in `text`, where `NNN` is exactly three digits.

## Why

Exercises all four phases of the `cairn-tdd-feature` skill on a target with clear inputs and outputs, no external integration, and no overlap with orchestrator code paths. Used as the M2 dogfood evidence for the cairn-shrink design.

## Boundary

- Pure function, no I/O, no logging, no caching.
- New file at `scripts/lib/invariant_id_extractor.py`. Empty `scripts/lib/__init__.py` to make the package importable.
- No changes to existing code, configuration, or hooks.

## Specification

```python
def extract_invariant_ids(text: str) -> list[str]:
    """Return sorted, deduplicated INV-NNN identifiers from `text`.

    NNN is exactly three digits. Matches are case-sensitive on `INV-`.
    """
```

Behaviors:

1. Empty string returns `[]`.
2. Text with no matches returns `[]`.
3. Single `INV-001` returns `["INV-001"]`.
4. Multiple unique ids return them sorted: `extract_invariant_ids("INV-008 see also INV-001")` returns `["INV-001", "INV-008"]`.
5. Duplicates collapse: `extract_invariant_ids("INV-001 and INV-001")` returns `["INV-001"]`.
6. Two-digit and four-digit forms do NOT match: `extract_invariant_ids("INV-99 INV-9999")` returns `[]`.
7. Lowercase `inv-001` does NOT match.
8. Embedded in word: `extract_invariant_ids("xINV-001y")` MAY match — define explicitly: yes, the regex is `INV-\d{3}` with no word boundaries; document this in the test.

## Verification

Tests at `tests/unit/test_invariant_id_extractor.py` covering all eight behaviors above.

Phase 4 must confirm: full suite passes; `validate_architecture.py` runs without new failures; `invariants-touched: []` so the invariant evidence section is empty by design.
